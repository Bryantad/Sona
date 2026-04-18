"""Tests for the consolidation kernel."""

from __future__ import annotations

import pytest

from sona.runtime.memory.enums import RetentionState, TrustState
from sona.runtime.memory.models import (
    Episode,
    Fact,
    MemoryClaim,
    MemoryReceiptRef,
)
from sona.runtime.memory.consolidation import (
    ConsolidationKernel,
    ConsolidationReport,
)
from sona.runtime.memory.sqlite_store import SQLiteMemoryStore


# ── helpers ────────────────────────────────────────────────────────

@pytest.fixture
def store(tmp_path):
    s = SQLiteMemoryStore(tmp_path / "memory.db")
    s.initialize()
    return s


def _ref(tag: str = "test") -> MemoryReceiptRef:
    return MemoryReceiptRef(
        receipt_id=f"receipt_{tag}",
        event_kind_or_path=f"test/{tag}",
    )


def _episode(
    store: SQLiteMemoryStore,
    kind: str = "user_input",
    *,
    payload: dict | None = None,
    importance: float | None = None,
    confidence: float | None = None,
    receipt_tag: str = "a",
    agent_id: str = "agent_1",
    session_id: str = "sess_1",
) -> Episode:
    ep = Episode(
        agent_id=agent_id,
        session_id=session_id,
        kind=kind,
        source_type="test",
        payload=payload or {"filename": "demo.sona"},
        importance=importance,
        confidence=confidence,
        receipt_refs=[_ref(receipt_tag)],
    )
    return store.append_episode(ep)


def _claim(
    store: SQLiteMemoryStore,
    statement: str,
    *,
    episode_ids: list[str] | None = None,
    confidence: float = 0.7,
    trust_state: TrustState = TrustState.DERIVED,
    retention_state: RetentionState = RetentionState.ACTIVE,
    agent_id: str = "agent_1",
    session_id: str = "sess_1",
    receipt_tag: str = "c",
) -> MemoryClaim:
    claim = MemoryClaim(
        statement=statement,
        claim_type="observation",
        derived_from_episode_ids=episode_ids or [],
        confidence=confidence,
        trust_state=trust_state,
        retention_state=retention_state,
        agent_id=agent_id,
        session_id=session_id,
        receipt_refs=[_ref(receipt_tag)],
    )
    return store.save_claim(claim)


# ── duplicate claim grouping ──────────────────────────────────────

class TestDuplicateClaimGrouping:
    def test_identical_statements_form_group(self, store):
        c1 = _claim(store, "X is true", receipt_tag="r1")
        c2 = _claim(store, "X is true", receipt_tag="r2")
        c3 = _claim(store, "Y is true", receipt_tag="r3")

        kernel = ConsolidationKernel(store)
        report = kernel.run(agent_id="agent_1")

        assert len(report.duplicate_claim_groups) == 1
        grp = report.duplicate_claim_groups[0]
        assert set(grp.claim_ids) == {c1.id, c2.id}
        assert grp.representative_claim_id in {c1.id, c2.id}

    def test_case_insensitive_matching(self, store):
        _claim(store, "Hello World", receipt_tag="r1")
        _claim(store, "hello world", receipt_tag="r2")

        kernel = ConsolidationKernel(store)
        report = kernel.run(agent_id="agent_1")

        assert len(report.duplicate_claim_groups) == 1

    def test_no_group_for_single_claim(self, store):
        _claim(store, "Unique claim", receipt_tag="r1")

        kernel = ConsolidationKernel(store)
        report = kernel.run(agent_id="agent_1")

        assert len(report.duplicate_claim_groups) == 0

    def test_archived_claims_excluded(self, store):
        _claim(store, "Dupe", receipt_tag="r1")
        _claim(
            store, "Dupe", receipt_tag="r2",
            retention_state=RetentionState.ARCHIVED,
        )

        kernel = ConsolidationKernel(store)
        report = kernel.run(agent_id="agent_1")

        assert len(report.duplicate_claim_groups) == 0

    def test_persist_creates_links(self, store):
        c1 = _claim(store, "Dupe X", confidence=0.9, receipt_tag="r1")
        c2 = _claim(store, "Dupe X", confidence=0.5, receipt_tag="r2")

        kernel = ConsolidationKernel(store)
        report = kernel.run(agent_id="agent_1", persist=True)

        dup_links = [
            l for l in report.links_created
            if l.relation_type == "duplicate_of"
        ]
        assert len(dup_links) == 1
        assert dup_links[0].from_id == c2.id
        assert dup_links[0].to_id == c1.id


# ── repeated-episode clustering ───────────────────────────────────

class TestEpisodeClustering:
    def test_cluster_emits_candidate_claim(self, store):
        for i in range(3):
            _episode(store, "user_input", receipt_tag=f"e{i}")

        kernel = ConsolidationKernel(store, min_episode_cluster=3)
        report = kernel.run(agent_id="agent_1")

        assert len(report.candidate_claims) == 1
        cc = report.candidate_claims[0]
        assert len(cc.source_episode_ids) == 3
        assert cc.claim_type == "user_input_observation"

    def test_below_threshold_no_candidate(self, store):
        _episode(store, "user_input", receipt_tag="e0")
        _episode(store, "user_input", receipt_tag="e1")

        kernel = ConsolidationKernel(store, min_episode_cluster=3)
        report = kernel.run(agent_id="agent_1")

        assert len(report.candidate_claims) == 0

    def test_different_kinds_not_clustered(self, store):
        for i in range(3):
            _episode(store, "user_input", receipt_tag=f"e{i}")
        for i in range(3):
            _episode(
                store, "intent_recorded",
                payload={"goal": "test"},
                receipt_tag=f"g{i}",
            )

        kernel = ConsolidationKernel(store, min_episode_cluster=3)
        report = kernel.run(agent_id="agent_1")

        # Each kind forms its own cluster
        assert len(report.candidate_claims) == 2

    def test_episodes_without_provenance_excluded(self, store):
        for _ in range(3):
            ep = Episode(
                agent_id="agent_1",
                session_id="sess_1",
                kind="user_input",
                source_type="test",
                payload={"filename": "demo.sona"},
                receipt_refs=[],  # no provenance
            )
            store.append_episode(ep)

        kernel = ConsolidationKernel(store, min_episode_cluster=3)
        report = kernel.run(agent_id="agent_1")

        assert len(report.candidate_claims) == 0

    def test_persist_saves_claim(self, store):
        for i in range(3):
            _episode(store, "user_input", receipt_tag=f"e{i}")

        kernel = ConsolidationKernel(store, min_episode_cluster=3)
        report = kernel.run(agent_id="agent_1", persist=True)

        assert len(report.candidate_claims) == 1
        claims = store.query_claims(agent_id="agent_1")
        assert any(
            c.claim_type == "user_input_observation" for c in claims
        )


# ── candidate fact detection ──────────────────────────────────────

class TestCandidateFactDetection:
    def test_repeated_claims_surface_candidate_fact(self, store):
        ep = _episode(store, receipt_tag="base")
        _claim(
            store, "Pattern observed",
            episode_ids=[ep.id], receipt_tag="c1",
        )
        _claim(
            store, "Pattern observed",
            episode_ids=[ep.id], receipt_tag="c2",
        )

        kernel = ConsolidationKernel(store, min_claims_for_candidate_fact=2)
        report = kernel.run(agent_id="agent_1")

        assert len(report.candidate_facts) == 1
        cf = report.candidate_facts[0]
        assert cf.canonical_statement == "pattern observed"
        assert len(cf.supporting_claim_ids) == 2

    def test_disputed_claims_excluded(self, store):
        _claim(
            store, "Suspect thing",
            trust_state=TrustState.DISPUTED, receipt_tag="c1",
        )
        _claim(
            store, "Suspect thing",
            trust_state=TrustState.DISPUTED, receipt_tag="c2",
        )

        kernel = ConsolidationKernel(store, min_claims_for_candidate_fact=2)
        report = kernel.run(agent_id="agent_1")

        assert len(report.candidate_facts) == 0

    def test_existing_fact_not_duplicated(self, store):
        ep = _episode(store, receipt_tag="base")
        c1 = _claim(
            store, "Already known",
            episode_ids=[ep.id], receipt_tag="c1",
        )
        c2 = _claim(
            store, "Already known",
            episode_ids=[ep.id], receipt_tag="c2",
        )

        # Pre-create the fact
        fact = Fact(
            canonical_statement="Already known",
            supporting_claim_ids=[c1.id, c2.id],
            supporting_episode_ids=[ep.id],
            agent_id="agent_1",
            receipt_refs=[_ref("f1")],
        )
        store.save_fact(fact)

        kernel = ConsolidationKernel(store, min_claims_for_candidate_fact=2)
        report = kernel.run(agent_id="agent_1")

        assert len(report.candidate_facts) == 0

    def test_persist_saves_fact_and_links(self, store):
        ep = _episode(store, receipt_tag="base")
        _claim(
            store, "Persistent pattern",
            episode_ids=[ep.id], receipt_tag="c1",
        )
        _claim(
            store, "Persistent pattern",
            episode_ids=[ep.id], receipt_tag="c2",
        )

        kernel = ConsolidationKernel(store, min_claims_for_candidate_fact=2)
        report = kernel.run(agent_id="agent_1", persist=True)

        assert len(report.candidate_facts) == 1
        facts = store.query_facts(agent_id="agent_1")
        assert any(
            f.canonical_statement == "persistent pattern" for f in facts
        )
        assert len(report.links_created) >= 2  # one per supporting claim


# ── noise detection ───────────────────────────────────────────────

class TestNoiseDetection:
    def test_low_importance_flagged(self, store):
        _episode(store, importance=0.05, receipt_tag="low")
        _episode(store, importance=0.8, receipt_tag="high")

        kernel = ConsolidationKernel(store, noise_max_importance=0.1)
        report = kernel.run(agent_id="agent_1")

        assert len(report.noise_flags) == 1
        assert "0.05" in report.noise_flags[0].reason

    def test_no_importance_not_flagged(self, store):
        _episode(store, receipt_tag="noimport")

        kernel = ConsolidationKernel(store, noise_max_importance=0.1)
        report = kernel.run(agent_id="agent_1")

        assert len(report.noise_flags) == 0

    def test_archived_episodes_not_flagged(self, store):
        ep = _episode(store, importance=0.01, receipt_tag="arch")
        store.update_retention("episode", ep.id, "archived")

        kernel = ConsolidationKernel(store, noise_max_importance=0.1)
        report = kernel.run(agent_id="agent_1")

        assert len(report.noise_flags) == 0


# ── provenance preservation ───────────────────────────────────────

class TestProvenancePreservation:
    def test_persisted_claim_has_receipt_refs(self, store):
        for i in range(3):
            _episode(store, "user_input", receipt_tag=f"prov{i}")

        kernel = ConsolidationKernel(store, min_episode_cluster=3)
        kernel.run(agent_id="agent_1", persist=True)

        claims = store.query_claims(agent_id="agent_1")
        consolidated = [
            c for c in claims if c.claim_type == "user_input_observation"
        ]
        assert len(consolidated) >= 1
        assert len(consolidated[0].receipt_refs) > 0

    def test_source_episodes_not_deleted(self, store):
        ep_ids = []
        for i in range(3):
            ep = _episode(store, "user_input", receipt_tag=f"src{i}")
            ep_ids.append(ep.id)

        kernel = ConsolidationKernel(store, min_episode_cluster=3)
        kernel.run(agent_id="agent_1", persist=True)

        for eid in ep_ids:
            assert store.get_episode(eid) is not None

    def test_persisted_fact_has_provenance(self, store):
        ep = _episode(store, receipt_tag="base")
        _claim(
            store, "Provenance check",
            episode_ids=[ep.id], receipt_tag="pc1",
        )
        _claim(
            store, "Provenance check",
            episode_ids=[ep.id], receipt_tag="pc2",
        )

        kernel = ConsolidationKernel(store, min_claims_for_candidate_fact=2)
        kernel.run(agent_id="agent_1", persist=True)

        facts = store.query_facts(agent_id="agent_1")
        target = [
            f for f in facts
            if f.canonical_statement == "provenance check"
        ]
        assert len(target) == 1
        assert len(target[0].receipt_refs) > 0
        assert ep.id in target[0].supporting_episode_ids


# ── report structure ──────────────────────────────────────────────

class TestReportStructure:
    def test_empty_store_produces_empty_report(self, store):
        kernel = ConsolidationKernel(store)
        report = kernel.run()

        assert isinstance(report, ConsolidationReport)
        assert report.duplicate_claim_groups == []
        assert report.candidate_claims == []
        assert report.candidate_facts == []
        assert report.noise_flags == []
        assert report.links_created == []
        assert report.errors == []
        assert report.timestamp is not None

    def test_report_has_timestamp(self, store):
        kernel = ConsolidationKernel(store)
        report = kernel.run()
        assert report.timestamp.endswith("Z")
