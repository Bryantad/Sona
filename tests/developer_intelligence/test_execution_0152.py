from __future__ import annotations

import sys
from pathlib import Path

import pytest

from sona.developer_intelligence import (
    ApprovalRecord,
    PatchFile,
    PatchSet,
    VerificationPlan,
    apply_patch_set,
    patch_set_hash,
    run_verification,
)
from sona.developer_intelligence.execution import PatchValidationError, sha256_bytes


def _approved(task_id: str, patch_set: PatchSet) -> ApprovalRecord:
    digest = patch_set_hash(patch_set)
    return ApprovalRecord(
        required=True,
        status="granted",
        scope=f"task:{task_id}",
        task_id=task_id,
        patch_hash=digest,
    )


def test_patch_application_checks_scope_hashes_limits_and_post_write(tmp_path: Path):
    target = tmp_path / "example.sona"
    target.write_text('print("old")\n', encoding="utf-8")
    proposed = 'print("new")\n'
    item = PatchFile(
        target_path="example.sona",
        original_hash=sha256_bytes(target.read_bytes()),
        proposed_hash=sha256_bytes(proposed.encode()),
        unified_diff="",
        operation="update",
        patch_size=len(proposed.encode()),
        proposed_content=proposed,
    )
    patch_set = PatchSet(files=(item,), total_size=len(proposed.encode()))
    applied = apply_patch_set(tmp_path, "task-1", patch_set, _approved("task-1", patch_set))
    assert target.read_text(encoding="utf-8") == proposed
    assert applied.files[0].applied is True

    with pytest.raises(PatchValidationError, match="approval"):
        apply_patch_set(tmp_path, "other-task", patch_set, _approved("task-1", patch_set))


def test_patch_application_rejects_traversal_and_stale_original(tmp_path: Path):
    proposed = "safe\n"
    traversal = PatchFile(
        target_path="../outside.txt", original_hash=None,
        proposed_hash=sha256_bytes(proposed.encode()), unified_diff="",
        operation="create", patch_size=len(proposed), proposed_content=proposed,
    )
    patch_set = PatchSet((traversal,), len(proposed))
    with pytest.raises(PatchValidationError, match="workspace-relative"):
        apply_patch_set(tmp_path, "task", patch_set, _approved("task", patch_set))

    root_target = PatchFile(
        target_path=".", original_hash=None, proposed_hash=sha256_bytes(proposed.encode()),
        unified_diff="", operation="create", patch_size=len(proposed), proposed_content=proposed,
    )
    root_set = PatchSet((root_target,), len(proposed))
    with pytest.raises(PatchValidationError, match="workspace-relative|name a file"):
        apply_patch_set(tmp_path, "task", root_set, _approved("task", root_set))

    target = tmp_path / "stale.txt"
    target.write_text("current\n", encoding="utf-8")
    stale = PatchFile(
        target_path="stale.txt", original_hash=sha256_bytes(b"old\n"),
        proposed_hash=sha256_bytes(proposed.encode()), unified_diff="",
        operation="update", patch_size=len(proposed), proposed_content=proposed,
    )
    patch_set = PatchSet((stale,), len(proposed))
    with pytest.raises(PatchValidationError, match="original hash mismatch"):
        apply_patch_set(tmp_path, "task", patch_set, _approved("task", patch_set))


def test_unified_diff_application_and_verification_are_bounded(tmp_path: Path):
    target = tmp_path / "example.txt"
    target.write_bytes(b"one\ntwo\n")
    diff = "--- a/example.txt\n+++ b/example.txt\n@@ -1,2 +1,2 @@\n one\n-two\n+three\n"
    proposed = b"one\nthree\n"
    item = PatchFile(
        "example.txt", sha256_bytes(target.read_bytes()), sha256_bytes(proposed),
        diff, "update", len(diff.encode()),
    )
    patch_set = PatchSet((item,), len(diff.encode()))
    apply_patch_set(tmp_path, "task", patch_set, _approved("task", patch_set))
    assert target.read_bytes() == proposed

    plan = VerificationPlan(commands=((sys.executable, "-c", "print('token=secret-value')"),), maximum_output_bytes=8)
    result = run_verification(tmp_path, plan)
    assert result.passed is False
    assert len(result.output_summary) < 100
    assert "limit exceeded" in result.output_summary

    denied = run_verification(tmp_path, VerificationPlan(commands=(("definitely-not-approved", "--version"),)))
    assert denied.passed is False
    assert denied.allowed == (False,)
