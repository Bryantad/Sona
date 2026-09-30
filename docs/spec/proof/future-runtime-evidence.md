# Future Runtime Evidence Receipt Design (Proposal)

**Status:** design note only; not an implemented receipt schema.

This proposal records extension points for a future Proof receipt version that
could describe local-model and durable-workflow execution. It does not change
`sona.native-proof.schema-1`, its canonicalization, its verifier, or the meaning
of any existing receipt. No version number or compatibility policy for a
future schema is selected here.

## Goals

A future receipt may bind a bounded runtime record to independently verifiable
identities for:

- the model artifact (format, byte count, and content digest);
- the inference runtime and its version/build identity;
- a workflow, task, and step using stable opaque IDs;
- an approved execution intent, represented without embedding prompts or
  source text;
- an ordered, bounded event-journal digest; and
- structured effect observations with their outcome and capability-scope
  references.

The receipt should allow a verifier to check internal consistency and detect
content changes. It must not imply that the model, runtime, host, timestamp,
operator, policy decision, or effect is authentic merely because a digest is
present.

## Candidate structure

The following is illustrative only; it is not accepted by the schema-1
verifier and must not be emitted as a schema-1 extension:

```json
{
  "runtime_evidence": {
    "schema_id": "sona.runtime-evidence.proposal-1",
    "model": {
      "format": "gguf",
      "bytes": 0,
      "sha256": "sha256:<64 lowercase hex characters>"
    },
    "inference_runtime": {
      "name": "llama.cpp",
      "version": "<reported version>",
      "build_sha256": null
    },
    "workflow": {
      "workflow_id": "<opaque stable id>",
      "task_id": "<opaque stable id>",
      "step_id": "<opaque stable id>"
    },
    "approved_intent": {
      "intent_sha256": "sha256:<64 lowercase hex characters>",
      "approval_record_id": "<opaque id or null>"
    },
    "event_journal": {
      "event_count": 0,
      "ordered_digest": "sha256:<64 lowercase hex characters>"
    },
    "effects": []
  }
}
```

Field names, requiredness, digest encoding, event ordering, and approval
representation require a separate schema review. This example is a design
sketch, not a validated JSON Schema or interoperable format.

## Authority and privacy boundaries

- Model output, workflow descriptions, event payloads, and effect requests
  remain data. None can grant a capability or make a policy decision.
- Human approval, trusted policy evaluation, and capability issuance must be
  represented as separate facts. An approval identifier alone is not proof of
  identity or authorization.
- Effect records describe attempted/observed operations and outcomes; they do
  not authorize replay. Reopening a receipt or journal must not resume work.
- Do not include prompts, source text, raw editor contents, credentials,
  environment values, or unrestricted filesystem paths. Prefer bounded opaque
  identifiers and digests, and document the residual correlation risk of
  stable hashes.
- A digest detects alteration only relative to a trusted expected value. It
  is not a signature, trusted timestamp, trusted-hardware claim, remote
  attestation, or operating-system integrity proof.

## Compatibility and migration

Schema-1 remains frozen and backward-compatible. A future version must have an
explicit schema identifier, independent canonicalization/hash rules, strict
field validation, and a verifier that continues to accept valid schema-1
receipts without silently upgrading or reinterpreting them. Whether a future
receipt embeds schema-1 or is a separate receipt type is intentionally open.

Before implementation, review at least these questions:

1. Which model and runtime identity fields are stable across platforms?
2. How are event digests formed when payloads are redacted or omitted?
3. Which approval/policy facts can be independently verified, and by whom?
4. How are retries, cancellation, partial completion, and recovery represented?
5. What size limits and privacy protections apply to event/effect records?
6. How does a verifier distinguish observation from enforcement and authority?

## Explicit non-goals

This proposal does not add signatures, PKI, cloud services, remote
attestation, trusted timestamps, or deterministic replay. It does not change
Guardian policy, mint capabilities, or claim that arbitrary model/runtime
execution is deterministic. Any such work requires separate authorization and
design review.
