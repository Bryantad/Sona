"""Offline smoke for a pre-staged GGUF model and optional direct binding.

Set SONA_GGUF_TEST_MODEL and SONA_GGUF_TEST_SHA256 before running this test.
The model must already be present locally; this test never downloads it.
"""

from __future__ import annotations

import os
import socket
from pathlib import Path

import pytest

from sona.intelligence.contracts import InferenceRequest, ModelFormat, ModelIdentity
from sona.intelligence.llama_cpp_runtime import LlamaCppRuntimeAdapter
from sona.intelligence.service import LocalAIService, LocalAIServiceLimits


def test_direct_gguf_inference_works_without_network_or_ollama(monkeypatch):
    pytest.importorskip("llama_cpp")
    model_path = os.environ.get("SONA_GGUF_TEST_MODEL")
    model_hash = os.environ.get("SONA_GGUF_TEST_SHA256")
    if not model_path or not model_hash:
        pytest.skip("pre-staged GGUF path and SHA-256 are not configured")
    assert Path(model_path).is_file()

    def deny_network(*_args, **_kwargs):
        raise AssertionError("direct local inference attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", deny_network)
    monkeypatch.setattr(socket, "create_connection", deny_network)

    model = ModelIdentity(
        model_id="offline-smoke-model",
        provider_id="local",
        runtime_id="llama-cpp",
        format=ModelFormat.GGUF,
        path=model_path,
        context_tokens=128,
        sha256=model_hash,
        device="cpu",
    )
    runtime = LlamaCppRuntimeAdapter()
    runtime.load(model)
    try:
        response = runtime.infer(
            InferenceRequest(
                model_id=model.model_id,
                prompt="Once upon a time,",
                maximum_output_tokens=12,
                timeout_seconds=60,
            )
        )
    finally:
        runtime.unload(model.model_id)

    assert response.text.strip()
    assert response.provider_id == "local"
    assert response.runtime_id == "llama-cpp"


def test_persistent_local_service_reuses_direct_gguf_model_offline(monkeypatch):
    pytest.importorskip("llama_cpp")
    model_path = os.environ.get("SONA_GGUF_TEST_MODEL")
    model_hash = os.environ.get("SONA_GGUF_TEST_SHA256")
    if not model_path or not model_hash:
        pytest.skip("pre-staged GGUF path and SHA-256 are not configured")
    assert Path(model_path).is_file()

    def deny_network(*_args, **_kwargs):
        raise AssertionError("direct local inference attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", deny_network)
    monkeypatch.setattr(socket, "create_connection", deny_network)
    model = ModelIdentity(
        model_id="offline-service-model",
        provider_id="local",
        runtime_id="llama-cpp",
        format=ModelFormat.GGUF,
        path=model_path,
        context_tokens=128,
        sha256=model_hash,
        device="cpu",
    )
    service = LocalAIService(
        LlamaCppRuntimeAdapter(),
        limits=LocalAIServiceLimits(
            pending_jobs=2,
            maximum_model_context_tokens=256,
            maximum_output_tokens=24,
            idle_timeout_seconds=60,
        ),
    )
    service.load_model(model)
    try:
        first = service.infer(
            InferenceRequest(
                model_id=model.model_id,
                prompt="Once upon a time,",
                maximum_output_tokens=12,
                timeout_seconds=60,
            )
        )
        second = service.infer(
            InferenceRequest(
                model_id=model.model_id,
                prompt="There was a small village.",
                maximum_output_tokens=12,
                timeout_seconds=60,
            )
        )
        assert first.text.strip()
        assert second.text.strip()
        assert first.runtime_id == second.runtime_id == "llama-cpp"
        assert service.snapshot().active_model_id == model.model_id
    finally:
        assert service.close()
