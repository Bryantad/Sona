"""Native backing for the public Sona Guardian facade.

Guardian state is local to an explicitly initialized project root. Importing
this module does not create storage or mutate user configuration.
"""

from __future__ import annotations

from datetime import datetime, timezone
import fnmatch
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_EXCLUDES = [
    ".git/**",
    ".venv/**",
    "__pycache__/**",
    "dist/**",
    "build/**",
    "*.pyc",
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    ".sona/guardian/**",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _project_root(value: Any = None) -> Path:
    root = Path(str(value or ".")).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Guardian project root does not exist: {root}")
    return root


def _state_dir(root: Path) -> Path:
    return root / ".sona" / "guardian"


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_excluded(rel_path: str) -> bool:
    normalized = rel_path.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in DEFAULT_EXCLUDES)


def _safe_resolve(root: Path, path: Path) -> Path:
    candidate = (root / path).resolve(strict=False) if not path.is_absolute() else path.resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Guardian rejected path outside project root: {candidate}") from exc
    return candidate


def _audit(root: Path, event: str, payload: dict[str, Any]) -> None:
    audit_dir = _state_dir(root) / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": _now(),
        "event": event,
        "payload": payload,
    }
    with (audit_dir / "audit.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inventory(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        safe = _safe_resolve(root, path)
        rel = _relative(root, safe)
        if _is_excluded(rel):
            continue
        if safe.is_dir():
            continue
        if safe.is_symlink():
            target = safe.resolve(strict=False)
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise ValueError(f"Guardian rejected symlink escape: {rel}") from exc
        records.append({
            "path": rel,
            "sha256": _hash_file(safe),
            "size": safe.stat().st_size,
        })
    return records


def _baseline_path(root: Path) -> Path:
    return _state_dir(root) / "baseline.json"


def _load_baseline(root: Path) -> dict[str, Any] | None:
    path = _baseline_path(root)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def guardian_status(project_root: Any = None) -> dict[str, Any]:
    root = _project_root(project_root)
    state = _state_dir(root)
    baseline = _baseline_path(root)
    return {
        "project_root": str(root),
        "initialized": baseline.exists(),
        "state_dir": str(state),
    }


def guardian_init(project_root: Any = None) -> dict[str, Any]:
    root = _project_root(project_root)
    state = _state_dir(root)
    state.mkdir(parents=True, exist_ok=True)
    manifest = {
        "version": 1,
        "created_at": _now(),
        "project_root": str(root),
        "excludes": list(DEFAULT_EXCLUDES),
        "files": _inventory(root),
    }
    _baseline_path(root).write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    _audit(root, "guardian.init", {"file_count": len(manifest["files"])})
    return {
        "status": "initialized",
        "project_root": str(root),
        "file_count": len(manifest["files"]),
    }


def guardian_verify(project_root: Any = None) -> dict[str, Any]:
    root = _project_root(project_root)
    baseline = _load_baseline(root)
    if baseline is None:
        return {"status": "uninitialized", "project_root": str(root)}
    current = {item["path"]: item for item in _inventory(root)}
    trusted = {item["path"]: item for item in baseline.get("files", [])}
    added = sorted(set(current) - set(trusted))
    missing = sorted(set(trusted) - set(current))
    changed = sorted(
        path for path in (set(current) & set(trusted))
        if current[path]["sha256"] != trusted[path]["sha256"]
    )
    result = {
        "status": "ok" if not added and not missing and not changed else "drift",
        "project_root": str(root),
        "added": added,
        "missing": missing,
        "changed": changed,
    }
    _audit(root, "guardian.verify", {
        "status": result["status"],
        "added": len(added),
        "missing": len(missing),
        "changed": len(changed),
    })
    return result


def guardian_doctor(project_root: Any = None) -> dict[str, Any]:
    status = guardian_status(project_root)
    status["default_excludes"] = list(DEFAULT_EXCLUDES)
    status["message"] = (
        "Guardian is initialized and ready."
        if status["initialized"]
        else "Guardian is not initialized for this project."
    )
    return status


__all__ = [
    "guardian_status",
    "guardian_init",
    "guardian_verify",
    "guardian_doctor",
]
