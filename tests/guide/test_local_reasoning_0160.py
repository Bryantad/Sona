"""Local AI augments Guide without becoming a source of trusted facts."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from sona.developer_intelligence.diagnostics import SourceSpan, diagnostic
from sona.guide import (
    GuideContextManager,
    GuideLocalReasoningError,
    GuideRequest,
    explain,
    explain_with_local_model,
)
from sona.intelligence.contracts import (
    InferenceChunk,
    InferenceRequest,
    InferenceResponse,
    ModelFormat,
    ModelIdentity,
)
from sona.intelligence.service import LocalAIService


@dataclass
class _FakeProvider:
    provider_id: str = "local"
    response_text: str = "The reviewed rule is about a name not being visible here."
    response_provider_id: str = "local"
    response_model_id: str | None = None
    request: InferenceRequest | None = None
    calls: int = 0

    def infer(self, request: InferenceRequest, cancellation=None) -> InferenceResponse:
        self.calls += 1
        self.request = request
        return InferenceResponse(
            request_id=request.request_id,
            model_id=self.response_model_id or request.model_id,
            provider_id=self.response_provider_id,
            runtime_id="test-local-runtime",
            runtime_version="test-1",
            text=self.response_text,
        )

    def stream(self, request: InferenceRequest, cancellation=None):
        raise AssertionError("Guide reasoning uses the bounded infer operation")


class _LocalServiceAdapter:
    provider_id = "local"
    runtime_id = "guide-test-runtime"

    def __init__(self) -> None:
        self.last_context = None

    def load(self, model: ModelIdentity) -> None:
        return None

    def unload(self, model_id: str) -> None:
        return None

    def infer(self, request: InferenceRequest, cancellation=None) -> InferenceResponse:
        self.last_context = request.context
        return InferenceResponse(
            request_id=request.request_id,
            model_id=request.model_id,
            provider_id=self.provider_id,
            runtime_id=self.runtime_id,
            text="Optional local explanation.",
        )

    def stream(self, request: InferenceRequest, cancellation=None):
        yield InferenceChunk(request.request_id, 0, "Optional local explanation.")


def _guide_response():
    item = diagnostic(
        "SONA-RUNTIME-003",
        "runtime",
        "PRIVATE_DIAGNOSTIC_MESSAGE",
        span=SourceSpan(file="C:\\private\\workspace\\secret.sona", start_line=7, start_column=2),
        metadata={"credential": "PRIVATE_DIAGNOSTIC_METADATA"},
    )
    return explain(GuideRequest(item.diagnostic_id, item))


def test_local_advisory_preserves_deterministic_guide_and_uses_only_bounded_context():
    deterministic = _guide_response()
    before = deterministic.to_dict()
    provider = _FakeProvider()

    result = explain_with_local_model(
        deterministic,
        provider,
        model_id="dev-local-model",
        selected_text="let quantity = 3;\nprint(quant);",
    )

    assert provider.calls == 1
    assert result.deterministic is deterministic
    assert result.deterministic.to_dict() == before
    assert result.trust_status == "unverified-local-advisory"
    payload = result.to_dict()
    assert payload["deterministic"] == before
    assert payload["local_advisory"]["trust_status"] == "unverified-local-advisory"
    assert payload["local_advisory"]["provider_id"] == "local"

    sent = provider.request.context.text
    assert "let quantity = 3;" in sent
    assert "PRIVATE_DIAGNOSTIC_MESSAGE" not in sent
    assert "PRIVATE_DIAGNOSTIC_METADATA" not in sent
    assert "C:\\\\private" not in sent
    assert "workspace files" in provider.request.context.omitted_sources
    assert provider.request.context.source_count == 1
    assert provider.request.context.estimated_tokens <= 16 * 1024
    assert "untrusted data" in provider.request.prompt


def test_no_selected_source_means_no_user_source_is_sent():
    provider = _FakeProvider()
    explain_with_local_model(_guide_response(), provider, model_id="dev-local-model")
    assert provider.request.context.source_count == 0
    assert provider.request.context.text.find("selected_excerpt_untrusted") >= 0
    assert '"selected_excerpt_untrusted":null' in provider.request.context.text


def test_sona_guide_integrates_with_the_bounded_local_ai_service():
    adapter = _LocalServiceAdapter()
    with LocalAIService(adapter) as service:
        service.load_model(
            ModelIdentity(
                model_id="guide-local-model",
                provider_id="local",
                runtime_id=adapter.runtime_id,
                format=ModelFormat.GGUF,
                path="the-fake-adapter-does-not-open-this.gguf",
                context_tokens=2048,
            )
        )
        result = explain_with_local_model(
            _guide_response(),
            service,
            model_id="guide-local-model",
            selected_text="print(quant);",
        )
        assert result.advisory_text == "Optional local explanation."
        assert result.runtime_id == adapter.runtime_id
        assert "print(quant);" in adapter.last_context.text
        assert result.deterministic.request.diagnostic_id == "SONA-RUNTIME-003"


def test_non_local_provider_is_rejected_before_inference():
    provider = _FakeProvider(provider_id="remote")
    with pytest.raises(GuideLocalReasoningError, match="explicitly local"):
        explain_with_local_model(_guide_response(), provider, model_id="remote-model")
    assert provider.calls == 0


def test_selected_context_and_total_context_limits_reject_instead_of_truncate():
    provider = _FakeProvider()
    with pytest.raises(GuideLocalReasoningError, match="size limit"):
        explain_with_local_model(
            _guide_response(),
            provider,
            model_id="dev-local-model",
            selected_text="x" * (8 * 1024 + 1),
        )
    assert provider.calls == 0

    manager = GuideContextManager(maximum_context_bytes=256, maximum_selected_text_bytes=128)
    with pytest.raises(GuideLocalReasoningError, match="context exceeds"):
        manager.build(_guide_response(), selected_text="x" * 128)


@pytest.mark.parametrize(
    ("provider_kwargs", "expected_message"),
    [
        ({"response_provider_id": "remote"}, "mismatched identity"),
        ({"response_model_id": "different-model"}, "mismatched identity"),
        ({"response_text": "  "}, "empty advisory"),
        ({"response_text": "x" * (16 * 1024 + 1)}, "exceeds its size limit"),
    ],
)
def test_untrusted_provider_responses_are_bounded_and_identity_checked(
    provider_kwargs, expected_message
):
    provider = _FakeProvider(**provider_kwargs)
    with pytest.raises(GuideLocalReasoningError, match=expected_message):
        explain_with_local_model(_guide_response(), provider, model_id="dev-local-model")


def test_only_reviewed_diagnostic_entries_can_be_augmented():
    from sona.guide.models import GuideResponse, GuideSection

    response = GuideResponse(
        request=GuideRequest("SONA-UNKNOWN-999"),
        summary="Not reviewed.",
        topic="unknown",
        catalog_version=1,
        sections=(GuideSection("what", "What", "Not reviewed."),),
        concept_ids=(),
    )
    provider = _FakeProvider()
    with pytest.raises(GuideLocalReasoningError, match="reviewed diagnostic"):
        explain_with_local_model(response, provider, model_id="dev-local-model")
    assert provider.calls == 0
