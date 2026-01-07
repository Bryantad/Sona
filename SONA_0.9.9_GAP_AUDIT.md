# Sona v0.9.9 Gap Audit (Draft)

This document tracks language/runtime gaps that are "stage-appropriate" to close in v0.9.9, plus what has already been addressed on `release/v0.9.9`.

## Shipped (this branch)

- **Callable expressions**: allow calling any expression result (e.g., `f()(x)`, `arr[i](x)`, `f = add; f(1)`)
- **Default parameters**: `func f(a, b=10) { ... }` with missing args filled from defaults

## High priority gaps (next)

- **Diagnostics**: unify parse/runtime errors with filename/line/column where available; avoid generic `Interpretation error: ...` wrapping that hides the real exception type.
- **Match semantics**: confirm `match`/`when` pattern behavior is consistent and documented; add clear fallthrough/default behavior.
- **Exceptions**: make `catch` type matching consistent (string vs name); document supported forms.
- **Functions**: keyword arguments, varargs (`*args`/`...`), and arity errors as `TypeError` with good messages.

## Medium priority gaps

- **Classes/inheritance**: multiple inheritance MRO (C3) and a stable method/attribute lookup model.
- **Scoping/closures**: clarify lexical scoping rules; decide whether nested functions capture outer variables.
- **Module system**: consistent import paths, module caching, and cycle handling.

## Notes

- The default grammar used by `SonaParserv090` is `sona/grammar.lark`.
