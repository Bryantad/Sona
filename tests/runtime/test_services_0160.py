"""Tests for supervised service lifecycle and bounded restarts."""

from __future__ import annotations

import threading

import pytest

from sona.runtime import (
    RestartMode,
    RestartPolicy,
    ServiceDefinition,
    ServiceLifecycleError,
    ServiceState,
    ServiceSupervisor,
)


def _wait(supervisor: ServiceSupervisor, service_id: str, state: ServiceState) -> None:
    assert supervisor.wait_for_state(service_id, state, timeout=2)


def _healthy_until_cancelled(context) -> None:
    context.mark_healthy()
    context.wait_cancelled()


def test_supervisor_starts_children_after_parent_health_and_cascades_stop():
    supervisor = ServiceSupervisor()
    supervisor.register(ServiceDefinition("root"), _healthy_until_cancelled)
    with pytest.raises(ValueError, match="parent service must be registered"):
        supervisor.register(
            ServiceDefinition("orphan"), _healthy_until_cancelled, parent_service_id="missing"
        )
    supervisor.register(
        ServiceDefinition("worker"), lambda _context: None, parent_service_id="root"
    )
    with pytest.raises(ServiceLifecycleError, match="parent service must be healthy"):
        supervisor.start("worker")

    supervisor.start("root")
    _wait(supervisor, "root", ServiceState.HEALTHY)
    supervisor.start("worker")
    _wait(supervisor, "worker", ServiceState.STOPPED)
    assert supervisor.snapshot("worker").parent_service_id == "root"
    assert supervisor.snapshot("root").state is ServiceState.HEALTHY
    assert supervisor.stop("root", cascade=True, timeout=1)
    assert supervisor.snapshot("root").state is ServiceState.STOPPED
    assert supervisor.close(timeout=1)


def test_failure_restarts_only_the_service_with_a_bounded_attempt_count():
    supervisor = ServiceSupervisor()
    attempts = 0
    count_lock = threading.Lock()

    def flaky(context) -> None:
        nonlocal attempts
        with count_lock:
            attempts += 1
            current_attempt = attempts
        if current_attempt < 3:
            raise RuntimeError("do not retain exception text")
        context.mark_healthy()
        context.wait_cancelled()

    supervisor.register(
        ServiceDefinition(
            "flaky",
            restart_policy=RestartPolicy(
                RestartMode.BOUNDED,
                maximum_restarts=2,
                delay_seconds=0.001,
            ),
        ),
        flaky,
    )
    supervisor.start("flaky")
    _wait(supervisor, "flaky", ServiceState.HEALTHY)
    status = supervisor.snapshot("flaky")
    assert attempts == 3
    assert status.attempts == 3
    assert status.restarts == 2
    assert status.last_failure_code == "SONA-SERVICE-FAILED"
    assert "do not retain" not in repr(status)
    assert supervisor.stop("flaky", timeout=1)


def test_restart_budget_exhaustion_is_terminal_and_reports_no_exception_text():
    supervisor = ServiceSupervisor()
    attempts = 0

    def always_fails(_context) -> None:
        nonlocal attempts
        attempts += 1
        raise OSError("secret path and raw OS message")

    supervisor.register(
        ServiceDefinition(
            "broken",
            restart_policy=RestartPolicy(
                RestartMode.ON_FAILURE,
                maximum_restarts=1,
                delay_seconds=0,
            ),
        ),
        always_fails,
    )
    supervisor.start("broken")
    _wait(supervisor, "broken", ServiceState.FAILED)
    status = supervisor.snapshot("broken")
    assert attempts == 2
    assert status.restarts == 1
    assert status.last_failure_code == "SONA-SERVICE-FAILED"
    assert "secret path" not in repr(status)
    assert supervisor.close(timeout=1)


def test_one_service_failure_does_not_stop_an_unrelated_service():
    supervisor = ServiceSupervisor()
    supervisor.register(ServiceDefinition("survivor"), _healthy_until_cancelled)
    supervisor.register(
        ServiceDefinition("failure"), lambda _context: (_ for _ in ()).throw(RuntimeError())
    )
    supervisor.start("survivor")
    _wait(supervisor, "survivor", ServiceState.HEALTHY)
    supervisor.start("failure")
    _wait(supervisor, "failure", ServiceState.FAILED)
    assert supervisor.snapshot("survivor").state is ServiceState.HEALTHY
    assert supervisor.stop_all(timeout=1)


def test_parent_failure_does_not_implicitly_stop_child_service():
    supervisor = ServiceSupervisor()
    fail_parent = threading.Event()

    def parent(context) -> None:
        context.mark_healthy()
        fail_parent.wait()
        raise RuntimeError("parent failure")

    supervisor.register(ServiceDefinition("parent"), parent)
    supervisor.register(
        ServiceDefinition("child"), _healthy_until_cancelled, parent_service_id="parent"
    )
    supervisor.start("parent")
    _wait(supervisor, "parent", ServiceState.HEALTHY)
    supervisor.start("child")
    _wait(supervisor, "child", ServiceState.HEALTHY)
    fail_parent.set()
    _wait(supervisor, "parent", ServiceState.FAILED)
    assert supervisor.snapshot("child").state is ServiceState.HEALTHY
    assert supervisor.stop("parent", cascade=True, timeout=1)
    assert supervisor.snapshot("child").state is ServiceState.STOPPED


def test_stop_during_restart_delay_prevents_another_attempt():
    supervisor = ServiceSupervisor()
    attempts = 0

    def fails(_context) -> None:
        nonlocal attempts
        attempts += 1
        raise RuntimeError

    supervisor.register(
        ServiceDefinition(
            "delayed",
            restart_policy=RestartPolicy(
                RestartMode.BOUNDED,
                maximum_restarts=5,
                delay_seconds=60,
            ),
        ),
        fails,
    )
    supervisor.start("delayed")
    _wait(supervisor, "delayed", ServiceState.DEGRADED)
    assert supervisor.stop("delayed", timeout=1)
    assert supervisor.snapshot("delayed").state is ServiceState.STOPPED
    assert attempts == 1


def test_uncooperative_service_is_not_force_killed_on_stop_timeout():
    supervisor = ServiceSupervisor()
    release = threading.Event()
    started = threading.Event()

    def ignores_cancellation(context) -> None:
        context.mark_healthy()
        started.set()
        release.wait()

    supervisor.register(ServiceDefinition("stuck"), ignores_cancellation)
    supervisor.start("stuck")
    assert started.wait(1)
    assert supervisor.stop("stuck", timeout=0.01) is False
    assert supervisor.snapshot("stuck").state is ServiceState.STOPPING
    release.set()
    try:
        _wait(supervisor, "stuck", ServiceState.STOPPED)
    finally:
        release.set()
        supervisor.close(timeout=1)


def test_restart_policy_and_service_targets_are_strictly_bounded():
    with pytest.raises(ValueError, match="between 0 and 1000"):
        RestartPolicy(RestartMode.BOUNDED, maximum_restarts=1001)
    with pytest.raises(ValueError, match="finite and between"):
        RestartPolicy(RestartMode.BOUNDED, maximum_restarts=1, delay_seconds=float("inf"))

    supervisor = ServiceSupervisor()
    with pytest.raises(TypeError, match="synchronous"):
        async def asynchronous(_context):
            return None

        supervisor.register(ServiceDefinition("async"), asynchronous)
    with pytest.raises(TypeError, match="context argument"):
        supervisor.register(ServiceDefinition("no-context"), lambda: None)
    assert supervisor.close(timeout=1)
