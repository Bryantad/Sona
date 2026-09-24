"""Data-only workflow identity, lifecycle, and dependency contracts."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from typing import NewType

WorkflowId = NewType("WorkflowId", str)
TaskId = NewType("TaskId", str)
StepId = NewType("StepId", str)


def _new_id() -> str:
    return str(uuid.uuid4())


def new_workflow_id() -> WorkflowId:
    return WorkflowId(_new_id())


def new_task_id() -> TaskId:
    return TaskId(_new_id())


def new_step_id() -> StepId:
    return StepId(_new_id())


def _validate_uuid(value: str, name: str) -> None:
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"{name} must be a UUID") from exc


class WorkflowState(StrEnum):
    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    RETRYING = "retrying"
    CANCELING = "canceling"
    CANCELED = "canceled"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TaskState(StrEnum):
    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    RETRYING = "retrying"
    CANCELING = "canceling"
    CANCELED = "canceled"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class StepState(StrEnum):
    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    RETRYING = "retrying"
    CANCELING = "canceling"
    CANCELED = "canceled"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class RetryMode(StrEnum):
    NONE = "none"
    FIXED = "fixed"
    EXPONENTIAL = "exponential"


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    mode: RetryMode = RetryMode.NONE
    maximum_attempts: int = 1
    delay_seconds: float = 0.0
    maximum_delay_seconds: float = 60.0

    def __post_init__(self) -> None:
        if (
            isinstance(self.maximum_attempts, bool)
            or not isinstance(self.maximum_attempts, int)
            or not 1 <= self.maximum_attempts <= 1000
        ):
            raise ValueError("maximum_attempts must be between one and 1000")
        if self.mode is not RetryMode.NONE and not isinstance(self.mode, RetryMode):
            raise ValueError("retry mode is unsupported")
        if self.mode is RetryMode.NONE and self.maximum_attempts != 1:
            raise ValueError("retry mode none requires exactly one attempt")
        delays = (self.delay_seconds, self.maximum_delay_seconds)
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
            or value < 0
            for value in delays
        ):
            raise ValueError("retry delays cannot be negative")
        if self.delay_seconds > self.maximum_delay_seconds:
            raise ValueError("delay_seconds cannot exceed maximum_delay_seconds")


@dataclass(frozen=True, slots=True)
class StepDefinition:
    step_id: StepId
    operation: str
    depends_on: tuple[StepId, ...] = ()
    retry: RetryPolicy = RetryPolicy()
    timeout_seconds: float | None = None

    def __post_init__(self) -> None:
        _validate_uuid(str(self.step_id), "step_id")
        for dependency in self.depends_on:
            _validate_uuid(str(dependency), "dependency step_id")
        if not self.operation.strip():
            raise ValueError("step operation is required")
        if self.step_id in self.depends_on:
            raise ValueError("a step cannot depend on itself")
        if len(set(self.depends_on)) != len(self.depends_on):
            raise ValueError("step dependencies must be unique")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("step timeout must be positive")


@dataclass(frozen=True, slots=True)
class TaskDefinition:
    task_id: TaskId
    steps: tuple[StepDefinition, ...]
    schema_version: int = 1

    def __post_init__(self) -> None:
        _validate_uuid(str(self.task_id), "task_id")
        if not self.steps:
            raise ValueError("task must contain at least one step")
        if self.schema_version != 1:
            raise ValueError("task definition requires schema_version 1")
        step_ids = [step.step_id for step in self.steps]
        if len(set(step_ids)) != len(step_ids):
            raise ValueError("step ids must be unique within a task")


@dataclass(frozen=True, slots=True)
class WorkflowDefinition:
    workflow_id: WorkflowId
    tasks: tuple[TaskDefinition, ...]
    schema_version: int = 1

    def __post_init__(self) -> None:
        _validate_uuid(str(self.workflow_id), "workflow_id")
        if not self.tasks:
            raise ValueError("workflow must contain at least one task")
        if self.schema_version != 1:
            raise ValueError("workflow definition requires schema_version 1")
        task_ids = [task.task_id for task in self.tasks]
        if len(set(task_ids)) != len(task_ids):
            raise ValueError("task ids must be unique within a workflow")
        steps = tuple(step for task in self.tasks for step in task.steps)
        ids = [step.step_id for step in steps]
        if len(set(ids)) != len(ids):
            raise ValueError("step ids must be unique within a workflow")
        known = set(ids)
        for step in steps:
            missing = set(step.depends_on) - known
            if missing:
                raise ValueError(
                    f"step has unknown dependencies: {', '.join(sorted(map(str, missing)))}"
                )
        self._validate_acyclic(steps)

    @staticmethod
    def _validate_acyclic(steps: tuple[StepDefinition, ...]) -> None:
        dependencies = {step.step_id: step.depends_on for step in steps}
        visiting: set[StepId] = set()
        visited: set[StepId] = set()

        def visit(step_id: StepId) -> None:
            if step_id in visiting:
                raise ValueError("workflow dependencies must be acyclic")
            if step_id in visited:
                return
            visiting.add(step_id)
            for dependency in dependencies[step_id]:
                visit(dependency)
            visiting.remove(step_id)
            visited.add(step_id)

        for step_id in dependencies:
            visit(step_id)
