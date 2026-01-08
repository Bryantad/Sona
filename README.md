# 🚀 Sona — **AI-Native** Programming Language

**Human × AI collaboration with cognitive accessibility at the core.**

[![Version](https://img.shields.io/badge/version-0.10-blue.svg)](https://github.com/Bryantad/Sona/releases/tag/v0.10)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://python.org)
[![Marketplace Installs](https://img.shields.io/visual-studio-marketplace/i/Waycoreinc.sona-ai-native-programming?label=VS%20Code%20Installs)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)
[![Marketplace Rating](https://img.shields.io/visual-studio-marketplace/r/Waycoreinc.sona-ai-native-programming?label=VS%20Code%20Rating)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)
[![GitHub Stars](https://img.shields.io/github/stars/Bryantad/Sona?style=social)](https://github.com/Bryantad/Sona/stargazers)
[![YouTube](https://img.shields.io/youtube/channel/subscribers/UCFWuiQHiQPrJSAeAVi5raZA?style=social)](https://www.youtube.com/channel/UCFWuiQHiQPrJSAeAVi5raZA)
[![X (Twitter) Follow](https://img.shields.io/twitter/follow/sona_org?style=social)](https://x.com/sona_org)

---

Overview
The Sona extension provides full editing, debugging, and AI-assisted capabilities for .sona and .smod files. It includes integrated Focus Mode, Working Memory, and AI Explain / Optimize / Review commands that work seamlessly inside VS Code.

Sona is built for:

Developers who want clarity and focus.
Educators who need explainable code for students.
Neurodivergent minds (ADHD, dyslexia, autism) who deserve tools that reduce cognitive overload.
Teams seeking explainable AI collaboration directly in their IDE.
Key Features
Cognitive Programming
Focus Mode — reduce distraction and visual noise for deep work.
Working Memory — record short-term notes, goals, or decisions directly in your code context.
Cognitive Check — evaluate code complexity or task load inline.
Intent — declare goals and constraints that the runtime can track and explain.
Decision Records — capture rationale and options alongside code.
Cognitive Trace / Explain Step — produce deterministic explainability snapshots.
Cognitive Scope — create boundaries for intent, decisions, and working memory.
Cognitive Scope Budgets — warn when scope complexity exceeds a budget.
Profile Annotations — set ADHD/dyslexia profiles at the language level.
Cognitive Lint / Report — deterministic lint checks and exportable reports.
AI-Native Commands
Sona: Explain Code — receive plain-language explanations for selected code.
Sona: Optimize Code — automatically propose cleaner, faster, or safer code variants.
Sona: Review Code — context-aware AI review with actionable recommendations.
Sona: Verify Runtime — ensure your local interpreter matches the expected version.
All AI features are optional and can be powered by your own OpenAI or Azure OpenAI credentials via the companion sona-ai Python package.

Language Support
Syntax highlighting for .sona and .smod.
Code snippets and autocomplete.
Error diagnostics integrated with Sona’s interpreter.
Multi-language transpilation (Python, JS, TS, C#, Go, Rust).
REPL integration for interactive exploration.
Built-In Stability
Deterministic standard library (30+ modules, 280 passing tests).
Verified on Windows 10/11, macOS, and Linux.
Zero network dependencies required for core functionality.
Coverage ≥ 40 percent and growing.
Support for vscode.dev
The Sona extension includes partial support for the vscode.dev and github.dev environments, enabling syntax highlighting, Focus Mode toggling, and lightweight AI Explain capabilities on open files.

Installed Extensions
For best results, Sona integrates optionally with:

Sona AI Provider (sona-ai Python package) — enables ai_explain, ai_optimize, ai_review.
Python Environments Extension — used for interpreter detection and environment setup.
Pylance — enhances completion, IntelliSense, and hover insights for embedded Python targets.
All dependencies are optional; Sona remains fully functional offline and without any AI provider configured.

Extensibility
Sona is designed as an open cognitive platform. Developers can extend its behavior by publishing custom .smod modules or IDE plugins using the provided extension APIs.

Available extension points:

Cognitive Plugins — add new working-memory or focus patterns.
AI Provider Plugins — connect external LLMs or custom inference endpoints.
Transpiler Targets — define new output languages via the sona_transpiler interface.
Documentation: Sona Extension API Guide

Quick Start
Install a supported version of Python (3.12+) on your system.

Install the Sona extension from the VS Code Marketplace.

Open or create a .sona file.

Run Sona: Welcome & Setup from the Command Palette.

Try Sona: Explain Code or Sona: Toggle Focus Mode.

(Optional) Install the AI Provider:

pip install "sona[ai]"
Environment Configuration
Select interpreter via Sona: Verify Runtime or set sona.pythonPath in settings.
Manage virtual environments with the Python Environments Extension.
Run the integrated REPL with Sona: Open REPL.
Jupyter Notebooks
Sona interoperates with the Jupyter Extension for educational workflows. Developers can embed .sona snippets or AI Explain comments directly in notebook cells for hybrid teaching or analysis.

Useful Commands
Command	Description
Sona: Welcome & Setup	Initializes extension and configuration wizard.
Sona: Explain Code	AI-powered code explanation for selected code.
Sona: Optimize Code	Suggests performance or readability improvements.
Sona: Toggle Focus Mode	Enables or disables distraction-free Focus Mode.
Sona: Clear Cognitive Memory	Clears stored working-memory context.
Sona: Export Cognitive Report	Exports a cognitive report for the active file.
Sona: Verify Runtime	Checks local environment and interpreter path.
Sona: Open REPL	Launches interactive Sona shell.
To view all Sona commands, open the Command Palette (Ctrl + Shift + P / Cmd + Shift + P) and type Sona.

Feature Details
Feature Area	Description
IntelliSense	AI-aware completions for .sona and .smod.
Cognitive Accessibility	Focus Mode, Working Memory, Intent, Decision Records, Trace/Explain, Profile, Lint/Report.
Debugging	Debug .sona scripts using the integrated Sona Runtime.
Transpilation	Generate equivalent code in Python, JS, TS, C#, Go, Rust.
Testing	Built-in sona test command for behavioral validation.
Docs Integration	Inline links to Sona documentation and wiki.
Supported Locales
The Sona extension is available in: en, fr, es, de, pt-br, ja, ko-kr, zh-cn, zh-tw.

Questions, Issues, and Contributions
Ask questions: GitHub Discussions
Report issues: GitHub Issues
Contribute: See CONTRIBUTING.md
Docs: https://github.com/Bryantad/Sona/wiki
Data and Telemetry
The Sona Extension collects anonymous usage data to improve performance, feature adoption, and accessibility design. This data is never sold or shared and respects VS Code’s telemetry.enableTelemetry setting. You can disable telemetry in Settings → Telemetry at any time.

License
MIT License — © 2025 Waycore Inc. See LICENSE.

About Waycore Inc.
Waycore Inc. is an AI R&D company focused on building human-centered developer tools and cognitive software systems. Sona is our flagship project — a language that brings accessibility, clarity, and AI into harmony with how the brain codes.

“Sona isn’t here to replace developers. It’s here to help them think more clearly.” — Andre D. Bryant, Founder & CEO of Waycore Inc.
