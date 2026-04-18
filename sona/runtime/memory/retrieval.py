"""Scoped retrieval over promoted and episodic memory objects."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone

from .enums import RetentionState, TrustState
from .models import Episode, Fact, MemoryClaim, Procedure
from .storage import MemoryStore


@dataclass(frozen=True, slots=True)
class RetrievedMemory:
    memory_type: str
    memory_id: str
    domain: str
    score: float
    token_count: int
    text: str
    memory: Episode | MemoryClaim | Fact | Procedure
    included: bool = True
    scope_reason: str = "matched"
    retention_reason: str = "included: active record"
    trust_reason: str = "included: trust state allowed"
    ranking_components: dict[str, float] = field(default_factory=dict)
    quota_reason: str = "included within limits"
    token_budget_reason: str = "not applied"


@dataclass(frozen=True, slots=True)
class RetrievalExplanation:
    included: list[RetrievedMemory]
    excluded: list[RetrievedMemory]
    top_k: int
    token_budget: int | None
    evaluated_candidates: int


class RetrievalKernel:
    """Filter, rank, and bound recall over durable memory objects."""

    def __init__(self, store: MemoryStore):
        self.store = store

    def retrieve(
        self,
        query_text: str,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
        project_id: str | None = None,
        goal_id: str | None = None,
        privacy_scope: str | None = None,
        domains: set[str] | None = None,
        include_claims: bool = True,
        include_episodes: bool = True,
        include_disputed: bool = False,
        include_archived: bool = False,
        top_k: int = 10,
        token_budget: int | None = None,
        domain_quotas: dict[str, int] | None = None,
    ) -> list[RetrievedMemory]:
        return self.explain_retrieval(
            query_text,
            agent_id=agent_id,
            session_id=session_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            goal_id=goal_id,
            privacy_scope=privacy_scope,
            domains=domains,
            include_claims=include_claims,
            include_episodes=include_episodes,
            include_disputed=include_disputed,
            include_archived=include_archived,
            top_k=top_k,
            token_budget=token_budget,
            domain_quotas=domain_quotas,
        ).included

    def explain_retrieval(
        self,
        query_text: str,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
        project_id: str | None = None,
        goal_id: str | None = None,
        privacy_scope: str | None = None,
        domains: set[str] | None = None,
        include_claims: bool = True,
        include_episodes: bool = True,
        include_disputed: bool = False,
        include_archived: bool = False,
        top_k: int = 10,
        token_budget: int | None = None,
        domain_quotas: dict[str, int] | None = None,
    ) -> RetrievalExplanation:
        candidates = self._collect_candidates(
            agent_id=agent_id,
            session_id=session_id,
            include_claims=include_claims,
            include_episodes=include_episodes,
        )

        eligible: list[RetrievedMemory] = []
        excluded: list[RetrievedMemory] = []
        for memory in candidates:
            domain = self._domain_for(memory)
            text = self._text_for(memory)
            ranking_components = self._score_components(
                memory,
                query_text,
                text,
            )
            scope_ok, scope_reason = self._scope_decision(
                memory,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                project_id=project_id,
                goal_id=goal_id,
                privacy_scope=privacy_scope,
            )
            retention_ok, retention_reason = self._retention_decision(
                memory,
                include_archived,
            )
            trust_ok, trust_reason = self._trust_decision(
                memory,
                include_disputed,
            )
            if domains is not None and domain not in domains:
                scope_ok = False
                scope_reason = (
                    f"excluded: domain '{domain}' not in allowed domains"
                )

            decision = RetrievedMemory(
                memory_type=self._memory_type(memory),
                memory_id=self._memory_id(memory),
                domain=domain,
                score=ranking_components["total"],
                token_count=self._token_count(text),
                text=text,
                memory=memory,
                included=False,
                scope_reason=scope_reason,
                retention_reason=retention_reason,
                trust_reason=trust_reason,
                ranking_components=ranking_components,
                quota_reason="not evaluated",
                token_budget_reason=(
                    "not applied"
                    if token_budget is None
                    else "not evaluated"
                ),
            )
            if not scope_ok or not retention_ok or not trust_ok:
                excluded.append(decision)
                continue
            eligible.append(decision)

        eligible.sort(
            key=lambda item: (
                -item.score,
                item.memory_id,
            )
        )

        quota_counts: dict[str, int] = {}
        token_total = 0
        included: list[RetrievedMemory] = []
        for item in eligible:
            if len(included) >= top_k:
                excluded.append(
                    replace(
                        item,
                        quota_reason="excluded: top_k limit reached",
                    )
                )
                continue
            if domain_quotas is not None:
                allowed = domain_quotas.get(item.domain)
                used = quota_counts.get(item.domain, 0)
                if allowed is not None and used >= allowed:
                    excluded.append(
                        replace(
                            item,
                            quota_reason=(
                                f"excluded: domain quota reached for "
                                f"'{item.domain}'"
                            ),
                        )
                    )
                    continue
            if (
                token_budget is not None
                and included
                and token_total + item.token_count > token_budget
            ):
                excluded.append(
                    replace(
                        item,
                        token_budget_reason=(
                            "excluded: token budget would be exceeded"
                        ),
                    )
                )
                continue
            if (
                token_budget is not None
                and not included
                and item.token_count > token_budget
            ):
                excluded.append(
                    replace(
                        item,
                        token_budget_reason=(
                            "excluded: single item exceeds token budget"
                        ),
                    )
                )
                continue

            included.append(
                replace(
                    item,
                    included=True,
                    quota_reason="included within limits",
                    token_budget_reason=(
                        "not applied"
                        if token_budget is None
                        else "included within token budget"
                    ),
                )
            )
            quota_counts[item.domain] = quota_counts.get(item.domain, 0) + 1
            token_total += item.token_count

        return RetrievalExplanation(
            included=included,
            excluded=excluded,
            top_k=top_k,
            token_budget=token_budget,
            evaluated_candidates=len(candidates),
        )

    def _collect_candidates(
        self,
        *,
        agent_id: str | None,
        session_id: str | None,
        include_claims: bool,
        include_episodes: bool,
    ) -> list[Episode | MemoryClaim | Fact | Procedure]:
        candidates: list[Episode | MemoryClaim | Fact | Procedure] = []
        candidates.extend(
            self.store.query_procedures(
                agent_id=agent_id,
                session_id=session_id,
                limit=200,
            )
        )
        candidates.extend(
            self.store.query_facts(
                agent_id=agent_id,
                session_id=session_id,
                limit=200,
            )
        )
        if include_claims:
            candidates.extend(
                self.store.query_claims(
                    agent_id=agent_id,
                    session_id=session_id,
                    limit=200,
                )
            )
        if include_episodes:
            candidates.extend(
                self.store.query_episodes(
                    agent_id=agent_id,
                    session_id=session_id,
                    limit=200,
                )
            )
        return candidates

    def _matches_scope(
        self,
        memory: Episode | MemoryClaim | Fact | Procedure,
        *,
        tenant_id: str | None,
        workspace_id: str | None,
        project_id: str | None,
        goal_id: str | None,
        privacy_scope: str | None,
    ) -> bool:
        matched, _ = self._scope_decision(
            memory,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            goal_id=goal_id,
            privacy_scope=privacy_scope,
        )
        return matched

    def _scope_decision(
        self,
        memory: Episode | MemoryClaim | Fact | Procedure,
        *,
        tenant_id: str | None,
        workspace_id: str | None,
        project_id: str | None,
        goal_id: str | None,
        privacy_scope: str | None,
    ) -> tuple[bool, str]:
        if (
            tenant_id is not None
            and getattr(memory, "tenant_id", None) != tenant_id
        ):
            return False, "excluded: tenant scope mismatch"
        if (
            workspace_id is not None
            and getattr(memory, "workspace_id", None) != workspace_id
        ):
            return False, "excluded: workspace scope mismatch"
        if (
            project_id is not None
            and getattr(memory, "project_id", None) != project_id
        ):
            return False, "excluded: project scope mismatch"
        if goal_id is not None and getattr(memory, "goal_id", None) != goal_id:
            return False, "excluded: goal scope mismatch"
        if (
            privacy_scope is not None
            and getattr(memory, "privacy_scope", None) != privacy_scope
        ):
            return False, "excluded: privacy scope mismatch"
        return True, "matched"

    def _matches_retention(
        self,
        memory: Episode | MemoryClaim | Fact | Procedure,
        include_archived: bool,
    ) -> bool:
        matched, _ = self._retention_decision(memory, include_archived)
        return matched

    def _retention_decision(
        self,
        memory: Episode | MemoryClaim | Fact | Procedure,
        include_archived: bool,
    ) -> tuple[bool, str]:
        retention_state = getattr(
            memory,
            "retention_state",
            RetentionState.ACTIVE,
        )
        if retention_state == RetentionState.FORGOTTEN:
            return False, "excluded: forgotten records are not retrievable"
        if retention_state == RetentionState.DELETED:
            return False, "excluded: deleted records are tombstoned"
        if retention_state == RetentionState.ARCHIVED and not include_archived:
            return False, "excluded: archived records hidden by default"
        if retention_state == RetentionState.ARCHIVED:
            return True, "included: archived records allowed by caller"
        return True, "included: active record"

    def _matches_dispute(
        self,
        memory: Episode | MemoryClaim | Fact | Procedure,
        include_disputed: bool,
    ) -> bool:
        matched, _ = self._trust_decision(memory, include_disputed)
        return matched

    def _trust_decision(
        self,
        memory: Episode | MemoryClaim | Fact | Procedure,
        include_disputed: bool,
    ) -> tuple[bool, str]:
        trust_state = getattr(memory, "trust_state", None)
        if trust_state == TrustState.DISPUTED and not include_disputed:
            return False, "excluded: disputed records hidden by default"
        if trust_state == TrustState.DISPUTED:
            return True, "included: disputed records allowed by caller"
        return True, "included: trust state allowed"

    def _memory_type(
        self,
        memory: Episode | MemoryClaim | Fact | Procedure,
    ) -> str:
        if isinstance(memory, Procedure):
            return "procedure"
        if isinstance(memory, Fact):
            return "fact"
        if isinstance(memory, MemoryClaim):
            return "claim"
        return "episode"

    def _memory_id(
        self,
        memory: Episode | MemoryClaim | Fact | Procedure,
    ) -> str:
        return str(getattr(memory, "id"))

    def _domain_for(
        self,
        memory: Episode | MemoryClaim | Fact | Procedure,
    ) -> str:
        if isinstance(memory, Procedure):
            return "procedural"
        if isinstance(memory, (Fact, MemoryClaim)):
            return "project"
        if isinstance(memory, Episode):
            if memory.kind == "user_input":
                return "user"
            if memory.source_type == "runtime":
                return "runtime"
        return "project"

    def _text_for(
        self,
        memory: Episode | MemoryClaim | Fact | Procedure,
    ) -> str:
        if isinstance(memory, Procedure):
            if isinstance(memory.steps_or_pattern, list):
                pattern_text = " ".join(
                    str(step) for step in memory.steps_or_pattern
                )
            elif isinstance(memory.steps_or_pattern, dict):
                pattern_text = " ".join(
                    f"{key} {value}"
                    for key, value in sorted(memory.steps_or_pattern.items())
                )
            else:
                pattern_text = str(memory.steps_or_pattern)
            return " ".join(
                part
                for part in (
                    memory.title,
                    memory.procedure_type,
                    pattern_text,
                )
                if part
            ).strip()
        if isinstance(memory, Fact):
            extra = memory.provenance_summary or ""
            return f"{memory.canonical_statement} {extra}".strip()
        if isinstance(memory, MemoryClaim):
            return f"{memory.statement} {memory.claim_type}".strip()

        payload_values = []
        for key, value in sorted(memory.payload.items()):
            if isinstance(value, list):
                payload_values.append(" ".join(str(item) for item in value))
            elif isinstance(value, dict):
                payload_values.append(
                    " ".join(
                        f"{child_key} {child_value}"
                        for child_key, child_value in sorted(value.items())
                    )
                )
            else:
                payload_values.append(str(value))
        return f"{memory.kind} {' '.join(payload_values)}".strip()

    def _score_memory(
        self,
        memory: Episode | MemoryClaim | Fact | Procedure,
        query_text: str,
        text: str,
    ) -> float:
        return self._score_components(memory, query_text, text)["total"]

    def _score_components(
        self,
        memory: Episode | MemoryClaim | Fact | Procedure,
        query_text: str,
        text: str,
    ) -> dict[str, float]:
        base_kind = self._base_kind_score(memory)
        trust = self._trust_score(memory)
        recency = self._recency_score(memory)
        relevance = self._relevance_score(query_text, text)
        importance_value = getattr(memory, "importance", None)
        importance = 0.0
        if isinstance(importance_value, (int, float)):
            importance = float(importance_value)
        confidence = getattr(memory, "confidence", None)
        confidence_score = 0.0
        if isinstance(confidence, (int, float)):
            confidence_score = float(confidence) * 0.5
        total = (
            base_kind
            + trust
            + recency
            + relevance
            + importance
            + confidence_score
        )
        return {
            "base_kind": base_kind,
            "trust": trust,
            "recency": recency,
            "relevance": relevance,
            "importance": importance,
            "confidence": confidence_score,
            "total": total,
        }

    def _base_kind_score(
        self,
        memory: Episode | MemoryClaim | Fact | Procedure,
    ) -> float:
        if isinstance(memory, Procedure):
            return 4.0
        if isinstance(memory, Fact):
            return 3.0
        if isinstance(memory, MemoryClaim):
            return 2.0
        return 1.0

    def _trust_score(
        self,
        memory: Episode | MemoryClaim | Fact | Procedure,
    ) -> float:
        trust_state = getattr(memory, "trust_state", TrustState.OBSERVED)
        weights = {
            TrustState.UNVERIFIED: -0.5,
            TrustState.OBSERVED: 0.0,
            TrustState.DERIVED: 0.5,
            TrustState.CONFIRMED: 1.0,
            TrustState.DISPUTED: -1.0,
        }
        return weights.get(trust_state, 0.0)

    def _recency_score(
        self,
        memory: Episode | MemoryClaim | Fact | Procedure,
    ) -> float:
        timestamp = (
            getattr(memory, "timestamp", None)
            or getattr(memory, "updated_at", None)
            or getattr(memory, "created_at", None)
        )
        if not timestamp:
            return 0.0
        try:
            parsed = datetime.fromisoformat(
                str(timestamp).replace("Z", "+00:00")
            )
        except ValueError:
            return 0.0
        now = datetime.now(timezone.utc)
        delta_seconds = max((now - parsed).total_seconds(), 0.0)
        days = delta_seconds / 86400.0
        return max(0.0, 1.0 - min(days / 30.0, 1.0))

    def _relevance_score(self, query_text: str, text: str) -> float:
        query_tokens = self._tokenize(query_text)
        if not query_tokens:
            return 0.0
        text_tokens = self._tokenize(text)
        if not text_tokens:
            return 0.0
        overlap = len(query_tokens & text_tokens)
        return float(overlap) * 2.0

    def _tokenize(self, text: str) -> set[str]:
        return {
            token
            for token in str(text).lower().replace("_", " ").split()
            if token
        }

    def _token_count(self, text: str) -> int:
        return max(1, len(str(text).split()))
