## [0.9.6] — 2025-10-13

### Truth-First Stabilization (Zero-Red Tests + 40 Percent Coverage)

**Overview**
This release focuses on correctness, contract enforcement, and data integrity. All failing tests were eliminated, and total coverage rose to 40.38 percent without inventing new APIs. Each module now declares its exports explicitly, verified through contract tests.

**Highlights**

- 0 failing tests (from 10)
- Coverage 40.38 percent (+12.46 pp)
- API-first guardrails across 18 modules
- 280 total tests (+104), 83 behavior tests

**Added**

- `string.reverse(text: str) → str` (Unicode-safe; exported via `__all__`).
- Fixed and completed `string` case conversions (`words`, `camel_case`, `snake_case`, `kebab_case`) with Unicode-aware boundary detection.
- Contract guardrails for `json, numbers, env, time, csv, path, collection, string, math, random, io, queue, stack, hashing, timer, toml, validation, encoding`.
- Added 62 new behavior tests across 16 modules.

**Fixed**

- Restored `rtrim` to `__all__`.
- Corrected case-conversion functions to handle Unicode boundaries.
- Enabled TOML writer support via `tomli_w` (optional extra).

**Tooling / CI**

- Enforced API-first discipline:

  - Modules must declare canonical exports (`__all__`).
  - Contract tests assert symbol existence and shape.
  - Behavior tests cannot access internals.

- Added contract-assertion helpers under `tests/utils/`.

**Documentation**

- `WORKING_DEFINITION.md` — criteria for “working module.”
- `TESTING.md` — API-first rubric (Inventory → Contract → Behavior).
- Session artifacts: `EXECUTION_SUMMARY_OCT6_2025.md`, `PR_TRUTH_FIRST_STABILIZATION.md`, `MERGE_READY_ARTIFACTS.md`, `TEST_ACCURACY_AUDIT_V096.md`, `V096_RELEASE_COMPLETE.md`.
- `NEXT_PR_PLAN.md` — v0.9.7 targets 50 percent coverage.

**Metrics (Before → After → Δ)**

- Tests: 176 → 280 (+104)
- Passing: 166 → 280 (+114)
- Failing: 10 → 0 (–10)
- Coverage: 27.92 → 40.38 (+12.46 pp)

**Top Coverage Gains**

- `timer` 43.33 → 96.67 (+53.34 pp)
- `hashing` 25.00 → 87.50 (+62.50 pp)
- `io` 46.15 → 87.18 (+41.03 pp)
- `collection` 19.49 → 81.36 (+61.87 pp)
- `numbers` 12.90 → 74.19 (+61.29 pp)
- `path` 29.63 → 64.81 (+35.18 pp)
- `env` 12.97 → 40.54 (+27.57 pp)
- `csv` 15.57 → 40.98 (+25.41 pp)
- `json` 12.00 → 35.27 (+23.27 pp)
- `time` 18.24 → 41.89 (+23.65 pp)

**Next**

- Coverage target met and exceeded.
- Eight modules qualify as fully working ( `boolean, type, operators, math, validation, uuid, timer, io, hashing` ).
- v0.9.7 will expand to the remaining 17 modules to surpass 50 percent coverage.

---

## [0.9.5] — 2025-09-28

### Marketplace Hotfix (VS Code Extension)

**Changed**

- Re-labeled v0.9.4.1 → v0.9.5 for Marketplace compliance.
- Improved listing (Overview, icon, banner, screenshots, keywords, Q&A).
- Validated stdlib packaging (22 modules) with `MANIFEST.json`.

**Fixed**

- Corrected Marketplace metadata and package integrity.

**Notes**

- Language features identical to v0.9.4.1.
- JSON enhancements (RFC 7396 merge_patch, JSON Pointer, deep_update) unchanged.
- Deterministic testing on Windows + Python 3.12 (coverage ≥ 85 percent).
- Regex module retains timeout semantics.

---

## [0.9.4] — 2025-09-26

### Type System MVP and Infrastructure

**Added**

- Union-type support (`int|str|bool`) with runtime validation.
- Enhanced `@check_types` decorator for args and returns with explicit bool/int separation.
- 24 tests total (5 new union cases).
- Demo: `day3_union_type_demo.py`.
- Config flag `TypeCheckingConfig.enabled`.

**Infrastructure**

- Deterministic packaging (lockfile + SHA256 verification).
- Expanded glob patterns (`**`) for Windows support.

**Impact**

- Closes runtime type-enforcement gap and lays foundation for advanced typing.

---

## [0.9.3] — 2025-09-15

### Resilience and Observability (No Breaking Changes)

**Added**

- Feature-flag system (off by default).
- LRU + TTL cache, circuit breaker, micro-batch queue.
- Policy engine (JSON rules + provider allow-list).
- Rotated JSONL performance logs.
- CLI tools: `ai-plan`, `ai-review`, `build-info`, `doctor`, `probe`.
- Default security policy and diagnostic probe.
- Optional dependency groups: `[ai]`, `[dev]`.
- Baseline Python 3.11+.

**Changed**

- Unified entry point at `sona.cli:main` (legacy retained).

**Security**

- Conservative default `sona-policy.json`.

**Documentation**

- Tutorials, teacher guide, feature-flag matrix.

**Internal**

- Lazy imports for diagnostics and graceful AI degrade.

---

## [0.9.2] — 2025-09-03

### Version Alignment and Stability

- Synchronized interpreter, transpiler, CLI, and type system to v0.9.2.
- Fixed version mismatches and metadata errors.
- Deterministic build and dependency structure.

---

## [0.9.1] — 2025-08-19

### Maintenance Release

- Minor stability fixes, typo corrections, and documentation updates.
- Prepared infrastructure for the 0.9.2 alignment release.

---

## [0.9.0] — 2025-08-17

### Major Release — Development Environment and VS Code Integration

**CLI**

- `sona run`, `sona repl`, `sona transpile` (7 targets), `sona format`, `sona check`, `sona info`, `sona init`, `sona clean`, `sona docs`.

**VS Code**

- Integrated command palette, context menus, keybindings, and target selection.
- Terminal integration for real-time execution.

**Transpilation**

- Targets: Python, JavaScript, TypeScript, Java, C#, Go, Rust.
- Cognitive block preservation and robust error recovery.

**Cognitive Accessibility**

- Flow-state monitoring, focus mode, and error clarity for neurodiverse developers.

**Developer Experience**

- Deterministic packaging, cross-platform support, comprehensive examples, and consistent error UX.

**Breaking Changes**

- Command syntax standardized (`sona run file.sona`, `sona repl`).

---

## Earlier Versions (0.7.0 → 0.5.0)

Summarized: Introduced OOP foundations, dictionary/array enhancements, module system (.smod) with dotted access, REPL diagnostics (`:env`, `:clear`, `:reload`, `:trace`, `:profile`), security hardening, and core interpreter stability fixes. See respective version files for full details.

---
