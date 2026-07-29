from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "release" / "import_0153_manifest.py"
SPEC = importlib.util.spec_from_file_location("import_0153_manifest", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
manifest_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manifest_tool)


def _git(root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        shell=False,
        check=True,
    )
    return process.stdout.strip()


def _repository(path: Path) -> str:
    path.mkdir()
    _git(path, "init")
    _git(path, "config", "user.name", "Sona Tests")
    _git(path, "config", "user.email", "tests@example.invalid")
    (path / "modified.txt").write_text("base\n", encoding="utf-8")
    (path / "deleted.txt").write_text("delete\n", encoding="utf-8")
    _git(path, "add", ".")
    _git(path, "commit", "-m", "base")
    return _git(path, "rev-parse", "HEAD")


def test_manifest_create_apply_and_verify_round_trip(tmp_path: Path):
    source = tmp_path / "source"
    base = _repository(source)
    destination = tmp_path / "destination"
    _git(tmp_path, "clone", str(source), str(destination))

    (source / "modified.txt").write_text("release\n", encoding="utf-8")
    (source / "deleted.txt").unlink()
    (source / "new.txt").write_text("new\n", encoding="utf-8")
    (source / "extensions").mkdir()
    (source / "extensions" / "excluded.txt").write_text("excluded\n", encoding="utf-8")
    (source / "debug.js.map").write_text("{}\n", encoding="utf-8")

    manifest_path = tmp_path / "manifest.json"
    create_summary = tmp_path / "create-summary"
    manifest_tool.create_manifest(source, base, manifest_path, create_summary)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = {
        entry["destination_relative_path"]: entry for entry in manifest["entries"]
    }
    assert set(entries) == {"deleted.txt", "modified.txt", "new.txt"}
    assert entries["new.txt"]["source_sha256"] == entries["new.txt"]["destination_sha256"]
    assert entries["deleted.txt"]["destination_sha256"] is None
    assert "extensions/excluded.txt" not in entries
    assert "debug.js.map" not in entries

    apply_summary = tmp_path / "apply-summary"
    manifest_tool.apply_manifest(
        manifest_path,
        source,
        destination,
        apply_summary,
    )
    assert (destination / "modified.txt").read_text(encoding="utf-8") == "release\n"
    assert (destination / "new.txt").read_text(encoding="utf-8") == "new\n"
    assert not (destination / "deleted.txt").exists()
    manifest_tool.verify_manifest(manifest_path, destination, verify_diff=False)
    _git(destination, "config", "user.name", "Sona Tests")
    _git(destination, "config", "user.email", "tests@example.invalid")
    _git(destination, "add", "--all")
    _git(destination, "commit", "-m", "import")
    manifest_tool.verify_manifest(manifest_path, destination, verify_diff=True)


def test_manifest_rejects_unsafe_and_case_colliding_destinations(tmp_path: Path):
    manifest_path = tmp_path / "manifest.json"
    entry = {
        "source_relative_path": "safe.txt",
        "destination_relative_path": "../escape.txt",
        "source_sha256": "A" * 64,
        "destination_sha256": "A" * 64,
        "classification": "new",
        "release_area": "runtime",
        "reason": "test",
    }
    manifest_path.write_text(
        json.dumps(
            {
                "schema_id": manifest_tool.SCHEMA_ID,
                "schema": 1,
                "release_version": "0.15.3",
                "source_workspace_baseline": "0" * 40,
                "destination_base_commit": "0" * 40,
                "excluded_paths": manifest_tool.DEFAULT_EXCLUSIONS,
                "entries": [entry],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unsafe relative path"):
        manifest_tool._load_manifest(manifest_path)

    entry["destination_relative_path"] = "Safe.txt"
    duplicate = dict(entry, destination_relative_path="safe.txt")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["entries"] = [entry, duplicate]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate destination"):
        manifest_tool._load_manifest(manifest_path)
