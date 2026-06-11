import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from sona.interpreter import SonaUnifiedInterpreter
from sona.stdlib import native_guardian as guardian


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

    rollback = guardian.guardian_rollback(project, snapshot_id)
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
    assert result["validation_results"][0]["exit_code"] == 0
    assert "SystemExit(99)" not in " ".join(result["validation_results"][0]["command"])
    assert any(item["event"] == "guardian.quarantine" for item in guardian.guardian_audit_history(project, 200))


def test_guardian_rejects_symlink_escape(tmp_path):
    project = make_project(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("secret\n", encoding="utf-8")
    link = project / "escape.txt"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation is unavailable in this environment")

    with pytest.raises(ValueError, match="symlink escape"):
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
