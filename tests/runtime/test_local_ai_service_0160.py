"""Lifecycle, queue, cancellation, and resource-control tests for local AI."""

from __future__ import annotations

from threading import Event
from time import monotonic, sleep

import pytest

from sona.intelligence.contracts import (
    InferenceChunk,
    InferenceRequest,
    InferenceResponse,
    InferenceState,
    ModelFormat,
    ModelIdentity,
    ModelState,
    ResidencyPolicy,
)
from sona.intelligence.llama_cpp_runtime import InferenceCancelled
from sona.intelligence.service import (
    InferenceQueueFull,
    InferenceWaitTimeout,
    LocalAIService,
    LocalAIServiceError,
    LocalAIServiceLimits,
)
from sona.runtime.contracts import EnforcementStatus, ResourceUnit


def _identity(model_id: str = "service-test-model", *, context: int = 1024) -> ModelIdentity:
    return ModelIdentity(
        model_id=model_id,
        provider_id="local",
        runtime_id="test-runtime",
        format=ModelFormat.GGUF,
        path="not-opened-by-fake-runtime.gguf",
        context_tokens=context,
    )


def _request(model_id: str = "service-test-model", *, output_tokens: int = 64) -> InferenceRequest:
    return InferenceRequest(
        model_id=model_id,
        prompt="Explain a local runtime.",
        maximum_output_tokens=output_tokens,
    )


class _FakeAdapter:
    runtime_id = "test-runtime"
    provider_id = "local"
    runtime_version = "test-1"

    def __init__(self) -> None:
        self.loaded: list[str] = []
        self.unloaded: list[str] = []
        self.entered = Event()
        self.release = Event()
        self.block = False
        self.ignore_cancellation = False
        self.load_failure: Exception | None = None
        self.failure: Exception | None = None
        self.inference_count = 0
        self.unload_failures = 0

    def load(self, model: ModelIdentity) -> None:
        self.loaded.append(model.model_id)
        if self.load_failure is not None:
            failure, self.load_failure = self.load_failure, None
            raise failure

    def unload(self, model_id: str) -> None:
        self.unloaded.append(model_id)
        if self.unload_failures:
            self.unload_failures -= 1
            raise RuntimeError("transient native cleanup failure")

    def infer(self, request: InferenceRequest, cancellation=None) -> InferenceResponse:
        self.inference_count += 1
        self.entered.set()
        if self.block:
            while not self.release.wait(0.01):
                if (
                    cancellation is not None
                    and cancellation.cancelled
                    and not self.ignore_cancellation
                ):
                    raise InferenceCancelled("test inference canceled")
        if self.failure is not None:
            failure, self.failure = self.failure, None
            raise failure
        return InferenceResponse(
            request_id=request.request_id,
            model_id=request.model_id,
            provider_id="local",
            runtime_id=self.runtime_id,
            runtime_version=self.runtime_version,
            text="local result",
        )

    def stream(self, request: InferenceRequest, cancellation=None):
        yield InferenceChunk(request.request_id, 0, "local ")
        yield InferenceChunk(request.request_id, 1, "stream")


def _service(adapter: _FakeAdapter, **kwargs) -> LocalAIService:
    service = LocalAIService(
        adapter,
        limits=kwargs.pop(
            "limits",
            LocalAIServiceLimits(
                pending_jobs=2,
                maximum_model_context_tokens=2048,
                maximum_output_tokens=512,
                idle_timeout_seconds=60,
            ),
        ),
        **kwargs,
    )
    service.load_model(_identity())
    return service


def test_service_limits_reject_unbounded_idle_timeout():
    with pytest.raises(ValueError, match="finite"):
        LocalAIServiceLimits(idle_timeout_seconds=float("inf"))


def test_model_stays_resident_across_requests_and_closes_once():
    adapter = _FakeAdapter()
    service = _service(adapter)
    try:
        first = service.infer(_request())
        second = service.infer(_request())
        assert first.text == second.text == "local result"
        assert adapter.loaded == ["service-test-model"]
        assert adapter.inference_count == 2
        assert service.snapshot().model_state is ModelState.IDLE
    finally:
        assert service.close()
    assert adapter.unloaded == ["service-test-model"]


def test_model_switch_releases_previous_model_before_loading_next():
    adapter = _FakeAdapter()
    service = _service(adapter)
    next_model = _identity("next-local-model")
    try:
        service.load_model(next_model)
        assert adapter.loaded == ["service-test-model", "next-local-model"]
        assert adapter.unloaded == ["service-test-model"]
        assert service.snapshot().active_model_id == "next-local-model"
    finally:
        assert service.close()
    assert adapter.unloaded == ["service-test-model", "next-local-model"]


def test_failed_model_load_is_reported_without_provider_fallback():
    adapter = _FakeAdapter()
    adapter.load_failure = RuntimeError("untrusted binding detail")
    service = LocalAIService(adapter)
    try:
        with pytest.raises(LocalAIServiceError, match="no provider fallback") as failure:
            service.load_model(_identity())
        assert "untrusted binding detail" not in str(failure.value)
        assert service.snapshot().model_state is ModelState.ERROR
        assert adapter.unloaded == ["service-test-model"]
    finally:
        assert service.close()


def test_queue_capacity_is_bounded_and_queued_job_can_be_canceled():
    adapter = _FakeAdapter()
    adapter.block = True
    service = _service(
        adapter,
        limits=LocalAIServiceLimits(
            pending_jobs=1,
            maximum_model_context_tokens=2048,
            maximum_output_tokens=512,
            idle_timeout_seconds=60,
        ),
    )
    first = service.submit(_request())
    assert adapter.entered.wait(1)
    second = service.submit(_request())
    with pytest.raises(InferenceQueueFull, match="at capacity"):
        service.submit(_request())
    assert service.cancel(second) is True
    assert service.state(second) is InferenceState.CANCELED
    adapter.release.set()
    try:
        assert service.wait(first, timeout=1).text == "local result"
        with pytest.raises(InferenceCancelled):
            service.wait(second, timeout=1)
        assert service.snapshot().queue_capacity == 1
    finally:
        assert service.close()


def test_wait_timeout_does_not_cancel_the_inference():
    adapter = _FakeAdapter()
    adapter.block = True
    service = _service(adapter)
    job_id = service.submit(_request())
    assert adapter.entered.wait(1)
    with pytest.raises(InferenceWaitTimeout):
        service.wait(job_id, timeout=0.001)
    assert service.state(job_id) is InferenceState.RUNNING
    adapter.release.set()
    try:
        assert service.wait(job_id, timeout=1).text == "local result"
    finally:
        assert service.close()


def test_running_cancellation_is_cooperative_and_close_releases_model():
    adapter = _FakeAdapter()
    adapter.block = True
    service = _service(adapter)
    job_id = service.submit(_request())
    assert adapter.entered.wait(1)
    assert service.cancel(job_id) is True
    with pytest.raises(InferenceCancelled):
        service.wait(job_id, timeout=1)
    assert service.state(job_id) is InferenceState.CANCELED
    assert service.close()
    assert adapter.unloaded == ["service-test-model"]


def test_non_cooperative_native_work_is_not_force_killed_on_close():
    adapter = _FakeAdapter()
    adapter.block = True
    adapter.ignore_cancellation = True
    service = _service(adapter)
    service.submit(_request())
    assert adapter.entered.wait(1)
    assert service.close(timeout=0.01) is False
    adapter.release.set()
    assert service.close(timeout=0.1) is True
    assert adapter.unloaded == ["service-test-model"]


def test_close_retries_native_cleanup_after_transient_unload_failure():
    adapter = _FakeAdapter()
    adapter.unload_failures = 1
    service = _service(adapter)
    assert service.close() is True
    assert adapter.unloaded == ["service-test-model", "service-test-model"]
    assert service.snapshot().cleanup_error is None


def test_automatic_residency_unloads_after_idle_and_reloads_on_demand():
    adapter = _FakeAdapter()
    service = _service(
        adapter,
        limits=LocalAIServiceLimits(
            pending_jobs=1,
            maximum_model_context_tokens=2048,
            maximum_output_tokens=512,
            idle_timeout_seconds=0.04,
        ),
    )
    try:
        deadline = monotonic() + 1
        while not adapter.unloaded and monotonic() < deadline:
            sleep(0.005)
        assert adapter.unloaded == ["service-test-model"]
        snapshot = service.snapshot()
        assert snapshot.active_model_id is None
        assert snapshot.configured_model_id == "service-test-model"
        assert snapshot.model_state is ModelState.SLEEPING
        assert service.infer(_request()).text == "local result"
        assert adapter.loaded == ["service-test-model", "service-test-model"]
    finally:
        assert service.close()
    assert adapter.unloaded == ["service-test-model", "service-test-model"]


def test_always_loaded_policy_keeps_model_resident_until_close():
    adapter = _FakeAdapter()
    service = _service(
        adapter,
        residency_policy=ResidencyPolicy.ALWAYS_LOADED,
        limits=LocalAIServiceLimits(
            pending_jobs=1,
            maximum_model_context_tokens=2048,
            maximum_output_tokens=512,
            idle_timeout_seconds=0.03,
        ),
    )
    try:
        sleep(0.08)
        assert adapter.unloaded == []
        assert service.snapshot().model_state is ModelState.READY
    finally:
        assert service.close()


def test_while_coding_policy_holds_model_and_then_enters_sleeping_state():
    adapter = _FakeAdapter()
    service = _service(
        adapter,
        residency_policy=ResidencyPolicy.WHILE_CODING,
        limits=LocalAIServiceLimits(
            pending_jobs=1,
            maximum_model_context_tokens=2048,
            maximum_output_tokens=512,
            idle_timeout_seconds=0.04,
        ),
    )
    try:
        service.set_coding_active(True)
        sleep(0.08)
        assert adapter.unloaded == []
        service.set_coding_active(False)
        deadline = monotonic() + 1
        while not adapter.unloaded and monotonic() < deadline:
            sleep(0.005)
        assert adapter.unloaded == ["service-test-model"]
        assert service.snapshot().model_state is ModelState.SLEEPING
    finally:
        assert service.close()


def test_streaming_uses_bounded_worker_and_returns_ordered_chunks():
    adapter = _FakeAdapter()
    service = _service(adapter)
    try:
        chunks = list(service.stream(_request()))
        assert [chunk.text for chunk in chunks] == ["local ", "stream"]
        assert [chunk.sequence for chunk in chunks] == [0, 1]
        assert service.snapshot().model_state is ModelState.IDLE
    finally:
        assert service.close()


def test_runtime_failure_unloads_model_and_requires_explicit_reload():
    adapter = _FakeAdapter()
    service = _service(adapter)
    adapter.failure = RuntimeError("private backend detail")
    try:
        with pytest.raises(LocalAIServiceError, match="resident model was unloaded") as failure:
            service.infer(_request())
        assert "private backend detail" not in str(failure.value)
        snapshot = service.snapshot()
        assert snapshot.active_model_id is None
        assert snapshot.model_state is ModelState.ERROR
        assert adapter.unloaded == ["service-test-model"]
        with pytest.raises(LocalAIServiceError, match="not ready"):
            service.infer(_request())
        service.load_model(_identity())
        assert service.infer(_request()).text == "local result"
    finally:
        assert service.close()


def test_service_enforces_request_and_model_limits_without_fallback():
    adapter = _FakeAdapter()
    service = _service(adapter)
    try:
        with pytest.raises(LocalAIServiceError, match="output exceeds"):
            service.submit(_request(output_tokens=513))
        with pytest.raises(LocalAIServiceError, match="context exceeds"):
            service.load_model(_identity("too-large", context=2049))
        with pytest.raises(LocalAIServiceError, match="explicitly local"):
            service.load_model(
                ModelIdentity(
                    model_id="remote-model",
                    provider_id="remote",
                    runtime_id="test-runtime",
                    format=ModelFormat.GGUF,
                    path="remote.gguf",
                    context_tokens=1024,
                )
            )
        with pytest.raises(LocalAIServiceError, match="not configured"):
            service.submit(_request("remote-model"))
        budget = service.snapshot().resource_budget
        limits = {limit.resource: limit for limit in budget.limits}
        assert limits["queued_inference_jobs"].status is EnforcementStatus.ENFORCED
        assert limits["queued_inference_jobs"].amount == 2
        assert limits["system_memory_bytes"].status is EnforcementStatus.UNSUPPORTED
        assert limits["system_memory_bytes"].amount == 0
        assert limits["system_memory_bytes"].unit is ResourceUnit.BYTES
        assert limits["accelerator_memory_bytes"].status is EnforcementStatus.UNSUPPORTED
    finally:
        assert service.close()


def test_manual_unload_refuses_to_invalidate_queued_work():
    adapter = _FakeAdapter()
    adapter.block = True
    service = _service(adapter)
    service.submit(_request())
    assert adapter.entered.wait(1)
    pending = service.submit(_request())
    with pytest.raises(LocalAIServiceError, match="jobs are pending"):
        service.unload_model("service-test-model")
    adapter.release.set()
    try:
        service.wait(pending, timeout=1)
        service.unload_model("service-test-model")
        assert service.snapshot().model_state is ModelState.OFF
    finally:
        assert service.close()
