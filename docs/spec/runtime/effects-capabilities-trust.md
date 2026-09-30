# Runtime Effects, Capabilities, and Proposal Trust (0.16.0)

This document describes the current Python runtime API in
`sona.runtime.effects`, `sona.runtime.capabilities`, and
`sona.runtime.proposals`. These are in-process contracts, not operating-system
sandboxing.

## Structured effects

`EffectClass` names an attempted interaction (for example `FS.READ`,
`NETWORK.REQUEST`, `PROCESS.EXECUTE`, `MODEL.INFERENCE`, or the Guide-specific
`EDITOR.BUFFER_REPLACE`). Records keep two independent facts:

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
trusted and connect to Guardian only through a reviewed adapter. The Guide
editor-buffer adapter below is the 0.16.0 integration; it does not change
native Proof Mode.

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

The Sona Guide request API also accepts `action: "validate_proposal"` with
the current `source` and a `proposed_source`. It validates the candidate using
the deterministic Sona frontend, rejects an unchanged candidate or any
candidate with an error-severity diagnostic, and returns diagnostic records
and SHA-256 values without echoing either source. The sources are bounded to
256 KiB each. This endpoint is read-only: it does not request model inference,
display a diff, obtain approval, write a file, or execute the candidate. A
caller must still show the exact candidate diff, obtain explicit user approval,
recheck the source hash/version, and apply the change as a separate operation.

The VS Code Guide exposes Propose Local AI Edit for a selected range in a
trusted local workspace. It routes only through the language server's
process-local LocalAIService and direct GGUF/llama.cpp adapter; no Ollama or
remote fallback is attempted. The model receives the selected source and a
bounded instruction, not the full file or workspace. The response is parsed
as a bounded JSON replacement, inserted into a candidate in memory, and
checked by the deterministic proposal endpoint above. Sona opens a
before/after diff and requires an explicit user action before applying the
replacement to the editor buffer. It does not save the file or execute the
candidate. A changed or closed document, invalid candidate, malformed model
response, untrusted workspace, unregistered/changed model artifact, or
unavailable direct runtime prevents application. The LSP-owned service reuses
the loaded model between requests and closes it when the language-server
process exits; this remains process-local service ownership, not an
OS-isolated daemon.

After the user chooses **Apply proposal**, the extension checks the live
document version, content hash, and selected range, then calls
`sona/guide/prepare_buffer_edit`. The LSP verifies that the selected range and
replacement reconstruct exactly the validated candidate. Trusted policy may
issue only `EDITOR.BUFFER_REPLACE`; it never maps this operation to `FS.WRITE`,
`PROCESS.EXECUTE`, save, execution, Guardian mutation, or Proof authority. If
Guardian state is absent, the narrow Guide policy applies. If Guardian state
exists, its read-only check must report a valid trusted baseline; drift,
invalid state, or check errors deny. Guardian's `filesystem_write` setting is
not consulted as an editor permission.

The capability binds an opaque workspace identity, document identity hash,
document version, selection start/end, original-source hash, complete candidate
hash, and replacement hash. Raw paths, source, replacement, and selection are
not written into the capability audit. The token remains server-side and the
extension receives only an opaque handle. It is short-lived (five seconds),
exact-resource, one-shot, and revoked/consumed on success or failure. Immediately
before the buffer operation, the LSP consumes the handle, rechecks Guardian
trust, and checks the exact token. The extension then rechecks document and
selection again, including inside the editor edit callback. Any mismatch burns
the handle and makes no edit; a new proposal and approval are required.

Human approval and capability authorization remain distinct facts. The model
cannot mint or transport a token, and approval alone cannot reach the edit
operation. The capability audit records request/check/revocation, not proof
that VS Code ultimately applied the edit; it is bounded and process-local. The
LSP authorization and VS Code edit are separate process operations, not one
atomic OS transaction. This is a trusted-host workflow gate, not protection
against a compromised extension, arbitrary same-process Python, or another
program running as the user. The LSP cannot independently prove that a human
clicked the approval UI. The edit changes the editor buffer only: it never
saves or executes the file and creates or strengthens no Proof receipt.

## Proof and Guardian compatibility

Proof receipt schema-1 is unchanged. These in-memory records do not add fields
to native Proof receipts and cannot verify, modify, or strengthen them. Native
Proof's current Guardian binding remains authoritative for the existing native
workflow. The Guide editor adapter is a distinct local workflow check; it does
not create a Proof receipt or attest execution.

## Known limitations

- No OS-level sandboxing or process isolation is added here.
- The general capability API still requires a trusted host policy. Only the
  Guide editor-buffer path has the Guardian adapter described above.
- Effect and capability audits are process-local and in-memory.
- The effect journal records supplied observations; it does not prove that an
  operation actually occurred.
- Capability checks are not wired into every Sona/stdlib operation; the Guide
  adapter is a narrowly scoped exception.
- Guide proposal application is limited to an explicit one-shot authorized
  editor-buffer edit after diff review; it is not a file writer, save operation, or
  execution path. Direct local inference requires the optional llama.cpp
  dependency and a registered, intact GGUF artifact.
- Proof schema-1 semantics and Guardian implementation are not changed.
