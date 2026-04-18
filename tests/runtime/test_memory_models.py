import json

from sona.runtime.memory import (
    ClassificationTier,
    Episode,
    Fact,
    MemoryClaim,
    MemoryReceiptRef,
    Procedure,
    ProcedureReviewState,
)


def test_episode_to_dict_serializes_enums_and_receipt_refs():
    ref = MemoryReceiptRef(
        receipt_id="rcpt_001",
        event_kind_or_path="execution.events[2]",
        classification=ClassificationTier.SENSITIVE,
    )
    episode = Episode(
        agent_id="orb.main",
        session_id="sess_001",
        kind="user_input",
        source_type="chat",
        payload={"text": "remember this"},
        receipt_refs=[ref],
    )

    data = episode.to_dict()
    assert data["classification"] == "internal"
    assert data["receipt_refs"][0]["classification"] == "sensitive"
    assert data["payload"]["text"] == "remember this"


def test_claim_fact_and_procedure_serialize_expected_shapes():
    claim = MemoryClaim(
        statement="Service is unstable",
        claim_type="service_health",
        derived_from_episode_ids=["ep_1", "ep_2"],
    )
    fact = Fact(
        canonical_statement="Service degraded in the last 24h",
        supporting_claim_ids=[claim.id],
        supporting_episode_ids=["ep_1", "ep_2"],
    )
    procedure = Procedure(
        title="Recover cache service",
        procedure_type="recovery",
        steps_or_pattern=["check health", "restart worker"],
        supporting_fact_ids=[fact.id],
        review_state=ProcedureReviewState.APPROVED,
    )

    claim_json = json.dumps(claim.to_dict())
    fact_json = json.dumps(fact.to_dict())
    procedure_json = json.dumps(procedure.to_dict())

    assert "Service is unstable" in claim_json
    assert "Service degraded" in fact_json
    assert "approved" in procedure_json
