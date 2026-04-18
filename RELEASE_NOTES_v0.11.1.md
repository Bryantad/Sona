# Sona v0.11.1 Release Notes

**Release Date:** 2025-07-12
**Type:** Minor stabilization release

---

## Summary

v0.11.1 fixes a small set of validated control-flow/runtime issues, adds
for-loop destructuring, and improves parser startup behavior without trying to
land larger architectural changes too early.

This release is intentionally conservative. It is meant to show steady forward
progress while keeping Sona stable.

---

## Bug Fixes

### P0 — `when` statement ignored subject expression

The `when` block evaluated each case condition as a standalone boolean instead
of comparing it against the subject. A `when x { 5 => ... }` would execute the
first _truthy_ case rather than the case whose value equals `x`.

**Fixed:** `WhenStatement.execute()` now evaluates the subject once and
compares each case value against it. The `_` wildcard is recognised as the
default/fallback case.

### P1 — Dead code in `ContinueStatement`

Three lines after `raise ContinueException()` could never execute. Removed.

### P2 — Ghost `control_flow_integration` checks

`EnhancedIfStatement` and `EnhancedWhileLoop` both checked for a
`control_flow_integration` attribute that was never set, adding unnecessary
indirection. Both classes now execute their logic directly.

---

## New Features

### For-loop destructuring

```sona
let items = ["a", "b", "c"];
for i, item in items {
    print(str(i) + ": " + item);    // 0: a, 1: b, 2: c
}

let ages = {"Alice": 30, "Bob": 25};
for name, age in ages {
    print(name + " is " + str(age)); // Alice is 30, Bob is 25
}
```

Lists are destructured as `(index, value)` via `enumerate()`.
Dicts are destructured as `(key, value)` via `.items()`.

---

## Performance

### Parser caching

The interpreter previously created a brand-new `SonaParserv090` (and rebuilt
the Earley grammar tables) on every `_execute_sona_code()` call — including
once per stdlib module loaded at startup. This caused noticeable startup lag
and could hang on resource-constrained machines.

**Fixed:** A single parser instance is now created once during
`SonaUnifiedInterpreter.__init__()` and reused for all subsequent parse calls.

---

## Cleanup

- Removed orphaned `TernaryExpression` AST node and parser transformer
  (grammar rule was reverted in v0.11.0 due to ambiguity with statement-level
  `if`). Conditional expressions remain available via `when {}` expressions.
- Fixed outdated REPL version string (`v0.10.2` → `v0.11.1`).

---

## Out Of Scope

- No first-class cognitive runtime or belief-graph system ships in `0.11.1`.
- No persistent replay/trace platform lands in this release.
- No large syntax or runtime rewrite is included just to represent roadmap work.

The receipts/traces/cognition roadmap remains active, but it belongs in a later
release after design and implementation are better isolated.

---

## Files Changed

| File                              | Change                                                                                                                                                           |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sona/ast_nodes.py`               | WhenStatement fix, ContinueStatement cleanup, EnhancedIfStatement/EnhancedWhileLoop ghost removal, new `EnhancedForDestructureLoop`, removed `TernaryExpression` |
| `sona/grammar.lark`               | `enhanced_for_stmt` split into destructure + basic forms                                                                                                         |
| `sona/parser_v090.py`             | New `enhanced_for_destructure_stmt` transformer, removed `ternary_expr` transformer                                                                              |
| `sona/interpreter.py`             | Parser caching, version bump                                                                                                                                     |
| `sona/__init__.py`                | Version → 0.11.1                                                                                                                                                 |
| `sona/cli.py`                     | Version → 0.11.1, fixed REPL banner                                                                                                                              |
| `pyproject.toml`                  | Version → 0.11.1                                                                                                                                                 |
| `setup.py`                        | Version → 0.11.1                                                                                                                                                 |
| `vscode-extension/*/package.json` | Version → 0.11.1                                                                                                                                                 |
| `run_sona.py`                     | Accept 0.11.x version strings                                                                                                                                    |

---

## Test Results

All 24 control-flow tests pass:

```
PASS: when x matched 10
PASS: when color matched blue
PASS: when y fell through to default
PASS: when expr category = Adult
PASS: conditional = big
PASS: conditional = small
PASS: index = 0 item = apple  (for destructuring)
PASS: index = 1 item = banana
PASS: index = 2 item = cherry
PASS: name = Alice age = 30   (dict destructuring)
PASS: name = Bob age = 25
PASS: else if val < 20
PASS: counter = 1  (while + continue)
PASS: counter = 2
PASS: counter = 4
PASS: counter = 5
PASS: match grade = B
PASS: repeat iteration 1
PASS: repeat iteration 2
PASS: repeat iteration 3
PASS: caught error
```
