"""Contract tests for Sona 0.16.0 runtime foundations."""

from __future__ import annotations

import uuid

import pytest

from sona.intelligence.contracts import (
    HardwareProfile,
    InferenceState,
    ModelFormat,
    ModelIdentity,
    ModelState,
    ResidencyPolicy,
)
from sona.runtime.contracts import (
    BackpressurePolicy,
    CapabilityScope,
    ChannelDefinition,
    EffectClass,
    EffectOutcome,
    EnforcementStatus,
    HealthState,
    ResourceBudget,
    ResourceLimit,
    ResourceUnit,
    RestartMode,
    RestartPolicy,
    ServiceDefinition,
    ServiceState,
)
from sona.runtime.events import EventEnvelope, EventField, EventSchema, MessageEnvelope
from sona.workflow.contracts import (
    RetryMode,
    RetryPolicy,
    StepDefinition,
    StepState,
    TaskDefinition,
    WorkflowDefinition,
    WorkflowState,
    new_step_id,
    new_task_id,
    new_workflow_id,
)


def test_model_identity_is_model_agnostic_and_versioned():
    identity = ModelIdentity(
        model_id="coder-local",
        provider_id="local",
        runtime_id="llama-cpp",
        format=ModelFormat.GGUF,
        path="models/coder.gguf",
        context_tokens=16_384,
        sha256="a" * 64,
        architecture="generic-causal-lm",
    )
    assert identity.schema_version == 1
    assert identity.format is ModelFormat.GGUF
    assert identity.provider_id == "local"


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"model_id": "../model"}, "safe identifier"),
        ({"path": " "}, "path is required"),
        ({"context_tokens": 0}, "context_tokens must be positive"),
        ({"sha256": "not-a-hash"}, "64 lowercase hexadecimal"),
        ({"schema_version": 2}, "schema_version 1"),
    ],
)
def test_model_identity_rejects_invalid_registry_data(changes, message):
    values = {
        "model_id": "coder-local",
        "provider_id": "local",
        "runtime_id": "llama-cpp",
        "format": ModelFormat.GGUF,
        "path": "models/coder.gguf",
        "context_tokens": 4096,
    }
    values.update(changes)
    with pytest.raises(ValueError, match=message):
        ModelIdentity(**values)


def test_hardware_profile_marks_host_facts_as_observations_by_contract():
    profile = HardwareProfile(
        cpu_model="Example CPU",
        logical_cpu_count=16,
        physical_memory_bytes=32 * 1024**3,
        accelerator="cuda",
        accelerator_memory_bytes=16 * 1024**3,
    )
    assert profile.logical_cpu_count == 16
    with pytest.raises(ValueError, match="must be positive"):
        HardwareProfile(logical_cpu_count=0)


def test_model_residency_and_inference_lifecycle_vocabularies_are_explicit():
    assert {item.value for item in ModelState} == {
        "off",
        "loading",
        "ready",
        "active",
        "idle",
        "sleeping",
        "error",
    }
    assert ResidencyPolicy.AUTOMATIC.value == "automatic"
    assert InferenceState.CANCELING.value == "canceling"
    assert InferenceState.CANCELED.value == "canceled"


def test_workflow_identity_generation_and_lifecycle_contracts():
    workflow_id, task_id, first_id, second_id = (
        new_workflow_id(),
        new_task_id(),
        new_step_id(),
        new_step_id(),
    )
    assert uuid.UUID(str(workflow_id))
    assert uuid.UUID(str(task_id))
    assert first_id != second_id
    definition = WorkflowDefinition(
        workflow_id=workflow_id,
        tasks=(
            TaskDefinition(
                task_id,
                (
                    StepDefinition(first_id, "build"),
                    StepDefinition(second_id, "test", depends_on=(first_id,)),
                ),
            ),
        ),
    )
    assert len(definition.tasks[0].steps) == 2
    assert {state.value for state in WorkflowState} >= {
        "created",
        "ready",
        "running",
        "blocked",
        "retrying",
        "canceling",
        "canceled",
        "succeeded",
        "failed",
    }
    assert StepState.SUCCEEDED.value == "succeeded"


def test_workflow_contract_rejects_duplicate_missing_and_cyclic_dependencies():
    first = new_step_id()
    second = new_step_id()
    workflow_id = new_workflow_id()
    with pytest.raises(ValueError, match="unique"):
        WorkflowDefinition(
            workflow_id,
            (
                TaskDefinition(
                    new_task_id(),
                    (StepDefinition(first, "one"), StepDefinition(first, "duplicate")),
                ),
            ),
        )
    with pytest.raises(ValueError, match="unknown dependencies"):
        WorkflowDefinition(
            workflow_id,
            (TaskDefinition(new_task_id(), (StepDefinition(first, "one", (second,)),)),),
        )
    with pytest.raises(ValueError, match="acyclic"):
        WorkflowDefinition(
            workflow_id,
            (
                TaskDefinition(
                    new_task_id(),
                    (
                        StepDefinition(first, "one", (second,)),
                        StepDefinition(second, "two", (first,)),
                    ),
                ),
            ),
        )
    with pytest.raises(ValueError, match="unique within a task"):
        TaskDefinition(
            new_task_id(),
            (StepDefinition(first, "one"), StepDefinition(first, "duplicate")),
        )


def test_retry_contract_is_bounded_and_has_explicit_modes():
    policy = RetryPolicy(
        RetryMode.EXPONENTIAL, maximum_attempts=3, delay_seconds=1, maximum_delay_seconds=8
    )
    assert policy.maximum_attempts == 3
    with pytest.raises(ValueError, match="exactly one attempt"):
        RetryPolicy(RetryMode.NONE, maximum_attempts=2)
    with pytest.raises(ValueError, match="cannot exceed"):
        RetryPolicy(RetryMode.FIXED, maximum_attempts=2, delay_seconds=9, maximum_delay_seconds=8)


def test_event_schema_validates_identity_fields_types_and_bounded_payload():
    schema = EventSchema(
        "build.completed",
        1,
        (EventField("artifact", "string"), EventField("success", "boolean")),
        maximum_payload_bytes=80,
    )
    event = EventEnvelope(
        "build.completed",
        "builder",
        {"artifact": "sona.exe", "success": True},
        1,
        "2026-09-24T12:00:00Z",
    )
    schema.validate(event)
    with pytest.raises(ValueError, match="missing required"):
        schema.validate_payload({"artifact": "sona.exe"})
    with pytest.raises(ValueError, match="unknown fields"):
        schema.validate_payload({"artifact": "sona.exe", "success": True, "extra": 1})
    with pytest.raises(ValueError, match="must be boolean"):
        schema.validate_payload({"artifact": "sona.exe", "success": 1})
    with pytest.raises(ValueError, match="exceeds maximum"):
        schema.validate_payload({"artifact": "x" * 100, "success": True})
    with pytest.raises(ValueError, match="does not match schema"):
        EventSchema("build.failed", 1, ()).validate(event)
    with pytest.raises(ValueError, match="between 1 and 65536"):
        EventSchema("large", 1, (), maximum_payload_bytes=100_000)


def test_event_and_message_envelopes_require_versioned_identified_json_data():
    event = EventEnvelope(
        "worker.ready", "worker-1", {"ready": True}, 1, "2026-09-24T12:00:00+00:00"
    )
    assert uuid.UUID(event.event_id)
    message = MessageEnvelope("BuildResult", {"success": True})
    assert uuid.UUID(message.message_id)
    with pytest.raises(ValueError, match="timezone"):
        EventEnvelope("worker.ready", "worker-1", {}, 1, "2026-09-24T12:00:00")
    with pytest.raises(ValueError, match="JSON-compatible"):
        MessageEnvelope("BuildResult", {"bad": object()})
    with pytest.raises(ValueError, match="JSON-compatible"):
        MessageEnvelope("BuildResult", {"bad": float("nan")})
    with pytest.raises(ValueError, match="keys must be strings"):
        MessageEnvelope("BuildResult", {1: "bad"})
    with pytest.raises(ValueError, match="65536 bytes"):
        MessageEnvelope("BuildResult", {"body": "x" * 70000})


def test_service_restart_health_and_resource_contracts():
    service = ServiceDefinition(
        "local-model",
        restart_policy=RestartPolicy(RestartMode.BOUNDED, maximum_restarts=3, delay_seconds=2),
    )
    budget = ResourceBudget(
        "worker-budget",
        (
            ResourceLimit("memory", 2 * 1024**3, ResourceUnit.BYTES, EnforcementStatus.OBSERVED),
            ResourceLimit("queue", 32, ResourceUnit.ITEMS, EnforcementStatus.ENFORCED),
        ),
    )
    assert service.restart_policy.maximum_restarts == 3
    assert budget.limits[0].status is EnforcementStatus.OBSERVED
    assert ServiceState.HEALTHY.value == HealthState.HEALTHY.value
    with pytest.raises(ValueError, match="finite positive maximum_restarts"):
        RestartPolicy(RestartMode.BOUNDED)
    with pytest.raises(ValueError, match="finite positive maximum_restarts"):
        RestartPolicy(RestartMode.ON_FAILURE)
    with pytest.raises(ValueError, match="unique"):
        ResourceBudget("duplicate", (budget.limits[0], budget.limits[0]))


def test_effect_and_capability_contracts_keep_outcome_separate_from_scope():
    scope = CapabilityScope(EffectClass.FS_WRITE, "workspace/**")
    assert scope.effect is EffectClass.FS_WRITE
    assert EffectOutcome.DENIED.value == "denied"
    # The scope is data; it does not authorize an operation by itself.
    assert BackpressurePolicy.BLOCK.value == "block"


def test_channel_contract_requires_finite_capacity_and_explicit_backpressure():
    channel = ChannelDefinition("build-results", "BuildResult", 32)
    assert channel.capacity == 32
    assert channel.backpressure is BackpressurePolicy.BLOCK
    with pytest.raises(ValueError, match="capacity must be positive"):
        ChannelDefinition("unbounded", "BuildResult", 0)
