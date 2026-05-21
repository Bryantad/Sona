"""Deterministic consolidation kernel for persistent memory.

Consolidation scans stored memory and produces *candidate* promotions,
duplicate-group markers, and supersession links.  It never mutates raw
episodic payloads, never deletes source episodes, and never breaks
provenance reachability.

Design rules
~~~~~~~~~~~~
* First pass is **rule-based and deterministic** — no fuzzy similarity
  or embedding vectors.
* Reuses :class:`PromotionKernel` rather than duplicating promotion
  semantics.
* Produces :class:`MemoryLink` records for new relationships.
* All reads go through the existing :class:`MemoryStore` query surface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict
from typing import Any

from .enums import RetentionState, TrustState
from .ids import utc_now
from .models import Episode, Fact, MemoryClaim, MemoryLink
from .promotion import PromotionKernel
from .storage import MemoryStore


# ── result containers ──────────────────────────────────────────────

@dataclass(slots=True)
class DuplicateClaimGroup:
    """A set of claims that share the same canonical statement."""
    canonical_statement: str
    claim_ids: list[str]
    representative_claim_id: str


@dataclass(slots=True)
class CandidateClaim:
    """A claim derived from repeated similar episodes."""
    statement: str
    claim_type: str
    source_episode_ids: list[str]
    confidence: float


@dataclass(slots=True)
class CandidateFact:
    """A fact candidate derived from repeated stable claims."""
    canonical_statement: str
    supporting_claim_ids: list[str]
    supporting_episode_ids: list[str]


@dataclass(slots=True)
class NoiseFlag:
    """An episode flagged as low-value noise."""
    episode_id: str
    reason: str


@dataclass(slots=True)
class ConsolidationReport:
    """Aggregate result of a single consolidation pass."""
    timestamp: str = field(default_factory=utc_now)
    duplicate_claim_groups: list[DuplicateClaimGroup] = field(
        default_factory=list,
    )
    candidate_claims: list[CandidateClaim] = field(default_factory=list)
    candidate_facts: list[CandidateFact] = field(default_factory=list)
    noise_flags: list[NoiseFlag] = field(default_factory=list)
    links_created: list[MemoryLink] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# ── kernel ─────────────────────────────────────────────────────────

class ConsolidationKernel:
    """Rule-based consolidation over the stored memory graph.

    Parameters
    ----------
    store:
        Backend that satisfies the :class:`MemoryStore` contract.
    min_episode_cluster:
        Minimum number of same-kind episodes with identical payload
        keys required before a candidate claim is emitted.
    min_claims_for_candidate_fact:
        Minimum identical-statement active claims needed to surface
        a candidate fact.
    noise_max_importance:
        Episodes at or below this importance value are flagged as
        low-value noise (only when *importance* is explicitly set).
    """

    def __init__(
        self,
        store: MemoryStore,
        *,
        min_episode_cluster: int = 3,
        min_claims_for_candidate_fact: int = 2,
        noise_max_importance: float = 0.1,
    ) -> None:
        self.store = store
        self.min_episode_cluster = min_episode_cluster
        self.min_claims_for_candidate_fact = min_claims_for_candidate_fact
        self.noise_max_importance = noise_max_importance
        self._promotion = PromotionKernel(store)

    # ── public entry point ─────────────────────────────────────────

    def run(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        episode_limit: int = 200,
        claim_limit: int = 200,
        persist: bool = False,
    ) -> ConsolidationReport:
        """Execute a single consolidation pass and return a report.

        When *persist* is ``True`` the kernel writes candidate claims,
        candidate facts, and duplicate-group links into the store.
        When ``False`` (default) the report is advisory only.
        """
        report = ConsolidationReport()

        episodes = self.store.query_episodes(
            agent_id=agent_id,
            session_id=session_id,
            limit=episode_limit,
        )
        claims = self.store.query_claims(
            agent_id=agent_id,
            session_id=session_id,
            limit=claim_limit,
        )

        self._detect_duplicate_claims(claims, report, persist=persist)
        self._detect_episode_clusters(episodes, report, persist=persist)
        self._detect_candidate_facts(claims, report, persist=persist)
        self._detect_noise(episodes, report)

        return report

    # ── duplicate claim grouping ───────────────────────────────────

    def _detect_duplicate_claims(
        self,
        claims: list[MemoryClaim],
        report: ConsolidationReport,
        *,
        persist: bool,
    ) -> None:
        active = [
            c for c in claims
            if c.retention_state == RetentionState.ACTIVE
        ]

        by_statement: dict[str, list[MemoryClaim]] = defaultdict(list)
        for claim in active:
            key = claim.statement.strip().lower()
            by_statement[key].append(claim)

        for canonical, group in by_statement.items():
            if len(group) < 2:
                continue

            best = max(group, key=lambda c: c.confidence or 0.0)
            group_obj = DuplicateClaimGroup(
                canonical_statement=canonical,
                claim_ids=[c.id for c in group],
                representative_claim_id=best.id,
            )
            report.duplicate_claim_groups.append(group_obj)

            if persist:
                for claim in group:
                    if claim.id == best.id:
                        continue
                    link = MemoryLink(
                        from_id=claim.id,
                        to_id=best.id,
                        relation_type="duplicate_of",
                    )
                    saved = self.store.add_link(link)
                    report.links_created.append(saved)

    # ── repeated-episode clustering ────────────────────────────────

    def _detect_episode_clusters(
        self,
        episodes: list[Episode],
        report: ConsolidationReport,
        *,
        persist: bool,
    ) -> None:
        active = [
            e for e in episodes
            if e.retention_state == RetentionState.ACTIVE
            and e.receipt_refs  # provenance required
        ]

        by_signature: dict[str, list[Episode]] = defaultdict(list)
        for ep in active:
            sig = self._episode_signature(ep)
            by_signature[sig].append(ep)

        for _sig, cluster in by_signature.items():
            if len(cluster) < self.min_episode_cluster:
                continue

            statement = self._promotion._statement_from_episode(cluster[0])
            claim_type = self._promotion._claim_type_from_episode(cluster[0])
            avg_confidence = self._cluster_confidence(cluster)

            candidate = CandidateClaim(
                statement=statement,
                claim_type=claim_type,
                source_episode_ids=[e.id for e in cluster],
                confidence=avg_confidence,
            )
            report.candidate_claims.append(candidate)

            if persist:
                self._persist_candidate_claim(candidate, cluster, report)

    def _episode_signature(self, episode: Episode) -> str:
        """Deterministic key: kind + sorted payload keys."""
        sorted_keys = ",".join(sorted(episode.payload.keys()))
        return f"{episode.kind}::{sorted_keys}"

    def _cluster_confidence(self, cluster: list[Episode]) -> float:
        values = [
            e.confidence if e.confidence is not None
            else (e.importance if e.importance is not None else 0.5)
            for e in cluster
        ]
        return sum(values) / len(values) if values else 0.5

    def _persist_candidate_claim(
        self,
        candidate: CandidateClaim,
        cluster: list[Episode],
        report: ConsolidationReport,
    ) -> None:
        merged_refs = []
        seen: set[str] = set()
        for ep in cluster:
            for ref in ep.receipt_refs:
                if ref.receipt_id not in seen:
                    seen.add(ref.receipt_id)
                    merged_refs.append(ref)

        claim = MemoryClaim(
            statement=candidate.statement,
            claim_type=candidate.claim_type,
            derived_from_episode_ids=list(candidate.source_episode_ids),
            confidence=candidate.confidence,
            trust_state=TrustState.DERIVED,
            agent_id=cluster[0].agent_id,
            tenant_id=cluster[0].tenant_id,
            workspace_id=cluster[0].workspace_id,
            project_id=cluster[0].project_id,
            session_id=cluster[0].session_id,
            goal_id=cluster[0].goal_id,
            privacy_scope=cluster[0].privacy_scope,
            receipt_refs=merged_refs,
        )
        self.store.save_claim(claim)

    # ── candidate fact detection ───────────────────────────────────

    def _detect_candidate_facts(
        self,
        claims: list[MemoryClaim],
        report: ConsolidationReport,
        *,
        persist: bool,
    ) -> None:
        active = [
            c for c in claims
            if c.retention_state == RetentionState.ACTIVE
            and c.trust_state != TrustState.DISPUTED
        ]

        by_statement: dict[str, list[MemoryClaim]] = defaultdict(list)
        for claim in active:
            key = claim.statement.strip().lower()
            by_statement[key].append(claim)

        existing_facts = self.store.query_facts(limit=200)
        existing_fact_keys = {
            f.canonical_statement.strip().lower()
            for f in existing_facts
            if f.retention_state == RetentionState.ACTIVE
        }

        for canonical, group in by_statement.items():
            if len(group) < self.min_claims_for_candidate_fact:
                continue
            if canonical in existing_fact_keys:
                continue

            all_episode_ids: list[str] = []
            seen_ep: set[str] = set()
            for c in group:
                for eid in c.derived_from_episode_ids:
                    if eid not in seen_ep:
                        seen_ep.add(eid)
                        all_episode_ids.append(eid)

            candidate = CandidateFact(
                canonical_statement=canonical,
                supporting_claim_ids=[c.id for c in group],
                supporting_episode_ids=all_episode_ids,
            )
            report.candidate_facts.append(candidate)

            if persist:
                self._persist_candidate_fact(candidate, group, report)

    def _persist_candidate_fact(
        self,
        candidate: CandidateFact,
        claims: list[MemoryClaim],
        report: ConsolidationReport,
    ) -> None:
        merged_refs = []
        seen: set[str] = set()
        for claim in claims:
            for ref in claim.receipt_refs:
                if ref.receipt_id not in seen:
                    seen.add(ref.receipt_id)
                    merged_refs.append(ref)

        fact = Fact(
            canonical_statement=candidate.canonical_statement,
            supporting_claim_ids=list(candidate.supporting_claim_ids),
            supporting_episode_ids=list(candidate.supporting_episode_ids),
            agent_id=claims[0].agent_id,
            tenant_id=claims[0].tenant_id,
            workspace_id=claims[0].workspace_id,
            project_id=claims[0].project_id,
            session_id=claims[0].session_id,
            goal_id=claims[0].goal_id,
            privacy_scope=claims[0].privacy_scope,
            trust_state=TrustState.DERIVED,
            receipt_refs=merged_refs,
        )
        saved_fact = self.store.save_fact(fact)

        for claim in claims:
            link = MemoryLink(
                from_id=claim.id,
                to_id=saved_fact.id,
                relation_type="supports",
            )
            saved_link = self.store.add_link(link)
            report.links_created.append(saved_link)

    # ── noise detection ────────────────────────────────────────────

    def _detect_noise(
        self,
        episodes: list[Episode],
        report: ConsolidationReport,
    ) -> None:
        for ep in episodes:
            if ep.retention_state != RetentionState.ACTIVE:
                continue
            if ep.importance is not None and ep.importance <= self.noise_max_importance:
                report.noise_flags.append(
                    NoiseFlag(
                        episode_id=ep.id,
                        reason=(
                            f"importance {ep.importance} <= "
                            f"threshold {self.noise_max_importance}"
                        ),
                    )
                )
