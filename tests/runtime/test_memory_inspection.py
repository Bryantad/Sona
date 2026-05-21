from sona.runtime.memory import (
    AgentCheckpoint,
    ClassificationTier,
    Goal,
    GoalState,
    MemoryLink,
    RetentionState,
)
from sona.runtime.memory.advanced import (
    MemoryPolicy,
    InspectionKernel,
    PolicyKernel,
    PromotionKernel,
    RetentionPolicy,
    RetrievalKernel,
    SQLiteMemoryStore,
)


def _episode(
    *,
    session_id: str,
    kind: str,
    payload: dict,
    receipt_id: str,
):
    from sona.runtime.memory import Episode, MemoryReceiptRef

    return Episode(
        agent_id="sona.interpreter.test",
        session_id=session_id,
        kind=kind,
        source_type="runtime",
        payload=payload,
        importance=0.8,
        receipt_refs=[
            MemoryReceiptRef(
                receipt_id=receipt_id,
                event_kind_or_path="execution.events[0]",
            )
        ],
    )


def test_inspect_fact_returns_related_ids_receipts_and_links(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    promotion = PromotionKernel(store)
    inspection = InspectionKernel(store)
    episodes = [
        store.append_episode(
            _episode(
                session_id="sess_inspect",
                kind="intent_recorded",
                payload={
                    "goal": f"Inspect {index}",
                    "has_constraints": False,
                    "has_success": True,
                },
                receipt_id=f"rcpt_inspect_{index}",
            )
        )
        for index in range(2)
    ]
    claims = [promotion.promote_episode_to_claim(ep) for ep in episodes]
    fact = promotion.promote_claims_to_fact(
        claims,
        canonical_statement="inspection fact",
    )
    store.add_link(
        MemoryLink(
            from_id=claims[0].id,
            to_id=fact.id,
            relation_type="supports",
            source_episode_ids=[episodes[0].id],
        )
    )

    result = inspection.inspect_object("fact", fact.id)

    assert result.object_type == "fact"
    assert result.retention_state == RetentionState.ACTIVE.value
    assert result.related_ids["supporting_claim_ids"] == [
        claims[0].id,
        claims[1].id,
    ]
    assert result.receipt_refs
    assert any(link.relation_type == "supports" for link in result.links)


def test_inspect_provenance_traces_fact_to_claims_and_episodes(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    promotion = PromotionKernel(store)
    inspection = InspectionKernel(store)
    episodes = [
        store.append_episode(
            _episode(
                session_id="sess_prov",
                kind="decision_recorded",
                payload={
                    "label": f"Decision {index}",
                    "option": "ship",
                    "has_rationale": True,
                },
                receipt_id=f"rcpt_prov_{index}",
            )
        )
        for index in range(2)
    ]
    fact = promotion.promote_claims_to_fact(
        [promotion.promote_episode_to_claim(ep) for ep in episodes],
        canonical_statement="provenance fact",
    )

    trace = inspection.inspect_provenance("fact", fact.id)

    assert trace.root.object_id == fact.id
    assert len(trace.supporting_claims) == 2
    assert len(trace.supporting_episodes) == 2


def test_goal_and_checkpoint_inspection_are_available_in_phase_c(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    inspection = InspectionKernel(store)
    goal = store.save_goal(
        Goal(
            title="Resume persistent work",
            status=GoalState.SUSPENDED,
            agent_id="sona.interpreter.test",
            session_id="sess_goal",
            linked_episode_ids=["ep_1"],
        )
    )
    checkpoint = store.save_checkpoint(
        AgentCheckpoint(
            agent_id="sona.interpreter.test",
            session_id="sess_goal",
            working_state_blob={"cursor": 3},
            active_goal_stack=[goal.id],
            last_processed_episode_id="ep_1",
        )
    )

    goal_view = inspection.inspect_goal(goal.id)
    checkpoint_view = inspection.inspect_checkpoint(checkpoint.id)
    listed_goals = inspection.list_active_or_suspended_goals(
        agent_id="sona.interpreter.test",
        session_id="sess_goal",
    )
    latest_checkpoint = inspection.get_latest_checkpoint(
        "sona.interpreter.test"
    )

    assert goal_view.related_ids["linked_episode_ids"] == ["ep_1"]
    assert checkpoint_view.related_ids["active_goal_stack"] == [goal.id]
    assert [item.object_id for item in listed_goals] == [goal.id]
    assert latest_checkpoint is not None
    assert latest_checkpoint.object_id == checkpoint.id


def test_archive_forget_and_delete_keep_records_inspectable(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    promotion = PromotionKernel(store)
    retrieval = RetrievalKernel(store)
    inspection = InspectionKernel(store)
    episodes = [
        store.append_episode(
            _episode(
                session_id="sess_lifecycle",
                kind="intent_recorded",
                payload={
                    "goal": f"Lifecycle {index}",
                    "has_constraints": False,
                    "has_success": True,
                },
                receipt_id=f"rcpt_lifecycle_{index}",
            )
        )
        for index in range(2)
    ]
    fact = promotion.promote_claims_to_fact(
        [promotion.promote_episode_to_claim(ep) for ep in episodes],
        canonical_statement="lifecycle fact",
    )

    archived = inspection.archive("fact", fact.id)
    forgotten = inspection.forget("fact", fact.id)
    deleted = inspection.delete("fact", fact.id)
    trace = inspection.inspect_object("fact", fact.id)
    explanation = retrieval.explain_retrieval(
        "lifecycle fact",
        agent_id="sona.interpreter.test",
        session_id="sess_lifecycle",
        include_claims=False,
        include_episodes=False,
    )

    assert archived.retention_state == RetentionState.ARCHIVED.value
    assert forgotten.retention_state == RetentionState.FORGOTTEN.value
    assert deleted.retention_state == RetentionState.DELETED.value
    assert trace.retention_state == RetentionState.DELETED.value
    assert explanation.included == []
    assert any(
        item.memory_id == fact.id and "deleted" in item.retention_reason
        for item in explanation.excluded
    )


def test_delete_requires_archive_when_policy_demands_it(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    promotion = PromotionKernel(store)
    inspection = InspectionKernel(
        store,
        policy_kernel=PolicyKernel(
            MemoryPolicy(
                retention_policy={"fact": RetentionPolicy(require_archive_before_delete=True)}
            )
        ),
    )
    episodes = [
        store.append_episode(
            _episode(
                session_id="sess_policy_delete",
                kind="intent_recorded",
                payload={
                    "goal": f"Policy delete {index}",
                    "has_constraints": False,
                    "has_success": True,
                },
                receipt_id=f"rcpt_policy_delete_{index}",
            )
        )
        for index in range(2)
    ]
    fact = promotion.promote_claims_to_fact(
        [promotion.promote_episode_to_claim(ep) for ep in episodes],
        canonical_statement="policy protected fact",
    )

    try:
        inspection.delete("fact", fact.id)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected delete to be denied by policy")

    assert "archived or forgotten before deletion" in message.lower()
