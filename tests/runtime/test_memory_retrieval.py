from sona.runtime.memory import (
    Episode,
    RetentionState,
)
from sona.runtime.memory.advanced import (
    PromotionKernel,
    RetrievalKernel,
    SQLiteMemoryStore,
)


def _episode(
    *,
    session_id: str,
    kind: str,
    payload: dict,
    receipt_id: str,
    importance: float = 0.8,
    tenant_id: str | None = None,
):
    from sona.runtime.memory import MemoryReceiptRef

    return Episode(
        agent_id="sona.interpreter.test",
        tenant_id=tenant_id,
        session_id=session_id,
        kind=kind,
        source_type="runtime",
        payload=payload,
        importance=importance,
        receipt_refs=[
            MemoryReceiptRef(
                receipt_id=receipt_id,
                event_kind_or_path="execution.events[0]",
            )
        ],
    )


def test_scope_mismatch_excludes_memory(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    kernel = PromotionKernel(store)
    retrieval = RetrievalKernel(store)

    episode_a = store.append_episode(
        _episode(
            session_id="sess_scope",
            kind="intent_recorded",
            payload={
                "goal": "Tenant A release",
                "has_constraints": False,
                "has_success": True,
            },
            receipt_id="rcpt_scope_a",
            tenant_id="tenant_a",
        )
    )
    episode_b = store.append_episode(
        _episode(
            session_id="sess_scope",
            kind="intent_recorded",
            payload={
                "goal": "Tenant B release",
                "has_constraints": False,
                "has_success": True,
            },
            receipt_id="rcpt_scope_b",
            tenant_id="tenant_b",
        )
    )
    fact_a = kernel.promote_claims_to_fact(
        [
            kernel.promote_episode_to_claim(episode_a),
            kernel.promote_episode_to_claim(
                store.append_episode(
                    _episode(
                        session_id="sess_scope",
                        kind="intent_recorded",
                        payload={
                            "goal": "Tenant A release again",
                            "has_constraints": False,
                            "has_success": True,
                        },
                        receipt_id="rcpt_scope_a2",
                        tenant_id="tenant_a",
                    )
                )
            ),
        ],
        canonical_statement="tenant release",
    )
    kernel.promote_claims_to_fact(
        [
            kernel.promote_episode_to_claim(episode_b),
            kernel.promote_episode_to_claim(
                store.append_episode(
                    _episode(
                        session_id="sess_scope",
                        kind="intent_recorded",
                        payload={
                            "goal": "Tenant B release again",
                            "has_constraints": False,
                            "has_success": True,
                        },
                        receipt_id="rcpt_scope_b2",
                        tenant_id="tenant_b",
                    )
                )
            ),
        ],
        canonical_statement="tenant release",
    )

    results = retrieval.retrieve(
        "tenant release",
        agent_id="sona.interpreter.test",
        session_id="sess_scope",
        tenant_id="tenant_a",
        include_claims=False,
        include_episodes=False,
    )

    assert [item.memory_id for item in results] == [fact_a.id]


def test_retrieval_explanation_reports_scope_and_retention_reasons(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    kernel = PromotionKernel(store)
    retrieval = RetrievalKernel(store)

    tenant_a_episodes = [
        store.append_episode(
            _episode(
                session_id="sess_explain",
                kind="intent_recorded",
                payload={
                    "goal": f"Tenant A {index}",
                    "has_constraints": False,
                    "has_success": True,
                },
                receipt_id=f"rcpt_explain_a_{index}",
                tenant_id="tenant_a",
            )
        )
        for index in range(2)
    ]
    tenant_b_episodes = [
        store.append_episode(
            _episode(
                session_id="sess_explain",
                kind="intent_recorded",
                payload={
                    "goal": f"Tenant B {index}",
                    "has_constraints": False,
                    "has_success": True,
                },
                receipt_id=f"rcpt_explain_b_{index}",
                tenant_id="tenant_b",
            )
        )
        for index in range(2)
    ]
    fact_a = kernel.promote_claims_to_fact(
        [kernel.promote_episode_to_claim(ep) for ep in tenant_a_episodes],
        canonical_statement="release status",
    )
    fact_b = kernel.promote_claims_to_fact(
        [kernel.promote_episode_to_claim(ep) for ep in tenant_b_episodes],
        canonical_statement="release status",
    )
    store.update_retention("fact", fact_b.id, RetentionState.ARCHIVED.value)

    explanation = retrieval.explain_retrieval(
        "release status",
        agent_id="sona.interpreter.test",
        session_id="sess_explain",
        tenant_id="tenant_a",
        include_claims=False,
        include_episodes=False,
    )

    assert [item.memory_id for item in explanation.included] == [fact_a.id]
    archived = [
        item for item in explanation.excluded if item.memory_id == fact_b.id
    ][0]
    assert "archived" in archived.retention_reason


def test_retrieval_explanation_reports_trust_and_token_budget(
    tmp_path,
):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    kernel = PromotionKernel(store)
    retrieval = RetrievalKernel(store)
    stable_episode = store.append_episode(
        _episode(
            session_id="sess_explain_budget",
            kind="decision_recorded",
            payload={
                "label": "Deploy safely",
                "option": "canary",
                "has_rationale": True,
            },
            receipt_id="rcpt_explain_budget_a",
        )
    )
    disputed_episode = store.append_episode(
        _episode(
            session_id="sess_explain_budget",
            kind="decision_recorded",
            payload={
                "label": "Deploy safely later",
                "option": "rollback",
                "has_rationale": True,
            },
            receipt_id="rcpt_explain_budget_b",
        )
    )
    stable_claim = kernel.promote_episode_to_claim(stable_episode)
    disputed_claim = kernel.promote_episode_to_claim(
        disputed_episode,
        contradicts_claim_ids=[stable_claim.id],
    )

    trust_explanation = retrieval.explain_retrieval(
        "deploy safely",
        agent_id="sona.interpreter.test",
        session_id="sess_explain_budget",
        include_episodes=False,
    )
    disputed = [
        item
        for item in trust_explanation.excluded
        if item.memory_id == disputed_claim.id
    ][0]
    assert "disputed" in disputed.trust_reason

    token_explanation = retrieval.explain_retrieval(
        "deploy safely",
        agent_id="sona.interpreter.test",
        session_id="sess_explain_budget",
        include_disputed=True,
        include_episodes=False,
        token_budget=4,
    )
    assert any(
        "token budget" in item.token_budget_reason
        for item in token_explanation.excluded
    )


def test_archived_records_are_excluded_from_normal_recall(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    kernel = PromotionKernel(store)
    retrieval = RetrievalKernel(store)
    episodes = [
        store.append_episode(
            _episode(
                session_id="sess_archive",
                kind="intent_recorded",
                payload={
                    "goal": f"Archive {index}",
                    "has_constraints": False,
                    "has_success": True,
                },
                receipt_id=f"rcpt_archive_{index}",
            )
        )
        for index in range(2)
    ]
    fact = kernel.promote_claims_to_fact(
        [kernel.promote_episode_to_claim(episode) for episode in episodes],
        canonical_statement="archived fact",
    )

    store.update_retention("fact", fact.id, RetentionState.ARCHIVED.value)

    results = retrieval.retrieve(
        "archived fact",
        agent_id="sona.interpreter.test",
        session_id="sess_archive",
        include_claims=False,
        include_episodes=False,
    )

    assert results == []


def test_disputed_records_excluded_by_default_and_downranked_when_included(
    tmp_path,
):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    kernel = PromotionKernel(store)
    retrieval = RetrievalKernel(store)
    stable_episode = store.append_episode(
        _episode(
            session_id="sess_dispute",
            kind="decision_recorded",
            payload={
                "label": "Use cache",
                "option": "redis",
                "has_rationale": True,
            },
            receipt_id="rcpt_dispute_1",
        )
    )
    disputed_episode = store.append_episode(
        _episode(
            session_id="sess_dispute",
            kind="decision_recorded",
            payload={
                "label": "Avoid cache",
                "option": "none",
                "has_rationale": True,
            },
            receipt_id="rcpt_dispute_2",
        )
    )
    stable_claim = kernel.promote_episode_to_claim(stable_episode)
    disputed_claim = kernel.promote_episode_to_claim(
        disputed_episode,
        contradicts_claim_ids=[stable_claim.id],
    )

    default_results = retrieval.retrieve(
        "cache",
        agent_id="sona.interpreter.test",
        session_id="sess_dispute",
        include_episodes=False,
    )
    included_results = retrieval.retrieve(
        "cache",
        agent_id="sona.interpreter.test",
        session_id="sess_dispute",
        include_episodes=False,
        include_disputed=True,
    )

    assert [item.memory_id for item in default_results] == [stable_claim.id]
    assert [item.memory_id for item in included_results][:2] == [
        stable_claim.id,
        disputed_claim.id,
    ]
    assert included_results[0].score > included_results[1].score


def test_facts_outrank_raw_episodes_when_equally_relevant(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    kernel = PromotionKernel(store)
    retrieval = RetrievalKernel(store)
    episodes = [
        store.append_episode(
            _episode(
                session_id="sess_rank",
                kind="intent_recorded",
                payload={
                    "goal": "deploy release",
                    "has_constraints": False,
                    "has_success": True,
                },
                receipt_id=f"rcpt_rank_{index}",
            )
        )
        for index in range(2)
    ]
    fact = kernel.promote_claims_to_fact(
        [kernel.promote_episode_to_claim(episode) for episode in episodes],
        canonical_statement="deploy release",
    )

    results = retrieval.retrieve(
        "deploy release",
        agent_id="sona.interpreter.test",
        session_id="sess_rank",
    )

    assert results[0].memory_type == "fact"
    assert results[0].memory_id == fact.id


def test_domain_quota_prevents_episode_flooding(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    kernel = PromotionKernel(store)
    retrieval = RetrievalKernel(store)
    runtime_episodes = [
        store.append_episode(
            _episode(
                session_id="sess_quota",
                kind="working_memory_update",
                payload={"action": "store", "key": f"key_{index}"},
                receipt_id=f"rcpt_quota_{index}",
            )
        )
        for index in range(4)
    ]
    fact = kernel.promote_claims_to_fact(
        [
            kernel.promote_episode_to_claim(runtime_episodes[0]),
            kernel.promote_episode_to_claim(runtime_episodes[1]),
        ],
        canonical_statement="store key",
    )

    results = retrieval.retrieve(
        "store key",
        agent_id="sona.interpreter.test",
        session_id="sess_quota",
        domain_quotas={"runtime": 1, "project": 1},
    )

    assert len(results) == 2
    assert [item.domain for item in results] == ["project", "runtime"]
    assert fact.id in [item.memory_id for item in results]


def test_top_k_and_token_budget_are_respected(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    retrieval = RetrievalKernel(store)
    episodes = [
        store.append_episode(
            _episode(
                session_id="sess_bounds",
                kind="user_input",
                payload={
                    "filename": f"f{index}.sona",
                    "line_count": 1,
                    "text": f"word{index}",
                },
                receipt_id=f"rcpt_bounds_{index}",
            )
        )
        for index in range(4)
    ]
    assert len(episodes) == 4

    results = retrieval.retrieve(
        "",
        agent_id="sona.interpreter.test",
        session_id="sess_bounds",
        include_claims=False,
        top_k=2,
        token_budget=7,
    )

    assert len(results) <= 2
    assert sum(item.token_count for item in results) <= 7
