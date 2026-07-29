from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from sona.developer_intelligence import DeveloperIntelligenceService, ModelRegistry, TaskConstraints, TaskRequest, TaskStatus, TaskType
from sona.developer_intelligence.models import descriptor_from_manifest
from sona.developer_intelligence.providers import HuggingFaceEndpointProvider


def _remote_manifest(model_id: str, endpoint: str, *, input_cost=None, output_cost=None):
    return {
        "schema_version": 1,
        "model_id": model_id,
        "provider_id": "huggingface",
        "provider_model_name": "org/model",
        "display_name": "Remote fixture",
        "supported_tasks": ["explain"],
        "capabilities": {"completion": True, "network_required": True, "local_execution": False},
        "privacy": "remote",
        "locality": "remote",
        "enabled": True,
        "input_cost_per_million_usd": input_cost,
        "output_cost_per_million_usd": output_cost,
        "configuration": {"endpoint": endpoint},
    }


def test_explicit_unavailable_model_never_falls_back(tmp_path: Path):
    request = TaskRequest(TaskType.EXPLAIN, "explain this code", model_id="claude:unavailable")
    result = DeveloperIntelligenceService(tmp_path).execute(request, write_task_receipt=False)
    assert result.status is TaskStatus.UNAVAILABLE
    assert result.provider_id is None
    assert "unavailable" in result.summary.lower()
    conflict = TaskRequest(
        TaskType.EXPLAIN, "explain this code", model_id="deterministic:sona",
        provider_id="ollama",
    )
    conflicted = DeveloperIntelligenceService(tmp_path).execute(conflict, write_task_receipt=False)
    assert conflicted.status is TaskStatus.UNAVAILABLE
    assert "does not belong" in conflicted.summary


def test_unknown_remote_cost_requires_approval_and_known_cost_policy_denies(tmp_path: Path):
    registry = ModelRegistry((descriptor_from_manifest(_remote_manifest("hf:remote", "https://fixture.invalid")),))
    request = TaskRequest(
        TaskType.EXPLAIN, "explain this code", model_id="hf:remote",
        constraints=TaskConstraints(allow_network=True),
    )
    result = DeveloperIntelligenceService(tmp_path, registry).execute(request, write_task_receipt=False)
    assert result.status is TaskStatus.APPROVAL_REQUIRED

    (tmp_path / ".sona").mkdir(exist_ok=True)
    policy = json.loads(json.dumps(__import__("sona.developer_intelligence.governance", fromlist=["DEFAULT_POLICY"]).DEFAULT_POLICY))
    policy["limits"]["require_known_cost"] = True
    (tmp_path / ".sona" / "governance.json").write_text(json.dumps(policy), encoding="utf-8")
    approved_request = replace(request, governance_metadata={"approval": {
        "status": "granted", "task_id": request.task_id,
        "capabilities": ["remote_cost", "network_access", "provider:huggingface"],
        "provider_id": "huggingface", "model_id": "hf:remote",
    }})
    denied = DeveloperIntelligenceService(tmp_path, registry).execute(approved_request, write_task_receipt=False)
    assert denied.status is TaskStatus.UNAVAILABLE
    assert "requires known" in denied.summary


def test_workspace_manifest_overrides_user_manifest(tmp_path: Path, monkeypatch):
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace_models = workspace / ".sona" / "models"
    user_models = home / "models"
    workspace_models.mkdir(parents=True)
    user_models.mkdir(parents=True)
    user = _remote_manifest("hf:shared", "https://user.invalid")
    workspace_data = _remote_manifest("hf:shared", "https://workspace.invalid")
    (user_models / "shared.json").write_text(json.dumps(user), encoding="utf-8")
    (workspace_models / "shared.json").write_text(json.dumps(workspace_data), encoding="utf-8")
    monkeypatch.setenv("SONA_HOME", str(home))
    service = DeveloperIntelligenceService(workspace)
    assert service.registry.get("hf:shared").configuration["endpoint"] == "https://workspace.invalid"  # type: ignore[union-attr]


def test_huggingface_endpoint_uses_bounded_standard_library_request(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit=-1):
            return b'[{"generated_text":"result"}]'

    def fake_urlopen(request, timeout):
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    model = descriptor_from_manifest(_remote_manifest("hf:remote", "https://fixture.invalid"))
    response = HuggingFaceEndpointProvider(endpoint="https://fixture.invalid", timeout=2.5).execute(
        TaskRequest(TaskType.EXPLAIN, "explain"), model,
    )
    assert response["summary"] == "result"
    assert captured["timeout"] == 2.5
    assert captured["body"]["parameters"]["max_new_tokens"] == 256
