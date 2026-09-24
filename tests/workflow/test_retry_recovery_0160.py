"""Bounded retry scheduling and explicit workflow recovery decisions."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from sona.workflow import (
    RecoveryDecision,
    RetryMode,
    RetryPolicy,
    StepDefinition,
    StepState,
    TaskDefinition,
    WorkflowDefinition,
    WorkflowJournalStore,
    WorkflowLedger,
    WorkflowState,
    WorkflowTransitionError,
    new_step_id,
    new_task_id,
    new_workflow_id,
)


class AdjustableClock:
    def __init__(self):
        self.value = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)

    def __call__(self):
        return self.value

    def advance(self, seconds: float):
        self.value += timedelta(seconds=seconds)


def _definition(policy: RetryPolicy):
    workflow_id = new_workflow_id()
    task_id = new_task_id()
    step_id = new_step_id()
    definition = WorkflowDefinition(
        workflow_id,
        (TaskDefinition(task_id, (StepDefinition(step_id, "build", retry=policy),)),),
    )
    return definition, step_id


def _running_ledger(root, policy, clock):
    definition, step_id = _definition(policy)
    ledger = WorkflowLedger(store=WorkflowJournalStore(root), clock=clock)
    ledger.create(definition)
    ledger.prepare(definition.workflow_id)
    ledger.start_step(definition.workflow_id, step_id)
    return definition, step_id, ledger


def test_exponential_retries_are_bounded_and_released_only_when_due(tmp_path):
    clock = AdjustableClock()
    policy = RetryPolicy(
        mode=RetryMode.EXPONENTIAL,
        maximum_attempts=3,
        delay_seconds=2,
        maximum_delay_seconds=5,
    )
    definition, step_id, ledger = _running_ledger(tmp_path / "state", policy, clock)

    retry1 = ledger.schedule_retry(definition.workflow_id, step_id)
    assert retry1.state is WorkflowState.RETRYING
    assert retry1.steps[0].retry_after_utc == "2026-09-24T12:00:02.000Z"
    assert ledger.release_due_retries() == ()

    clock.advance(2)
    ready1 = ledger.release_due_retries()[0]
    assert ready1.state is WorkflowState.READY
    assert ready1.steps[0].state is StepState.READY
    assert ready1.steps[0].retry_after_utc is None
    ledger.start_step(definition.workflow_id, step_id)
    retry2 = ledger.schedule_retry(definition.workflow_id, step_id)
    assert retry2.steps[0].retry_after_utc == "2026-09-24T12:00:06.000Z"

    clock.advance(4)
    ledger.release_due_retries()
    ledger.start_step(definition.workflow_id, step_id)
    exhausted = ledger.schedule_retry(definition.workflow_id, step_id)
    assert exhausted.state is WorkflowState.FAILED
    assert exhausted.steps[0].attempt_count == 3
    assert exhausted.steps[0].state is StepState.FAILED


def test_retry_schedule_survives_reopen_without_automatic_execution(tmp_path):
    clock = AdjustableClock()
    policy = RetryPolicy(
        mode=RetryMode.FIXED,
        maximum_attempts=2,
        delay_seconds=30,
        maximum_delay_seconds=30,
    )
    definition, step_id, ledger = _running_ledger(tmp_path / "state", policy, clock)
    scheduled = ledger.schedule_retry(definition.workflow_id, step_id)

    reopened = WorkflowLedger(store=WorkflowJournalStore(tmp_path / "state"), clock=clock)
    restored = reopened.restore()[0]
    assert restored == scheduled
    assert restored.state is WorkflowState.RETRYING
    assert restored.steps[0].attempt_count == 1
    assert reopened.snapshot(definition.workflow_id).steps[0].state is StepState.RETRYING
    assert reopened.release_due_retries() == ()

    clock.advance(30)
    ready = reopened.release_due_retries()[0]
    assert ready.steps[0].state is StepState.READY
    assert reopened.start_step(definition.workflow_id, step_id).steps[0].attempt_count == 2


def test_recovery_requires_explicit_audited_decision(tmp_path):
    clock = AdjustableClock()
    policy = RetryPolicy(
        mode=RetryMode.FIXED,
        maximum_attempts=2,
        delay_seconds=1,
        maximum_delay_seconds=1,
    )
    definition, step_id, _ledger = _running_ledger(tmp_path / "state", policy, clock)
    reopened = WorkflowLedger(store=WorkflowJournalStore(tmp_path / "state"), clock=clock)
    recovered = reopened.restore()[0]

    with pytest.raises(WorkflowTransitionError, match="explicit resume decision"):
        reopened.unblock_step(definition.workflow_id, step_id)
    with pytest.raises(WorkflowTransitionError, match="recovery decision"):
        reopened.cancel(definition.workflow_id)

    resumed = reopened.resume_step(
        definition.workflow_id,
        step_id,
        decision=RecoveryDecision.RETRY_FROM_START,
    )
    assert resumed.state is WorkflowState.READY
    assert resumed.steps[0].attempt_count == 1
    assert reopened.start_step(definition.workflow_id, step_id).steps[0].attempt_count == 2

    directory = tmp_path / "state" / "workflows" / str(definition.workflow_id)
    last_event = json.loads((directory / "event-00000005.json").read_text(encoding="utf-8"))
    assert last_event["event_type"] == "workflow.recovery_resumed"
    assert last_event["details"] == {"recovery_decision": "retry_from_start"}
    assert recovered.steps[0].state is StepState.BLOCKED


def test_recovery_can_be_explicitly_marked_failed_when_retry_budget_is_exhausted(tmp_path):
    clock = AdjustableClock()
    policy = RetryPolicy()
    definition, step_id, _ledger = _running_ledger(tmp_path / "state", policy, clock)
    recovered = WorkflowLedger(store=WorkflowJournalStore(tmp_path / "state"), clock=clock)
    recovered.restore()

    with pytest.raises(WorkflowTransitionError, match="no remaining"):
        recovered.resume_step(
            definition.workflow_id,
            step_id,
            decision=RecoveryDecision.RETRY_FROM_START,
        )
    failed = recovered.resume_step(
        definition.workflow_id,
        step_id,
        decision=RecoveryDecision.MARK_FAILED,
    )
    assert failed.state is WorkflowState.FAILED
    assert failed.steps[0].failure_code == "SONA-WORKFLOW-RECOVERY-REJECTED"


def test_canceling_retry_wait_clears_retry_deadline_and_prevents_retry(tmp_path):
    clock = AdjustableClock()
    policy = RetryPolicy(
        mode=RetryMode.FIXED,
        maximum_attempts=3,
        delay_seconds=20,
        maximum_delay_seconds=20,
    )
    definition, step_id, ledger = _running_ledger(tmp_path / "state", policy, clock)
    retrying = ledger.schedule_retry(definition.workflow_id, step_id)
    canceled = ledger.cancel(definition.workflow_id)

    assert retrying.steps[0].retry_after_utc is not None
    assert canceled.state is WorkflowState.CANCELED
    assert canceled.steps[0].retry_after_utc is None
    clock.advance(30)
    assert ledger.release_due_retries() == ()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"maximum_attempts": 0},
        {"maximum_attempts": 1001, "mode": RetryMode.FIXED},
        {"maximum_attempts": True},
        {"delay_seconds": float("inf"), "mode": RetryMode.FIXED},
        {"delay_seconds": -1, "mode": RetryMode.FIXED},
    ],
)
def test_retry_policy_rejects_unbounded_or_invalid_values(kwargs):
    with pytest.raises(ValueError):
        RetryPolicy(**kwargs)


def test_real_process_restart_restores_inert_and_requires_resume_decision(tmp_path):
    root = tmp_path / "process-restart"
    create_script = """
import json, sys
from sona.workflow import (
    RetryMode, RetryPolicy, StepDefinition, TaskDefinition, WorkflowDefinition,
    WorkflowJournalStore, WorkflowLedger, new_step_id, new_task_id, new_workflow_id,
)
root = sys.argv[1]
workflow_id, task_id, step_id = new_workflow_id(), new_task_id(), new_step_id()
policy = RetryPolicy(
    mode=RetryMode.FIXED,
    maximum_attempts=2,
    delay_seconds=1,
    maximum_delay_seconds=1,
)
step = StepDefinition(step_id, "build", retry=policy)
definition = WorkflowDefinition(workflow_id, (TaskDefinition(task_id, (step,)),))
ledger = WorkflowLedger(store=WorkflowJournalStore(root))
ledger.create(definition)
ledger.prepare(workflow_id)
ledger.start_step(workflow_id, step_id)
print(json.dumps([str(workflow_id), str(step_id)]))
"""
    created = subprocess.run(
        [sys.executable, "-c", create_script, str(root)],
        cwd=Path.cwd(),
        capture_output=True,
        check=True,
        text=True,
        timeout=20,
    )
    workflow_id, step_id = json.loads(created.stdout)

    reopen_script = """
import json, sys
from sona.workflow import RecoveryDecision, WorkflowJournalStore, WorkflowLedger
ledger = WorkflowLedger(store=WorkflowJournalStore(sys.argv[1]))
snapshot = ledger.restore()[0]
if snapshot.state.value != "blocked" or snapshot.steps[0].state.value != "blocked":
    raise SystemExit("recovery was not inert")
snapshot = ledger.resume_step(
    snapshot.definition.workflow_id,
    snapshot.steps[0].step_id,
    decision=RecoveryDecision.RETRY_FROM_START,
)
result = [snapshot.state.value, snapshot.steps[0].attempt_count, snapshot.steps[0].state.value]
print(json.dumps(result))
"""
    reopened = subprocess.run(
        [sys.executable, "-c", reopen_script, str(root), workflow_id, step_id],
        cwd=Path.cwd(),
        capture_output=True,
        check=True,
        text=True,
        timeout=20,
    )

    assert json.loads(reopened.stdout) == ["ready", 1, "ready"]
