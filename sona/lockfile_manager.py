from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any


LOCKFILE_NAME = "sona.lock.json"
LOCKFILE_VERSION = "0.1"
HASH_ALGORITHM = "sha256"
TOP_LEVEL_INCLUDE_FILES = (
    "pyproject.toml",
    "setup.py",
    "requirements.txt",
    "sona.json",
)
INCLUDE_ROOTS = (
    "sona",
    "stdlib",
)
EXCLUDE_DIRS = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".mypy_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".sona",
}


def _utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _tree_sha256(entries: list[dict[str, Any]]) -> str:
    hasher = hashlib.sha256()
    for entry in sorted(entries, key=lambda item: str(item["path"])):
        hasher.update(str(entry["path"]).encode("utf-8"))
        hasher.update(b"\n")
        hasher.update(str(entry["sha256"]).encode("utf-8"))
        hasher.update(b"\n")
        hasher.update(str(int(entry["size"])).encode("utf-8"))
        hasher.update(b"\n")
    return hasher.hexdigest()


def _collect_top_level_entries(workspace_dir: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for name in TOP_LEVEL_INCLUDE_FILES:
        candidate = workspace_dir / name
        if not candidate.exists() or not candidate.is_file():
            continue
        entries.append(
            {
                "path": candidate.relative_to(workspace_dir).as_posix(),
                "size": int(candidate.stat().st_size),
                "sha256": _sha256_file(candidate),
            }
        )
    return entries


def _collect_tree_entries(workspace_dir: Path) -> list[dict[str, Any]]:
    entries = _collect_top_level_entries(workspace_dir)

    for root_name in INCLUDE_ROOTS:
        root = workspace_dir / root_name
        if not root.exists() or not root.is_dir():
            continue

        for current_root, dir_names, file_names in os.walk(root, topdown=True):
            dir_names[:] = sorted([name for name in dir_names if name not in EXCLUDE_DIRS])
            for file_name in sorted(file_names):
                candidate = Path(current_root) / file_name
                if not candidate.is_file():
                    continue

                rel_path = candidate.relative_to(workspace_dir).as_posix()
                if "/.git/" in f"/{rel_path}/":
                    continue
                if "/__pycache__/" in f"/{rel_path}/":
                    continue

                entries.append(
                    {
                        "path": rel_path,
                        "size": int(candidate.stat().st_size),
                        "sha256": _sha256_file(candidate),
                    }
                )

    entries.sort(key=lambda item: str(item["path"]))
    return entries


def _lockfile_payload(workspace_dir: Path, *, include_timestamp: bool) -> dict[str, Any]:
    root = workspace_dir.resolve()
    entries = _collect_tree_entries(root)
    payload: dict[str, Any] = {
        "lock_version": LOCKFILE_VERSION,
        "hash_algorithm": HASH_ALGORITHM,
        "workspace": root.as_posix(),
        "entries": entries,
        "summary": {
            "file_count": len(entries),
            "tree_sha256": _tree_sha256(entries),
        },
    }
    if include_timestamp:
        payload["generated_at_utc"] = _utc_timestamp()
    return payload


def lockfile_payload(workspace_dir: Path) -> dict[str, Any]:
    """Public API: deterministic lockfile payload (no timestamp) for embedding in bundles."""
    return _lockfile_payload(workspace_dir, include_timestamp=False)


def _lock_path(workspace_dir: Path) -> Path:
    return workspace_dir.resolve() / LOCKFILE_NAME


def generate_lockfile(workspace_dir: Path) -> bool:
    """
    Generate deterministic workspace lockfile for runtime + stdlib artifacts.

    Returns True on success and False on failure.
    """
    try:
        workspace = workspace_dir.resolve()
        if not workspace.exists() or not workspace.is_dir():
            return False

        payload = _lockfile_payload(workspace, include_timestamp=True)
        lock_path = _lock_path(workspace)
        text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        lock_path.write_text(text, encoding="utf-8", newline="\n")
        return True
    except Exception:
        return False


def verify_lockfile(workspace_dir: Path) -> bool:
    """
    Verify current workspace against sona.lock.json.

    Returns True when the lockfile matches current workspace state.
    """
    try:
        workspace = workspace_dir.resolve()
        lock_path = _lock_path(workspace)
        if not lock_path.exists() or not lock_path.is_file():
            return False

        expected = json.loads(lock_path.read_text(encoding="utf-8"))
        if not isinstance(expected, dict):
            return False

        current = _lockfile_payload(workspace, include_timestamp=False)
        expected_copy = dict(expected)
        expected_copy.pop("generated_at_utc", None)
        return expected_copy == current
    except Exception:
        return False
