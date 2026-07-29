import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from sona.developer_intelligence import ApprovalRecord, PatchFile, PatchSet, TaskRequest, TaskResult, TaskStatus, TaskType
from sona.developer_intelligence.governance import authorize_mutation, load_policy
from sona.developer_intelligence.receipts import build_task_receipt, write_receipt
from sona.developer_intelligence.execution import patch_set_hash, sha256_bytes

from sona.interpreter import SonaUnifiedInterpreter
from sona.stdlib import native_accessibility
from sona.stdlib import native_guardian as guardian
from sona.stdlib import native_log


ROOT = Path(__file__).resolve().parents[2]


def call(fn, *args):
    if hasattr(fn, "call"):
        return fn.call(list(args), {})
    return fn(*args)


def make_project(tmp_path: Path) -> Path:
    project = tmp_path / "guardian-fixture"
    project.mkdir()
    (project / "app.sona").write_text('print("hello")\n', encoding="utf-8")
    (project / "lib.py").write_text("import app\n", encoding="utf-8")
    (project / "sona.guard.json").write_text(
        json.dumps(
            {
                "validation_commands": [
                    [sys.executable, "-c", "from pathlib import Path; assert Path('app.sona').exists()"]
                ],
                "auto_recover": False,
            }
        ),
        encoding="utf-8",
    )
    return project


def test_guardian_lifecycle_quarantine_and_rollback(tmp_path):
    project = make_project(tmp_path)

    initialized = guardian.guardian_init(project)
    assert initialized["status"] == "initialized"
    assert initialized["file_count"] >= 3
    snapshot_id = initialized["snapshot_id"]

    assert guardian.guardian_status(project)["initialized"] is True
    assert guardian.guardian_verify(project)["status"] == "ok"
    assert guardian.guardian_graph(project)["nodes"]
    assert "No drift" in guardian.guardian_report_plain(project)

    (project / "app.sona").write_text('print("changed")\n', encoding="utf-8")
    (project / "new.txt").write_text("new\n", encoding="utf-8")
    drift = guardian.guardian_verify(project)
    assert drift["status"] == "drift"
    assert "app.sona" in drift["changed"]
    assert "new.txt" in drift["added"]

    recommendation = guardian.guardian_heal(project)
    assert recommendation["status"] == "recommend-apply"

    quarantine = guardian.guardian_quarantine(project, ["app.sona", "new.txt"], "test")
    assert quarantine["status"] == "quarantined"
    assert all(item["copied"] for item in quarantine["files"])

    rollback = guardian.guardian_rollback(project, snapshot_id, dry_run=False, approved=True)
    assert rollback["status"] == "rolled-back"
    assert (project / "app.sona").read_text(encoding="utf-8") == 'print("hello")\n'
    assert not (project / "new.txt").exists()
    assert guardian.guardian_verify(project)["status"] == "ok"
    assert any(item["event"] == "guardian.rollback" for item in guardian.guardian_audit_history(project, 200))


def test_guardian_config_drift_uses_trusted_validation_policy(tmp_path):
    project = make_project(tmp_path)
    guardian.guardian_init(project)
    config = project / "sona.guard.json"
    config.write_text(
        json.dumps(
            {
                "validation_commands": [[sys.executable, "-c", "raise SystemExit(99)"]],
                "auto_recover": True,
            }
        ),
        encoding="utf-8",
    )

    result = guardian.guardian_verify(project, run_validation=True)
    assert result["status"] == "drift"
    assert result["config_drift"]["drift"] is True
    assert result["validation_results"]
    assert result["validation_results"][0]["status"] == "not-executed"
    assert result["validation_results"][0]["diagnostic_id"] == "SONA-GUARD-003"
    assert "SystemExit(99)" not in " ".join(result["validation_results"][0]["command"])
    assert not any(item["event"] == "guardian.quarantine" for item in guardian.guardian_audit_history(project, 200))
    assert config.exists(), "read-only verification must not quarantine project files"


def test_guardian_verify_does_not_write_project_or_guardian_state(tmp_path):
    project = make_project(tmp_path)
    guardian.guardian_init(project)
    before = {path.relative_to(project).as_posix(): path.read_bytes() for path in project.rglob("*") if path.is_file()}
    assert guardian.guardian_verify(project)["status"] == "ok"
    after = {path.relative_to(project).as_posix(): path.read_bytes() for path in project.rglob("*") if path.is_file()}
    assert after == before


def test_guardian_canonical_mutation_requires_enforcing_policy_and_writes_receipt(tmp_path):
    project = make_project(tmp_path)
    initialized = guardian.guardian_init(project)
    snapshot_id = initialized["snapshot_id"]
    (project / "app.sona").write_text('print("changed")\n', encoding="utf-8")

    policy, source = load_policy(project)
    denied = authorize_mutation(
        policy, source=source, task_type="guardian_rollback",
        capabilities=("write_workspace", "execute_code"), approval_granted=True,
        approval_scope=f"guardian:rollback:{project.resolve()}",
    )
    result = guardian.guardian_rollback(project, snapshot_id, dry_run=False, approved=True, authorization=denied)
    assert result["status"] == "denied"
    assert Path(result["receipt_path"]).exists()
    assert "changed" in (project / "app.sona").read_text(encoding="utf-8")

    governance_dir = project / ".sona"
    governance_dir.mkdir(exist_ok=True)
    enforcing = json.loads(json.dumps(policy))
    enforcing["mode"] = "enforce"
    (governance_dir / "governance.json").write_text(json.dumps(enforcing), encoding="utf-8")
    authorization = authorize_mutation(
        enforcing, source=str(governance_dir / "governance.json"), task_type="guardian_rollback",
        capabilities=("write_workspace", "execute_code"), approval_granted=True,
        approval_scope=f"guardian:rollback:{project.resolve()}",
    )
    result = guardian.guardian_rollback(project, snapshot_id, dry_run=False, approved=True, authorization=authorization)
    assert result["status"] == "rolled-back"
    receipt = json.loads(Path(result["receipt_path"]).read_text(encoding="utf-8"))
    assert receipt["schema_version"] == 1
    assert receipt["approval"]["status"] == "granted"
    assert receipt["policy_hash"] == authorization["policy_hash"]


def test_guardian_classifies_approved_receipt_drift_as_expected(tmp_path):
    project = make_project(tmp_path)
    guardian.guardian_init(project)
    target = project / "app.sona"
    target.write_text('print("approved")\n', encoding="utf-8")
    patch = PatchFile(
        target_path="app.sona", original_hash="sha256:old", proposed_hash=sha256_bytes(target.read_bytes()),
        unified_diff="", operation="update", patch_size=1, applied=True,
    )
    patch_set = PatchSet((patch,), 1)
    approval = ApprovalRecord(required=True, status="granted", scope="task:approved", task_id="approved", patch_hash=patch_set_hash(patch_set))
    request = TaskRequest(TaskType.EDIT, "approved edit", task_id="approved")
    result = TaskResult(
        "approved", TaskType.EDIT, TaskStatus.OK, "applied",
        patch_set=patch_set, approval=approval,
    )
    receipt = build_task_receipt(request, result, policy_hash="sha256:policy", started_at="2026-01-01T00:00:00Z")
    write_receipt(receipt, project / ".sona" / "receipts" / "tasks" / "approved.json")
    verified = guardian.guardian_verify(project)
    assert verified["drift_classification"]["expected"] == ["app.sona"]
    assert "app.sona" not in verified["drift_classification"]["suspicious"]
    target.write_text('print("different-later")\n', encoding="utf-8")
    later = guardian.guardian_verify(project)
    assert "app.sona" in later["drift_classification"]["suspicious"]


def test_canonical_guardian_cli_enforces_governance_before_apply(tmp_path):
    project = make_project(tmp_path)
    snapshot_id = guardian.guardian_init(project)["snapshot_id"]
    (project / "app.sona").write_text('print("changed")\n', encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    command = [
        sys.executable, "-m", "sona", "guardian", "rollback",
        "--project-root", str(project), "--snapshot-id", snapshot_id,
        "--apply", "--approve",
    ]
    denied = subprocess.run(command, cwd=project, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert denied.returncode == 1
    assert json.loads(denied.stdout)["status"] == "denied"

    policy, _ = load_policy(project)
    policy["mode"] = "enforce"
    (project / ".sona" / "governance.json").write_text(json.dumps(policy), encoding="utf-8")
    allowed = subprocess.run(command, cwd=project, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert allowed.returncode == 0, allowed.stderr or allowed.stdout
    payload = json.loads(allowed.stdout)
    assert payload["status"] == "rolled-back"
    assert Path(payload["receipt_path"]).exists()


def test_guardian_publishes_accessibility_context(tmp_path):
    project = make_project(tmp_path)
    native_accessibility.breadcrumb_clear()
    native_accessibility.certainty_clear()
    native_log.log_clear()

    guardian.guardian_init(project)
    (project / "app.sona").write_text('print("drift")\n', encoding="utf-8")
    result = guardian.guardian_verify(project)

    assert result["status"] == "drift"
    assert result["accessibility"]["available"] is True
    assert result["accessibility"]["issue_chunks"] == [["app.sona"]]
    assert any(item["message"] == "guardian.verify" for item in native_accessibility.breadcrumb_history(20))
    assert any(item.get("name") == "guardian.verify" for item in native_log.log_history(20))
    assert any(item["name"] == "guardian-drift" for item in native_accessibility.certainty_report())


def test_guardian_rejects_symlink_escape(tmp_path):
    project = make_project(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("secret\n", encoding="utf-8")
    link = project / "escape.txt"
    try:
        link.symlink_to(outside)
    except OSError as error:
        if os.name != "nt":
            pytest.fail(f"symlink creation is required for certification: {error}")
        outside_directory = tmp_path / "outside-directory"
        outside_directory.mkdir()
        (outside_directory / "secret.txt").write_text("secret\n", encoding="utf-8")
        link = project / "escape-directory"
        junction = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(outside_directory)],
            text=True,
            capture_output=True,
            shell=False,
            timeout=30,
        )
        if junction.returncode != 0:
            class SimulatedSymlink:
                def is_symlink(self):
                    return True

                def resolve(self, strict=False):
                    return outside.resolve()

                def relative_to(self, root):
                    return Path("escape.txt")

            with pytest.raises(ValueError, match="symlink escape"):
                guardian._assert_no_symlink_escape(
                    project.resolve(),
                    SimulatedSymlink(),
                    "inventory",
                    audit=False,
                )
            return

    with pytest.raises(ValueError, match="symlink escape|outside project root"):
        guardian.guardian_init(project)


def test_guardian_cli_runs_against_fixture_not_repo_root(tmp_path):
    project = make_project(tmp_path)
    repo_guardian_state = ROOT / ".sona" / "guardian"
    before_repo_state = repo_guardian_state.exists()

    for command in ["init", "status", "verify", "doctor"]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)
        proc = subprocess.run(
            [sys.executable, "-m", "sona", "guard", command, "--project-root", str(project)],
            cwd=tmp_path,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert proc.returncode == 0, proc.stderr or proc.stdout
        assert json.loads(proc.stdout)

    assert repo_guardian_state.exists() is before_repo_state


def test_guardian_public_smod_facade(tmp_path):
    project = make_project(tmp_path)
    interp = SonaUnifiedInterpreter(project_root=project)
    module = interp.module_system.import_module("guardian")

    assert call(module.status, str(project))["initialized"] is False
    assert call(module.init, str(project))["status"] == "initialized"
    assert call(module.verify, str(project))["status"] == "ok"
    assert call(module.snapshot, str(project), "manual")["status"] == "snapshot-created"
    assert call(module.diff, str(project))["status"] == "ok"
    assert "Guardian status: ok" in call(module.report_plain, str(project))
