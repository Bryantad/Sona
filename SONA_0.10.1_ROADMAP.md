# (PLANNING) Sona v0.10.1 — FINAL FEATURE SET

**Target Release:** Q1 2026  
**Previous Version:** v0.10.0 (Cognitive Preview)  
**Branch:** (planning only)  
**Status:** 🔒 LOCKED (planning) — Not implemented in this workspace

---

## 🎯 Release Philosophy

v0.10.1 is about **credibility, stability, and forward momentum** — not scope explosion.

- Ship what's listed below, **nothing more**
- Everything else moves to v0.10.2+
- No AI dependencies required — fully offline-safe

---

## 🧠 1. Cognitive Features (Production-Ready)

These are Sona's **identity** — they must ship solid.

### Custom Cognitive Profiles

```sona
// Load built-in or custom profile
cognitive.load_profile("adhd")
cognitive.load_profile("my_custom_profile")

// Save custom profile configuration
cognitive.save_profile("focus_heavy", {
  break_interval: 15,
  chunk_size: "small",
  verbosity: "high"
})
```

### Diff-Aware Tracing

- Trace logs only record **changes**, not full state dumps
- Dramatically reduces log noise
- Preserves full context when needed

### HTML Cognitive Report Export

```powershell
python run_sona.py report program.sona --format html --out report.html
```

- Single-page, static HTML (no server required)
- Timeline visualization
- Decision tree view
- Error summary with context

### Decision Provenance

```sona
// Returns structured decision tree
let tree = decision.trace()
// {decisions: [...], rationale: [...], timestamps: [...]}
```

### Explain-First Errors (Hardened)

- Human explanation appears **before** technical trace
- Deterministic output (no randomness)
- Works offline without AI

---

## 🔤 2. Language Features (Parser + Runtime)

Only features that **unlock real code ergonomics**.

### Imports (🔴 MUST SHIP)

```sona
// Alias imports
import json as j
import collection as c

// Selective imports
from math import sqrt, pow
from collection import list, dict

// Selective with alias
from json import parse as json_parse

// Error suggestions for typos
// "Module 'jon' not found. Did you mean 'json'?"
```

### Spread Operator (🔴 MUST SHIP)

```sona
// Lists
let a = [1, 2, 3]
let b = [4, 5, 6]
let merged = [...a, ...b]  // [1, 2, 3, 4, 5, 6]

// Dicts (last wins on conflicts)
let defaults = {theme: "dark", size: 12}
let overrides = {size: 14}
let config = {...defaults, ...overrides}  // {theme: "dark", size: 14}
```

> ❌ Spread in function calls (`func(...args)`) is **NOT** in v0.10.1

### Arrow Functions (🟡 LIMITED)

```sona
// Expression body ONLY
let add = (a, b) => a + b
let square = x => x * x
let greet = () => "hello"

// Use in callbacks
let doubled = list.map(items, x => x * 2)
```

> ❌ Block bodies (`(x) => { ... }`) are **NOT** in v0.10.1

### repeat-until Fix

```sona
// Must parse and execute correctly
let x = 0
repeat {
  x = x + 1
} until x >= 10
```

---

## 🧱 3. Runtime & Parser Stability (Release Blockers)

These are **non-negotiable** — release blocked if broken.

| Issue               | Status | Requirement                                    |
| ------------------- | ------ | ---------------------------------------------- |
| Nested control flow | 🔴 Fix | Complex if/for/while nesting must work         |
| Trailing commas     | 🔴 Fix | `[1, 2, 3,]` must parse                        |
| Multiline strings   | 🔴 Fix | Edge cases resolved                            |
| Path behavior       | 🔴 Fix | Windows/Linux aligned                          |
| None leaks          | 🔴 Fix | No stdlib function returns `None` unexpectedly |
| Import resolution   | 🔴 Fix | Deterministic, no race conditions              |

---

## 📚 4. Stdlib Upgrades (Minimal, High-Impact)

**No massive expansion** — only essentials with full test coverage.

### collection Module

```sona
import collection

// List operations
collection.list.flatten([1, [2, [3]]], 1)    // [1, 2, [3]]
collection.list.flatten([1, [2, [3]]], 2)    // [1, 2, 3]
collection.list.chunk([1,2,3,4,5], 2)        // [[1,2], [3,4], [5]]
collection.list.unique([1, 2, 2, 3, 1])      // [1, 2, 3]

// Dict operations
collection.dict.merge({a: 1}, {b: 2})        // {a: 1, b: 2}
collection.dict.deep_get({a: {b: 1}}, "a.b", 0)  // 1
```

### string Module

```sona
import string

string.template("Hello {name}!", {name: "World"})  // "Hello World!"
string.truncate("Long text here", 8, "...")        // "Long ..."
string.slugify("Hello World!")                     // "hello-world"
```

### math Module

```sona
import math

math.clamp(15, 0, 10)      // 10
math.lerp(0, 100, 0.5)     // 50
math.gcd(12, 8)            // 4
math.is_prime(17)          // true
```

### json Module

```sona
import json

json.stringify_pretty({a: 1}, 2)  // "{\n  \"a\": 1\n}"
json.diff({a: 1}, {a: 2})         // [{path: "a", old: 1, new: 2}]
```

### Requirements for ALL Stdlib Functions

- ✅ Deterministic output
- ✅ `.sona` test file
- ✅ Docstring with example

---

## 🧪 5. Testing & Assertions

Enough to feel **professional**, not overbuilt.

```sona
import test
import assert

test.describe("Math operations", func() {
  test.it("adds numbers correctly", func() {
    assert.equals(1 + 1, 2)
  })

  test.it("compares nested structures", func() {
    assert.deep_equals({a: [1, 2]}, {a: [1, 2]})
  })

  test.it("catches errors", func() {
    assert.throws(func() {
      throw "expected error"
    })
  })
})
```

### Test Module Functions

- `test.describe(name, fn)` — Group tests
- `test.it(name, fn)` — Individual test
- `test.skip(name, fn)` — Skip test (documented)
- `test.only(name, fn)` — Run only this test

### Assert Module Functions

- `assert.equals(a, b)` — Strict equality
- `assert.deep_equals(a, b)` — Deep comparison
- `assert.throws(fn)` — Exception expected
- `assert.truthy(val)` — Truthy check
- `assert.falsy(val)` — Falsy check

### Snapshot Testing (Minimal)

```sona
test.snapshot(result, "my_snapshot_name")
```

---

## 🧯 6. Diagnostics & Errors

This is where **trust is built**.

### Unified Error Format

```
program.sona:42:15: E001 Undefined variable 'foo'

   40 |   let bar = 10
   41 |   let baz = 20
>  42 |   print(foo + bar)
              ^^^
   43 | }

💡 Did you mean 'bar' or 'baz'?
```

### Error Features

| Feature      | Description                             |
| ------------ | --------------------------------------- |
| Location     | `filename:line:column` format           |
| Context      | Show surrounding source lines           |
| Error codes  | `E001`, `E002`, etc. (documentable)     |
| Suggestions  | "Did you mean 'json'?" for imports      |
| Warnings     | Non-fatal issues (don't halt execution) |
| Deprecations | Warn about features moving/changing     |

### Explain-First Format

```
❌ Cannot find module 'jon'

The module 'jon' doesn't exist in Sona's standard library.
This usually happens when there's a typo in the import name.

💡 Did you mean 'json'?

Technical: ImportError at program.sona:1:8
```

---

## 🛠 7. Tooling (Bare Minimum)

Do **not** overbuild yet.

### LSP v0 (`sona/lsp_server.py`)

| Feature          | Status                             |
| ---------------- | ---------------------------------- |
| Diagnostics      | ✅ Errors + warnings on save       |
| Hover docs       | ✅ Function/variable documentation |
| Go-to-definition | ✅ Functions only                  |
| Autocomplete     | ❌ Not in v0.10.1                  |
| Rename           | ❌ Not in v0.10.1                  |

### VS Code Extension Updates

- [ ] Updated syntax highlighting (spread, arrow functions)
- [ ] "Run Sona File" command
- [ ] "Export Cognitive Report" command (md/json/html)
- [ ] Error squiggles from LSP

---

## ❌ Explicitly NOT in v0.10.1

**Important for discipline** — these move to v0.10.2+:

| Feature                       | Reason     |
| ----------------------------- | ---------- |
| Multiple inheritance / C3 MRO | Complexity |
| Interfaces / abstract classes | Complexity |
| Generators (`yield`)          | Complexity |
| Full typing system            | Scope      |
| itertools/functools modules   | Scope      |
| Spread in function calls      | Complexity |
| Block-body arrow functions    | Complexity |
| Debug adapter protocol        | Scope      |
| AI-required features          | Dependency |
| Autocomplete in LSP           | Scope      |

---

## 🎯 Success Criteria

**v0.10.1 ships when:**

- [ ] All listed features pass `.sona` tests
- [ ] No regressions in v0.10.0 test suite
- [ ] Imports + spread work flawlessly
- [ ] Cognitive reports render correctly (md/json/html)
- [ ] Errors feel human, not cryptic
- [ ] Windows + Linux paths work identically

---

## 📅 Timeline

| Week | Focus                                                  |
| ---- | ------------------------------------------------------ |
| 1-2  | Parser: imports, spread, arrow functions, repeat-until |
| 3-4  | Runtime: stability fixes, error handling               |
| 5-6  | Stdlib: collection, string, math, json upgrades        |
| 7    | Cognitive: profiles, diff-trace, HTML export           |
| 8    | Testing: test/assert modules, full suite               |
| 9    | Tooling: LSP v0, VS Code updates                       |
| 10   | Polish: docs, final testing, release                   |

---

## 📁 Key Files

| File                          | Changes                                 |
| ----------------------------- | --------------------------------------- |
| `sona/grammar.lark`           | Import aliases, spread, arrow functions |
| `sona/interpreter.py`         | Runtime for new features                |
| `sona/parser_v090.py`         | AST construction                        |
| `sona/stdlib/collection/*.py` | flatten, chunk, unique, merge, deep_get |
| `sona/stdlib/string.py`       | template, truncate, slugify             |
| `sona/stdlib/math.py`         | clamp, lerp, gcd, is_prime              |
| `sona/stdlib/json.py`         | stringify_pretty, diff                  |
| `sona/stdlib/test.py`         | describe, it, skip, only                |
| `sona/stdlib/assert.py`       | deep_equals, throws                     |
| `sona/lsp_server.py`          | Diagnostics, hover, go-to-def           |
| `run_sona.py`                 | HTML report export                      |

---

_Document locked: January 3, 2026_  
_Sona Development Team_
