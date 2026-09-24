"""Workflow lifecycle ledger with optional durable journal (no step execution)."""

from __future__ import annotations

import re
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from threading import RLock
from typing import Protocol

from .contracts import (
    RetryMode,
    StepDefinition,
    StepId,
    StepState,
    TaskDefinition,
    TaskId,
    TaskState,
    WorkflowDefinition,
    WorkflowId,
    WorkflowState,
)

_SAFE_FAILURE_CODE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_TERMINAL_STEP_STATES = {
    StepState.SUCCEEDED,
    StepState.FAILED,
    StepState.CANCELED,
    StepState.SKIPPED,
}
_TERMINAL_WORKFLOW_STATES = {
    WorkflowState.SUCCEEDED,
    WorkflowState.FAILED,
    WorkflowState.CANCELED,
}


class WorkflowLedgerError(ValueError):
    """A workflow identity, transition, or state-ledger error."""


class UnknownWorkflow(WorkflowLedgerError):
    """The requested workflow is not present in this in-memory ledger."""


class WorkflowTransitionError(WorkflowLedgerError):
    """The requested state transition is invalid and made no state change."""


class RecoveryDecision(StrEnum):
    RETRY_FROM_START = "retry_from_start"
    MARK_FAILED = "mark_failed"


@dataclass(frozen=True, slots=True)
class WorkflowStepSnapshot:
    step_id: StepId
    task_id: TaskId
    state: StepState
    attempt_count: int
    created_at_utc: str
    started_at_utc: str | None
    finished_at_utc: str | None
    failure_code: str | None
    retry_after_utc: str | None = None


@dataclass(frozen=True, slots=True)
class WorkflowTaskSnapshot:
    task_id: TaskId
    state: TaskState
    created_at_utc: str
    started_at_utc: str | None
    finished_at_utc: str | None


@dataclass(frozen=True, slots=True)
class WorkflowProgress:
    completed_steps: int
    total_steps: int
    percent_complete: float


@dataclass(frozen=True, slots=True)
class WorkflowSnapshot:
    schema_version: int
    definition: WorkflowDefinition
    state: WorkflowState
    tasks: tuple[WorkflowTaskSnapshot, ...]
    steps: tuple[WorkflowStepSnapshot, ...]
    progress: WorkflowProgress
    created_at_utc: str
    started_at_utc: str | None
    finished_at_utc: str | None
    terminal_outcome: WorkflowState | None


class WorkflowSnapshotStore(Protocol):
    """Persistence boundary used by the ledger; storage never executes work."""

    def append(
        self,
        snapshot: WorkflowSnapshot,
        *,
        event_type: str,
        details: dict[str, str] | None = None,
    ) -> None: ...

    def load_latest(self) -> tuple[WorkflowSnapshot, ...]: ...


@dataclass(slots=True)
class _StepRecord:
    definition: StepDefinition
    task_id: TaskId
    state: StepState
    created_at_utc: str
    started_at_utc: str | None = None
    finished_at_utc: str | None = None
    attempt_count: int = 0
    failure_code: str | None = None
    retry_after_utc: str | None = None


@dataclass(slots=True)
class _TaskRecord:
    definition: TaskDefinition
    state: TaskState
    created_at_utc: str
    started_at_utc: str | None = None
    finished_at_utc: str | None = None


@dataclass(slots=True)
class _WorkflowRecord:
    definition: WorkflowDefinition
    state: WorkflowState
    created_at_utc: str
    started_at_utc: str | None
    finished_at_utc: str | None
    tasks: dict[TaskId, _TaskRecord] = field(default_factory=dict)
    steps: dict[StepId, _StepRecord] = field(default_factory=dict)
    active_step_id: StepId | None = None


class WorkflowLedger:
    """Validate lifecycle transitions; optionally persist before accepting them.

    The ledger serializes one active step per workflow. When a journal store is
    configured, each accepted state transition is committed before it is
    returned; persistence failures roll back the in-memory state. Restore is
    explicit and inert, converting interrupted active work to BLOCKED.
    """

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] | None = None,
        store: WorkflowSnapshotStore | None = None,
    ) -> None:
        self._clock = clock or (lambda: datetime.now(UTC))
        self._lock = RLock()
        self._workflows: dict[WorkflowId, _WorkflowRecord] = {}
        self._store = store

    def create(self, definition: WorkflowDefinition) -> WorkflowSnapshot:
        if not isinstance(definition, WorkflowDefinition):
            raise WorkflowLedgerError("workflow definition is invalid")
        with self._lock:
            if definition.workflow_id in self._workflows:
                raise WorkflowLedgerError("workflow id already exists in this ledger")
            now = self._timestamp()
            record = _WorkflowRecord(
                definition=definition,
                state=WorkflowState.CREATED,
                created_at_utc=now,
                started_at_utc=None,
                finished_at_utc=None,
            )
            for task in definition.tasks:
                record.tasks[task.task_id] = _TaskRecord(
                    definition=task,
                    state=TaskState.CREATED,
                    created_at_utc=now,
                )
                for step in task.steps:
                    record.steps[step.step_id] = _StepRecord(
                        definition=step,
                        task_id=task.task_id,
                        state=StepState.CREATED,
                        created_at_utc=now,
                    )
            self._workflows[definition.workflow_id] = record
            try:
                self._persist(record, "workflow.created")
            except Exception:
                del self._workflows[definition.workflow_id]
                raise
            return self._snapshot(record)

    def prepare(self, workflow_id: WorkflowId) -> WorkflowSnapshot:
        """Mark dependency-free steps READY and dependent steps BLOCKED."""
        with self._lock:
            record = self._get(workflow_id)
            if record.state is not WorkflowState.CREATED:
                raise WorkflowTransitionError("only a created workflow can be prepared")
            before = deepcopy(record)
            now = self._timestamp()
            for step in record.steps.values():
                step.state = (
                    StepState.READY if not step.definition.depends_on else StepState.BLOCKED
                )
            record.state = WorkflowState.READY
            self._refresh_tasks(record, now)
            self._commit_transition(record, before, "workflow.prepared")
            return self._snapshot(record)

    def start_step(self, workflow_id: WorkflowId, step_id: StepId) -> WorkflowSnapshot:
        """Claim one ready step; this records intent but does not run its operation."""
        with self._lock:
            record = self._get(workflow_id)
            before = deepcopy(record)
            step = self._get_step(record, step_id)
            if record.state is not WorkflowState.READY or record.active_step_id is not None:
                raise WorkflowTransitionError("workflow is not available to start a step")
            if step.state is not StepState.READY:
                raise WorkflowTransitionError("only a ready step can be started")
            if step.attempt_count >= step.definition.retry.maximum_attempts:
                raise WorkflowTransitionError("step exhausted its declared maximum attempts")
            now = self._timestamp()
            step.state = StepState.RUNNING
            step.attempt_count += 1
            step.started_at_utc = step.started_at_utc or now
            step.retry_after_utc = None
            record.active_step_id = step_id
            record.state = WorkflowState.RUNNING
            record.started_at_utc = record.started_at_utc or now
            self._refresh_tasks(record, now)
            self._commit_transition(record, before, "step.started")
            return self._snapshot(record)

    def succeed_step(self, workflow_id: WorkflowId, step_id: StepId) -> WorkflowSnapshot:
        with self._lock:
            record = self._get(workflow_id)
            before = deepcopy(record)
            step = self._require_active_step(record, step_id)
            now = self._timestamp()
            step.state = StepState.SUCCEEDED
            step.finished_at_utc = now
            record.active_step_id = None
            for dependent in record.steps.values():
                if dependent.state is StepState.BLOCKED and all(
                    record.steps[dependency].state is StepState.SUCCEEDED
                    for dependency in dependent.definition.depends_on
                ):
                    dependent.state = StepState.READY
            self._derive_workflow_state(record, now)
            self._commit_transition(record, before, "step.succeeded")
            return self._snapshot(record)

    def fail_step(
        self,
        workflow_id: WorkflowId,
        step_id: StepId,
        *,
        failure_code: str = "SONA-WORKFLOW-STEP-FAILED",
    ) -> WorkflowSnapshot:
        """Fail the workflow with a stable code; raw exception text is not stored."""
        if not isinstance(failure_code, str) or not _SAFE_FAILURE_CODE.fullmatch(failure_code):
            raise WorkflowLedgerError("failure_code must be a safe diagnostic identifier")
        with self._lock:
            record = self._get(workflow_id)
            before = deepcopy(record)
            step = self._require_active_step(record, step_id)
            now = self._timestamp()
            self._mark_failed(record, step, failure_code, now)
            self._commit_transition(record, before, "step.failed")
            return self._snapshot(record)

    def schedule_retry(
        self,
        workflow_id: WorkflowId,
        step_id: StepId,
        *,
        failure_code: str = "SONA-WORKFLOW-STEP-RETRYABLE",
    ) -> WorkflowSnapshot:
        """Schedule one bounded retry; due work is released only by an explicit poll."""
        if not isinstance(failure_code, str) or not _SAFE_FAILURE_CODE.fullmatch(failure_code):
            raise WorkflowLedgerError("failure_code must be a safe diagnostic identifier")
        with self._lock:
            record = self._get(workflow_id)
            before = deepcopy(record)
            step = self._require_active_step(record, step_id)
            policy = step.definition.retry
            if policy.mode is RetryMode.NONE or step.attempt_count >= policy.maximum_attempts:
                self._mark_failed(record, step, failure_code, self._timestamp())
                self._commit_transition(record, before, "step.failed")
                return self._snapshot(record)

            now = self._timestamp()
            current = datetime.fromisoformat(now.replace("Z", "+00:00"))
            delay = self._retry_delay(
                policy.mode, policy.delay_seconds, policy.maximum_delay_seconds, step.attempt_count
            )
            try:
                retry_after = (current + timedelta(seconds=delay)).astimezone(UTC)
            except OverflowError as exc:
                raise WorkflowLedgerError(
                    "retry delay exceeds the supported timestamp range"
                ) from exc
            step.state = StepState.RETRYING
            step.failure_code = failure_code
            step.finished_at_utc = None
            step.retry_after_utc = retry_after.isoformat(timespec="milliseconds").replace(
                "+00:00", "Z"
            )
            record.active_step_id = None
            record.state = WorkflowState.RETRYING
            self._refresh_tasks(record, now)
            self._commit_transition(record, before, "step.retrying")
            return self._snapshot(record)

    def release_due_retries(self) -> tuple[WorkflowSnapshot, ...]:
        """Release only retries whose durable retry-after timestamp has passed."""
        with self._lock:
            now = self._timestamp()
            now_value = datetime.fromisoformat(now.replace("Z", "+00:00"))
            released: list[WorkflowSnapshot] = []
            for record in self._workflows.values():
                retrying = [
                    step for step in record.steps.values() if step.state is StepState.RETRYING
                ]
                for step in retrying:
                    if step.retry_after_utc is None:
                        raise WorkflowLedgerError("retrying step has no durable retry-after time")
                    due = datetime.fromisoformat(step.retry_after_utc.replace("Z", "+00:00"))
                    if due > now_value:
                        continue
                    before = deepcopy(record)
                    step.state = StepState.READY
                    step.retry_after_utc = None
                    step.failure_code = None
                    record.state = WorkflowState.READY
                    self._refresh_tasks(record, now)
                    self._commit_transition(record, before, "step.retry_ready")
                    released.append(self._snapshot(record))
            return tuple(released)

    def block_step(
        self,
        workflow_id: WorkflowId,
        step_id: StepId,
        *,
        failure_code: str | None = None,
    ) -> WorkflowSnapshot:
        """Record an external/policy block on a ready step without running it."""
        if failure_code is not None and (
            not isinstance(failure_code, str) or not _SAFE_FAILURE_CODE.fullmatch(failure_code)
        ):
            raise WorkflowLedgerError("failure_code must be a safe diagnostic identifier")
        with self._lock:
            record = self._get(workflow_id)
            before = deepcopy(record)
            step = self._get_step(record, step_id)
            if record.state is not WorkflowState.READY or step.state is not StepState.READY:
                raise WorkflowTransitionError("only a ready step can be blocked")
            now = self._timestamp()
            step.state = StepState.BLOCKED
            step.failure_code = failure_code
            self._derive_workflow_state(record, now)
            self._commit_transition(record, before, "step.blocked")
            return self._snapshot(record)

    def unblock_step(self, workflow_id: WorkflowId, step_id: StepId) -> WorkflowSnapshot:
        with self._lock:
            record = self._get(workflow_id)
            before = deepcopy(record)
            step = self._get_step(record, step_id)
            if record.state not in (WorkflowState.READY, WorkflowState.BLOCKED):
                raise WorkflowTransitionError("workflow cannot release a blocked step")
            if step.state is not StepState.BLOCKED:
                raise WorkflowTransitionError("only a blocked step can be released")
            if step.failure_code == "SONA-WORKFLOW-RECOVERY-REQUIRED":
                raise WorkflowTransitionError(
                    "interrupted work requires an explicit resume decision"
                )
            if not all(
                record.steps[dependency].state is StepState.SUCCEEDED
                for dependency in step.definition.depends_on
            ):
                raise WorkflowTransitionError("step dependencies are not complete")
            now = self._timestamp()
            step.state = StepState.READY
            step.failure_code = None
            self._derive_workflow_state(record, now)
            self._commit_transition(record, before, "step.unblocked")
            return self._snapshot(record)

    def resume_step(
        self,
        workflow_id: WorkflowId,
        step_id: StepId,
        *,
        decision: RecoveryDecision,
    ) -> WorkflowSnapshot:
        """Explicitly retry interrupted work from its beginning or mark it failed."""
        if not isinstance(decision, RecoveryDecision):
            raise WorkflowLedgerError("recovery decision is unsupported")
        with self._lock:
            record = self._get(workflow_id)
            before = deepcopy(record)
            step = self._get_step(record, step_id)
            if (
                record.state is not WorkflowState.BLOCKED
                or step.state is not StepState.BLOCKED
                or step.failure_code != "SONA-WORKFLOW-RECOVERY-REQUIRED"
            ):
                raise WorkflowTransitionError("step is not awaiting an interrupted-work decision")
            now = self._timestamp()
            if decision is RecoveryDecision.RETRY_FROM_START:
                if step.attempt_count >= step.definition.retry.maximum_attempts:
                    raise WorkflowTransitionError("step has no remaining configured retry attempts")
                if not all(
                    record.steps[dependency].state is StepState.SUCCEEDED
                    for dependency in step.definition.depends_on
                ):
                    raise WorkflowTransitionError("step dependencies are not complete")
                step.state = StepState.READY
                step.failure_code = None
                step.retry_after_utc = None
                record.state = WorkflowState.READY
                self._refresh_tasks(record, now)
                event_type = "workflow.recovery_resumed"
            else:
                self._mark_failed(
                    record,
                    step,
                    "SONA-WORKFLOW-RECOVERY-REJECTED",
                    now,
                )
                event_type = "workflow.recovery_failed"
            self._commit_transition(
                record,
                before,
                event_type,
                details={"recovery_decision": decision.value},
            )
            return self._snapshot(record)

    def cancel(self, workflow_id: WorkflowId) -> WorkflowSnapshot:
        """Request cancellation; an active step must acknowledge it separately."""
        with self._lock:
            record = self._get(workflow_id)
            if record.state in _TERMINAL_WORKFLOW_STATES or record.state is WorkflowState.CANCELING:
                raise WorkflowTransitionError("workflow cannot transition to canceling")
            if any(
                step.failure_code == "SONA-WORKFLOW-RECOVERY-REQUIRED"
                for step in record.steps.values()
            ):
                raise WorkflowTransitionError(
                    "interrupted work requires an explicit recovery decision before cancellation"
                )
            before = deepcopy(record)
            now = self._timestamp()
            active = record.steps.get(record.active_step_id) if record.active_step_id else None
            for step in record.steps.values():
                if step is active:
                    step.state = StepState.CANCELING
                    step.retry_after_utc = None
                    continue
                if step.state not in _TERMINAL_STEP_STATES:
                    step.state = StepState.CANCELED
                    step.finished_at_utc = now
                    step.retry_after_utc = None
            if active is None:
                record.state = WorkflowState.CANCELED
                record.finished_at_utc = now
            else:
                record.state = WorkflowState.CANCELING
            self._refresh_tasks(record, now)
            self._commit_transition(record, before, "workflow.cancel_requested")
            return self._snapshot(record)

    def finish_step_cancellation(
        self, workflow_id: WorkflowId, step_id: StepId
    ) -> WorkflowSnapshot:
        with self._lock:
            record = self._get(workflow_id)
            before = deepcopy(record)
            step = self._get_step(record, step_id)
            if (
                record.state is not WorkflowState.CANCELING
                or record.active_step_id != step_id
                or step.state is not StepState.CANCELING
            ):
                raise WorkflowTransitionError("step has no pending cancellation to finish")
            now = self._timestamp()
            step.state = StepState.CANCELED
            step.finished_at_utc = now
            record.active_step_id = None
            record.state = WorkflowState.CANCELED
            record.finished_at_utc = now
            self._refresh_tasks(record, now)
            self._commit_transition(record, before, "step.cancellation_finished")
            return self._snapshot(record)

    def snapshot(self, workflow_id: WorkflowId) -> WorkflowSnapshot:
        with self._lock:
            return self._snapshot(self._get(workflow_id))

    def restore(self) -> tuple[WorkflowSnapshot, ...]:
        """Load persisted state inertly; interrupted active steps become BLOCKED.

        No operation is invoked. A step that was RUNNING or CANCELING at the
        last durable journal point becomes recovery-required and must be
        explicitly released before a new attempt can start.
        """
        if self._store is None:
            raise WorkflowLedgerError("workflow ledger has no persistence store")
        with self._lock:
            if self._workflows:
                raise WorkflowLedgerError("restore requires an empty workflow ledger")
            snapshots = self._store.load_latest()
            records = [self._record_from_snapshot(item) for item in snapshots]
            if len({item.definition.workflow_id for item in records}) != len(records):
                raise WorkflowLedgerError("persistence store returned duplicate workflow IDs")
            recovered: list[WorkflowSnapshot] = []
            for record in records:
                active = next(
                    (
                        step
                        for step in record.steps.values()
                        if step.state in {StepState.RUNNING, StepState.CANCELING}
                    ),
                    None,
                )
                if active is not None:
                    before = deepcopy(record)
                    active.state = StepState.BLOCKED
                    active.failure_code = "SONA-WORKFLOW-RECOVERY-REQUIRED"
                    record.active_step_id = None
                    record.state = WorkflowState.BLOCKED
                    record.finished_at_utc = None
                    self._refresh_tasks(record, active.created_at_utc)
                    self._persist(record, "workflow.recovery_required")
                    if record.state is not WorkflowState.BLOCKED:
                        record = before
                        raise WorkflowLedgerError("interrupted workflow recovery state is invalid")
                recovered.append(self._snapshot(record))
            self._workflows = {item.definition.workflow_id: item for item in records}
            return tuple(recovered)

    def _persist(
        self,
        record: _WorkflowRecord,
        event_type: str,
        *,
        details: dict[str, str] | None = None,
    ) -> None:
        if self._store is not None:
            if details is None:
                self._store.append(self._snapshot(record), event_type=event_type)
            else:
                self._store.append(self._snapshot(record), event_type=event_type, details=details)

    def _commit_transition(
        self,
        record: _WorkflowRecord,
        before: _WorkflowRecord,
        event_type: str,
        *,
        details: dict[str, str] | None = None,
    ) -> None:
        try:
            self._persist(record, event_type, details=details)
        except Exception:
            self._workflows[record.definition.workflow_id] = before
            raise

    @staticmethod
    def _record_from_snapshot(snapshot: WorkflowSnapshot) -> _WorkflowRecord:
        if snapshot.schema_version not in {1, 2} or not isinstance(
            snapshot.definition, WorkflowDefinition
        ):
            raise WorkflowLedgerError("persisted workflow snapshot is unsupported")
        tasks = {item.task_id: item for item in snapshot.tasks}
        steps = {item.step_id: item for item in snapshot.steps}
        record = _WorkflowRecord(
            definition=snapshot.definition,
            state=snapshot.state,
            created_at_utc=snapshot.created_at_utc,
            started_at_utc=snapshot.started_at_utc,
            finished_at_utc=snapshot.finished_at_utc,
        )
        for task in snapshot.definition.tasks:
            task_snapshot = tasks.get(task.task_id)
            if task_snapshot is None:
                raise WorkflowLedgerError("persisted workflow task is missing")
            record.tasks[task.task_id] = _TaskRecord(
                definition=task,
                state=task_snapshot.state,
                created_at_utc=task_snapshot.created_at_utc,
                started_at_utc=task_snapshot.started_at_utc,
                finished_at_utc=task_snapshot.finished_at_utc,
            )
            for definition in task.steps:
                item = steps.get(definition.step_id)
                if item is None or item.task_id != task.task_id:
                    raise WorkflowLedgerError("persisted workflow step identity is invalid")
                record.steps[definition.step_id] = _StepRecord(
                    definition=definition,
                    task_id=task.task_id,
                    state=item.state,
                    created_at_utc=item.created_at_utc,
                    started_at_utc=item.started_at_utc,
                    finished_at_utc=item.finished_at_utc,
                    attempt_count=item.attempt_count,
                    failure_code=item.failure_code,
                    retry_after_utc=item.retry_after_utc,
                )
        active_steps = [
            item
            for item in record.steps.values()
            if item.state in {StepState.RUNNING, StepState.CANCELING}
        ]
        if len(active_steps) > 1:
            raise WorkflowLedgerError("persisted workflow has multiple active steps")
        record.active_step_id = active_steps[0].definition.step_id if active_steps else None
        return record

    @staticmethod
    def _retry_delay(mode: RetryMode, base: float, maximum: float, attempt: int) -> float:
        if mode is RetryMode.FIXED:
            return min(base, maximum)
        if mode is RetryMode.EXPONENTIAL:
            delay = min(base, maximum)
            for _ in range(max(0, attempt - 1)):
                if delay == 0:
                    return 0.0
                if delay >= maximum / 2:
                    return maximum
                delay *= 2
            return min(delay, maximum)
        return 0.0

    def _mark_failed(
        self,
        record: _WorkflowRecord,
        step: _StepRecord,
        failure_code: str,
        now: str,
    ) -> None:
        step.state = StepState.FAILED
        step.failure_code = failure_code
        step.finished_at_utc = now
        step.retry_after_utc = None
        record.active_step_id = None
        for pending in record.steps.values():
            if pending.state in (StepState.CREATED, StepState.READY, StepState.BLOCKED):
                pending.state = StepState.SKIPPED
                pending.finished_at_utc = now
                pending.retry_after_utc = None
        record.state = WorkflowState.FAILED
        record.finished_at_utc = now
        self._refresh_tasks(record, now)

    def _derive_workflow_state(self, record: _WorkflowRecord, now: str) -> None:
        states = tuple(step.state for step in record.steps.values())
        if all(state is StepState.SUCCEEDED for state in states):
            record.state = WorkflowState.SUCCEEDED
            record.finished_at_utc = now
        elif any(state is StepState.RUNNING for state in states):
            record.state = WorkflowState.RUNNING
        elif any(state is StepState.RETRYING for state in states):
            record.state = WorkflowState.RETRYING
        elif any(state is StepState.READY for state in states):
            record.state = WorkflowState.READY
        elif any(state in (StepState.BLOCKED, StepState.CREATED) for state in states):
            record.state = WorkflowState.BLOCKED
        self._refresh_tasks(record, now)

    def _refresh_tasks(self, record: _WorkflowRecord, now: str) -> None:
        for task in record.tasks.values():
            states = tuple(record.steps[item.step_id].state for item in task.definition.steps)
            if all(state is StepState.CREATED for state in states):
                task.state = TaskState.CREATED
            elif any(state is StepState.CANCELING for state in states):
                task.state = TaskState.CANCELING
            elif any(state is StepState.RUNNING for state in states):
                task.state = TaskState.RUNNING
            elif any(state is StepState.RETRYING for state in states):
                task.state = TaskState.RETRYING
            elif any(state in (StepState.FAILED, StepState.SKIPPED) for state in states):
                task.state = TaskState.FAILED
            elif all(state in _TERMINAL_STEP_STATES for state in states):
                task.state = (
                    TaskState.CANCELED
                    if any(state is StepState.CANCELED for state in states)
                    else TaskState.SUCCEEDED
                )
            elif any(state is StepState.READY for state in states):
                task.state = TaskState.READY
            else:
                task.state = TaskState.BLOCKED
            task_started = [
                record.steps[item.step_id].started_at_utc
                for item in task.definition.steps
                if record.steps[item.step_id].started_at_utc is not None
            ]
            if task_started:
                task.started_at_utc = min(task_started)
            if task.state in {
                TaskState.SUCCEEDED,
                TaskState.FAILED,
                TaskState.CANCELED,
            }:
                task.finished_at_utc = task.finished_at_utc or now

    def _snapshot(self, record: _WorkflowRecord) -> WorkflowSnapshot:
        steps = tuple(
            WorkflowStepSnapshot(
                step_id=item.step_id,
                task_id=record.steps[item.step_id].task_id,
                state=record.steps[item.step_id].state,
                attempt_count=record.steps[item.step_id].attempt_count,
                created_at_utc=record.steps[item.step_id].created_at_utc,
                started_at_utc=record.steps[item.step_id].started_at_utc,
                finished_at_utc=record.steps[item.step_id].finished_at_utc,
                failure_code=record.steps[item.step_id].failure_code,
                retry_after_utc=record.steps[item.step_id].retry_after_utc,
            )
            for task in record.definition.tasks
            for item in task.steps
        )
        tasks = tuple(
            WorkflowTaskSnapshot(
                task_id=item.task_id,
                state=record.tasks[item.task_id].state,
                created_at_utc=record.tasks[item.task_id].created_at_utc,
                started_at_utc=record.tasks[item.task_id].started_at_utc,
                finished_at_utc=record.tasks[item.task_id].finished_at_utc,
            )
            for item in record.definition.tasks
        )
        completed = sum(item.state in _TERMINAL_STEP_STATES for item in steps)
        total = len(steps)
        return WorkflowSnapshot(
            schema_version=2,
            definition=record.definition,
            state=record.state,
            tasks=tasks,
            steps=steps,
            progress=WorkflowProgress(
                completed_steps=completed,
                total_steps=total,
                percent_complete=round(completed * 100.0 / total, 2),
            ),
            created_at_utc=record.created_at_utc,
            started_at_utc=record.started_at_utc,
            finished_at_utc=record.finished_at_utc,
            terminal_outcome=(record.state if record.state in _TERMINAL_WORKFLOW_STATES else None),
        )

    def _get(self, workflow_id: WorkflowId) -> _WorkflowRecord:
        try:
            return self._workflows[workflow_id]
        except KeyError as exc:
            raise UnknownWorkflow("workflow is unknown to this in-memory ledger") from exc

    @staticmethod
    def _get_step(record: _WorkflowRecord, step_id: StepId) -> _StepRecord:
        try:
            return record.steps[step_id]
        except KeyError as exc:
            raise WorkflowLedgerError("step is not part of this workflow") from exc

    def _require_active_step(self, record: _WorkflowRecord, step_id: StepId) -> _StepRecord:
        step = self._get_step(record, step_id)
        if (
            record.state is not WorkflowState.RUNNING
            or record.active_step_id != step_id
            or step.state is not StepState.RUNNING
        ):
            raise WorkflowTransitionError("step is not the active running step")
        return step

    def _timestamp(self) -> str:
        current = self._clock()
        if current.tzinfo is None or current.utcoffset() is None:
            raise WorkflowLedgerError("workflow clock must return a timezone-aware datetime")
        return current.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
