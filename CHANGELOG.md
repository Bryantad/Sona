# Changelog

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
