# Sona Determinism Spec (Draft-1)

## Date
- February 24, 2026

## Status
- Draft
- Target freeze: v0.10.4

## Goal
- Define deterministic execution guarantees that can be tested and audited.

## Determinism Modes

## `STRICT`
- Inputs required to reproduce:
  - source bytes
  - runtime version
  - policy fingerprint
  - seed values
  - receipt chain context (if enabled)
- Disallowed:
  - wall-clock as implicit input
  - unstamped randomness
  - unordered iteration affecting output
- Contract:
  - same inputs produce byte-identical outputs and canonical receipts.

## `SEALED`
- Allows nondeterministic internals (time/random/external), but each nondeterministic value must be sealed into receipt fields.
- Contract:
  - same sealed receipt can be replayed for decision-path verification.

## `NON_DETERMINISTIC`
- No reproducibility guarantee.
- Requires explicit mode declaration and warning in receipt metadata.

## Canonical Rules
- JSON serialization:
  - UTF-8
  - sorted keys
  - LF newlines
  - stable numeric representation
- Path normalization:
  - project-relative POSIX-style separators for receipt file entries.
- Event ordering:
  - strict append order, no implicit resorting after emission.
- Hashing:
  - SHA-256 for receipt and tree hashes.
  - receipt hash computed from canonical payload excluding `receipt_hash` fields.

## Test Requirements (Draft Gate)
- Deterministic rerun test set must assert:
  - output byte identity
  - receipt hash identity
  - tree hash identity.
- Minimum replay smoke:
  - generate receipt
  - verify same state
  - mutate input
  - verify fails with deterministic diff.

## Non-Goals in Draft-1
- Formal proof system.
- Cross-org trust federation.
- Hardware enclave guarantees.
