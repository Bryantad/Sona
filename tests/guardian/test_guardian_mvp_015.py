import hashlib
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


def _sha256_label(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _write_guardian_bound_native_proof(project: Path, destination: Path) -> None:
    source = project / "app.sona"
    source_bytes = source.read_bytes()
    anchor, _baseline = guardian._guardian_proof_anchor(project)
    receipt = {
        "schema_id": "sona.native-proof.schema-1",
        "schema": 1,
        "receipt_type": "native_execution_proof",
        "generated_at_utc": "2026-08-10T00:00:00Z",
        "sona_version": "0.15.4",
        "engine": {
            "name": "native",
            "python_required": False,
            "python_embedded": False,
            "fallback_used": False,
        },
        "program": {
            "kind": "source",
            "source": {"sha256": _sha256_label(source_bytes), "bytes": len(source_bytes)},
        },
        "capabilities": {
            "console": True,
            "filesystem_read": False,
            "filesystem_write": False,
            "network": False,
            "process": False,
            "environment": False,
        },
        "execution": {
            "status": "ok",
            "exit_code": 0,
            "duration_ms": 0,
            "diagnostic": None,
            "stdout": {"sha256": _sha256_label(b""), "bytes": 0},
            "stderr": {"sha256": _sha256_label(b""), "bytes": 0},
        },
        "effects": [],
        "guardian": anchor,
    }
    unsigned = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    receipt["receipt_hash"] = _sha256_label(unsigned)
    destination.write_bytes(
        json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"
    )


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


def test_guardian_verifies_and_attests_a_bound_native_proof_without_receipt_paths(tmp_path):
    project = make_project(tmp_path)
    guardian.guardian_init(project)
    receipt = tmp_path / "native-proof.json"
    _write_guardian_bound_native_proof(project, receipt)

    before = {path.relative_to(project).as_posix(): path.read_bytes() for path in project.rglob("*") if path.is_file()}
    verified = guardian.guardian_proof_verify(project, receipt)
    after = {path.relative_to(project).as_posix(): path.read_bytes() for path in project.rglob("*") if path.is_file()}
    assert verified["status"] == "verified"
    assert verified["execution"] == {"status": "ok", "exit_code": 0}
    assert verified["guardian"]["program_baseline"] == "tracked"
    assert after == before, "receipt verification must remain read-only"

    attested = guardian.guardian_proof_attest(project, receipt)
    assert attested["status"] == "attested"
    history = guardian.guardian_proof_history(project)
    assert len(history) == 1
    payload = history[0]["payload"]
    assert payload["receipt_hash"] == verified["receipt_hash"]
    assert str(receipt) not in json.dumps(payload)
    assert "app.sona" not in json.dumps(payload)

    (project / "app.sona").write_text('print("drift")\n', encoding="utf-8")
    assert guardian.guardian_proof_verify(project, receipt)["status"] == "verified"
    rejected = guardian.guardian_proof_attest(project, receipt)
    assert rejected["status"] == "rejected"
    assert rejected["reason"] == "guardian-drift"
    assert len(guardian.guardian_proof_history(project)) == 1


def test_guardian_ai_review_uses_only_verified_redacted_evidence(tmp_path):
    project = make_project(tmp_path)
    guardian.guardian_init(project)
    receipt = tmp_path / "native-proof.json"
    _write_guardian_bound_native_proof(project, receipt)
    guardian_state = project / ".sona" / "guardian"
    before = {
        path.relative_to(guardian_state).as_posix(): path.read_bytes()
        for path in guardian_state.rglob("*")
        if path.is_file()
    }

    reviewed = guardian.guardian_proof_review(project, receipt, "deterministic")
    after = {
        path.relative_to(guardian_state).as_posix(): path.read_bytes()
        for path in guardian_state.rglob("*")
        if path.is_file()
    }

    assert reviewed["status"] == "reviewed"
    assert reviewed["schema_id"] == "sona.guardian-proof-ai-review.schema-1"
    assert reviewed["proof_status"] == "verified"
    assert reviewed["evidence"]["local_attestation_recorded"] is False
    assert reviewed["reviewer"] == {
        "provider_id": "deterministic",
        "model_id": "deterministic:sona",
        "advisory": True,
    }
    assert reviewed["review_input_hash"].startswith("sha256:")
    assert "does not add" in reviewed["review"]
    assert "not part of" in reviewed["trust_boundary"]
    rendered = json.dumps(reviewed)
    assert str(project) not in rendered
    assert str(receipt) not in rendered
    assert "app.sona" not in rendered
    assert 'print("hello")' not in rendered
    assert after == before, "AI review must not mutate Guardian proof state"
    assert not (project / ".sona" / "receipts" / "tasks").exists(), "AI review must not write a task receipt"

    guardian.guardian_proof_attest(project, receipt)
    attested_review = guardian.guardian_proof_review(project, receipt, "deterministic")
    assert attested_review["evidence"]["local_attestation_recorded"] is True


def test_guardian_ai_review_rejects_before_provider_routing(tmp_path):
    project = make_project(tmp_path)
    guardian.guardian_init(project)
    receipt = tmp_path / "native-proof.json"
    _write_guardian_bound_native_proof(project, receipt)
    receipt.write_bytes(b" " + receipt.read_bytes())

    governance_audit = project / ".sona" / "governance" / "audit.jsonl"
    reviewed = guardian.guardian_proof_review(project, receipt, "ollama")

    assert reviewed["status"] == "rejected"
    assert reviewed["reason"] == "receipt-not-canonical"
    assert not governance_audit.exists(), "invalid evidence must not reach governed provider routing"


def test_guardian_ai_review_routes_only_redacted_packet_to_local_ollama(tmp_path, monkeypatch):
    project = make_project(tmp_path)
    guardian.guardian_init(project)
    receipt = tmp_path / "native-proof.json"
    _write_guardian_bound_native_proof(project, receipt)
    captured = {}

    def fake_ollama_execute(_self, request, model):
        captured["request"] = request
        captured["model"] = model
        return {"summary": "Local model advisory review complete.", "status": "ok"}

    monkeypatch.setattr(
        "sona.developer_intelligence.providers.OllamaProvider.execute",
        fake_ollama_execute,
    )
    reviewed = guardian.guardian_proof_review(project, receipt, "ollama")

    assert reviewed["status"] == "reviewed"
    assert reviewed["reviewer"]["provider_id"] == "ollama"
    assert reviewed["reviewer"]["model_id"].startswith("ollama:")
    request = captured["request"]
    packet = json.loads(request.context.selected_text)
    assert set(packet) == {
        "schema_id",
        "proof_status",
        "receipt_hash",
        "execution",
        "guardian",
        "local_attestation_recorded",
    }
    assert request.target_files == ()
    assert request.context.active_file is None
    assert request.constraints.read_only is True
    assert request.constraints.allow_file_writes is False
    assert request.constraints.allow_shell is False
    assert request.constraints.allow_network is False
    rendered = request.context.selected_text
    assert str(project) not in rendered
    assert str(receipt) not in rendered
    assert "app.sona" not in rendered
    assert 'print("hello")' not in rendered


def test_guardian_rejects_noncanonical_or_wrongly_bound_native_proofs(tmp_path):
    project = make_project(tmp_path)
    guardian.guardian_init(project)
    receipt = tmp_path / "native-proof.json"
    _write_guardian_bound_native_proof(project, receipt)

    receipt.write_bytes(b" " + receipt.read_bytes())
    noncanonical = guardian.guardian_proof_verify(project, receipt)
    assert noncanonical["status"] == "rejected"
    assert noncanonical["reason"] == "receipt-not-canonical"

    _write_guardian_bound_native_proof(project, receipt)
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    payload["guardian"]["baseline_snapshot_id"] = "different-baseline"
    unsigned = dict(payload)
    unsigned.pop("receipt_hash")
    payload["receipt_hash"] = _sha256_label(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )
    receipt.write_bytes(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"
    )
    mismatch = guardian.guardian_proof_verify(project, receipt)
    assert mismatch["status"] == "rejected"
    assert mismatch["reason"] == "guardian-binding-mismatch"
    assert guardian.guardian_proof_history(project) == []


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


def test_canonical_guardian_proof_cli_verifies_attests_and_lists_history(tmp_path):
    project = make_project(tmp_path)
    guardian.guardian_init(project)
    receipt = tmp_path / "native-proof.json"
    _write_guardian_bound_native_proof(project, receipt)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)

    verify = subprocess.run(
        [
            sys.executable, "-m", "sona", "guardian", "proof", "verify",
            "--project-root", str(project), "--receipt", str(receipt),
        ],
        cwd=project, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert verify.returncode == 0, verify.stderr or verify.stdout
    assert json.loads(verify.stdout)["status"] == "verified"

    attest = subprocess.run(
        [
            sys.executable, "-m", "sona", "guardian", "proof", "attest",
            "--project-root", str(project), "--receipt", str(receipt),
        ],
        cwd=project, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert attest.returncode == 0, attest.stderr or attest.stdout
    assert json.loads(attest.stdout)["status"] == "attested"

    review = subprocess.run(
        [
            sys.executable, "-m", "sona", "guardian", "proof", "review",
            "--project-root", str(project), "--receipt", str(receipt),
            "--provider", "deterministic",
        ],
        cwd=project, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert review.returncode == 0, review.stderr or review.stdout
    review_payload = json.loads(review.stdout)
    assert review_payload["status"] == "reviewed"
    assert review_payload["evidence"]["local_attestation_recorded"] is True
    assert review_payload["reviewer"]["advisory"] is True
    assert str(project) not in review.stdout
    assert str(receipt) not in review.stdout

    history = subprocess.run(
        [sys.executable, "-m", "sona", "guardian", "proof", "history", "--project-root", str(project)],
        cwd=project, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert history.returncode == 0, history.stderr or history.stdout
    assert json.loads(history.stdout)[0]["event"] == "guardian.proof.attest"


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
    receipt = tmp_path / "native-proof.json"
    _write_guardian_bound_native_proof(project, receipt)
    assert call(module.proof_verify, str(project), str(receipt))["status"] == "verified"
    assert call(module.proof_review, str(project), str(receipt), "deterministic", None)["status"] == "reviewed"
    assert call(module.proof_attest, str(project), str(receipt))["status"] == "attested"
    assert call(module.proof_history, str(project))[0]["event"] == "guardian.proof.attest"
    assert "Guardian status: ok" in call(module.report_plain, str(project))
