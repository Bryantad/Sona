# Sona 0.15.1 - Local AI Setup and VS Code Console Preview

Sona `0.15.1` is a focused maintenance and developer-experience release on
top of the `0.15.0` cognitive runtime and Guardian resilience foundation.

## Highlights

- Restores the Sona setup module so `sona setup manual` and
  `sona setup azure --manual` load cleanly.
- Adds local Ollama setup support to manual setup, including installed Qwen
  model auto-detection.
- Keeps `sona explain` and `sona suggest` responsive by using deterministic
  local analysis by default, with model-backed output available through
  explicit `--ai`.
- Adds the preview Sona-owned VS Code sidebar chat surface,
  **Sona AI Console**, with selectable agent modes and provider-ready routing.
- Rebuilds the primary VS Code extension as
  `sona-ai-native-programming-0.15.1.vsix`.

## Sona AI Console

Sona AI Console adds a local Sona-owned chat surface with selectable agent
modes and provider-ready routing.

Agents shown in the UI:

- Sona
- Qwen
- Claude
- Codex
- Local

Implemented providers:

- `Sona`: deterministic local response, no network calls.
- `Local`: deterministic local response, no network calls.
- `Qwen`: wired only when a local Ollama/Qwen configuration is present.

Placeholder-only providers:

- `Claude`: reports `not_configured`.
- `Codex`: reports `not_configured` and does not control external Codex
  extensions.

This release does not claim working Claude or Codex integration.

## Local AI Setup

Manual setup now supports:

```powershell
python -m sona setup manual --workspace .
```

Choose `local` to use an installed Ollama model. The setup flow detects Qwen
models such as `qwen2.5:14b` and writes workspace `.env` entries:

```env
SONA_AI_PROVIDER=ollama
SONA_AI_BACKEND=ollama
SONA_OLLAMA_MODEL=<installed-model>
OLLAMA_HOST=http://localhost:11434
```

## CLI Responsiveness

`sona explain` and `sona suggest` now default to fast local analysis so editor
commands do not block on a slow local model.

Use `--ai` for explicit model-backed output:

```powershell
python -m sona explain examples\stdlib_math.sona --ai
python -m sona suggest examples\stdlib_math.sona --ai
```

## Validation

Validated locally:

```powershell
python -m pytest tests\cli -q
python tools\run_examples.py
python tools\validate_release_metadata.py --version 0.15.1
python -m sona --version
python -m sona check examples\hello.sona
python -m sona probe stdlib
python -m sona probe accessibility
python -m sona probe guardian
cd vscode-extension
npm run compile
npm test
npm run package:vsix
```

VSIX artifact:

```text
vscode-extension/sona-ai-native-programming-0.15.1.vsix
Size: 1183192 bytes
SHA-256: CBEF61B66E82D0D855830CF35501117D4BED5829EE87CF31312FA2DB09971426
```

## Release Boundary

Sona `0.15.1` remains Python-backed. Native compiler independence, LLVM code
generation, self-hosting, package publishing, full LSP completion, formatter
support, debugger support, and benchmark expansion remain roadmap items.
