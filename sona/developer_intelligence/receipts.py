"""Schema-1 task receipts with canonical hashes and redaction."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .redaction import redact


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_task_receipt(
    request, result, *, policy_hash: str, started_at: str | None = None,
    completed_at: str | None = None, duration_ms: int = 0,
) -> dict[str, Any]:
    timestamp = started_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    finished = completed_at or timestamp
    context_payload = {
        "origin": request.context.origin,
        "target_files": list(request.target_files),
        "active_file": request.context.active_file,
        "selected_text_present": bool(request.context.selected_text),
        "selected_text_hash": _hash(request.context.selected_text or ""),
        "workspace_summary_hash": _hash(request.context.workspace_summary or ""),
    }
    patch_digest = None
    if result.patch_set:
        from .execution import patch_set_hash
        patch_digest = patch_set_hash(result.patch_set)
    payload = {
        "schema_version": 1, "task_id": request.task_id, "timestamp": timestamp,
        "started_at": timestamp, "completed_at": finished,
        "task_type": request.task_type.value, "provider": result.provider_id, "model": result.model_id,
        "local_execution": result.provider_id in {None, "deterministic", "ollama", "huggingface"},
        "prompt_hash": _hash(request.instruction),
        "response_hash": _hash(result.summary),
        "context_hash": _hash(json.dumps(context_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "context": {"origin": request.context.origin, "target_files": list(request.target_files), "selected_text_present": bool(request.context.selected_text)},
        "governance": list(result.governance_decisions), "approval": result.approval.to_dict() if result.approval else None,
        "files_proposed": [item.target_path for item in result.patch_set.files] if result.patch_set else [],
        "files_changed": [item.target_path for item in result.patch_set.files if item.applied] if result.patch_set else [],
        "post_write_hashes": {item.target_path: (None if item.operation == "delete" else item.proposed_hash) for item in result.patch_set.files if item.applied} if result.patch_set else {},
        "patch_hash": patch_digest,
        "verification": result.verification.to_dict() if result.verification else None,
        "duration_ms": int(duration_ms), "budget": result.budget.to_dict() if result.budget else None,
        "policy_hash": policy_hash, "status": result.status.value,
    }
    clean = redact(payload)
    clean["receipt_hash"] = _hash(json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    return clean


def write_receipt(receipt: dict[str, Any], path: str | Path) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    temp = destination.with_suffix(destination.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8", newline="\n")
    temp.replace(destination)
    return destination
