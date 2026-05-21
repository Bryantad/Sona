# Sona Trust-Layer Roadmap (v0.10.4 -> v1.0.0)

## Date
- February 24, 2026

## Purpose
- Convert Sona from feature-progress runtime into infrastructure-grade trust rails.
- Use deterministic execution, cryptographic receipts, policy guarantees, and hardened tool boundaries as the release spine.
- Complete the native `.smod` transition with explicit backend contracts per module.

## Direct Status Answer
- Yes, Sona is closer after v0.10.3.
- No, Sona is not yet at infrastructure-grade maturity.
- Current posture: early infrastructure stage with strongest progress in native module migration and baseline receipts.

## Evidence Snapshot (Current State)
- Native `.smod` contract exists for six must-have modules (`queue`, `stack`, `random`, `uuid`, `regex`, `hashing`).
- `sona receipt` CLI now supports `init|scan|build|verify|verify-chain|diff` with deterministic tree hashes.
- Deterministic receipt tests exist in `tests/test_receipt_integrity.py`.
- `sona receipt verify-chain` now validates receipt hash links and emits chain certificate summaries.
- CI now includes a dedicated `trust-layer-smoke` matrix job (Windows/Linux/macOS).
- Control-plane baselines restored:
  - `sona probe` works with restored `sona.policy`.
  - `sona lock` / `sona verify` work with `sona.lockfile_manager`.
- Receipt header now carries governance anchors:
  - `policy_fingerprint`
  - `engine_policy_fingerprint`
  - optional `prev_receipt_hash`
  - canonical `receipt_hash`
- Wave 1 `.smod` metadata contracts now explicit for: `json`, `fs`, `io`, `path`, `env`.
- `.smod` coverage is partial:
  - Top-level `.smod` files: 16.
  - `.smod` files with explicit runtime backend metadata: 11.
  - `.smod` files still using `__native__` bridge calls: 11.

## Maturity Scorecard (Estimated)

| Layer | Infrastructure Bar | Current Status | Readiness |
|---|---|---|---|
| 1. Deterministic Runtime | Formal modes + no hidden nondeterminism + replayable outputs | Partial determinism and targeted tests, draft mode spec published, freeze pending | 40% |
| 2. Receipt Ledger | Canonical stream, hash-chain, signing, redaction, scale querying | Good baseline with hash-chain pointer + policy fingerprints; no signature/redaction/index yet | 45% |
| 3. Policy Guarantees | Deterministic ordering, conflict semantics, static validation | Baseline policy engine restored with deterministic rule ordering; no static analyzer yet | 20% |
| 4. Tool Boundary Hardening | All external I/O in auditable envelope | Partial bridge controls in module loading, no full boundary governor | 20% |
| 5. Operational/Enterprise | Stable contracts, migrations, compatibility, compliance controls | Release flow exists; core command breakages fixed, compatibility and migration guarantees pending | 30% |

## Release Plan

### Sequencing Decision
- Pause Native `.smod` Wave 1 until governance primitives are in place.
- Execute governance-first sequence:
  1. restore policy engine
  2. freeze determinism draft
  3. add receipt hash-chain and policy fingerprints
  4. add replay smoke gates
- Resume `.smod` expansion only after those gates pass.

## v0.10.4 - Reliability Baseline
- Restore broken control-plane commands (`policy`, `lockfile_manager`) or deprecate with explicit migration path.
- Freeze Determinism Spec `DRAFT-1`:
  - Execution modes: `STRICT`, `SEALED`, `NON_DETERMINISTIC`.
  - Canonical JSON and path normalization rules.
  - Seed and clock behavior contract.
- Define Receipt Spec `0.3`:
  - Required fields and canonical serialization constraints.
  - `tree_sha256`, `policy_fingerprint`, and `prev_receipt_hash` requirements.
- Implement hash-chain baseline:
  - `prev_receipt_hash` in receipt header
  - canonical `receipt_hash` calculation.
- Add CI gates for:
  - deterministic re-run checks
  - receipt schema validation
  - receipt diff regression
  - replay smoke.
- Exit gate:
  - `sona receipt` and baseline control-plane commands green in CI on Windows/Linux/macOS.

## v0.10.5 - Receipt Ledger Alpha
- Receipt model upgrades:
  - canonical event stream section
  - hash-chaining (`prev_receipt_hash`)
  - runtime+policy+graph fingerprint block.
- Add sealed nondeterministic outputs (`sealed_fields`) and provenance markers.
- Add receipt signing API (`sign`, `verify-signature`) with pluggable key provider.
- Build indexer MVP for receipt query by:
  - receipt id
  - tree hash
  - policy hash
  - status.
- Exit gate:
  - auditor can reconstruct decision path from receipt alone for covered flows.

## v0.10.6 - Policy Engine Beta
- Introduce policy engine module with deterministic evaluation ordering.
- Add conflict resolution semantics (`deny_overrides`, `priority`, explicit tie-breakers).
- Emit rule-hit traces into receipts.
- Add static policy analyzer:
  - unreachable rules
  - contradictory rules
  - duplicate conditions.
- Add simulation mode (`sona policy simulate`).
- Exit gate:
  - policy allow/deny decisions are explainable and reproducible for fixed inputs.

## v0.10.7 - Tool Boundary Controls
- Route all external I/O through audited wrappers.
- Canonicalize tool invocation payloads before execution.
- Add deterministic retry policy profiles.
- Add data classification labels (`public`, `internal`, `sensitive`) and policy enforcement hooks.
- Add rate-limit and budget controls at policy layer.
- Exit gate:
  - no unmanaged external call path remains in production runtime.

## v0.10.8 - Native `.smod` Wave 1
- Migrate high-impact wrapper-heavy modules toward explicit backend contracts:
  - `json`, `fs`, `io`, `path`, `env`.
- For each module, require:
  - `module_format`
  - `runtime_backend`
  - deterministic behavior tests.
- If bridge is still required, enforce explicit allow-list of native calls and reason annotation.
- Exit gate:
  - no top-level `.smod` module is metadata-ambiguous.

## v0.10.9 - Native `.smod` Wave 2 + Replay Hardening
- Continue native module transition:
  - `csv`, `date`, `time`, `math`, `string`.
- Introduce replay harness:
  - receipt -> replay -> byte-level output comparison.
- Add 1,000+ deterministic regression receipts across module/runtime combinations.
- Exit gate:
  - replay pass-rate >= 99.5% for STRICT-mode coverage set.

## v1.0.0 - Trust-Layer GA
- Freeze:
  - Determinism Spec v1
  - Receipt Spec v1
  - Policy Spec v1.
- Commit compatibility policy:
  - backward compatibility guarantees
  - migration tooling for receipt and policy schemas.
- Deliver production docs:
  - formal determinism model
  - policy semantics
  - operational runbook
  - security boundary model.
- GA gate:
  - all checklist items in "Infrastructure Threshold" pass.

## Fully Native `.smod` Completion Plan

## Definition of Done
- Every shipped top-level `.smod` module has explicit metadata:
  - `module_format = "smod-runtime"`
  - `runtime_backend = "smod"` or `runtime_backend = "smod-bridge"`.
- No implicit bridge behavior.
- No unlabeled wrapper module in release artifacts.

## Rules
- Prefer `runtime_backend = "smod"` (bridge-free) whenever correctness is preserved.
- Use `runtime_backend = "smod-bridge"` only when security/correctness requires host-native primitives.
- Bridge-backed modules must declare:
  - native call allow-list
  - determinism impact
  - cryptographic/security rationale.

## Current Native Backlog (Top-Level `.smod`)
- Metadata/contract completion needed: `csv`, `date`, `math`, `string`, `time`.
- Existing explicit contracts: `queue`, `stack`, `random`, `uuid`, `regex`, `hashing`, `env`, `fs`, `io`, `json`, `path`.

## Infrastructure Threshold Checklist (v1.0.0 Gate)
- [ ] Deterministic execution modes finalized (`STRICT`, `SEALED`, `NON_DETERMINISTIC`).
- [ ] Receipt spec v1 frozen with canonical event stream + hash chain.
- [ ] Replay engine passes 1,000+ deterministic regression tests.
- [ ] Policy DSL supports static validation and deterministic conflict semantics.
- [ ] Tool boundary enforcement audited and complete.
- [ ] Receipt redaction + signing/encryption capabilities production-ready.
- [ ] Receipt diff and query tooling production-ready.
- [ ] Formal determinism and policy docs published for operators/auditors.

## Immediate Next Actions (Now -> v0.10.4 Kickoff)
- Keep `sona.policy` and `sona.lockfile_manager` under CI smoke coverage.
- Publish Determinism Spec `DRAFT-1` in `docs/spec/`.
- Publish Receipt Spec `0.3` in `docs/spec/`.
- Expand CI smoke to include deterministic rerun and replay command coverage when replay CLI is finalized.
- Start `.smod` metadata completion PR for the 10 metadata-ambiguous top-level modules (after governance gates pass).
