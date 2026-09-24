"""Bounded structured in-process task groups with cooperative cancellation."""

from __future__ import annotations

import inspect
import math
import re
import threading
import time
import uuid
from concurrent.futures import CancelledError, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Callable

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class TaskGroupError(RuntimeError):
    """Base error for task-group lifecycle or capacity failures."""


class TaskGroupFullError(TaskGroupError):
    """Raised rather than permitting unbounded pending work or history."""


class TaskGroupClosedError(TaskGroupError):
    """Raised when a closed or canceled group receives new work."""


class TaskCancelledError(TaskGroupError):
    """Raised by a task when its cooperative cancellation is observed."""


class TaskState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    CANCELING = "canceling"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass(frozen=True, slots=True)
class TaskSnapshot:
    task_id: str
    state: TaskState
    submitted_at_utc: str
    started_at_utc: str | None
    completed_at_utc: str | None
    failure_code: str | None


@dataclass(slots=True)
class _TaskRecord:
    task_id: str
    target: Callable[[TaskContext], Any]
    cancel_event: threading.Event
    state: TaskState
    submitted_at_utc: str
    future: Future[Any] | None = None
    started_at_utc: str | None = None
    completed_at_utc: str | None = None
    failure_code: str | None = None


class TaskContext:
    """Cooperative cancellation token supplied to every structured task."""

    def __init__(self, task_id: str, cancel_event: threading.Event) -> None:
        self.task_id = task_id
        self._cancel_event = cancel_event

    @property
    def cancellation_requested(self) -> bool:
        return self._cancel_event.is_set()

    def wait_cancelled(self, timeout: float | None = None) -> bool:
        if timeout is not None and (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or timeout < 0
        ):
            raise ValueError("timeout must be non-negative or None")
        return self._cancel_event.wait(timeout)

    def raise_if_cancelled(self) -> None:
        if self.cancellation_requested:
            raise TaskCancelledError(f"task {self.task_id} cancellation requested")


class TaskHandle:
    def __init__(self, group: BoundedTaskGroup, task_id: str, future: Future[Any]) -> None:
        self.task_id = task_id
        self._group = group
        self._future = future

    def result(self, timeout: float | None = None) -> Any:
        return self._future.result(timeout)

    def cancel(self) -> bool:
        return self._group.cancel_task(self.task_id)

    def snapshot(self) -> TaskSnapshot:
        return self._group.snapshot(self.task_id)


class BoundedTaskGroup:
    """Own a finite worker set, pending-work ceiling, and bounded task history.

    Cancellation is cooperative for running callables. Queued work is canceled
    before start when possible. This API does not force-kill threads or isolate
    resource use at the operating-system boundary.
    """

    def __init__(
        self,
        *,
        maximum_workers: int,
        maximum_tasks: int,
        maximum_records: int = 4096,
        thread_name_prefix: str = "sona-task",
    ) -> None:
        for name, value, upper in (
            ("maximum_workers", maximum_workers, 1024),
            ("maximum_tasks", maximum_tasks, 65_536),
            ("maximum_records", maximum_records, 65_536),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= upper:
                raise ValueError(f"{name} must be between 1 and {upper}")
        if maximum_workers > maximum_tasks:
            raise ValueError("maximum_workers cannot exceed maximum_tasks")
        if not isinstance(thread_name_prefix, str) or not _SAFE_ID.fullmatch(thread_name_prefix):
            raise ValueError("thread_name_prefix must be a safe identifier")
        self.maximum_workers = maximum_workers
        self.maximum_tasks = maximum_tasks
        self.maximum_records = maximum_records
        self._lock = threading.RLock()
        self._records: dict[str, _TaskRecord] = {}
        self._closed = False
        self._cancelled = False
        self._executor = ThreadPoolExecutor(
            max_workers=maximum_workers,
            thread_name_prefix=thread_name_prefix,
        )

    def submit(
        self,
        target: Callable[[TaskContext], Any],
        *,
        task_id: str | None = None,
    ) -> TaskHandle:
        if not callable(target):
            raise TypeError("target must be callable and accept TaskContext")
        try:
            inspect.signature(target).bind(object())
        except (TypeError, ValueError) as exc:
            raise TypeError("target must be callable with one TaskContext argument") from exc
        identifier = task_id or str(uuid.uuid4())
        if not isinstance(identifier, str) or not _SAFE_ID.fullmatch(identifier):
            raise ValueError("task_id must be a safe identifier")
        with self._lock:
            if self._closed or self._cancelled:
                raise TaskGroupClosedError("task group is closed or canceled")
            if identifier in self._records:
                raise ValueError("task_id is already registered")
            pending = sum(
                record.state in {TaskState.QUEUED, TaskState.RUNNING, TaskState.CANCELING}
                for record in self._records.values()
            )
            if pending >= self.maximum_tasks:
                raise TaskGroupFullError("maximum pending task count reached")
            if len(self._records) >= self.maximum_records:
                raise TaskGroupFullError("task history is full; forget terminal records first")
            record = _TaskRecord(
                task_id=identifier,
                target=target,
                cancel_event=threading.Event(),
                state=TaskState.QUEUED,
                submitted_at_utc=_utc_now(),
            )
            self._records[identifier] = record
            try:
                future = self._executor.submit(self._run, identifier)
            except RuntimeError:
                del self._records[identifier]
                raise TaskGroupClosedError("task executor is shut down") from None
            record.future = future
            future.add_done_callback(lambda done, key=identifier: self._on_done(key, done))
            return TaskHandle(self, identifier, future)

    def cancel_task(self, task_id: str) -> bool:
        with self._lock:
            record = self._require_record(task_id)
            if record.state in _TERMINAL:
                return False
            record.cancel_event.set()
            record.state = TaskState.CANCELING
            future = record.future
            if future is not None and future.cancel():
                self._finish(record, TaskState.CANCELED)
            return True

    def cancel(self) -> None:
        with self._lock:
            self._cancelled = True
            task_ids = [
                key for key, record in self._records.items() if record.state not in _TERMINAL
            ]
        for task_id in task_ids:
            self.cancel_task(task_id)

    def snapshot(self, task_id: str) -> TaskSnapshot:
        with self._lock:
            return _snapshot(self._require_record(task_id))

    def snapshots(self) -> tuple[TaskSnapshot, ...]:
        with self._lock:
            return tuple(_snapshot(record) for record in self._records.values())

    def forget(self, task_id: str) -> bool:
        with self._lock:
            record = self._require_record(task_id)
            if record.state not in _TERMINAL:
                return False
            del self._records[task_id]
            return True

    def wait(self, timeout: float | None = None) -> bool:
        if timeout is not None and (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or timeout < 0
        ):
            raise ValueError("timeout must be non-negative or None")
        with self._lock:
            futures = [
                record.future
                for record in self._records.values()
                if record.future is not None and record.state not in _TERMINAL
            ]
        if not futures:
            return True
        _, pending = wait(futures, timeout=timeout)
        return not pending

    def close(self, *, cancel_pending: bool = False, wait_for_tasks: bool = True) -> None:
        if not isinstance(cancel_pending, bool) or not isinstance(wait_for_tasks, bool):
            raise TypeError("cancel_pending and wait_for_tasks must be booleans")
        with self._lock:
            already_closed = self._closed
            self._closed = True
        if cancel_pending:
            self.cancel()
        if not already_closed:
            self._executor.shutdown(wait=wait_for_tasks, cancel_futures=cancel_pending)
        elif wait_for_tasks:
            self._executor.shutdown(wait=True)

    def __enter__(self) -> BoundedTaskGroup:
        with self._lock:
            if self._closed:
                raise TaskGroupClosedError("task group is closed")
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.close(cancel_pending=exc_type is not None, wait_for_tasks=True)
        return False

    def _run(self, task_id: str) -> Any:
        with self._lock:
            record = self._require_record(task_id)
            if record.cancel_event.is_set():
                self._finish(record, TaskState.CANCELED)
                raise TaskCancelledError(f"task {task_id} canceled before start")
            record.state = TaskState.RUNNING
            record.started_at_utc = _utc_now()
            target = record.target
            context = TaskContext(task_id, record.cancel_event)
        try:
            result = target(context)
        except TaskCancelledError:
            with self._lock:
                current = self._require_record(task_id)
                self._finish(current, TaskState.CANCELED)
            raise
        except BaseException:
            with self._lock:
                current = self._require_record(task_id)
                current.failure_code = "SONA-TASK-FAILED"
                self._finish(current, TaskState.FAILED)
            raise
        with self._lock:
            current = self._require_record(task_id)
            self._finish(current, TaskState.SUCCEEDED)
        return result

    def _on_done(self, task_id: str, future: Future[Any]) -> None:
        if not future.cancelled():
            return
        with self._lock:
            record = self._records.get(task_id)
            if record is not None and record.state not in _TERMINAL:
                record.cancel_event.set()
                self._finish(record, TaskState.CANCELED)

    def _require_record(self, task_id: str) -> _TaskRecord:
        record = self._records.get(task_id)
        if record is None:
            raise KeyError(f"unknown task_id: {task_id}")
        return record

    @staticmethod
    def _finish(record: _TaskRecord, state: TaskState) -> None:
        record.state = state
        record.completed_at_utc = _utc_now()


_TERMINAL = {TaskState.SUCCEEDED, TaskState.FAILED, TaskState.CANCELED}


def _snapshot(record: _TaskRecord) -> TaskSnapshot:
    return TaskSnapshot(
        task_id=record.task_id,
        state=record.state,
        submitted_at_utc=record.submitted_at_utc,
        started_at_utc=record.started_at_utc,
        completed_at_utc=record.completed_at_utc,
        failure_code=record.failure_code,
    )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
