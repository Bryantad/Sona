"""Checkpoint restoration and narrow goal-continuation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .audit import AuditKernel
from .enums import CheckpointState, GoalState
from .ids import utc_now
from .models import AgentCheckpoint, Goal
from .policy import MemoryPolicy, PolicyKernel, default_runtime_policy
from .retrieval import RetrievedMemory, RetrievalKernel
from .storage import MemoryStore


_RESUMABLE_GOAL_STATES = {
    GoalState.OPEN,
    GoalState.ACTIVE,
    GoalState.SUSPENDED,
}


@dataclass(frozen=True, slots=True)
class CheckpointRestoration:
    success: bool
    checkpoint_id: str | None
    restored_working_memory: dict[str, Any] = field(default_factory=dict)
    restored_intent_stack: list[dict[str, Any]] = field(default_factory=list)
    restored_decision_log: list[dict[str, Any]] = field(default_factory=list)
    restored_scope_stack: list[dict[str, Any]] = field(default_factory=list)
    restored_goal_stack: list[Goal] = field(default_factory=list)
    restored_focus_stack: list[dict[str, Any]] = field(default_factory=list)
    restored_current_context: str | None = None
    restored_focus_active: bool = False
    last_processed_episode_id: str | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class GoalContinuationStep:
    success: bool
    goal_id: str | None
    goal_status: GoalState | None = None
    next_action: str | None = None
    suggestion: GoalInferenceSuggestion | None = None
    retrieved_memories: list[RetrievedMemory] = field(default_factory=list)
    evidence_episode_id: str | None = None
    checkpoint_id: str | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class GoalStateTransition:
    success: bool
    goal_id: str | None
    previous_status: GoalState | None = None
    current_status: GoalState | None = None
    evidence_episode_id: str | None = None
    checkpoint_id: str | None = None
    stack_changed: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class GoalInferenceSuggestion:
    goal_id: str
    inference_mode: str
    action_type: str
    next_action: str
    reason_code: str
    supporting_object_ids: list[str] = field(default_factory=list)
    candidate_actions: list[str] = field(default_factory=list)
    candidate_features: dict[str, Any] = field(default_factory=dict)
    gating_results: dict[str, Any] = field(default_factory=dict)
    ranking_policy_version: str = "deterministic-goal-inference-v1"
    memory_input_ids: list[str] = field(default_factory=list)
    sampling_metadata: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    requires_review: bool = False

    def explanation_envelope(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "inference_mode": self.inference_mode,
            "selected_action": self.next_action,
            "reason_code": self.reason_code,
            "supporting_object_ids": list(self.supporting_object_ids),
            "candidate_actions": list(self.candidate_actions),
            "candidate_features": dict(self.candidate_features),
            "gating_results": dict(self.gating_results),
            "ranking_policy_version": self.ranking_policy_version,
            "memory_input_ids": list(self.memory_input_ids),
            "sampling_metadata": dict(self.sampling_metadata),
        }

    def has_complete_explanation(self) -> bool:
        envelope = self.explanation_envelope()
        required_keys = {
            "goal_id",
            "inference_mode",
            "selected_action",
            "reason_code",
            "supporting_object_ids",
            "candidate_actions",
            "candidate_features",
            "gating_results",
            "ranking_policy_version",
            "memory_input_ids",
            "sampling_metadata",
        }
        if set(envelope.keys()) != required_keys:
            return False
        if not envelope["goal_id"]:
            return False
        if not envelope["inference_mode"]:
            return False
        if not envelope["selected_action"]:
            return False
        if not envelope["reason_code"]:
            return False
        if not isinstance(envelope["candidate_actions"], list):
            return False
        if not isinstance(envelope["candidate_features"], dict):
            return False
        if not isinstance(envelope["gating_results"], dict):
            return False
        if not isinstance(envelope["memory_input_ids"], list):
            return False
        if not isinstance(envelope["sampling_metadata"], dict):
            return False
        return True


class GoalInferenceKernel:
    """Structured, deterministic inference over goal-scoped retrieved memory."""

    RANKING_POLICY_VERSION = "deterministic-goal-inference-v1"

    def suggest_next_step(
        self,
        goal: Goal,
        retrieved: list[RetrievedMemory],
    ) -> GoalInferenceSuggestion:
        candidate_features = self._candidate_features(retrieved)
        candidate_actions = self._candidate_actions(candidate_features)
        memory_input_ids = [item.memory_id for item in retrieved]

        failure_episode = self._best_episode_by_kind(
            retrieved,
            kind="interpret_failure",
        )
        if failure_episode is not None:
            return self._suggestion(
                goal=goal,
                action_type="resolve_failure",
                next_action=(
                    f"Resolve runtime failure '{failure_episode.memory_id}' "
                    f"for goal '{goal.title}'"
                ),
                reason_code="runtime_failure",
                supporting_object_ids=[failure_episode.memory_id],
                candidate_actions=candidate_actions,
                candidate_features=candidate_features,
                gating_results={
                    "runtime_failure": True,
                    "procedure_available": False,
                    "fact_available": False,
                    "decision_gap": False,
                    "claim_available": False,
                    "has_context": bool(retrieved),
                },
                memory_input_ids=memory_input_ids,
                confidence=1.0,
                requires_review=True,
            )

        procedure_memory = self._best_memory_by_type(
            retrieved,
            memory_type="procedure",
        )
        if procedure_memory is not None:
            return self._suggestion(
                goal=goal,
                action_type="apply_procedure",
                next_action=(
                    f"Apply procedure '{procedure_memory.memory_id}' "
                    f"for goal '{goal.title}'"
                ),
                reason_code="procedure_available",
                supporting_object_ids=[procedure_memory.memory_id],
                candidate_actions=candidate_actions,
                candidate_features=candidate_features,
                gating_results={
                    "runtime_failure": False,
                    "procedure_available": True,
                    "fact_available": False,
                    "decision_gap": False,
                    "claim_available": False,
                    "has_context": bool(retrieved),
                },
                memory_input_ids=memory_input_ids,
                confidence=0.95,
            )

        fact_memory = self._best_memory_by_type(
            retrieved,
            memory_type="fact",
        )
        if fact_memory is not None:
            return self._suggestion(
                goal=goal,
                action_type="validate_fact",
                next_action=(
                    f"Validate fact '{fact_memory.memory_id}' "
                    f"against goal '{goal.title}'"
                ),
                reason_code="fact_available",
                supporting_object_ids=[fact_memory.memory_id],
                candidate_actions=candidate_actions,
                candidate_features=candidate_features,
                gating_results={
                    "runtime_failure": False,
                    "procedure_available": False,
                    "fact_available": True,
                    "decision_gap": False,
                    "claim_available": False,
                    "has_context": bool(retrieved),
                },
                memory_input_ids=memory_input_ids,
                confidence=0.9,
            )

        if self._has_unresolved_decision_gap(retrieved):
            supporting_ids = [item.memory_id for item in retrieved[:3]]
            return self._suggestion(
                goal=goal,
                action_type="record_decision",
                next_action=(
                    f"Record the next decision needed to advance goal '{goal.title}'"
                ),
                reason_code="decision_gap",
                supporting_object_ids=supporting_ids,
                candidate_actions=candidate_actions,
                candidate_features=candidate_features,
                gating_results={
                    "runtime_failure": False,
                    "procedure_available": False,
                    "fact_available": False,
                    "decision_gap": True,
                    "claim_available": False,
                    "has_context": bool(retrieved),
                },
                memory_input_ids=memory_input_ids,
                confidence=0.85,
                requires_review=True,
            )

        claim_memory = self._best_memory_by_type(
            retrieved,
            memory_type="claim",
        )
        if claim_memory is not None:
            return self._suggestion(
                goal=goal,
                action_type="confirm_claim",
                next_action=(
                    f"Confirm claim '{claim_memory.memory_id}' "
                    f"for goal '{goal.title}'"
                ),
                reason_code="claim_available",
                supporting_object_ids=[claim_memory.memory_id],
                candidate_actions=candidate_actions,
                candidate_features=candidate_features,
                gating_results={
                    "runtime_failure": False,
                    "procedure_available": False,
                    "fact_available": False,
                    "decision_gap": False,
                    "claim_available": True,
                    "has_context": bool(retrieved),
                },
                memory_input_ids=memory_input_ids,
                confidence=0.8,
            )

        if retrieved:
            primary = retrieved[0]
            return self._suggestion(
                goal=goal,
                action_type="review_memory",
                next_action=(
                    f"Review {primary.memory_type} '{primary.memory_id}' "
                    f"for goal '{goal.title}'"
                ),
                reason_code="generic_review",
                supporting_object_ids=[primary.memory_id],
                candidate_actions=candidate_actions,
                candidate_features=candidate_features,
                gating_results={
                    "runtime_failure": False,
                    "procedure_available": False,
                    "fact_available": False,
                    "decision_gap": False,
                    "claim_available": False,
                    "has_context": True,
                },
                memory_input_ids=memory_input_ids,
                confidence=0.7,
            )

        return self._suggestion(
            goal=goal,
            action_type="capture_decision",
            next_action=(
                f"Capture the next decision needed to advance goal '{goal.title}'"
            ),
            reason_code="no_context",
            supporting_object_ids=[],
            candidate_actions=candidate_actions,
            candidate_features=candidate_features,
            gating_results={
                "runtime_failure": False,
                "procedure_available": False,
                "fact_available": False,
                "decision_gap": False,
                "claim_available": False,
                "has_context": False,
            },
            memory_input_ids=memory_input_ids,
            confidence=0.6,
            requires_review=True,
        )

    def _suggestion(
        self,
        *,
        goal: Goal,
        action_type: str,
        next_action: str,
        reason_code: str,
        supporting_object_ids: list[str],
        candidate_actions: list[str],
        candidate_features: dict[str, Any],
        gating_results: dict[str, Any],
        memory_input_ids: list[str],
        confidence: float,
        requires_review: bool = False,
    ) -> GoalInferenceSuggestion:
        return GoalInferenceSuggestion(
            goal_id=goal.id,
            inference_mode="deterministic",
            action_type=action_type,
            next_action=next_action,
            reason_code=reason_code,
            supporting_object_ids=supporting_object_ids,
            candidate_actions=candidate_actions,
            candidate_features=candidate_features,
            gating_results=gating_results,
            ranking_policy_version=self.RANKING_POLICY_VERSION,
            memory_input_ids=memory_input_ids,
            sampling_metadata={
                "sampling": "none",
                "seed": "not_applicable",
            },
            confidence=confidence,
            requires_review=requires_review,
        )

    def _candidate_features(
        self,
        retrieved: list[RetrievedMemory],
    ) -> dict[str, Any]:
        memory_types = [item.memory_type for item in retrieved]
        episode_kinds = [
            getattr(item.memory, "kind", None)
            for item in retrieved
            if item.memory_type == "episode"
        ]
        return {
            "retrieved_count": len(retrieved),
            "memory_types": memory_types,
            "episode_kinds": [kind for kind in episode_kinds if kind],
            "has_runtime_failure": "interpret_failure" in episode_kinds,
            "has_procedure": "procedure" in memory_types,
            "has_fact": "fact" in memory_types,
            "has_claim": "claim" in memory_types,
            "has_decision_episode": "decision_recorded" in episode_kinds,
            "has_context": bool(retrieved),
        }

    def _candidate_actions(self, candidate_features: dict[str, Any]) -> list[str]:
        actions: list[str] = [
            "resolve_failure",
            "apply_procedure",
            "validate_fact",
            "record_decision",
            "confirm_claim",
            "review_memory",
            "capture_decision",
        ]
        if not candidate_features.get("has_context", False):
            return ["capture_decision"]
        return actions

    def _best_memory_by_type(
        self,
        retrieved: list[RetrievedMemory],
        *,
        memory_type: str,
    ) -> RetrievedMemory | None:
        for item in retrieved:
            if item.memory_type == memory_type:
                return item
        return None

    def _best_episode_by_kind(
        self,
        retrieved: list[RetrievedMemory],
        *,
        kind: str,
    ) -> RetrievedMemory | None:
        for item in retrieved:
            if item.memory_type != "episode":
                continue
            if getattr(item.memory, "kind", None) == kind:
                return item
        return None

    def _has_unresolved_decision_gap(
        self,
        retrieved: list[RetrievedMemory],
    ) -> bool:
        if len(retrieved) < 2:
            return False
        has_decision = False
        gap_signals = 0
        for item in retrieved:
            if item.memory_type != "episode":
                if item.memory_type in {"fact", "claim", "procedure"}:
                    gap_signals += 1
                continue
            kind = getattr(item.memory, "kind", None)
            if kind == "decision_recorded":
                has_decision = True
            elif kind in {"intent_recorded", "working_memory_update", "user_input"}:
                gap_signals += 1
        return gap_signals > 1 and not has_decision


class GoalContinuationManager:
    """Manage the narrow active-goal stack used by Phase D restore."""

    def __init__(self, store: MemoryStore, interpreter: Any | None = None):
        self.store = store
        self.interpreter = interpreter
        self.retrieval_kernel = RetrievalKernel(store)
        self.inference_kernel = GoalInferenceKernel()

    def get_goal(self, goal_id: str) -> Goal | None:
        return self.store.get_goal(goal_id)

    def list_active_or_suspended_goals(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[Goal]:
        goals = self.store.query_goals(
            agent_id=agent_id,
            session_id=session_id,
            statuses=[
                GoalState.ACTIVE.value,
                GoalState.SUSPENDED.value,
            ],
            limit=limit,
        )
        return self._sort_resumable_goals(goals)

    def restore_goal_stack(
        self,
        goal_ids: list[str],
    ) -> tuple[list[Goal], list[str]]:
        restored: list[Goal] = []
        warnings: list[str] = []
        positions = {goal_id: index for index, goal_id in enumerate(goal_ids)}
        for goal_id in goal_ids:
            goal = self.store.get_goal(goal_id)
            if goal is None:
                warnings.append(f"Goal '{goal_id}' was not found during restore")
                continue
            if goal.status not in _RESUMABLE_GOAL_STATES:
                warnings.append(
                    f"Goal '{goal_id}' is not resumable from status "
                    f"'{goal.status.value}'"
                )
                continue
            restored.append(goal)
        restored.sort(key=lambda goal: positions.get(goal.id, len(positions)))
        self._apply_goal_stack([goal.id for goal in restored])
        return restored, warnings

    def choose_primary_resumable_goal(
        self,
        goals: list[Goal] | None = None,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
    ) -> Goal | None:
        candidates = goals or self.list_active_or_suspended_goals(
            agent_id=agent_id,
            session_id=session_id,
        )
        if not candidates:
            return None

        active_stack = list(getattr(self.interpreter, "active_goal_stack", []))
        for goal_id in reversed(active_stack):
            for goal in candidates:
                if goal.id == goal_id:
                    return goal

        return self._sort_resumable_goals(candidates)[0]

    def get_active_goal(self) -> Goal | None:
        active_stack = list(getattr(self.interpreter, "active_goal_stack", []))
        if not active_stack:
            return None
        return self.store.get_goal(active_stack[-1])

    def open_goal(
        self,
        title: str,
        *,
        workspace_id: str | None = None,
        project_id: str | None = None,
        priority: int | None = None,
        activate: bool = False,
    ) -> GoalStateTransition:
        if self.interpreter is None:
            raise ValueError("GoalContinuationManager requires an interpreter")

        status = GoalState.ACTIVE if activate else GoalState.OPEN
        now = utc_now()
        goal = Goal(
            title=title,
            status=status,
            opened_at=now,
            resumed_at=now if activate else None,
            priority=priority,
            agent_id=self.interpreter.runtime_agent_id,
            session_id=self.interpreter.runtime_session_id,
            workspace_id=workspace_id or self.interpreter.runtime_workspace_id,
            project_id=project_id or self.interpreter.runtime_project_id,
        )
        goal = self.store.save_goal(goal)

        final_stack = list(getattr(self.interpreter, "active_goal_stack", []))
        if activate and goal.id not in final_stack:
            final_stack.append(goal.id)
        stack_changed = final_stack != list(
            getattr(self.interpreter, "active_goal_stack", [])
        )

        evidence_episode_id = self._emit_goal_transition_episode(
            goal,
            previous_status=None,
            current_status=status,
            reason="open",
        )
        if evidence_episode_id is not None:
            goal.linked_episode_ids.append(evidence_episode_id)
            goal = self.store.save_goal(goal)

        self._apply_goal_stack(final_stack)

        checkpoint_id: str | None = None
        if activate and stack_changed:
            checkpoint = self.interpreter.create_checkpoint(
                f"goal opened: {goal.id}"
            )
            checkpoint_id = checkpoint.id

        return GoalStateTransition(
            success=True,
            goal_id=goal.id,
            previous_status=None,
            current_status=goal.status,
            evidence_episode_id=evidence_episode_id,
            checkpoint_id=checkpoint_id,
            stack_changed=stack_changed,
        )

    def resume_goal(
        self,
        goal_id: str,
        *,
        reason: str | None = None,
    ) -> GoalStateTransition:
        return self._transition_goal_state(
            goal_id,
            GoalState.ACTIVE,
            reason=reason or "resume",
        )

    def suspend_goal(
        self,
        goal_id: str,
        *,
        reason: str,
    ) -> GoalStateTransition:
        return self._transition_goal_state(
            goal_id,
            GoalState.SUSPENDED,
            reason=reason,
        )

    def complete_goal(
        self,
        goal_id: str,
        *,
        summary: str,
    ) -> GoalStateTransition:
        return self._transition_goal_state(
            goal_id,
            GoalState.COMPLETED,
            reason=summary,
        )

    def abandon_goal(
        self,
        goal_id: str,
        *,
        reason: str,
    ) -> GoalStateTransition:
        return self._transition_goal_state(
            goal_id,
            GoalState.ABANDONED,
            reason=reason,
        )

    def push_goal(self, goal_id: str) -> Goal:
        goal = self.store.get_goal(goal_id)
        if goal is None:
            raise ValueError(f"Goal '{goal_id}' could not be found")
        if goal.status not in _RESUMABLE_GOAL_STATES:
            raise ValueError(
                f"Goal '{goal_id}' is not resumable from status "
                f"'{goal.status.value}'"
            )
        goal_stack = list(getattr(self.interpreter, "active_goal_stack", []))
        if goal_id not in goal_stack:
            goal_stack.append(goal_id)
        self._apply_goal_stack(goal_stack)
        return goal

    def pop_goal(self) -> Goal | None:
        goal_stack = list(getattr(self.interpreter, "active_goal_stack", []))
        if not goal_stack:
            return None
        goal_id = goal_stack.pop()
        self._apply_goal_stack(goal_stack)
        return self.store.get_goal(goal_id)

    def continue_goal_once(
        self,
        *,
        goal_id: str | None = None,
        top_k: int = 5,
        token_budget: int = 256,
    ) -> GoalContinuationStep:
        warnings: list[str] = []
        goal = self._resolve_continuation_goal(goal_id=goal_id)
        if goal is None:
            return GoalContinuationStep(
                success=False,
                goal_id=goal_id,
                warnings=["No resumable goal is available for continuation"],
            )

        transition: GoalStateTransition | None = None
        current_stack = list(getattr(self.interpreter, "active_goal_stack", []))
        needs_resume = goal.status in {GoalState.OPEN, GoalState.SUSPENDED}
        needs_stack_update = goal.id not in current_stack
        if needs_resume or needs_stack_update:
            transition = self._transition_goal_state(
                goal.id,
                GoalState.ACTIVE,
                reason="continue",
            )
            if not transition.success:
                return GoalContinuationStep(
                    success=False,
                    goal_id=goal.id,
                    warnings=transition.warnings,
                )
            goal = self.store.get_goal(goal.id) or goal

        retrieved = self.retrieval_kernel.retrieve(
            goal.title,
            agent_id=goal.agent_id,
            session_id=goal.session_id,
            tenant_id=goal.tenant_id,
            workspace_id=goal.workspace_id,
            project_id=goal.project_id,
            goal_id=goal.id,
            privacy_scope=goal.privacy_scope,
            top_k=top_k,
            token_budget=token_budget,
        )
        retrieved = [
            item
            for item in retrieved
            if not (
                item.memory_type == "episode"
                and getattr(item.memory, "kind", None) == "goal_state_transition"
            )
        ]
        suggestion = self.inference_kernel.suggest_next_step(goal, retrieved)
        if not suggestion.has_complete_explanation():
            return GoalContinuationStep(
                success=False,
                goal_id=goal.id,
                goal_status=goal.status,
                warnings=[
                    "Goal inference explanation envelope is incomplete; "
                    "continuation aborted"
                ],
            )
        next_action = suggestion.next_action

        evidence_episode_id: str | None = None
        if self.interpreter is not None:
            evidence_episode = self.interpreter.record_memory_episode(
                kind="goal_continuation_step",
                source_type="runtime",
                importance=0.65,
                classification="internal",
                payload={
                    "goal_title": goal.title,
                    "retrieved_count": len(retrieved),
                    "next_action": next_action,
                    "action_type": suggestion.action_type,
                    "reason_code": suggestion.reason_code,
                    "primary_memory_id": (
                        suggestion.supporting_object_ids[0]
                        if suggestion.supporting_object_ids
                        else ""
                    ),
                    "inference": suggestion.explanation_envelope(),
                },
            )
            if evidence_episode is not None:
                evidence_episode_id = evidence_episode.id
                if evidence_episode.id not in goal.linked_episode_ids:
                    goal.linked_episode_ids.append(evidence_episode.id)
                    goal = self.store.save_goal(goal)

        checkpoint_id = transition.checkpoint_id if transition else None

        return GoalContinuationStep(
            success=True,
            goal_id=goal.id,
            goal_status=goal.status,
            next_action=next_action,
            suggestion=suggestion,
            retrieved_memories=retrieved,
            evidence_episode_id=evidence_episode_id,
            checkpoint_id=checkpoint_id,
            warnings=warnings,
        )

    def _apply_goal_stack(self, goal_stack: list[str]) -> None:
        if self.interpreter is None:
            return
        self.interpreter.active_goal_stack = list(goal_stack)

    def _resolve_continuation_goal(self, *, goal_id: str | None) -> Goal | None:
        if goal_id is not None:
            goal = self.store.get_goal(goal_id)
            if goal is None or goal.status not in _RESUMABLE_GOAL_STATES:
                return None
            return goal

        active_goal = self.get_active_goal()
        if active_goal is not None and active_goal.status in _RESUMABLE_GOAL_STATES:
            return active_goal

        agent_id = getattr(self.interpreter, "runtime_agent_id", None)
        session_id = getattr(self.interpreter, "runtime_session_id", None)
        return self.choose_primary_resumable_goal(
            agent_id=agent_id,
            session_id=session_id,
        )

    def _transition_goal_state(
        self,
        goal_id: str,
        target_status: GoalState,
        *,
        reason: str,
    ) -> GoalStateTransition:
        goal = self.store.get_goal(goal_id)
        if goal is None:
            return GoalStateTransition(
                success=False,
                goal_id=goal_id,
                warnings=[f"Goal '{goal_id}' could not be found"],
            )
        if not self._is_valid_transition(goal.status, target_status):
            return GoalStateTransition(
                success=False,
                goal_id=goal_id,
                previous_status=goal.status,
                current_status=goal.status,
                warnings=[
                    f"Goal '{goal_id}' cannot transition from "
                    f"'{goal.status.value}' to '{target_status.value}'"
                ],
            )

        previous_status = goal.status
        status_changed = previous_status != target_status
        final_stack = self._stack_after_transition(goal_id, target_status)
        current_stack = list(getattr(self.interpreter, "active_goal_stack", []))
        stack_changed = final_stack != current_stack

        if status_changed:
            self._apply_status_metadata(goal, target_status)
            goal.status = target_status
            goal = self.store.save_goal(goal)

        evidence_episode_id = self._emit_goal_transition_episode(
            goal,
            previous_status=previous_status,
            current_status=target_status,
            reason=reason,
        )
        if evidence_episode_id is not None and evidence_episode_id not in goal.linked_episode_ids:
            goal.linked_episode_ids.append(evidence_episode_id)
            goal = self.store.save_goal(goal)

        if self.interpreter is not None:
            self._apply_goal_stack(final_stack)

        checkpoint_id: str | None = None
        if self.interpreter is not None and (status_changed or stack_changed):
            checkpoint = self.interpreter.create_checkpoint(
                f"goal state transition: {goal.id} {previous_status.value}->{target_status.value}"
            )
            checkpoint_id = checkpoint.id

        return GoalStateTransition(
            success=True,
            goal_id=goal.id,
            previous_status=previous_status,
            current_status=goal.status,
            evidence_episode_id=evidence_episode_id,
            checkpoint_id=checkpoint_id,
            stack_changed=stack_changed,
        )

    def _is_valid_transition(
        self,
        current_status: GoalState,
        target_status: GoalState,
    ) -> bool:
        if current_status == target_status:
            return True
        if current_status == GoalState.ABANDONED:
            return False
        if current_status == GoalState.COMPLETED:
            return False
        if target_status == GoalState.ACTIVE:
            return current_status in {GoalState.OPEN, GoalState.SUSPENDED}
        if target_status == GoalState.SUSPENDED:
            return current_status in {GoalState.OPEN, GoalState.ACTIVE}
        if target_status in {GoalState.COMPLETED, GoalState.ABANDONED}:
            return current_status in {
                GoalState.OPEN,
                GoalState.ACTIVE,
                GoalState.SUSPENDED,
            }
        return False

    def _apply_status_metadata(
        self,
        goal: Goal,
        target_status: GoalState,
    ) -> None:
        now = utc_now()
        if target_status == GoalState.ACTIVE:
            goal.resumed_at = now
        elif target_status == GoalState.SUSPENDED:
            goal.suspended_at = now
        elif target_status in {GoalState.COMPLETED, GoalState.ABANDONED}:
            goal.completed_at = now

    def _stack_after_transition(
        self,
        goal_id: str,
        target_status: GoalState,
    ) -> list[str]:
        current_stack = list(getattr(self.interpreter, "active_goal_stack", []))
        stack = [candidate for candidate in current_stack if candidate != goal_id]
        if target_status == GoalState.ACTIVE:
            stack.append(goal_id)
        return stack

    def _emit_goal_transition_episode(
        self,
        goal: Goal,
        *,
        previous_status: GoalState | None,
        current_status: GoalState,
        reason: str,
    ) -> str | None:
        if self.interpreter is None:
            return None
        original_stack = list(getattr(self.interpreter, "active_goal_stack", []))
        if goal.id not in original_stack:
            self.interpreter.active_goal_stack = [*original_stack, goal.id]
        try:
            episode = self.interpreter.record_memory_episode(
                kind="goal_state_transition",
                source_type="runtime",
                importance=0.75,
                classification="internal",
                payload={
                    "goal_title": goal.title,
                    "from_status": (
                        previous_status.value
                        if previous_status is not None
                        else "new"
                    ),
                    "to_status": current_status.value,
                    "reason": reason,
                },
            )
        finally:
            self.interpreter.active_goal_stack = original_stack
        if episode is None:
            return None
        return episode.id

    def _sort_resumable_goals(self, goals: list[Goal]) -> list[Goal]:
        return sorted(
            goals,
            key=lambda goal: (
                self._goal_priority(goal),
                goal.resumed_at or goal.opened_at or "",
                goal.id,
            ),
            reverse=True,
        )

    def _goal_priority(self, goal: Goal) -> int:
        if goal.status == GoalState.ACTIVE:
            return 3
        if goal.status == GoalState.SUSPENDED:
            return 2
        if goal.status == GoalState.OPEN:
            return 1
        return 0


class CheckpointManager:
    """Create and restore interpreter checkpoints for narrow persistence."""

    def __init__(
        self,
        store: MemoryStore,
        interpreter: Any | None = None,
        goal_manager: GoalContinuationManager | None = None,
        *,
        policy: MemoryPolicy | None = None,
        policy_kernel: PolicyKernel | None = None,
        audit_kernel: AuditKernel | None = None,
    ):
        self.store = store
        self.interpreter = interpreter
        self.goal_manager = goal_manager
        self.policy_kernel = policy_kernel or PolicyKernel(
            policy or default_runtime_policy()
        )
        self.audit_kernel = audit_kernel

    def create_checkpoint(
        self,
        *,
        reason: str,
        state: CheckpointState = CheckpointState.CURRENT,
    ) -> AgentCheckpoint:
        if self.interpreter is None:
            raise ValueError("CheckpointManager requires an interpreter")
        checkpoint = AgentCheckpoint(
            agent_id=self.interpreter.runtime_agent_id,
            session_id=self.interpreter.runtime_session_id,
            working_state_blob=self.interpreter.export_checkpoint_state(
                reason=reason,
            ),
            last_processed_episode_id=(
                self.interpreter.last_processed_episode_id
                or self.interpreter.last_recorded_episode_id
            ),
            state=state,
            active_goal_stack=list(self.interpreter.active_goal_stack),
            focus_stack=self.interpreter._capture_focus_stack(),
        )
        saved = self.store.save_checkpoint(checkpoint)
        if state == CheckpointState.CURRENT:
            self._supersede_other_current_checkpoints(saved)
        return saved

    def list_checkpoints(
        self,
        *,
        agent_id: str,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[AgentCheckpoint]:
        return self.store.query_checkpoints(
            agent_id=agent_id,
            session_id=session_id,
            limit=limit,
        )

    def restore_latest_checkpoint(
        self,
        agent_id: str,
    ) -> CheckpointRestoration:
        checkpoint = self._latest_current_checkpoint(agent_id)
        if checkpoint is None:
            return CheckpointRestoration(
                success=False,
                checkpoint_id=None,
                warnings=["No current checkpoint found for agent"],
            )
        return self.restore_checkpoint(checkpoint.id)

    def restore_checkpoint(
        self,
        checkpoint_id: str,
    ) -> CheckpointRestoration:
        checkpoint = self.store.get_checkpoint(checkpoint_id)
        if checkpoint is None:
            return CheckpointRestoration(
                success=False,
                checkpoint_id=checkpoint_id,
                warnings=["Checkpoint could not be found"],
            )

        warnings: list[str] = []
        decision = self.policy_kernel.validate_checkpoint_restore(
            checkpoint,
            agent_id=(
                self.interpreter.runtime_agent_id
                if self.interpreter is not None
                else None
            ),
        )
        warnings.extend(decision.warnings)
        if not decision.allowed:
            if self.audit_kernel is not None:
                self.audit_kernel.log_action(
                    subject_type="checkpoint",
                    subject_id=checkpoint.id,
                    action="checkpoint_restore_denied",
                    actor_id=checkpoint.agent_id,
                    policy_fingerprint=decision.policy_fingerprint,
                    details={"violation": decision.message},
                )
            return CheckpointRestoration(
                success=False,
                checkpoint_id=checkpoint.id,
                warnings=[decision.message, *warnings],
            )
        if not self._is_checkpoint_valid(checkpoint):
            return CheckpointRestoration(
                success=False,
                checkpoint_id=checkpoint.id,
                warnings=["Checkpoint integrity validation failed"],
            )

        restored_goals: list[Goal] = []
        if self.goal_manager is not None:
            restored_goals, goal_warnings = self.goal_manager.restore_goal_stack(
                checkpoint.active_goal_stack
            )
            warnings.extend(goal_warnings)
            if not restored_goals:
                restored_goals = self.goal_manager.list_active_or_suspended_goals(
                    agent_id=checkpoint.agent_id,
                    session_id=checkpoint.session_id,
                )
                if restored_goals:
                    self.goal_manager._apply_goal_stack(
                        [goal.id for goal in restored_goals]
                    )

        working_state = dict(checkpoint.working_state_blob)
        if self.audit_kernel is not None:
            self.audit_kernel.log_action(
                subject_type="checkpoint",
                subject_id=checkpoint.id,
                action="checkpoint_restored",
                actor_id=checkpoint.agent_id,
                policy_fingerprint=decision.policy_fingerprint,
                details={
                    "goal_count": len(restored_goals),
                    "has_working_memory": bool(working_state.get("working_memory")),
                },
            )
        return CheckpointRestoration(
            success=True,
            checkpoint_id=checkpoint.id,
            restored_working_memory=dict(
                working_state.get("working_memory", {})
            ),
            restored_intent_stack=list(working_state.get("intent_stack", [])),
            restored_decision_log=list(
                working_state.get("decision_log", [])
            ),
            restored_scope_stack=list(working_state.get("scope_stack", [])),
            restored_goal_stack=restored_goals,
            restored_focus_stack=list(checkpoint.focus_stack),
            restored_current_context=working_state.get("current_context"),
            restored_focus_active=bool(
                working_state.get("focus_block_active")
                or checkpoint.focus_stack
            ),
            last_processed_episode_id=checkpoint.last_processed_episode_id,
            warnings=warnings,
        )

    def mark_checkpoint_current(self, checkpoint_id: str) -> AgentCheckpoint:
        checkpoint = self._require_checkpoint(checkpoint_id)
        checkpoint.state = CheckpointState.CURRENT
        saved = self.store.save_checkpoint(checkpoint)
        self._supersede_other_current_checkpoints(saved)
        return saved

    def invalidate_checkpoint(
        self,
        checkpoint_id: str,
        *,
        reason: str | None = None,
    ) -> AgentCheckpoint:
        checkpoint = self._require_checkpoint(checkpoint_id)
        checkpoint.state = CheckpointState.INVALIDATED
        if reason:
            checkpoint.working_state_blob = {
                **checkpoint.working_state_blob,
                "invalidated_reason": reason,
            }
        return self.store.save_checkpoint(checkpoint)

    def verify_checkpoint_integrity(self, checkpoint_id: str) -> bool:
        checkpoint = self.store.get_checkpoint(checkpoint_id)
        if checkpoint is None:
            return False
        return self._is_checkpoint_valid(checkpoint)

    def _latest_current_checkpoint(
        self,
        agent_id: str,
    ) -> AgentCheckpoint | None:
        for checkpoint in self.store.query_checkpoints(agent_id=agent_id):
            if checkpoint.state == CheckpointState.CURRENT:
                return checkpoint
        return None

    def _supersede_other_current_checkpoints(
        self,
        current_checkpoint: AgentCheckpoint,
    ) -> None:
        checkpoints = self.store.query_checkpoints(
            agent_id=current_checkpoint.agent_id,
        )
        for checkpoint in checkpoints:
            if checkpoint.id == current_checkpoint.id:
                continue
            if checkpoint.state != CheckpointState.CURRENT:
                continue
            checkpoint.state = CheckpointState.SUPERSEDED
            self.store.save_checkpoint(checkpoint)

    def _require_checkpoint(self, checkpoint_id: str) -> AgentCheckpoint:
        checkpoint = self.store.get_checkpoint(checkpoint_id)
        if checkpoint is None:
            raise ValueError(f"Checkpoint '{checkpoint_id}' could not be found")
        return checkpoint

    def _is_checkpoint_valid(self, checkpoint: AgentCheckpoint) -> bool:
        return (
            isinstance(checkpoint.working_state_blob, dict)
            and isinstance(checkpoint.active_goal_stack, list)
            and isinstance(checkpoint.focus_stack, list)
        )
