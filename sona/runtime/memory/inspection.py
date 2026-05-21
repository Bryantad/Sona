"""Inspection and governance APIs for the persistent memory subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .audit import AuditKernel
from .enums import GoalState, RetentionState
from .models import (
    AgentCheckpoint,
    Episode,
    Fact,
    Goal,
    MemoryClaim,
    MemoryLink,
    MemoryReceiptRef,
    Procedure,
)
from .policy import MemoryPolicy, PolicyKernel, default_runtime_policy
from .storage import MemoryStore


InspectableMemory = (
    Episode | MemoryClaim | Fact | Procedure | Goal | AgentCheckpoint
)


@dataclass(frozen=True, slots=True)
class MemoryInspection:
    object_type: str
    object_id: str
    data: dict[str, Any]
    trust_state: str | None
    retention_state: str | None
    receipt_refs: list[MemoryReceiptRef] = field(default_factory=list)
    links: list[MemoryLink] = field(default_factory=list)
    related_ids: dict[str, list[str]] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProvenanceTrace:
    root: MemoryInspection
    supporting_claims: list[MemoryInspection] = field(default_factory=list)
    supporting_facts: list[MemoryInspection] = field(default_factory=list)
    supporting_episodes: list[MemoryInspection] = field(default_factory=list)
    supporting_procedures: list[MemoryInspection] = field(default_factory=list)


class InspectionKernel:
    """Inspect stored memory objects and apply lifecycle transitions."""

    def __init__(
        self,
        store: MemoryStore,
        *,
        policy: MemoryPolicy | None = None,
        policy_kernel: PolicyKernel | None = None,
        audit_kernel: AuditKernel | None = None,
    ):
        self.store = store
        self.policy_kernel = policy_kernel or PolicyKernel(
            policy or default_runtime_policy()
        )
        self.audit_kernel = audit_kernel

    def inspect_object(
        self,
        object_type: str,
        object_id: str,
    ) -> MemoryInspection:
        memory = self._fetch_required_object(object_type, object_id)
        receipt_refs = self._receipt_refs_for(memory)
        links = self.store.query_links_for(object_id)
        return MemoryInspection(
            object_type=object_type,
            object_id=object_id,
            data=self._object_to_dict(memory),
            trust_state=self._enum_value(getattr(memory, "trust_state", None)),
            retention_state=self._enum_value(
                getattr(memory, "retention_state", None)
            ),
            receipt_refs=receipt_refs,
            links=links,
            related_ids=self._related_ids_for(memory),
        )

    def inspect_provenance(
        self,
        object_type: str,
        object_id: str,
    ) -> ProvenanceTrace:
        root_memory = self._fetch_required_object(object_type, object_id)
        root = self.inspect_object(object_type, object_id)

        claims: list[MemoryInspection] = []
        facts: list[MemoryInspection] = []
        episodes: list[MemoryInspection] = []
        procedures: list[MemoryInspection] = []

        if isinstance(root_memory, MemoryClaim):
            episodes = self._inspect_ids(
                "episode",
                root_memory.derived_from_episode_ids,
            )
        elif isinstance(root_memory, Fact):
            claims = self._inspect_ids(
                "claim",
                root_memory.supporting_claim_ids,
            )
            episodes = self._inspect_ids(
                "episode",
                root_memory.supporting_episode_ids,
            )
        elif isinstance(root_memory, Procedure):
            facts = self._inspect_ids("fact", root_memory.supporting_fact_ids)
            procedures = [root]
            claim_ids: list[str] = []
            episode_ids: list[str] = list(root_memory.success_evidence_ids)
            for fact in facts:
                claim_ids.extend(
                    fact.related_ids.get("supporting_claim_ids", [])
                )
                episode_ids.extend(
                    fact.related_ids.get("supporting_episode_ids", [])
                )
            claims = self._inspect_ids("claim", claim_ids)
            episodes = self._inspect_ids("episode", episode_ids)
        elif isinstance(root_memory, Goal):
            procedures = self._inspect_ids(
                "procedure",
                root_memory.linked_procedure_ids,
            )
            facts = self._inspect_ids("fact", root_memory.linked_fact_ids)
            episodes = self._inspect_ids(
                "episode",
                root_memory.linked_episode_ids,
            )
        return ProvenanceTrace(
            root=root,
            supporting_claims=self._dedupe_inspections(claims),
            supporting_facts=self._dedupe_inspections(facts),
            supporting_episodes=self._dedupe_inspections(episodes),
            supporting_procedures=self._dedupe_inspections(procedures),
        )

    def inspect_goal(self, goal_id: str) -> MemoryInspection:
        return self.inspect_object("goal", goal_id)

    def inspect_checkpoint(self, checkpoint_id: str) -> MemoryInspection:
        return self.inspect_object("checkpoint", checkpoint_id)

    def list_active_or_suspended_goals(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[MemoryInspection]:
        goals = self.store.query_goals(
            agent_id=agent_id,
            session_id=session_id,
            statuses=[GoalState.ACTIVE.value, GoalState.SUSPENDED.value],
            limit=limit,
        )
        return [self.inspect_object("goal", goal.id) for goal in goals]

    def get_latest_checkpoint(
        self,
        agent_id: str,
    ) -> MemoryInspection | None:
        checkpoint = self.store.get_latest_checkpoint(agent_id)
        if checkpoint is None:
            return None
        return self.inspect_object("checkpoint", checkpoint.id)

    def archive(self, owner_type: str, owner_id: str) -> MemoryInspection:
        return self._transition_retention(
            owner_type,
            owner_id,
            RetentionState.ARCHIVED,
        )

    def forget(self, owner_type: str, owner_id: str) -> MemoryInspection:
        return self._transition_retention(
            owner_type,
            owner_id,
            RetentionState.FORGOTTEN,
        )

    def delete(self, owner_type: str, owner_id: str) -> MemoryInspection:
        return self._transition_retention(
            owner_type,
            owner_id,
            RetentionState.DELETED,
        )

    def _transition_retention(
        self,
        owner_type: str,
        owner_id: str,
        target_state: RetentionState,
    ) -> MemoryInspection:
        if owner_type == "checkpoint":
            raise ValueError("Checkpoint retention is not managed here")
        memory = self._fetch_required_object(owner_type, owner_id)
        current_state = getattr(memory, "retention_state", RetentionState.ACTIVE)
        decision = self.policy_kernel.validate_retention_transition(
            owner_type,
            current_state,
            target_state,
        )
        if not decision.allowed:
            if self.audit_kernel is not None:
                self.audit_kernel.log_action(
                    subject_type=owner_type,
                    subject_id=owner_id,
                    action="retention_transition_denied",
                    actor_id="inspection_kernel",
                    policy_fingerprint=decision.policy_fingerprint,
                    details={
                        "current_state": current_state.value if hasattr(current_state, "value") else str(current_state),
                        "target_state": target_state.value,
                        "violation": decision.message,
                    },
                )
            raise ValueError(decision.message)
        self.store.update_retention(owner_type, owner_id, target_state.value)
        if self.audit_kernel is not None:
            self.audit_kernel.log_action(
                subject_type=owner_type,
                subject_id=owner_id,
                action="retention_transition",
                actor_id="inspection_kernel",
                policy_fingerprint=decision.policy_fingerprint,
                details={
                    "from_state": current_state.value if hasattr(current_state, "value") else str(current_state),
                    "to_state": target_state.value,
                },
            )
        return self.inspect_object(owner_type, owner_id)

    def _fetch_required_object(
        self,
        object_type: str,
        object_id: str,
    ) -> InspectableMemory:
        loaders = {
            "episode": self.store.get_episode,
            "claim": self.store.get_claim,
            "fact": self.store.get_fact,
            "procedure": self.store.get_procedure,
            "goal": self.store.get_goal,
            "checkpoint": self.store.get_checkpoint,
        }
        loader = loaders.get(object_type)
        if loader is None:
            raise ValueError(f"Unsupported object_type: {object_type}")
        memory = loader(object_id)
        if memory is None:
            raise ValueError(
                f"{object_type.title()} '{object_id}' could not be found"
            )
        return memory

    def _receipt_refs_for(
        self,
        memory: InspectableMemory,
    ) -> list[MemoryReceiptRef]:
        if isinstance(memory, AgentCheckpoint):
            return [memory.last_receipt_ref] if memory.last_receipt_ref else []
        return list(getattr(memory, "receipt_refs", []))

    def _related_ids_for(
        self,
        memory: InspectableMemory,
    ) -> dict[str, list[str]]:
        if isinstance(memory, MemoryClaim):
            return {
                "derived_from_episode_ids": list(
                    memory.derived_from_episode_ids
                ),
                "contradicts_claim_ids": list(memory.contradicts_claim_ids),
                "supports_claim_ids": list(memory.supports_claim_ids),
            }
        if isinstance(memory, Fact):
            related = {
                "supporting_claim_ids": list(memory.supporting_claim_ids),
                "supporting_episode_ids": list(
                    memory.supporting_episode_ids
                ),
            }
            if memory.supersedes_fact_id:
                related["supersedes_fact_id"] = [memory.supersedes_fact_id]
            return related
        if isinstance(memory, Procedure):
            return {
                "supporting_fact_ids": list(memory.supporting_fact_ids),
                "success_evidence_ids": list(memory.success_evidence_ids),
            }
        if isinstance(memory, Goal):
            return {
                "linked_episode_ids": list(memory.linked_episode_ids),
                "linked_fact_ids": list(memory.linked_fact_ids),
                "linked_procedure_ids": list(memory.linked_procedure_ids),
            }
        if isinstance(memory, AgentCheckpoint):
            related: dict[str, list[str]] = {
                "active_goal_stack": list(memory.active_goal_stack),
            }
            if memory.last_processed_episode_id:
                related["last_processed_episode_id"] = [
                    memory.last_processed_episode_id
                ]
            return related
        return {}

    def _inspect_ids(
        self,
        object_type: str,
        ids: list[str],
    ) -> list[MemoryInspection]:
        inspections: list[MemoryInspection] = []
        seen: set[str] = set()
        for object_id in ids:
            if object_id in seen:
                continue
            seen.add(object_id)
            try:
                inspections.append(self.inspect_object(object_type, object_id))
            except ValueError:
                continue
        return inspections

    def _dedupe_inspections(
        self,
        inspections: list[MemoryInspection],
    ) -> list[MemoryInspection]:
        deduped: list[MemoryInspection] = []
        seen: set[tuple[str, str]] = set()
        for inspection in inspections:
            key = (inspection.object_type, inspection.object_id)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(inspection)
        return deduped

    def _object_to_dict(self, memory: InspectableMemory) -> dict[str, Any]:
        if hasattr(memory, "to_dict"):
            return memory.to_dict()
        return {"id": getattr(memory, "id")}

    def _enum_value(self, value: Any) -> str | None:
        if value is None:
            return None
        return value.value if hasattr(value, "value") else str(value)
