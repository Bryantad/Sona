# Sona v0.13.0 Governance Release Specification

## 1. Release Definition

- **Version:** `0.13.0`
- **Type:** Runtime Governance + Infrastructure Hardening
- **Status:** Feature Complete, Pre-Publish

### Core Statement

> Sona `0.13.0` introduces deterministic runtime memory governance through policy enforcement, audit logging, and compliance reporting, fully integrated into the interpreter lifecycle.

This release does not redefine the public language surface. It formalizes the runtime trust layer required for persistent memory, receipts, replay, and accountable AI execution.

## 2. Architectural Intent

### Why this release exists

`0.12.0` stabilized boundaries, packaging, and runtime separation.

`0.13.0` makes the runtime trustworthy.

This matters because Sona's long-term direction depends on governed persistent state rather than raw storage alone. The governance layer introduced here is the foundation for:

- persistent memory
- receipts and observability
- deterministic replay
- AIFS integration
- AI decision tracing

Without runtime governance, those systems are storage features. With runtime governance, they become credible infrastructure.

## 3. Core Feature Pillars

### 3.1 Policy Enforcement Layer

#### Components

- `PolicyKernel`
- `MemoryPolicy`
- classification, retention, scope, promotion, and checkpoint policy structures
- deterministic policy fingerprinting

#### Specification

Every governance-relevant memory operation must pass through a deterministic policy check.

Policies must produce:

- consistent decisions
- reproducible outcomes
- exportable fingerprints

#### Guarantees

- no implicit memory writes
- no silent policy bypass
- full traceability of policy decisions

### 3.2 Audit System

#### Components

- `AuditKernel`
- `AuditEvent`
- `AuditSummary`
- SQLite-backed append-only audit store

#### Specification

Every governance-relevant action must emit an audit record.

The audit log must be:

- append-only
- immutable in effect
- queryable by subject, actor, and action
- self-bootstrapping at storage initialization

#### Guarantees

- complete historical trace
- no mutation of past events through normal runtime flow
- durable forensic visibility into governance activity

### 3.3 Compliance Engine

#### Components

- `ComplianceReporter`
- `ComplianceReport`
- `ComplianceViolation`

#### Specification

Compliance reporting is a read-only scan across governed runtime state, including stored memory records and audit state.

The compliance layer must detect violations of active policy rules without mutating runtime data.

#### Guarantees

- no side effects during reporting
- deterministic report output for the same underlying state
- independent validation layer over runtime governance data

### 3.4 Interpreter Integration

#### Specification

The interpreter must construct and wire:

- `PolicyKernel`
- `AuditKernel`
- `ComplianceReporter`

Governance must be integrated into:

- memory intake
- inspection
- checkpoint and goal-loop flows

#### Guarantees

- governance is not optional during normal execution
- governance is part of interpreter startup, not a detached subsystem
- execution paths that touch governed memory participate in the trust pipeline

## 4. Runtime Contract

### Before `0.13.0`

- memory behavior was partially implicit
- traceability was limited
- no formal governance contract existed

### After `0.13.0`

All governed memory operations follow this trust pipeline:

```text
input -> policy check -> execution -> audit log -> compliance visibility
```

This is the first explicit trust pipeline in Sona's runtime.

## 5. Stability Classification

### Stable in `0.13.x`

- policy enforcement behavior
- audit logging mechanics
- compliance reporting structure
- interpreter-level governance integration
- append-only audit storage model

### Semi-Stable

- policy schema shape, which may expand without changing the core contract
- compliance rules and report detail, which may evolve as governance coverage grows

### Internal

- storage backend implementation details
- optimization paths
- internal kernel wiring details not exposed as release guarantees

## 6. Explicit Non-Goals

The following are intentionally out of scope for `0.13.0`:

- syntax changes
- language redesign
- standard library expansion as the main payload
- AI runtime feature expansion as the release focus
- broad architecture pivots unrelated to persistent memory governance

This release should be read as a governance hardening milestone, not as a feature-surface expansion.

## 7. Validation Requirements

The release is considered valid only if the following categories pass.

### Governance Validation

- policy tests verify deterministic evaluation
- audit tests verify append-only integrity and query behavior
- compliance tests verify correct violation detection

### Runtime Validation

- the runtime test suite passes without governance regressions
- interpreter startup preserves governance construction and wiring

### CLI Validation

- version reporting is correct
- the runtime initializes the governance stack in normal CLI usage

### Packaging Validation

- wheel installation succeeds outside the repository root
- CLI behavior remains correct after installation
- release artifacts are generated with version-consistent names

## 8. Release Gates

`0.13.0` is publishable only when all of the following are true.

### Gate 1: Integrity

- all required tests pass
- no deterministic governance failures remain

### Gate 2: Packaging

- `.whl` installs cleanly
- CLI works outside the repository

### Gate 3: Documentation

- release notes reflect governance scope accurately
- release messaging does not overstate `0.13.0` as a feature expansion release

### Gate 4: Artifacts

- wheel built
- sdist built
- VSIX built

### Gate 5: Final Review

- extension dependencies reviewed before VSIX publication
- version consistency verified across package metadata and release docs

## 9. Release Messaging

### This release is

- a governance layer
- trust infrastructure for runtime state
- a correctness and traceability improvement

### This release is not

- a major new language-feature drop
- a large user-facing syntax expansion
- a flashy milestone driven by breadth instead of rigor

The correct tone for `0.13.0` is technical, precise, and infrastructure-focused.

## 10. Roadmap Position

The clean progression for the release line is:

### `0.12.0`

- boundary cleanup
- packaging maturity

### `0.13.0`

- runtime governance and trust layer

### `0.14.0`

- standard library stabilization
- CLI improvements
- developer experience work

### `0.15.0`

- docs, examples, and test hardening

### `1.0.0`

- stable public language release

These roadmap items are directional planning anchors, not locked feature commitments.

## 11. Strategic Significance

`0.13.0` is not just an internal cleanup release. It establishes the infrastructure that differentiates Sona from runtimes that store state without proving how that state was governed.

This release directly supports future systems such as:

- receipts
- AIFS trust workflows
- deterministic replay
- agent accountability
- memory-based reasoning systems

## 12. Immediate Publish Plan

### 1. Lock the release contract

- keep this document as the specification source of truth for `0.13.0`

### 2. Final checks

- review VSIX dependency advisories
- verify version strings
- confirm CLI behavior post-install

### 3. Tag the release

```bash
git tag v0.13.0
git push origin v0.13.0
```

### 4. Publish artifacts

- GitHub release
- attach `.whl`, `.tar.gz`, and `.vsix`

### 5. Announce accurately

- present `0.13.0` as a governance and trust-layer release
- avoid framing it as a broad language expansion

## Bottom Line

Sona `0.13.0` does not need a new identity. It already has the right one.

This specification locks that identity into a ship-ready release contract: runtime governance, trust infrastructure, clear non-goals, explicit validation gates, and a clean place in the roadmap from `0.14.0` to `1.0.0`.
