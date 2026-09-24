"""Tests for independent, time-aware health and heartbeat reporting."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from sona.runtime import (
    HealthMonitor,
    HealthPolicy,
    HealthState,
    ServiceDefinition,
    ServiceState,
    ServiceSupervisor,
)


class FakeClock:
    def __init__(self) -> None:
        self.monotonic = 100.0
        self.wall = datetime(2026, 9, 24, tzinfo=UTC)

    def monotonic_now(self) -> float:
        return self.monotonic

    def utc_now(self) -> datetime:
        return self.wall

    def advance(self, seconds: float) -> None:
        self.monotonic += seconds
        self.wall += timedelta(seconds=seconds)


def _monitor(clock: FakeClock, policy: HealthPolicy | None = None) -> HealthMonitor:
    monitor = HealthMonitor(
        monotonic_clock=clock.monotonic_now,
        utc_clock=clock.utc_now,
    )
    monitor.register("worker", policy or HealthPolicy(5, 12))
    return monitor


def test_heartbeat_is_liveness_not_health_and_stale_state_escalates():
    clock = FakeClock()
    monitor = _monitor(clock)
    initial = monitor.snapshot("worker")
    assert initial.state is HealthState.UNKNOWN
    assert initial.age_seconds is None

    alive = monitor.heartbeat("worker")
    assert alive.state is HealthState.UNKNOWN
    assert alive.heartbeat_count == 1
    assert alive.sequence == 1

    ready = monitor.report("worker", HealthState.HEALTHY)
    assert ready.state is HealthState.HEALTHY
    assert ready.last_observed_at_utc == "2026-09-24T00:00:00Z"
    clock.advance(5)
    assert monitor.snapshot("worker").state is HealthState.DEGRADED
    clock.advance(7)
    stale = monitor.snapshot("worker")
    assert stale.state is HealthState.UNHEALTHY
    assert stale.age_seconds == 12
    # This UNHEALTHY state was derived only from missing contact, so a fresh
    # heartbeat clears staleness and restores the last reported HEALTHY state.
    assert monitor.heartbeat("worker").state is HealthState.HEALTHY


def test_fresh_heartbeat_does_not_clear_reported_degradation_or_unhealthy_state():
    clock = FakeClock()
    monitor = _monitor(clock)
    monitor.report("worker", HealthState.DEGRADED, diagnostic_code="WORKER_BUSY")
    clock.advance(4)
    heartbeat = monitor.heartbeat("worker")
    assert heartbeat.state is HealthState.DEGRADED
    assert heartbeat.age_seconds == 0
    assert heartbeat.diagnostic_code == "WORKER_BUSY"

    monitor.report("worker", HealthState.UNHEALTHY, diagnostic_code="DEPENDENCY_DOWN")
    monitor.heartbeat("worker")
    assert monitor.snapshot("worker").state is HealthState.UNHEALTHY
    recovered = monitor.report("worker", HealthState.HEALTHY)
    assert recovered.state is HealthState.HEALTHY
    assert recovered.diagnostic_code is None


def test_health_policy_and_report_inputs_are_strict():
    with pytest.raises(ValueError, match="greater than degraded"):
        HealthPolicy(5, 5)
    with pytest.raises(ValueError, match="finite and positive"):
        HealthPolicy(float("nan"), 10)
    with pytest.raises(ValueError, match="30 days"):
        HealthPolicy(40 * 24 * 60 * 60, 41 * 24 * 60 * 60)

    monitor = HealthMonitor()
    with pytest.raises(ValueError, match="safe identifier"):
        monitor.register("../worker")
    monitor.register("worker")
    with pytest.raises(ValueError, match="already registered"):
        monitor.register("worker")
    with pytest.raises(ValueError, match="uppercase code"):
        monitor.report("worker", HealthState.UNHEALTHY, diagnostic_code="raw OS failure")
    with pytest.raises(TypeError, match="HealthState"):
        monitor.report("worker", "healthy")
    with pytest.raises(KeyError, match="unknown health subject"):
        monitor.snapshot("missing")


def test_service_health_is_exposed_separately_from_lifecycle_and_stops_unknown():
    clock = FakeClock()
    monitor = HealthMonitor(
        monotonic_clock=clock.monotonic_now,
        utc_clock=clock.utc_now,
    )
    supervisor = ServiceSupervisor(health_monitor=monitor)
    context_holder = []

    def service(context) -> None:
        context_holder.append(context)
        context.mark_healthy()
        context.wait_cancelled()

    supervisor.register(
        ServiceDefinition("worker"),
        service,
        health_policy=HealthPolicy(2, 4),
    )
    supervisor.start("worker")
    assert supervisor.wait_for_state("worker", ServiceState.HEALTHY, timeout=1)
    assert supervisor.snapshot("worker").health.state is HealthState.HEALTHY

    clock.advance(2)
    status = supervisor.snapshot("worker")
    assert status.state is ServiceState.HEALTHY
    assert status.health.state is HealthState.DEGRADED

    context_holder[0].heartbeat()
    assert supervisor.snapshot("worker").health.state is HealthState.HEALTHY
    context_holder[0].report_health(HealthState.HEALTHY)
    assert supervisor.snapshot("worker").health.state is HealthState.HEALTHY

    assert supervisor.stop("worker", timeout=1)
    assert supervisor.snapshot("worker").health.state is HealthState.UNKNOWN
    with pytest.raises(RuntimeError, match="cannot heartbeat"):
        context_holder[0].heartbeat()
