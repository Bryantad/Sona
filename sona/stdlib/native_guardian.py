"""Native backing for the public Sona Guardian facade.

Guardian state is local to an explicitly initialized project root. Importing
this module does not create storage or mutate user configuration.
"""

from __future__ import annotations

from datetime import datetime, timezone
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import time
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

CONFIG_NAME = "sona.guard.json"
STATE_VERSION = 1


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _project_root(value: Any = None) -> Path:
    root = Path(str(value or ".")).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Guardian project root does not exist: {root}")
    return root


def _state_dir(root: Path) -> Path:
    return root / ".sona" / "guardian"


def _baseline_path(root: Path) -> Path:
    return _state_dir(root) / "baseline.json"


def _trusted_config_path(root: Path) -> Path:
    return _state_dir(root) / "trusted_config.json"


def _circuit_path(root: Path) -> Path:
    return _state_dir(root) / "circuit_breaker.json"


def _snapshot_root(root: Path) -> Path:
    return _state_dir(root) / "snapshots"


def _quarantine_root(root: Path) -> Path:
    return _state_dir(root) / "quarantine"


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_excluded(rel_path: str, extra_excludes: list[str] | None = None) -> bool:
    normalized = rel_path.replace("\\", "/")
    patterns = [*DEFAULT_EXCLUDES, *(extra_excludes or [])]
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)


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


def _safe_resolve(root: Path, path: Path | str, action: str) -> Path:
    root = root.resolve()
    source = Path(path)
    original = source if source.is_absolute() else root / source
    if original.is_symlink():
        target = original.resolve(strict=False)
        try:
            target.relative_to(root)
        except ValueError as exc:
            rel = original.relative_to(root).as_posix() if original.is_relative_to(root) else str(original)
            _audit(root, "guardian.path.reject", {"action": action, "path": rel, "reason": "symlink-escape"})
            raise ValueError(f"Guardian rejected symlink escape: {rel}") from exc
    candidate = (root / source).resolve(strict=False) if not source.is_absolute() else source.resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        _audit(root, "guardian.path.reject", {"action": action, "path": str(candidate), "reason": "outside-project-root"})
        raise ValueError(f"Guardian rejected path outside project root: {candidate}") from exc
    _audit(root, "guardian.path.allow", {"action": action, "path": _relative(root, candidate)})
    return candidate


def _assert_no_symlink_escape(root: Path, path: Path, action: str) -> None:
    if not path.is_symlink():
        return
    target = path.resolve(strict=False)
    try:
        target.relative_to(root)
    except ValueError as exc:
        rel = _relative(root, path)
        _audit(root, "guardian.path.reject", {"action": action, "path": rel, "reason": "symlink-escape"})
        raise ValueError(f"Guardian rejected symlink escape: {rel}") from exc


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _config_path(root: Path) -> Path:
    return root / CONFIG_NAME


def _config_hash(root: Path) -> str | None:
    path = _config_path(root)
    if not path.exists():
        return None
    return _hash_bytes(path.read_bytes())


def _normalize_command(command: Any) -> list[str]:
    if isinstance(command, list) and all(isinstance(part, str) for part in command):
        return list(command)
    if isinstance(command, str):
        return shlex.split(command, posix=os.name != "nt")
    raise ValueError("Guardian validation commands must be strings or string lists")


def _load_working_config(root: Path) -> dict[str, Any]:
    path = _config_path(root)
    if not path.exists():
        return {
            "validation_commands": [],
            "auto_recover": False,
            "excludes": [],
        }
    _safe_resolve(root, path, "read-config")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("sona.guard.json must contain a JSON object")
    commands = [_normalize_command(item) for item in raw.get("validation_commands", [])]
    excludes = [str(item) for item in raw.get("excludes", [])]
    return {
        "validation_commands": commands,
        "auto_recover": bool(raw.get("auto_recover", False)),
        "excludes": excludes,
    }


def _load_trusted_config(root: Path) -> dict[str, Any]:
    return _read_json(
        _trusted_config_path(root),
        {
            "config_hash": None,
            "validation_commands": [],
            "auto_recover": False,
            "excludes": [],
        },
    )


def _load_baseline(root: Path) -> dict[str, Any] | None:
    return _read_json(_baseline_path(root), None)


def _circuit_status(root: Path) -> dict[str, Any]:
    return _read_json(_circuit_path(root), {"active": False})


def _set_circuit(root: Path, reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    state = {"active": True, "reason": reason, "timestamp": _now(), "payload": payload}
    _write_json(_circuit_path(root), state)
    _audit(root, "guardian.circuit.open", state)
    return state


def _inventory(root: Path, extra_excludes: list[str] | None = None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        safe = _safe_resolve(root, path, "inventory")
        rel = _relative(root, safe)
        if _is_excluded(rel, extra_excludes):
            continue
        if safe.is_dir():
            continue
        _assert_no_symlink_escape(root, safe, "inventory")
        records.append({
            "path": rel,
            "sha256": _hash_file(safe),
            "size": safe.stat().st_size,
        })
    return records


def _inventory_map(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["path"]: item for item in records}


def _diff_records(current: list[dict[str, Any]], trusted: list[dict[str, Any]]) -> dict[str, list[str]]:
    current_map = _inventory_map(current)
    trusted_map = _inventory_map(trusted)
    added = sorted(set(current_map) - set(trusted_map))
    missing = sorted(set(trusted_map) - set(current_map))
    changed = sorted(
        path for path in (set(current_map) & set(trusted_map))
        if current_map[path]["sha256"] != trusted_map[path]["sha256"]
    )
    return {"added": added, "missing": missing, "changed": changed}


def _snapshot_id(name: Any = None) -> str:
    suffix = str(name).strip().replace(" ", "-") if name else ""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{stamp}-{suffix}" if suffix else stamp


def _copy_project_file(root: Path, rel_path: str, destination_root: Path, action: str) -> dict[str, Any]:
    source = _safe_resolve(root, rel_path, action)
    _assert_no_symlink_escape(root, source, action)
    if not source.exists() or not source.is_file():
        return {"path": rel_path, "copied": False, "reason": "missing"}
    target = destination_root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return {"path": rel_path, "copied": True, "sha256": _hash_file(target), "size": target.stat().st_size}


def _latest_snapshot_id(root: Path) -> str | None:
    snapshots = _snapshot_root(root)
    if not snapshots.exists():
        return None
    candidates = sorted(path.name for path in snapshots.iterdir() if (path / "manifest.json").exists())
    return candidates[-1] if candidates else None


def _snapshot_manifest_path(root: Path, snapshot_id: str) -> Path:
    return _snapshot_root(root) / snapshot_id / "manifest.json"


def _load_snapshot(root: Path, snapshot_id: str | None = None) -> dict[str, Any]:
    selected = snapshot_id or _latest_snapshot_id(root)
    if not selected:
        raise ValueError("No Guardian snapshot is available")
    path = _snapshot_manifest_path(root, selected)
    if not path.exists():
        raise ValueError(f"Unknown Guardian snapshot: {selected}")
    return json.loads(path.read_text(encoding="utf-8"))


def _verify_snapshot_integrity(root: Path, snapshot: dict[str, Any]) -> dict[str, Any]:
    snapshot_dir = _snapshot_root(root) / snapshot["snapshot_id"] / "files"
    failed = []
    for item in snapshot.get("files", []):
        stored = snapshot_dir / item["path"]
        if not stored.exists() or _hash_file(stored) != item["sha256"]:
            failed.append(item["path"])
    return {"ok": not failed, "failed": failed}


def _write_baseline(root: Path, manifest: dict[str, Any]) -> None:
    baseline = {
        "version": STATE_VERSION,
        "created_at": manifest.get("created_at", _now()),
        "project_root": str(root),
        "excludes": manifest.get("excludes", list(DEFAULT_EXCLUDES)),
        "trusted_config_hash": manifest.get("trusted_config_hash"),
        "snapshot_id": manifest.get("snapshot_id"),
        "parg": manifest.get("parg", {"nodes": [], "edges": []}),
        "files": manifest.get("files", []),
    }
    _write_json(_baseline_path(root), baseline)


def _parg_graph(root: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = [{"id": item["path"], "sha256": item["sha256"], "size": item["size"]} for item in records]
    known = {item["path"] for item in records}
    edges = []
    for item in records:
        rel = item["path"]
        path = root / rel
        if path.suffix.lower() not in {".py", ".sona", ".smod", ".md", ".txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line in text.splitlines():
            stripped = line.strip()
            target = ""
            if stripped.startswith("import "):
                target = stripped.split()[1].replace(".", "/")
            elif stripped.startswith("from "):
                target = stripped.split()[1].replace(".", "/")
            elif stripped.startswith("use "):
                target = stripped.split()[1].replace(".", "/")
            elif stripped.startswith("# depends:"):
                target = stripped.split(":", 1)[1].strip()
            if not target:
                continue
            matches = [candidate for candidate in known if candidate.startswith(target) or candidate.endswith(target)]
            for match in matches[:5]:
                edges.append({"from": rel, "to": match, "type": "declared"})
    return {"nodes": nodes, "edges": edges}


def _run_validation_commands(root: Path, trusted_config: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for command in trusted_config.get("validation_commands", []):
        normalized = _normalize_command(command)
        started = time.perf_counter()
        proc = subprocess.run(
            normalized,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            timeout=120,
        )
        elapsed = round(time.perf_counter() - started, 3)
        result = {
            "command": normalized,
            "exit_code": proc.returncode,
            "duration_seconds": elapsed,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
        }
        _audit(root, "guardian.validation", result)
        results.append(result)
    return results


def _config_drift(root: Path, trusted_config: dict[str, Any]) -> dict[str, Any]:
    current_hash = _config_hash(root)
    trusted_hash = trusted_config.get("config_hash")
    drift = current_hash != trusted_hash
    return {
        "drift": drift,
        "trusted_hash": trusted_hash,
        "current_hash": current_hash,
    }


def guardian_status(project_root: Any = None) -> dict[str, Any]:
    root = _project_root(project_root)
    baseline = _load_baseline(root)
    circuit = _circuit_status(root)
    return {
        "project_root": str(root),
        "initialized": baseline is not None,
        "state_dir": str(_state_dir(root)),
        "snapshot_id": baseline.get("snapshot_id") if baseline else None,
        "circuit_breaker": circuit,
    }


def guardian_snapshot(project_root: Any = None, name: Any = None) -> dict[str, Any]:
    root = _project_root(project_root)
    trusted_config = _load_trusted_config(root)
    files = _inventory(root, trusted_config.get("excludes", []))
    snapshot_id = _snapshot_id(name)
    destination = _snapshot_root(root) / snapshot_id / "files"
    copied = [_copy_project_file(root, item["path"], destination, "snapshot") for item in files]
    manifest = {
        "version": STATE_VERSION,
        "snapshot_id": snapshot_id,
        "created_at": _now(),
        "project_root": str(root),
        "trusted_config_hash": trusted_config.get("config_hash"),
        "excludes": [*DEFAULT_EXCLUDES, *trusted_config.get("excludes", [])],
        "files": files,
        "copied": copied,
        "parg": _parg_graph(root, files),
    }
    _write_json(_snapshot_manifest_path(root, snapshot_id), manifest)
    _audit(root, "guardian.snapshot", {"snapshot_id": snapshot_id, "file_count": len(files)})
    return {"status": "snapshot-created", "snapshot_id": snapshot_id, "file_count": len(files)}


def guardian_init(project_root: Any = None) -> dict[str, Any]:
    root = _project_root(project_root)
    state = _state_dir(root)
    state.mkdir(parents=True, exist_ok=True)
    working_config = _load_working_config(root)
    trusted_config = {
        "version": STATE_VERSION,
        "created_at": _now(),
        "config_hash": _config_hash(root),
        "validation_commands": working_config["validation_commands"],
        "auto_recover": working_config["auto_recover"],
        "excludes": working_config["excludes"],
    }
    _write_json(_trusted_config_path(root), trusted_config)
    snapshot = guardian_snapshot(root, "baseline")
    manifest = _load_snapshot(root, snapshot["snapshot_id"])
    _write_baseline(root, manifest)
    _audit(root, "guardian.init", {"file_count": len(manifest["files"]), "snapshot_id": snapshot["snapshot_id"]})
    return {
        "status": "initialized",
        "project_root": str(root),
        "file_count": len(manifest["files"]),
        "snapshot_id": snapshot["snapshot_id"],
        "trusted_config_hash": trusted_config["config_hash"],
        "validation_commands": trusted_config["validation_commands"],
    }


def guardian_quarantine(project_root: Any = None, paths: Any = None, reason: Any = "manual") -> dict[str, Any]:
    root = _project_root(project_root)
    selected = [str(item) for item in paths] if isinstance(paths, list) else []
    if not selected:
        verify = guardian_verify(root)
        selected = sorted(set(verify.get("added", []) + verify.get("changed", [])))
        if verify.get("config_drift", {}).get("drift") and _config_path(root).exists():
            selected.append(CONFIG_NAME)
    quarantine_id = _snapshot_id(reason or "quarantine")
    destination = _quarantine_root(root) / quarantine_id / "files"
    records = []
    for rel_path in selected:
        if _is_excluded(rel_path):
            continue
        records.append(_copy_project_file(root, rel_path, destination, "quarantine"))
    manifest = {
        "version": STATE_VERSION,
        "quarantine_id": quarantine_id,
        "created_at": _now(),
        "reason": str(reason or "manual"),
        "files": records,
    }
    _write_json(_quarantine_root(root) / quarantine_id / "manifest.json", manifest)
    _audit(root, "guardian.quarantine", {"quarantine_id": quarantine_id, "paths": selected})
    return {"status": "quarantined", "quarantine_id": quarantine_id, "files": records}


def guardian_verify(project_root: Any = None, run_validation: Any = False) -> dict[str, Any]:
    root = _project_root(project_root)
    baseline = _load_baseline(root)
    if baseline is None:
        return {"status": "uninitialized", "project_root": str(root)}
    trusted_config = _load_trusted_config(root)
    current = _inventory(root, trusted_config.get("excludes", []))
    diff = _diff_records(current, baseline.get("files", []))
    config_drift = _config_drift(root, trusted_config)
    if config_drift["drift"] and _config_path(root).exists():
        guardian_quarantine(root, [CONFIG_NAME], "config-drift")
    validations = _run_validation_commands(root, trusted_config) if run_validation else []
    status = "ok" if not any(diff.values()) and not config_drift["drift"] else "drift"
    result = {
        "status": status,
        "project_root": str(root),
        "added": diff["added"],
        "missing": diff["missing"],
        "changed": diff["changed"],
        "config_drift": config_drift,
        "validation_results": validations,
        "policy_source": "trusted-baseline",
    }
    _audit(root, "guardian.verify", {
        "status": result["status"],
        "added": len(diff["added"]),
        "missing": len(diff["missing"]),
        "changed": len(diff["changed"]),
        "config_drift": config_drift["drift"],
    })
    return result


def guardian_diff(project_root: Any = None) -> dict[str, Any]:
    result = guardian_verify(project_root)
    return {
        "status": result.get("status"),
        "added": result.get("added", []),
        "missing": result.get("missing", []),
        "changed": result.get("changed", []),
        "config_drift": result.get("config_drift", {}),
    }


def guardian_rollback(project_root: Any = None, snapshot_id: Any = None) -> dict[str, Any]:
    root = _project_root(project_root)
    circuit = _circuit_status(root)
    if circuit.get("active"):
        return {"status": "blocked", "reason": "circuit-breaker-active", "circuit_breaker": circuit}
    snapshot = _load_snapshot(root, str(snapshot_id) if snapshot_id else None)
    integrity = _verify_snapshot_integrity(root, snapshot)
    if not integrity["ok"]:
        breaker = _set_circuit(root, "snapshot-integrity-failed", integrity)
        return {"status": "failed", "snapshot_id": snapshot["snapshot_id"], "circuit_breaker": breaker}
    before = guardian_verify(root)
    quarantine = guardian_quarantine(root, reason="pre-rollback")
    snapshot_files = _inventory_map(snapshot.get("files", []))
    snapshot_source = _snapshot_root(root) / snapshot["snapshot_id"] / "files"
    for rel_path, item in snapshot_files.items():
        target = _safe_resolve(root, rel_path, "rollback-restore")
        source = snapshot_source / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.guardian-restore")
        shutil.copy2(source, temporary)
        os.replace(temporary, target)
        if _hash_file(target) != item["sha256"]:
            breaker = _set_circuit(root, "restore-hash-mismatch", {"path": rel_path})
            return {"status": "failed", "snapshot_id": snapshot["snapshot_id"], "quarantine": quarantine, "circuit_breaker": breaker}
    for rel_path in before.get("added", []):
        target = _safe_resolve(root, rel_path, "rollback-remove-added")
        if target.exists() and target.is_file():
            target.unlink()
    _write_baseline(root, snapshot)
    trusted_config = _load_trusted_config(root)
    validations = _run_validation_commands(root, trusted_config)
    failed_validations = [item for item in validations if item["exit_code"] != 0]
    after = guardian_verify(root)
    if after.get("status") != "ok" or failed_validations:
        breaker = _set_circuit(root, "post-rollback-verification-failed", {"verify": after, "validation_results": validations})
        return {"status": "failed", "snapshot_id": snapshot["snapshot_id"], "quarantine": quarantine, "verify": after, "validation_results": validations, "circuit_breaker": breaker}
    _audit(root, "guardian.rollback", {"snapshot_id": snapshot["snapshot_id"], "quarantine_id": quarantine["quarantine_id"]})
    return {
        "status": "rolled-back",
        "snapshot_id": snapshot["snapshot_id"],
        "quarantine": quarantine,
        "verify": after,
        "validation_results": validations,
    }


def guardian_heal(project_root: Any = None, apply: Any = False) -> dict[str, Any]:
    root = _project_root(project_root)
    verify = guardian_verify(root)
    if verify.get("status") == "ok":
        return {"status": "ok", "message": "No Guardian drift detected.", "verify": verify}
    if not apply:
        return {
            "status": "recommend-apply",
            "message": "Guardian detected drift. Run `sona guard heal --apply` to quarantine and restore the last known-good snapshot.",
            "verify": verify,
        }
    return guardian_rollback(root)


def guardian_doctor(project_root: Any = None) -> dict[str, Any]:
    root = _project_root(project_root)
    status = guardian_status(root)
    status["default_excludes"] = list(DEFAULT_EXCLUDES)
    status["trusted_config"] = _load_trusted_config(root) if status["initialized"] else None
    status["message"] = (
        "Guardian is initialized and ready."
        if status["initialized"]
        else "Guardian is not initialized for this project."
    )
    return status


def guardian_graph(project_root: Any = None) -> dict[str, Any]:
    root = _project_root(project_root)
    trusted_config = _load_trusted_config(root)
    files = _inventory(root, trusted_config.get("excludes", []))
    graph = _parg_graph(root, files)
    _audit(root, "guardian.graph", {"nodes": len(graph["nodes"]), "edges": len(graph["edges"])})
    return graph


def guardian_audit_history(project_root: Any = None, limit: Any = 50) -> list[dict[str, Any]]:
    root = _project_root(project_root)
    path = _state_dir(root) / "audit" / "audit.jsonl"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines if line.strip()]
    return records[-int(limit or 50):]


def guardian_report_json(project_root: Any = None) -> dict[str, Any]:
    root = _project_root(project_root)
    return {
        "status": guardian_status(root),
        "verify": guardian_verify(root),
        "doctor": guardian_doctor(root),
    }


def guardian_report_plain(project_root: Any = None) -> str:
    report = guardian_report_json(project_root)
    verify = report["verify"]
    if verify.get("status") == "ok":
        return "Guardian status: ok. No drift detected."
    if verify.get("status") == "uninitialized":
        return "Guardian status: uninitialized. Run `sona guard init` for this project root."
    parts = [
        "Guardian status: drift detected.",
        f"Added files: {len(verify.get('added', []))}.",
        f"Changed files: {len(verify.get('changed', []))}.",
        f"Missing files: {len(verify.get('missing', []))}.",
    ]
    if verify.get("config_drift", {}).get("drift"):
        parts.append("Guardian config changed; trusted baseline policy remains in use.")
    parts.append("Run `sona guard heal --apply` to quarantine suspect state and restore the last known-good snapshot.")
    return " ".join(parts)


__all__ = [
    "guardian_audit_history",
    "guardian_diff",
    "guardian_doctor",
    "guardian_graph",
    "guardian_heal",
    "guardian_init",
    "guardian_quarantine",
    "guardian_report_json",
    "guardian_report_plain",
    "guardian_rollback",
    "guardian_snapshot",
    "guardian_status",
    "guardian_verify",
]
