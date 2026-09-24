# Sona Guide with optional local reasoning

Status: experimental Python API for the Sona 0.16.0 development branch.

Sona Guide remains deterministic and catalog-backed. The optional API
`sona.guide.explain_with_local_model` is a second, explicitly requested layer:
it returns the original `GuideResponse` unchanged beside separate model text
marked `unverified-local-advisory`. It does not replace diagnostics, Guide
facts, fixes, or provenance, and it does not write source files or execute
commands.

## Invocation and trust boundary

Call the deterministic Guide first, then opt in to local reasoning:

```python
from sona.guide import GuideRequest, explain, explain_with_local_model

guide = explain(GuideRequest("SONA-RUNTIME-003"))
augmented = explain_with_local_model(
    guide,
    local_ai_service,
    model_id="my-local-model",
    selected_text="print(quant);",
)
```

The provider must identify itself as `local`; the helper rejects non-local
providers before inference. `LocalAIService` also validates the configured
model provider/runtime identity and has no cloud or Ollama fallback. Model
text remains advisory even when inference succeeds. Consumers must not treat
it as compiler evidence, a validated edit, a capability decision, a Guardian
decision, or Proof evidence.

## Context minimization

The context manager only accepts a deterministic response and optional
explicitly selected text. It does not accept workspace roots, file paths, or
whole-document/workspace objects. The selected excerpt is limited to 8 KiB;
the complete JSON context is limited to 16 KiB. Oversized input is rejected,
not silently truncated. With no explicit selection, only reviewed catalog
fields are sent.

The payload omits the caller's diagnostic message, source path, source span,
fix metadata, and arbitrary diagnostic metadata. It includes only the
canonical diagnostic identifier and reviewed catalog topic, summary,
explanation, and next-step text. The selected excerpt is encoded as an
untrusted JSON data field and is not interpreted as an instruction by trusted
Sona code. This size/redaction boundary reduces disclosure; it cannot prevent
a model from making mistakes or following hostile content in the excerpt.

Prompt text and model output stay in process memory. The service's bounded
job history may retain them until eviction or successful service shutdown;
closing clears the retained job history. A timed-out close leaves the service
active until native work cooperatively stops. No reasoning
payload is appended to Native Proof schema-1, a Guardian baseline, or the
deterministic Guide catalog. The current API augments reviewed diagnostic
explanations only; concepts, selection mode, and editor/CLI UX remain future
integration work.
