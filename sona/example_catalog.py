"""Versioned shipped example metadata and resources; no execution semantics."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path, PurePosixPath

MAX_ASSET_BYTES = 256 * 1024
_NAME = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")
_PATH = re.compile(r"[a-zA-Z0-9_./-]+\Z")


@dataclass
class ExampleError(Exception):
    diagnostic_id: str
    message: str
    hint: str

    def to_dict(self) -> dict:
        return {"diagnostic_id": self.diagnostic_id, "message": self.message, "hint": self.hint}


def invalid_catalog() -> ExampleError:
    return ExampleError("SONA-EXAMPLE-002", "The shipped example catalog is invalid or unavailable.",
                        "Reinstall Sona from a complete package; do not execute unreviewed replacement assets.")


def safe_asset_path(value: object) -> bool:
    if not isinstance(value, str) or not _PATH.fullmatch(value):
        return False
    path = PurePosixPath(value)
    return (not path.is_absolute() and str(path) == value
            and all(part not in {".", ".."} and not part.startswith(".") for part in path.parts))


def validate_manifest(payload: object) -> dict:
    if not isinstance(payload, dict) or set(payload) != {"schema", "revision", "examples"}:
        raise invalid_catalog()
    if type(payload["schema"]) is not int or payload["schema"] != 1:
        raise invalid_catalog()
    if type(payload["revision"]) is not int or payload["revision"] < 1:
        raise invalid_catalog()
    entries = payload["examples"]
    if not isinstance(entries, list) or not 1 <= len(entries) <= 100:
        raise invalid_catalog()
    names, concepts = set(), set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"name", "source", "assets", "runtime", "concept", "stdout"}:
            raise invalid_catalog()
        name, source, assets, concept = entry["name"], entry["source"], entry["assets"], entry["concept"]
        if not isinstance(name, str) or not _NAME.fullmatch(name) or name in names:
            raise invalid_catalog()
        names.add(name)
        if not safe_asset_path(source) or not source.endswith(".sona"):
            raise invalid_catalog()
        if not isinstance(assets, list) or len(assets) > 20 or any(not safe_asset_path(a) for a in assets):
            raise invalid_catalog()
        if len(set(assets)) != len(assets) or source in assets:
            raise invalid_catalog()
        if entry["runtime"] not in ("python", "native-proof", "guardian-proof"):
            raise invalid_catalog()
        if not isinstance(entry["stdout"], str) or len(entry["stdout"].encode("utf-8")) > 16384:
            raise invalid_catalog()
        if concept is not None:
            if not isinstance(concept, str) or not _NAME.fullmatch(concept) or concept in concepts:
                raise invalid_catalog()
            concepts.add(concept)
    return payload


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise invalid_catalog()
        result[key] = value
    return result


def load_manifest() -> dict:
    try:
        with files("sona").joinpath("data", "examples.json").open("rb") as handle:
            raw = handle.read(MAX_ASSET_BYTES + 1)
        if len(raw) > MAX_ASSET_BYTES:
            raise invalid_catalog()
        return validate_manifest(json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object))
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        raise invalid_catalog() from exc


def find_example(name: str, manifest: dict | None = None) -> dict:
    for entry in (manifest or load_manifest())["examples"]:
        if name == entry["name"]:
            return entry
    raise ExampleError("SONA-EXAMPLE-001", "The example name is unknown.", "Run `sona examples` for exact available names.")


def asset_text(path: str) -> str:
    if not safe_asset_path(path):
        raise invalid_catalog()
    packaged = files("sona").joinpath("_examples")
    # A wheel must not silently fall back to unrelated adjacent files if damaged.
    if packaged.is_dir():
        target = packaged.joinpath(*PurePosixPath(path).parts)
    else:
        checkout = Path(__file__).resolve().parent.parent
        if not (checkout / "pyproject.toml").is_file():
            raise invalid_catalog()
        target = checkout / "examples" / path
        try:
            target.resolve(strict=True).relative_to((checkout / "examples").resolve(strict=True))
        except (OSError, ValueError, RuntimeError) as exc:
            raise invalid_catalog() from exc
    try:
        with target.open("rb") as handle:
            raw = handle.read(MAX_ASSET_BYTES + 1)
        if len(raw) > MAX_ASSET_BYTES:
            raise invalid_catalog()
        return raw.decode("utf-8").replace("\r\n", "\n")
    except (OSError, UnicodeError) as exc:
        raise invalid_catalog() from exc
