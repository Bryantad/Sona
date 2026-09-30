"""Direct local-model routing used by Sona Guide edit proposals."""

from __future__ import annotations

import hashlib
import json

import pytest

from sona.guide.local_model import GuideLocalModel
from sona.guide.models import GuideError
from sona.guide.service import guide_request
from sona.intelligence import InferenceResponse, ModelFormat, ModelIdentity, ModelState
from sona.intelligence.registry import ModelInspection


class _Registry:
    def __init__(self, identity, *, hash_verified=True):
        self.identity = identity
        self.hash_verified = hash_verified
        self.verify_requests = []

    def get(self, model_id):
        return self.identity if model_id == self.identity.model_id else None

    def default(self):
        return self.identity

    def inspect(self, model_id, *, verify_hash=False):
        self.verify_requests.append(verify_hash)
        return ModelInspection(
            self.identity,
            artifact_exists=True,
            artifact_size_bytes=100,
            format_valid=True,
            expected_sha256=self.identity.sha256,
            hash_verified=self.hash_verified if verify_hash else None,
        )


def _runtime_fakes(monkeypatch, tmp_path, *, hash_verified=True):
    import sona.intelligence as intelligence

    artifact = tmp_path / "fixture.gguf"
    artifact.write_bytes(b"GGUF fixture")
    identity = ModelIdentity(
        model_id="guide-model",
        provider_id="local",
        runtime_id="llama-cpp",
        format=ModelFormat.GGUF,
        path=str(artifact),
        context_tokens=4096,
        sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),
    )
    registry = _Registry(identity, hash_verified=hash_verified)
    services = []

    class FakeService:
        def __init__(self, adapter, *, limits):
            self.state = ModelState.OFF
            self.loaded = []
            self.prompts = []
            self.close_calls = 0
            services.append(self)

        def snapshot(self):
            return type("Snapshot", (), {"model_state": self.state})()

        def load_model(self, model):
            self.loaded.append(model)
            self.state = ModelState.READY

        def infer(self, request):
            self.prompts.append(request)
            return InferenceResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                provider_id="local",
                runtime_id="llama-cpp",
                text='{"replacement":"print(1);"}',
            )

        def close(self, timeout=5.0):
            self.close_calls += 1
            return True

    monkeypatch.setattr(intelligence, "LocalModelRegistry", lambda path: registry)
    monkeypatch.setattr(intelligence, "LocalAIService", FakeService)
    monkeypatch.setattr(intelligence, "LocalAIServiceLimits", lambda **values: values)
    monkeypatch.setattr(intelligence, "LlamaCppRuntimeAdapter", lambda: object())
    return identity, registry, services


def test_guide_direct_local_inference_reuses_resident_service_without_fallback(
    monkeypatch, tmp_path
):
    identity, registry, services = _runtime_fakes(monkeypatch, tmp_path)
    model = GuideLocalModel(registry_path=tmp_path / "models.json")

    first = model.propose_replacement("print(0);", "change the value to one")
    second = model.propose_replacement("print(0);", "change the value to one")

    assert first["provider_id"] == "local"
    assert first["runtime_id"] == "llama-cpp"
    assert first["model_id"] == identity.model_id
    assert first["proposal"] == '{"replacement":"print(1);"}'
    assert second == first
    assert len(services) == 1
    assert len(services[0].loaded) == 1
    assert len(services[0].prompts) == 2
    assert services[0].prompts[0].maximum_output_tokens <= 1024
    assert services[0].prompts[0].context.text == ""
    assert json.loads(services[0].prompts[0].output_json_schema) == {
        "type": "object",
        "properties": {"replacement": {"type": "string"}},
        "required": ["replacement"],
        "additionalProperties": False,
    }
    assert "complete replacement source" in services[0].prompts[0].system_prompt
    assert services[0].prompts[0].prompt.startswith("User edit request:")
    assert "complete replacement source" in services[0].prompts[0].system_prompt
    assert services[0].prompts[0].prompt.startswith("User edit request:")
    assert registry.verify_requests == [True]
    assert model.close() is True
    assert services[0].close_calls == 1


def test_guide_rejects_changed_model_artifact_before_loading(monkeypatch, tmp_path):
    _identity, registry, services = _runtime_fakes(monkeypatch, tmp_path, hash_verified=False)
    model = GuideLocalModel(registry_path=tmp_path / "models.json")

    with pytest.raises(GuideError, match="missing or changed"):
        model.propose_replacement("print(0);", "change the value")
    assert registry.verify_requests == [True]
    assert services == []


def test_guide_local_inference_request_is_injected_and_keeps_result_untrusted(
    monkeypatch,
):
    class FakeInference:
        def propose_replacement(self, source, instruction, *, model_id=None):
            assert source == "print(0);"
            assert instruction == "change the value"
            assert model_id == "guide-model"
            return {
                "schema_version": 1,
                "status": "ok",
                "provider_id": "local",
                "runtime_id": "llama-cpp",
                "model_id": "guide-model",
                "proposal": '{"replacement":"print(1);"}',
            }

    result = guide_request(
        {
            "schema_version": 1,
            "action": "local_model_proposal",
            "document": "file:///workspace/main.sona",
            "source": "print(0);",
            "instruction": "change the value",
            "model_id": "guide-model",
        },
        local_inference=FakeInference(),
    )
    assert result["status"] == "ok"
    assert result["provider_id"] == "local"
    assert "approved" not in result


def test_guide_local_inference_request_fails_closed_when_no_runtime_is_injected():
    result = guide_request(
        {
            "schema_version": 1,
            "action": "local_model_proposal",
            "document": "file:///workspace/main.sona",
            "source": "print(0);",
            "instruction": "change the value",
        }
    )
    assert result["status"] == "unavailable"
    assert result["diagnostic"]["diagnostic_id"] == "SONA-GUIDE-006"
