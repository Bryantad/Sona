"""In-process supervised services with isolated, bounded restart behavior."""

from __future__ import annotations

import inspect
import math
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from .contracts import RestartMode, ServiceDefinition, ServiceState

ServiceTarget = Callable[["ServiceContext"], None]


class ServiceLifecycleError(RuntimeError):
    """Raised when a service lifecycle operation is invalid for its current state."""


@dataclass(frozen=True, slots=True)
class ServiceSnapshot:
    service_id: str
    parent_service_id: str | None
    state: ServiceState
    attempts: int
    restarts: int
    last_failure_code: str | None
    updated_at_utc: str


@dataclass(slots=True)
class _ServiceRecord:
    definition: ServiceDefinition
    target: ServiceTarget
    parent_service_id: str | None
    state: ServiceState
    attempts: int
    restarts: int
    last_failure_code: str | None
    updated_at_utc: str
    cancel_event: threading.Event | None = None
    thread: threading.Thread | None = None


class ServiceContext:
    """Cooperative cancellation and startup readiness for one service run."""

    def __init__(
        self,
        service_id: str,
        cancel_event: threading.Event,
        mark_healthy: Callable[[], None],
    ) -> None:
        self.service_id = service_id
        self._cancel_event = cancel_event
        self._mark_healthy_callback = mark_healthy

    @property
    def cancellation_requested(self) -> bool:
        return self._cancel_event.is_set()

    def wait_cancelled(self, timeout: float | None = None) -> bool:
        """Wait for cooperative cancellation; return whether it was requested."""
        deadline = _deadline(timeout)
        return self._cancel_event.wait(_remaining(deadline))

    def mark_healthy(self) -> None:
        """Report startup readiness; health is informational, not authorization."""
        self._mark_healthy_callback()


class ServiceSupervisor:
    """Own service threads, isolate failures, and cap per-service restarts."""

    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._records: dict[str, _ServiceRecord] = {}
        self._closed = False

    def register(
        self,
        definition: ServiceDefinition,
        target: ServiceTarget,
        *,
        parent_service_id: str | None = None,
    ) -> None:
        if not isinstance(definition, ServiceDefinition):
            raise TypeError("definition must be a ServiceDefinition")
        if not callable(target):
            raise TypeError("target must be callable with a ServiceContext")
        if inspect.iscoroutinefunction(target):
            raise TypeError("service target must be synchronous")
        try:
            inspect.signature(target).bind(object())
        except (TypeError, ValueError) as exc:
            raise TypeError("service target must accept a context argument") from exc
        if parent_service_id is not None and not isinstance(parent_service_id, str):
            raise ValueError("parent_service_id must be a registered service ID")
        with self._condition:
            if self._closed:
                raise ServiceLifecycleError("supervisor is closed")
            if definition.service_id in self._records:
                raise ValueError(f"service is already registered: {definition.service_id}")
            if parent_service_id is not None and parent_service_id not in self._records:
                raise ValueError("parent service must be registered before its child")
            now = _utc_now()
            self._records[definition.service_id] = _ServiceRecord(
                definition=definition,
                target=target,
                parent_service_id=parent_service_id,
                state=ServiceState.STOPPED,
                attempts=0,
                restarts=0,
                last_failure_code=None,
                updated_at_utc=now,
            )

    def start(self, service_id: str) -> None:
        with self._condition:
            record = self._get_record(service_id)
            if self._closed:
                raise ServiceLifecycleError("supervisor is closed")
            if record.state not in {ServiceState.STOPPED, ServiceState.FAILED}:
                raise ServiceLifecycleError(
                    f"cannot start service from state {record.state.value}"
                )
            if record.thread is not None and record.thread.is_alive():
                raise ServiceLifecycleError("previous service run has not stopped")
            if record.parent_service_id is not None:
                parent = self._records[record.parent_service_id]
                if parent.state is not ServiceState.HEALTHY:
                    raise ServiceLifecycleError("parent service must be healthy before child start")
            record.cancel_event = threading.Event()
            record.attempts = 0
            record.restarts = 0
            record.last_failure_code = None
            self._set_state(record, ServiceState.STARTING)
            thread = threading.Thread(
                target=self._run_service,
                args=(record,),
                name=f"sona-service-{record.definition.service_id}",
                daemon=False,
            )
            record.thread = thread
            try:
                thread.start()
            except RuntimeError:
                record.thread = None
                record.last_failure_code = "SONA-SERVICE-START-FAILED"
                self._set_state(record, ServiceState.FAILED)
                raise ServiceLifecycleError("could not start the service worker thread") from None

    def stop(
        self,
        service_id: str,
        *,
        cascade: bool = False,
        timeout: float | None = None,
    ) -> bool:
        deadline = _deadline(timeout)
        with self._condition:
            record = self._get_record(service_id)
            target_ids = self._descendant_order(service_id) if cascade else [service_id]
        stopped = True
        for target_id in target_ids:
            remaining = _remaining(deadline)
            stopped = self._stop_one(target_id, remaining) and stopped
        return stopped

    def stop_all(self, *, timeout: float | None = None) -> bool:
        deadline = _deadline(timeout)
        with self._condition:
            ordered_ids: list[str] = []
            for service_id in reversed(tuple(self._records)):
                ordered_ids.extend(self._descendant_order(service_id))
            # Preserve the first occurrence; child-first order is already supplied.
            ordered_ids = list(dict.fromkeys(ordered_ids))
            self._closed = True
        stopped = True
        for service_id in ordered_ids:
            stopped = self._stop_one(service_id, _remaining(deadline)) and stopped
        return stopped

    def close(self, *, timeout: float | None = None) -> bool:
        return self.stop_all(timeout=timeout)

    def snapshot(self, service_id: str) -> ServiceSnapshot:
        with self._condition:
            record = self._get_record(service_id)
            return _snapshot(record)

    def snapshots(self) -> tuple[ServiceSnapshot, ...]:
        with self._condition:
            return tuple(_snapshot(record) for record in self._records.values())

    def wait_for_state(
        self,
        service_id: str,
        state: ServiceState,
        *,
        timeout: float,
    ) -> bool:
        deadline = _deadline(timeout)
        if deadline is None:
            raise ValueError("wait_for_state requires a finite timeout")
        if not isinstance(state, ServiceState):
            raise TypeError("state must be a ServiceState")
        with self._condition:
            record = self._get_record(service_id)
            while record.state is not state:
                remaining = _remaining(deadline)
                if remaining is not None and remaining <= 0:
                    return False
                self._condition.wait(remaining)
            return True

    def _run_service(self, record: _ServiceRecord) -> None:
        assert record.cancel_event is not None
        context = ServiceContext(
            record.definition.service_id,
            record.cancel_event,
            lambda: self._mark_healthy(record),
        )
        while True:
            with self._condition:
                if record.cancel_event.is_set():
                    self._set_state(record, ServiceState.STOPPED)
                    return
                record.attempts += 1
                self._condition.notify_all()
            try:
                record.target(context)
            except (Exception, SystemExit, KeyboardInterrupt, GeneratorExit):
                with self._condition:
                    if record.cancel_event.is_set():
                        self._set_state(record, ServiceState.STOPPED)
                        return
                    record.last_failure_code = "SONA-SERVICE-FAILED"
                    policy = record.definition.restart_policy
                    if (
                        policy.mode is RestartMode.NEVER
                        or record.restarts >= policy.maximum_restarts
                    ):
                        self._set_state(record, ServiceState.FAILED)
                        return
                    record.restarts += 1
                    self._set_state(record, ServiceState.DEGRADED)
                if record.cancel_event.wait(record.definition.restart_policy.delay_seconds):
                    with self._condition:
                        self._set_state(record, ServiceState.STOPPED)
                    return
                with self._condition:
                    self._set_state(record, ServiceState.STARTING)
                continue
            else:
                with self._condition:
                    self._set_state(record, ServiceState.STOPPED)
                return

    def _mark_healthy(self, record: _ServiceRecord) -> None:
        with self._condition:
            if record.state not in {ServiceState.STARTING, ServiceState.DEGRADED}:
                raise ServiceLifecycleError(
                    f"cannot report healthy from state {record.state.value}"
                )
            self._set_state(record, ServiceState.HEALTHY)

    def _stop_one(self, service_id: str, timeout: float | None) -> bool:
        with self._condition:
            record = self._get_record(service_id)
            thread = record.thread
            if record.state in {ServiceState.STOPPED, ServiceState.FAILED}:
                if thread is None or not thread.is_alive():
                    return True
            elif record.cancel_event is None or thread is None:
                self._set_state(record, ServiceState.STOPPED)
                return True
            else:
                record.cancel_event.set()
                self._set_state(record, ServiceState.STOPPING)
                self._condition.notify_all()
        thread.join(timeout)
        return not thread.is_alive()

    def _get_record(self, service_id: str) -> _ServiceRecord:
        try:
            return self._records[service_id]
        except (KeyError, TypeError) as exc:
            raise KeyError(f"unknown service: {service_id}") from exc

    def _descendant_order(self, service_id: str) -> list[str]:
        descendants = [
            child_id
            for child_id, record in self._records.items()
            if record.parent_service_id == service_id
        ]
        ordered: list[str] = []
        for child_id in descendants:
            ordered.extend(self._descendant_order(child_id))
        ordered.append(service_id)
        return ordered

    def _set_state(self, record: _ServiceRecord, state: ServiceState) -> None:
        record.state = state
        record.updated_at_utc = _utc_now()
        self._condition.notify_all()


def _snapshot(record: _ServiceRecord) -> ServiceSnapshot:
    return ServiceSnapshot(
        service_id=record.definition.service_id,
        parent_service_id=record.parent_service_id,
        state=record.state,
        attempts=record.attempts,
        restarts=record.restarts,
        last_failure_code=record.last_failure_code,
        updated_at_utc=record.updated_at_utc,
    )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _deadline(timeout: float | None) -> float | None:
    if timeout is None:
        return None
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise ValueError("timeout must be finite and non-negative")
    try:
        timeout_value = float(timeout)
    except (OverflowError, ValueError) as exc:
        raise ValueError("timeout must be finite and non-negative") from exc
    if not math.isfinite(timeout_value) or timeout_value < 0:
        raise ValueError("timeout must be finite and non-negative")
    deadline = time.monotonic() + timeout_value
    if not math.isfinite(deadline):
        raise ValueError("timeout deadline exceeds supported range")
    return deadline


def _remaining(deadline: float | None) -> float | None:
    return None if deadline is None else max(0.0, deadline - time.monotonic())
