# Sona v0.13.0 Release Notes

**Release Date:** 2026-03-22
**Type:** Persistent Memory Governance Release

---

## Summary

v0.13.0 adds a full governance layer to Sona's persistent memory subsystem. Three new modules — policy, audit, and compliance — provide deterministic runtime policy enforcement, append-only audit logging, and read-only compliance reporting. All modules are wired into the interpreter and exposed through the `advanced` surface. No breaking changes.

For the locked release contract, non-goals, publish gates, and roadmap position, see `docs/SPEC_v0.13.0_GOVERNANCE.md`.

---

## Highlights

- `sona.runtime.memory.policy` — deterministic runtime policy engine (`PolicyKernel`, `MemoryPolicy`, 5 sub-policies) enforcing classification ceilings, retention constraints, and episode limits at the storage boundary.
- `sona.runtime.memory.audit` — append-only governance audit log (`AuditKernel`, `AuditEvent`, `AuditSummary`) with self-bootstrapping `audit_log` SQLite table, forensic export, and immutability verification.
- `sona.runtime.memory.compliance` — read-only compliance reporter (`ComplianceReporter`, `ComplianceReport`, `ComplianceViolation`) scanning episodes, goals, checkpoints, and audit events against policy constraints.
- Interpreter constructor creates and wires `AuditKernel` and `ComplianceReporter` alongside the existing `PolicyKernel`.
- Audit logging integrated into `intake.py` (episode append/deny), `inspection.py` (retention transitions), and `goal_loop.py` (checkpoint restore).
- All governance types exported from `sona.runtime.memory.advanced`.
- 31 new tests across three test modules (6 policy + 16 audit + 9 compliance).

---

## New Modules

| Module          | LOC | Public Types                                                                                                                                      |
| --------------- | --- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `policy.py`     | 487 | `PolicyKernel`, `MemoryPolicy`, `ClassificationPolicy`, `RetentionPolicy`, `CapacityPolicy`, `AccessPolicy`, `GovernancePolicy`, `PolicyDecision` |
| `audit.py`      | 296 | `AuditKernel`, `AuditEvent`, `AuditSummary`                                                                                                       |
| `compliance.py` | 173 | `ComplianceReporter`, `ComplianceReport`, `ComplianceViolation`                                                                                   |

---

## Validation

- Runtime test suite: `118 passed`
- Governance tests: `31 passed` (policy 6 + audit 16 + compliance 9)
- Lint errors: `0` across all modified files

---

## Release Identity

`0.13.0 adds deterministic governance to Sona's persistent memory subsystem — policy enforcement, append-only audit logging, and compliance reporting — keeping the language surface stable while hardening the runtime for production traceability.`
