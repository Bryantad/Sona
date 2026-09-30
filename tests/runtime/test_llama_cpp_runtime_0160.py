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
        self.completion_options = []
        self.chat_requests = []

    def tokenize(self, text, add_bos=True, special=False):
        return list(text)

    def create_completion(
        self, *, prompt, max_tokens, stream, stopping_criteria, grammar=None, temperature=None
    ):
        self.prompts.append(prompt)
        self.completion_options.append({"grammar": grammar, "temperature": temperature})
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

    def create_chat_completion(self, *, messages, max_tokens, stream, temperature, grammar=None):
        self.chat_requests.append(
            {
                "messages": messages,
                "max_tokens": max_tokens,
                "stream": stream,
                "temperature": temperature,
                "grammar": grammar,
            }
        )
        return iter([{"choices": [{"delta": {"content": '{"replacement":"print(1);"}'}}]}])

    def close(self):
        self.closed = True


class _FakeBinding:
    __version__ = "test-llama-binding"
    StoppingCriteriaList = _Criteria

    def __init__(self, *, gpu=False):
        self.gpu = gpu
        self.instances = []
        self.grammar_schemas = []
        self.LlamaGrammar = self

    def from_json_schema(self, schema, *, verbose=True):
        self.grammar_schemas.append((schema, verbose))
        return {"json_schema": schema}

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


def _artifact(tmp_path, write_gguf):
    path = tmp_path / "test.gguf"
    return write_gguf(path)


def test_discovery_reports_optional_direct_binding_without_loading_models():
    if importlib.util.find_spec("llama_cpp") is None:
        pytest.skip("optional llama-cpp-python dependency is not installed")
    result = discover_runtime()
    assert result.available is True
    assert result.cpu_supported is True
    assert result.runtime_id == "llama-cpp"


def test_cpu_runtime_loads_once_streams_directly_and_reports_identity(tmp_path, write_gguf):
    artifact = _artifact(tmp_path, write_gguf)
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


def test_runtime_applies_bounded_json_schema_without_changing_default_completion(
    tmp_path, write_gguf
):
    artifact = _artifact(tmp_path, write_gguf)
    binding = _FakeBinding()
    adapter = LlamaCppRuntimeAdapter(module_loader=lambda: binding, monotonic=lambda: 0.0)
    adapter.load(_identity(artifact))
    schema = (
        '{"type":"object","properties":{"replacement":{"type":"string"}},'
        '"required":["replacement"],"additionalProperties":false}'
    )

    adapter.infer(
        InferenceRequest(
            model_id="local-test-model",
            prompt="Return a replacement object.",
            maximum_output_tokens=32,
            output_json_schema=schema,
        )
    )

    assert binding.grammar_schemas == [(schema, False)]
    assert binding.instances[0].completion_options == [
        {"grammar": {"json_schema": schema}, "temperature": 0.0}
    ]
    adapter.unload("local-test-model")


def test_runtime_uses_chat_template_and_streams_constrained_json(tmp_path, write_gguf):
    artifact = _artifact(tmp_path, write_gguf)
    binding = _FakeBinding()
    adapter = LlamaCppRuntimeAdapter(module_loader=lambda: binding, monotonic=lambda: 0.0)
    adapter.load(_identity(artifact))
    schema = (
        '{"type":"object","properties":{"replacement":{"type":"string"}},'
        '"required":["replacement"],"additionalProperties":false}'
    )
    request = InferenceRequest(
        model_id="local-test-model",
        prompt="Change zero to one for this selection.",
        maximum_output_tokens=32,
        output_json_schema=schema,
        system_prompt="Return the complete replacement Sona source as JSON.",
    )

    response = adapter.infer(request)

    assert response.text == '{"replacement":"print(1);"}'
    assert binding.instances[0].prompts == []
    assert binding.instances[0].chat_requests == [
        {
            "messages": [
                {
                    "role": "system",
                    "content": "Return the complete replacement Sona source as JSON.",
                },
                {"role": "user", "content": "Change zero to one for this selection."},
            ],
            "max_tokens": 32,
            "stream": True,
            "temperature": 0.0,
            "grammar": {"json_schema": schema},
        }
    ]
    adapter.unload("local-test-model")


def test_chat_runtime_does_not_start_for_already_canceled_request(tmp_path, write_gguf):
    artifact = _artifact(tmp_path, write_gguf)
    binding = _FakeBinding()
    adapter = LlamaCppRuntimeAdapter(module_loader=lambda: binding, monotonic=lambda: 0.0)
    adapter.load(_identity(artifact))
    request = InferenceRequest(
        model_id="local-test-model",
        prompt="Generate an edit.",
        maximum_output_tokens=32,
        system_prompt="Use the model's native chat template.",
    )

    with pytest.raises(InferenceCancelled, match="was canceled"):
        list(adapter.stream(request, _CancelNow()))

    assert binding.instances[0].chat_requests == []
    adapter.unload("local-test-model")


@pytest.mark.parametrize("schema", ["[]", "not-json", "{}" + " " * (16 * 1024)])
def test_inference_request_rejects_invalid_or_oversized_json_schema(schema):
    with pytest.raises(ValueError, match="output_json_schema"):
        InferenceRequest("local-test-model", "prompt", output_json_schema=schema)


def test_inference_request_rejects_oversized_system_prompt():
    with pytest.raises(ValueError, match="system_prompt"):
        InferenceRequest("local-test-model", "prompt", system_prompt="x" * (16 * 1024 + 1))


def test_cuda_request_fails_before_loading_if_binding_has_no_gpu_support(tmp_path, write_gguf):
    binding = _FakeBinding(gpu=False)
    adapter = LlamaCppRuntimeAdapter(module_loader=lambda: binding)
    with pytest.raises(LocalRuntimeUnavailable, match="does not support GPU offload"):
        adapter.load(_identity(_artifact(tmp_path, write_gguf), device="cuda"))
    assert binding.instances == []


def test_cuda_request_uses_gpu_offload_only_when_binding_confirms_support(tmp_path, write_gguf):
    binding = _FakeBinding(gpu=True)
    adapter = LlamaCppRuntimeAdapter(module_loader=lambda: binding)
    adapter.load(_identity(_artifact(tmp_path, write_gguf), device="cuda"))
    assert binding.instances[0].kwargs["n_gpu_layers"] == -1


def test_registry_hash_is_rechecked_before_loading(tmp_path, write_gguf):
    artifact = _artifact(tmp_path, write_gguf)
    binding = _FakeBinding()
    adapter = LlamaCppRuntimeAdapter(module_loader=lambda: binding)
    with pytest.raises(LocalRuntimeError, match="changed after registry registration"):
        adapter.load(_identity(artifact, sha256="0" * 64))
    assert binding.instances == []


def test_model_context_is_checked_before_inference_and_missing_load_is_rejected(
    tmp_path, write_gguf
):
    binding = _FakeBinding()
    adapter = LlamaCppRuntimeAdapter(module_loader=lambda: binding)
    request = InferenceRequest(
        model_id="local-test-model", prompt="too much", maximum_output_tokens=8
    )
    with pytest.raises(LocalRuntimeError, match="not loaded"):
        list(adapter.stream(request))

    adapter.load(_identity(_artifact(tmp_path, write_gguf), context=8))
    with pytest.raises(LocalRuntimeError, match="exceed the configured model context"):
        list(adapter.stream(request))
    assert binding.instances[0].prompts == []


def test_load_rejects_declared_context_above_model_limit_before_runtime_start(tmp_path, write_gguf):
    artifact = _artifact(tmp_path, write_gguf)
    bindings = []
    adapter = LlamaCppRuntimeAdapter(module_loader=lambda: bindings.append(_FakeBinding()))

    with pytest.raises(LocalRuntimeError, match="context exceeds the GGUF-declared"):
        adapter.load(_identity(artifact, context=16384))

    assert bindings == []


def test_cancelled_and_timed_out_generation_stop_without_returning_partial_text(
    tmp_path, write_gguf
):
    artifact = _artifact(tmp_path, write_gguf)
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
