from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from sona.developer_intelligence.redaction import redact
from sona.fact_service import explain_checked_facts
from sona.guide.facts import explain_facts
from sona.guide.models import GuideError, GuideRequest
from sona.guide.service import guide_request
from sona.proof import canonical_json_bytes, inspect_receipt, sha256_label
from sona.stdlib import native_guardian as guardian

ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / "tests/proof/fixtures/0.15.4-native-hello.json"


@pytest.mark.parametrize("mode", ["guided", "balanced", "expert"])
@pytest.mark.parametrize("style", ["simple", "visual", "technical"])
def test_frozen_receipt_cli_parity_and_fact_preservation(mode, style, tmp_path):
    before = RECEIPT.read_bytes()
    result = explain_checked_facts("proof", receipt=RECEIPT, mode=mode, style=style, no_profile=True)
    assert result["facts"] == inspect_receipt(RECEIPT)
    assert result["fixes"] == []
    assert all(limit in result["text"] for limit in result["assurance_limits"])
    command = subprocess.run([sys.executable, "-m", "sona", "guide", "proof", str(RECEIPT),
                              "--mode", mode, "--style", style, "--no-profile", "--json"],
                             cwd=tmp_path, env={**os.environ, "PYTHONPATH": str(ROOT)},
                             capture_output=True, text=True, timeout=15, check=False)
    assert command.returncode == 0 and command.stderr == ""
    assert json.loads(command.stdout) == result
    assert not list(tmp_path.iterdir())
    assert RECEIPT.read_bytes() == before


@pytest.mark.parametrize("mode", ["guided", "balanced", "expert"])
def test_corrupted_receipt_never_gets_valid_summary(mode, tmp_path):
    receipt = tmp_path / "bad.sproof"
    payload = json.loads(RECEIPT.read_bytes())
    payload["sona_version"] = "changed"
    receipt.write_bytes(canonical_json_bytes(payload))
    result = explain_checked_facts("proof", receipt=receipt, mode=mode, no_profile=True)
    assert result["facts"] == inspect_receipt(receipt)
    assert result["facts"]["status"] == "invalid"
    assert "PROOF-VERIFY-005" in result["text"]
    assert "Receipt integrity: VALID" not in result["text"]
    assert "Engine: Native Core" not in result["text"]


@pytest.mark.parametrize("status", ["uninitialized", "ok", "drift"])
@pytest.mark.parametrize("mode", ["guided", "balanced", "expert"])
def test_real_guardian_states_preserve_check_results_and_files(status, mode, tmp_path):
    source = tmp_path / "hello.sona"
    source.write_text('print("before");', encoding="utf-8")
    if status != "uninitialized":
        guardian.guardian_init(tmp_path)
    if status == "drift":
        source.write_text('print("after");', encoding="utf-8")
    before = {str(path.relative_to(tmp_path)): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    expected = redact(guardian.guardian_check(tmp_path))
    result = explain_checked_facts("guardian", project_root=tmp_path, mode=mode, no_profile=True)
    assert result["facts"] == expected
    assert result["facts"]["status"] == status
    assert all(limit in result["text"] for limit in result["assurance_limits"])
    after = {str(path.relative_to(tmp_path)): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    assert before == after


def test_legacy_and_changed_policy_warnings_survive_expert_mode(tmp_path):
    # Renderer-only shape fixture; actual state-provider behavior is tested above.
    facts = redact(guardian.guardian_check(tmp_path))
    facts["policy"].update(legacy_baseline=True, working_matches_trusted=False)
    facts["proof_mode"].update(ready=True, policy_enforced=False)
    original = copy.deepcopy(facts)
    result = explain_facts(GuideRequest(fact_kind="guardian", facts=facts, mode="expert"))
    assert result["facts"] == original == facts
    assert "Legacy baseline" in result["text"]
    assert "Working policy differs" in result["text"]
    assert result["facts"]["proof_mode"]["policy_enforced"] is False


def test_failed_execution_remains_failed_and_effects_remain_partial(tmp_path):
    payload = json.loads(RECEIPT.read_bytes())
    payload["execution"].update(status="failed", exit_code=1)
    payload.pop("receipt_hash")
    payload["receipt_hash"] = sha256_label(canonical_json_bytes(payload))
    path = tmp_path / "failed.sproof"
    path.write_bytes(canonical_json_bytes(payload))
    result = explain_checked_facts("proof", receipt=path, no_profile=True)
    assert result["facts"]["status"] == "valid"
    assert "Execution: failed (exit 1)" in result["text"]
    assert "PARTIAL" in result["text"]


@pytest.mark.parametrize("payload", [
    {"fact_kind": "proof", "facts": {}, "diagnostic_id": "SONA-RUNTIME-003"},
    {"fact_kind": "unknown", "facts": {}}, {"fact_kind": "proof", "facts": None},
])
def test_fact_and_diagnostic_variants_are_exclusive(payload):
    with pytest.raises(GuideError):
        GuideRequest(**payload)


def test_untrusted_json_cannot_assert_verification_success():
    response = guide_request({"schema_version": 1, "action": "proof", "facts": {"status": "valid"}})
    assert response["status"] == "unavailable"
    with pytest.raises(GuideError):
        explain_facts(GuideRequest(fact_kind="proof", facts={"status": "valid"}))


def test_profile_mode_applies_read_only_and_explicit_mode_wins(tmp_path):
    from sona.guide.profile import set_preferences

    set_preferences(tmp_path, guidance_mode="expert")
    profile = tmp_path / ".sona/learning.json"
    before = profile.read_bytes()
    assert explain_checked_facts("proof", receipt=RECEIPT, project_root=tmp_path)["mode"] == "expert"
    assert explain_checked_facts("proof", receipt=RECEIPT, project_root=tmp_path, mode="guided")["mode"] == "guided"
    assert profile.read_bytes() == before


@pytest.mark.parametrize("field,identifier", [("fallback_used", "PROOF-VERIFY-013"), ("python_required", "PROOF-VERIFY-012")])
def test_rehashed_non_native_only_claim_is_rejected(field, identifier, tmp_path):
    payload = json.loads(RECEIPT.read_bytes())
    payload["engine"][field] = True
    payload.pop("receipt_hash")
    payload["receipt_hash"] = sha256_label(canonical_json_bytes(payload))
    path = tmp_path / "unsupported.sproof"
    path.write_bytes(canonical_json_bytes(payload))
    result = explain_checked_facts("proof", receipt=path, no_profile=True)
    assert result["facts"]["status"] == "invalid"
    assert identifier in result["text"]
    assert "Receipt integrity: VALID" not in result["text"]


def test_real_native_denial_is_explained_without_rerunning(native_binary, tmp_path):
    source = tmp_path / "denied.sona"
    source.write_text('import fs; fs.write_text("blocked.txt", "denied");', encoding="utf-8")
    receipt = tmp_path / "denied.sproof"
    process = subprocess.run([str(native_binary), "proof", str(source), "--receipt", str(receipt), "--engine", "native"],
                             cwd=tmp_path, capture_output=True, text=True, timeout=15, check=False)
    assert process.returncode == 1
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir() if path.is_file()}
    for mode in ("guided", "balanced", "expert"):
        result = explain_checked_facts("proof", receipt=receipt, mode=mode, no_profile=True)
        assert result["facts"] == inspect_receipt(receipt)
        assert "Execution: failed (exit 1)" in result["text"]
        assert "SONA-FS-005" in result["text"]
    assert not (tmp_path / "blocked.txt").exists()
    assert before == {path.name: path.read_bytes() for path in tmp_path.iterdir() if path.is_file()}


def test_profile_failure_does_not_replace_provider_diagnostic(tmp_path):
    missing = tmp_path / "missing"
    result = explain_checked_facts("guardian", project_root=missing)
    assert result["facts"] == redact(guardian.guardian_check(missing))
    assert result["facts"]["diagnostic_id"] == "SONA-GUARD-001"
    assert result["profile_diagnostic"]["diagnostic_id"] == "SONA-GUIDE-005"
    assert "SONA-GUARD-001" in result["text"]
    assert not list(tmp_path.iterdir())
