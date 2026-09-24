"""API-first workflow progress and transition tests (no step execution)."""

from __future__ import annotations

from datetime import datetime

import pytest

from sona.workflow import (
    StepDefinition,
    StepState,
    TaskDefinition,
    TaskState,
    UnknownWorkflow,
    WorkflowDefinition,
    WorkflowLedger,
    WorkflowLedgerError,
    WorkflowState,
    WorkflowTransitionError,
    new_step_id,
    new_task_id,
    new_workflow_id,
)


def _definition(*, cross_task_dependency: bool = False) -> tuple[WorkflowDefinition, tuple]:
    workflow_id = new_workflow_id()
    task_a = new_task_id()
    task_b = new_task_id() if cross_task_dependency else task_a
    first, second = new_step_id(), new_step_id()
    third = new_step_id() if cross_task_dependency else None
    task_a_steps = [StepDefinition(first, "build")]
    task_b_steps = []
    if cross_task_dependency:
        task_b_steps.append(StepDefinition(second, "test", depends_on=(first,)))
        task_b_steps.append(StepDefinition(third, "publish", depends_on=(second,)))
        tasks = (
            TaskDefinition(task_a, tuple(task_a_steps)),
            TaskDefinition(task_b, tuple(task_b_steps)),
        )
        ids = (workflow_id, task_a, task_b, first, second, third)
    else:
        task_a_steps.append(StepDefinition(second, "test", depends_on=(first,)))
        tasks = (TaskDefinition(task_a, tuple(task_a_steps)),)
        ids = (workflow_id, task_a, first, second)
    return WorkflowDefinition(workflow_id, tasks), ids


def test_created_workflow_has_stable_progress_then_readies_only_roots():
    definition, (_, _, first, second) = _definition()
    ledger = WorkflowLedger()
    created = ledger.create(definition)
    assert created.state is WorkflowState.CREATED
    assert created.progress.completed_steps == 0
    assert created.progress.total_steps == 2
    assert created.progress.percent_complete == 0
    assert created.terminal_outcome is None

    prepared = ledger.prepare(definition.workflow_id)
    assert prepared.state is WorkflowState.READY
    assert [step.state for step in prepared.steps] == [StepState.READY, StepState.BLOCKED]
    assert [step.step_id for step in prepared.steps] == [first, second]


def test_dependency_order_and_success_produce_terminal_outcome_and_progress():
    definition, (_, task_id, first, second) = _definition()
    ledger = WorkflowLedger()
    ledger.create(definition)
    ledger.prepare(definition.workflow_id)

    before = ledger.snapshot(definition.workflow_id)
    with pytest.raises(WorkflowTransitionError, match="ready step"):
        ledger.start_step(definition.workflow_id, second)
    assert ledger.snapshot(definition.workflow_id) == before

    running = ledger.start_step(definition.workflow_id, first)
    assert running.state is WorkflowState.RUNNING
    assert running.steps[0].attempt_count == 1
    assert running.steps[0].started_at_utc is not None
    with pytest.raises(WorkflowTransitionError, match="available"):
        ledger.start_step(definition.workflow_id, first)
    assert ledger.succeed_step(definition.workflow_id, first).steps[1].state is StepState.READY

    ledger.start_step(definition.workflow_id, second)
    done = ledger.succeed_step(definition.workflow_id, second)
    assert done.state is WorkflowState.SUCCEEDED
    assert done.terminal_outcome is WorkflowState.SUCCEEDED
    assert done.progress.completed_steps == 2
    assert done.progress.percent_complete == 100
    assert done.finished_at_utc is not None
    assert all(task.state is TaskState.SUCCEEDED for task in done.tasks)
    assert done.tasks[0].task_id == task_id


def test_cross_task_dependencies_release_in_dag_order():
    definition, (_, _, _, first, second, third) = _definition(cross_task_dependency=True)
    ledger = WorkflowLedger()
    ledger.create(definition)
    ledger.prepare(definition.workflow_id)
    assert [step.state for step in ledger.snapshot(definition.workflow_id).steps] == [
        StepState.READY,
        StepState.BLOCKED,
        StepState.BLOCKED,
    ]
    ledger.start_step(definition.workflow_id, first)
    progress = ledger.succeed_step(definition.workflow_id, first)
    assert progress.steps[1].state is StepState.READY
    assert progress.steps[2].state is StepState.BLOCKED
    ledger.start_step(definition.workflow_id, second)
    progress = ledger.succeed_step(definition.workflow_id, second)
    assert progress.steps[2].state is StepState.READY
    ledger.start_step(definition.workflow_id, third)
    assert ledger.succeed_step(definition.workflow_id, third).state is WorkflowState.SUCCEEDED


def test_failure_is_terminal_skips_pending_steps_and_stores_only_safe_code():
    definition, (_, _, first, second) = _definition()
    ledger = WorkflowLedger()
    ledger.create(definition)
    ledger.prepare(definition.workflow_id)
    ledger.start_step(definition.workflow_id, first)
    failed = ledger.fail_step(definition.workflow_id, first, failure_code="SONA-BUILD-17")
    assert failed.state is WorkflowState.FAILED
    assert failed.terminal_outcome is WorkflowState.FAILED
    assert failed.steps[0].failure_code == "SONA-BUILD-17"
    assert failed.steps[1].state is StepState.SKIPPED
    assert failed.progress.completed_steps == 2
    with pytest.raises(WorkflowTransitionError):
        ledger.start_step(definition.workflow_id, second)


def test_blocked_step_can_be_explicitly_released_only_when_dependencies_succeed():
    definition, (_, _, first, second) = _definition()
    ledger = WorkflowLedger()
    ledger.create(definition)
    ledger.prepare(definition.workflow_id)
    ledger.block_step(definition.workflow_id, first, failure_code="POLICY-REVIEW")
    assert ledger.snapshot(definition.workflow_id).state is WorkflowState.BLOCKED
    before = ledger.snapshot(definition.workflow_id)
    with pytest.raises(WorkflowTransitionError, match="dependencies"):
        ledger.unblock_step(definition.workflow_id, second)
    assert ledger.snapshot(definition.workflow_id) == before
    ready = ledger.unblock_step(definition.workflow_id, first)
    assert ready.state is WorkflowState.READY
    assert ready.steps[0].failure_code is None


def test_cancellation_before_execution_is_terminal_and_running_cancel_requires_ack():
    definition, (_, _, first, second) = _definition()
    ledger = WorkflowLedger()
    ledger.create(definition)
    ledger.prepare(definition.workflow_id)
    canceled = ledger.cancel(definition.workflow_id)
    assert canceled.state is WorkflowState.CANCELED
    assert canceled.terminal_outcome is WorkflowState.CANCELED
    assert [step.state for step in canceled.steps] == [StepState.CANCELED, StepState.CANCELED]

    another, (workflow_id, _, first, second) = _definition()
    ledger.create(another)
    ledger.prepare(workflow_id)
    ledger.start_step(workflow_id, first)
    stopping = ledger.cancel(workflow_id)
    assert stopping.state is WorkflowState.CANCELING
    assert stopping.terminal_outcome is None
    assert stopping.steps[0].state is StepState.CANCELING
    assert stopping.steps[1].state is StepState.CANCELED
    done = ledger.finish_step_cancellation(workflow_id, first)
    assert done.state is WorkflowState.CANCELED
    assert done.terminal_outcome is WorkflowState.CANCELED
    with pytest.raises(WorkflowTransitionError):
        ledger.finish_step_cancellation(workflow_id, second)


def test_invalid_failure_code_or_unknown_identity_does_not_mutate_state():
    definition, (_, _, first, _) = _definition()
    ledger = WorkflowLedger()
    ledger.create(definition)
    ledger.prepare(definition.workflow_id)
    ledger.start_step(definition.workflow_id, first)
    before = ledger.snapshot(definition.workflow_id)
    with pytest.raises(WorkflowLedgerError, match="safe diagnostic"):
        ledger.fail_step(definition.workflow_id, first, failure_code="raw path C:\\secret")
    assert ledger.snapshot(definition.workflow_id) == before
    with pytest.raises(UnknownWorkflow, match="unknown"):
        ledger.snapshot(new_workflow_id())


def test_duplicate_workflow_id_is_rejected_without_replacing_existing_state():
    definition, _ = _definition()
    ledger = WorkflowLedger()
    original = ledger.create(definition)
    with pytest.raises(WorkflowLedgerError, match="already exists"):
        ledger.create(definition)
    assert ledger.snapshot(definition.workflow_id) == original


def test_naive_clock_is_rejected_before_authoritative_state_is_created():
    definition, _ = _definition()
    ledger = WorkflowLedger(clock=lambda: datetime(2026, 9, 24))
    with pytest.raises(WorkflowLedgerError, match="timezone-aware"):
        ledger.create(definition)
    with pytest.raises(UnknownWorkflow):
        ledger.snapshot(definition.workflow_id)


def test_progress_records_are_inert_and_never_execute_step_operation():
    definition, (_, _, first, _) = _definition()
    dangerous = WorkflowDefinition(
        definition.workflow_id,
        (
            TaskDefinition(
                definition.tasks[0].task_id,
                (StepDefinition(first, "process.execute: delete-user-data"),),
            ),
        ),
    )
    ledger = WorkflowLedger()
    snapshot = ledger.create(dangerous)
    assert snapshot.steps[0].state is StepState.CREATED
    assert ledger.snapshot(dangerous.workflow_id).steps[0].attempt_count == 0
