"""Direct in-process GGUF inference through llama-cpp-python.

This adapter never contacts Ollama or a cloud provider. Cancellation and
generation deadlines are checked by llama.cpp's stopping-criteria callback at
token boundaries. The native library may still spend time in an indivisible
prompt-evaluation operation before the next callback is observed.
"""

from __future__ import annotations

import hashlib
import importlib
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any

from .contracts import (
    CancellationSignal,
    InferenceChunk,
    InferenceRequest,
    InferenceResponse,
    ModelFormat,
    ModelIdentity,
)


class LocalRuntimeError(RuntimeError):
    """A local-runtime failure with a stable, user-facing description."""


class LocalRuntimeUnavailable(LocalRuntimeError):
    """The configured direct runtime is not installed or cannot serve a model."""


class InferenceCancelled(LocalRuntimeError):
    """Inference stopped after cooperative cancellation was observed."""


class InferenceTimeout(LocalRuntimeError):
    """Inference exceeded its cooperative generation deadline."""


@dataclass(frozen=True, slots=True)
class RuntimeDiscovery:
    available: bool
    runtime_id: str = "llama-cpp"
    version: str | None = None
    cpu_supported: bool = False
    gpu_offload_compiled: bool = False
    diagnostic: str | None = None


def discover_runtime() -> RuntimeDiscovery:
    """Inspect the installed binding without loading a model or contacting a service."""
    try:
        module = importlib.import_module("llama_cpp")
    except (ImportError, OSError):
        return RuntimeDiscovery(
            available=False,
            diagnostic=(
                'Install the optional direct runtime with `pip install "sona-lang[llama-cpp]"`.'
            ),
        )
    gpu_probe = getattr(module, "llama_supports_gpu_offload", None)
    try:
        gpu_supported = bool(gpu_probe()) if callable(gpu_probe) else False
    except Exception:
        gpu_supported = False
    return RuntimeDiscovery(
        available=callable(getattr(module, "Llama", None)),
        version=str(getattr(module, "__version__", "unknown")),
        cpu_supported=callable(getattr(module, "Llama", None)),
        gpu_offload_compiled=gpu_supported,
        diagnostic=None
        if callable(getattr(module, "Llama", None))
        else "llama.cpp Python binding is incomplete.",
    )


class LlamaCppRuntimeAdapter:
    """Keep GGUF models resident and invoke llama.cpp directly in this process."""

    runtime_id = "llama-cpp"
    provider_id = "local"

    def __init__(
        self,
        *,
        module_loader: Callable[[], Any] | None = None,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        self._module_loader = module_loader or (lambda: importlib.import_module("llama_cpp"))
        self._monotonic = monotonic or time.monotonic
        self._module: Any | None = None
        self._models: dict[str, tuple[ModelIdentity, Any]] = {}
        self._lock = RLock()

    def _binding(self) -> Any:
        if self._module is not None:
            return self._module
        try:
            self._module = self._module_loader()
        except (ImportError, OSError) as exc:
            raise LocalRuntimeUnavailable(
                "Direct llama.cpp runtime is unavailable; install `sona-lang[llama-cpp]`."
            ) from exc
        return self._module

    def load(self, model: ModelIdentity) -> None:
        if model.runtime_id != self.runtime_id:
            raise LocalRuntimeError("model is configured for a different runtime")
        if model.format is not ModelFormat.GGUF:
            raise LocalRuntimeError("direct llama.cpp runtime requires a GGUF model")
        path = Path(model.path).expanduser()
        try:
            path = path.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise LocalRuntimeError("model artifact path is unavailable") from exc
        if not path.is_file():
            raise LocalRuntimeError("model artifact is not a readable GGUF file")
        try:
            with path.open("rb") as artifact:
                has_gguf_header = artifact.read(4) == b"GGUF"
        except OSError as exc:
            raise LocalRuntimeError("model artifact is not a readable GGUF file") from exc
        if not has_gguf_header:
            raise LocalRuntimeError("model artifact is not a readable GGUF file")
        if model.sha256 is not None:
            digest = hashlib.sha256()
            try:
                with path.open("rb") as artifact:
                    for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
                        digest.update(chunk)
            except OSError as exc:
                raise LocalRuntimeError(
                    "model artifact could not be hashed before loading"
                ) from exc
            if digest.hexdigest() != model.sha256:
                raise LocalRuntimeError(
                    "model artifact SHA-256 changed after registry registration"
                )

        with self._lock:
            existing = self._models.get(model.model_id)
            if existing is not None:
                if existing[0] == model:
                    return
                raise LocalRuntimeError("a different model already uses this model id")
            module = self._binding()
            if model.device == "cpu" or model.device == "auto":
                gpu_layers = 0
            elif model.device == "cuda":
                gpu_probe = getattr(module, "llama_supports_gpu_offload", None)
                try:
                    gpu_available = bool(gpu_probe()) if callable(gpu_probe) else False
                except Exception:
                    gpu_available = False
                if not gpu_available:
                    raise LocalRuntimeUnavailable(
                        "CUDA was requested, but this llama.cpp build does not support GPU offload"
                    )
                gpu_layers = -1
            else:
                raise LocalRuntimeError(f"unsupported llama.cpp device selection: {model.device}")
            try:
                instance = module.Llama(
                    model_path=str(path),
                    n_ctx=model.context_tokens,
                    n_gpu_layers=gpu_layers,
                    verbose=False,
                )
            except Exception as exc:
                raise LocalRuntimeError("llama.cpp could not load the configured model") from exc
            self._models[model.model_id] = (model, instance)

    def unload(self, model_id: str) -> None:
        with self._lock:
            loaded = self._models.pop(model_id, None)
            if loaded is None:
                return
            close = getattr(loaded[1], "close", None)
            if callable(close):
                close()

    def stream(
        self,
        request: InferenceRequest,
        cancellation: CancellationSignal | None = None,
    ) -> Iterator[InferenceChunk]:
        with self._lock:
            loaded = self._models.get(request.model_id)
            if loaded is None:
                raise LocalRuntimeError("model is not loaded in the direct local runtime")
            identity, model = loaded
            prompt = request.prompt
            if request.context is not None and request.context.text:
                prompt = f"{prompt}\n\n{request.context.text}"
            try:
                prompt_tokens = model.tokenize(prompt.encode("utf-8"), add_bos=True, special=False)
            except Exception as exc:
                raise LocalRuntimeError(
                    "llama.cpp could not tokenize the inference prompt"
                ) from exc
            if len(prompt_tokens) + request.maximum_output_tokens > identity.context_tokens:
                raise LocalRuntimeError(
                    "prompt and requested output exceed the configured model context"
                )

            deadline = self._monotonic() + request.timeout_seconds
            if self._monotonic() >= deadline:
                raise InferenceTimeout("local inference exceeded its configured timeout")
            stop_reason: list[str | None] = [None]

            def should_stop(_tokens: Any, _scores: Any) -> bool:
                if cancellation is not None and cancellation.cancelled:
                    stop_reason[0] = "canceled"
                    return True
                if self._monotonic() >= deadline:
                    stop_reason[0] = "timeout"
                    return True
                return False

            criteria_type = getattr(self._binding(), "StoppingCriteriaList", None)
            criteria = criteria_type([should_stop]) if callable(criteria_type) else should_stop
            chunks: Any = None
            sequence = 0
            try:
                chunks = model.create_completion(
                    prompt=prompt_tokens,
                    max_tokens=request.maximum_output_tokens,
                    stream=True,
                    stopping_criteria=criteria,
                )
                for item in chunks:
                    if cancellation is not None and cancellation.cancelled:
                        stop_reason[0] = "canceled"
                        break
                    choices = item.get("choices") if isinstance(item, dict) else None
                    text = (
                        choices[0].get("text", "")
                        if choices and isinstance(choices[0], dict)
                        else ""
                    )
                    if text:
                        yield InferenceChunk(request.request_id, sequence, str(text))
                        sequence += 1
                if stop_reason[0] == "canceled":
                    raise InferenceCancelled("local inference was canceled")
                if stop_reason[0] == "timeout" or self._monotonic() >= deadline:
                    raise InferenceTimeout("local inference exceeded its configured timeout")
            except (InferenceCancelled, InferenceTimeout):
                raise
            except Exception as exc:
                raise LocalRuntimeError("llama.cpp inference failed") from exc
            finally:
                close = getattr(chunks, "close", None)
                if callable(close):
                    close()

    def infer(
        self,
        request: InferenceRequest,
        cancellation: CancellationSignal | None = None,
    ) -> InferenceResponse:
        with self._lock:
            started = self._monotonic()
            text_parts = [chunk.text for chunk in self.stream(request, cancellation)]
            duration_ms = max(0, int((self._monotonic() - started) * 1000))
            loaded = self._models.get(request.model_id)
            if loaded is None:
                raise LocalRuntimeError("model was unloaded during inference")
            identity, model = loaded
            runtime_version = str(getattr(self._binding(), "__version__", "unknown"))
            prompt = request.prompt
            if request.context is not None and request.context.text:
                prompt = f"{prompt}\n\n{request.context.text}"
            input_tokens = len(model.tokenize(prompt.encode("utf-8"), add_bos=True, special=False))
            output_tokens = len(
                model.tokenize("".join(text_parts).encode("utf-8"), add_bos=False, special=False)
            )
        return InferenceResponse(
            request_id=request.request_id,
            model_id=identity.model_id,
            provider_id=self.provider_id,
            runtime_id=self.runtime_id,
            runtime_version=runtime_version,
            text="".join(text_parts),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
        )
