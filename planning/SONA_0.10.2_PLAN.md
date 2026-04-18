# Sona v0.10.2 — 1-Month Development Plan (Locked)

**Timebox:** 4 weeks (month-long dev cycle)  
**Goal:** A polished, publishable, and testable Sona experience end-to-end (runtime + docs + VS Code).

## Principles

- Ship fewer things, but finish them.
- No “almost working”: each feature needs tests + docs + examples.
- Keep Marketplace packaging clean (publisher, repo metadata, icons, size).

## Scope (Locked)

### 1) VS Code Extension Release Engineering

- Ensure Marketplace-ready manifest metadata (publisher, repository, valid categories).
- Icon + branding always present.
- Keep VSIX small (tight `.vscodeignore`, avoid shipping internal artifacts).
- Optional: bundle dependencies to improve performance.

### 2) Cognitive UX (Editor + Runtime)

- Make cognitive features discoverable with a minimal onboarding flow.
- Keep outputs deterministic and “offline safe” by default.
- Improve report export ergonomics (paths, formats, defaults).

### 3) Stability & Tests

- Expand smoke tests around:
  - CLI entrypoints
  - stdlib import resolution
  - critical language constructs
- Establish a single “release gate” script and document it.

### 4) Language Gap & Bug Fix Pass (Runtime + Parser + Stdlib + LSP)

Goal: close known language gaps and reliability issues that block real usage. This is a
catch-up release, not a feature-expansion release.

**Release blockers (must ship in 0.10.2):**

- Parser/runtime alignment with real-world syntax:
  - `repeat while` and `repeat until` loops parse + execute correctly.
  - Trailing commas in lists/dicts parse correctly.
  - Multiline string edge cases are handled or explicitly disallowed with clear errors.
- Imports parity:
  - `import x as y` works reliably.
  - `from x import a, b` and `from x import a as b` parse + execute correctly.
- LSP correctness:
  - Go-to-definition and outline recognize `func` / `def` (not just `fn`).
- Stdlib parity (minimum high-impact gaps):
  - `collection.dict.deep_get`
  - `string.template`
  - `assert.deep_equals` and `assert.throws` (or deprecate + alias existing names)
  - `test.only` and `test.snapshot` (minimal implementation acceptable)

**Non-goals:** no new language features beyond the gaps above. If it is not in this list,
it is out of scope for 0.10.2.

## Week-by-Week Plan

### Week 1 — Planning + Release Baseline

- Lock the v0.10.2 scope (add/remove items explicitly).
- Decide release gating: what must pass to cut a release.
- Confirm docs nav + GitHub release page workflow.

**Deliverables:**

- Updated v0.10.2 checklist
- Minimal release gate script (documented)

### Week 2 — VS Code Packaging + UX Polish

- Validate publishing path (no publisher/category/repo errors).
- Reduce VSIX size and remove accidental inclusions.
- Quick UX sweep: commands, activation events, error messages.

**Deliverables:**

- Marketplace-dry-run checklist pass
- Packaged VSIX that is small and branded

### Week 3 — Runtime Hardening

- Address the top reliability issues discovered during 0.10.1 testing.
- Add/strengthen tests for the fixed behaviors.

**Deliverables:**

- Test coverage improvements for fixed issues
- Updated troubleshooting docs

### Week 4 — Release Candidate + Docs Freeze

- Cut an RC build, do a short test pass, then freeze docs.
- Prepare release notes and publish artifacts.

**Deliverables:**

- v0.10.2 release notes draft
- Final VSIX + Python package ready to publish

## Release Checklist (High-Level)

- [ ] `pyproject.toml` version matches release tag
- [ ] README and docs point to correct release notes
- [ ] VS Code extension publishes under the right publisher and shows its icon
- [ ] VSIX size reasonable (no dev artifacts)
- [ ] Automated tests pass; smoke test script passes

---

If you tell me the exact priorities for v0.10.2 (runtime features vs editor features), I can turn this into a locked checklist with concrete acceptance criteria.

---

## Locked Checklist (acceptance criteria)

Top priorities (proposed):

- 1. VS Code packaging & branding
- 2. Runtime stability & tests
- 3. Language gap/bug fixes
- 4. Docs & release process

Notes:

- I added `assets/sona-lock.png` (128px) at the repo root for website/lock usage.
- I verified extension icons exist across `extensions/*`.

Each item below must include tests/docs and a short example before being marked done.

Week 1 — Planning + Release Baseline

- [ ] Lock scope and acceptance criteria (documented in `planning/SONA_0.10.2_PLAN.md`)
- [ ] Create `scripts/release_gate.ps1` that runs smoke tests and checks versions
- [ ] Define “release blockers” list (language gaps) and tie each to a test file

Week 2 — VS Code Packaging + UX Polish

- [ ] Marketplace dry-run: `vsce package` success with no repository/category errors
- [ ] Icon present and validated inside VSIX (`package.json` `icon` file exists inside VSIX)
- [ ] `.vscodeignore` tightened and VSIX < 1.5MB (or justified)

Week 3 — Runtime Hardening

- [ ] Fix language gaps & bugs (each with a regression test):
  - [ ] `repeat while` and `repeat until`
  - [ ] trailing commas in lists/dicts
  - [ ] multiline string edge cases (or explicit, consistent errors)
  - [ ] `from x import y` and `import x as y`
  - [ ] LSP go-to-definition/outline recognizes `func` and `def`
  - [ ] stdlib parity: `collection.dict.deep_get`, `string.template`
  - [ ] stdlib parity: `assert.deep_equals`, `assert.throws`
  - [ ] stdlib parity: `test.only`, `test.snapshot`
- [ ] Add smoke tests: CLI entrypoints, stdlib import resolution, parser/semantic quickchecks

Week 4 — Release Candidate + Docs Freeze

- [ ] Cut RC artifacts: `sona-0.10.2rc`, `sona-ai-native-programming-0.10.2-vsix` (packaged)
- [ ] Docs freeze + release notes drafted and placed in `docs/release-notes/v0.10.2.md`

Acceptance criteria (global):

- All checks in `scripts/release_gate.ps1` pass locally.
- `pyproject.toml` version matches tag `v0.10.2` at release time.
- VSIX publishes under `Waycoreinc` and the Marketplace shows the correct icon.
- Language gap/bug fix list above is complete and each item has a test + doc note.

---

When you confirm the top-3 priorities (or change them), I will: (A) convert these checklist items into tracked git changes, (B) create a milestone + issues template, and (C) prepare a one-month sprint board you can use.
