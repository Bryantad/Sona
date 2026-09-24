"""Persistent registry for explicit local model artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from contextlib import suppress
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from threading import RLock
from typing import Any

from .contracts import ModelFormat, ModelIdentity

REGISTRY_SCHEMA_VERSION = 1
MAX_REGISTRY_BYTES = 16_000_000
_MODEL_REQUIRED = {"model_id", "provider_id", "runtime_id", "format", "path", "context_tokens"}
_MODEL_FIELDS = set(ModelIdentity.__dataclass_fields__)
_DOCUMENT_FIELDS = {"schema_version", "default_model_id", "models"}


class ModelRegistryError(ValueError):
    """Safe, user-actionable registry validation or persistence failure."""


@dataclass(frozen=True, slots=True)
class ModelInspection:
    identity: ModelIdentity
    artifact_exists: bool
    artifact_size_bytes: int | None
    format_valid: bool | None
    expected_sha256: str | None
    hash_verified: bool | None


def _identity_from_data(payload: Any) -> ModelIdentity:
    if not isinstance(payload, dict):
        raise ModelRegistryError("each model entry must be an object")
    missing = _MODEL_REQUIRED - set(payload)
    unknown = set(payload) - _MODEL_FIELDS
    if missing:
        raise ModelRegistryError(f"model entry missing fields: {', '.join(sorted(missing))}")
    if unknown:
        raise ModelRegistryError(f"model entry has unknown fields: {', '.join(sorted(unknown))}")
    if isinstance(payload.get("context_tokens"), bool) or not isinstance(
        payload.get("context_tokens"), int
    ):
        raise ModelRegistryError("context_tokens must be an integer")
    try:
        values = dict(payload)
        values["format"] = ModelFormat(values["format"])
        return ModelIdentity(**values)
    except (TypeError, ValueError) as exc:
        raise ModelRegistryError(f"invalid model entry: {exc}") from exc


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_gguf(path: Path) -> bool:
    try:
        with path.open("rb") as artifact:
            return artifact.read(4) == b"GGUF"
    except OSError as exc:
        raise ModelRegistryError("model artifact could not be read") from exc


class LocalModelRegistry:
    """One persistent local-model catalogue with explicit default selection.

    Registry updates are validated before an atomic same-directory replacement.
    Loading a registry never loads a model or starts a runtime.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()
        self._lock = RLock()
        self._models: dict[str, ModelIdentity] = {}
        self._default_model_id: str | None = None
        self._load()

    @property
    def default_model_id(self) -> str | None:
        with self._lock:
            return self._default_model_id

    def list(self) -> tuple[ModelIdentity, ...]:
        with self._lock:
            return tuple(self._models[key] for key in sorted(self._models))

    def get(self, model_id: str) -> ModelIdentity | None:
        with self._lock:
            return self._models.get(model_id)

    def default(self) -> ModelIdentity | None:
        with self._lock:
            if self._default_model_id is None:
                return None
            return self._models[self._default_model_id]

    def add(self, identity: ModelIdentity) -> ModelIdentity:
        path = Path(identity.path).expanduser()
        try:
            resolved = path.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise ModelRegistryError(
                "model artifact path does not exist or cannot be resolved"
            ) from exc
        if not resolved.is_file():
            raise ModelRegistryError("model artifact path must name a regular file")
        if identity.format is ModelFormat.GGUF and not _is_gguf(resolved):
            raise ModelRegistryError("model artifact does not have a valid GGUF header")
        normalized = replace(identity, path=str(resolved))
        if normalized.sha256 is not None:
            try:
                actual_hash = _hash_file(resolved)
            except OSError as exc:
                raise ModelRegistryError(
                    "model artifact could not be read for hash verification"
                ) from exc
            if actual_hash != normalized.sha256:
                raise ModelRegistryError(
                    "model artifact SHA-256 does not match the declared identity"
                )
        with self._lock:
            if normalized.model_id in self._models:
                raise ModelRegistryError(f"model id already exists: {normalized.model_id}")
            candidate = dict(self._models)
            candidate[normalized.model_id] = normalized
            self._persist(candidate, self._default_model_id)
            self._models = candidate
        return normalized

    def inspect(self, model_id: str, *, verify_hash: bool = False) -> ModelInspection:
        identity = self.get(model_id)
        if identity is None:
            raise ModelRegistryError(f"unknown model id: {model_id}")
        path = Path(identity.path)
        if not path.is_file():
            return ModelInspection(identity, False, None, None, identity.sha256, None)
        format_valid = _is_gguf(path) if identity.format is ModelFormat.GGUF else False
        verified: bool | None = None
        if verify_hash and identity.sha256 is not None:
            try:
                verified = _hash_file(path) == identity.sha256
            except OSError as exc:
                raise ModelRegistryError(
                    "model artifact could not be read for hash verification"
                ) from exc
        try:
            size = path.stat().st_size
        except OSError as exc:
            raise ModelRegistryError("model artifact metadata could not be read") from exc
        return ModelInspection(identity, True, size, format_valid, identity.sha256, verified)

    def remove(self, model_id: str) -> ModelIdentity:
        with self._lock:
            if model_id not in self._models:
                raise ModelRegistryError(f"unknown model id: {model_id}")
            removed = self._models[model_id]
            candidate = dict(self._models)
            del candidate[model_id]
            default_model_id = (
                None if self._default_model_id == model_id else self._default_model_id
            )
            self._persist(candidate, default_model_id)
            self._models = candidate
            self._default_model_id = default_model_id
            return removed

    def set_default(self, model_id: str) -> ModelIdentity:
        with self._lock:
            identity = self._models.get(model_id)
            if identity is None:
                raise ModelRegistryError(f"unknown model id: {model_id}")
            self._persist(self._models, model_id)
            self._default_model_id = model_id
            return identity

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            size = self.path.stat().st_size
            if size > MAX_REGISTRY_BYTES:
                raise ModelRegistryError("model registry exceeds the maximum supported size")
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except ModelRegistryError:
            raise
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ModelRegistryError("model registry could not be read as valid JSON") from exc
        if not isinstance(document, dict):
            raise ModelRegistryError("model registry root must be an object")
        missing = _DOCUMENT_FIELDS - set(document)
        unknown = set(document) - _DOCUMENT_FIELDS
        if missing:
            raise ModelRegistryError(f"registry missing fields: {', '.join(sorted(missing))}")
        if unknown:
            raise ModelRegistryError(f"registry has unknown fields: {', '.join(sorted(unknown))}")
        if (
            isinstance(document["schema_version"], bool)
            or document["schema_version"] != REGISTRY_SCHEMA_VERSION
        ):
            raise ModelRegistryError("unsupported model registry schema_version")
        raw_models = document["models"]
        if not isinstance(raw_models, list):
            raise ModelRegistryError("registry models field must be a list")
        models: dict[str, ModelIdentity] = {}
        for raw_model in raw_models:
            identity = _identity_from_data(raw_model)
            if identity.model_id in models:
                raise ModelRegistryError(f"duplicate model id in registry: {identity.model_id}")
            models[identity.model_id] = identity
        default_model_id = document["default_model_id"]
        if default_model_id is not None and (
            not isinstance(default_model_id, str) or default_model_id not in models
        ):
            raise ModelRegistryError("default_model_id must refer to a registered model")
        self._models = models
        self._default_model_id = default_model_id

    def _persist(self, models: dict[str, ModelIdentity], default_model_id: str | None) -> None:
        document = {
            "schema_version": REGISTRY_SCHEMA_VERSION,
            "default_model_id": default_model_id,
            "models": [asdict(models[key]) for key in sorted(models)],
        }
        encoded = json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        if len(encoded) > MAX_REGISTRY_BYTES:
            raise ModelRegistryError("model registry exceeds the maximum supported size")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent
            )
        except OSError as exc:
            raise ModelRegistryError("model registry directory is not writable") from exc
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as destination:
                destination.write(encoded)
                destination.flush()
                os.fsync(destination.fileno())
            os.replace(temporary_path, self.path)
        except OSError as exc:
            with suppress(OSError):
                temporary_path.unlink(missing_ok=True)
            raise ModelRegistryError("model registry update could not be published") from exc
