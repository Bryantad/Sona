"""Rule-based promotion from episodes into durable cognitive memory."""

from __future__ import annotations

from typing import Iterable

from .enums import ProcedureReviewState, RetentionState, TrustState
from .models import Episode, Fact, MemoryClaim, MemoryReceiptRef, Procedure
from .payloads import supported_episode_kinds
from .storage import MemoryStore


class PromotionKernel:
    """Conservative, provenance-aware promotion kernel."""

    def __init__(
        self,
        store: MemoryStore,
        *,
        min_claim_confidence: float = 0.5,
        min_claims_for_fact: int = 2,
        min_success_events_for_procedure: int = 2,
    ):
        self.store = store
        self.min_claim_confidence = float(min_claim_confidence)
        self.min_claims_for_fact = int(min_claims_for_fact)
        self.min_success_events_for_procedure = int(
            min_success_events_for_procedure
        )

    def promote_episode_to_claim(
        self,
        episode: Episode,
        *,
        claim_type: str | None = None,
        statement: str | None = None,
        confidence: float | None = None,
        contradicts_claim_ids: list[str] | None = None,
        supports_claim_ids: list[str] | None = None,
    ) -> MemoryClaim:
        self._require_active_record(
            "episode",
            episode.id,
            episode.retention_state,
        )
        self._require_supported_episode_kind(episode)
        self._require_episode_provenance(episode)

        effective_confidence = self._claim_confidence(episode, confidence)
        if effective_confidence < self.min_claim_confidence:
            raise ValueError(
                f"Episode '{episode.id}' confidence "
                f"{effective_confidence:.2f} is below the claim "
                "promotion threshold"
            )

        claim = MemoryClaim(
            statement=statement or self._statement_from_episode(episode),
            claim_type=claim_type or self._claim_type_from_episode(episode),
            derived_from_episode_ids=[episode.id],
            agent_id=episode.agent_id,
            tenant_id=episode.tenant_id,
            workspace_id=episode.workspace_id,
            project_id=episode.project_id,
            session_id=episode.session_id,
            goal_id=episode.goal_id,
            privacy_scope=episode.privacy_scope,
            confidence=effective_confidence,
            trust_state=(
                TrustState.DISPUTED
                if contradicts_claim_ids
                else TrustState.DERIVED
            ),
            contradicts_claim_ids=list(contradicts_claim_ids or []),
            supports_claim_ids=list(supports_claim_ids or []),
            receipt_refs=list(episode.receipt_refs),
        )
        return self.store.save_claim(claim)

    def promote_claims_to_fact(
        self,
        claims: Iterable[MemoryClaim],
        *,
        canonical_statement: str,
        supersedes_fact_id: str | None = None,
        provenance_summary: str | None = None,
    ) -> Fact:
        claim_list = list(claims)
        if len(claim_list) < self.min_claims_for_fact:
            raise ValueError(
                "Fact promotion requires multiple supporting claims"
            )

        supporting_episode_ids: list[str] = []
        supporting_receipt_refs: list[MemoryReceiptRef] = []
        for claim in claim_list:
            self._require_active_record(
                "claim",
                claim.id,
                claim.retention_state,
            )
            if claim.trust_state == TrustState.DISPUTED:
                raise ValueError(
                    f"Claim '{claim.id}' is disputed and cannot "
                    "promote to fact"
                )
            if not claim.derived_from_episode_ids:
                raise ValueError(
                    f"Claim '{claim.id}' has no supporting episode provenance"
                )
            supporting_episode_ids.extend(claim.derived_from_episode_ids)
            supporting_receipt_refs.extend(claim.receipt_refs)

        deduped_episode_ids = self._dedupe_preserve_order(
            supporting_episode_ids
        )
        supporting_episodes = self._fetch_required_episodes(
            deduped_episode_ids
        )
        if not any(episode.receipt_refs for episode in supporting_episodes):
            raise ValueError(
                "Fact promotion requires reachable receipt provenance from "
                "supporting episodes"
            )

        if (
            supersedes_fact_id is not None
            and self.store.get_fact(supersedes_fact_id) is None
        ):
            raise ValueError(
                f"Superseded fact '{supersedes_fact_id}' does not exist"
            )

        fact = Fact(
            canonical_statement=str(canonical_statement).strip(),
            supporting_claim_ids=[claim.id for claim in claim_list],
            supporting_episode_ids=deduped_episode_ids,
            agent_id=claim_list[0].agent_id,
            tenant_id=claim_list[0].tenant_id,
            workspace_id=claim_list[0].workspace_id,
            project_id=claim_list[0].project_id,
            session_id=claim_list[0].session_id,
            goal_id=claim_list[0].goal_id,
            privacy_scope=claim_list[0].privacy_scope,
            trust_state=TrustState.CONFIRMED,
            supersedes_fact_id=supersedes_fact_id,
            provenance_summary=(
                provenance_summary
                or self._default_fact_summary(claim_list, deduped_episode_ids)
            ),
            receipt_refs=self._merge_receipt_refs(
                supporting_receipt_refs,
                *(episode.receipt_refs for episode in supporting_episodes),
            ),
        )
        return self.store.save_fact(fact)

    def promote_facts_to_procedure(
        self,
        facts: Iterable[Fact],
        *,
        title: str,
        procedure_type: str,
        steps_or_pattern: list[str] | dict[str, object] | str,
        success_episode_ids: list[str] | None = None,
        review_state: ProcedureReviewState = ProcedureReviewState.PENDING,
    ) -> Procedure:
        fact_list = list(facts)
        if not fact_list:
            raise ValueError("Procedure promotion requires at least one fact")

        for fact in fact_list:
            self._require_active_record(
                "fact",
                fact.id,
                fact.retention_state,
            )
            if fact.trust_state == TrustState.DISPUTED:
                raise ValueError(
                    f"Fact '{fact.id}' is disputed and cannot promote "
                    "to procedure"
                )

        evidence_ids = self._dedupe_preserve_order(
            list(success_episode_ids or [])
            or [
                episode_id
                for fact in fact_list
                for episode_id in fact.supporting_episode_ids
            ]
        )
        if len(evidence_ids) < self.min_success_events_for_procedure:
            raise ValueError(
                "Procedure promotion requires repeated successful evidence"
            )

        supporting_episodes = self._fetch_required_episodes(evidence_ids)
        if not any(episode.receipt_refs for episode in supporting_episodes):
            raise ValueError(
                "Procedure promotion requires reachable receipt provenance"
            )

        procedure = Procedure(
            title=str(title).strip(),
            procedure_type=str(procedure_type).strip(),
            steps_or_pattern=steps_or_pattern,
            supporting_fact_ids=[fact.id for fact in fact_list],
            agent_id=fact_list[0].agent_id,
            tenant_id=fact_list[0].tenant_id,
            workspace_id=fact_list[0].workspace_id,
            project_id=fact_list[0].project_id,
            session_id=fact_list[0].session_id,
            goal_id=fact_list[0].goal_id,
            privacy_scope=fact_list[0].privacy_scope,
            trust_state=TrustState.DERIVED,
            success_evidence_ids=evidence_ids,
            review_state=review_state,
            receipt_refs=self._merge_receipt_refs(
                *(fact.receipt_refs for fact in fact_list),
                *(episode.receipt_refs for episode in supporting_episodes),
            ),
        )
        return self.store.save_procedure(procedure)

    def _require_supported_episode_kind(self, episode: Episode) -> None:
        if episode.kind not in supported_episode_kinds():
            raise ValueError(
                f"Episode kind '{episode.kind}' is not eligible for "
                "rule-based claim promotion"
            )

    def _require_episode_provenance(self, episode: Episode) -> None:
        if not episode.receipt_refs:
            raise ValueError(
                f"Episode '{episode.id}' has no receipt provenance and "
                "cannot be promoted"
            )

    def _require_active_record(
        self,
        owner_type: str,
        owner_id: str,
        retention_state: RetentionState,
    ) -> None:
        if retention_state != RetentionState.ACTIVE:
            raise ValueError(
                f"{owner_type.title()} '{owner_id}' is not active and "
                "cannot be promoted"
            )

    def _claim_confidence(
        self,
        episode: Episode,
        explicit_confidence: float | None,
    ) -> float:
        candidates = [
            explicit_confidence,
            episode.confidence,
            episode.importance,
        ]
        for candidate in candidates:
            if candidate is None:
                continue
            return float(candidate)
        return 0.0

    def _statement_from_episode(self, episode: Episode) -> str:
        payload = episode.payload
        if episode.kind == "user_input":
            return (
                "User input received from "
                f"{payload.get('filename', '<unknown>')}"
            )
        if episode.kind == "interpret_failure":
            return (
                f"{payload.get('error_type', 'RuntimeError')} in "
                f"{payload.get('filename', '<unknown>')}: "
                f"{payload.get('message', '')}"
            ).strip()
        if episode.kind == "intent_recorded":
            return f"Intent declared: {payload.get('goal', '')}".strip()
        if episode.kind == "decision_recorded":
            label = payload.get("label", "")
            option = payload.get("option", "")
            return f"Decision recorded: {label} [{option}]".strip()
        if episode.kind == "focus_transition":
            return (
                f"Focus transition: {payload.get('action', '')} "
                f"{payload.get('target', '')}"
            ).strip()
        if episode.kind == "working_memory_update":
            return (
                f"Working memory update: {payload.get('action', '')} "
                f"{payload.get('key', '')}"
            ).strip()
        return f"Observed episode: {episode.kind}"

    def _claim_type_from_episode(self, episode: Episode) -> str:
        mapping = {
            "user_input": "user_input_observation",
            "interpret_failure": "runtime_failure",
            "intent_recorded": "intent",
            "decision_recorded": "decision",
            "focus_transition": "focus_transition",
            "working_memory_update": "working_memory_update",
        }
        return mapping.get(episode.kind, "observation")

    def _fetch_required_episodes(
        self,
        episode_ids: list[str],
    ) -> list[Episode]:
        episodes: list[Episode] = []
        for episode_id in episode_ids:
            episode = self.store.get_episode(episode_id)
            if episode is None:
                raise ValueError(
                    f"Supporting episode '{episode_id}' could not be found"
                )
            episodes.append(episode)
        return episodes

    def _default_fact_summary(
        self,
        claims: list[MemoryClaim],
        episode_ids: list[str],
    ) -> str:
        return (
            f"Derived from {len(claims)} claims and {len(episode_ids)} "
            "supporting episodes"
        )

    def _merge_receipt_refs(
        self,
        *ref_groups: Iterable[MemoryReceiptRef],
    ) -> list[MemoryReceiptRef]:
        merged: list[MemoryReceiptRef] = []
        seen: set[tuple[str, str, int | None]] = set()
        for refs in ref_groups:
            for ref in refs:
                marker = (
                    ref.receipt_id,
                    ref.event_kind_or_path,
                    ref.event_offset,
                )
                if marker in seen:
                    continue
                seen.add(marker)
                merged.append(ref)
        return merged

    def _dedupe_preserve_order(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            deduped.append(value)
        return deduped
