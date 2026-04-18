# Sona: AI-Native Programming with Cognitive Accessibility

[![Version](https://img.shields.io/badge/version-0.10-blue.svg)](https://github.com/Bryantad/Sona/releases/tag/v0.9.9)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://python.org)
[![Marketplace Installs](https://img.shields.io/visual-studio-marketplace/i/Waycoreinc.sona-ai-native-programming?label=VS%20Code%20Installs)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)
[![Marketplace Rating](https://img.shields.io/visual-studio-marketplace/r/Waycoreinc.sona-ai-native-programming?label=VS%20Code%20Rating)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)
[![GitHub Stars](https://img.shields.io/github/stars/Bryantad/Sona?style=social)](https://github.com/Bryantad/Sona/stargazers)
[![YouTube](https://img.shields.io/youtube/channel/subscribers/UCFWuiQHiQPrJSAeAVi5raZA?style=social)](https://www.youtube.com/channel/UCFWuiQHiQPrJSAeAVi5raZA)
[![X (Twitter) Follow](https://img.shields.io/twitter/follow/sona_org?style=social)](https://x.com/sona_org)

---

A Visual Studio Code extension with native support for the Sona programming language.
It focuses on practical language tooling, cognitive accessibility features, and optional AI-assisted commands inside VS Code.

---

## Overview

The Sona extension provides editing, runtime integration, and optional AI-assisted workflows for `.sona` and `.smod` files.
It includes Focus Mode, Working Memory, explainability-oriented commands, snippets, syntax highlighting, and REPL/runtime commands.

---

## Key Features

### Cognitive Programming

- **Focus Mode** — reduce distraction and visual noise for deep work.
- **Working Memory** — record short-term notes, goals, or decisions directly in your code context.
- **Cognitive Check** — evaluate code complexity or task load inline.
- **Intent / Decision / Explain Step** — support explainable programming workflows.
- **Profile Annotations** — set ADHD/dyslexia profiles at the language level.
- **Cognitive Report Export** — generate a report for the active file.

### AI Commands

- **Sona: Explain Code** — receive plain-language explanations for selected code.
- **Sona: Optimize Code** — automatically propose cleaner, faster, or safer code variants.
- **Sona: Verify Runtime** — ensure your local interpreter matches the expected version.

All AI features are optional and can be powered by your own OpenAI or Azure OpenAI credentials via the companion `sona-ai` Python package.

### Language Support

- **Syntax highlighting** for `.sona` and `.smod`.
- **Code snippets** and autocomplete.
- **Error diagnostics** integrated with Sona’s interpreter.
- **Multi-language transpilation** (Python, JS, TS, C#, Go, Rust).
- **REPL integration** for interactive exploration.

### Built-In Stability

- Deterministic standard library (30+ modules, 280 passing tests).
- Verified on Windows 10/11, macOS, and Linux.
- Zero network dependencies required for core functionality.
- Coverage ≥ 40 percent and growing.

---

## Quick Start

1. **Install a supported version of Python (3.12+)** on your system.
2. **Install the Sona extension** from the [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming).
3. **Open or create** a `.sona` file.
4. Run **Sona: Welcome & Setup** from the Command Palette.
5. Try **Sona: Explain Code** or **Sona: Toggle Focus Mode**.
6. _(Optional)_ Install the AI Provider:

   ```bash
   pip install "sona[ai]"
   ```

---

## Environment Configuration

- Select interpreter via `Sona: Verify Runtime` or set `sona.pythonPath` in settings.
- Run the integrated REPL with `Sona: Open REPL`.

---

## Useful Commands

| Command                           | Description                                       |
| --------------------------------- | ------------------------------------------------- |
| **Sona: Welcome & Setup**         | Initializes extension and configuration wizard.   |
| **Sona: Explain Code**            | AI-powered code explanation for selected code.    |
| **Sona: Optimize Code**           | Suggests performance or readability improvements. |
| **Sona: Toggle Focus Mode**       | Enables or disables distraction-free Focus Mode.  |
| **Sona: Clear Cognitive Memory**  | Clears stored working-memory context.             |
| **Sona: Export Cognitive Report** | Exports a cognitive report for the active file.   |
| **Sona: Verify Runtime**          | Checks local environment and interpreter path.    |
| **Sona: Open REPL**               | Launches interactive Sona shell.                  |

To view all Sona commands, open the Command Palette (`Ctrl + Shift + P` / `Cmd + Shift + P`) and type **Sona**.

---

## Questions, Issues, and Contributions

- **Ask questions:** [GitHub Discussions](https://github.com/Bryantad/Sona/discussions)
- **Report issues:** [GitHub Issues](https://github.com/Bryantad/Sona/issues)
- **Contribute:** See [CONTRIBUTING.md](https://github.com/Bryantad/Sona/blob/main/CONTRIBUTING.md)
- **Docs:** [https://github.com/Bryantad/Sona/wiki](https://github.com/Bryantad/Sona/wiki)

---

## License

MIT License — © 2025 Waycore Inc.
See [LICENSE](https://github.com/Bryantad/Sona/blob/main/LICENSE).
