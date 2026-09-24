"""Phase 13: structured effects, scoped grants, and proposal trust boundaries."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from sona.runtime import (
    CapabilityAuditFullError,
    CapabilityAuthority,
    CapabilityPolicyDecision,
    CapabilityPolicyError,
    CapabilityRequest,
    EffectClass,
    EffectDecision,
    EffectJournal,
    EffectJournalFullError,
    EffectResult,
    ProposalApproval,
    ProposalGate,
    ProposalStatus,
    ProposalValidation,
    UntrustedProposal,
)

_POLICY_HASH = "sha256:" + "0" * 64


class _Policy:
    def __init__(self, decision=EffectDecision.ALLOWED, ttl=120):
        self.decision = decision
        self.ttl = ttl
        self.calls = 0

    def evaluate(self, request):
        self.calls += 1
        return CapabilityPolicyDecision(
            self.decision, "test-policy", "allow-exact", _POLICY_HASH,
            "SONA-TEST-POLICY", self.ttl,
        )


def test_effect_taxonomy_separates_decision_from_observed_result():
    journal = EffectJournal(maximum_records=2)
    denied = journal.record(
        EffectClass.FS_DELETE,
        "resource-17",
        EffectDecision.DENIED,
        EffectResult.NOT_ATTEMPTED,
    )
    allowed = journal.record(
        EffectClass.NETWORK_REQUEST,
        "endpoint-2",
        EffectDecision.ALLOWED,
        EffectResult.FAILED,
    )
    assert (denied.decision, denied.result) == (
        EffectDecision.DENIED,
        EffectResult.NOT_ATTEMPTED,
    )
    assert (allowed.decision, allowed.result) == (
        EffectDecision.ALLOWED,
        EffectResult.FAILED,
    )
    assert allowed.sequence == 2
    with pytest.raises(EffectJournalFullError):
        journal.record(
            EffectClass.PROCESS_EXECUTE,
            "operation-3",
            EffectDecision.ALLOWED,
            EffectResult.SUCCEEDED,
        )
    assert len(journal.snapshot()) == 2


@pytest.mark.parametrize("effect", list(EffectClass))
def test_effect_taxonomy_values_are_unique_and_stable(effect):
    assert effect.value.isupper()
    assert "." in effect.value


def test_effect_journal_rejects_denied_but_completed_effects_and_paths():
    journal = EffectJournal()
    with pytest.raises(ValueError, match="denied effect"):
        journal.record(
            EffectClass.FS_WRITE,
            "file-1",
            EffectDecision.DENIED,
            EffectResult.SUCCEEDED,
        )
    with pytest.raises(ValueError, match="opaque identifier"):
        journal.record(
            EffectClass.FS_READ,
            r"C:\\private\\source.sona",
            EffectDecision.ALLOWED,
            EffectResult.SUCCEEDED,
        )


def test_capability_grant_requires_policy_and_is_exact_scoped_and_revocable():
    policy = _Policy()
    authority = CapabilityAuthority(policy)
    request = CapabilityRequest(EffectClass.FS_READ, "workspace-file-7", 60)
    result = authority.request(request)
    assert policy.calls == 1
    assert result.decision is EffectDecision.ALLOWED
    token = result.capability
    assert token is not None
    assert authority.check(token, EffectClass.FS_READ, "workspace-file-7").decision is (
        EffectDecision.ALLOWED
    )
    mismatch = authority.check(token, EffectClass.FS_WRITE, "workspace-file-7")
    assert mismatch.decision is EffectDecision.DENIED
    assert mismatch.reason_code == "SONA-CAPABILITY-SCOPE-MISMATCH"
    assert authority.revoke(token)
    assert authority.check(token, EffectClass.FS_READ, "workspace-file-7").reason_code == (
        "SONA-CAPABILITY-REVOKED"
    )


def test_capability_deny_ttl_limit_and_policy_failure_never_issue_token():
    denied_authority = CapabilityAuthority(_Policy(EffectDecision.DENIED))
    denied = denied_authority.request(CapabilityRequest(EffectClass.FS_READ, "item-1"))
    assert denied.capability is None
    assert denied.decision is EffectDecision.DENIED

    ttl_authority = CapabilityAuthority(_Policy(ttl=10))
    ttl_denied = ttl_authority.request(CapabilityRequest(EffectClass.FS_READ, "item-2", 11))
    assert ttl_denied.capability is None
    assert ttl_denied.reason_code == "SONA-CAPABILITY-TTL-EXCEEDED"

    class BrokenPolicy:
        def evaluate(self, request):
            raise RuntimeError("private path and secret must not leak")

    failing = CapabilityAuthority(BrokenPolicy())
    with pytest.raises(CapabilityPolicyError, match="policy failed") as caught:
        failing.request(CapabilityRequest(EffectClass.FS_READ, "item-3"))
    assert "private path" not in str(caught.value)
    assert failing.audit_snapshot()[0].decision is EffectDecision.DENIED


def test_capability_expiry_and_audit_exhaustion_fail_closed():
    now = [100.0]
    authority = CapabilityAuthority(_Policy(), monotonic_clock=lambda: now[0])
    token = authority.request(
        CapabilityRequest(EffectClass.MODEL_INFERENCE, "model-1", 5)
    ).capability
    assert token is not None
    now[0] = 105.0
    expired = authority.check(token, EffectClass.MODEL_INFERENCE, "model-1")
    assert expired.decision is EffectDecision.DENIED
    assert expired.reason_code == "SONA-CAPABILITY-EXPIRED"

    limited = CapabilityAuthority(
        _Policy(), maximum_active_grants=1, maximum_audit_records=8,
        monotonic_clock=lambda: now[0],
    )
    first = limited.request(CapabilityRequest(EffectClass.FS_READ, "item-a", 1)).capability
    assert first is not None
    now[0] += 2
    second = limited.request(CapabilityRequest(EffectClass.FS_READ, "item-b", 1)).capability
    assert second is not None

    full = CapabilityAuthority(_Policy(), maximum_audit_records=1)
    full.request(CapabilityRequest(EffectClass.FS_READ, "item-4"))
    with pytest.raises(CapabilityAuditFullError, match="fails closed"):
        full.request(CapabilityRequest(EffectClass.FS_READ, "item-4"))


def test_capability_token_construction_and_invalid_policy_records_are_rejected():
    from sona.runtime.capabilities import CapabilityToken

    with pytest.raises(TypeError, match="issued only"):
        CapabilityToken("fake", EffectClass.FS_READ, "item-1", 999.0, _seal=None)
    with pytest.raises(TypeError, match="EffectDecision"):
        CapabilityPolicyDecision("allowed", "policy", "rule", _POLICY_HASH, "OK", 10)


def test_untrusted_model_proposal_cannot_self_approve_or_skip_validation():
    calls = []
    proposal = UntrustedProposal.from_data(
        "proposal-1", "local-model", {"change": "candidate", "approved": True}
    )
    gate = ProposalGate(
        validator=lambda candidate: calls.append("validate")
        or ProposalValidation(False, "SONA-PROPOSAL-INVALID"),
        approver=lambda candidate: calls.append("approve")
        or ProposalApproval(True, "human-reviewer"),
    )
    result = gate.process(proposal)
    assert result.status is ProposalStatus.REJECTED
    assert result.accepted is None
    assert calls == ["validate"]


def test_accepted_proposal_requires_explicit_approval_and_remains_data_only():
    proposal = UntrustedProposal.from_data(
        "proposal-2", "local-model", {"change": "candidate", "approved": False}
    )
    denied = ProposalGate(
        lambda _: ProposalValidation(True, "SONA-PROPOSAL-VALID"),
        lambda _: ProposalApproval(False, "human-reviewer"),
    ).process(proposal)
    assert denied.status is ProposalStatus.REJECTED
    assert denied.reason_code == "SONA-PROPOSAL-NOT-APPROVED"

    accepted = ProposalGate(
        lambda _: ProposalValidation(True, "SONA-PROPOSAL-VALID"),
        lambda _: ProposalApproval(True, "human-reviewer"),
    ).process(proposal)
    assert accepted.status is ProposalStatus.ACCEPTED
    assert accepted.accepted is not None
    assert accepted.accepted.payload["approved"] is False
    assert not hasattr(accepted.accepted, "capability")
    exposed = accepted.accepted.payload
    exposed["change"] = "mutated copy"
    assert accepted.accepted.payload["change"] == "candidate"
    from sona.runtime.proposals import AcceptedProposal

    with pytest.raises(TypeError, match="issued only"):
        AcceptedProposal("proposal-2", "local-model", "{}", "VALID", "reviewer", None)


def test_untrusted_proposal_direct_construction_cannot_bypass_canonical_size_checks():
    with pytest.raises(ValueError, match="canonical bounded JSON"):
        UntrustedProposal("p-4", "model", '{"x": 1}')
    with pytest.raises(ValueError, match="canonical bounded JSON"):
        UntrustedProposal("p-5", "model", '{"x":1,"x":2}')


def test_proposals_are_bounded_json_and_callback_errors_fail_closed():
    with pytest.raises(ValueError, match="finite JSON"):
        UntrustedProposal.from_data("p-1", "model", {"score": float("nan")})
    with pytest.raises(ValueError, match="65536"):
        UntrustedProposal.from_data("p-2", "model", {"data": "x" * 70_000})

    proposal = UntrustedProposal.from_data("p-3", "model", {"change": "x"})
    result = ProposalGate(
        lambda _: (_ for _ in ()).throw(RuntimeError("hidden detail")),
        lambda _: ProposalApproval(True, "reviewer"),
    ).process(proposal)
    assert result.status is ProposalStatus.REJECTED
    assert result.reason_code == "SONA-PROPOSAL-VALIDATION-ERROR"


def test_proposal_gate_requires_distinct_validation_and_approval_callbacks():
    callback = lambda _: ProposalValidation(True, "SONA-PROPOSAL-VALID")
    with pytest.raises(ValueError, match="separate callbacks"):
        ProposalGate(callback, callback)


def test_effect_journal_uses_utc_timestamp_without_accepting_naive_time():
    journal = EffectJournal()
    record = journal.record(
        EffectClass.CLOCK_READ,
        "clock-system",
        EffectDecision.NOT_REQUIRED,
        EffectResult.UNKNOWN,
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert record.occurred_at_utc == "2026-01-01T00:00:00Z"
    with pytest.raises(ValueError, match="timezone-aware"):
        journal.record(
            EffectClass.CLOCK_READ,
            "clock-system",
            EffectDecision.UNKNOWN,
            EffectResult.UNKNOWN,
            occurred_at=datetime(2026, 1, 1),
        )
