"""Canonical, bounded workflow journal and atomic snapshot storage."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import threading
import uuid
import warnings
from contextlib import suppress
from pathlib import Path
from typing import Any

from .contracts import (
    RetryMode,
    RetryPolicy,
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
from .ledger import (
    WorkflowLedgerError,
    WorkflowProgress,
    WorkflowSnapshot,
    WorkflowStepSnapshot,
    WorkflowTaskSnapshot,
)

_EVENT_NAME = re.compile(r"^event-(\d{8})\.json$")
_TEMP_NAME = re.compile(r"^\.(?:event-\d{8}\.json|snapshot\.json)\.[^.]+\.tmp$")
_SAFE_OPERATION = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_SAFE_FAILURE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_EVENT_TYPES = {
    "workflow.created",
    "workflow.prepared",
    "step.started",
    "step.succeeded",
    "step.failed",
    "step.blocked",
    "step.unblocked",
    "workflow.cancel_requested",
    "step.cancellation_finished",
    "workflow.recovery_required",
    "step.retrying",
    "step.retry_ready",
    "workflow.recovery_resumed",
    "workflow.recovery_failed",
}
_EVENT_TYPES_V1 = _EVENT_TYPES - {
    "step.retrying",
    "step.retry_ready",
    "workflow.recovery_resumed",
    "workflow.recovery_failed",
}
_ROOT_LOCKS: dict[str, threading.RLock] = {}
_ROOT_LOCKS_GUARD = threading.Lock()


class WorkflowPersistenceError(WorkflowLedgerError):
    """Persisted workflow bytes are unavailable, corrupt, or exceed limits."""


class WorkflowJournalStore:
    """Append hash-chained canonical records and maintain a derived snapshot.

    Journal records are individually staged, flushed, and atomically renamed.
    The append-only journal is authoritative; ``snapshot.json`` is a validated
    convenience copy and is rebuilt from the journal when missing or stale.
    This implementation supports one writer object per store root at a time.
    It does not execute or authorize workflow operations.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        maximum_workflows: int = 1000,
        maximum_events_per_workflow: int = 10000,
        maximum_record_bytes: int = 1_048_576,
        maximum_total_bytes: int = 67_108_864,
    ) -> None:
        self.root = Path(root)
        limits = (
            maximum_workflows,
            maximum_events_per_workflow,
            maximum_record_bytes,
            maximum_total_bytes,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in limits
        ):
            raise WorkflowPersistenceError("workflow persistence limits must be positive integers")
        if maximum_record_bytes > maximum_total_bytes:
            raise WorkflowPersistenceError("record limit cannot exceed total journal limit")
        self.maximum_workflows = maximum_workflows
        self.maximum_events_per_workflow = maximum_events_per_workflow
        self.maximum_record_bytes = maximum_record_bytes
        self.maximum_total_bytes = maximum_total_bytes
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink() or not self.root.is_dir():
            raise WorkflowPersistenceError("workflow journal root must be a real directory")
        self.root = self.root.resolve(strict=True)
        with _ROOT_LOCKS_GUARD:
            self._lock = _ROOT_LOCKS.setdefault(str(self.root).casefold(), threading.RLock())
        self._workflows_root = self.root / "workflows"
        if self._workflows_root.exists() and self._workflows_root.is_symlink():
            raise WorkflowPersistenceError("workflow journal directory cannot be a symlink")
        self._workflows_root.mkdir(exist_ok=True)
        self._validate_tree()

    def append(
        self,
        snapshot: WorkflowSnapshot,
        *,
        event_type: str,
        details: dict[str, str] | None = None,
    ) -> None:
        if event_type not in _EVENT_TYPES:
            raise WorkflowPersistenceError("workflow journal event type is unsupported")
        if details is None:
            details = {}
        _validate_event_details(event_type, details)
        _validate_snapshot(snapshot)
        workflow_id = str(snapshot.definition.workflow_id)
        with self._lock:
            self._validate_tree()
            directory = self._workflow_dir(workflow_id)
            if (
                not directory.exists()
                and len(self._workflow_directories()) >= self.maximum_workflows
            ):
                raise WorkflowPersistenceError("workflow count limit reached")
            if directory.exists():
                if directory.is_symlink():
                    raise WorkflowPersistenceError("workflow journal entry cannot be a symlink")
                existing = self._read_events(directory)
            else:
                existing = []
            if existing:
                prior = existing[-1]
                sequence = prior["sequence"] + 1
                previous_hash = prior["event_hash"]
            else:
                sequence = 1
                previous_hash = None
            if sequence > self.maximum_events_per_workflow:
                raise WorkflowPersistenceError("workflow journal event limit reached")
            event: dict[str, Any] = {
                "event_schema": 2,
                "event_id": str(uuid.uuid4()),
                "event_type": event_type,
                "sequence": sequence,
                "workflow_id": workflow_id,
                "previous_hash": previous_hash,
                "snapshot": _snapshot_to_dict(snapshot),
                "details": details,
            }
            event["event_hash"] = _hash_event(event)
            data = _canonical_json(event)
            if len(data) > self.maximum_record_bytes:
                raise WorkflowPersistenceError("workflow journal record exceeds its byte limit")
            if self._tree_size() + len(data) > self.maximum_total_bytes:
                raise WorkflowPersistenceError("workflow journal total byte limit reached")
            directory.mkdir(exist_ok=True)
            if directory.is_symlink():
                raise WorkflowPersistenceError("workflow journal entry cannot be a symlink")
            destination = directory / f"event-{sequence:08d}.json"
            if destination.exists() or destination.is_symlink():
                raise WorkflowPersistenceError("workflow journal sequence already exists")
            try:
                _atomic_publish_new(destination, data)
            except Exception:
                if sequence == 1:
                    with suppress(OSError):
                        directory.rmdir()
                raise
            try:
                _atomic_replace(directory / "snapshot.json", data)
            except OSError:
                warnings.warn(
                    "Workflow journal event is durable; its derived snapshot will be rebuilt.",
                    RuntimeWarning,
                    stacklevel=2,
                )

    def load_latest(self) -> tuple[WorkflowSnapshot, ...]:
        """Validate all journals and return their latest inert state snapshots."""
        with self._lock:
            self._validate_tree()
            latest: list[WorkflowSnapshot] = []
            for directory in self._workflow_directories():
                events = self._read_events(directory)
                if not events:
                    # A process may have stopped after creating a workflow
                    # directory or staging an uncommitted temporary record.
                    # No published event means no durable workflow exists.
                    continue
                latest.append(_snapshot_from_dict(events[-1]["snapshot"]))
                self._repair_snapshot(directory, events[-1])
            return tuple(sorted(latest, key=lambda item: str(item.definition.workflow_id)))

    def _read_events(self, directory: Path) -> list[dict[str, Any]]:
        if directory.is_symlink() or not directory.is_dir():
            raise WorkflowPersistenceError("workflow journal entry is not a real directory")
        paths: list[tuple[int, Path]] = []
        for path in directory.iterdir():
            match = _EVENT_NAME.fullmatch(path.name)
            if match:
                if path.is_symlink() or not path.is_file():
                    raise WorkflowPersistenceError("workflow journal record is not a regular file")
                paths.append((int(match.group(1)), path))
            elif path.name == "snapshot.json" or _TEMP_NAME.fullmatch(path.name):
                if path.is_symlink() or not path.is_file():
                    raise WorkflowPersistenceError("workflow journal auxiliary file is invalid")
            else:
                raise WorkflowPersistenceError("workflow journal contains an unknown file")
        paths.sort()
        events: list[dict[str, Any]] = []
        previous_hash: str | None = None
        for expected_sequence, (sequence, path) in enumerate(paths, start=1):
            if sequence != expected_sequence:
                raise WorkflowPersistenceError("workflow journal sequence has a gap")
            if sequence > self.maximum_events_per_workflow:
                raise WorkflowPersistenceError("workflow journal event limit exceeded")
            try:
                raw = path.read_bytes()
            except OSError as exc:
                raise WorkflowPersistenceError("workflow journal record cannot be read") from exc
            if len(raw) > self.maximum_record_bytes:
                raise WorkflowPersistenceError("workflow journal record exceeds its byte limit")
            event = _parse_canonical_object(raw)
            required_v1 = {
                "event_schema",
                "event_id",
                "event_type",
                "sequence",
                "workflow_id",
                "previous_hash",
                "snapshot",
                "event_hash",
            }
            required = required_v1 | {"details"} if event.get("event_schema") == 2 else required_v1
            if set(event) != required:
                raise WorkflowPersistenceError("workflow journal record fields are invalid")
            if event["event_schema"] not in {1, 2} or event["sequence"] != sequence:
                raise WorkflowPersistenceError("workflow journal schema or sequence is invalid")
            if event["event_type"] not in _EVENT_TYPES:
                raise WorkflowPersistenceError("workflow journal event type is invalid")
            if event["event_schema"] == 1 and event["event_type"] not in _EVENT_TYPES_V1:
                raise WorkflowPersistenceError("workflow event requires a newer journal schema")
            if event["event_schema"] == 2:
                _validate_event_details(event["event_type"], event["details"])
            if event["previous_hash"] != previous_hash or event["event_hash"] != _hash_event(event):
                raise WorkflowPersistenceError("workflow journal hash chain is invalid")
            try:
                uuid.UUID(event["event_id"])
                uuid.UUID(event["workflow_id"])
            except (ValueError, TypeError, AttributeError) as exc:
                raise WorkflowPersistenceError("workflow journal identity is invalid") from exc
            snapshot = _snapshot_from_dict(event["snapshot"])
            if (
                str(snapshot.definition.workflow_id) != event["workflow_id"]
                or directory.name != event["workflow_id"]
            ):
                raise WorkflowPersistenceError("workflow journal identity does not match snapshot")
            expected_states = {
                "workflow.created": {WorkflowState.CREATED},
                "workflow.prepared": {WorkflowState.READY},
                "step.started": {WorkflowState.RUNNING},
                "step.succeeded": {WorkflowState.READY, WorkflowState.SUCCEEDED},
                "step.failed": {WorkflowState.FAILED},
                "step.blocked": {WorkflowState.BLOCKED},
                "step.unblocked": {WorkflowState.READY},
                "workflow.cancel_requested": {WorkflowState.CANCELING, WorkflowState.CANCELED},
                "step.cancellation_finished": {WorkflowState.CANCELED},
                "workflow.recovery_required": {WorkflowState.BLOCKED},
                "step.retrying": {WorkflowState.RETRYING},
                "step.retry_ready": {WorkflowState.READY},
                "workflow.recovery_resumed": {WorkflowState.READY},
                "workflow.recovery_failed": {WorkflowState.FAILED},
            }
            if snapshot.state not in expected_states[event["event_type"]]:
                raise WorkflowPersistenceError("workflow event type does not match its snapshot")
            if sequence == 1 and event["event_type"] != "workflow.created":
                raise WorkflowPersistenceError("workflow journal must begin with creation")
            previous_hash = event["event_hash"]
            events.append(event)
        return events

    def _repair_snapshot(self, directory: Path, event: dict[str, Any]) -> None:
        snapshot_path = directory / "snapshot.json"
        if snapshot_path.is_symlink():
            raise WorkflowPersistenceError("workflow snapshot cannot be a symlink")
        try:
            current = snapshot_path.read_bytes()
            if current == _canonical_json(event):
                return
        except FileNotFoundError:
            pass
        try:
            _atomic_replace(snapshot_path, _canonical_json(event))
        except OSError as exc:
            raise WorkflowPersistenceError("workflow snapshot could not be rebuilt") from exc

    def _workflow_dir(self, workflow_id: str) -> Path:
        try:
            normalized = str(uuid.UUID(workflow_id))
        except (ValueError, TypeError, AttributeError) as exc:
            raise WorkflowPersistenceError("workflow ID is invalid") from exc
        return self._workflows_root / normalized

    def _workflow_directories(self) -> list[Path]:
        result: list[Path] = []
        for path in self._workflows_root.iterdir():
            if path.is_symlink() or not path.is_dir():
                raise WorkflowPersistenceError("unexpected item in workflow journal directory")
            try:
                uuid.UUID(path.name)
            except ValueError as exc:
                raise WorkflowPersistenceError(
                    "workflow journal directory name is invalid"
                ) from exc
            result.append(path)
        return result

    def _tree_size(self) -> int:
        total = 0
        for directory in self._workflow_directories():
            for path in directory.iterdir():
                if path.is_symlink() or not path.is_file():
                    raise WorkflowPersistenceError("unexpected workflow persistence entry")
                total += path.stat().st_size
                if total > self.maximum_total_bytes:
                    raise WorkflowPersistenceError("workflow journal total byte limit exceeded")
        return total

    def _validate_tree(self) -> None:
        directories = self._workflow_directories()
        if len(directories) > self.maximum_workflows:
            raise WorkflowPersistenceError("workflow count limit exceeded")
        self._tree_size()


def _snapshot_to_dict(snapshot: WorkflowSnapshot) -> dict[str, Any]:
    return {
        "schema_version": snapshot.schema_version,
        "definition": {
            "workflow_id": str(snapshot.definition.workflow_id),
            "schema_version": snapshot.definition.schema_version,
            "tasks": [
                {
                    "task_id": str(task.task_id),
                    "schema_version": task.schema_version,
                    "steps": [
                        {
                            "step_id": str(step.step_id),
                            "operation": step.operation,
                            "depends_on": [str(item) for item in step.depends_on],
                            "retry": {
                                "mode": step.retry.mode.value,
                                "maximum_attempts": step.retry.maximum_attempts,
                                "delay_seconds": step.retry.delay_seconds,
                                "maximum_delay_seconds": step.retry.maximum_delay_seconds,
                            },
                            "timeout_seconds": step.timeout_seconds,
                        }
                        for step in task.steps
                    ],
                }
                for task in snapshot.definition.tasks
            ],
        },
        "state": snapshot.state.value,
        "tasks": [
            {
                "task_id": str(item.task_id),
                "state": item.state.value,
                "created_at_utc": item.created_at_utc,
                "started_at_utc": item.started_at_utc,
                "finished_at_utc": item.finished_at_utc,
            }
            for item in snapshot.tasks
        ],
        "steps": [
            {
                "step_id": str(item.step_id),
                "task_id": str(item.task_id),
                "state": item.state.value,
                "attempt_count": item.attempt_count,
                "created_at_utc": item.created_at_utc,
                "started_at_utc": item.started_at_utc,
                "finished_at_utc": item.finished_at_utc,
                "failure_code": item.failure_code,
                **(
                    {"retry_after_utc": item.retry_after_utc}
                    if snapshot.schema_version >= 2
                    else {}
                ),
            }
            for item in snapshot.steps
        ],
        "progress": {
            "completed_steps": snapshot.progress.completed_steps,
            "total_steps": snapshot.progress.total_steps,
            "percent_complete": snapshot.progress.percent_complete,
        },
        "created_at_utc": snapshot.created_at_utc,
        "started_at_utc": snapshot.started_at_utc,
        "finished_at_utc": snapshot.finished_at_utc,
        "terminal_outcome": snapshot.terminal_outcome.value if snapshot.terminal_outcome else None,
    }


def _snapshot_from_dict(value: Any) -> WorkflowSnapshot:
    if not isinstance(value, dict):
        raise WorkflowPersistenceError("workflow snapshot must be an object")
    required = {
        "schema_version",
        "definition",
        "state",
        "tasks",
        "steps",
        "progress",
        "created_at_utc",
        "started_at_utc",
        "finished_at_utc",
        "terminal_outcome",
    }
    if set(value) != required or value["schema_version"] not in {1, 2}:
        raise WorkflowPersistenceError("workflow snapshot schema or fields are invalid")
    try:
        definition_value = value["definition"]
        if set(definition_value) != {"workflow_id", "schema_version", "tasks"}:
            raise ValueError("definition fields")
        tasks = []
        for task_value in definition_value["tasks"]:
            if set(task_value) != {"task_id", "schema_version", "steps"}:
                raise ValueError("task definition fields")
            steps = []
            for step_value in task_value["steps"]:
                if set(step_value) != {
                    "step_id",
                    "operation",
                    "depends_on",
                    "retry",
                    "timeout_seconds",
                }:
                    raise ValueError("step definition fields")
                retry_value = step_value["retry"]
                if set(retry_value) != {
                    "mode",
                    "maximum_attempts",
                    "delay_seconds",
                    "maximum_delay_seconds",
                }:
                    raise ValueError("retry policy fields")
                steps.append(
                    StepDefinition(
                        step_id=StepId(step_value["step_id"]),
                        operation=step_value["operation"],
                        depends_on=tuple(StepId(item) for item in step_value["depends_on"]),
                        retry=RetryPolicy(
                            mode=RetryMode(retry_value["mode"]),
                            maximum_attempts=retry_value["maximum_attempts"],
                            delay_seconds=retry_value["delay_seconds"],
                            maximum_delay_seconds=retry_value["maximum_delay_seconds"],
                        ),
                        timeout_seconds=step_value["timeout_seconds"],
                    )
                )
            tasks.append(
                TaskDefinition(
                    task_id=TaskId(task_value["task_id"]),
                    steps=tuple(steps),
                    schema_version=task_value["schema_version"],
                )
            )
        definition = WorkflowDefinition(
            workflow_id=WorkflowId(definition_value["workflow_id"]),
            tasks=tuple(tasks),
            schema_version=definition_value["schema_version"],
        )
        task_snapshots = tuple(
            WorkflowTaskSnapshot(
                task_id=TaskId(item["task_id"]),
                state=TaskState(item["state"]),
                created_at_utc=item["created_at_utc"],
                started_at_utc=item["started_at_utc"],
                finished_at_utc=item["finished_at_utc"],
            )
            for item in value["tasks"]
        )
        step_snapshot_fields = {
            "step_id",
            "task_id",
            "state",
            "attempt_count",
            "created_at_utc",
            "started_at_utc",
            "finished_at_utc",
            "failure_code",
        }
        if value["schema_version"] >= 2:
            step_snapshot_fields.add("retry_after_utc")
        if any(set(item) != step_snapshot_fields for item in value["steps"]):
            raise ValueError("workflow step snapshot fields")
        step_snapshots = tuple(
            WorkflowStepSnapshot(
                step_id=StepId(item["step_id"]),
                task_id=TaskId(item["task_id"]),
                state=StepState(item["state"]),
                attempt_count=item["attempt_count"],
                created_at_utc=item["created_at_utc"],
                started_at_utc=item["started_at_utc"],
                finished_at_utc=item["finished_at_utc"],
                failure_code=item["failure_code"],
                retry_after_utc=item.get("retry_after_utc"),
            )
            for item in value["steps"]
        )
        progress_value = value["progress"]
        if set(progress_value) != {"completed_steps", "total_steps", "percent_complete"}:
            raise ValueError("progress fields")
        outcome = WorkflowState(value["terminal_outcome"]) if value["terminal_outcome"] else None
        snapshot = WorkflowSnapshot(
            schema_version=value["schema_version"],
            definition=definition,
            state=WorkflowState(value["state"]),
            tasks=task_snapshots,
            steps=step_snapshots,
            progress=WorkflowProgress(
                progress_value["completed_steps"],
                progress_value["total_steps"],
                progress_value["percent_complete"],
            ),
            created_at_utc=value["created_at_utc"],
            started_at_utc=value["started_at_utc"],
            finished_at_utc=value["finished_at_utc"],
            terminal_outcome=outcome,
        )
        _validate_snapshot(snapshot)
        return snapshot
    except WorkflowPersistenceError:
        raise
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise WorkflowPersistenceError("workflow snapshot contents are invalid") from exc


def _validate_snapshot(snapshot: WorkflowSnapshot) -> None:
    if snapshot.schema_version not in {1, 2} or not isinstance(
        snapshot.definition, WorkflowDefinition
    ):
        raise WorkflowPersistenceError("workflow snapshot identity is invalid")
    if len(snapshot.steps) != sum(len(task.steps) for task in snapshot.definition.tasks):
        raise WorkflowPersistenceError("workflow snapshot step count is inconsistent")
    if len(snapshot.tasks) != len(snapshot.definition.tasks):
        raise WorkflowPersistenceError("workflow snapshot task count is inconsistent")
    definition_steps = {
        step.step_id: (task.task_id, step)
        for task in snapshot.definition.tasks
        for step in task.steps
    }
    observed_steps = {item.step_id: item for item in snapshot.steps}
    observed_tasks = {item.task_id: item for item in snapshot.tasks}
    if set(definition_steps) != set(observed_steps) or set(observed_tasks) != {
        task.task_id for task in snapshot.definition.tasks
    }:
        raise WorkflowPersistenceError("workflow snapshot identities are inconsistent")
    for step_id, (task_id, definition) in definition_steps.items():
        item = observed_steps[step_id]
        if (
            item.task_id != task_id
            or isinstance(item.attempt_count, bool)
            or not isinstance(item.attempt_count, int)
        ):
            raise WorkflowPersistenceError("workflow step identity or attempt count is invalid")
        if item.attempt_count < 0 or item.attempt_count > definition.retry.maximum_attempts:
            raise WorkflowPersistenceError("workflow step attempt count is out of range")
        if not _SAFE_OPERATION.fullmatch(definition.operation):
            raise WorkflowPersistenceError(
                "workflow operation must be a safe registered identifier"
            )
        if item.failure_code is not None and not _SAFE_FAILURE.fullmatch(item.failure_code):
            raise WorkflowPersistenceError("workflow failure code is invalid")
        if item.state is StepState.RETRYING:
            if item.retry_after_utc is None or not _valid_timestamp(item.retry_after_utc):
                raise WorkflowPersistenceError("retrying step has no valid retry-after timestamp")
            if (
                definition.retry.mode is RetryMode.NONE
                or item.attempt_count >= definition.retry.maximum_attempts
                or item.failure_code is None
            ):
                raise WorkflowPersistenceError("retrying step has no configured retry remaining")
        elif item.retry_after_utc is not None:
            raise WorkflowPersistenceError("non-retrying step has a retry-after timestamp")
        if snapshot.schema_version == 1 and item.retry_after_utc is not None:
            raise WorkflowPersistenceError(
                "schema-1 workflow state cannot contain retry scheduling"
            )
        if item.state is StepState.READY and any(
            observed_steps[dependency].state is not StepState.SUCCEEDED
            for dependency in definition.depends_on
        ):
            raise WorkflowPersistenceError("ready workflow step has incomplete dependencies")
        for timestamp in (item.created_at_utc, item.started_at_utc, item.finished_at_utc):
            if timestamp is not None and not _valid_timestamp(timestamp):
                raise WorkflowPersistenceError("workflow step timestamp is invalid")
    for item in snapshot.tasks:
        for timestamp in (item.created_at_utc, item.started_at_utc, item.finished_at_utc):
            if timestamp is not None and not _valid_timestamp(timestamp):
                raise WorkflowPersistenceError("workflow task timestamp is invalid")
    for task in snapshot.definition.tasks:
        task_snapshot = observed_tasks[task.task_id]
        states = tuple(observed_steps[step.step_id].state for step in task.steps)
        if all(state is StepState.CREATED for state in states):
            expected_task_state = TaskState.CREATED
        elif any(state is StepState.CANCELING for state in states):
            expected_task_state = TaskState.CANCELING
        elif any(state is StepState.RUNNING for state in states):
            expected_task_state = TaskState.RUNNING
        elif any(state is StepState.RETRYING for state in states):
            expected_task_state = TaskState.RETRYING
        elif any(state in {StepState.FAILED, StepState.SKIPPED} for state in states):
            expected_task_state = TaskState.FAILED
        elif all(
            state in {StepState.SUCCEEDED, StepState.FAILED, StepState.CANCELED, StepState.SKIPPED}
            for state in states
        ):
            expected_task_state = (
                TaskState.CANCELED
                if any(state is StepState.CANCELED for state in states)
                else TaskState.SUCCEEDED
            )
        elif any(state is StepState.READY for state in states):
            expected_task_state = TaskState.READY
        else:
            expected_task_state = TaskState.BLOCKED
        if task_snapshot.state is not expected_task_state:
            raise WorkflowPersistenceError("workflow task state is inconsistent with its steps")
    for timestamp in (snapshot.created_at_utc, snapshot.started_at_utc, snapshot.finished_at_utc):
        if timestamp is not None and not _valid_timestamp(timestamp):
            raise WorkflowPersistenceError("workflow timestamp is invalid")
    active = [
        item for item in snapshot.steps if item.state in {StepState.RUNNING, StepState.CANCELING}
    ]
    if len(active) > 1:
        raise WorkflowPersistenceError("workflow snapshot has multiple active steps")
    completed = sum(
        item.state in {StepState.SUCCEEDED, StepState.FAILED, StepState.CANCELED, StepState.SKIPPED}
        for item in snapshot.steps
    )
    total = len(snapshot.steps)
    if (
        snapshot.progress.completed_steps != completed
        or snapshot.progress.total_steps != total
        or snapshot.progress.percent_complete != round(completed * 100.0 / total, 2)
    ):
        raise WorkflowPersistenceError("workflow progress summary is inconsistent")
    terminal = snapshot.state in {
        WorkflowState.SUCCEEDED,
        WorkflowState.FAILED,
        WorkflowState.CANCELED,
    }
    if snapshot.terminal_outcome != (snapshot.state if terminal else None):
        raise WorkflowPersistenceError("workflow terminal outcome is inconsistent")
    step_states = tuple(item.state for item in snapshot.steps)
    workflow_state_valid = {
        WorkflowState.CREATED: all(state is StepState.CREATED for state in step_states),
        WorkflowState.READY: bool(any(state is StepState.READY for state in step_states))
        and not active,
        WorkflowState.RUNNING: len(active) == 1 and active[0].state is StepState.RUNNING,
        WorkflowState.BLOCKED: any(state is StepState.BLOCKED for state in step_states)
        and not active,
        WorkflowState.CANCELING: len(active) == 1 and active[0].state is StepState.CANCELING,
        WorkflowState.SUCCEEDED: all(state is StepState.SUCCEEDED for state in step_states),
        WorkflowState.FAILED: any(state is StepState.FAILED for state in step_states)
        and not active,
        WorkflowState.CANCELED: any(state is StepState.CANCELED for state in step_states)
        and all(
            state in {StepState.SUCCEEDED, StepState.FAILED, StepState.CANCELED, StepState.SKIPPED}
            for state in step_states
        ),
        WorkflowState.RETRYING: any(state is StepState.RETRYING for state in step_states)
        and not active,
    }[snapshot.state]
    if not workflow_state_valid:
        raise WorkflowPersistenceError("workflow state is inconsistent with its steps")


def _valid_timestamp(value: str) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    from datetime import datetime

    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return parsed.isoformat(timespec="milliseconds").replace("+00:00", "Z") == value


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _parse_canonical_object(data: bytes) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
        canonical = _canonical_json(value)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise WorkflowPersistenceError("workflow journal JSON is invalid") from exc
    if not isinstance(value, dict) or canonical != data:
        raise WorkflowPersistenceError("workflow journal JSON is not canonical")
    return value


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _hash_event(event: dict[str, Any]) -> str:
    unsigned = dict(event)
    unsigned.pop("event_hash", None)
    return "sha256:" + hashlib.sha256(_canonical_json(unsigned)).hexdigest()


def _validate_event_details(event_type: str, details: Any) -> None:
    if not isinstance(details, dict) or any(
        not isinstance(key, str) or not isinstance(value, str) for key, value in details.items()
    ):
        raise WorkflowPersistenceError("workflow journal event details are invalid")
    expected = {
        "workflow.recovery_resumed": {"recovery_decision": "retry_from_start"},
        "workflow.recovery_failed": {"recovery_decision": "mark_failed"},
    }.get(event_type, {})
    if details != expected:
        raise WorkflowPersistenceError("workflow journal event details are invalid")


def _atomic_publish_new(destination: Path, data: bytes) -> None:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if destination.exists() or destination.is_symlink():
            raise FileExistsError("journal record already exists")
        os.link(temporary, destination)
        with suppress(OSError):
            temporary.unlink()
        _fsync_directory(destination.parent)
    except OSError as exc:
        raise WorkflowPersistenceError("workflow journal record could not be published") from exc
    finally:
        if temporary is not None:
            with suppress(OSError):
                temporary.unlink(missing_ok=True)


def _atomic_replace(destination: Path, data: bytes) -> None:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if destination.is_symlink():
            raise WorkflowPersistenceError("workflow snapshot cannot be a symlink")
        os.replace(temporary, destination)
        _fsync_directory(destination.parent)
    finally:
        if temporary is not None:
            with suppress(OSError):
                temporary.unlink(missing_ok=True)


def _fsync_directory(directory: Path) -> None:
    """Best-effort directory-entry durability where the platform supports it."""
    if os.name == "nt":
        return
    try:
        descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError:
        warnings.warn(
            "Workflow record was atomically published but directory fsync is unsupported.",
            RuntimeWarning,
            stacklevel=2,
        )
