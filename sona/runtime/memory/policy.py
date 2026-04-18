"""Deterministic runtime governance policy for persistent memory operations."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from sona.policy import POLICY_VERSION as ENGINE_POLICY_VERSION
from sona.policy import policy_fingerprint as engine_policy_fingerprint

from .enums import ClassificationTier, CheckpointState, RetentionState
from .models import AgentCheckpoint, Episode, MemoryReceiptRef


def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _classification_rank(value: ClassificationTier | str | None) -> int:
    normalized = _normalize_classification(value)
    ordering = {
        ClassificationTier.PUBLIC: 1,
        ClassificationTier.INTERNAL: 2,
        ClassificationTier.SENSITIVE: 3,
    }
    return ordering[normalized]


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


def _normalize_retention_state(value: RetentionState | str) -> RetentionState:
    if isinstance(value, RetentionState):
        return value
    return RetentionState(str(value).strip().lower())


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    active_ttl_days: int | None = None
    archived_ttl_days: int | None = None
    auto_archive_after_days: int | None = None
    allow_archive: bool = True
    allow_forget: bool = True
    allow_delete: bool = True
    require_archive_before_delete: bool = True


@dataclass(frozen=True, slots=True)
class ClassificationPolicy:
    max_classification: ClassificationTier = ClassificationTier.SENSITIVE
    allowed_privacy_scopes: tuple[str, ...] = ()
    mutable_privacy_scopes: tuple[str, ...] = ()
    allow_missing_privacy_scope: bool = True


@dataclass(frozen=True, slots=True)
class ScopePolicy:
    enforce_tenant_isolation: bool = False
    enforce_workspace_isolation: bool = True
    enforce_project_isolation: bool = False
    require_workspace_for_project: bool = True


@dataclass(frozen=True, slots=True)
class PromotionPolicy:
    min_claim_confidence: float = 0.5
    min_claims_for_fact: int = 2
    min_success_events_for_procedure: int = 2


@dataclass(frozen=True, slots=True)
class CheckpointPolicy:
    allow_restore_current: bool = True
    allow_restore_superseded: bool = False
    allow_restore_invalidated: bool = False
    require_matching_agent: bool = True
    require_receipt_policy_fingerprint: bool = False
    enforce_receipt_policy_match: bool = False
    allow_missing_receipt_policy_fingerprint: bool = True


@dataclass(frozen=True, slots=True)
class MemoryPolicy:
    retention_policy: dict[str, RetentionPolicy]
    classification_policy: ClassificationPolicy = field(default_factory=ClassificationPolicy)
    scope_policy: ScopePolicy = field(default_factory=ScopePolicy)
    promotion_policy: PromotionPolicy = field(default_factory=PromotionPolicy)
    checkpoint_policy: CheckpointPolicy = field(default_factory=CheckpointPolicy)
    policy_version: str = "runtime-memory-policy-v1"
    require_receipt_policy_context: bool = False


@dataclass(frozen=True, slots=True)
class PolicyViolation:
    rule_code: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    policy_fingerprint: str
    violation: PolicyViolation | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def message(self) -> str:
        if self.violation is None:
            return "allowed"
        return self.violation.message


@dataclass(frozen=True, slots=True)
class PolicySnapshot:
    payload: dict[str, Any]
    fingerprint: str


def default_runtime_policy() -> MemoryPolicy:
    default_retention = RetentionPolicy()
    retention_policy = {
        object_type: default_retention
        for object_type in ("episode", "claim", "fact", "procedure", "goal")
    }
    return MemoryPolicy(retention_policy=retention_policy)


class PolicyKernel:
    """Apply deterministic runtime-governance checks to memory operations."""

    def __init__(self, policy: MemoryPolicy | None = None):
        self.policy = policy or default_runtime_policy()

    def export_snapshot(self) -> PolicySnapshot:
        payload = {
            "policy_version": self.policy.policy_version,
            "engine_policy_version": ENGINE_POLICY_VERSION,
            "engine_policy_fingerprint": engine_policy_fingerprint(),
            "require_receipt_policy_context": self.policy.require_receipt_policy_context,
            "retention_policy": {
                object_type: {
                    "active_ttl_days": config.active_ttl_days,
                    "archived_ttl_days": config.archived_ttl_days,
                    "auto_archive_after_days": config.auto_archive_after_days,
                    "allow_archive": config.allow_archive,
                    "allow_forget": config.allow_forget,
                    "allow_delete": config.allow_delete,
                    "require_archive_before_delete": config.require_archive_before_delete,
                }
                for object_type, config in sorted(self.policy.retention_policy.items())
            },
            "classification_policy": {
                "max_classification": self.policy.classification_policy.max_classification.value,
                "allowed_privacy_scopes": list(self.policy.classification_policy.allowed_privacy_scopes),
                "mutable_privacy_scopes": list(self.policy.classification_policy.mutable_privacy_scopes),
                "allow_missing_privacy_scope": self.policy.classification_policy.allow_missing_privacy_scope,
            },
            "scope_policy": {
                "enforce_tenant_isolation": self.policy.scope_policy.enforce_tenant_isolation,
                "enforce_workspace_isolation": self.policy.scope_policy.enforce_workspace_isolation,
                "enforce_project_isolation": self.policy.scope_policy.enforce_project_isolation,
                "require_workspace_for_project": self.policy.scope_policy.require_workspace_for_project,
            },
            "promotion_policy": {
                "min_claim_confidence": self.policy.promotion_policy.min_claim_confidence,
                "min_claims_for_fact": self.policy.promotion_policy.min_claims_for_fact,
                "min_success_events_for_procedure": self.policy.promotion_policy.min_success_events_for_procedure,
            },
            "checkpoint_policy": {
                "allow_restore_current": self.policy.checkpoint_policy.allow_restore_current,
                "allow_restore_superseded": self.policy.checkpoint_policy.allow_restore_superseded,
                "allow_restore_invalidated": self.policy.checkpoint_policy.allow_restore_invalidated,
                "require_matching_agent": self.policy.checkpoint_policy.require_matching_agent,
                "require_receipt_policy_fingerprint": self.policy.checkpoint_policy.require_receipt_policy_fingerprint,
                "enforce_receipt_policy_match": self.policy.checkpoint_policy.enforce_receipt_policy_match,
                "allow_missing_receipt_policy_fingerprint": self.policy.checkpoint_policy.allow_missing_receipt_policy_fingerprint,
            },
        }
        return PolicySnapshot(
            payload=payload,
            fingerprint=_hash_text(_canonical_json(payload)),
        )

    def resolve_policy_fingerprint(self) -> str:
        return self.export_snapshot().fingerprint

    def validate_episode_append(self, episode: Episode) -> PolicyDecision:
        violation = self._validate_scope(
            tenant_id=episode.tenant_id,
            workspace_id=episode.workspace_id,
            project_id=episode.project_id,
        )
        if violation is not None:
            return self._deny(violation)

        classification_policy = self.policy.classification_policy
        if _classification_rank(episode.classification) > _classification_rank(
            classification_policy.max_classification
        ):
            return self._deny(
                PolicyViolation(
                    "classification.max_exceeded",
                    "Episode classification exceeds the active runtime policy",
                    {
                        "classification": _enum_value(episode.classification),
                        "max_classification": classification_policy.max_classification.value,
                    },
                )
            )

        privacy_scope = str(episode.privacy_scope or "").strip()
        if (
            classification_policy.allowed_privacy_scopes
            and privacy_scope
            and privacy_scope not in classification_policy.allowed_privacy_scopes
        ):
            return self._deny(
                PolicyViolation(
                    "scope.privacy_scope_not_allowed",
                    "Episode privacy scope is not permitted by the active runtime policy",
                    {
                        "privacy_scope": privacy_scope,
                        "allowed_privacy_scopes": list(classification_policy.allowed_privacy_scopes),
                    },
                )
            )

        if (
            not classification_policy.allow_missing_privacy_scope
            and episode.classification == ClassificationTier.SENSITIVE
            and not privacy_scope
        ):
            return self._deny(
                PolicyViolation(
                    "classification.missing_privacy_scope",
                    "Sensitive episodes require a privacy scope under the active runtime policy",
                    {},
                )
            )

        return self._receipt_policy_decision(episode.receipt_refs)

    def validate_retention_transition(
        self,
        owner_type: str,
        current_state: RetentionState | str,
        target_state: RetentionState | str,
    ) -> PolicyDecision:
        current = _normalize_retention_state(current_state)
        target = _normalize_retention_state(target_state)
        config = self.policy.retention_policy.get(owner_type, RetentionPolicy())

        if current == target:
            return self._allow()
        if current == RetentionState.DELETED:
            return self._deny(
                PolicyViolation(
                    "retention.deleted_immutable",
                    "Deleted records cannot transition to another retention state",
                    {"owner_type": owner_type, "current_state": current.value, "target_state": target.value},
                )
            )
        if target == RetentionState.ARCHIVED and not config.allow_archive:
            return self._deny(
                PolicyViolation(
                    "retention.archive_denied",
                    "Archiving is disabled by the active runtime policy",
                    {"owner_type": owner_type},
                )
            )
        if target == RetentionState.FORGOTTEN and not config.allow_forget:
            return self._deny(
                PolicyViolation(
                    "retention.forget_denied",
                    "Forgetting is disabled by the active runtime policy",
                    {"owner_type": owner_type},
                )
            )
        if target == RetentionState.DELETED:
            if not config.allow_delete:
                return self._deny(
                    PolicyViolation(
                        "retention.delete_denied",
                        "Deletion is disabled by the active runtime policy",
                        {"owner_type": owner_type},
                    )
                )
            if (
                config.require_archive_before_delete
                and current not in (RetentionState.ARCHIVED, RetentionState.FORGOTTEN)
            ):
                return self._deny(
                    PolicyViolation(
                        "retention.archive_required_before_delete",
                        "Records must be archived or forgotten before deletion under the active runtime policy",
                        {
                            "owner_type": owner_type,
                            "current_state": current.value,
                            "target_state": target.value,
                        },
                    )
                )

        return self._allow()

    def validate_checkpoint_restore(
        self,
        checkpoint: AgentCheckpoint,
        *,
        agent_id: str | None = None,
    ) -> PolicyDecision:
        checkpoint_policy = self.policy.checkpoint_policy
        state = checkpoint.state
        if state == CheckpointState.CURRENT and not checkpoint_policy.allow_restore_current:
            return self._deny(
                PolicyViolation(
                    "checkpoint.current_restore_denied",
                    "Current checkpoints are not restorable under the active runtime policy",
                    {"checkpoint_id": checkpoint.id},
                )
            )
        if state == CheckpointState.SUPERSEDED and not checkpoint_policy.allow_restore_superseded:
            return self._deny(
                PolicyViolation(
                    "checkpoint.superseded_restore_denied",
                    "Superseded checkpoints are not restorable under the active runtime policy",
                    {"checkpoint_id": checkpoint.id},
                )
            )
        if state == CheckpointState.INVALIDATED and not checkpoint_policy.allow_restore_invalidated:
            return self._deny(
                PolicyViolation(
                    "checkpoint.invalidated_restore_denied",
                    "Invalidated checkpoints cannot be restored under the active runtime policy",
                    {"checkpoint_id": checkpoint.id},
                )
            )
        if (
            checkpoint_policy.require_matching_agent
            and agent_id is not None
            and checkpoint.agent_id != agent_id
        ):
            return self._deny(
                PolicyViolation(
                    "checkpoint.agent_mismatch",
                    "Checkpoint agent does not match the active interpreter agent",
                    {
                        "checkpoint_id": checkpoint.id,
                        "checkpoint_agent": checkpoint.agent_id,
                        "active_agent": agent_id,
                    },
                )
            )

        refs = [checkpoint.last_receipt_ref] if checkpoint.last_receipt_ref else []
        return self._receipt_policy_decision(
            refs,
            require_fingerprint=checkpoint_policy.require_receipt_policy_fingerprint,
            enforce_match=checkpoint_policy.enforce_receipt_policy_match,
            allow_missing=checkpoint_policy.allow_missing_receipt_policy_fingerprint,
        )

    def validate_access(
        self,
        *,
        classification: ClassificationTier | str | None,
        actor_max_classification: ClassificationTier | str | None = None,
        owner_workspace_id: str | None = None,
        actor_workspace_id: str | None = None,
        privacy_scope: str | None = None,
    ) -> PolicyDecision:
        actor_limit = actor_max_classification or self.policy.classification_policy.max_classification
        if _classification_rank(classification) > _classification_rank(actor_limit):
            return self._deny(
                PolicyViolation(
                    "access.classification_denied",
                    "Requested memory classification exceeds the actor's permitted classification",
                    {
                        "classification": _enum_value(_normalize_classification(classification)),
                        "actor_max_classification": _enum_value(_normalize_classification(actor_limit)),
                    },
                )
            )

        if (
            self.policy.scope_policy.enforce_workspace_isolation
            and owner_workspace_id
            and actor_workspace_id
            and owner_workspace_id != actor_workspace_id
        ):
            return self._deny(
                PolicyViolation(
                    "access.workspace_mismatch",
                    "Requested memory belongs to a different workspace under the active runtime policy",
                    {
                        "owner_workspace_id": owner_workspace_id,
                        "actor_workspace_id": actor_workspace_id,
                        "privacy_scope": privacy_scope,
                    },
                )
            )

        return self._allow()

    def _validate_scope(
        self,
        *,
        tenant_id: str | None,
        workspace_id: str | None,
        project_id: str | None,
    ) -> PolicyViolation | None:
        scope_policy = self.policy.scope_policy
        if scope_policy.enforce_tenant_isolation and tenant_id is not None:
            tenant = str(tenant_id).strip()
            if not tenant:
                return PolicyViolation(
                    "scope.tenant_required",
                    "Tenant isolation is enabled and tenant_id is required",
                    {},
                )
        if scope_policy.require_workspace_for_project and project_id and not workspace_id:
            return PolicyViolation(
                "scope.workspace_required_for_project",
                "Project-scoped records require a workspace id under the active runtime policy",
                {"project_id": project_id},
            )
        return None

    def _receipt_policy_decision(
        self,
        receipt_refs: list[MemoryReceiptRef],
        *,
        require_fingerprint: bool | None = None,
        enforce_match: bool | None = None,
        allow_missing: bool | None = None,
    ) -> PolicyDecision:
        require_fingerprint = (
            self.policy.require_receipt_policy_context
            if require_fingerprint is None
            else require_fingerprint
        )
        checkpoint_policy = self.policy.checkpoint_policy
        enforce_match = (
            checkpoint_policy.enforce_receipt_policy_match
            if enforce_match is None
            else enforce_match
        )
        allow_missing = (
            checkpoint_policy.allow_missing_receipt_policy_fingerprint
            if allow_missing is None
            else allow_missing
        )
        runtime_fingerprint = self.resolve_policy_fingerprint()
        warnings: list[str] = []

        if not receipt_refs:
            if require_fingerprint:
                return self._deny(
                    PolicyViolation(
                        "receipt.policy_context_required",
                        "Receipt policy context is required by the active runtime policy",
                        {},
                    )
                )
            return self._allow(warnings=warnings)

        for ref in receipt_refs:
            fingerprint = str(ref.policy_fingerprint or "").strip()
            if not fingerprint:
                if require_fingerprint and not allow_missing:
                    return self._deny(
                        PolicyViolation(
                            "receipt.policy_fingerprint_missing",
                            "Receipt policy fingerprint is required by the active runtime policy",
                            {"receipt_id": ref.receipt_id},
                        )
                    )
                warnings.append(
                    f"Receipt ref {ref.receipt_id} has no policy fingerprint"
                )
                continue
            if fingerprint != runtime_fingerprint:
                message = (
                    f"Receipt ref {ref.receipt_id} policy fingerprint does not match the active runtime policy"
                )
                if enforce_match:
                    return self._deny(
                        PolicyViolation(
                            "receipt.policy_fingerprint_mismatch",
                            message,
                            {
                                "receipt_id": ref.receipt_id,
                                "receipt_policy_fingerprint": fingerprint,
                                "runtime_policy_fingerprint": runtime_fingerprint,
                            },
                        )
                    )
                warnings.append(message)

        return self._allow(warnings=warnings)

    def _allow(self, *, warnings: list[str] | None = None) -> PolicyDecision:
        return PolicyDecision(
            allowed=True,
            policy_fingerprint=self.resolve_policy_fingerprint(),
            warnings=warnings or [],
        )

    def _deny(self, violation: PolicyViolation) -> PolicyDecision:
        return PolicyDecision(
            allowed=False,
            policy_fingerprint=self.resolve_policy_fingerprint(),
            violation=violation,
        )


__all__ = [
    "CheckpointPolicy",
    "ClassificationPolicy",
    "MemoryPolicy",
    "PolicyDecision",
    "PolicyKernel",
    "PolicySnapshot",
    "PolicyViolation",
    "PromotionPolicy",
    "RetentionPolicy",
    "ScopePolicy",
    "default_runtime_policy",
]