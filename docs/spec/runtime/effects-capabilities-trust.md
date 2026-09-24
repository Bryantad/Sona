# Runtime Effects, Capabilities, and Proposal Trust (0.16.0 Phase 13)

This document describes the current Python runtime API in
`sona.runtime.effects`, `sona.runtime.capabilities`, and
`sona.runtime.proposals`. These are in-process contracts, not operating-system
sandboxing.

## Structured effects

`EffectClass` names an attempted interaction (for example `FS.READ`,
`NETWORK.REQUEST`, `PROCESS.EXECUTE`, or `MODEL.INFERENCE`). Records keep two
independent facts:

- `EffectDecision`: `allowed`, `denied`, `not_required`, or `unknown`.
- `EffectResult`: `not_attempted`, `failed`, `succeeded`, or `unknown`.

`EffectJournal` accepts caller-supplied decision/result observations and opaque
resource identifiers. It is append-only and bounded in memory; it raises
`EffectJournalFullError` rather than discard a record. A denial must have
`not_attempted` as its result. The journal neither authorizes nor executes an
effect, and its records are not durable Proof receipts. Callers must avoid raw
paths and sensitive data in resource identifiers.

The older `EffectOutcome` enum remains for source compatibility. It is not
silently reinterpreted as a structured decision/result pair.

## Capability requests and grants

`CapabilityAuthority` requires an injected `CapabilityPolicy`; there is no
default-allow policy. A `CapabilityRequest` names one effect, one opaque exact
resource reference, and a requested lifetime bounded to 1–3600 seconds. An
allowing policy response carries policy/rule identifiers, a policy SHA-256
label, a safe reason code, and a maximum lifetime. Only then does the authority
issue an exact-scope, expiring `CapabilityToken`.

`check()` must be called by trusted runtime code at each protected operation
boundary. Scope mismatch, expiry, revocation, unknown tokens, policy errors,
active-grant exhaustion, and full audit history do not authorize the
operation. Authorization checks and token lifecycle are auditable in a
bounded in-memory log. Revocation prevents later checks from allowing the
token; it cannot undo an operation already performed.

Token construction is restricted through the ordinary API, but Python
introspection and code executing in the same process are outside this trust
boundary. These objects are not a sandbox, OS permission system, durable
authorization database, or Guardian replacement. The injected policy must be
trusted and must connect to Guardian only through a reviewed adapter; Phase 13
does not add a Guardian adapter or change native Proof Mode.

## AI proposals

`UntrustedProposal.from_data()` snapshots a mapping as canonical, bounded JSON
(65,536 UTF-8 bytes maximum). The model-supplied payload is data only; fields
such as `approved`, `capability`, or `policy` inside it have no control meaning.

`ProposalGate` requires both a trusted deterministic validator and a distinct
approval callback. Validation failure skips the approval callback. Exceptions
are reduced to fixed Sona reason codes rather than exposing exception text.
The accepted value contains the original data snapshot, validation code, and
approver identity, but no capability or execution method. Acceptance means
only “validated and approved proposal data”; a caller still needs a separate
policy decision and an authorized effect boundary before performing work.

```python
proposal = UntrustedProposal.from_data("edit-42", "local-model", candidate)
result = gate.process(proposal)
if result.accepted is not None:
    # Preview/use as data. This object does not authorize a file write.
    preview(result.accepted.payload)
```

An approval callback represents an explicit trusted host decision. This
library does not implement a UI prompt or claim that a Boolean returned by an
AI model is user consent.

## Proof and Guardian compatibility

Proof receipt schema-1 is unchanged. These in-memory records do not add fields
to native Proof receipts and cannot verify, modify, or strengthen them. Native
Proof's current Guardian binding remains authoritative for the existing native
workflow. General-purpose Python capability checks are not yet connected to
Guardian. Do not describe Phase 13 as end-to-end enforcement until trusted
operation adapters and cross-boundary tests exist.

## Known limitations

- No OS-level sandboxing or process isolation is added here.
- The policy port must be supplied by trusted host code; the module does not
  load Guardian policy itself.
- Effect and capability audits are process-local and in-memory.
- The effect journal records supplied observations; it does not prove that an
  operation actually occurred.
- Capability checks are not yet wired into every Sona/stdlib operation.
- Proposal validation/approval is generic host API plumbing, not a Guide
  editor integration, diff UI, or automatic code writer.
- Proof schema-1 semantics and Guardian implementation are not changed.
