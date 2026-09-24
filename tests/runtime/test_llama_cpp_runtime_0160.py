"""Direct-runtime adapter tests that do not require a real model download."""

from __future__ import annotations

import importlib.util
import uuid

import pytest

from sona.intelligence.contracts import (
    InferenceContext,
    InferenceRequest,
    ModelFormat,
    ModelIdentity,
)
from sona.intelligence.llama_cpp_runtime import (
    InferenceCancelled,
    InferenceTimeout,
    LlamaCppRuntimeAdapter,
    LocalRuntimeError,
    LocalRuntimeUnavailable,
    discover_runtime,
)


class _Criteria:
    def __init__(self, callbacks):
        self.callbacks = callbacks

    def __call__(self, tokens, scores):
        return any(callback(tokens, scores) for callback in self.callbacks)


class _FakeModel:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.closed = False
        self.prompts = []

    def tokenize(self, text, add_bos=True, special=False):
        return list(text)

    def create_completion(self, *, prompt, max_tokens, stream, stopping_criteria):
        self.prompts.append(prompt)
        assert stream is True
        assert max_tokens > 0
        if stopping_criteria([1], None):
            return iter(())
        return iter(
            [
                {"choices": [{"text": "Sona "}]},
                {"choices": [{"text": "direct"}]},
            ]
        )

    def close(self):
        self.closed = True


class _FakeBinding:
    __version__ = "test-llama-binding"
    StoppingCriteriaList = _Criteria

    def __init__(self, *, gpu=False):
        self.gpu = gpu
        self.instances = []

    def llama_supports_gpu_offload(self):
        return self.gpu

    def Llama(self, **kwargs):
        model = _FakeModel(**kwargs)
        self.instances.append(model)
        return model


class _CancelNow:
    @property
    def cancelled(self):
        return True


def _identity(path, *, device="cpu", sha256=None, context=8192):
    return ModelIdentity(
        model_id="local-test-model",
        provider_id="local",
        runtime_id="llama-cpp",
        format=ModelFormat.GGUF,
        path=str(path),
        context_tokens=context,
        device=device,
        sha256=sha256,
    )


def _artifact(tmp_path):
    path = tmp_path / "test.gguf"
    path.write_bytes(b"GGUF" + b"fake weights")
    return path


def test_discovery_reports_optional_direct_binding_without_loading_models():
    if importlib.util.find_spec("llama_cpp") is None:
        pytest.skip("optional llama-cpp-python dependency is not installed")
    result = discover_runtime()
    assert result.available is True
    assert result.cpu_supported is True
    assert result.runtime_id == "llama-cpp"


def test_cpu_runtime_loads_once_streams_directly_and_reports_identity(tmp_path):
    artifact = _artifact(tmp_path)
    binding = _FakeBinding()
    adapter = LlamaCppRuntimeAdapter(module_loader=lambda: binding, monotonic=lambda: 0.0)
    adapter.load(_identity(artifact))
    adapter.load(_identity(artifact))

    response = adapter.infer(
        InferenceRequest(
            model_id="local-test-model",
            prompt="Explain Sona",
            context=InferenceContext("Only this selected context."),
            request_id=str(uuid.uuid4()),
        )
    )

    assert response.text == "Sona direct"
    assert response.provider_id == "local"
    assert response.runtime_id == "llama-cpp"
    assert response.runtime_version == "test-llama-binding"
    assert response.input_tokens > 0
    assert response.output_tokens > 0
    assert binding.instances[0].kwargs["n_gpu_layers"] == 0
    assert binding.instances[0].kwargs["verbose"] is False
    assert b"Only this selected context." in bytes(binding.instances[0].prompts[0])
    adapter.unload("local-test-model")
    assert binding.instances[0].closed is True


def test_cuda_request_fails_before_loading_if_binding_has_no_gpu_support(tmp_path):
    binding = _FakeBinding(gpu=False)
    adapter = LlamaCppRuntimeAdapter(module_loader=lambda: binding)
    with pytest.raises(LocalRuntimeUnavailable, match="does not support GPU offload"):
        adapter.load(_identity(_artifact(tmp_path), device="cuda"))
    assert binding.instances == []


def test_cuda_request_uses_gpu_offload_only_when_binding_confirms_support(tmp_path):
    binding = _FakeBinding(gpu=True)
    adapter = LlamaCppRuntimeAdapter(module_loader=lambda: binding)
    adapter.load(_identity(_artifact(tmp_path), device="cuda"))
    assert binding.instances[0].kwargs["n_gpu_layers"] == -1


def test_registry_hash_is_rechecked_before_loading(tmp_path):
    artifact = _artifact(tmp_path)
    binding = _FakeBinding()
    adapter = LlamaCppRuntimeAdapter(module_loader=lambda: binding)
    with pytest.raises(LocalRuntimeError, match="changed after registry registration"):
        adapter.load(_identity(artifact, sha256="0" * 64))
    assert binding.instances == []


def test_model_context_is_checked_before_inference_and_missing_load_is_rejected(tmp_path):
    binding = _FakeBinding()
    adapter = LlamaCppRuntimeAdapter(module_loader=lambda: binding)
    request = InferenceRequest(
        model_id="local-test-model", prompt="too much", maximum_output_tokens=8
    )
    with pytest.raises(LocalRuntimeError, match="not loaded"):
        list(adapter.stream(request))

    adapter.load(_identity(_artifact(tmp_path), context=8))
    with pytest.raises(LocalRuntimeError, match="exceed the configured model context"):
        list(adapter.stream(request))
    assert binding.instances[0].prompts == []


def test_cancelled_and_timed_out_generation_stop_without_returning_partial_text(tmp_path):
    artifact = _artifact(tmp_path)
    cancellation_binding = _FakeBinding()
    cancellation_adapter = LlamaCppRuntimeAdapter(
        module_loader=lambda: cancellation_binding, monotonic=lambda: 0.0
    )
    cancellation_adapter.load(_identity(artifact))
    request = InferenceRequest("local-test-model", "write a response")
    with pytest.raises(InferenceCancelled, match="was canceled"):
        list(cancellation_adapter.stream(request, _CancelNow()))

    values = iter((0.0, 0.0, 1.0))
    timeout_binding = _FakeBinding()
    timeout_adapter = LlamaCppRuntimeAdapter(
        module_loader=lambda: timeout_binding, monotonic=lambda: next(values)
    )
    timeout_adapter.load(_identity(artifact))
    short_request = InferenceRequest("local-test-model", "write a response", timeout_seconds=0.5)
    with pytest.raises(InferenceTimeout, match="configured timeout"):
        list(timeout_adapter.stream(short_request))
