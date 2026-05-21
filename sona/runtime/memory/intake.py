"""Thin runtime intake adapter for persistent memory episodes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from sona.receipts import (
    append_receipt_event,
    build_memory_receipt_ref_from_active_context,
)

from .audit import AuditKernel
from .enums import ClassificationTier
from .models import Episode
from .payloads import normalize_episode_payload
from .policy import MemoryPolicy, PolicyKernel, default_runtime_policy
from .sqlite_store import SQLiteMemoryStore
from .storage import MemoryStore


def _normalize_classification(
    value: ClassificationTier | str | None,
) -> ClassificationTier:
    if isinstance(value, ClassificationTier):
        return value
    if value is None:
        return ClassificationTier.INTERNAL
    try:
        return ClassificationTier(str(value).strip().lower())
    except ValueError:
        return ClassificationTier.INTERNAL


@dataclass(slots=True)
class RuntimeExecutionIdentity:
    agent_id: str
    session_id: str
    tenant_id: str | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    goal_id: str | None = None
    trace_id: str | None = None
    correlation_id: str | None = None
    privacy_scope: str | None = None


class RuntimeMemoryIntake:
    """Persist runtime events as immutable memory episodes."""

    def __init__(
        self,
        store: MemoryStore | SQLiteMemoryStore,
        *,
        importance_threshold: float = 0.2,
        policy: MemoryPolicy | None = None,
        policy_kernel: PolicyKernel | None = None,
        audit_kernel: AuditKernel | None = None,
    ):
        self.store = store
        self.importance_threshold = float(importance_threshold)
        self.policy_kernel = policy_kernel or PolicyKernel(
            policy or default_runtime_policy()
        )
        self.audit_kernel = audit_kernel

    def append_episode(
        self,
        *,
        kind: str,
        source_type: str,
        payload: Mapping[str, Any] | None,
        execution_identity: RuntimeExecutionIdentity,
        importance: float | None = None,
        classification: ClassificationTier | str | None = None,
        confidence: float | None = None,
        attach_receipt_provenance: bool = True,
    ) -> Episode | None:
        normalized_importance = self._normalize_importance(importance)
        if not self._should_persist(normalized_importance):
            return None

        normalized_classification = _normalize_classification(classification)
        receipt_refs = []
        if attach_receipt_provenance:
            receipt_event = append_receipt_event(
                "memory_episode",
                payload={
                    "kind": str(kind),
                    "source_type": str(source_type),
                },
                classification=normalized_classification.value,
            )
            receipt_ref = build_memory_receipt_ref_from_active_context(
                event=receipt_event,
            )
            if receipt_ref is not None:
                receipt_refs.append(receipt_ref)

        episode = Episode(
            agent_id=execution_identity.agent_id,
            tenant_id=execution_identity.tenant_id,
            workspace_id=execution_identity.workspace_id,
            project_id=execution_identity.project_id,
            session_id=execution_identity.session_id,
            goal_id=execution_identity.goal_id,
            trace_id=execution_identity.trace_id,
            correlation_id=execution_identity.correlation_id,
            kind=str(kind),
            source_type=str(source_type),
            payload=normalize_episode_payload(kind, payload),
            classification=normalized_classification,
            privacy_scope=execution_identity.privacy_scope,
            importance=normalized_importance,
            confidence=confidence,
            receipt_refs=receipt_refs,
        )
        decision = self.policy_kernel.validate_episode_append(episode)
        if not decision.allowed:
            if self.audit_kernel is not None:
                self.audit_kernel.log_action(
                    subject_type="episode",
                    subject_id=episode.id,
                    action="episode_append_denied",
                    actor_id=execution_identity.agent_id,
                    policy_fingerprint=decision.policy_fingerprint,
                    details={"violation": decision.message},
                )
            raise ValueError(decision.message)
        saved = self.store.append_episode(episode)
        if self.audit_kernel is not None:
            self.audit_kernel.log_action(
                subject_type="episode",
                subject_id=saved.id,
                action="episode_appended",
                actor_id=execution_identity.agent_id,
                policy_fingerprint=decision.policy_fingerprint,
                details={"kind": saved.kind, "source_type": saved.source_type},
            )
        return saved

    def _normalize_importance(self, value: float | None) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _should_persist(self, importance: float | None) -> bool:
        if importance is None:
            return True
        return importance >= self.importance_threshold
