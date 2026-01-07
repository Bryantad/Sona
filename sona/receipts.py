from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _git_info(repo_root: Path) -> dict[str, Any]:
    # Best-effort; never fail execution if git is missing.
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()

        dirty = (
            subprocess.call(
                ["git", "diff", "--quiet"],
                cwd=str(repo_root),
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )
            != 0
        )

        return {"git_commit": commit, "dirty": bool(dirty)}
    except Exception:
        return {"git_commit": None, "dirty": None}


def _utc_timestamp() -> str:
    # ISO-ish; not deterministic across runs (by design), but stable format.
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass(frozen=True)
class ReceiptConfig:
    receipt_version: str = "0.1"
    env_allowlist: tuple[str, ...] = ()
    include_lockfile: bool = True
    include_git: bool = True


def build_receipt(
    *,
    sona_version: str,
    entry_file: Path,
    project_root: Path,
    argv: list[str],
    exit_code: int,
    duration_ms: int,
    error_text: Optional[str],
    config: ReceiptConfig,
) -> dict[str, Any]:
    entry_file = entry_file.resolve()
    project_root = project_root.resolve()

    code_hash = _sha256_file(entry_file) if entry_file.exists() else None

    lock_path = project_root / "sona.lock.json"
    lock_exists = config.include_lockfile and lock_path.exists()
    lock_hash = _sha256_file(lock_path) if lock_exists else None

    env_out: dict[str, str] = {}
    for key in config.env_allowlist:
        if key in os.environ:
            env_out[key] = os.environ[key]

    git = _git_info(project_root) if config.include_git else {"git_commit": None, "dirty": None}

    receipt: dict[str, Any] = {
        "sona_version": str(sona_version),
        "receipt_version": str(config.receipt_version),
        "timestamp_utc": _utc_timestamp(),
        "code": {
            "entry_file": str(entry_file),
            "file_hash": code_hash,
            **git,
        },
        "dependencies": {
            "lockfile": str(lock_path) if lock_exists else None,
            "lock_hash": lock_hash,
        },
        "inputs": {
            "args": list(argv),
            "env_allowlist": env_out,
        },
        "execution": {
            "exit_code": int(exit_code),
            "duration_ms": int(duration_ms),
            "errors": [] if not error_text else [{"kind": "error", "text": str(error_text)}],
            "events": [
                {"t": 0, "kind": "start"},
                {"t": int(duration_ms), "kind": "end"},
            ],
        },
        "reproduce": {
            "command": f"sona run {entry_file.name}",
            "contract": None,
        },
    }

    return receipt


def write_receipt_json(receipt: dict[str, Any], out_path: Path) -> None:
    """
    Deterministic JSON serialization:
    - sorted keys
    - fixed indentation
    - LF newlines

    Atomic write to avoid partial receipts.
    """
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = (
        json.dumps(
            receipt,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )

    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp_path.write_text(payload, encoding="utf-8", newline="\n")
    tmp_path.replace(out_path)
