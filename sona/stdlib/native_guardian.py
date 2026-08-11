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
    ".sona/receipts/**",
    ".sona/governance/**",
]

CONFIG_NAME = "sona.guard.json"
STATE_VERSION = 1
NATIVE_PROOF_SCHEMA_ID = "sona.native-proof.schema-1"
GUARDIAN_PROOF_BINDING_SCHEMA_ID = "sona.guardian-proof-binding.schema-1"
GUARDIAN_PROOF_AI_REVIEW_SCHEMA_ID = "sona.guardian-proof-ai-review.schema-1"
MUTATING_ACTIONS = {"init", "snapshot", "quarantine", "rollback", "heal-apply", "proof-attest"}


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
    from sona.developer_intelligence.governance import load_policy, policy_hash
    from sona.developer_intelligence.redaction import redact
    policy, _source = load_policy(root)
    audit_dir = _state_dir(root) / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "schema_version": 1,
        "timestamp": _now(),
        "event": event,
        "policy_hash": policy_hash(policy),
        "payload": redact(payload),
    }
    with (audit_dir / "audit.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def _guardian_receipt(root: Path, action: str, result: dict[str, Any], authorization: dict[str, Any]) -> str:
    """Write a redacted schema-1 receipt for a canonical Guardian operation."""
    from sona.developer_intelligence.redaction import redact
    policy_digest = str(authorization.get("policy_hash") or "")
    post_write_hashes = dict(result.get("post_write_hashes", {}) or {})
    for removed in result.get("removed", []) or []:
        post_write_hashes[str(removed)] = None
    receipt = {
        "schema_version": 1,
        "receipt_type": "guardian",
        "timestamp": _now(),
        "task_id": f"guardian:{action}",
        "task_type": action,
        "status": str(result.get("status", "failed")),
        "policy_hash": policy_digest,
        "governance": authorization,
        "approval": {
            "status": "granted" if authorization.get("approval_granted") else "denied",
            "scope": authorization.get("approval_scope"),
        },
        "files_changed": sorted(set(
            list(result.get("restored", []) or [])
            + list(result.get("removed", []) or [])
            + list(result.get("files_changed", []) or [])
        )),
        "post_write_hashes": post_write_hashes,
        "output": str(result.get("reason") or result.get("message") or result.get("status", ""))[:4000],
    }
    clean = redact(receipt)
    encoded = json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    clean["receipt_hash"] = "sha256:" + hashlib.sha256(encoded).hexdigest()
    destination = _state_dir(root) / "receipts" / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{action}.json"
    _write_json(destination, clean)
    return str(destination)


def _valid_receipt_changed_paths(root: Path) -> dict[str, str | None]:
    expected: dict[str, str | None] = {}
    roots = [root / ".sona" / "receipts", _state_dir(root) / "receipts"]
    for receipt_root in roots:
        if not receipt_root.exists():
            continue
        for path in receipt_root.rglob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                supplied = data.pop("receipt_hash")
                encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
                if supplied != "sha256:" + hashlib.sha256(encoded).hexdigest():
                    continue
                approval = data.get("approval") or {}
                if str(approval.get("status", "")).lower() not in {"approved", "granted"}:
                    continue
                if data.get("receipt_type") == "guardian":
                    governance = data.get("governance") or {}
                    if not governance.get("authorized") or not str(approval.get("scope") or "").startswith("guardian:"):
                        continue
                else:
                    patch_digest = data.get("patch_hash")
                    task_id = data.get("task_id")
                    if not patch_digest or approval.get("patch_hash") != patch_digest or approval.get("task_id") != task_id:
                        continue
                    if approval.get("scope") not in {task_id, f"task:{task_id}", f"patch:{patch_digest}"}:
                        continue
                for changed in data.get("files_changed", []) or []:
                    candidate = _safe_resolve(root, str(changed), "receipt-classification", audit=False)
                    relative = _relative(root, candidate)
                    expected[relative] = (data.get("post_write_hashes") or {}).get(str(changed))
            except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
                continue
    return expected


def _safe_resolve(root: Path, path: Path | str, action: str, *, audit: bool = True) -> Path:
    root = root.resolve()
    source = Path(path)
    original = source if source.is_absolute() else root / source
    if original.is_symlink():
        target = original.resolve(strict=False)
        try:
            target.relative_to(root)
        except ValueError as exc:
            rel = original.relative_to(root).as_posix() if original.is_relative_to(root) else str(original)
            if audit:
                _audit(root, "guardian.path.reject", {"action": action, "path": rel, "reason": "symlink-escape"})
            raise ValueError(f"Guardian rejected symlink escape: {rel}") from exc
    candidate = (root / source).resolve(strict=False) if not source.is_absolute() else source.resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        if audit:
            _audit(root, "guardian.path.reject", {"action": action, "path": str(candidate), "reason": "outside-project-root"})
        raise ValueError(f"Guardian rejected path outside project root: {candidate}") from exc
    if audit:
        _audit(root, "guardian.path.allow", {"action": action, "path": _relative(root, candidate)})
    return candidate


def _assert_no_symlink_escape(root: Path, path: Path, action: str, *, audit: bool = True) -> None:
    if not path.is_symlink():
        return
    target = path.resolve(strict=False)
    try:
        target.relative_to(root)
    except ValueError as exc:
        rel = _relative(root, path)
        if audit:
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


def _sha256_label(value: bytes) -> str:
    return "sha256:" + _hash_bytes(value)


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


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
    state = {"schema_version": 1, "active": True, "reason": reason, "timestamp": _now(), "payload": payload}
    _write_json(_circuit_path(root), state)
    _audit(root, "guardian.circuit.open", state)
    return state


def _inventory(root: Path, extra_excludes: list[str] | None = None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        safe = _safe_resolve(root, path, "inventory", audit=False)
        rel = _relative(root, safe)
        if _is_excluded(rel, extra_excludes):
            continue
        if safe.is_dir():
            continue
        _assert_no_symlink_escape(root, safe, "inventory", audit=False)
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
        "schema_version": 1,
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


def _run_validation_commands(root: Path, trusted_config: dict[str, Any], *, audit: bool = True) -> list[dict[str, Any]]:
    from sona.developer_intelligence.redaction import redact_text
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
            "stdout": redact_text(proc.stdout[-4000:]),
            "stderr": redact_text(proc.stderr[-4000:]),
        }
        if audit:
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


def _accessibility_event(root: Path, action: str, result: dict[str, Any]) -> dict[str, Any]:
    """Publish Guardian context to stable in-memory accessibility helpers."""
    try:
        from . import native_accessibility as access
        from . import native_log
    except Exception:
        return {"available": False}

    status = str(result.get("status", "unknown"))
    fields = {
        "action": action,
        "status": status,
        "added": len(result.get("added", []) or []),
        "changed": len(result.get("changed", []) or []),
        "missing": len(result.get("missing", []) or []),
        "project_root": str(root),
    }
    access.contract_require(bool(root), "Guardian project root is required")
    boundary_ok = access.boundary_check("guardian", action)
    strict = access.strict_check({
        "side_effect": action in MUTATING_ACTIONS,
        "boundary": "guardian" if boundary_ok else "",
    })
    access.breadcrumb_add(f"guardian.{action}", fields)
    native_log.log_event(f"guardian.{action}", fields)
    certainty = None
    if status == "drift" or result.get("config_drift", {}).get("drift"):
        certainty = access.certainty_add(
            "guardian-drift",
            "Guardian detected project state drift.",
            "warning",
        )
    issue_chunks = access.chunk_items(
        [*result.get("added", []), *result.get("changed", []), *result.get("missing", [])],
        5,
    )
    explanation = access.explain_value({"action": action, "status": status})
    message = access.simplify_message(f"Guardian {action} finished with status {status}.")
    paced = access.pace_format(message)
    sensory = access.sensory_apply(paced)
    visible_events = access.noise_filter([{"scope": "guardian", "action": action, "status": status}])
    return {
        "available": True,
        "boundary_ok": boundary_ok,
        "strict": strict,
        "certainty": certainty,
        "issue_chunks": issue_chunks,
        "explanation": explanation,
        "message": sensory,
        "visible_events": visible_events,
    }


def guardian_status(project_root: Any = None) -> dict[str, Any]:
    root = _project_root(project_root)
    baseline = _load_baseline(root)
    circuit = _circuit_status(root)
    result = {
        "project_root": str(root),
        "initialized": baseline is not None,
        "state_dir": str(_state_dir(root)),
        "snapshot_id": baseline.get("snapshot_id") if baseline else None,
        "circuit_breaker": circuit,
    }
    result["accessibility"] = _accessibility_event(root, "status", result)
    return result


def guardian_snapshot(project_root: Any = None, name: Any = None) -> dict[str, Any]:
    root = _project_root(project_root)
    trusted_config = _load_trusted_config(root)
    files = _inventory(root, trusted_config.get("excludes", []))
    snapshot_id = _snapshot_id(name)
    destination = _snapshot_root(root) / snapshot_id / "files"
    copied = [_copy_project_file(root, item["path"], destination, "snapshot") for item in files]
    manifest = {
        "schema_version": 1,
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
    result = {"status": "snapshot-created", "snapshot_id": snapshot_id, "file_count": len(files)}
    result["accessibility"] = _accessibility_event(root, "snapshot", result)
    return result


def guardian_init(project_root: Any = None) -> dict[str, Any]:
    root = _project_root(project_root)
    state = _state_dir(root)
    state.mkdir(parents=True, exist_ok=True)
    working_config = _load_working_config(root)
    trusted_config = {
        "schema_version": 1,
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
    result = {
        "status": "initialized",
        "project_root": str(root),
        "file_count": len(manifest["files"]),
        "snapshot_id": snapshot["snapshot_id"],
        "trusted_config_hash": trusted_config["config_hash"],
        "validation_commands": trusted_config["validation_commands"],
    }
    result["accessibility"] = _accessibility_event(root, "init", result)
    return result


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
        "schema_version": 1,
        "version": STATE_VERSION,
        "quarantine_id": quarantine_id,
        "created_at": _now(),
        "reason": str(reason or "manual"),
        "files": records,
    }
    _write_json(_quarantine_root(root) / quarantine_id / "manifest.json", manifest)
    _audit(root, "guardian.quarantine", {"quarantine_id": quarantine_id, "paths": selected})
    result = {"status": "quarantined", "quarantine_id": quarantine_id, "files": records}
    result["accessibility"] = _accessibility_event(root, "quarantine", result)
    return result


def guardian_verify(project_root: Any = None, run_validation: Any = False) -> dict[str, Any]:
    root = _project_root(project_root)
    baseline = _load_baseline(root)
    if baseline is None:
        return {"status": "uninitialized", "project_root": str(root)}
    trusted_config = _load_trusted_config(root)
    current = _inventory(root, trusted_config.get("excludes", []))
    diff = _diff_records(current, baseline.get("files", []))
    config_drift = _config_drift(root, trusted_config)
    # Verification is strictly read-only. Config drift is reported and any
    # quarantine is deferred to an approved repair plan.
    validations = []
    if run_validation:
        validations = [
            {
                "schema_version": 1,
                "status": "not-executed",
                "diagnostic_id": "SONA-GUARD-003",
                "command": _normalize_command(command),
                "message": "guardian verify is read-only; trusted commands run only during approved recovery verification",
            }
            for command in trusted_config.get("validation_commands", [])
        ]
    status = "ok" if not any(diff.values()) and not config_drift["drift"] else "drift"
    drift_paths = sorted(set(diff["added"] + diff["missing"] + diff["changed"] + ([CONFIG_NAME] if config_drift["drift"] else [])))
    approved_paths = _valid_receipt_changed_paths(root)
    current_map = _inventory_map(current)
    expected = []
    suspicious = []
    for path in drift_paths:
        approved_hash = approved_paths.get(path, "__missing_receipt__")
        current_hash = current_map.get(path, {}).get("sha256")
        if isinstance(approved_hash, str) and approved_hash.startswith("sha256:"):
            approved_hash = approved_hash.split(":", 1)[1]
        matches_receipt = (
            path in approved_paths
            and ((approved_hash is None and current_hash is None) or approved_hash == current_hash)
        )
        (expected if matches_receipt else suspicious).append(path)
    result = {
        "status": status,
        "project_root": str(root),
        "added": diff["added"],
        "missing": diff["missing"],
        "changed": diff["changed"],
        "config_drift": config_drift,
        "validation_results": validations,
        "policy_source": "trusted-baseline",
        "drift_classification": {
            "expected": expected,
            "suspicious": suspicious,
            "classification": "suspicious" if suspicious else ("expected" if expected else "none"),
        },
    }
    result["accessibility"] = _accessibility_event(root, "verify", result)
    return result


def guardian_check(project_root: Any = None) -> dict[str, Any]:
    """Compatibility alias for read-only Guardian verification."""
    try:
        return guardian_verify(project_root)
    except ValueError as exc:
        return {
            "schema_version": 1,
            "status": "invalid-project-root",
            "diagnostic_id": "SONA-GUARD-001",
            "message": str(exc),
        }


def guardian_diff(project_root: Any = None) -> dict[str, Any]:
    result = guardian_verify(project_root)
    diff = {
        "status": result.get("status"),
        "added": result.get("added", []),
        "missing": result.get("missing", []),
        "changed": result.get("changed", []),
        "config_drift": result.get("config_drift", {}),
    }
    diff["accessibility"] = _accessibility_event(_project_root(project_root), "diff", diff)
    return diff


def _guardian_proof_rejection(reason: str, message: str, receipt_hash: str | None = None) -> dict[str, Any]:
    result = {
        "schema_version": 1,
        "status": "rejected",
        "reason": reason,
        "message": message,
    }
    if receipt_hash:
        result["receipt_hash"] = receipt_hash
    return result


def _guardian_proof_anchor(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a redacted anchor that matches Native Core's binding reader."""
    baseline_path = _baseline_path(root)
    trusted_config_path = _trusted_config_path(root)
    values: list[bytes] = []
    for path in (baseline_path, trusted_config_path):
        if path.is_symlink() or not path.is_file():
            raise ValueError("Guardian proof binding is unavailable")
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to(root):
            raise ValueError("Guardian proof binding is unavailable")
        values.append(path.read_bytes())
    baseline_bytes, trusted_config_bytes = values
    baseline = json.loads(baseline_bytes.decode("utf-8"))
    trusted_config = json.loads(trusted_config_bytes.decode("utf-8"))
    if not isinstance(baseline, dict) or not isinstance(trusted_config, dict):
        raise ValueError("Guardian proof binding is unavailable")
    if baseline.get("schema_version") != 1 or trusted_config.get("schema_version") != 1:
        raise ValueError("Guardian proof binding is unavailable")
    snapshot_id = baseline.get("snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError("Guardian proof binding is unavailable")
    if (
        "trusted_config_hash" not in baseline
        or "config_hash" not in trusted_config
        or baseline["trusted_config_hash"] != trusted_config["config_hash"]
    ):
        raise ValueError("Guardian proof binding is unavailable")
    return {
        "schema_id": GUARDIAN_PROOF_BINDING_SCHEMA_ID,
        "baseline_snapshot_id": snapshot_id,
        "baseline_sha256": _sha256_label(baseline_bytes),
        "trusted_config_sha256": _sha256_label(trusted_config_bytes),
        "program_baseline": "tracked",
    }, baseline


def _is_sha256_label(value: Any) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    digest = value.removeprefix("sha256:")
    return len(digest) == 64 and all(character in "0123456789abcdef" for character in digest)


def guardian_proof_verify(project_root: Any = None, receipt_path: Any = None) -> dict[str, Any]:
    """Verify a Native Proof receipt against this Guardian's trusted baseline.

    The check is read-only. It validates the canonical receipt hash, Native
    Core identity, redacted Guardian anchor, and the program's baseline hash;
    it intentionally does not persist the receipt or its source path.
    """
    root = _project_root(project_root)
    try:
        anchor, baseline = _guardian_proof_anchor(root)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return _guardian_proof_rejection(
            "guardian-unavailable",
            "Guardian is not initialized with a consistent trusted baseline.",
        )

    if receipt_path is None or not str(receipt_path).strip():
        return _guardian_proof_rejection("invalid-receipt", "Provide a Native Proof receipt path.")
    try:
        path = Path(str(receipt_path)).expanduser()
        if path.is_symlink() or not path.is_file():
            return _guardian_proof_rejection("invalid-receipt", "Provide a regular Native Proof receipt file.")
        raw = path.read_bytes()
        receipt = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return _guardian_proof_rejection("invalid-receipt", "The Native Proof receipt could not be read safely.")
    if not isinstance(receipt, dict):
        return _guardian_proof_rejection("invalid-receipt", "The Native Proof receipt must contain a JSON object.")

    canonical = _canonical_json_bytes(receipt)
    if raw not in {canonical, canonical + b"\n"}:
        return _guardian_proof_rejection(
            "receipt-not-canonical",
            "The Native Proof receipt is not stored in canonical form.",
        )
    unsigned = dict(receipt)
    receipt_hash = unsigned.pop("receipt_hash", None)
    if not _is_sha256_label(receipt_hash) or receipt_hash != _sha256_label(_canonical_json_bytes(unsigned)):
        return _guardian_proof_rejection(
            "receipt-hash-mismatch",
            "The Native Proof receipt hash does not match its canonical contents.",
        )

    engine = receipt.get("engine")
    if (
        receipt.get("schema_id") != NATIVE_PROOF_SCHEMA_ID
        or receipt.get("schema") != 1
        or receipt.get("receipt_type") != "native_execution_proof"
        or not isinstance(engine, dict)
        or engine.get("name") != "native"
        or engine.get("python_required") is not False
        or engine.get("python_embedded") is not False
        or engine.get("fallback_used") is not False
    ):
        return _guardian_proof_rejection(
            "unsupported-receipt",
            "The receipt is not a Native Core Proof Mode schema-1 receipt.",
            receipt_hash,
        )

    execution = receipt.get("execution")
    if not isinstance(execution, dict):
        return _guardian_proof_rejection("invalid-receipt", "The Native Proof receipt has no execution record.", receipt_hash)
    execution_status = execution.get("status")
    exit_code = execution.get("exit_code")
    if (
        execution_status not in {"ok", "failed"}
        or not isinstance(exit_code, int)
        or isinstance(exit_code, bool)
        or (execution_status == "ok" and exit_code != 0)
        or (execution_status == "failed" and exit_code != 1)
    ):
        return _guardian_proof_rejection("invalid-receipt", "The Native Proof execution record is inconsistent.", receipt_hash)

    binding = receipt.get("guardian")
    if not isinstance(binding, dict):
        return _guardian_proof_rejection(
            "unbound-receipt",
            "The Native Proof receipt was not created with --guardian-root.",
            receipt_hash,
        )
    if any(binding.get(key) != value for key, value in anchor.items()):
        return _guardian_proof_rejection(
            "guardian-binding-mismatch",
            "The Native Proof receipt is bound to a different Guardian baseline.",
            receipt_hash,
        )

    program = receipt.get("program")
    if not isinstance(program, dict) or program.get("kind") not in {"source", "sbc"}:
        return _guardian_proof_rejection("invalid-receipt", "The Native Proof program identity is invalid.", receipt_hash)
    source = program.get("source")
    if not isinstance(source, dict) or not _is_sha256_label(source.get("sha256")):
        return _guardian_proof_rejection("invalid-receipt", "The Native Proof source identity is invalid.", receipt_hash)
    program_hash = source["sha256"]
    if program["kind"] == "sbc":
        container = program.get("container")
        if not isinstance(container, dict) or not _is_sha256_label(container.get("sha256")):
            return _guardian_proof_rejection("invalid-receipt", "The Native Proof container identity is invalid.", receipt_hash)
        program_hash = container["sha256"]
    baseline_files = baseline.get("files", [])
    if not isinstance(baseline_files, list):
        return _guardian_proof_rejection("guardian-unavailable", "Guardian baseline inventory is invalid.", receipt_hash)
    baseline_hashes = {
        "sha256:" + item["sha256"]
        for item in baseline_files
        if isinstance(item, dict) and isinstance(item.get("sha256"), str)
    }
    if program_hash not in baseline_hashes:
        return _guardian_proof_rejection(
            "program-not-baseline-tracked",
            "The proven program is not present in this Guardian baseline.",
            receipt_hash,
        )

    result = {
        "schema_version": 1,
        "status": "verified",
        "receipt_hash": receipt_hash,
        "execution": {"status": execution_status, "exit_code": exit_code},
        "guardian": anchor,
        "message": "Native Proof receipt matches this Guardian baseline.",
    }
    result["accessibility"] = _accessibility_event(root, "proof-verify", result)
    return result


def guardian_proof_review(
    project_root: Any = None,
    receipt_path: Any = None,
    provider: Any = None,
    model: Any = None,
    allow_network: Any = False,
) -> dict[str, Any]:
    """Run governed advisory analysis over verified, redacted Proof facts only.

    AI is deliberately outside the trust chain: it cannot verify, attest, or
    mutate the receipt. Provider routing receives no project path, receipt
    path, source, program path, stdout, stderr, environment, or credentials.
    """
    root = _project_root(project_root)
    verified = guardian_proof_verify(root, receipt_path)
    if verified.get("status") != "verified":
        return verified

    receipt_hash = verified["receipt_hash"]
    locally_attested = any(
        record.get("payload", {}).get("receipt_hash") == receipt_hash
        for record in guardian_proof_history(root, 100_000)
        if isinstance(record.get("payload"), dict)
    )
    evidence = {
        "schema_id": GUARDIAN_PROOF_AI_REVIEW_SCHEMA_ID,
        "proof_status": "verified",
        "receipt_hash": receipt_hash,
        "execution": verified["execution"],
        "guardian": verified["guardian"],
        "local_attestation_recorded": locally_attested,
    }
    review_input = _canonical_json_bytes(evidence)

    from sona.developer_intelligence import (
        ContextEnvelope,
        DeveloperIntelligenceService,
        TaskConstraints,
        TaskRequest,
        TaskType,
    )

    provider_id = str(provider).strip() if provider is not None and str(provider).strip() else None
    model_id = str(model).strip() if model is not None and str(model).strip() else None
    request = TaskRequest(
        task_type=TaskType.REVIEW,
        instruction=(
            "Review this verified Sona Native Proof evidence as an advisory analyst. "
            "State the execution outcome, Guardian baseline binding, and local attestation status. "
            "Explicitly state that AI does not verify, sign, attest, or add trust to the receipt. "
            "Do not infer source, paths, output content, identity, machine integrity, remote "
            "attestation, or facts absent from the evidence packet."
        ),
        provider_id=provider_id,
        model_id=model_id,
        context=ContextEnvelope(
            selected_text=review_input.decode("utf-8"),
            origin="guardian-proof-review",
            redacted_context=(
                "project_root",
                "receipt_path",
                "program_path",
                "program_source",
                "stdout",
                "stderr",
                "environment",
            ),
            omitted_context=("workspace_files", "selected_source", "output_bodies"),
        ),
        constraints=TaskConstraints(
            read_only=True,
            allow_file_writes=False,
            allow_shell=False,
            allow_network=bool(allow_network),
            maximum_files=1,
            maximum_context_tokens=4096,
        ),
        governance_metadata={
            "guardian_proof_review": True,
            "trust_boundary": "advisory-only",
            "network_explicitly_allowed": bool(allow_network),
        },
    )
    reviewed = DeveloperIntelligenceService(root).execute(request, write_task_receipt=False)
    reviewer = {
        "provider_id": reviewed.provider_id,
        "model_id": reviewed.model_id,
        "advisory": True,
    }
    boundary = (
        "AI analysis is advisory and is not part of the Proof receipt, Guardian verification, "
        "or Guardian attestation."
    )
    if reviewed.status.value != "ok":
        result = {
            "schema_version": 1,
            "schema_id": GUARDIAN_PROOF_AI_REVIEW_SCHEMA_ID,
            "status": "review-unavailable",
            "reason": reviewed.status.value.replace("_", "-"),
            "receipt_hash": receipt_hash,
            "proof_status": "verified",
            "review_input_hash": _sha256_label(review_input),
            "reviewer": reviewer,
            "message": "The proof remains verified, but governed AI review was not produced.",
            "trust_boundary": boundary,
        }
        result["accessibility"] = _accessibility_event(root, "proof-review", result)
        return result

    result = {
        "schema_version": 1,
        "schema_id": GUARDIAN_PROOF_AI_REVIEW_SCHEMA_ID,
        "status": "reviewed",
        "receipt_hash": receipt_hash,
        "proof_status": "verified",
        "review_input_hash": _sha256_label(review_input),
        "evidence": evidence,
        "reviewer": reviewer,
        "review": str(reviewed.summary),
        "trust_boundary": boundary,
    }
    result["accessibility"] = _accessibility_event(root, "proof-review", result)
    return result


def guardian_proof_attest(project_root: Any = None, receipt_path: Any = None) -> dict[str, Any]:
    """Record a successful, Guardian-bound Native Proof after a clean verify."""
    root = _project_root(project_root)
    verified = guardian_proof_verify(root, receipt_path)
    if verified.get("status") != "verified":
        return verified
    if verified["execution"]["status"] != "ok":
        return _guardian_proof_rejection(
            "execution-not-successful",
            "Only a successful Native Proof execution can be attested.",
            verified["receipt_hash"],
        )
    project_verify = guardian_verify(root)
    if project_verify.get("status") != "ok":
        return _guardian_proof_rejection(
            "guardian-drift",
            "Guardian detected project drift; restore a clean baseline before attesting this proof.",
            verified["receipt_hash"],
        ) | {
            "drift": {
                "added": len(project_verify.get("added", [])),
                "changed": len(project_verify.get("changed", [])),
                "missing": len(project_verify.get("missing", [])),
            }
        }

    anchor = verified["guardian"]
    _audit(root, "guardian.proof.attest", {
        "receipt_hash": verified["receipt_hash"],
        "execution_status": "ok",
        "baseline_snapshot_id": anchor["baseline_snapshot_id"],
        "baseline_sha256": anchor["baseline_sha256"],
        "trusted_config_sha256": anchor["trusted_config_sha256"],
        "program_baseline": "tracked",
    })
    result = {
        "schema_version": 1,
        "status": "attested",
        "receipt_hash": verified["receipt_hash"],
        "guardian": anchor,
        "message": "Guardian recorded the successful Native Proof against its clean trusted baseline.",
    }
    result["accessibility"] = _accessibility_event(root, "proof-attest", result)
    return result


def guardian_proof_history(project_root: Any = None, limit: Any = 50) -> list[dict[str, Any]]:
    """Return local Guardian audit entries for Native Proof attestations only."""
    root = _project_root(project_root)
    requested = max(0, int(limit or 50))
    records = [
        record for record in guardian_audit_history(root, 100_000)
        if record.get("event") == "guardian.proof.attest"
    ]
    return records[-requested:] if requested else []


def guardian_rollback(
    project_root: Any = None,
    snapshot_id: Any = None,
    *,
    dry_run: Any = True,
    approved: Any = False,
    authorization: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = _project_root(project_root)

    def finish(result: dict[str, Any]) -> dict[str, Any]:
        if authorization is not None:
            result["receipt_path"] = _guardian_receipt(root, "rollback", result, authorization)
        return result

    if authorization is not None and not authorization.get("authorized"):
        return finish({
            "schema_version": 1, "status": "denied",
            "reason": str(authorization.get("reason") or "Guardian mutation was denied by governance."),
            "governance": authorization,
        })
    circuit = _circuit_status(root)
    if circuit.get("active"):
        result = {"status": "blocked", "reason": "circuit-breaker-active", "circuit_breaker": circuit}
        result["accessibility"] = _accessibility_event(root, "rollback", result)
        return finish(result)
    snapshot = _load_snapshot(root, str(snapshot_id) if snapshot_id else None)
    integrity = _verify_snapshot_integrity(root, snapshot)
    if not integrity["ok"]:
        breaker = _set_circuit(root, "snapshot-integrity-failed", integrity)
        result = {"status": "failed", "snapshot_id": snapshot["snapshot_id"], "circuit_breaker": breaker}
        result["accessibility"] = _accessibility_event(root, "rollback", result)
        return finish(result)
    before = guardian_verify(root)
    plan = {
        "schema_version": 1,
        "summary": "Restore the selected Guardian snapshot.",
        "snapshot_id": snapshot["snapshot_id"],
        "files_to_restore": [item["path"] for item in snapshot.get("files", [])],
        "files_to_remove": list(before.get("added", [])),
        "required_capabilities": ["write_workspace", "execute_code"],
        "approval_required": True,
    }
    if dry_run or not approved:
        return finish({
            "schema_version": 1,
            "status": "dry-run" if dry_run else "approval-required",
            "plan": plan,
            "governance": {"decision": "require_approval", "blocked": True},
        })
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
            result = {"status": "failed", "snapshot_id": snapshot["snapshot_id"], "quarantine": quarantine, "circuit_breaker": breaker}
            result["accessibility"] = _accessibility_event(root, "rollback", result)
            return finish(result)
    removed = list(before.get("added", []))
    for rel_path in removed:
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
        result = {"status": "failed", "snapshot_id": snapshot["snapshot_id"], "quarantine": quarantine, "verify": after, "validation_results": validations, "circuit_breaker": breaker}
        result["accessibility"] = _accessibility_event(root, "rollback", result)
        return finish(result)
    _audit(root, "guardian.rollback", {"snapshot_id": snapshot["snapshot_id"], "quarantine_id": quarantine["quarantine_id"]})
    restored = [item["path"] for item in snapshot.get("files", [])]
    post_hashes = {
        item["path"]: _hash_file(_safe_resolve(root, item["path"], "rollback-post-hash"))
        for item in snapshot.get("files", [])
    }
    result = {
        "schema_version": 1,
        "status": "rolled-back",
        "snapshot_id": snapshot["snapshot_id"],
        "quarantine": quarantine,
        "verify": after,
        "validation_results": validations,
        "restored": restored,
        "removed": removed,
        "post_write_hashes": post_hashes,
    }
    result["accessibility"] = _accessibility_event(root, "rollback", result)
    return finish(result)


def guardian_heal(project_root: Any = None, apply: Any = False, approved: Any = False, authorization: dict[str, Any] | None = None) -> dict[str, Any]:
    root = _project_root(project_root)
    verify = guardian_verify(root)
    if verify.get("status") == "ok":
        result = {"status": "ok", "message": "No Guardian drift detected.", "verify": verify}
        result["accessibility"] = _accessibility_event(root, "heal", result)
        return result
    if not apply:
        result = {
            "status": "recommend-apply",
            "message": "Guardian detected drift. Review the plan, then run `sona guardian heal --apply --approve`.",
            "verify": verify,
            "plan": guardian_rollback(root, dry_run=True).get("plan"),
        }
        result["accessibility"] = _accessibility_event(root, "heal", result)
        return result
    return guardian_rollback(root, dry_run=False, approved=approved, authorization=authorization)


guardian_repair = guardian_heal


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
    status["accessibility"] = _accessibility_event(root, "doctor", status)
    return status


def guardian_graph(project_root: Any = None) -> dict[str, Any]:
    root = _project_root(project_root)
    trusted_config = _load_trusted_config(root)
    files = _inventory(root, trusted_config.get("excludes", []))
    graph = _parg_graph(root, files)
    _audit(root, "guardian.graph", {"nodes": len(graph["nodes"]), "edges": len(graph["edges"])})
    graph["accessibility"] = _accessibility_event(root, "graph", {"status": "ok"})
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
        "proof_attestations": guardian_proof_history(root, 10),
    }


def guardian_report_plain(project_root: Any = None) -> str:
    report = guardian_report_json(project_root)
    verify = report["verify"]
    if verify.get("status") == "ok":
        attestations = report.get("proof_attestations", [])
        if attestations:
            return f"Guardian status: ok. No drift detected. {len(attestations)} Native Proof receipt(s) attested."
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
    "guardian_check",
    "guardian_diff",
    "guardian_doctor",
    "guardian_graph",
    "guardian_heal",
    "guardian_init",
    "guardian_proof_attest",
    "guardian_proof_history",
    "guardian_proof_review",
    "guardian_proof_verify",
    "guardian_quarantine",
    "guardian_report_json",
    "guardian_report_plain",
    "guardian_rollback",
    "guardian_repair",
    "guardian_snapshot",
    "guardian_status",
    "guardian_verify",
]
