# Sona Guardian Reference

Sona `0.15.0` ships `guardian` as a local resilience facade. Guardian helps a
developer detect project drift, preserve suspect state, restore a trusted local
snapshot, verify the restored project, and report what happened.

Guardian is not antivirus software, does not claim operating-system compromise
protection, and does not silently apply AI-generated repairs.

## Public Facade

`guardian` is available through `stdlib/guardian.smod` and the `sona guard`
CLI. The stable public flow is:

```text
sona guard init
sona guard status
sona guard verify
sona guard doctor
```

Additional public operations include snapshot creation, diff, quarantine,
rollback, plain-language reports, JSON reports, local audit history, and
explicit `heal --apply` recovery.

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
```

Guardian storage does not recursively snapshot itself.

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

