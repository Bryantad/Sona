# Sona v0.10.0 Pre-Release Summary

Date: 2025-12-30
Status: Pre-release candidate
Theme: Cognitive + AI wiring, core syntax stability

Executive Summary
Sona 0.10.0 is the strongest release of the year for this codebase. This pre-release hardens
core syntax, fixes parser edge cases, wires AI and cognitive tooling across the CLI and runtime,
and adds local Ollama support so advanced features can run offline. The result is a stable core
with opt-in cognitive and AI layers that are now consistently routed end to end.

Highlights
- Cognitive programming substrate stays front and center (intent, decision, trace, scope, profile).
- New cognitive-first primitives: focus blocks, intent annotations, and explain-first errors.
- CLI is fully wired for AI workflows and diagnostics (run, demo, profile, benchmark, suggest,
  explain, doctor, build-info, ai-model, ai-mode).
- Core syntax stability improvements remove previously brittle parse paths in common expressions.
- Offline AI support via Ollama replaces the GPT-2-only dependency path when configured.
- Stdlib .smod wrappers are now first-class and preferred in imports, with native bridge wiring.

Added
- Local Ollama model management and health checks via `sona ai-model` and `sona ai-mode`.
- Ollama-backed AI integration with a GPT-2 compatible interface for completions and explanations.
- Backend selector that prefers Ollama when installed and running (configurable via env vars).
- `focus { ... }` blocks to reduce runtime noise and increase trace detail inside the block.
- `@intent "..."` annotations to preserve intent and improve cognitive explain output.
- Explain-first runtime errors with deterministic suggestions and location hints.
- CLI error output mode `--errors=explain|trace|both` (default explain-first).
- Direct CLI invocation for Python helpers via `sona <file.py>`.
- Stdlib CLI probes and doctor helpers for quick module and environment status checks.
- Built-in `set` constructor in the runtime for basic set usage.
- Transpiler `--core-only` flag to emit pure core syntax (no cognitive helpers).
- Stdlib .smod wrapper layer for core modules (math, string, json, path, regex, time, date, fs, env, csv).

Fixed
- Parser normalization to prevent assignment sequences from splitting in `x = x + y` patterns.
- Argument mapping normalization to handle nested positional arguments.
- `set([...])` call parsing that previously split into separate statements.
- Postfix call normalization so `module.method(arg)` and `obj.method(arg)` no longer split into separate statements.
- `not` unary parsing clarified so it does not interfere with `!=`.
- Data-structures tests no longer crash on scoring reductions (int + list type mismatch).
- Nested stdlib module wiring no longer overrides module globals (ex: `collection.list` no longer shadows list helpers).
- Regex patterns now normalize escape sequences (ex: `\\w`, `\\d`) and `match` uses start-of-string semantics.
- Base64 and hex decode helpers now return text by default (bytes available via `return_bytes=true`).
- Archived experimental modules under `sona/_attic` to keep core coverage and tooling clean.
- Pytest now filters upstream Lark deprecation warnings (`sre_parse`, `sre_constants`) on Python 3.13.
- Smod wrapper options no longer throw null indexing errors; regex replace/split use native options mapping.
- Path join now accepts multi-part segments (matches stdlib path behavior).

Updated and Wired
- AI entry points in cognitive assistant, code completion, and natural language now route through
  the backend selector instead of hard-wiring GPT-2.
- CLI AI status now reports the active backend (Ollama or GPT-2) instead of assuming GPT-2.
- Transpiler defaults now include cognitive/AI helpers unless `--core-only` is used.
- Local AI diagnostics integrated into `sona doctor` output for faster readiness checks.
- Stdlib modules are preloaded into the core runtime (global modules + `stdlib` namespace).
- Nested stdlib modules resolve through a submodule registry to preserve top-level module globals.
- Complete stdlib sweep now includes sanity assertions beyond import checks.
- Smod import verification added to the standard pre-release test suite.

Compatibility and Defaults
- Core syntax remains stable and is the default focus for 0.10.0.
- Cognitive and AI layers are opt-in at runtime; if Ollama is not running, the system degrades
  gracefully and surfaces readiness hints.
- Offline AI defaults to `qwen2.5-coder:7b` and can be overridden via env vars.

Configuration Notes
- Preferred backend: `SONA_AI_BACKEND=ollama` or `SONA_AI_BACKEND=gpt2`
- Ollama model override: `SONA_OLLAMA_MODEL=<model>`
- Ollama host override: `OLLAMA_HOST=http://localhost:11434`

Known Caveats
- AI features require Ollama running with a model installed, or GPT-2 model files present.
- Some stdlib modules require optional Python dependencies for full functionality.
- Cognitive features are stable but may evolve during 0.10.x.

Release Readiness
- Core runtime: stable for 0.10.0 pre-release.
- Cognitive features: wired and functional with deterministic fallbacks.
- AI features: functional with Ollama or GPT-2 configured.

Suggested Validation (Pre-Release)
- `python -m sona.cli info --ai-status`
- `python -m sona.cli doctor`
- `.\run_all_tests.ps1`
- `python -m sona.cli run test_data_structures_096.sona`
- `python -m sona.cli run test_core_features_096.sona`

Positioning
Sona 0.10.0 combines stable core syntax with a fully wired cognitive and AI toolchain, making it
the most powerful and complete Sona release in this codebase this year.
