"""Internal, approval-scoped patch application and bounded verification.

The public 0.15.3 task API remains preview-only.  This module is the shared
execution boundary for Guardian and future clients that already possess a
governance decision and a narrowly scoped approval.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
from dataclasses import replace
from pathlib import Path
from typing import Iterable

from .contracts import (
    ApprovalRecord,
    PatchFile,
    PatchSet,
    VerificationPlan,
    VerificationResult,
)
from .redaction import redact_text


class PatchValidationError(ValueError):
    """A proposed patch failed a deterministic safety check."""


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def patch_set_hash(patch_set: PatchSet) -> str:
    payload = {
        "files": [
            {
                "target_path": item.target_path,
                "original_hash": item.original_hash,
                "proposed_hash": item.proposed_hash,
                "operation": item.operation,
                "patch_size": item.patch_size,
                "content_hash": sha256_bytes((item.proposed_content or item.unified_diff).encode("utf-8")),
            }
            for item in patch_set.files
        ],
        "total_size": patch_set.total_size,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256_bytes(encoded)


def _canonical_target(workspace: Path, target_path: str) -> Path:
    relative = Path(target_path)
    if not str(target_path).strip() or relative in {Path("."), Path("")} or relative.is_absolute() or ".." in relative.parts:
        raise PatchValidationError(f"patch target must be workspace-relative: {target_path}")
    target = (workspace / relative).resolve(strict=False)
    if target == workspace:
        raise PatchValidationError("patch target must name a file inside the workspace")
    try:
        target.relative_to(workspace)
    except ValueError as exc:
        raise PatchValidationError(f"patch target escapes workspace: {target_path}") from exc
    # Resolve the nearest existing parent so directory symlinks cannot escape.
    parent = target.parent
    while not parent.exists() and parent != workspace:
        parent = parent.parent
    try:
        parent.resolve().relative_to(workspace)
    except ValueError as exc:
        raise PatchValidationError(f"patch target crosses a symlink outside workspace: {target_path}") from exc
    return target


_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _apply_unified_diff(original: str, unified_diff: str) -> str:
    """Apply a conventional unified diff after exact context validation."""
    source = original.splitlines(keepends=True)
    lines = unified_diff.splitlines(keepends=True)
    output: list[str] = []
    source_index = 0
    index = 0
    while index < len(lines) and not lines[index].startswith("@@ "):
        index += 1
    if index == len(lines):
        raise PatchValidationError("patch has no unified-diff hunks")
    while index < len(lines):
        match = _HUNK.match(lines[index].rstrip("\r\n"))
        if not match:
            raise PatchValidationError("invalid unified-diff hunk header")
        old_start = int(match.group(1)) - 1
        if old_start < source_index or old_start > len(source):
            raise PatchValidationError("unified-diff hunk is outside the source")
        output.extend(source[source_index:old_start])
        source_index = old_start
        index += 1
        while index < len(lines) and not lines[index].startswith("@@ "):
            line = lines[index]
            if line.startswith("\\ No newline at end of file"):
                index += 1
                continue
            marker, content = line[:1], line[1:]
            if marker == "+":
                output.append(content)
            elif marker in {" ", "-"}:
                if source_index >= len(source) or source[source_index] != content:
                    raise PatchValidationError("unified-diff context does not match the original file")
                if marker == " ":
                    output.append(content)
                source_index += 1
            else:
                raise PatchValidationError("invalid unified-diff line")
            index += 1
    output.extend(source[source_index:])
    return "".join(output)


def _approval_granted(approval: ApprovalRecord, task_id: str, digest: str) -> bool:
    approved = approval.status.lower() in {"approved", "granted"}
    scope = approval.scope in {task_id, f"task:{task_id}", f"patch:{digest}"}
    return bool(
        approval.required
        and approved
        and scope
        and approval.task_id == task_id
        and approval.patch_hash == digest
    )


def apply_patch_set(
    workspace: str | Path,
    task_id: str,
    patch_set: PatchSet,
    approval: ApprovalRecord,
    *,
    maximum_files: int = 10,
    maximum_patch_bytes: int = 100_000,
) -> PatchSet:
    """Validate and atomically apply an approved patch set inside *workspace*."""
    root = Path(workspace).resolve()
    if not root.is_dir():
        raise PatchValidationError(f"workspace does not exist: {root}")
    if len(patch_set.files) > maximum_files:
        raise PatchValidationError(f"patch exceeds the {maximum_files}-file limit")
    computed_size = sum(len((item.proposed_content or item.unified_diff).encode("utf-8")) for item in patch_set.files)
    if any(item.patch_size != len((item.proposed_content or item.unified_diff).encode("utf-8")) for item in patch_set.files):
        raise PatchValidationError("a patch file has an invalid byte count")
    if computed_size > maximum_patch_bytes or patch_set.total_size not in {0, computed_size}:
        raise PatchValidationError("patch byte total is invalid or exceeds policy")
    digest = patch_set_hash(patch_set)
    if not _approval_granted(approval, task_id, digest):
        raise PatchValidationError("approval is not granted for this task and patch hash")

    prepared: list[tuple[PatchFile, Path, bytes | None, bytes | None]] = []
    seen_targets: set[Path] = set()
    for item in patch_set.files:
        if item.operation not in {"create", "update", "delete"}:
            raise PatchValidationError(f"unsupported patch operation: {item.operation}")
        target = _canonical_target(root, item.target_path)
        if target in seen_targets:
            raise PatchValidationError(f"duplicate patch target: {item.target_path}")
        seen_targets.add(target)
        old = target.read_bytes() if target.is_file() else None
        if item.operation == "create" and old is not None:
            raise PatchValidationError(f"create target already exists: {item.target_path}")
        if item.operation == "create" and item.original_hash is not None:
            raise PatchValidationError(f"create target must not declare an original hash: {item.target_path}")
        if item.operation in {"update", "delete"} and old is None:
            raise PatchValidationError(f"patch target does not exist: {item.target_path}")
        if old is not None and item.original_hash != sha256_bytes(old):
            raise PatchValidationError(f"original hash mismatch: {item.target_path}")
        if item.operation == "delete":
            proposed = None
        elif item.proposed_content is not None:
            proposed = item.proposed_content.encode("utf-8")
        else:
            try:
                proposed = _apply_unified_diff((old or b"").decode("utf-8"), item.unified_diff).encode("utf-8")
            except UnicodeDecodeError as exc:
                raise PatchValidationError("unified diffs only support UTF-8 text files") from exc
        expected = sha256_bytes(proposed or b"")
        if item.proposed_hash != expected:
            raise PatchValidationError(f"proposed hash mismatch: {item.target_path}")
        prepared.append((item, target, old, proposed))

    changed: list[tuple[Path, bytes | None]] = []
    try:
        for item, target, old, proposed in prepared:
            changed.append((target, old))
            if proposed is None:
                target.unlink()
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_name(f".{target.name}.sona-patch-{os.getpid()}")
                temporary.write_bytes(proposed)
                os.replace(temporary, target)
                if sha256_bytes(target.read_bytes()) != item.proposed_hash:
                    raise PatchValidationError(f"post-write hash mismatch: {item.target_path}")
    except Exception:
        for target, old in reversed(changed):
            if old is None:
                target.unlink(missing_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(old)
        raise
    return PatchSet(tuple(replace(item, applied=True) for item in patch_set.files), computed_size)


def default_verification_prefixes() -> tuple[tuple[str, ...], ...]:
    executable = str(Path(sys.executable).resolve())
    return ((executable,), (executable, "-m", "sona"), (executable, "-m", "pytest"))


def _has_prefix(command: tuple[str, ...], prefixes: Iterable[tuple[str, ...]]) -> bool:
    def normalize(parts: tuple[str, ...]) -> tuple[str, ...]:
        if not parts:
            return parts
        executable = shutil.which(parts[0]) or str(Path(parts[0]).resolve())
        return (str(Path(executable).resolve()), *parts[1:])
    normalized = normalize(command)
    return any(len(normalized) >= len(prefix) and normalized[:len(prefix)] == normalize(prefix) for prefix in prefixes)


def run_verification(workspace: str | Path, plan: VerificationPlan) -> VerificationResult:
    root = Path(workspace).resolve()
    prefixes = plan.allowed_prefixes or default_verification_prefixes()
    allowed: list[bool] = []
    statuses: list[int | None] = []
    summaries: list[str] = []
    within_limits: list[bool] = []
    for command in plan.commands:
        command = tuple(command)
        is_allowed = bool(command) and _has_prefix(command, prefixes)
        allowed.append(is_allowed)
        if not is_allowed:
            statuses.append(None)
            within_limits.append(False)
            summaries.append(f"denied command prefix: {command[0] if command else '<empty>'}")
            continue
        try:
            process = subprocess.Popen(
                list(command), cwd=root, shell=False,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            captured = bytearray()
            exceeded = threading.Event()

            def read_output() -> None:
                assert process.stdout is not None
                while True:
                    chunk = process.stdout.read(16_384)
                    if not chunk:
                        return
                    remaining = plan.maximum_output_bytes - len(captured)
                    if remaining > 0:
                        captured.extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        exceeded.set()
                        if process.poll() is None:
                            process.terminate()
                        return

            reader = threading.Thread(target=read_output, name="sona-verification-output", daemon=True)
            reader.start()
            try:
                return_code = process.wait(timeout=plan.timeout_seconds)
                timed_out = False
            except subprocess.TimeoutExpired:
                timed_out = True
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                return_code = None
            reader.join(timeout=2)
            statuses.append(return_code)
            within_limits.append(not exceeded.is_set() and not timed_out)
            output = captured.decode("utf-8", errors="replace")
            if exceeded.is_set():
                output += "\n[output limit exceeded]"
            if timed_out:
                output += "\n[verification timed out]"
            summaries.append(redact_text(output))
        except subprocess.TimeoutExpired as exc:
            statuses.append(None)
            within_limits.append(False)
            partial = (exc.stdout or b"")[:plan.maximum_output_bytes]
            if isinstance(partial, bytes):
                partial = partial.decode("utf-8", errors="replace")
            summaries.append(redact_text(str(partial) + "\n[verification timed out]"))
    passed = bool(plan.commands) and all(allowed) and all(within_limits) and all(code == 0 for code in statuses)
    return VerificationResult(
        commands=plan.commands, allowed=tuple(allowed), exit_statuses=tuple(statuses),
        output_summary="\n".join(summaries), passed=passed,
        rollback_recommended=not passed,
    )
