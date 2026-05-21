from sona.interpreter import SonaUnifiedInterpreter
from sona.runtime.memory import AgentCheckpoint, CheckpointState, Goal, GoalState


def _make_interpreter(tmp_path, *, resume_from_latest_checkpoint=False):
    return SonaUnifiedInterpreter(
        project_root=tmp_path,
        resume_from_latest_checkpoint=resume_from_latest_checkpoint,
    )


def test_create_checkpoint_round_trip_restores_interpreter_state(tmp_path):
    initial = _make_interpreter(tmp_path)
    goal = initial.runtime_memory_store.save_goal(
        Goal(
            title="Resume release work",
            status=GoalState.SUSPENDED,
            agent_id=initial.runtime_agent_id,
            session_id=initial.runtime_session_id,
        )
    )
    initial.active_goal_stack = [goal.id]
    initial.cognitive_monitor.working_memory["cursor"] = 3
    initial.cognitive_monitor.intent_stack.append({"goal": "ship"})
    initial.cognitive_monitor.decision_log.append({"label": "review"})
    initial.cognitive_monitor.scope_stack.append({"name": "release"})
    initial.cognitive_monitor.focus_sessions.append(
        {"description": "release", "minutes": 25}
    )
    initial.current_context = "resume release context"
    initial.last_processed_episode_id = "ep_last"

    checkpoint = initial.create_checkpoint("before shutdown")

    restored = _make_interpreter(
        tmp_path,
        resume_from_latest_checkpoint=True,
    )

    assert restored.restored_checkpoint is not None
    assert restored.restored_checkpoint.checkpoint_id == checkpoint.id
    assert restored.cognitive_monitor.working_memory == {"cursor": 3}
    assert restored.cognitive_monitor.intent_stack == [{"goal": "ship"}]
    assert restored.cognitive_monitor.decision_log == [{"label": "review"}]
    assert restored.cognitive_monitor.scope_stack == [{"name": "release"}]
    assert restored.cognitive_monitor.focus_sessions == [
        {"description": "release", "minutes": 25}
    ]
    assert restored.active_goal_stack == [goal.id]
    assert restored.get_active_goal() is not None
    assert restored.get_active_goal().id == goal.id
    assert restored.last_processed_episode_id == "ep_last"
    assert restored.current_context == "resume release context"


def test_restore_latest_checkpoint_prefers_current_state(tmp_path):
    interpreter = _make_interpreter(tmp_path)
    goal = interpreter.runtime_memory_store.save_goal(
        Goal(
            title="Restore priority goal",
            status=GoalState.SUSPENDED,
            agent_id=interpreter.runtime_agent_id,
            session_id=interpreter.runtime_session_id,
        )
    )
    superseded = interpreter.runtime_memory_store.save_checkpoint(
        AgentCheckpoint(
            agent_id=interpreter.runtime_agent_id,
            session_id=interpreter.runtime_session_id,
            created_at="2026-03-15T09:00:00Z",
            state=CheckpointState.SUPERSEDED,
            working_state_blob={"working_memory": {"value": "old"}},
            active_goal_stack=[goal.id],
        )
    )
    current = interpreter.runtime_memory_store.save_checkpoint(
        AgentCheckpoint(
            agent_id=interpreter.runtime_agent_id,
            session_id=interpreter.runtime_session_id,
            created_at="2026-03-15T10:00:00Z",
            state=CheckpointState.CURRENT,
            working_state_blob={"working_memory": {"value": "current"}},
            active_goal_stack=[goal.id],
        )
    )
    interpreter.runtime_memory_store.save_checkpoint(
        AgentCheckpoint(
            agent_id=interpreter.runtime_agent_id,
            session_id=interpreter.runtime_session_id,
            created_at="2026-03-15T11:00:00Z",
            state=CheckpointState.INVALIDATED,
            working_state_blob={"working_memory": {"value": "bad"}},
            active_goal_stack=[goal.id],
        )
    )

    restored = _make_interpreter(
        tmp_path,
        resume_from_latest_checkpoint=True,
    )

    assert restored.restored_checkpoint is not None
    assert restored.restored_checkpoint.checkpoint_id == current.id
    assert restored.cognitive_monitor.working_memory == {"value": "current"}
    assert restored.restored_checkpoint.checkpoint_id != superseded.id


def test_restore_preserves_goal_stack_order_and_active_goal(tmp_path):
    initial = _make_interpreter(tmp_path)
    goal_a = initial.runtime_memory_store.save_goal(
        Goal(
            title="Older resumable goal",
            status=GoalState.SUSPENDED,
            agent_id=initial.runtime_agent_id,
            session_id=initial.runtime_session_id,
        )
    )
    goal_b = initial.runtime_memory_store.save_goal(
        Goal(
            title="Top of stack goal",
            status=GoalState.ACTIVE,
            agent_id=initial.runtime_agent_id,
            session_id=initial.runtime_session_id,
        )
    )
    initial.active_goal_stack = [goal_a.id, goal_b.id]

    initial.create_checkpoint("persist active stack")
    restored = _make_interpreter(
        tmp_path,
        resume_from_latest_checkpoint=True,
    )

    assert restored.active_goal_stack == [goal_a.id, goal_b.id]
    assert restored.get_active_goal() is not None
    assert restored.get_active_goal().id == goal_b.id


def test_restore_latest_checkpoint_is_idempotent(tmp_path):
    initial = _make_interpreter(tmp_path)
    goal = initial.runtime_memory_store.save_goal(
        Goal(
            title="Idempotent restore goal",
            status=GoalState.SUSPENDED,
            agent_id=initial.runtime_agent_id,
            session_id=initial.runtime_session_id,
        )
    )
    initial.active_goal_stack = [goal.id]
    initial.cognitive_monitor.focus_sessions.append(
        {"description": "focus", "minutes": 15}
    )
    checkpoint = initial.create_checkpoint("idempotency")

    restored = _make_interpreter(tmp_path)
    first = restored.restore_latest_checkpoint()
    second = restored.restore_latest_checkpoint()

    assert first is not None
    assert second is not None
    assert first.checkpoint_id == checkpoint.id
    assert second.checkpoint_id == checkpoint.id
    assert restored.active_goal_stack == [goal.id]
    assert restored.cognitive_monitor.focus_sessions == [
        {"description": "focus", "minutes": 15}
    ]


def test_restore_checkpoint_does_not_create_claims_or_facts(tmp_path):
    initial = _make_interpreter(tmp_path)
    goal = initial.runtime_memory_store.save_goal(
        Goal(
            title="Operational restore only",
            status=GoalState.SUSPENDED,
            agent_id=initial.runtime_agent_id,
            session_id=initial.runtime_session_id,
        )
    )
    initial.active_goal_stack = [goal.id]
    initial.cognitive_monitor.working_memory["note"] = "resume only"
    initial.create_checkpoint("restore without promotion")

    restored = _make_interpreter(
        tmp_path,
        resume_from_latest_checkpoint=True,
    )

    assert restored.runtime_memory_store.query_claims(
        agent_id=restored.runtime_agent_id
    ) == []
    assert restored.runtime_memory_store.query_facts(
        agent_id=restored.runtime_agent_id
    ) == []


def test_restore_checkpoint_rejects_invalidated_checkpoint(tmp_path):
    interpreter = _make_interpreter(tmp_path)
    checkpoint = interpreter.runtime_memory_store.save_checkpoint(
        AgentCheckpoint(
            agent_id=interpreter.runtime_agent_id,
            session_id=interpreter.runtime_session_id,
            state=CheckpointState.INVALIDATED,
            working_state_blob={"working_memory": {"value": "bad"}},
        )
    )

    restoration = interpreter.restore_checkpoint(checkpoint.id)

    assert restoration.success is False
    assert restoration.checkpoint_id == checkpoint.id
    assert any("invalidated checkpoints cannot be restored" in item.lower() for item in restoration.warnings)


def test_goal_manager_lists_only_active_or_suspended_goals(tmp_path):
    interpreter = _make_interpreter(tmp_path)
    interpreter.runtime_memory_store.save_goal(
        Goal(
            title="Active goal",
            status=GoalState.ACTIVE,
            agent_id=interpreter.runtime_agent_id,
            session_id=interpreter.runtime_session_id,
        )
    )
    interpreter.runtime_memory_store.save_goal(
        Goal(
            title="Suspended goal",
            status=GoalState.SUSPENDED,
            agent_id=interpreter.runtime_agent_id,
            session_id=interpreter.runtime_session_id,
        )
    )
    interpreter.runtime_memory_store.save_goal(
        Goal(
            title="Completed goal",
            status=GoalState.COMPLETED,
            agent_id=interpreter.runtime_agent_id,
            session_id=interpreter.runtime_session_id,
        )
    )

    goals = interpreter.list_active_or_suspended_goals(
        session_id=interpreter.runtime_session_id,
    )

    assert [goal.status for goal in goals] == [
        GoalState.ACTIVE,
        GoalState.SUSPENDED,
    ]


def test_continuation_step_restores_goal_and_persists_evidence(tmp_path):
    initial = _make_interpreter(tmp_path)
    goal = initial.runtime_memory_store.save_goal(
        Goal(
            title="Ship release",
            status=GoalState.SUSPENDED,
            agent_id=initial.runtime_agent_id,
            session_id=initial.runtime_session_id,
        )
    )
    initial.active_goal_stack = [goal.id]
    seed_episode = initial.record_memory_episode(
        kind="working_memory_update",
        payload={"action": "store", "key": "release_cursor"},
        importance=0.8,
    )
    assert seed_episode is not None
    initial.create_checkpoint("before continuation")

    restored = _make_interpreter(tmp_path, resume_from_latest_checkpoint=True)
    step = restored.run_goal_continuation_step()

    assert step.success is True
    assert step.goal_id == goal.id
    assert step.goal_status == GoalState.ACTIVE
    assert step.evidence_episode_id is not None
    assert step.checkpoint_id is not None
    assert step.retrieved_memories
    assert step.retrieved_memories[0].memory_id == seed_episode.id
    assert step.next_action == (
        f"Review episode '{seed_episode.id}' for goal '{goal.title}'"
    )
    assert step.suggestion is not None
    assert step.suggestion.inference_mode == "deterministic"
    assert step.suggestion.reason_code == "generic_review"
    assert step.suggestion.action_type == "review_memory"
    assert step.suggestion.has_complete_explanation() is True
    assert step.suggestion.ranking_policy_version == "deterministic-goal-inference-v1"
    assert step.suggestion.memory_input_ids == [seed_episode.id]

    updated_goal = restored.runtime_memory_store.get_goal(goal.id)
    assert updated_goal is not None
    assert updated_goal.status == GoalState.ACTIVE
    assert step.evidence_episode_id in updated_goal.linked_episode_ids

    evidence_episode = restored.runtime_memory_store.get_episode(
        step.evidence_episode_id
    )
    assert evidence_episode is not None
    assert evidence_episode.kind == "goal_continuation_step"
    assert evidence_episode.goal_id == goal.id
    assert evidence_episode.payload["retrieved_count"] == 1
    assert evidence_episode.payload["reason_code"] == "generic_review"
    assert evidence_episode.payload["inference"]["goal_id"] == goal.id
    assert evidence_episode.payload["inference"]["inference_mode"] == "deterministic"
    assert evidence_episode.payload["inference"]["ranking_policy_version"] == (
        "deterministic-goal-inference-v1"
    )
    assert evidence_episode.payload["inference"]["memory_input_ids"] == [
        seed_episode.id
    ]
    assert evidence_episode.payload["inference"]["sampling_metadata"] == {
        "sampling": "none",
        "seed": "not_applicable",
    }


def test_continuation_step_for_active_goal_skips_checkpoint_without_transition(tmp_path):
    interpreter = _make_interpreter(tmp_path)
    goal = interpreter.runtime_memory_store.save_goal(
        Goal(
            title="Already active",
            status=GoalState.ACTIVE,
            agent_id=interpreter.runtime_agent_id,
            session_id=interpreter.runtime_session_id,
        )
    )
    interpreter.active_goal_stack = [goal.id]

    step = interpreter.run_goal_continuation_step()

    assert step.success is True
    assert step.goal_status == GoalState.ACTIVE
    assert step.checkpoint_id is None
    assert step.retrieved_memories == []
    assert step.next_action == (
        f"Capture the next decision needed to advance goal '{goal.title}'"
    )
    assert step.suggestion is not None
    assert step.suggestion.reason_code == "no_context"
    assert step.suggestion.inference_mode == "deterministic"
    assert step.suggestion.has_complete_explanation() is True

    evidence_episode = interpreter.runtime_memory_store.get_episode(
        step.evidence_episode_id
    )
    assert evidence_episode is not None
    assert evidence_episode.kind == "goal_continuation_step"
    assert evidence_episode.payload["retrieved_count"] == 0


def test_continuation_step_without_resumable_goal_returns_failure(tmp_path):
    interpreter = _make_interpreter(tmp_path)

    step = interpreter.run_goal_continuation_step()

    assert step.success is False
    assert step.goal_id is None
    assert step.evidence_episode_id is None
    assert step.checkpoint_id is None
    assert step.warnings == ["No resumable goal is available for continuation"]


def test_resume_and_suspend_goal_create_transition_evidence_and_checkpoint(tmp_path):
    interpreter = _make_interpreter(tmp_path)
    goal = interpreter.runtime_memory_store.save_goal(
        Goal(
            title="Lifecycle goal",
            status=GoalState.SUSPENDED,
            agent_id=interpreter.runtime_agent_id,
            session_id=interpreter.runtime_session_id,
        )
    )

    resumed = interpreter.resume_goal(goal.id, reason="resume work")

    assert resumed.success is True
    assert resumed.previous_status == GoalState.SUSPENDED
    assert resumed.current_status == GoalState.ACTIVE
    assert resumed.stack_changed is True
    assert resumed.evidence_episode_id is not None
    assert resumed.checkpoint_id is not None
    assert interpreter.active_goal_stack == [goal.id]

    resumed_episode = interpreter.runtime_memory_store.get_episode(
        resumed.evidence_episode_id
    )
    assert resumed_episode is not None
    assert resumed_episode.kind == "goal_state_transition"
    assert resumed_episode.goal_id == goal.id
    assert resumed_episode.payload["from_status"] == "suspended"
    assert resumed_episode.payload["to_status"] == "active"

    suspended = interpreter.suspend_goal(goal.id, reason="waiting on review")

    assert suspended.success is True
    assert suspended.previous_status == GoalState.ACTIVE
    assert suspended.current_status == GoalState.SUSPENDED
    assert suspended.stack_changed is True
    assert suspended.evidence_episode_id is not None
    assert suspended.checkpoint_id is not None
    assert interpreter.active_goal_stack == []

    updated_goal = interpreter.runtime_memory_store.get_goal(goal.id)
    assert updated_goal is not None
    assert updated_goal.status == GoalState.SUSPENDED


def test_complete_and_abandon_goal_remove_from_stack_and_checkpoint(tmp_path):
    interpreter = _make_interpreter(tmp_path)
    complete_goal = interpreter.runtime_memory_store.save_goal(
        Goal(
            title="Finish goal",
            status=GoalState.ACTIVE,
            agent_id=interpreter.runtime_agent_id,
            session_id=interpreter.runtime_session_id,
        )
    )
    abandon_goal = interpreter.runtime_memory_store.save_goal(
        Goal(
            title="Drop goal",
            status=GoalState.ACTIVE,
            agent_id=interpreter.runtime_agent_id,
            session_id=interpreter.runtime_session_id,
        )
    )

    interpreter.active_goal_stack = [complete_goal.id, abandon_goal.id]

    completed = interpreter.complete_goal(
        abandon_goal.id,
        summary="done with the active branch",
    )

    assert completed.success is True
    assert completed.current_status == GoalState.COMPLETED
    assert completed.stack_changed is True
    assert completed.checkpoint_id is not None
    assert interpreter.active_goal_stack == [complete_goal.id]

    abandoned = interpreter.abandon_goal(
        complete_goal.id,
        reason="superseded by another plan",
    )

    assert abandoned.success is True
    assert abandoned.current_status == GoalState.ABANDONED
    assert abandoned.stack_changed is True
    assert abandoned.checkpoint_id is not None
    assert interpreter.active_goal_stack == []

    stored_completed = interpreter.runtime_memory_store.get_goal(abandon_goal.id)
    stored_abandoned = interpreter.runtime_memory_store.get_goal(complete_goal.id)
    assert stored_completed is not None
    assert stored_completed.status == GoalState.COMPLETED
    assert stored_completed.completed_at is not None
    assert stored_abandoned is not None
    assert stored_abandoned.status == GoalState.ABANDONED
    assert stored_abandoned.completed_at is not None


def test_continuation_step_prefers_decision_gap_when_context_exists_without_decision(tmp_path):
    interpreter = _make_interpreter(tmp_path)
    goal = interpreter.runtime_memory_store.save_goal(
        Goal(
            title="Decision gap goal",
            status=GoalState.ACTIVE,
            agent_id=interpreter.runtime_agent_id,
            session_id=interpreter.runtime_session_id,
        )
    )
    interpreter.active_goal_stack = [goal.id]
    first = interpreter.record_memory_episode(
        kind="intent_recorded",
        payload={
            "goal": goal.title,
            "has_constraints": True,
            "has_success": False,
        },
        importance=0.8,
    )
    second = interpreter.record_memory_episode(
        kind="working_memory_update",
        payload={"action": "store", "key": "decision-gap"},
        importance=0.8,
    )

    assert first is not None
    assert second is not None

    step = interpreter.run_goal_continuation_step()

    assert step.success is True
    assert step.next_action == (
        f"Record the next decision needed to advance goal '{goal.title}'"
    )
    assert step.suggestion is not None
    assert step.suggestion.reason_code == "decision_gap"
    assert step.suggestion.action_type == "record_decision"
    assert step.suggestion.inference_mode == "deterministic"
    assert step.suggestion.has_complete_explanation() is True


def test_goal_continuation_inference_does_not_create_claims_or_facts(tmp_path):
    interpreter = _make_interpreter(tmp_path)
    goal = interpreter.runtime_memory_store.save_goal(
        Goal(
            title="Inference remains operational",
            status=GoalState.ACTIVE,
            agent_id=interpreter.runtime_agent_id,
            session_id=interpreter.runtime_session_id,
        )
    )
    interpreter.active_goal_stack = [goal.id]
    episode = interpreter.record_memory_episode(
        kind="working_memory_update",
        payload={"action": "store", "key": "inference-only"},
        importance=0.8,
    )

    assert episode is not None

    step = interpreter.run_goal_continuation_step()

    assert step.success is True
    assert interpreter.runtime_memory_store.query_claims(
        agent_id=interpreter.runtime_agent_id
    ) == []
    assert interpreter.runtime_memory_store.query_facts(
        agent_id=interpreter.runtime_agent_id
    ) == []


def test_open_goal_without_activation_persists_evidence_without_checkpoint(tmp_path):
    interpreter = _make_interpreter(tmp_path)

    opened = interpreter.open_goal("Draft release notes")

    assert opened.success is True
    assert opened.previous_status is None
    assert opened.current_status == GoalState.OPEN
    assert opened.stack_changed is False
    assert opened.checkpoint_id is None
    assert interpreter.active_goal_stack == []

    goal = interpreter.runtime_memory_store.get_goal(opened.goal_id)
    assert goal is not None
    assert goal.status == GoalState.OPEN
    assert opened.evidence_episode_id in goal.linked_episode_ids

    evidence_episode = interpreter.runtime_memory_store.get_episode(
        opened.evidence_episode_id
    )
    assert evidence_episode is not None
    assert evidence_episode.kind == "goal_state_transition"
    assert evidence_episode.payload["from_status"] == "new"
    assert evidence_episode.payload["to_status"] == "open"


def test_open_goal_with_activation_updates_stack_and_checkpoint(tmp_path):
    interpreter = _make_interpreter(tmp_path)

    opened = interpreter.open_goal("Ship release", activate=True)

    assert opened.success is True
    assert opened.current_status == GoalState.ACTIVE
    assert opened.stack_changed is True
    assert opened.checkpoint_id is not None
    assert interpreter.active_goal_stack == [opened.goal_id]

    goal = interpreter.runtime_memory_store.get_goal(opened.goal_id)
    assert goal is not None
    assert goal.status == GoalState.ACTIVE
    assert goal.resumed_at is not None


def test_continuation_step_prefers_failure_reason_code(tmp_path):
    interpreter = _make_interpreter(tmp_path)
    goal = interpreter.runtime_memory_store.save_goal(
        Goal(
            title="Failure goal",
            status=GoalState.ACTIVE,
            agent_id=interpreter.runtime_agent_id,
            session_id=interpreter.runtime_session_id,
        )
    )
    interpreter.active_goal_stack = [goal.id]
    failure = interpreter.record_memory_episode(
        kind="interpret_failure",
        payload={
            "filename": "demo.sona",
            "error_type": "RuntimeError",
            "message": "boom",
        },
        importance=0.9,
    )
    context = interpreter.record_memory_episode(
        kind="working_memory_update",
        payload={"action": "store", "key": "context"},
        importance=0.8,
    )

    assert failure is not None
    assert context is not None

    step = interpreter.run_goal_continuation_step()

    assert step.suggestion is not None
    assert step.suggestion.reason_code == "runtime_failure"
    assert step.suggestion.action_type == "resolve_failure"
    assert step.suggestion.supporting_object_ids == [failure.id]
    assert step.next_action == (
        f"Resolve runtime failure '{failure.id}' for goal '{goal.title}'"
    )