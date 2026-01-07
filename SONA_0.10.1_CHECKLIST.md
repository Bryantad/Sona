# (DRAFT) Sona v0.10.1 — Implementation Checklist

**Status:** 🔒 LOCKED SCOPE  
**Reference:** [SONA_0.10.1_ROADMAP.md](SONA_0.10.1_ROADMAP.md)

---

## 🚀 Quick Start

```powershell
.\.venv\Scripts\Activate.ps1
python -c "from sona import __version__; print(f'Sona version: {__version__}')"
# NOTE: v0.10.1 is now active; checklist items may still be incomplete.
.\run_all_tests.ps1
```

---

## ✅ Master Checklist

### 🧠 1. Cognitive Features

- [ ] **Custom profiles**

  - [ ] `cognitive.load_profile(name)` — Load built-in or custom profile
  - [ ] `cognitive.save_profile(name, config)` — Save custom profile
  - [ ] Default profiles work: adhd, dyslexia, neurotypical
  - [ ] Test: `test_cognitive_profiles.sona`

- [ ] **Diff-aware tracing**

  - [ ] Trace logs only record changes
  - [ ] Full context available on demand
  - [ ] Test: `test_diff_trace.sona`

- [ ] **HTML report export**

  - [ ] `python run_sona.py report file.sona --format html`
  - [ ] Timeline visualization
  - [ ] Decision tree view
  - [ ] Test: manual verification

- [ ] **Decision provenance**

  - [ ] `decision.trace()` returns structured tree
  - [ ] Test: `test_decision_trace.sona`

- [ ] **Explain-first errors**
  - [ ] Human explanation before technical trace
  - [ ] Deterministic output
  - [ ] No AI required

---

### 🔤 2. Language Features

- [ ] **Import aliases** (🔴 MUST)

  - [ ] Grammar: `import NAME as NAME`
  - [ ] Grammar: `from NAME import NAME, NAME`
  - [ ] Grammar: `from NAME import NAME as NAME`
  - [ ] Interpreter: alias mapping
  - [ ] Error: "Did you mean?" suggestions
  - [ ] Test: `test_import_aliases.sona`

- [ ] **Spread operator** (🔴 MUST)

  - [ ] Grammar: `spread_expr: "..." expr`
  - [ ] Lists: `[...a, ...b]`
  - [ ] Dicts: `{...a, ...b}` (last wins)
  - [ ] Test: `test_spread.sona`

- [ ] **Arrow functions** (🟡 LIMITED)

  - [ ] Grammar: `(params) => expr`
  - [ ] Single param: `x => expr`
  - [ ] No params: `() => expr`
  - [ ] Expression body ONLY (no blocks)
  - [ ] Test: `test_arrow_functions.sona`

- [ ] **repeat-until fix**
  - [ ] Parser handles `repeat { } until expr`
  - [ ] Runtime executes correctly
  - [ ] Test: `test_repeat_until.sona`

---

### 🧱 3. Stability Fixes (Release Blockers)

- [ ] **Nested control flow**

  - [ ] Complex if/for/while nesting works
  - [ ] Test: `test_nested_control.sona`

- [ ] **Trailing commas**

  - [ ] `[1, 2, 3,]` parses
  - [ ] `{a: 1, b: 2,}` parses
  - [ ] Test: `test_trailing_commas.sona`

- [ ] **Multiline strings**

  - [ ] Edge cases resolved
  - [ ] Test: `test_multiline_strings.sona`

- [ ] **Path behavior**

  - [ ] Windows/Linux paths aligned
  - [ ] Test: `test_paths.sona`

- [ ] **None leaks**

  - [ ] No stdlib function returns None unexpectedly
  - [ ] Audit all stdlib modules

- [ ] **Import resolution**
  - [ ] Deterministic behavior
  - [ ] No race conditions

---

### 📚 4. Stdlib Upgrades

- [ ] **collection.list**

  - [ ] `flatten(list, depth=1)` — Flatten nested lists
  - [ ] `chunk(list, size)` — Split into chunks
  - [ ] `unique(list)` — Remove duplicates (preserve order)
  - [ ] Test: `test_collection_list.sona`

- [ ] **collection.dict**

  - [ ] `merge(*dicts)` — Merge dictionaries
  - [ ] `deep_get(dict, path, default)` — Nested key access
  - [ ] Test: `test_collection_dict.sona`

- [ ] **string**

  - [ ] `template(str, vars)` — String interpolation
  - [ ] `truncate(str, len, suffix)` — Smart truncate
  - [ ] `slugify(str)` — URL-safe slug
  - [ ] Test: `test_string_upgrades.sona`

- [ ] **math**

  - [ ] `clamp(val, min, max)` — Constrain to range
  - [ ] `lerp(a, b, t)` — Linear interpolation
  - [ ] `gcd(a, b)` — Greatest common divisor
  - [ ] `is_prime(n)` — Primality test
  - [ ] Test: `test_math_upgrades.sona`

- [ ] **json**
  - [ ] `stringify_pretty(obj, indent)` — Pretty print
  - [ ] `diff(a, b)` — JSON diff
  - [ ] Test: `test_json_upgrades.sona`

---

### 🧪 5. Testing Module

- [ ] **test module**

  - [ ] `describe(name, fn)` — Group tests
  - [ ] `it(name, fn)` — Individual test
  - [ ] `skip(name, fn)` — Skip test
  - [ ] `only(name, fn)` — Run only this
  - [ ] `snapshot(val, name)` — Snapshot testing
  - [ ] Test: `test_test_module.sona`

- [ ] **assert module**
  - [ ] `equals(a, b)` — Strict equality
  - [ ] `deep_equals(a, b)` — Deep comparison
  - [ ] `throws(fn)` — Exception expected
  - [ ] `truthy(val)` / `falsy(val)`
  - [ ] Test: `test_assert_module.sona`

---

### 🧯 6. Diagnostics

- [ ] **Error format**

  - [ ] `filename:line:column` format
  - [ ] Source context (surrounding lines)
  - [ ] Error codes (E001, E002, etc.)
  - [ ] Test: manual verification

- [ ] **Suggestions**

  - [ ] "Did you mean?" for imports
  - [ ] "Did you mean?" for variables
  - [ ] Test: `test_error_suggestions.sona`

- [ ] **Warnings**
  - [ ] Non-fatal warnings work
  - [ ] Deprecation warnings work
  - [ ] Test: `test_warnings.sona`

---

### 🛠 7. Tooling

- [ ] **LSP v0**

  - [ ] Diagnostics on save
  - [ ] Hover documentation
  - [ ] Go-to-definition (functions)
  - [ ] Test: manual VS Code verification

- [ ] **VS Code extension**
  - [ ] Syntax highlighting updated
  - [ ] Run file command works
  - [ ] Export cognitive report (md/json/html)
  - [ ] Test: manual verification

---

## 📁 Files to Modify

| File                             | Changes                       |
| -------------------------------- | ----------------------------- |
| `sona/grammar.lark`              | imports, spread, arrows       |
| `sona/interpreter.py`            | runtime features              |
| `sona/parser_v090.py`            | AST updates                   |
| `sona/stdlib/collection/list.py` | flatten, chunk, unique        |
| `sona/stdlib/collection/dict.py` | merge, deep_get               |
| `sona/stdlib/string.py`          | template, truncate, slugify   |
| `sona/stdlib/math.py`            | clamp, lerp, gcd, is_prime    |
| `sona/stdlib/json.py`            | stringify_pretty, diff        |
| `sona/stdlib/test.py`            | describe, it, skip, only      |
| `sona/stdlib/assert.py`          | deep_equals, throws           |
| `sona/lsp_server.py`             | diagnostics, hover, go-to-def |
| `run_sona.py`                    | HTML export                   |

---

## 🎯 Release Criteria

All must be ✅ before release:

- [ ] All checklist items above complete
- [ ] No regressions in v0.10.0 tests
- [ ] `.\run_all_tests.ps1` passes
- [ ] Windows + Linux tested
- [ ] Release notes written

---

## ❌ NOT IN SCOPE

Do not implement (v0.10.2+):

- Multiple inheritance
- Generators/yield
- Full typing system
- Spread in function calls
- Block-body arrow functions
- LSP autocomplete
- AI features

---

_Checklist created: January 3, 2026_
