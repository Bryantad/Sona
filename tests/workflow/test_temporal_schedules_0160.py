"""Durable time-aware workflow scheduling contracts."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta

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
    WorkflowPersistenceError,
    WorkflowState,
    WorkflowTransitionError,
    new_step_id,
    new_task_id,
    new_workflow_id,
)


class AdjustableClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += timedelta(seconds=seconds)


def _rewrite_rehashed_event(path, update):
    event = json.loads(path.read_text(encoding="utf-8"))
    update(event)
    unsigned = dict(event)
    unsigned.pop("event_hash")
    payload = json.dumps(
        unsigned, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    event["event_hash"] = "sha256:" + hashlib.sha256(payload).hexdigest()
    path.write_text(
        json.dumps(event, sort_keys=True, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def _create(
    root,
    clock: AdjustableClock,
    *,
    delay_seconds: float = 0,
    timeout_seconds: float | None = None,
    deadline_utc: str | None = None,
    expires_at_utc: str | None = None,
    retry: RetryPolicy | None = None,
):
    workflow_id = new_workflow_id()
    task_id = new_task_id()
    step_id = new_step_id()
    definition = WorkflowDefinition(
        workflow_id,
        (
            TaskDefinition(
                task_id,
                (
                    StepDefinition(
                        step_id,
                        "build",
                        retry=retry or RetryPolicy(),
                        timeout_seconds=timeout_seconds,
                        delay_seconds=delay_seconds,
                        deadline_utc=deadline_utc,
                        expires_at_utc=expires_at_utc,
                    ),
                ),
            ),
        ),
    )
    store = WorkflowJournalStore(root)
    ledger = WorkflowLedger(store=store, clock=clock)
    ledger.create(definition)
    return definition, step_id, ledger, store


def test_delay_deadline_and_expiration_fields_are_validated_and_normalized():
    workflow_id, task_id, step_id = new_workflow_id(), new_task_id(), new_step_id()
    definition = WorkflowDefinition(
        workflow_id,
        (
            TaskDefinition(
                task_id,
                (
                    StepDefinition(
                        step_id,
                        "build",
                        delay_seconds=2.5,
                        deadline_utc="2026-09-24T08:00:00-04:00",
                        expires_at_utc="2026-09-24T12:01:00Z",
                    ),
                ),
            ),
        ),
    )
    step = definition.tasks[0].steps[0]
    assert step.deadline_utc == "2026-09-24T12:00:00.000Z"
    assert step.expires_at_utc == "2026-09-24T12:01:00.000Z"

    for invalid in (-1, float("inf"), float("nan"), True):
        with pytest.raises(ValueError, match="delay_seconds"):
            StepDefinition(step_id, "build", delay_seconds=invalid)
    for invalid in (0, float("inf"), float("nan"), True):
        with pytest.raises(ValueError, match="timeout"):
            StepDefinition(step_id, "build", timeout_seconds=invalid)
    with pytest.raises(ValueError, match="timezone-aware"):
        StepDefinition(step_id, "build", deadline_utc="2026-09-24T12:00:00")


def test_delayed_step_persists_and_restore_does_not_release_or_execute_it(tmp_path):
    clock = AdjustableClock()
    definition, step_id, ledger, store = _create(tmp_path / "journal", clock, delay_seconds=10)
    prepared = ledger.prepare(definition.workflow_id)
    assert prepared.schema_version == 3
    assert prepared.steps[0].state is StepState.BLOCKED
    assert prepared.steps[0].not_before_utc == "2026-09-24T12:00:10.000Z"

    reopened = WorkflowLedger(store=WorkflowJournalStore(store.root), clock=clock)
    restored = reopened.restore()[0]
    assert restored.steps[0].state is StepState.BLOCKED
    assert reopened.release_due_delays() == ()

    clock.advance(10)
    released = reopened.release_due_delays()
    assert len(released) == 1
    assert released[0].steps[0].state is StepState.READY
    assert reopened.start_step(definition.workflow_id, step_id).steps[0].state is StepState.RUNNING


def test_timeout_is_persisted_per_attempt_and_recovery_remains_explicit(tmp_path):
    clock = AdjustableClock()
    retry = RetryPolicy(
        mode=RetryMode.FIXED,
        maximum_attempts=2,
        delay_seconds=0,
        maximum_delay_seconds=0,
    )
    definition, step_id, ledger, store = _create(
        tmp_path / "journal", clock, timeout_seconds=5, retry=retry
    )
    ledger.prepare(definition.workflow_id)
    started = ledger.start_step(definition.workflow_id, step_id)
    assert started.steps[0].attempt_started_at_utc == "2026-09-24T12:00:00.000Z"

    reopened = WorkflowLedger(store=WorkflowJournalStore(store.root), clock=clock)
    restored = reopened.restore()[0]
    assert restored.steps[0].state is StepState.BLOCKED
    assert restored.steps[0].failure_code == "SONA-WORKFLOW-RECOVERY-REQUIRED"

    # Restore does not replay the operation; an explicit retry begins a new timed attempt.
    with pytest.raises(WorkflowTransitionError, match="recovery decision"):
        reopened.start_step(definition.workflow_id, step_id)
    reopened.resume_step(
        definition.workflow_id,
        step_id,
        decision=RecoveryDecision.RETRY_FROM_START,
    )
    clock.advance(2)
    restarted = reopened.start_step(definition.workflow_id, step_id)
    assert restarted.steps[0].attempt_started_at_utc == "2026-09-24T12:00:02.000Z"


def test_active_timeout_requests_cancel_then_owner_acknowledgment_fails_step(tmp_path):
    clock = AdjustableClock()
    definition, step_id, ledger, _ = _create(tmp_path / "journal", clock, timeout_seconds=5)
    ledger.prepare(definition.workflow_id)
    ledger.start_step(definition.workflow_id, step_id)
    clock.advance(5)

    requests = ledger.expire_due_steps()
    assert len(requests) == 1
    assert requests[0].state is WorkflowState.CANCELING
    assert requests[0].steps[0].state is StepState.CANCELING
    assert requests[0].steps[0].failure_code == "SONA-WORKFLOW-TIMED-OUT"

    finished = ledger.finish_step_cancellation(definition.workflow_id, step_id)
    assert finished.state is WorkflowState.FAILED
    assert finished.steps[0].state is StepState.FAILED
    assert finished.steps[0].failure_code == "SONA-WORKFLOW-TIMED-OUT"


def test_late_success_cannot_bypass_deadline_polling(tmp_path):
    clock = AdjustableClock()
    definition, step_id, ledger, _ = _create(
        tmp_path / "journal", clock, deadline_utc="2026-09-24T12:00:05Z"
    )
    ledger.prepare(definition.workflow_id)
    ledger.start_step(definition.workflow_id, step_id)
    clock.advance(5)

    finished = ledger.succeed_step(definition.workflow_id, step_id)
    assert finished.state is WorkflowState.FAILED
    assert finished.steps[0].failure_code == "SONA-WORKFLOW-DEADLINE-MISSED"


@pytest.mark.parametrize(
    ("field", "expected_code"),
    [
        ("deadline_utc", "SONA-WORKFLOW-DEADLINE-MISSED"),
        ("expires_at_utc", "SONA-WORKFLOW-EXPIRED"),
    ],
)
def test_pending_step_deadline_or_expiration_fails_closed(tmp_path, field, expected_code):
    clock = AdjustableClock()
    definition, _step_id, ledger, _ = _create(
        tmp_path / "journal",
        clock,
        **{field: "2026-09-24T12:00:05Z"},
    )
    ledger.prepare(definition.workflow_id)
    clock.advance(5)

    with pytest.raises(WorkflowTransitionError, match="expire_due_steps"):
        ledger.start_step(definition.workflow_id, _step_id)
    expired = ledger.expire_due_steps()
    assert len(expired) == 1
    assert expired[0].state is WorkflowState.FAILED
    assert expired[0].steps[0].failure_code == expected_code


def test_retry_due_after_expiration_is_not_released(tmp_path):
    clock = AdjustableClock()
    retry = RetryPolicy(
        mode=RetryMode.FIXED,
        maximum_attempts=2,
        delay_seconds=5,
        maximum_delay_seconds=5,
    )
    definition, step_id, ledger, _ = _create(
        tmp_path / "journal",
        clock,
        retry=retry,
        expires_at_utc="2026-09-24T12:00:04Z",
    )
    ledger.prepare(definition.workflow_id)
    ledger.start_step(definition.workflow_id, step_id)
    retrying = ledger.schedule_retry(definition.workflow_id, step_id)
    assert retrying.state is WorkflowState.RETRYING
    clock.advance(5)

    expired = ledger.expire_due_steps()
    assert len(expired) == 1
    assert expired[0].state is WorkflowState.FAILED
    assert expired[0].steps[0].failure_code == "SONA-WORKFLOW-EXPIRED"
    assert ledger.release_due_retries() == ()


def test_rehashed_journal_cannot_change_a_durable_delay(tmp_path):
    clock = AdjustableClock()
    definition, _step_id, ledger, store = _create(tmp_path / "journal", clock, delay_seconds=10)
    ledger.prepare(definition.workflow_id)
    latest_event = store.root / "workflows" / str(definition.workflow_id) / "event-00000002.json"
    _rewrite_rehashed_event(
        latest_event,
        lambda event: event["snapshot"]["steps"][0].update(
            {"not_before_utc": "2026-09-24T12:00:11.000Z"}
        ),
    )

    with pytest.raises(WorkflowPersistenceError, match="not-before time is inconsistent"):
        WorkflowJournalStore(store.root).load_latest()


def test_schema3_definition_timestamps_must_be_canonical_utc(tmp_path):
    clock = AdjustableClock()
    definition, _step_id, _ledger, store = _create(
        tmp_path / "journal",
        clock,
        deadline_utc="2026-09-24T12:00:30Z",
    )
    first_event = store.root / "workflows" / str(definition.workflow_id) / "event-00000001.json"
    _rewrite_rehashed_event(
        first_event,
        lambda event: event["snapshot"]["definition"]["tasks"][0]["steps"][0].update(
            {"deadline_utc": "2026-09-24T08:00:30-04:00"}
        ),
    )

    with pytest.raises(WorkflowPersistenceError, match="not canonical UTC"):
        WorkflowJournalStore(store.root).load_latest()
