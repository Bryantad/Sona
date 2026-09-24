"""Persistence and validation tests for the Sona local model registry."""

from __future__ import annotations

import hashlib
import json

import pytest

from sona.intelligence.contracts import ModelFormat, ModelIdentity
from sona.intelligence.registry import LocalModelRegistry, ModelRegistryError


def _model(path, *, model_id="local-coder", digest=None):
    return ModelIdentity(
        model_id=model_id,
        provider_id="local",
        runtime_id="llama-cpp",
        format=ModelFormat.GGUF,
        path=str(path),
        context_tokens=8192,
        sha256=digest,
        architecture="test-architecture",
        quantization="Q4_K_M",
    )


def test_registry_adds_and_reopens_gguf_model_with_stable_default(tmp_path):
    artifact = tmp_path / "coder.gguf"
    artifact.write_bytes(b"GGUF" + b"model payload")
    registry_path = tmp_path / "registry" / "models.json"

    registry = LocalModelRegistry(registry_path)
    added = registry.add(_model(artifact))
    assert added.path == str(artifact.resolve())
    assert registry.set_default(added.model_id) == added
    assert registry.default_model_id == "local-coder"

    reopened = LocalModelRegistry(registry_path)
    inspection = reopened.inspect("local-coder")
    assert reopened.default() == added
    assert inspection.artifact_exists is True
    assert inspection.format_valid is True
    assert inspection.artifact_size_bytes == artifact.stat().st_size
    assert inspection.hash_verified is None


def test_registry_verifies_optional_artifact_hash_and_uses_canonical_json(tmp_path):
    artifact = tmp_path / "model.gguf"
    contents = b"GGUF" + b"artifact"
    artifact.write_bytes(contents)
    digest = hashlib.sha256(contents).hexdigest()
    registry_path = tmp_path / "models.json"
    registry = LocalModelRegistry(registry_path)
    registry.add(_model(artifact, digest=digest))

    inspection = registry.inspect("local-coder", verify_hash=True)
    assert inspection.hash_verified is True
    raw = registry_path.read_text(encoding="utf-8")
    assert raw == json.dumps(
        json.loads(raw), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )

    artifact.write_bytes(b"GGUF" + b"modified")
    assert registry.inspect("local-coder", verify_hash=True).hash_verified is False


def test_registry_rejects_missing_non_gguf_mismatched_hash_and_duplicate(tmp_path):
    registry = LocalModelRegistry(tmp_path / "models.json")
    with pytest.raises(ModelRegistryError, match="does not exist"):
        registry.add(_model(tmp_path / "missing.gguf"))

    wrong_format = tmp_path / "not-a-model.gguf"
    wrong_format.write_bytes(b"NOPE" + b"payload")
    with pytest.raises(ModelRegistryError, match="valid GGUF header"):
        registry.add(_model(wrong_format))

    artifact = tmp_path / "valid.gguf"
    artifact.write_bytes(b"GGUF" + b"payload")
    with pytest.raises(ModelRegistryError, match="does not match"):
        registry.add(_model(artifact, digest="0" * 64))

    registry.add(_model(artifact))
    with pytest.raises(ModelRegistryError, match="already exists"):
        registry.add(_model(artifact))


def test_registry_set_default_remove_and_missing_model_are_consistent(tmp_path):
    artifact_a = tmp_path / "a.gguf"
    artifact_b = tmp_path / "b.gguf"
    artifact_a.write_bytes(b"GGUF-a")
    artifact_b.write_bytes(b"GGUF-b")
    registry = LocalModelRegistry(tmp_path / "models.json")
    registry.add(_model(artifact_b, model_id="b"))
    registry.add(_model(artifact_a, model_id="a"))
    assert [item.model_id for item in registry.list()] == ["a", "b"]
    with pytest.raises(ModelRegistryError, match="unknown model id"):
        registry.set_default("missing")
    registry.set_default("b")
    removed = registry.remove("b")
    assert removed.model_id == "b"
    assert registry.default_model_id is None
    assert [item.model_id for item in LocalModelRegistry(tmp_path / "models.json").list()] == ["a"]
    with pytest.raises(ModelRegistryError, match="unknown model id"):
        registry.remove("b")


@pytest.mark.parametrize(
    "document, message",
    [
        ([], "root must be an object"),
        ({"schema_version": 2, "default_model_id": None, "models": []}, "unsupported"),
        (
            {"schema_version": 1, "default_model_id": None, "models": [], "extra": 1},
            "unknown fields",
        ),
        (
            {"schema_version": 1, "default_model_id": None, "models": [{"model_id": "x"}]},
            "missing fields",
        ),
    ],
)
def test_registry_rejects_malformed_or_unknown_persisted_state(tmp_path, document, message):
    path = tmp_path / "models.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ModelRegistryError, match=message):
        LocalModelRegistry(path)


def test_registry_does_not_overwrite_corrupt_state_when_loading_or_mutating(tmp_path):
    path = tmp_path / "models.json"
    corrupt = "{invalid json"
    path.write_text(corrupt, encoding="utf-8")
    with pytest.raises(ModelRegistryError, match="valid JSON"):
        LocalModelRegistry(path)
    assert path.read_text(encoding="utf-8") == corrupt
