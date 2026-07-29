import json

import pytest

from sona.developer_intelligence import (
    DeveloperIntelligenceService,
    ExecutionReceipt,
    ModelRegistry,
    TaskConstraints,
    TaskRequest,
    TaskStatus,
    TaskType,
    VerificationPlan,
)
from sona.developer_intelligence.governance import DEFAULT_POLICY, evaluate, policy_hash, validate_policy
from sona.developer_intelligence.models import descriptor_from_manifest
from sona.developer_intelligence.redaction import redact


def test_task_contract_round_trip_and_deterministic_json():
    request = TaskRequest(TaskType.EXPLAIN, "explain", task_id="task-1")
    payload = request.to_dict()
    restored = TaskRequest.from_dict(payload)
    assert restored == request
    assert request.to_json(canonical=True) == restored.to_json(canonical=True)


def test_verification_plan_and_execution_receipt_contracts_are_serializable():
    plan = VerificationPlan(commands=(("python", "-m", "pytest"),), allowed_prefixes=(("python",),))
    receipt = ExecutionReceipt(
        task_id="task-1",
        prompt_hash="sha256:prompt",
        response_hash="sha256:response",
        metadata={"api_key": "secret-value"},
    )
    assert plan.to_dict()["shell"] is False
    assert receipt.to_dict()["status"] == "ok"
    assert "[redacted]" in receipt.to_json(canonical=True)

    with pytest.raises(ValueError, match="shell=False"):
        VerificationPlan(shell=True)


def test_invalid_task_and_constraints_are_rejected():
    with pytest.raises(ValueError, match="invalid task_type"):
        TaskRequest.from_dict({"task_type": "chat", "instruction": "hello"})
    with pytest.raises(TypeError):
        TaskConstraints(maximum_files="many")  # type: ignore[arg-type]


def test_recursive_redaction_does_not_redact_token_counts():
    data = redact({"api_key": "secret-value", "maximum_context_tokens": 32000, "nested": {"password": "x"}})
    assert data["api_key"] == "[redacted]"
    assert data["maximum_context_tokens"] == 32000
    assert data["nested"]["password"] == "[redacted]"
    assert redact({"AZURE_OPENAI_API_KEY": "secret"})["AZURE_OPENAI_API_KEY"] == "[redacted]"


def test_default_governance_is_deterministic_and_safe():
    validate_policy(DEFAULT_POLICY)
    first = evaluate(DEFAULT_POLICY, source="built-in", task_type="edit", capability="run_shell")
    second = evaluate(DEFAULT_POLICY, source="built-in", task_type="edit", capability="run_shell")
    assert first == second
    assert first.decision == "deny"
    assert first.blocked is True
    remote = evaluate(DEFAULT_POLICY, source="built-in", task_type="explain", provider="azure")
    assert remote.decision == "require_approval"
    assert remote.blocked is False, "missing-policy audit mode must report without enforcing remote approval"
    assert policy_hash(DEFAULT_POLICY) == policy_hash(json.loads(json.dumps(DEFAULT_POLICY)))
    disabled = json.loads(json.dumps(DEFAULT_POLICY))
    disabled["mode"] = "off"
    assert evaluate(disabled, source="test", task_type="edit", capability="read_secrets").blocked is True
    assert evaluate(disabled, source="test", task_type="edit", capability="run_shell").decision == "deny"


def test_registry_rejects_duplicates_and_invalid_manifest():
    registry = ModelRegistry()
    with pytest.raises(ValueError, match="duplicate model id"):
        registry.register(registry.get("deterministic:sona"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="schema_version"):
        descriptor_from_manifest({})
    unsafe = {
        "schema_version": 1, "model_id": "../escape", "provider_id": "custom",
        "provider_model_name": "model", "display_name": "unsafe", "supported_tasks": ["explain"],
    }
    with pytest.raises(ValueError, match="safe identifiers"):
        descriptor_from_manifest(unsafe)
    unsafe["model_id"] = "custom:model"
    unsafe["configuration"] = {"api_key": "plaintext"}
    with pytest.raises(ValueError, match="plaintext credentials"):
        descriptor_from_manifest(unsafe)


def test_service_defaults_to_local_deterministic_and_no_receipt(tmp_path):
    request = TaskRequest(TaskType.SUGGEST, "suggest improvements", task_id="task-2")
    result = DeveloperIntelligenceService(tmp_path).execute(request, write_task_receipt=False)
    assert result.status is TaskStatus.OK
    assert result.provider_id == "deterministic"
    assert result.receipt_path is None
