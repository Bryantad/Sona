"""Lazy provider adapters. Network providers use bounded standard-library HTTP."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Protocol

from .contracts import TaskRequest
from .models import ModelDescriptor


class Provider(Protocol):
    def execute(self, request: TaskRequest, model: ModelDescriptor) -> dict[str, Any]: ...


def _developer_prompt(request: TaskRequest) -> str:
    parts = [f"Developer task: {request.task_type.value}", request.instruction]
    if request.context.active_file:
        parts.append(f"Active file: {request.context.active_file}")
    if request.context.selected_text:
        parts.append("Developer context:\n" + request.context.selected_text)
    return "\n\n".join(parts)


class DeterministicProvider:
    def execute(self, request: TaskRequest, model: ModelDescriptor) -> dict[str, Any]:
        source = request.context.selected_text or ""
        if request.task_type.value == "review" and request.governance_metadata.get("guardian_proof_review"):
            try:
                evidence = json.loads(source)
            except (TypeError, ValueError, json.JSONDecodeError):
                evidence = {}
            execution = evidence.get("execution") if isinstance(evidence, dict) else {}
            guardian = evidence.get("guardian") if isinstance(evidence, dict) else {}
            outcome = "succeeded" if isinstance(execution, dict) and execution.get("status") == "ok" else "failed"
            tracked = isinstance(guardian, dict) and guardian.get("program_baseline") == "tracked"
            attested = bool(evidence.get("local_attestation_recorded")) if isinstance(evidence, dict) else False
            return {
                "summary": (
                    f"Guardian Proof review (local): the verified Native Core execution {outcome}; "
                    f"the program is {'baseline-tracked' if tracked else 'not confirmed as baseline-tracked'}; "
                    f"a local Guardian attestation {'is recorded' if attested else 'is not recorded'}. "
                    "This advisory review does not add signer identity, remote attestation, machine "
                    "integrity, or new trust to the receipt."
                ),
                "status": "ok",
            }
        if request.task_type.value == "explain" and source:
            from .deterministic import explain_source
            return {"summary": "Explanation (local): " + explain_source(source, str(request.governance_metadata.get("style") or "simple")), "status": "ok"}
        if request.task_type.value == "suggest" and source:
            from .deterministic import suggest_source
            return {"summary": suggest_source(source), "status": "ok"}
        files = ", ".join(request.target_files) or request.context.active_file or "the supplied context"
        verb = request.task_type.value.replace("_", " ")
        return {"summary": f"Local deterministic {verb} analysis for {files}.", "status": "ok"}


class OllamaProvider:
    def execute(self, request: TaskRequest, model: ModelDescriptor) -> dict[str, Any]:
        from sona.ai.ollama_integration import OllamaIntegration
        backend = OllamaIntegration(
            model=model.provider_model_name,
            host=model.configuration.get("host"),
            timeout=float(model.configuration.get("timeout", 30.0)),
        )
        values = backend.generate_completion(_developer_prompt(request), max_new_tokens=256)
        text = values[0] if values else ""
        if str(text).startswith("Error:"):
            raise RuntimeError(str(text))
        return {"summary": str(text), "status": "ok"}


class JsonHttpProvider:
    def __init__(self, *, endpoint: str, api_key: str | None = None, timeout: float = 30.0, maximum_response_bytes: int = 2_000_000):
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("provider endpoint must use http or https")
        self.endpoint = endpoint
        self.api_key = api_key
        self.timeout = timeout
        self.maximum_response_bytes = maximum_response_bytes

    def execute(self, request: TaskRequest, model: ModelDescriptor) -> dict[str, Any]:
        payload = json.dumps({"model": model.provider_model_name, "messages": [{"role": "user", "content": _developer_prompt(request)}], "stream": False}).encode()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["api-key"] = self.api_key
        req = urllib.request.Request(self.endpoint, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                body = response.read(self.maximum_response_bytes + 1)
                if len(body) > self.maximum_response_bytes:
                    raise RuntimeError("provider response exceeded the configured byte limit")
                data = json.loads(body.decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise RuntimeError(f"provider request failed: {exc}") from exc
        text = data.get("response")
        if text is None:
            choices = data.get("choices") or []
            text = choices[0].get("message", {}).get("content") if choices else None
        return {"summary": str(text or "Provider returned no content."), "status": "ok", "raw_metadata": {"has_usage": bool(data.get("usage"))}}


class HuggingFaceEndpointProvider:
    """Bounded adapter for an explicitly configured Hugging Face endpoint."""

    def __init__(self, *, endpoint: str, api_key: str | None = None, timeout: float = 30.0, maximum_response_bytes: int = 2_000_000):
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("Hugging Face endpoint must use http or https")
        self.endpoint = endpoint
        self.api_key = api_key
        self.timeout = timeout
        self.maximum_response_bytes = maximum_response_bytes

    def execute(self, request: TaskRequest, model: ModelDescriptor) -> dict[str, Any]:
        payload = json.dumps({"inputs": _developer_prompt(request), "parameters": {"max_new_tokens": 256, "return_full_text": False}}).encode()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(self.endpoint, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                body = response.read(self.maximum_response_bytes + 1)
                if len(body) > self.maximum_response_bytes:
                    raise RuntimeError("Hugging Face response exceeded the configured byte limit")
                data = json.loads(body.decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise RuntimeError(f"Hugging Face endpoint request failed: {exc}") from exc
        if isinstance(data, list) and data:
            text = data[0].get("generated_text") if isinstance(data[0], dict) else data[0]
        elif isinstance(data, dict):
            if data.get("error"):
                raise RuntimeError(f"Hugging Face endpoint error: {data['error']}")
            text = data.get("generated_text")
        else:
            text = None
        return {"summary": str(text or "Provider returned no content."), "status": "ok"}


class HuggingFaceLocalProvider:
    def execute(self, request: TaskRequest, model: ModelDescriptor) -> dict[str, Any]:
        path = Path(model.configuration.get("local_path", ""))
        if not path.exists():
            raise RuntimeError(f"local Hugging Face model path does not exist: {path}")
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        except ImportError as exc:
            raise RuntimeError('Hugging Face local inference requires: pip install "sona-lang[huggingface]"') from exc
        tokenizer = AutoTokenizer.from_pretrained(str(path), local_files_only=True)
        local_model = AutoModelForCausalLM.from_pretrained(str(path), local_files_only=True)
        generator = pipeline("text-generation", model=local_model, tokenizer=tokenizer)
        result = generator(_developer_prompt(request), max_new_tokens=256)
        return {"summary": str(result[0].get("generated_text", "")), "status": "ok"}
