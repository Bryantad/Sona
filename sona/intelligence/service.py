"""Bounded, resident local-model service with explicit lifecycle ownership.

The service is process-local. It serializes access to one resident model, bounds
queued inference and streaming data, and never falls back to another provider.
Host RAM/VRAM isolation is not provided by this Python service.
"""

from __future__ import annotations

import queue
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite
from threading import Event, RLock, Thread

from sona.runtime.contracts import (
    EnforcementStatus,
    ResourceBudget,
    ResourceLimit,
    ResourceUnit,
)

from .contracts import (
    CancellationSignal,
    InferenceChunk,
    InferenceJobId,
    InferenceRequest,
    InferenceResponse,
    InferenceState,
    ModelIdentity,
    ModelState,
    ResidencyPolicy,
    RuntimeAdapter,
    new_inference_job_id,
)
from .llama_cpp_runtime import InferenceCancelled, InferenceTimeout


class LocalAIServiceError(RuntimeError):
    """A service lifecycle, configuration, or request failure."""


class InferenceQueueFull(LocalAIServiceError):
    """The bounded pending-job queue has no capacity for another job."""


class UnknownInferenceJob(LocalAIServiceError):
    """The job is unknown or has aged out of the bounded result history."""


class InferenceWaitTimeout(LocalAIServiceError):
    """Waiting for a local inference job exceeded the caller's wait limit."""


class _ServiceCancellation:
    def __init__(self) -> None:
        self._event = Event()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def cancel(self) -> None:
        self._event.set()


class _StreamEnd(StrEnum):
    END = "end"


_STREAM_END = _StreamEnd.END


@dataclass(frozen=True, slots=True)
class LocalAIServiceLimits:
    """Limits this service can enforce without operating-system isolation."""

    pending_jobs: int = 4
    maximum_model_context_tokens: int = 32768
    maximum_output_tokens: int = 4096
    idle_timeout_seconds: float = 300.0
    stream_buffer_chunks: int = 32
    job_history: int = 256

    def __post_init__(self) -> None:
        for name, value in (
            ("pending_jobs", self.pending_jobs),
            ("maximum_model_context_tokens", self.maximum_model_context_tokens),
            ("maximum_output_tokens", self.maximum_output_tokens),
            ("stream_buffer_chunks", self.stream_buffer_chunks),
            ("job_history", self.job_history),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.job_history < self.pending_jobs + 1:
            raise ValueError("job_history must cover the pending queue and one active job")
        if self.idle_timeout_seconds <= 0:
            raise ValueError("idle_timeout_seconds must be positive")
        if not isfinite(self.idle_timeout_seconds):
            raise ValueError("idle_timeout_seconds must be finite")


@dataclass(frozen=True, slots=True)
class InferenceJobSnapshot:
    job_id: InferenceJobId
    request_id: str
    model_id: str
    state: InferenceState


@dataclass(frozen=True, slots=True)
class LocalAIServiceSnapshot:
    accepting_jobs: bool
    active_model_id: str | None
    configured_model_id: str | None
    model_state: ModelState
    residency_policy: ResidencyPolicy
    active_job_id: InferenceJobId | None
    pending_jobs: int
    queue_capacity: int
    resource_budget: ResourceBudget
    cleanup_error: str | None = None


@dataclass(slots=True)
class _InferenceJob:
    job_id: InferenceJobId
    request: InferenceRequest
    streaming: bool
    state: InferenceState = InferenceState.QUEUED
    cancellation: _ServiceCancellation = field(default_factory=_ServiceCancellation)
    completed: Event = field(default_factory=Event)
    stream_chunks: queue.Queue[InferenceChunk | _StreamEnd] | None = None
    response: InferenceResponse | None = None
    error: Exception | None = None
    finished_at: float | None = None


class LocalAIService:
    """Keep one explicitly configured local model resident across requests.

    Jobs execute on one owned worker thread. Queue capacity limits waiting
    work, and per-job stream buffers are independently bounded. Call ``close``
    or use this object as a context manager to release native model resources.
    """

    provider_id = "local"

    def __init__(
        self,
        adapter: RuntimeAdapter,
        *,
        limits: LocalAIServiceLimits | None = None,
        residency_policy: ResidencyPolicy = ResidencyPolicy.AUTOMATIC,
        monotonic=time.monotonic,
    ) -> None:
        self._adapter = adapter
        self._limits = limits if limits is not None else LocalAIServiceLimits()
        self._residency_policy = residency_policy
        self._clock = monotonic
        self._queue: queue.Queue[_InferenceJob] = queue.Queue(maxsize=self._limits.pending_jobs)
        self._lock = RLock()
        self._runtime_lock = RLock()
        self._jobs: dict[InferenceJobId, _InferenceJob] = {}
        self._model_states: dict[str, ModelState] = {}
        self._active_model: ModelIdentity | None = None
        self._configured_model: ModelIdentity | None = None
        self._active_job_id: InferenceJobId | None = None
        self._last_activity = self._clock()
        self._coding_active = False
        self._accepting_jobs = True
        self._stopping = Event()
        self._closed = False
        self._cleanup_error: str | None = None
        self._cleanup_succeeded = True
        self._worker = Thread(
            target=self._work_loop,
            name="sona-local-ai",
            daemon=True,
        )
        self._worker.start()

    @property
    def runtime_id(self) -> str:
        return self._adapter.runtime_id

    def __enter__(self) -> LocalAIService:
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def load_model(self, model: ModelIdentity) -> None:
        """Load or select a model after enforcing the configured context cap."""
        if model.provider_id != self.provider_id:
            raise LocalAIServiceError(
                "local service accepts only explicitly local model identities"
            )
        if model.runtime_id != self.runtime_id:
            raise LocalAIServiceError("model runtime does not match the configured local adapter")
        if model.context_tokens > self._limits.maximum_model_context_tokens:
            raise LocalAIServiceError("configured model context exceeds the local service limit")
        with self._runtime_lock:
            with self._lock:
                self._ensure_open()
                if self._has_pending_jobs():
                    raise LocalAIServiceError(
                        "cannot change models while inference jobs are pending"
                    )
                if self._active_model == model and self._model_states.get(model.model_id) in (
                    ModelState.READY,
                    ModelState.IDLE,
                ):
                    return
                previous = self._active_model
                if previous is not None:
                    self._model_states[previous.model_id] = ModelState.LOADING
                elif (
                    self._configured_model is not None
                    and self._configured_model.model_id != model.model_id
                ):
                    self._model_states[self._configured_model.model_id] = ModelState.OFF
                self._configured_model = model
                self._model_states[model.model_id] = ModelState.LOADING

            if previous is not None:
                try:
                    self._adapter.unload(previous.model_id)
                except Exception as exc:
                    with self._lock:
                        self._configured_model = previous
                        self._model_states[previous.model_id] = ModelState.ERROR
                        if model.model_id != previous.model_id:
                            self._model_states[model.model_id] = ModelState.ERROR
                    self._record_cleanup_error(exc)
                    raise LocalAIServiceError(
                        "previous local model could not be released; replacement was not loaded"
                    ) from exc
                with self._lock:
                    self._active_model = None
                    self._model_states[previous.model_id] = ModelState.OFF
                    self._cleanup_error = None
                    self._cleanup_succeeded = True

            try:
                self._adapter.load(model)
            except Exception as exc:
                try:
                    self._adapter.unload(model.model_id)
                except Exception as cleanup_exc:
                    self._record_cleanup_error(cleanup_exc)
                    with self._lock:
                        self._active_model = model
                with self._lock:
                    self._model_states[model.model_id] = ModelState.ERROR
                    self._last_activity = self._clock()
                if isinstance(exc, LocalAIServiceError):
                    raise
                raise LocalAIServiceError(
                    "local model could not be loaded; no provider fallback was attempted"
                ) from exc

            with self._lock:
                self._active_model = model
                self._model_states[model.model_id] = ModelState.READY
                self._last_activity = self._clock()

    def unload_model(self, model_id: str) -> None:
        """Unload the active model; queued requests must be drained first."""
        with self._lock:
            self._ensure_open()
            if self._has_pending_jobs(model_id=model_id):
                raise LocalAIServiceError(
                    "cannot unload a model while its inference jobs are pending"
                )
        with self._runtime_lock:
            with self._lock:
                self._ensure_open()
                if self._has_pending_jobs(model_id=model_id):
                    raise LocalAIServiceError(
                        "cannot unload a model while its inference jobs are pending"
                    )
                model = self._active_model
                configured = self._configured_model
                if configured is None or configured.model_id != model_id:
                    return
                if model is not None and model.model_id != model_id:
                    return
                if model is not None:
                    self._model_states[model_id] = ModelState.LOADING
            try:
                if model is not None:
                    self._adapter.unload(model_id)
            except Exception as exc:
                with self._lock:
                    self._model_states[model_id] = ModelState.ERROR
                self._record_cleanup_error(exc)
                raise LocalAIServiceError("local model cleanup failed") from exc
            with self._lock:
                self._active_model = None
                self._configured_model = None
                self._model_states[model_id] = ModelState.OFF
                self._last_activity = self._clock()
                self._cleanup_error = None
                self._cleanup_succeeded = True

    def set_coding_active(self, active: bool) -> None:
        """Update the activity signal used by the while-coding residency mode."""
        if not isinstance(active, bool):
            raise ValueError("active must be a boolean")
        with self._lock:
            self._ensure_open()
            was_active = self._coding_active
            self._coding_active = active
            if was_active and not active:
                self._last_activity = self._clock()

    def submit(self, request: InferenceRequest) -> InferenceJobId:
        return self._submit(request, streaming=False).job_id

    def state(self, job_id: InferenceJobId) -> InferenceState:
        return self._find_job(job_id).state

    def cancel(self, job_id: InferenceJobId) -> bool:
        job = self._find_job(job_id)
        with self._lock:
            if job.state not in (
                InferenceState.QUEUED,
                InferenceState.RUNNING,
                InferenceState.CANCELING,
            ):
                return False
            job.cancellation.cancel()
            if job.state is InferenceState.QUEUED:
                job.state = InferenceState.CANCELED
                job.finished_at = self._clock()
                job.completed.set()
            else:
                job.state = InferenceState.CANCELING
            return True

    def wait(self, job_id: InferenceJobId, timeout: float | None = None) -> InferenceResponse:
        job = self._find_job(job_id)
        if timeout is not None and (timeout < 0 or not isfinite(timeout)):
            raise ValueError("wait timeout must be finite and non-negative")
        if not job.completed.wait(timeout):
            raise InferenceWaitTimeout("local inference is still running")
        return self._result(job)

    def infer(
        self,
        request: InferenceRequest,
        cancellation: CancellationSignal | None = None,
    ) -> InferenceResponse:
        job = self._submit(request, streaming=False)
        while not job.completed.wait(0.05):
            if cancellation is not None and cancellation.cancelled:
                self.cancel(job.job_id)
        if cancellation is not None and cancellation.cancelled:
            self.cancel(job.job_id)
        return self._result(job)

    def stream(
        self,
        request: InferenceRequest,
        cancellation: CancellationSignal | None = None,
    ) -> Iterator[InferenceChunk]:
        job = self._submit(request, streaming=True)
        assert job.stream_chunks is not None
        try:
            while True:
                if cancellation is not None and cancellation.cancelled:
                    self.cancel(job.job_id)
                try:
                    chunk = job.stream_chunks.get(timeout=0.05)
                except queue.Empty:
                    if job.completed.is_set() and job.stream_chunks.empty():
                        break
                    continue
                if chunk is _STREAM_END:
                    break
                if not job.cancellation.cancelled:
                    yield chunk
            self._result(job)
        finally:
            if not job.completed.is_set():
                self.cancel(job.job_id)

    def snapshot(self) -> LocalAIServiceSnapshot:
        with self._lock:
            active_model = self._active_model
            state = (
                self._model_states.get(active_model.model_id, ModelState.OFF)
                if active_model is not None
                else self._model_states.get(
                    self._configured_model.model_id if self._configured_model is not None else "",
                    self._most_recent_model_state(),
                )
            )
            return LocalAIServiceSnapshot(
                accepting_jobs=self._accepting_jobs,
                active_model_id=active_model.model_id if active_model is not None else None,
                configured_model_id=(
                    self._configured_model.model_id if self._configured_model is not None else None
                ),
                model_state=state,
                residency_policy=self._residency_policy,
                active_job_id=self._active_job_id,
                pending_jobs=self._queue.qsize(),
                queue_capacity=self._limits.pending_jobs,
                resource_budget=self._resource_budget(),
                cleanup_error=self._cleanup_error,
            )

    def jobs(self) -> tuple[InferenceJobSnapshot, ...]:
        with self._lock:
            return tuple(
                InferenceJobSnapshot(
                    job.job_id, job.request.request_id, job.request.model_id, job.state
                )
                for job in self._jobs.values()
            )

    def close(self, timeout: float = 5.0) -> bool:
        """Stop accepting work, cooperatively cancel jobs, and release the model.

        Returns false if native inference did not stop before ``timeout`` or
        native cleanup failed. The Python thread is not force-killed.
        """
        if timeout < 0 or not isfinite(timeout):
            raise ValueError("close timeout must be finite and non-negative")
        with self._lock:
            if not self._closed:
                self._accepting_jobs = False
                self._stopping.set()
                for job in self._jobs.values():
                    if job.state is InferenceState.QUEUED:
                        job.cancellation.cancel()
                        job.state = InferenceState.CANCELED
                        job.finished_at = self._clock()
                        job.completed.set()
                    elif job.state in (InferenceState.RUNNING, InferenceState.CANCELING):
                        job.cancellation.cancel()
                        job.state = InferenceState.CANCELING
        self._worker.join(timeout)
        if self._worker.is_alive():
            return False
        if not self._cleanup_succeeded:
            self._retry_native_cleanup()
        return self._cleanup_succeeded

    def _submit(self, request: InferenceRequest, *, streaming: bool) -> _InferenceJob:
        with self._lock:
            self._ensure_open()
            model = self._configured_model
            if model is None or model.model_id != request.model_id:
                raise LocalAIServiceError("requested model is not configured for the local service")
            if self._model_states.get(model.model_id) not in (
                ModelState.READY,
                ModelState.IDLE,
                ModelState.ACTIVE,
                ModelState.SLEEPING,
            ):
                raise LocalAIServiceError("configured local model is not ready")
            if request.maximum_output_tokens > self._limits.maximum_output_tokens:
                raise LocalAIServiceError("requested output exceeds the local service token limit")
            if request.maximum_output_tokens > model.context_tokens:
                raise LocalAIServiceError("requested output exceeds the resident model context")
            if (
                request.context is not None
                and request.context.estimated_tokens > self._limits.maximum_model_context_tokens
            ):
                raise LocalAIServiceError("prepared context exceeds the local service token limit")
            self._trim_job_history()
            job = _InferenceJob(
                job_id=new_inference_job_id(),
                request=request,
                streaming=streaming,
                stream_chunks=(
                    queue.Queue(maxsize=self._limits.stream_buffer_chunks) if streaming else None
                ),
            )
            self._jobs[job.job_id] = job
            try:
                self._queue.put_nowait(job)
            except queue.Full as exc:
                del self._jobs[job.job_id]
                raise InferenceQueueFull("local inference queue is at capacity") from exc
            return job

    def _work_loop(self) -> None:
        try:
            while True:
                if self._stopping.is_set() and self._queue.empty():
                    break
                try:
                    job = self._queue.get(timeout=self._next_poll_seconds())
                except queue.Empty:
                    self._unload_if_idle()
                    continue
                try:
                    self._run_job(job)
                finally:
                    self._queue.task_done()
        finally:
            self._cleanup_runtime()

    def _run_job(self, job: _InferenceJob) -> None:
        with self._runtime_lock:
            with self._lock:
                if job.completed.is_set() or job.cancellation.cancelled or self._stopping.is_set():
                    self._finish_job(job, state=InferenceState.CANCELED)
                    self._signal_stream_end(job)
                    return
                model = self._configured_model
                if model is None or model.model_id != job.request.model_id:
                    self._finish_job(
                        job,
                        state=InferenceState.FAILED,
                        error=LocalAIServiceError(
                            "configured local model changed before job execution"
                        ),
                    )
                    self._signal_stream_end(job)
                    return
                self._active_job_id = job.job_id
                job.state = InferenceState.RUNNING

            try:
                if self._active_model is None:
                    with self._lock:
                        self._model_states[model.model_id] = ModelState.LOADING
                    self._adapter.load(model)
                    with self._lock:
                        self._active_model = model
                        self._model_states[model.model_id] = ModelState.READY
                with self._lock:
                    self._model_states[model.model_id] = ModelState.ACTIVE
            except Exception:
                self._unload_after_failure(model)
                self._finish_job(
                    job,
                    state=InferenceState.FAILED,
                    error=LocalAIServiceError(
                        "configured local model could not be resumed; "
                        "no provider fallback was attempted"
                    ),
                )
                with self._lock:
                    self._active_job_id = None
                self._signal_stream_end(job)
                return

            started = self._clock()
            try:
                if job.streaming:
                    response = self._run_stream_job(job, model, started)
                else:
                    response = self._adapter.infer(job.request, job.cancellation)
                    self._validate_response(job.request, response)
                if job.cancellation.cancelled or self._stopping.is_set():
                    self._finish_job(job, state=InferenceState.CANCELED)
                else:
                    self._finish_job(job, state=InferenceState.SUCCEEDED, response=response)
            except InferenceCancelled:
                self._finish_job(job, state=InferenceState.CANCELED)
            except InferenceTimeout as exc:
                self._finish_job(job, state=InferenceState.FAILED, error=exc)
            except Exception:
                self._unload_after_failure(model)
                self._finish_job(
                    job,
                    state=InferenceState.FAILED,
                    error=LocalAIServiceError(
                        "local inference failed; the resident model was unloaded"
                    ),
                )
            finally:
                with self._lock:
                    self._active_job_id = None
                    if self._active_model is not None:
                        state = self._model_states.get(self._active_model.model_id)
                        if state is ModelState.ACTIVE:
                            self._model_states[self._active_model.model_id] = ModelState.IDLE
                    self._last_activity = self._clock()
                self._signal_stream_end(job)

    def _run_stream_job(
        self, job: _InferenceJob, model: ModelIdentity, started: float
    ) -> InferenceResponse:
        chunks: list[InferenceChunk] = []
        for expected_sequence, chunk in enumerate(
            self._adapter.stream(job.request, job.cancellation)
        ):
            if chunk.request_id != job.request.request_id or chunk.sequence != expected_sequence:
                raise LocalAIServiceError("runtime produced a malformed inference stream")
            if job.cancellation.cancelled:
                raise InferenceCancelled("local inference was canceled")
            self._publish_stream_chunk(job, chunk)
            chunks.append(chunk)
        response = InferenceResponse(
            request_id=job.request.request_id,
            model_id=model.model_id,
            provider_id=getattr(self._adapter, "provider_id", "local"),
            runtime_id=self._adapter.runtime_id,
            runtime_version=getattr(self._adapter, "runtime_version", None),
            text="".join(chunk.text for chunk in chunks),
            duration_ms=max(0, int((self._clock() - started) * 1000)),
        )
        return response

    @staticmethod
    def _validate_response(request: InferenceRequest, response: InferenceResponse) -> None:
        if response.request_id != request.request_id or response.model_id != request.model_id:
            raise LocalAIServiceError("runtime response identity does not match its request")
        if response.provider_id != "local":
            raise LocalAIServiceError("local service rejected a non-local runtime response")

    def _publish_stream_chunk(self, job: _InferenceJob, chunk: InferenceChunk) -> None:
        assert job.stream_chunks is not None
        while not job.cancellation.cancelled:
            try:
                job.stream_chunks.put(chunk, timeout=0.05)
                return
            except queue.Full:
                if self._stopping.is_set():
                    break
        raise InferenceCancelled("local inference stream was canceled")

    def _signal_stream_end(self, job: _InferenceJob) -> None:
        stream_queue = job.stream_chunks
        if stream_queue is None:
            return
        while not job.cancellation.cancelled:
            try:
                stream_queue.put(_STREAM_END, timeout=0.05)
                return
            except queue.Full:
                if self._stopping.is_set():
                    return

    def _finish_job(
        self,
        job: _InferenceJob,
        *,
        state: InferenceState,
        response: InferenceResponse | None = None,
        error: Exception | None = None,
    ) -> None:
        with self._lock:
            if job.completed.is_set():
                return
            job.state = state
            job.response = response
            job.error = error
            job.finished_at = self._clock()
            job.completed.set()
            self._trim_job_history()

    def _unload_after_failure(self, model: ModelIdentity) -> None:
        unloaded = False
        try:
            self._adapter.unload(model.model_id)
            unloaded = True
        except Exception as exc:
            self._record_cleanup_error(exc)
        with self._lock:
            if unloaded and self._active_model == model:
                self._active_model = None
            self._model_states[model.model_id] = ModelState.ERROR
            if unloaded:
                self._cleanup_error = None
                self._cleanup_succeeded = True

    def _unload_if_idle(self) -> None:
        if self._residency_policy not in (
            ResidencyPolicy.AUTOMATIC,
            ResidencyPolicy.WHILE_CODING,
        ):
            return
        with self._runtime_lock:
            with self._lock:
                model = self._active_model
                if model is None or self._queue.qsize() > 0:
                    return
                if self._residency_policy is ResidencyPolicy.WHILE_CODING and self._coding_active:
                    return
                if self._model_states.get(model.model_id) not in (
                    ModelState.READY,
                    ModelState.IDLE,
                ):
                    return
                if self._clock() - self._last_activity < self._limits.idle_timeout_seconds:
                    return
                self._model_states[model.model_id] = ModelState.LOADING
            try:
                self._adapter.unload(model.model_id)
            except Exception as exc:
                with self._lock:
                    self._model_states[model.model_id] = ModelState.ERROR
                self._record_cleanup_error(exc)
                return
            with self._lock:
                self._active_model = None
                self._model_states[model.model_id] = ModelState.SLEEPING
                self._last_activity = self._clock()
                self._cleanup_error = None
                self._cleanup_succeeded = True

    def _next_poll_seconds(self) -> float:
        if self._residency_policy in (ResidencyPolicy.AUTOMATIC, ResidencyPolicy.WHILE_CODING):
            with self._lock:
                if self._active_model is not None and not (
                    self._residency_policy is ResidencyPolicy.WHILE_CODING and self._coding_active
                ):
                    remaining = self._limits.idle_timeout_seconds - (
                        self._clock() - self._last_activity
                    )
                    return max(0.01, min(0.1, remaining))
        return 0.1

    def _cleanup_runtime(self) -> None:
        with self._runtime_lock:
            with self._lock:
                model = self._active_model
                configured = self._configured_model
                self._active_job_id = None
            if model is not None:
                try:
                    self._adapter.unload(model.model_id)
                except Exception as exc:
                    self._cleanup_succeeded = False
                    self._record_cleanup_error(exc)
                else:
                    with self._lock:
                        self._active_model = None
                        self._model_states[model.model_id] = ModelState.OFF
                        self._cleanup_error = None
                        self._cleanup_succeeded = True
            if model is None and configured is not None:
                with self._lock:
                    self._model_states[configured.model_id] = ModelState.OFF
            with self._lock:
                self._configured_model = None
                self._jobs.clear()
                self._closed = True

    def _retry_native_cleanup(self) -> None:
        with self._runtime_lock:
            with self._lock:
                model = self._active_model
            if model is None:
                return
            try:
                self._adapter.unload(model.model_id)
            except Exception as exc:
                self._record_cleanup_error(exc)
                return
            with self._lock:
                self._active_model = None
                self._model_states[model.model_id] = ModelState.OFF
                self._cleanup_error = None
                self._cleanup_succeeded = True

    def _resource_budget(self) -> ResourceBudget:
        return ResourceBudget(
            budget_id="local-ai-service",
            limits=(
                ResourceLimit(
                    "queued_inference_jobs",
                    self._limits.pending_jobs,
                    ResourceUnit.ITEMS,
                    EnforcementStatus.ENFORCED,
                ),
                ResourceLimit(
                    "inference_concurrency",
                    1,
                    ResourceUnit.ITEMS,
                    EnforcementStatus.ENFORCED,
                ),
                ResourceLimit(
                    "model_context_tokens",
                    self._limits.maximum_model_context_tokens,
                    ResourceUnit.TOKENS,
                    EnforcementStatus.ENFORCED,
                ),
                ResourceLimit(
                    "output_tokens_per_request",
                    self._limits.maximum_output_tokens,
                    ResourceUnit.TOKENS,
                    EnforcementStatus.ENFORCED,
                ),
                ResourceLimit(
                    "system_memory_bytes",
                    0,
                    ResourceUnit.BYTES,
                    EnforcementStatus.UNSUPPORTED,
                ),
                ResourceLimit(
                    "accelerator_memory_bytes",
                    0,
                    ResourceUnit.BYTES,
                    EnforcementStatus.UNSUPPORTED,
                ),
            ),
        )

    def _trim_job_history(self) -> None:
        limit = self._limits.job_history
        while len(self._jobs) >= limit:
            oldest_id = next(iter(self._jobs))
            oldest = self._jobs[oldest_id]
            if not oldest.completed.is_set():
                break
            del self._jobs[oldest_id]

    def _has_pending_jobs(self, *, model_id: str | None = None) -> bool:
        return any(
            job.state in (InferenceState.QUEUED, InferenceState.RUNNING, InferenceState.CANCELING)
            and (model_id is None or job.request.model_id == model_id)
            for job in self._jobs.values()
        )

    def _find_job(self, job_id: InferenceJobId) -> _InferenceJob:
        with self._lock:
            try:
                return self._jobs[job_id]
            except KeyError as exc:
                raise UnknownInferenceJob("inference job is unknown or no longer retained") from exc

    def _result(self, job: _InferenceJob) -> InferenceResponse:
        if job.state is InferenceState.CANCELED:
            raise InferenceCancelled("local inference was canceled")
        if job.error is not None:
            raise job.error
        if job.response is None:
            raise LocalAIServiceError("inference job completed without a response")
        return job.response

    def _most_recent_model_state(self) -> ModelState:
        if not self._model_states:
            return ModelState.OFF
        return next(reversed(self._model_states.values()))

    def _ensure_open(self) -> None:
        if not self._accepting_jobs or self._closed:
            raise LocalAIServiceError("local AI service is closing or closed")

    def _record_cleanup_error(self, error: Exception) -> None:
        with self._lock:
            self._cleanup_succeeded = False
            self._cleanup_error = type(error).__name__
