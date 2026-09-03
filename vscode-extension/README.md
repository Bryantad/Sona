# Sona: AI-Native Programming with Cognitive Accessibility

[![Source Version](https://img.shields.io/github/v/tag/Bryantad/Sona?label=source&sort=semver)](https://github.com/Bryantad/Sona/tags)
[![Marketplace Version](https://img.shields.io/visual-studio-marketplace/v/Waycoreinc.sona-ai-native-programming?label=marketplace)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)
[![Marketplace Installs](https://img.shields.io/visual-studio-marketplace/i/Waycoreinc.sona-ai-native-programming?label=installs)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)
[![License](https://img.shields.io/github/license/Bryantad/Sona)](https://github.com/Bryantad/Sona/blob/HEAD/LICENSE)

Visual Studio Code support for the Sona programming language.

## What's New in 0.15.5

Sona `0.15.5` adds a CLI-backed **Proof Mode Explorer** to the
Sona activity bar. It displays execution status, shared-verifier status, Native
Core identity, capabilities, observed effects, Guardian binding, and redacted
evidence identities.

The explorer does not verify receipts in TypeScript. **Verify Receipt** and
**Inspect Receipt** call the installed Sona CLI and display the shared Proof
Mode verifier's normalized result.

It also uses the stabilized language server for diagnostics, completion, hover,
local definition lookup, and document symbols. Guardian review and AI remain
outside the receipt verification chain, and Native HTTP remains unavailable.

## How to Use Sona in VS Code

1. Install Python 3.11 or newer and the Sona CLI:

   ```bash
   pip install sona-lang
   ```

2. Open a folder and create `hello.sona`:

   ```sona
   print("Hello, Sona!");
   ```

3. Open the Command Palette and run **Sona: Run Sona File**.
4. Use `.sona` files for Sona programs and `.smod` files for Sona modules.

## Quick Start

1. Install Python 3.11 or newer.
2. Install the Sona CLI:

   ```bash
   pip install sona-lang
   ```

3. Check the CLI:

   ```bash
   sona --version
   sona --help
   sona check hello.sona
   sona check hello.sona --json
   ```

4. Create `hello.sona`:

   ```sona
   print("Hello from Sona!");
   ```

5. Run it:

   ```bash
   sona run hello.sona
   ```

See the full quickstart in `docs/QUICKSTART.md`.

## Features

- Syntax highlighting for `.sona` and `.smod`.
- Canonical diagnostics, completion, hover, local go to definition, and
  document symbols through the Sona language server.
- Run, check, format, profile, benchmark, and transpile commands.
- REPL integration for interactive exploration.
- Optional AI-assisted explain and suggestion commands.
- Preview Sona AI Console with local Sona-owned chat, selectable agent modes, and provider-ready routing.
- Cognitive accessibility workflows including Focus Mode, Working Memory, and user profiles.

## Language Server

The extension starts `python -P -m sona.lsp_server --stdio` for Sona files. The
selected Python environment must be able to import both `sona.lsp_server` and
pygls; installing `sona-lang` supplies the supported dependency set.

Set `sona.cli.pythonPath` when you want a specific interpreter. When that
setting is not explicitly configured, the extension checks the workspace
`.venv` before using `python` from `PATH`.

Sona `0.15.5` supports canonical diagnostics, local and stdlib completion,
known-symbol hover, current-document definition, and top-level document
symbols. References, rename, cross-file indexing, and LSP formatting remain
deferred and are not advertised by the server. The **Sona: Format Code** command
is a separate CLI-backed command, not an LSP formatting capability.

## Useful Commands

| Command | Description |
| --- | --- |
| **Sona: Welcome & Setup** | Opens extension onboarding. |
| **Sona: Run Sona File** | Runs the active Sona file. |
| **Sona: Run with Proof Mode** | Runs the active saved Sona file with Native Core and creates a new receipt. |
| **Sona: Verify Receipt** | Validates a receipt with the shared Proof Mode verifier. |
| **Sona: Inspect Receipt** | Displays verified receipt facts in the Proof Mode Explorer. |
| **Sona: Open Receipt** | Opens the current receipt as a document. |
| **Sona: Explain with Guardian** | Runs the existing local Guardian receipt review for a trusted workspace. |
| **Sona: Check Syntax** | Checks syntax for the active Sona file. |
| **Sona: Format Code** | Formats Sona code. |
| **Sona: Start REPL** | Starts an interactive Sona shell. |
| **Sona: Open AI Console** | Opens the preview Sona-owned AI chat surface. |
| **Sona: Show System Info** | Shows runtime and extension environment details. |

## Configuration

```json
{
  "sona.cli.pythonPath": "python",
  "sona.cli.timeout": 30000,
  "sona.userProfile": "neurotypical",
  "sona.ai.autoSetup": true,
  "sona.ai.defaultAgent": "sona",
  "sona.ai.qwen.enabled": false,
  "sona.ai.qwen.model": "qwen2.5-coder:7b",
  "sona.ai.ollama.url": "http://127.0.0.1:11434",
  "sona.ai.claude.enabled": false,
  "sona.ai.codex.enabled": false,
  "sona.onboarding.showWelcome": true
}
```

Sona AI Console is a preview feature. Claude and Codex are placeholder agent modes unless a proper provider integration is added; the extension does not control external AI extensions.

For receipts produced by the new 0.15.5 Native runtime, the explorer also
shows the validated Native executable digest and an optional build-supplied
source revision. These are correlation identities from the shared verifier,
not authenticated provenance.

Proof Mode execution and Guardian review are disabled for untrusted VS Code
workspaces. Receipt verification and inspection are read-only. The extension
invokes Python in safe-path mode and does not add the workspace to
`PYTHONPATH`.

## Proof and Guardian Guides

- [Native Proof Mode](https://github.com/Bryantad/Sona/blob/main/docs/guides/proof-mode.md)
- [Guardian](https://github.com/Bryantad/Sona/blob/main/docs/guides/guardian.md)
- [Using Native Proof and Guardian Together](https://github.com/Bryantad/Sona/blob/main/docs/guides/proof-and-guardian.md)

## Release Notes

- [0.15.5 release notes](https://github.com/Bryantad/Sona/blob/main/RELEASE_NOTES_v0.15.5.md)

## License

MIT License. See [LICENSE](https://github.com/Bryantad/Sona/blob/main/LICENSE).
