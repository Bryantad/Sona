# Sona Guardian Reference

This page defines Guardian's technical behavior. For task-oriented setup, start
with the [Guardian guide](guides/guardian.md) or the
[combined Proof Mode and Guardian workflow](guides/proof-and-guardian.md).

Sona `0.15.6` ships `guardian` as a local resilience facade. Guardian helps a
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
sona guardian check
sona guardian explain
sona guardian doctor
```

Additional public operations include snapshot creation, diff, quarantine,
rollback, plain-language reports, JSON reports, local audit history, and
explicit `heal --apply` recovery. Guardian also exposes `proof_verify`,
`proof_attest`, `proof_review`, and `proof_history` for a local Proof Mode
release chain with optional governed advisory analysis.

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

## Proof Mode Trust Chain

Guardian and Proof Mode are intentionally coordinated but not silently
coupled. A release workflow opts in at each state-changing or evidence-bearing
step:

```text
mkdir .sona/receipts
sona guardian init --project-root .
sona proof app.sona --receipt .sona/receipts/proof.json --engine native --guardian-root . --summary
sona guardian proof verify --project-root . --receipt .sona/receipts/proof.json
sona guardian proof attest --project-root . --receipt .sona/receipts/proof.json
sona guardian proof review --project-root . --receipt .sona/receipts/proof.json --provider deterministic
sona guardian proof history --project-root .
```

At proof creation, Native Core reads Guardian's persisted baseline and trusted
configuration without importing Python, executing Guardian, or mutating its
state. It requires the program to be inside the explicit project root and to
match the tracked baseline hash. For policy-aware state, filesystem and network
flags are requests and the effective grant is intersected with the trusted
Guardian decision. The receipt stores only a redacted anchor: baseline snapshot
ID, SHA-256 labels for the two Guardian state files, canonical policy identity,
policy-enforcement marker, and `program_baseline: "tracked"`.

`guardian proof verify` is read-only. It checks canonical receipt storage and
self-hash, Native Core/no-Python engine identity, the matching Guardian anchor,
and that the receipt's source or container hash is represented by the trusted
baseline. `guardian proof attest` additionally requires a successful proof and
a clean current Guardian verification. It then appends a redacted local audit
record containing the receipt hash and anchor, not the receipt path, source,
program path, or output body.

`guardian proof review` repeats read-only verification before provider routing.
The reviewer sees a canonical redacted packet containing the receipt hash,
execution outcome, program and Native runtime identities, capability grants,
output identities, target-free normalized effects, Guardian anchor, and whether
a matching local attestation is recorded. Sona returns the packet's SHA-256
label as `review_input_hash` so the exact advisory input is visible. The packet
explicitly says agent actions are not represented and AI-request causality is
not established. The default deterministic reviewer is fully local;
`--provider ollama` selects configured local Ollama. A configured remote
provider additionally requires `--allow-network` and must still pass governance
policy. Invalid evidence never reaches a provider.

AI review does not write an AI task receipt, change Guardian proof state, or
become part of verification or attestation. Provider-routing decisions may be
recorded in Sona's separate governance audit. Model text is always advisory and
cannot verify, sign, attest, or add trust to evidence.

Developer-intelligence task records and model responses are application
metadata, not Proof Mode receipts. `AGENT.ACTION` is not a registered effect;
see [Proof Mode and Trusted Automation](spec/proof/automation.md).

This is a local release-integrity chain, not a remote or hardware attestation.
Neither AI review nor the underlying chain provides signer identity or protects
against a party that can modify both the proof receipt and local Guardian state.

## Trusted Configuration

`sona.guard.json` is security-sensitive. At initialization, Guardian validates
the configuration, records a trusted hash, copies trusted validation policy into
local Guardian state, and establishes the baseline.

The schema-1 capability policy is:

```json
{
  "schema_version": 1,
  "capabilities": {
    "filesystem_read": "deny",
    "filesystem_write": "deny",
    "network": "deny"
  }
}
```

Missing entries default to `deny`. Unknown capability names or decisions other
than `allow` and `deny` are invalid. `policy_sha256` is SHA-256 over compact,
key-sorted UTF-8 JSON for the normalized object above; paths, commands,
exclusions, timestamps, and recovery settings are excluded from that identity.

If the configuration is absent, `guardian init` creates this default without
clobbering a concurrent or existing file. Complete existing Guardian state
returns `already-initialized` without writes. Partial state fails closed.

`guardian check` is read-only and validates configuration, policy identity,
trusted-state coherence, drift, and Proof Mode readiness. `guardian explain`
returns those same normalized decisions with warnings and a next step. Neither
command executes validation commands or project code, accesses the network, or
modifies project files or Guardian state.

During verification, unexpected config drift is reported without changing the
project or Guardian state, and Guardian continues using the trusted baseline
policy. Quarantine is deferred to an explicit preservation or approved recovery
step. Newly introduced validation commands are not executed automatically.

## Validation Commands

Validation commands must be recorded during initialization. They are executed
without shell interpolation where practical and logged locally with exit code
and duration.

## Healing And Rollback

Default healing is non-mutating:

```text
detect -> report -> recommend -> require explicit apply
```

Mutating recovery requires `sona guardian heal --apply --approve`, an enforcing
`.sona/governance.json`, and non-denied `write_workspace` and `execute_code`
rules. The built-in audit policy denies mutation; `--approve` and
`auto_recover` do not bypass policy. Before rollback, Guardian preserves
suspect state in quarantine, verifies snapshot integrity, restores files,
reruns trusted validation, verifies restored hashes, and records an audit
event.

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

