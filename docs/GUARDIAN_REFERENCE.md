# Sona Guardian Reference

Sona `0.15.4` ships `guardian` as a local resilience facade. Guardian helps a
developer detect project drift, preserve suspect state, restore a trusted local
snapshot, verify the restored project, and report what happened.

Guardian is not antivirus software, does not claim operating-system compromise
protection, and does not silently apply AI-generated repairs.

## Public Facade

`guardian` is available through `stdlib/guardian.smod` and the canonical
`sona guardian` CLI (`sona guard` remains compatible). The stable public flow
is:

```text
sona guardian init
sona guardian status
sona guardian verify
sona guardian doctor
```

Additional public operations include snapshot creation, diff, quarantine,
rollback, plain-language reports, JSON reports, local audit history, and
explicit `heal --apply` recovery. Guardian also exposes `proof_verify`,
`proof_attest`, and `proof_history` for a local Native Proof release chain.

## Trust Boundary

Guardian may only modify files inside the explicitly initialized project root.
Before reading, snapshotting, quarantining, or restoring a file, Guardian
resolves the canonical path and rejects unsafe traversal or symlink escapes.

Default exclusions include:

```text
.git/**
.venv/**
__pycache__/**
dist/**
build/**
*.pyc
.env
.env.*
*.pem
*.key
*.p12
*.pfx
.sona/guardian/**
.sona/receipts/**
.sona/governance/**
```

Guardian storage does not recursively snapshot itself.

## Native Proof Trust Chain

Guardian and Native Proof Mode are intentionally coordinated but not silently
coupled. A release workflow opts in at each state-changing or evidence-bearing
step:

```text
mkdir .sona/receipts
sona guardian init --project-root .
sona proof app.sona --receipt .sona/receipts/proof.json --engine native --guardian-root . --summary
sona guardian proof verify --project-root . --receipt .sona/receipts/proof.json
sona guardian proof attest --project-root . --receipt .sona/receipts/proof.json
sona guardian proof history --project-root .
```

At proof creation, Native Core reads Guardian's persisted baseline and trusted
configuration without importing Python, executing Guardian, or mutating its
state. It requires the program to be inside the explicit project root and to
match the tracked baseline hash. The Native receipt stores only a redacted
anchor: baseline snapshot ID, SHA-256 labels for the two Guardian state files,
and `program_baseline: "tracked"`.

`guardian proof verify` is read-only. It checks canonical receipt storage and
self-hash, Native Core/no-Python engine identity, the matching Guardian anchor,
and that the receipt's source or container hash is represented by the trusted
baseline. `guardian proof attest` additionally requires a successful proof and
a clean current Guardian verification. It then appends a redacted local audit
record containing the receipt hash and anchor, not the receipt path, source,
program path, or output body.

This is a local release-integrity chain, not a remote or hardware attestation.
It does not provide signer identity or protect against a party that can modify
both the proof receipt and the local Guardian state.

## Trusted Configuration

`sona.guard.json` is security-sensitive. At initialization, Guardian validates
the configuration, records a trusted hash, copies trusted validation policy into
local Guardian state, and establishes the baseline.

During verification, unexpected config drift is quarantined and Guardian
continues using the trusted baseline policy. Newly introduced validation
commands are not executed automatically.

## Validation Commands

Validation commands must be recorded during initialization. They are executed
without shell interpolation where practical and logged locally with exit code
and duration.

## Healing And Rollback

Default healing is non-mutating:

```text
detect -> report -> recommend -> require explicit apply
```

Mutating recovery requires `sona guard heal --apply` or an explicit automatic
recovery policy. Before rollback, Guardian preserves suspect state in
quarantine, verifies snapshot integrity, restores files, reruns trusted
validation, verifies restored hashes, and records an audit event.

If verification fails, Guardian stops safely, activates the circuit breaker,
preserves evidence, and reports the failure. Guardian must not enter an
infinite recovery loop.

## Cognitive Integration

Guardian reports integrate with stable local cognitive helpers for boundaries,
contracts, breadcrumbs, logs, certainty notes, chunking, simplified messages,
and plain-language explanations. These integrations are local and in-memory by
default.

## Test Safety

Guardian mutation tests must use temporary fixture projects outside the source
repository. The repository root must not be used as a Guardian mutation fixture.

