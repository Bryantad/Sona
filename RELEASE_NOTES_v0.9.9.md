# Sona v0.9.9 — Release Notes

Sona 0.9.9 is about locking in a real, day-to-day developer experience. This release focuses on correctness, editor integration, and making sure the language, tooling, and documentation all move in sync. There are no intended breaking changes from v0.9.8—this is refinement, not reinvention.

I’m also walking through this release on YouTube with real examples, editor flows, and explanations of the fixes and design decisions behind them.

---

## Highlights

- Language polish: block statements no longer require trailing semicolons; `and` / `or` now work alongside `&&` / `||`.
- Correctness: fixed chained comparisons, boolean short-circuiting, and literal handling (`true`, `false`, `null`).
- VS Code experience: Run File (F5), snippets, Go to Definition, Find References, Document Symbols, and Formatting all working together.
- Packaging and version alignment: runtime, standard library, CLI, documentation, and VS Code extension are fully synced to v0.9.9 with a one-shot installer that just works.

---

## Language & Grammar

- Block statements (`if`, `while`, `for`, `func`, `class`, `try`, `match`, `when`) no longer require a semicolon after the closing brace. Semicolons are still accepted for simple statements.
- Boolean operators support both keyword (`and`, `or`) and symbolic (`&&`, `||`) forms.
- Class bodies accept both function members and variable declarations; trailing semicolons are optional.
- Try/Catch supports both explicit typing (`catch Exception as e { ... }`) and shorthand catch-all (`catch e { ... }`).
- When/Match keeps both expression and block forms, with cleaned-up terminal priorities and conflict resolution.

---

## Interpreter & Runtime

- Boolean and null literals are mapped consistently:
  - `true` → `True`
  - `false` → `False`
  - `null` → `None`
- Added proper `ast.BoolOp` evaluation with correct short-circuit behavior for `and` and `or`.
- Fixed chained comparison evaluation so expressions like `a < b < c` or `x % 2 != 0` no longer get clobbered mid-chain.
- Hardened the Python-compatibility fallback converter:
  - Recognizes `if/elif/else`, `while`, `for`, and `repeat N`
  - Converts braces to indentation
  - Handles optional semicolons
  - Normalizes literals correctly
- Try/Catch handling now correctly binds variables for both typed and catch-all cases and no longer swallows control-flow (`break`, `continue`, `return`).

---

## Tooling — VS Code Extension

**Waycoreinc.sona-ai-native-programming v0.9.9**

- Run Sona File:
  - F5 runs the current file
  - Ctrl+F5 runs without debug
  - Uses `run_sona.py` during development or `python -m sona.cli run` when installed
- Snippets:
  - 30+ snippets covering `fn`, conditionals, loops, `match`, `when`, `class`, `try/catch`, imports, and more
- Navigation:
  - Go to Definition
  - Find References
  - Document Symbols / Outline powered by the stdio LSP server
- Formatting:
  - Server-side formatting implemented
  - Fixed `FormattingOptions` handling to prevent runtime errors
- LSP server:
  - Updated to `get_text_document()` to resolve deprecations
  - Improved open/change logging for stability
- Packaging fixes:
  - Corrected language client import (`vscode-languageclient/node.js`)
  - Ensured transitive dependencies are bundled
  - Added `sona/__main__.py` so `python -m sona` works as expected

---

## CLI & Packaging

- Added `sona/__main__.py` to support `python -m sona`.
- `run_sona.py` is now the zero-friction runner used by both the VS Code extension and local scripts.
- Version constants are fully synchronized across:
  - `pyproject.toml`
  - `setup.py`
  - `sona/__init__.py`
  - Standard library manifest
  - CLI banners

---

## Standard Library & Tests

- Verified standard library imports and usage across 91 modules in legacy test suites.
- Refreshed test flows for:
  - basics
  - collections
  - data
  - filesystems
  - time and random
- Fixed legacy tests using spaced operators (`> =`, `! =`, `< =`) and normalized them to standard forms (`>=`, `!=`, `<=`).
- Confirmed `test_control_flow_096.sona` runs cleanly under the native parser with no fallback required.

---

## Documentation

- README updated with:
  - v0.9.9 “What’s New”
  - refreshed badges
  - current examples
  - links to these release notes
- Security and contributing docs now reference v0.9.9 as the active supported release.
- A full walkthrough of this release, including editor flows and runtime behavior, is available on the Sona YouTube channel.

---

## Known Limitations (Tracked for v0.9.10)

- `repeat while` and `repeat until` appear in some legacy tests but are not yet formally specified in the canonical grammar.
- Some advanced `match` patterns may require additional transformer rules for complex normalization cases.

---

## Upgrade Notes

- No breaking changes expected when upgrading from v0.9.8 to v0.9.9.
- Existing code should continue to run without modification; semicolons remain supported.

---

## Acknowledgements

Thanks to everyone testing Sona in real workflows and reporting issues—especially around IDE integration and control-flow correctness. This release is stronger because of that feedback.

Repository: https://github.com/Bryantad/Sona
Inquries: sona-dev@hotmail.com
issues/questions: sona-dev@hotmail.com
