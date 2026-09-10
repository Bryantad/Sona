# Proof Mode

This page defines the field-level Proof Mode contract. For task-oriented setup,
start with the [Proof Mode guide](../guides/proof-mode.md) or the
[combined Proof and Guardian workflow](../guides/proof-and-guardian.md).

Examples use the installed user-facing `sona` command. Generation is delegated
without a shell to `sona-native` on `PATH`, or to the regular executable named
by `SONA_NATIVE_BINARY`. Native Core remains the sole receipt producer and the
coordinator never substitutes Python-compatible execution or fallback. Direct
`sona-native proof ...` and archive-local `.\sona.exe proof ...` invocations
remain supported.

Proof Mode records bounded evidence for one Native Core execution. It
observes the existing native runtime; it does not select another engine, alter
program semantics, or provide a general security attestation.

```text
sona proof app.sona --receipt proof.json --engine native
sona proof app.sbc --receipt proof.json --allow-fs-read
sona proof app.sona --receipt proof.json --summary
sona proof app.sona --receipt proof.json --engine native --guardian-root . --summary
```

The receipt destination is required, its parent directory must already exist,
and the destination must be new. Proof Mode never overwrites, truncates, or
merges an existing receipt. Writing the requested receipt is runner-owned and
does not grant a program filesystem-write access.

## Evidence contract

Proof Mode accepts `.sona` source and version-1 source-backed `.sbc`
containers. A container must first pass the normal Native Core container
validation, including its exact UTF-8 source payload. Invalid containers keep
their existing `SONA-NATIVE-BYTECODE-*` diagnostic and do not produce a Proof
receipt.

Receipts use `sona.native-proof.schema-1`. They record only:

- exact-source and container SHA-256 identities and byte counts;
- Native Core and no-Python/fallback flags;
- explicitly granted capabilities;
- execution status, duration, exit status, and stable diagnostic coordinates;
- SHA-256/byte-count summaries of stdout and stderr; and
- redacted filesystem, console, stdin, unavailable-network, clock, and random
  host-boundary effects.

Recognized effects retain their low-level `scope` and `operation` and add a
stable normalized `effect` identifier plus `support` status. The current
statuses are `SUPPORTED`, `PARTIAL`, `UNOBSERVED`, and `UNAVAILABLE`. Outcome
and support are independent: for example, a denied `FS.READ` attempt is still
an observation at a supported boundary, while an allowed network capability
can yield an unavailable `NET.REQUEST` because Native HTTP is not implemented.
Legacy 0.15.4 receipts omit these optional fields and remain verifiable; the
verifier derives recognized normalized names only in its returned view.

When `--guardian-root <project>` is explicitly requested, the receipt also
contains a redacted Guardian binding: a schema ID, trusted baseline snapshot
ID, and SHA-256 labels for Guardian's baseline and trusted-config state files.
Policy-aware bindings also contain the canonical Guardian `policy_sha256` and
`policy_enforced: true`. Native Core intersects filesystem and network requests
with that trusted policy before execution.
It records only `program_baseline: "tracked"`; it never records the project
root, Guardian inventory, program path, or configuration contents.

No receipt stores source text, raw paths, stdout/stderr bodies, stdin values,
clock values, random seeds or results, environment values, credentials,
request bodies, temporary paths, or operating system error text. Filesystem
targets use a new execution-local
`hmac-sha256:` fingerprint. The key is never stored, so receipts cannot usefully
correlate the same path across executions. Stdin effects never include a target
or value fingerprint.

Effects cover only instrumented Native host boundaries. Their absence is not
evidence that uninstrumented operating-system, parent-process, or external
activity did not occur. The normative mapping and support semantics are in the
[Proof effect vocabulary](../spec/proof/effects.md).

`receipt_hash` is SHA-256 over the compact canonical UTF-8 JSON receipt with
the `receipt_hash` member omitted. Object keys are lexicographically sorted,
arrays retain execution order, and the newline written to the JSON file is not
included in the digest. Hashes use lowercase `sha256:<hex>` notation.

## Diagnostics and compatibility

`PROOF-001` through `PROOF-008` belong exclusively to Proof Mode invocation,
input, receipt destination, creation, serialization, and finalization
failures. `PROOF-008` means an explicitly requested Guardian binding was
unavailable, inconsistent, outside the requested project, or no longer tracked
by the trusted baseline. It is raised before program execution and no receipt
is published. Diagnostics produced by the program retain their existing Sona
identifiers: Proof Mode does not reclassify parser, container, VM, runtime,
engine, capability, or host failures.

Python-coordinator discovery and process-launch failures occur before the Rust
producer runs. They use the separate redacted `SonaProofLaunchError` text
contract, provide an installation or `SONA_NATIVE_BINARY` hint, expose no raw
operating-system error, and create no receipt. They are not `PROOF-*` receipt
diagnostics.

When a program fails and the receipt persists, Sona prints the original program
diagnostic and stores its identifier in the receipt. When persistence itself
fails, Sona prints the relevant `PROOF-*` diagnostic and makes no proof-success
claim. A final path may remain after a post-publication durability failure; it
must not be treated as publication-certified.

Without `--summary`, a successfully persisted Native Core `proof` has the same
program-visible stdout, stderr, exit result, VM semantics, and runtime
diagnostics as an equivalent native `sona run`. Only the explicitly requested
evidence side effect differs.

## Interactive summary

Pass `--summary` when a person is watching the terminal and needs a concise
confirmation that the receipt was saved. After a successful execution and
receipt publication, Sona writes a labeled summary to stderr with the receipt
path, Native Core engine, observed-effect count, output byte counts, duration,
and receipt hash.

The summary is presentation-only: it is not emitted for program or receipt
failures, is not included in the receipt's output hashes, and does not change
the receipt contents, receipt hash, program stdout, or exit result. Leave the
flag off for the exact `sona run`-compatible stdout/stderr contract used by
scripts and automated tests.

## Guardian-bound proof and local attestation

Use Guardian before a release proof when the program is part of an explicitly
trusted project:

```text
mkdir .sona/receipts
sona guardian init --project-root .
sona proof app.sona --receipt .sona/receipts/proof.json --engine native --guardian-root . --summary
sona guardian proof verify --project-root . --receipt .sona/receipts/proof.json
sona guardian proof attest --project-root . --receipt .sona/receipts/proof.json
sona guardian proof review --project-root . --receipt .sona/receipts/proof.json --provider deterministic
sona guardian proof history --project-root .
```

`--guardian-root` is opt-in. Native Core reads only the regular
`.sona/guardian/baseline.json` and `trusted_config.json` state files. It checks
that the input lies inside the supplied project and that its exact source hash
(or `.sbc` container hash) is still the tracked baseline entry. Native Core
does not import Python, execute Guardian, write Guardian state, or make an
audit entry while creating the receipt.

`sona guardian proof verify` is read-only. It verifies the receipt's canonical
self-hash, Native Core/no-Python engine fields, Guardian binding, and the
redacted baseline program identity. `sona guardian proof attest` repeats that
verification, requires a successful execution and a currently clean Guardian
project, then records only the receipt hash and Guardian anchor in local audit
history. It does not copy the receipt, source, program path, or output bodies.

The optional terminal summary identifies a bound receipt as `Guardian Bound
baseline <id>` without revealing the project root.

## Governed advisory AI review

`sona guardian proof review` is an analysis layer after verification, not a new
trust layer. It verifies the receipt first; rejected or noncanonical evidence
never reaches provider routing. The exact provider input is a canonical packet
containing the receipt hash, execution status, program and runtime identities,
capability grants, output identities, target-free normalized effects, redacted
Guardian anchor, local-attestation flag, and explicit observation boundary. The
command returns a `review_input_hash` for that packet and never sends project
paths, receipt paths, source, effect targets, output bodies, environment values,
or credentials as review context.

The observation boundary states that agent actions are not represented and
AI-request causality is not established. `AGENT.ACTION` is not a Proof Mode
effect. A developer-intelligence task record can describe provider metadata,
but it is not Native execution evidence.

The deterministic local reviewer is the safe default. A configured local Qwen
model can be used through Ollama:

```text
sona guardian proof review --project-root . --receipt .sona/receipts/proof.json --provider ollama
```

Configured remote providers require both explicit provider selection and
`--allow-network`; governance policy can still deny or require approval. Review
does not write an AI task receipt or alter Guardian proof state. Provider-routing
decisions may enter the separate governance audit. All returned model text is
marked advisory and cannot verify, sign, attest, or add trust to the receipt.
See [Proof Mode and Trusted Automation](../spec/proof/automation.md) for the
normative evidence boundary.

## Limits of the claim

Proof Mode creates redacted, self-hashed, integrity-checkable Native Core
execution evidence. An actor who replaces a receipt can recompute its
self-hash. The Guardian flow adds a local baseline binding,
read-only receipt verification, an explicit local audit attestation, and an
optional governed advisory review; it is
not authentication, cryptographic signer identity, machine or remote attestation,
trusted-hardware proof, operating-system integrity proof, or full
Python/native semantic parity. Guardian state is not a protected trust anchor;
a local user who can alter and re-hash both receipt and Guardian state is
outside this trust claim.

New 0.15.6 producers also identify the running Native CLI executable by
SHA-256 and byte count. Release builds may include their full build-supplied
Git revision. `sona proof inspect` displays both after shared verification.
They are correlation fields inside the self-hashed receipt, not authenticated
runtime provenance; compare them with independently published release records.
