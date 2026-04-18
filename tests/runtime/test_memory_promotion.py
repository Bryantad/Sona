"""Unit tests for the PromotionKernel class."""

from sona.runtime.memory import (
    Episode,
    MemoryReceiptRef,
    ProcedureReviewState,
    TrustState,
)
from sona.runtime.memory.advanced import PromotionKernel, SQLiteMemoryStore


def _receipt_ref(receipt_id: str, event_offset: int = 0) -> MemoryReceiptRef:
    return MemoryReceiptRef(
        receipt_id=receipt_id,
        event_kind_or_path=f"execution.events[{event_offset}]",
    )


def _episode(
    *,
    session_id: str,
    kind: str,
    payload: dict,
    receipt_id: str,
    importance: float = 0.8,
):
    return Episode(
        agent_id="sona.interpreter.test",
        session_id=session_id,
        kind=kind,
        source_type="runtime",
        payload=payload,
        importance=importance,
        receipt_refs=[_receipt_ref(receipt_id)],
    )


def test_episode_with_provenance_promotes_to_claim(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    kernel = PromotionKernel(store)
    episode = store.append_episode(
        _episode(
            session_id="sess_claim",
            kind="intent_recorded",
            payload={
                "goal": "Ship promotion kernel",
                "has_constraints": True,
                "has_success": False,
            },
            receipt_id="rcpt_claim",
        )
    )

    claim = kernel.promote_episode_to_claim(episode)

    assert claim.claim_type == "intent"
    assert claim.derived_from_episode_ids == [episode.id]
    assert claim.trust_state == TrustState.DERIVED
    assert len(claim.receipt_refs) == 1


def test_low_confidence_episode_does_not_promote_to_claim(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    kernel = PromotionKernel(store, min_claim_confidence=0.5)
    episode = store.append_episode(
        _episode(
            session_id="sess_low_conf",
            kind="focus_transition",
            payload={"action": "start", "target": "deep work", "minutes": 25},
            receipt_id="rcpt_low",
            importance=0.1,
        )
    )

    try:
        kernel.promote_episode_to_claim(episode)
        assert False, "Expected low-confidence promotion to fail"
    except ValueError as exc:
        assert "below the claim promotion threshold" in str(exc)


def test_contradictory_claim_is_marked_disputed(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    kernel = PromotionKernel(store)
    first_episode = store.append_episode(
        _episode(
            session_id="sess_contradiction",
            kind="decision_recorded",
            payload={
                "label": "Use cache",
                "option": "redis",
                "has_rationale": True,
            },
            receipt_id="rcpt_decision_1",
        )
    )
    first_claim = kernel.promote_episode_to_claim(first_episode)

    second_episode = store.append_episode(
        _episode(
            session_id="sess_contradiction",
            kind="decision_recorded",
            payload={
                "label": "Avoid cache",
                "option": "none",
                "has_rationale": True,
            },
            receipt_id="rcpt_decision_2",
        )
    )

    contradictory_claim = kernel.promote_episode_to_claim(
        second_episode,
        contradicts_claim_ids=[first_claim.id],
    )

    assert contradictory_claim.trust_state == TrustState.DISPUTED
    assert contradictory_claim.contradicts_claim_ids == [first_claim.id]


def test_multiple_claims_promote_to_fact_with_provenance(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    kernel = PromotionKernel(store)
    episodes = [
        store.append_episode(
            _episode(
                session_id="sess_fact",
                kind="intent_recorded",
                payload={
                    "goal": f"Goal {index}",
                    "has_constraints": False,
                    "has_success": True,
                },
                receipt_id=f"rcpt_fact_{index}",
            )
        )
        for index in range(2)
    ]
    claims = [kernel.promote_episode_to_claim(episode) for episode in episodes]

    fact = kernel.promote_claims_to_fact(
        claims,
        canonical_statement="The release goal is stable",
    )

    assert fact.trust_state == TrustState.CONFIRMED
    assert fact.supporting_claim_ids == [claim.id for claim in claims]
    assert fact.supporting_episode_ids == [episode.id for episode in episodes]
    assert len(fact.receipt_refs) == 2


def test_superseded_fact_is_preserved_not_overwritten(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    kernel = PromotionKernel(store)
    original_episodes = [
        store.append_episode(
            _episode(
                session_id="sess_supersede",
                kind="intent_recorded",
                payload={
                    "goal": f"Original {index}",
                    "has_constraints": False,
                    "has_success": True,
                },
                receipt_id=f"rcpt_original_{index}",
            )
        )
        for index in range(2)
    ]
    original_claims = [
        kernel.promote_episode_to_claim(episode)
        for episode in original_episodes
    ]
    original_fact = kernel.promote_claims_to_fact(
        original_claims,
        canonical_statement="Original fact",
    )

    replacement_episodes = [
        store.append_episode(
            _episode(
                session_id="sess_supersede",
                kind="intent_recorded",
                payload={
                    "goal": f"Replacement {index}",
                    "has_constraints": False,
                    "has_success": True,
                },
                receipt_id=f"rcpt_replacement_{index}",
            )
        )
        for index in range(2)
    ]
    replacement_claims = [
        kernel.promote_episode_to_claim(episode)
        for episode in replacement_episodes
    ]
    replacement_fact = kernel.promote_claims_to_fact(
        replacement_claims,
        canonical_statement="Replacement fact",
        supersedes_fact_id=original_fact.id,
    )

    assert replacement_fact.supersedes_fact_id == original_fact.id
    assert store.get_fact(original_fact.id) is not None
    assert store.get_fact(replacement_fact.id) is not None
    assert original_fact.id != replacement_fact.id


def test_repeated_success_evidence_promotes_to_procedure(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    kernel = PromotionKernel(store)
    episodes = [
        store.append_episode(
            _episode(
                session_id="sess_procedure",
                kind="working_memory_update",
                payload={"action": "store", "key": f"step_{index}"},
                receipt_id=f"rcpt_proc_{index}",
            )
        )
        for index in range(2)
    ]
    claims = [kernel.promote_episode_to_claim(episode) for episode in episodes]
    fact = kernel.promote_claims_to_fact(
        claims,
        canonical_statement="Working memory updates succeeded twice",
    )

    procedure = kernel.promote_facts_to_procedure(
        [fact],
        title="Persist working memory update",
        procedure_type="runtime_pattern",
        steps_or_pattern=["store key", "validate persistence"],
        success_episode_ids=[episode.id for episode in episodes],
        review_state=ProcedureReviewState.REVIEWED,
    )

    assert procedure.supporting_fact_ids == [fact.id]
    assert procedure.success_evidence_ids == [
        episode.id for episode in episodes
    ]
    assert procedure.review_state == ProcedureReviewState.REVIEWED
    assert len(procedure.receipt_refs) == 2
