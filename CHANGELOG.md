# Changelog

## 0.15.6

- Added the deterministic Sona Guide layer for Guided, Balanced, and Expert
  explanations, focused diagnostics, preview-first quick fixes, local learning
  profiles, executable examples, and lessons.
- Added Guide-backed CLI, LSP, and VS Code workflows while preserving the
  canonical diagnostic and Proof Mode / Guardian fact contracts.
- Hardened Native executable selection, version preflight, runtime diagnostic
  handoff, and standard-library migration guidance.
- Added release-candidate packaging, acceptance auditing, and platform
  certification workflow definitions for portable artifacts and Native Core.
- Preserved Sona syntax, schema-1 Proof Mode compatibility, local-only
  learning state, and the explicit limits on authentication and attestation.

## 0.15.5

- Added shared `sona proof verify` and `sona proof inspect` commands with
  schema-1 compatibility, canonical JSON enforcement, self-hash validation,
  fail-closed diagnostics, and normalized human/JSON output.
- Extended new receipts with validated Native executable identity and an
  optional build-supplied source revision while preserving 0.15.4 receipts.
- Hardened Guardian policy, effect evaluation, zero-configuration onboarding,
  local explanation, and Guardian-bound Proof Mode workflows without adding
  signatures, PKI, remote attestation, or cloud services.
- Stabilized the language server's supported diagnostics, completion, hover,
  local definition, and document-symbol surface.
- Added a CLI-backed Proof Mode Explorer to the VS Code extension; receipt
  verification remains in the shared Python verifier, not TypeScript.
- Hardened local-only SPM initialization, locking, installation, verification,
  path containment, integrity checking, and rollback behavior.
- Added four executable trusted-workflow examples for AI action evidence,
  auditable calculation, a compatibility-runtime service API, and bounded
  local deployment evidence.
- Added the normative schema-1 specification, canonicalization contract,
  effect vocabulary, compatibility rules, threat model, and assurance levels.
- Preserved Sona syntax, schema-1 required fields, frozen 0.15.4 vectors,
  Python compatibility behavior, and explicit Native HTTP limitations.

## 0.15.4

- Established one schema-2 standard-library manifest and generated catalog for
  146 preserved public modules and the 11-module certified foundation.
- Added canonical filesystem, HTTP, JSON, random, stream, input, string, date,
  and time APIs with structured diagnostic families.
- Added safe-mode filesystem/network restrictions to the Python-compatible
  runtime and explicit filesystem/network capability flags to Native Core.
- Added Native Core host-module implementations for the bounded foundation;
  native HTTP remains explicitly unavailable with `SONA-HTTP-005`.
- Added bounded Python/Native standard-library conformance fixtures, runtime
  capability regressions, HTTP mock-server tests, and executable documentation
  examples.
- Updated the VS Code extension's `brace-expansion` resolution to 5.0.9 for
  the current production dependency audit.
- Added an opt-in `sona proof --summary` terminal confirmation for saved proof
  receipts while preserving the default machine-compatible output contract.
- Added an opt-in Guardian-bound Native Proof chain: baseline-tracked native
  receipts, read-only Guardian verification, clean-state attestation, and
  redacted local audit history without adding Python to Native Core.
- Added governed `sona guardian proof review`: verified redacted facts can be
  reviewed by Sona's deterministic analyst or an explicitly selected AI
  provider, while model output remains outside the trust and attestation chain.
- Added task-oriented guides for Native Proof Mode, Guardian drift and recovery,
  and the complete Guardian-bound Proof and advisory AI workflow.
- Added host-matched 0.15.4 release-candidate packaging for Windows x86-64,
  Linux x86-64/ARM64, and macOS Intel/Apple Silicon, plus one portable wheel,
  source distribution, VSIX, machine verifier, checksum authority, and release
  manifest. Android and iOS remain explicit compile-only experiments.
- Preserved 0.15.x aliases, Python compatibility semantics, cognitive runtime,
  Guardian interfaces, and workspace-module precedence.

## 0.15.1

- Restored manual and Azure AI setup loading.
- Added local Ollama/Qwen setup with installed model auto-detection.
- Kept `sona explain` and `sona suggest` fast by default with local static
  analysis; model-backed output is opt-in through `--ai`.
- Added the preview Sona AI Console VS Code sidebar view with selectable
  provider-ready agent modes.
- Rebuilt the primary VS Code extension package for `0.15.1`.

## 0.15.0

- Added the cognitive-accessibility runtime foundation with 55 public modules:
  21 stable modules and 34 experimental modules.
- Added local-only Guardian resilience with trusted configuration, SHA-256
  inventory, snapshots, diff, quarantine, rollback, verification, circuit
  breaker, reports, and audit history.
- Made stdlib probing static and manifest-driven.
- Added release inventory, module matrix, import-purity, and metadata gates.

## 0.14.1

- Moved the public stdlib foundation toward Sona-authored `.smod` modules.
- Added release hardening for Python artifacts and the primary VS Code
  extension package.
