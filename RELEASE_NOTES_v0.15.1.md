# Sona 0.15.1 - Local AI Setup, Responsive CLI AI, and VS Code AI Console Preview

Sona `0.15.1` is an update release on top of the `0.15.0` cognitive runtime
and Guardian resilience foundation. This release focuses on fixing the broken
AI setup path, making editor-triggered AI commands responsive by default,
adding local Ollama/Qwen setup support, and shipping the first preview of a
Sona-owned VS Code AI side panel.

## Release Summary

This update includes:

- Restored `sona setup manual` and `sona setup azure --manual` by adding the
  missing `sona.setup_azure` module.
- Added manual local AI setup for already-downloaded Ollama models.
- Added Qwen model detection and selection for local setup.
- Made `sona explain` and `sona suggest` fast by default with deterministic
  local analysis.
- Kept model-backed `explain` and `suggest` available through explicit `--ai`
  opt-in or `SONA_ENHANCED_CLI_AI`.
- Reduced slow AI startup paths by lazily importing AI modules and using short
  Ollama readiness checks.
- Added the preview **Sona AI Console** VS Code sidebar webview.
- Added provider-ready routing for `Sona`, `Qwen`, `Claude`, `Codex`, and
  `Local` agent modes.
- Added VS Code extension packaging, smoke checks, icon verification, and VSIX
  ignore rules.
- Updated Sona package, CLI, stdlib, LSP, SPM, docs, tests, and release gates
  from `0.15.0` to `0.15.1`.

## Fixed Setup Commands

Before this release, setup commands could fail with:

```text
Failed to load setup: No module named 'sona.setup_azure'
Failed to load Azure setup: No module named 'sona.setup_azure'
```

`0.15.1` restores the setup module and covers both setup entry points:

```powershell
python -m sona setup manual --workspace .
python -m sona setup azure --manual --workspace .
```

The restored setup helper now supports:

- Azure OpenAI interactive setup through the Azure CLI.
- Manual Azure setup when users already have endpoint/key/deployment values.
- Manual local setup for Ollama-backed AI.
- Workspace `.env` updates without discarding unrelated existing entries.
- User config writes under the Sona home config directory.
- Dry-run behavior used by tests.
- Clear error messages when Azure CLI, Ollama, or a requested local model is
  not available.

## Local Ollama and Qwen Setup

Manual setup can now choose a local provider:

```text
Provider [azure/local] (Enter for azure):
```

Local setup writes workspace `.env` values like:

```env
SONA_AI_PROVIDER=ollama
SONA_AI_BACKEND=ollama
SONA_OLLAMA_MODEL=<installed-model>
OLLAMA_HOST=http://localhost:11434
SONA_AI_MAX_TOKENS=512
SONA_AI_TEMPERATURE=0.2
```

The setup flow checks whether Ollama is running, asks Ollama for installed
models, and selects a Qwen model when one is available. The preference order
includes Qwen coder models and general Qwen models, including:

- `qwen3-coder-next`
- `qwen3-coder:30b`
- `qwen3-coder:480b`
- `qwen2.5-coder:7b`
- `qwen2.5-coder:14b`
- `qwen2.5-coder:32b`
- `qwen2.5-coder:3b`
- `qwen3:32b`
- `qwen3:14b`
- `qwen3:8b`
- `qwen2.5:14b`
- `qwen2.5:7b`
- `qwen2.5:3b`

If the selected model is missing, setup now fails with an actionable message
instead of continuing into a broken configuration:

```text
Model '<model>' is not installed in Ollama.
Download it with: sona ai-model pull --model <model>
Or run: ollama pull <model>
```

## AI Backend Startup Improvements

The AI package now avoids heavy imports until an AI-backed command actually
needs them. This keeps normal CLI startup and editor command invocations from
paying the cost of model initialization.

Backend selection now:

- Loads workspace `.env` once so local setup can influence AI behavior.
- Honors `SONA_AI_BACKEND=ollama`, `local`, or `offline`.
- Honors `SONA_OLLAMA_MODEL` and `OLLAMA_HOST`.
- Performs bounded Ollama readiness checks before selecting the Ollama backend.
- Falls back to the local GPT-2 integration only when appropriate.
- Caches the selected backend and exposes a reset helper for tests.

Ollama integration now uses centralized local model helpers, short readiness
checks, normalized host handling, and clearer error text when Ollama is not
running or the model is not installed.

## Responsive `explain` and `suggest`

`sona explain` and `sona suggest` no longer require a model startup by default.
This directly addresses editor timeouts where VS Code invoked commands such as:

```powershell
python -m sona suggest examples\stdlib_math.sona
python -m sona explain examples\stdlib_math.sona
```

Default behavior is now deterministic local analysis:

- `sona explain <file>` summarizes imports, functions, prints, returns,
  conditionals, loops, and code structure.
- `sona explain <file> --style detailed` includes structural counts.
- `sona explain <file> --style cognitive` includes cognitive review notes.
- `sona suggest <file>` returns local cognitive, performance, and accessibility
  suggestions.
- `sona suggest <file> --cognitive`, `--performance`, or `--accessibility`
  narrows the suggestion category.

Model-backed behavior remains available, but only when explicitly requested:

```powershell
python -m sona explain examples\stdlib_math.sona --ai
python -m sona suggest examples\stdlib_math.sona --ai
```

It can also be enabled for enhanced CLI commands with:

```powershell
$env:SONA_ENHANCED_CLI_AI = "1"
```

This keeps the default editor path local and fast while preserving explicit AI
mode for users who have configured a backend.

## Sona AI Console Preview

`0.15.1` adds the first version of **Sona AI Console**, a Sona-owned VS Code
sidebar chat surface.

VS Code contribution details:

- View container: `sona`
- View ID: `sona.aiConsole`
- Primary command: `sona.aiConsole.focus`
- Clear command: `sona.aiConsole.clear`
- Agent command: `sona.aiConsole.selectAgent`
- Command palette title: `Sona: Open AI Console`

The UI includes:

- Header: `Sona AI Console`
- Agent selector tabs for `Sona`, `Qwen`, `Claude`, `Codex`, and `Local`
- Active agent label
- Chat message area
- Input box
- Send button
- Context toggles for current file, selected text, workspace summary, and
  diagnostics
- Provider status area
- Clear chat button
- Enter-to-send and Shift+Enter-for-newline behavior
- Disabled send state while a request is running

The webview uses local CSS and JavaScript assets, preserves chat state, and
uses message passing between the webview and extension host.

## AI Console Provider Routing

The console ships with an internal provider abstraction and agent registry:

- `sona`: implemented as a deterministic local response. No network calls.
- `local`: implemented as a deterministic local response. No network calls.
- `qwen`: implemented only when a local Ollama/Qwen configuration is present.
- `claude`: placeholder-only and returns `not_configured`.
- `codex`: placeholder-only and returns `not_configured`.

Qwen configuration can come from VS Code settings or workspace `.env` values.
The console recognizes `.env` values written by Sona manual local setup:

```env
SONA_AI_PROVIDER=ollama
SONA_AI_BACKEND=ollama
SONA_OLLAMA_MODEL=<qwen-model>
OLLAMA_HOST=<ollama-url>
```

When Qwen is configured, the extension calls local Ollama `/api/generate`.
When Qwen is not configured, the UI shows a clear not-configured response
instead of failing.

Claude and Codex are intentionally not direct integrations in this release.
The console does not control external Claude or Codex extensions and does not
claim those providers are working.

## AI Console Context Collection

Prompt context is opt-in through UI toggles. The collector can include:

- Current file path or URI
- Visible editor language ID
- Selected text, clipped to a safe maximum
- Workspace folder name
- Diagnostics for the active file, including message, severity, source, code,
  line, character, and file label

The console does not send full workspace contents by default.

## VS Code Extension Packaging

This release adds a primary `vscode-extension/` package for the Sona extension,
including:

- `package.json` contribution points for commands, settings, view container,
  and `sona.aiConsole`.
- TypeScript source under `vscode-extension/src/`.
- Compiled runtime files under `vscode-extension/out/`.
- Webview CSS and JavaScript under `vscode-extension/media/`.
- AI Console documentation under `vscode-extension/docs/SONA_AI_CONSOLE.md`.
- Icon verification script.
- Smoke test script for the AI Console contribution and provider behavior.
- `.vscodeignore` rules to exclude source maps, TypeScript source, scripts,
  and nested VSIX files from the packaged extension.

The VSIX was rebuilt as:

```text
vscode-extension/sona-ai-native-programming-0.15.1.vsix
```

The VSIX is a release artifact and is ignored by git.

## Version and Metadata Updates

The release version was updated to `0.15.1` across the active release surface:

- Python package metadata
- `sona.__version__`
- CLI version output and help text
- REPL banner
- Interpreter `__version__`
- LSP server version
- SPM default project version
- Stdlib manifest and stdlib package version
- Active README and docs references
- Release gate scripts
- Release metadata validator inputs
- Tests that assert current release metadata

Historical `0.15.0` release documents remain historical references and were not
rewritten as `0.15.1` documents.

## Tests Added or Updated

New and updated tests cover:

- `sona.setup_azure` importability and setup routing.
- Manual Azure setup `.env` writes.
- Manual local Ollama setup `.env` writes.
- Qwen model detection and missing-model handling.
- Runtime startup behavior that should not eagerly load heavy AI modules.
- Current stdlib manifest version assertions for `0.15.1`.
- AI Console extension smoke checks:
  - command registration
  - `sona.aiConsole` view contribution
  - expected agent list
  - not-configured provider responses
  - deterministic local provider responses
  - CSP presence in generated webview HTML
  - absence of hardcoded secret-like values in the checked surface

## Validation Run

Validated locally for this release:

```powershell
python tools\validate_release_metadata.py --version 0.15.1
python -m sona --version
python -m sona check examples\hello.sona
python tools\run_examples.py
python -m sona probe stdlib
python -m sona probe accessibility
python -m sona probe guardian
python -m pytest -q tests

cd vscode-extension
npm run compile
npm test
npm run package:vsix
```

Final full test result:

```text
156 passed, 2 warnings
```

The two warnings are existing Lark deprecation warnings from Python's
dependency stack.

## Artifact Hashes

```text
sona-ai-native-programming-0.15.1.vsix
Path: vscode-extension/sona-ai-native-programming-0.15.1.vsix
Size: 1183192 bytes
SHA-256: CBEF61B66E82D0D855830CF35501117D4BED5829EE87CF31312FA2DB09971426
```

VSIX archive inspection confirmed no source maps and no nested VSIX payloads in
the packaged extension.

## Explicit Release Boundaries

This release does not include:

- Full Claude provider integration.
- Full Codex provider integration.
- Control of external Claude, Codex, or other AI extensions.
- Hardcoded API keys or credentials.
- Automatic external API calls before a provider is configured.
- Full native compiler independence.
- LLVM code generation.
- Self-hosting.
- Production formatter support.
- Production debugger support.
- Full benchmark expansion.

Sona `0.15.1` remains Python-backed. The AI Console is a preview/developer
feature, and the safe public wording is:

```text
Sona AI Console adds a local Sona-owned chat surface with selectable agent
modes and provider-ready routing.
```
