# Sona: AI-Native Programming with Cognitive Accessibility

[![Source Version](https://img.shields.io/github/v/tag/Bryantad/Sona?label=source&sort=semver)](https://github.com/Bryantad/Sona/tags)
[![Marketplace Version](https://img.shields.io/visual-studio-marketplace/v/Waycoreinc.sona-ai-native-programming?label=marketplace)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)
[![Marketplace Installs](https://img.shields.io/visual-studio-marketplace/i/Waycoreinc.sona-ai-native-programming?label=installs)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)
[![License](https://img.shields.io/github/license/Bryantad/Sona)](https://github.com/Bryantad/Sona/blob/HEAD/LICENSE)

Visual Studio Code support for the Sona programming language.

## What's New in 0.15.1

Sona `0.15.1` focuses on Cognitive Diagnostics and language-wide audit
hardening while preserving the existing extension feature surface.

- Stable CLI flow remains available: `sona --version`, `sona --help`, `sona run file.sona`, and `sona file.sona`.
- `sona check file.sona` reports Cognitive Diagnostics for common mistakes.
- `sona check file.sona --json` returns structured diagnostics for tools.
- Existing **Run Sona File** command remains available from the Command Palette and editor context menu.
- `.sona` and `.smod` syntax highlighting remains activation-safe.

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
- Run, check, format, profile, benchmark, and transpile commands.
- REPL integration for interactive exploration.
- Optional AI-assisted explain and suggestion commands.
- Preview Sona AI Console with local Sona-owned chat, selectable agent modes, and provider-ready routing.
- Cognitive accessibility workflows including Focus Mode, Working Memory, and user profiles.

## Useful Commands

| Command | Description |
| --- | --- |
| **Sona: Welcome & Setup** | Opens extension onboarding. |
| **Sona: Run Sona File** | Runs the active Sona file. |
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

## Release Notes

- [Release notes](https://github.com/Bryantad/Sona/blob/main/RELEASE_NOTES_v0.15.1.md)

## License

MIT License. See [LICENSE](https://github.com/Bryantad/Sona/blob/main/LICENSE).
