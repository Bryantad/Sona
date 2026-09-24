"""Phase 14 tests for bounded task ownership and honest resource reports."""

from __future__ import annotations

import threading
from concurrent.futures import CancelledError

import pytest

from sona.runtime import (
    BoundedTaskGroup,
    EnforcementStatus,
    ResourceBudget,
    ResourceBudgetReporter,
    ResourceLimit,
    ResourceMeasurement,
    ResourceUnit,
    TaskCancelledError,
    TaskGroupClosedError,
    TaskGroupFullError,
    TaskState,
)


def test_resource_budget_report_keeps_enforcement_observation_and_unsupported_distinct():
    budget = ResourceBudget(
        "worker-budget",
        (
            ResourceLimit("memory", 1024, ResourceUnit.BYTES, EnforcementStatus.OBSERVED),
            ResourceLimit("queue", 4, ResourceUnit.ITEMS, EnforcementStatus.ENFORCED),
            ResourceLimit("vram", 0, ResourceUnit.BYTES, EnforcementStatus.UNSUPPORTED),
        ),
    )
    report = ResourceBudgetReporter.report(
        budget,
        (
            ResourceMeasurement("memory", ResourceUnit.BYTES, 2048),
            ResourceMeasurement("queue", ResourceUnit.ITEMS, 3),
            ResourceMeasurement("vram", ResourceUnit.BYTES, 8192),
        ),
    )
    assert [(item.status, item.exceeds_limit) for item in report.limits] == [
        (EnforcementStatus.OBSERVED, True),
        (EnforcementStatus.ENFORCED, False),
        (EnforcementStatus.UNSUPPORTED, None),
    ]
    assert report.limits[2].observed_amount == 8192


def test_resource_contracts_reject_unhonest_or_malformed_limits():
    with pytest.raises(ValueError, match="amount=0"):
        ResourceLimit("memory", 10, ResourceUnit.BYTES, EnforcementStatus.UNSUPPORTED)
    with pytest.raises(ValueError, match="positive"):
        ResourceLimit("memory", 0, ResourceUnit.BYTES, EnforcementStatus.OBSERVED)
    with pytest.raises(TypeError, match="EnforcementStatus"):
        ResourceLimit("memory", 10, ResourceUnit.BYTES, "enforced")
    with pytest.raises(ValueError, match="safe identifier"):
        ResourceLimit(r"C:\\temp", 10, ResourceUnit.BYTES, EnforcementStatus.OBSERVED)


def test_resource_report_rejects_duplicate_and_undeclared_measurements():
    budget = ResourceBudget(
        "budget-2",
        (ResourceLimit("queue", 2, ResourceUnit.ITEMS, EnforcementStatus.ENFORCED),),
    )
    measurement = ResourceMeasurement("queue", ResourceUnit.ITEMS, 1)
    with pytest.raises(ValueError, match="unique"):
        ResourceBudgetReporter.report(budget, (measurement, measurement))
    with pytest.raises(ValueError, match="does not match"):
        ResourceBudgetReporter.report(
            budget, (ResourceMeasurement("memory", ResourceUnit.BYTES, 2),)
        )


def test_task_group_bounds_workers_and_queued_work():
    group = BoundedTaskGroup(maximum_workers=1, maximum_tasks=2)
    started = threading.Event()
    release = threading.Event()

    def blocked(context):
        started.set()
        release.wait(2)
        return "first"

    first = group.submit(blocked, task_id="task-1")
    assert started.wait(1)
    second = group.submit(lambda context: "second", task_id="task-2")
    assert second.snapshot().state is TaskState.QUEUED
    with pytest.raises(TaskGroupFullError, match="maximum pending"):
        group.submit(lambda context: "overflow")
    release.set()
    assert first.result(2) == "first"
    assert second.result(2) == "second"
    assert first.snapshot().state is TaskState.SUCCEEDED
    assert second.snapshot().state is TaskState.SUCCEEDED
    group.close()
    with pytest.raises(TaskGroupClosedError):
        group.submit(lambda context: None)


def test_task_group_never_exceeds_configured_running_worker_count():
    group = BoundedTaskGroup(maximum_workers=2, maximum_tasks=4)
    release = threading.Event()
    both_started = threading.Event()
    lock = threading.Lock()
    active = 0
    peak = 0

    def measured(context):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
            if active == 2:
                both_started.set()
        release.wait(2)
        with lock:
            active -= 1

    handles = [group.submit(measured) for _ in range(4)]
    assert both_started.wait(1)
    assert sum(handle.snapshot().state is TaskState.QUEUED for handle in handles) == 2
    release.set()
    assert all(handle.result(2) is None for handle in handles)
    assert peak == 2
    group.close()


def test_task_cancellation_propagates_to_running_and_queued_children():
    group = BoundedTaskGroup(maximum_workers=1, maximum_tasks=4)
    started = threading.Event()

    def cooperative(context):
        started.set()
        context.wait_cancelled(2)
        context.raise_if_cancelled()

    running = group.submit(cooperative)
    assert started.wait(1)
    queued = group.submit(lambda context: "must not run")
    group.cancel()
    assert running.snapshot().state in {TaskState.CANCELING, TaskState.CANCELED}
    assert queued.snapshot().state is TaskState.CANCELED
    with pytest.raises(TaskCancelledError):
        running.result(2)
    with pytest.raises(CancelledError):
        queued.result(1)
    assert group.wait(1)
    assert running.snapshot().state is TaskState.CANCELED
    assert queued.snapshot().state is TaskState.CANCELED
    group.close()


def test_task_failure_is_recorded_with_safe_code_and_result_preserves_exception():
    group = BoundedTaskGroup(maximum_workers=1, maximum_tasks=1)

    def fail(context):
        raise RuntimeError("sensitive path must not be copied into snapshots")

    handle = group.submit(fail)
    with pytest.raises(RuntimeError, match="sensitive path"):
        handle.result(1)
    snapshot = handle.snapshot()
    assert snapshot.state is TaskState.FAILED
    assert snapshot.failure_code == "SONA-TASK-FAILED"
    assert "sensitive" not in str(snapshot)
    assert snapshot.started_at_utc is not None
    assert snapshot.completed_at_utc is not None
    group.close()


def test_task_history_is_bounded_and_terminal_records_can_be_forgotten():
    group = BoundedTaskGroup(maximum_workers=1, maximum_tasks=1, maximum_records=1)
    first = group.submit(lambda context: 1, task_id="durable-id")
    assert first.result(1) == 1
    with pytest.raises(TaskGroupFullError, match="history"):
        group.submit(lambda context: 2)
    assert group.forget("durable-id")
    second = group.submit(lambda context: 2, task_id="durable-id")
    assert second.result(1) == 2
    group.close()


def test_task_group_validates_limits_targets_and_ids():
    with pytest.raises(ValueError, match="cannot exceed"):
        BoundedTaskGroup(maximum_workers=2, maximum_tasks=1)
    group = BoundedTaskGroup(maximum_workers=1, maximum_tasks=1)
    try:
        with pytest.raises(TypeError, match="TaskContext"):
            group.submit(lambda: None)
        with pytest.raises(ValueError, match="safe identifier"):
            group.submit(lambda context: None, task_id="bad id")
        with pytest.raises(ValueError, match="timeout"):
            group.wait(-1)
    finally:
        group.close(cancel_pending=True)


def test_context_manager_joins_children_and_cancels_them_on_error():
    started = threading.Event()
    finished = threading.Event()

    def child(context):
        started.set()
        context.wait_cancelled(2)
        finished.set()
        context.raise_if_cancelled()

    with pytest.raises(RuntimeError, match="parent failed"):
        with BoundedTaskGroup(maximum_workers=1, maximum_tasks=2) as group:
            handle = group.submit(child)
            assert started.wait(1)
            raise RuntimeError("parent failed")
    assert finished.is_set()
    assert handle.snapshot().state is TaskState.CANCELED
    with pytest.raises(TaskGroupClosedError):
        group.submit(lambda context: None)
