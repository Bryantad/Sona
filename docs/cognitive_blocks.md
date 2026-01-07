# Cognitive Blocks (Design)

Purpose
-------
Describe the `cognitive` feature for Sona: a language-level annotation that marks code regions which the transpiler or runtime may augment with higher-level "cognitive" helpers (hints, generated comments, or optional AI-assisted transformations). Cognitive blocks are opt-in and can be toggled by transpiler options.

High-level goals
-----------------
- Provide a small, safe syntax for authors to mark regions for optional enhancement.
- Ensure transpiler can include/exclude cognitive content via `TranspileOptions.include_cognitive_blocks`.
- Emit deterministic, testable output when cognitive features are disabled.
- Provide clear examples for users and docs.

Syntax
------
Two forms are supported:

1. Inline marker (single statement)

    cognitive: explain "What this line does"

2. Block form (multi-line)

    cognitive {
        prompt: "Explain step-by-step why we do X"
        hint: "Keep explanation beginner-friendly"
    }
    some_sona_code_here()
    another_statement()

Semantics
---------
- When `include_cognitive_blocks` is false (default for production), the transpiler ignores cognitive markers and produces normal code.
- When true, the transpiler may inject comments, helper functions, or generated code that aids readability or debugging.
- The transformation must be deterministic and subject to unit tests (no external network calls during transpile).

Transpiler integration
----------------------
API expectations (matches `TranspileOptions` and `TranspileResult`):

- `TranspileOptions.include_cognitive_blocks`: bool — include cognitive augmentations.
- `TranspileOptions.optimise_code`: bool — run normal optimisations after cognitive injection.

Implementation notes for `sona_transpiler.py`:

- Parser: parse `cognitive:` inline markers and `cognitive { ... }` blocks into an AST node `CognitiveBlock` with fields `prompt`, `hint`, `body`.
- `SonaTranspiler._enhance_with_cognitive_features(ast_node, options)`: given an AST region and options, produce augmented AST/comments.
- Augmentations should be limited to:
  - Inserting explanatory comments above the block.
  - Creating a small helper function named `_cognitive_note_<n>()` that returns a string explanation (for runtime inspection) — only if options request runtime helpers.
  - Adding `# SOURCE: cognitive` metadata to generated source maps.
- No network/AI calls during transpilation; any AI-assisted workflow must be explicit tooling outside the core transpile pipeline.

Examples
--------
Sona source:

```sona
cognitive: explain "This computes factorial for small n"
def fact(n):
    if n <= 1:
        return 1
    return n * fact(n - 1)
```

Transpiled Python (with `include_cognitive_blocks = true`):

```python
# Cognitive: This computes factorial for small n
def fact(n):
    if n <= 1:
        return 1
    return n * fact(n - 1)

def _cognitive_note_1():
    return "This function uses recursion; for large n consider iterative approach."
```

Transpiled Python (with `include_cognitive_blocks = false`):

```python
def fact(n):
    if n <= 1:
        return 1
    return n * fact(n - 1)
```

Testing guidance
----------------
- Unit tests should assert that when `include_cognitive_blocks` is false, output equals baseline expected output.
- When true, check that comments and helper functions are present and that semantics are unchanged (i.e., executing the code returns same results).

Docs and UX
-----------
- Provide `docs/cognitive_blocks.md` (this file) as the authoritative design doc.
- Add a `--include-cognitive` flag to `cli.py transpile` command (defaults to false).
- Document cognitive blocks in language reference with examples and recommended use-cases.

Next steps
----------
1. Search VCS for prior `sona_transpiler.py` implementation to reuse existing parsing logic.
2. Implement AST nodes and `_enhance_with_cognitive_features` helper in transpiler core.
3. Add unit tests and a CLI flag.
4. Update `RELEASE_NOTES_v0.9.10.md` and `pyproject.toml` when ready.
