# Sona: AI-Native Programming with Cognitive Accessibility

[![Version](https://img.shields.io/badge/version-0.14.0-blue.svg)](https://github.com/Bryantad/Sona/releases/tag/v0.14.0)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![Marketplace Installs](https://img.shields.io/visual-studio-marketplace/i/Waycoreinc.sona-ai-native-programming?label=VS%20Code%20Installs)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)

Visual Studio Code support for the Sona programming language.

## What's New in 0.14.0

Sona `0.14.0` focuses on developer usability: clearer CLI behavior,
validated examples, better onboarding docs, and package stability.

- Stable CLI flow: `sona --version`, `sona --help`, `sona run file.sona`, and `sona file.sona`.
- Updated quickstart path for installing and running Sona.
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
- Cognitive accessibility workflows including Focus Mode, Working Memory, and user profiles.

## Useful Commands

| Command | Description |
| --- | --- |
| **Sona: Welcome & Setup** | Opens extension onboarding. |
| **Sona: Run Sona File** | Runs the active Sona file. |
| **Sona: Check Syntax** | Checks syntax for the active Sona file. |
| **Sona: Format Code** | Formats Sona code. |
| **Sona: Start REPL** | Starts an interactive Sona shell. |
| **Sona: Show System Info** | Shows runtime and extension environment details. |

## Configuration

```json
{
  "sona.cli.pythonPath": "python",
  "sona.cli.timeout": 30000,
  "sona.userProfile": "neurotypical",
  "sona.ai.autoSetup": true,
  "sona.onboarding.showWelcome": true
}
```

## Release Notes

- [Release notes](https://github.com/Bryantad/Sona/blob/main/RELEASE_NOTES_v0.14.0.md)
- [GitHub release body](https://github.com/Bryantad/Sona/blob/main/docs/release-notes/v0.14.0_GITHUB_RELEASE_BODY.md)

## License

MIT License. See [LICENSE](https://github.com/Bryantad/Sona/blob/main/LICENSE).
