# Changelog

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
