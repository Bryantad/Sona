# Sona: AI-Native Programming with Cognitive Accessibility

[![Source Version](https://img.shields.io/github/v/tag/Bryantad/Sona?label=source&sort=semver)](https://github.com/Bryantad/Sona/tags)
[![Marketplace Version](https://img.shields.io/visual-studio-marketplace/v/Waycoreinc.sona-ai-native-programming?label=marketplace)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)
[![Marketplace Installs](https://img.shields.io/visual-studio-marketplace/i/Waycoreinc.sona-ai-native-programming?label=installs)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)
[![License](https://img.shields.io/github/license/Bryantad/Sona)](https://github.com/Bryantad/Sona/blob/HEAD/LICENSE)

Visual Studio Code support for the Sona programming language.

## What's New in 0.15.4

Sona `0.15.4` adds a release-trust workflow while preserving the extension's
existing editor and AI Console surface.

- `sona-native proof file.sona --guardian-root . --summary` can bind redacted
  Native Proof execution evidence to an initialized Guardian baseline.
- `sona guardian proof verify`, `attest`, `review`, and `history` provide local
  receipt verification, audit history, and governed advisory analysis without
  storing program paths or output in the Guardian attestation or AI context.
- Proof review defaults to Sona's deterministic local analyst and can use a
  configured local Ollama provider; AI output never becomes proof or attestation.
- The extension continues to use the separately installed `sona` CLI for its
  editor commands; install `sona-native` alongside it when using Native Proof.
- Existing **Run Sona File** command and `.sona` / `.smod` syntax highlighting
  remain activation-safe.

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

## Proof and Guardian Guides

- [Native Proof Mode](https://github.com/Bryantad/Sona/blob/main/docs/guides/proof-mode.md)
- [Guardian](https://github.com/Bryantad/Sona/blob/main/docs/guides/guardian.md)
- [Using Native Proof and Guardian Together](https://github.com/Bryantad/Sona/blob/main/docs/guides/proof-and-guardian.md)

## Release Notes

- [0.15.4 release notes](https://github.com/Bryantad/Sona/blob/main/RELEASE_NOTES_v0.15.4.md)

## License

MIT License. See [LICENSE](https://github.com/Bryantad/Sona/blob/main/LICENSE).
