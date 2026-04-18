"""Canonical data models for the persistent memory subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import (
    CheckpointState,
    ClassificationTier,
    GoalState,
    ProcedureReviewState,
    RetentionState,
    TrustState,
)
from .ids import make_prefixed_id, utc_now


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


@dataclass(slots=True)
class MemoryReceiptRef:
    receipt_id: str
    event_kind_or_path: str
    receipt_hash: str | None = None
    classification: ClassificationTier = ClassificationTier.INTERNAL
    policy_fingerprint: str | None = None
    event_offset: int | None = None
    sealed_mode_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "event_kind_or_path": self.event_kind_or_path,
            "receipt_hash": self.receipt_hash,
            "classification": _enum_value(self.classification),
            "policy_fingerprint": self.policy_fingerprint,
            "event_offset": self.event_offset,
            "sealed_mode_ref": self.sealed_mode_ref,
        }


@dataclass(slots=True)
class Episode:
    agent_id: str
    session_id: str
    kind: str
    source_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: make_prefixed_id("ep"))
    timestamp: str = field(default_factory=utc_now)
    tenant_id: str | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    goal_id: str | None = None
    trace_id: str | None = None
    correlation_id: str | None = None
    classification: ClassificationTier = ClassificationTier.INTERNAL
    trust_state: TrustState = TrustState.OBSERVED
    retention_state: RetentionState = RetentionState.ACTIVE
    privacy_scope: str | None = None
    importance: float | None = None
    confidence: float | None = None
    receipt_refs: list[MemoryReceiptRef] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "tenant_id": self.tenant_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "goal_id": self.goal_id,
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "kind": self.kind,
            "source_type": self.source_type,
            "payload": self.payload,
            "classification": _enum_value(self.classification),
            "trust_state": _enum_value(self.trust_state),
            "retention_state": _enum_value(self.retention_state),
            "privacy_scope": self.privacy_scope,
            "importance": self.importance,
            "confidence": self.confidence,
            "receipt_refs": [ref.to_dict() for ref in self.receipt_refs],
        }


@dataclass(slots=True)
class MemoryClaim:
    statement: str
    claim_type: str
    derived_from_episode_ids: list[str]
    id: str = field(default_factory=lambda: make_prefixed_id("claim"))
    created_at: str = field(default_factory=utc_now)
    updated_at: str | None = None
    agent_id: str | None = None
    tenant_id: str | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    session_id: str | None = None
    goal_id: str | None = None
    privacy_scope: str | None = None
    confidence: float | None = None
    trust_state: TrustState = TrustState.DERIVED
    retention_state: RetentionState = RetentionState.ACTIVE
    contradicts_claim_ids: list[str] = field(default_factory=list)
    supports_claim_ids: list[str] = field(default_factory=list)
    receipt_refs: list[MemoryReceiptRef] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "statement": self.statement,
            "claim_type": self.claim_type,
            "derived_from_episode_ids": list(self.derived_from_episode_ids),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "agent_id": self.agent_id,
            "tenant_id": self.tenant_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "goal_id": self.goal_id,
            "privacy_scope": self.privacy_scope,
            "confidence": self.confidence,
            "trust_state": _enum_value(self.trust_state),
            "retention_state": _enum_value(self.retention_state),
            "contradicts_claim_ids": list(self.contradicts_claim_ids),
            "supports_claim_ids": list(self.supports_claim_ids),
            "receipt_refs": [ref.to_dict() for ref in self.receipt_refs],
        }


@dataclass(slots=True)
class Fact:
    canonical_statement: str
    supporting_claim_ids: list[str]
    supporting_episode_ids: list[str]
    id: str = field(default_factory=lambda: make_prefixed_id("fact"))
    created_at: str = field(default_factory=utc_now)
    updated_at: str | None = None
    agent_id: str | None = None
    tenant_id: str | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    session_id: str | None = None
    goal_id: str | None = None
    privacy_scope: str | None = None
    trust_state: TrustState = TrustState.CONFIRMED
    retention_state: RetentionState = RetentionState.ACTIVE
    validity_window: dict[str, Any] | None = None
    supersedes_fact_id: str | None = None
    provenance_summary: str | None = None
    receipt_refs: list[MemoryReceiptRef] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "canonical_statement": self.canonical_statement,
            "supporting_claim_ids": list(self.supporting_claim_ids),
            "supporting_episode_ids": list(self.supporting_episode_ids),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "agent_id": self.agent_id,
            "tenant_id": self.tenant_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "goal_id": self.goal_id,
            "privacy_scope": self.privacy_scope,
            "trust_state": _enum_value(self.trust_state),
            "retention_state": _enum_value(self.retention_state),
            "validity_window": self.validity_window,
            "supersedes_fact_id": self.supersedes_fact_id,
            "provenance_summary": self.provenance_summary,
            "receipt_refs": [ref.to_dict() for ref in self.receipt_refs],
        }


@dataclass(slots=True)
class Procedure:
    title: str
    procedure_type: str
    steps_or_pattern: list[str] | dict[str, Any] | str
    supporting_fact_ids: list[str]
    id: str = field(default_factory=lambda: make_prefixed_id("proc"))
    created_at: str = field(default_factory=utc_now)
    updated_at: str | None = None
    agent_id: str | None = None
    tenant_id: str | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    session_id: str | None = None
    goal_id: str | None = None
    privacy_scope: str | None = None
    trust_state: TrustState = TrustState.DERIVED
    retention_state: RetentionState = RetentionState.ACTIVE
    success_evidence_ids: list[str] = field(default_factory=list)
    version: int = 1
    review_state: ProcedureReviewState = ProcedureReviewState.PENDING
    receipt_refs: list[MemoryReceiptRef] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "procedure_type": self.procedure_type,
            "steps_or_pattern": self.steps_or_pattern,
            "supporting_fact_ids": list(self.supporting_fact_ids),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "agent_id": self.agent_id,
            "tenant_id": self.tenant_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "goal_id": self.goal_id,
            "privacy_scope": self.privacy_scope,
            "trust_state": _enum_value(self.trust_state),
            "retention_state": _enum_value(self.retention_state),
            "success_evidence_ids": list(self.success_evidence_ids),
            "version": self.version,
            "review_state": _enum_value(self.review_state),
            "receipt_refs": [ref.to_dict() for ref in self.receipt_refs],
        }


@dataclass(slots=True)
class Goal:
    title: str
    status: GoalState = GoalState.OPEN
    id: str = field(default_factory=lambda: make_prefixed_id("goal"))
    opened_at: str = field(default_factory=utc_now)
    priority: int | None = None
    resumed_at: str | None = None
    suspended_at: str | None = None
    completed_at: str | None = None
    agent_id: str | None = None
    tenant_id: str | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    session_id: str | None = None
    goal_id: str | None = None
    privacy_scope: str | None = None
    trust_state: TrustState = TrustState.OBSERVED
    retention_state: RetentionState = RetentionState.ACTIVE
    linked_episode_ids: list[str] = field(default_factory=list)
    linked_fact_ids: list[str] = field(default_factory=list)
    linked_procedure_ids: list[str] = field(default_factory=list)
    receipt_refs: list[MemoryReceiptRef] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": _enum_value(self.status),
            "opened_at": self.opened_at,
            "priority": self.priority,
            "resumed_at": self.resumed_at,
            "suspended_at": self.suspended_at,
            "completed_at": self.completed_at,
            "agent_id": self.agent_id,
            "tenant_id": self.tenant_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "goal_id": self.goal_id,
            "privacy_scope": self.privacy_scope,
            "trust_state": _enum_value(self.trust_state),
            "retention_state": _enum_value(self.retention_state),
            "linked_episode_ids": list(self.linked_episode_ids),
            "linked_fact_ids": list(self.linked_fact_ids),
            "linked_procedure_ids": list(self.linked_procedure_ids),
            "receipt_refs": [ref.to_dict() for ref in self.receipt_refs],
        }


@dataclass(slots=True)
class AgentCheckpoint:
    agent_id: str
    working_state_blob: dict[str, Any]
    last_processed_episode_id: str | None = None
    id: str = field(default_factory=lambda: make_prefixed_id("checkpoint"))
    created_at: str = field(default_factory=utc_now)
    session_id: str | None = None
    trace_id: str | None = None
    state: CheckpointState = CheckpointState.CURRENT
    active_goal_stack: list[str] = field(default_factory=list)
    focus_stack: list[dict[str, Any]] = field(default_factory=list)
    last_receipt_ref: MemoryReceiptRef | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "working_state_blob": self.working_state_blob,
            "last_processed_episode_id": self.last_processed_episode_id,
            "created_at": self.created_at,
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "state": _enum_value(self.state),
            "active_goal_stack": list(self.active_goal_stack),
            "focus_stack": list(self.focus_stack),
            "last_receipt_ref": (
                self.last_receipt_ref.to_dict()
                if self.last_receipt_ref
                else None
            ),
        }


@dataclass(slots=True)
class MemoryLink:
    from_id: str
    to_id: str
    relation_type: str
    id: str = field(default_factory=lambda: make_prefixed_id("link"))
    created_at: str = field(default_factory=utc_now)
    weight: float | None = None
    source_episode_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "from_id": self.from_id,
            "to_id": self.to_id,
            "relation_type": self.relation_type,
            "created_at": self.created_at,
            "weight": self.weight,
            "source_episode_ids": list(self.source_episode_ids),
        }


@dataclass(slots=True)
class AgentStateProfile:
    agent_id: str
    id: str = field(default_factory=lambda: make_prefixed_id("agent"))
    tenant_id: str | None = None
    display_name: str | None = None
    default_privacy_scope: str | None = None
    capabilities: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "tenant_id": self.tenant_id,
            "display_name": self.display_name,
            "default_privacy_scope": self.default_privacy_scope,
            "capabilities": list(self.capabilities),
            "metadata": dict(self.metadata),
        }
