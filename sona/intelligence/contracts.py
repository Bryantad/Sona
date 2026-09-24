"""Data contracts for local model identity and inference.

These interfaces describe intent and data shape only. They do not load models,
enforce resource budgets, grant capabilities, or promise hardware performance.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import StrEnum
from typing import NewType, Protocol


class ModelFormat(StrEnum):
    GGUF = "gguf"


class ModelState(StrEnum):
    OFF = "off"
    LOADING = "loading"
    READY = "ready"
    ACTIVE = "active"
    IDLE = "idle"
    SLEEPING = "sleeping"
    ERROR = "error"


class ResidencyPolicy(StrEnum):
    AUTOMATIC = "automatic"
    WHILE_CODING = "while_coding"
    ALWAYS_LOADED = "always_loaded"
    MANUAL = "manual"


class InferenceState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELING = "canceling"
    CANCELED = "canceled"


_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
InferenceJobId = NewType("InferenceJobId", str)


def new_inference_job_id() -> InferenceJobId:
    return InferenceJobId(str(uuid.uuid4()))


def _validate_safe_id(value: str, name: str) -> None:
    if not _SAFE_ID.fullmatch(value):
        raise ValueError(f"{name} must be a safe identifier")


def _validate_request_id(value: str, name: str) -> None:
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"{name} must be a UUID") from exc


@dataclass(frozen=True, slots=True)
class ModelIdentity:
    """Stable registry identity plus the local artifact/runtime description."""

    model_id: str
    provider_id: str
    runtime_id: str
    format: ModelFormat
    path: str
    context_tokens: int
    sha256: str | None = None
    architecture: str | None = None
    quantization: str | None = None
    device: str = "auto"
    schema_version: int = 1

    def __post_init__(self) -> None:
        for name, value in (
            ("model_id", self.model_id),
            ("provider_id", self.provider_id),
            ("runtime_id", self.runtime_id),
        ):
            _validate_safe_id(value, name)
        if not self.path.strip():
            raise ValueError("model path is required")
        if (
            isinstance(self.context_tokens, bool)
            or not isinstance(self.context_tokens, int)
            or self.context_tokens <= 0
        ):
            raise ValueError("context_tokens must be positive")
        if self.sha256 is not None and not _SHA256.fullmatch(self.sha256):
            raise ValueError("sha256 must contain 64 lowercase hexadecimal characters")
        if isinstance(self.schema_version, bool) or self.schema_version != 1:
            raise ValueError("model identity requires schema_version 1")


@dataclass(frozen=True, slots=True)
class HardwareProfile:
    """Observed host facts; values are not guarantees of runtime capacity."""

    schema_version: int = 1
    cpu_model: str | None = None
    logical_cpu_count: int | None = None
    physical_memory_bytes: int | None = None
    accelerator: str | None = None
    accelerator_name: str | None = None
    accelerator_memory_bytes: int | None = None
    supported_runtimes: tuple[str, ...] = ()
    observed_at_utc: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("logical_cpu_count", self.logical_cpu_count),
            ("physical_memory_bytes", self.physical_memory_bytes),
            ("accelerator_memory_bytes", self.accelerator_memory_bytes),
        ):
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive when provided")
        if self.schema_version != 1:
            raise ValueError("hardware profile requires schema_version 1")
        if len(set(self.supported_runtimes)) != len(self.supported_runtimes):
            raise ValueError("supported runtimes must be unique")
        for runtime_id in self.supported_runtimes:
            _validate_safe_id(runtime_id, "runtime_id")


@dataclass(frozen=True, slots=True)
class InferenceContext:
    """Bounded context prepared by trusted host code for one inference."""

    text: str
    source_count: int = 0
    estimated_tokens: int = 0
    omitted_sources: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.source_count < 0 or self.estimated_tokens < 0:
            raise ValueError("context counts cannot be negative")


@dataclass(frozen=True, slots=True)
class InferenceRequest:
    """In-memory request. Prompts are deliberately not a durable receipt."""

    model_id: str
    prompt: str = field(repr=False)
    context: InferenceContext | None = None
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    maximum_output_tokens: int = 512
    timeout_seconds: float = 60.0

    def __post_init__(self) -> None:
        _validate_safe_id(self.model_id, "model_id")
        _validate_request_id(self.request_id, "request_id")
        if self.maximum_output_tokens <= 0:
            raise ValueError("maximum_output_tokens must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


@dataclass(frozen=True, slots=True)
class InferenceResponse:
    request_id: str
    model_id: str
    provider_id: str
    runtime_id: str
    text: str = field(repr=False)
    runtime_version: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    duration_ms: int | None = None

    def __post_init__(self) -> None:
        _validate_request_id(self.request_id, "request_id")
        _validate_safe_id(self.model_id, "model_id")
        _validate_safe_id(self.provider_id, "provider_id")
        _validate_safe_id(self.runtime_id, "runtime_id")
        for name, value in (
            ("input_tokens", self.input_tokens),
            ("output_tokens", self.output_tokens),
            ("duration_ms", self.duration_ms),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{name} cannot be negative")


@dataclass(frozen=True, slots=True)
class InferenceChunk:
    request_id: str
    sequence: int
    text: str = field(repr=False)
    final: bool = False

    def __post_init__(self) -> None:
        _validate_request_id(self.request_id, "request_id")
        if self.sequence < 0:
            raise ValueError("inference chunk sequence cannot be negative")


class CancellationSignal(Protocol):
    """Cooperative cancellation signal owned by the calling runtime scope."""

    @property
    def cancelled(self) -> bool: ...


class RuntimeAdapter(Protocol):
    """Runtime-specific model loading and execution boundary."""

    runtime_id: str

    def load(self, model: ModelIdentity) -> None: ...

    def infer(
        self, request: InferenceRequest, cancellation: CancellationSignal | None = None
    ) -> InferenceResponse: ...

    def stream(
        self, request: InferenceRequest, cancellation: CancellationSignal | None = None
    ) -> Iterator[InferenceChunk]: ...

    def unload(self, model_id: str) -> None: ...


class LocalModelProvider(Protocol):
    """Explicitly local provider; implementations must not cloud-fallback."""

    provider_id: str

    def infer(
        self, request: InferenceRequest, cancellation: CancellationSignal | None = None
    ) -> InferenceResponse: ...

    def stream(
        self, request: InferenceRequest, cancellation: CancellationSignal | None = None
    ) -> Iterator[InferenceChunk]: ...


class ContextManager(Protocol):
    """Select and bound context before it is passed to a model."""

    def build(self, request: InferenceRequest) -> InferenceContext: ...


class InferenceQueue(Protocol):
    """Queue contract; capacity and cancellation policy belong to its owner."""

    def submit(self, request: InferenceRequest) -> InferenceJobId: ...

    def state(self, job_id: InferenceJobId) -> InferenceState: ...

    def cancel(self, job_id: InferenceJobId) -> bool: ...
