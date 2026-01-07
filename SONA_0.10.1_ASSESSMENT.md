# (DRAFT) Sona v0.10.0 → v0.10.1 Implementation Assessment

**Assessment Date:** January 3, 2026  
**Current Version:** v0.10.1 (in progress)  
**Reference:** [SONA_0.10.1_ROADMAP.md](SONA_0.10.1_ROADMAP.md)

---

## 📊 Executive Summary

| Category               | v0.10.0 Status                | v0.10.1 Required                   | Gap     |
| ---------------------- | ----------------------------- | ---------------------------------- | ------- |
| **Import aliases**     | ✅ Basic `import x as y`      | ✅ Done                            | None    |
| **Selective imports**  | ❌ Not in grammar             | `from x import a, b`               | **NEW** |
| **Spread operator**    | 🟡 In arguments only          | Lists/dicts: `[...a]`              | **NEW** |
| **Arrow functions**    | ❌ None                       | `(a) => a + 1`                     | **NEW** |
| **repeat-until**       | ❌ Only `repeat N {}`         | `repeat {} until expr`             | **NEW** |
| **Cognitive profiles** | 🟡 `set_profile()` only       | `load_profile()`, `save_profile()` | **NEW** |
| **HTML reports**       | ❌ md/json only               | HTML export                        | **NEW** |
| **Diff-aware trace**   | ❌ Full dumps                 | Change-only logging                | **NEW** |
| **Stdlib: collection** | ✅ chunk, flatten, unique     | merge, deep_get                    | Partial |
| **Stdlib: string**     | ✅ truncate, slugify          | template                           | **NEW** |
| **Stdlib: math**       | ✅ clamp, lerp, gcd, is_prime | ✅ Done                            | None    |
| **Stdlib: json**       | 🟡 diff exists                | stringify_pretty                   | Partial |
| **test module**        | ✅ describe, it, skip         | only, snapshot                     | Partial |
| **assert module**      | 🟡 equal, true, contains      | deep_equals, throws                | **NEW** |
| **LSP**                | 🟡 Diagnostics, hover         | go-to-def                          | Partial |
| **Error format**       | 🟡 Basic                      | file:line:col + codes              | **NEW** |

---

## 🟢 Already Implemented (No Work Needed)

### Grammar & Parser

- ✅ `import module as alias` — Grammar supports it
- ✅ Spread in function arguments: `func(...args)` — Grammar has `spread_arg`
- ✅ Keyword arguments: `func(a=1)` — Grammar has `kw_arg`
- ✅ Default parameters: `func(a, b=10)` — Working

### Stdlib: math Module

- ✅ `clamp(value, lower, upper)` — Line 147
- ✅ `lerp(start, end, t)` — Line 155
- ✅ `gcd(a, b)` — Line 319
- ✅ `is_prime(n)` — Line 404

### Stdlib: string Module

- ✅ `truncate(value, length, suffix)` — Line 317
- ✅ `slugify(value, separator)` — Line 345

### Stdlib: collection.list Module

- ✅ `chunk(seq, n)` — Working
- ✅ `flatten(nested)` — Working (1-level only)
- ✅ `unique(seq)` — Working
- ✅ `window(seq, k, step)` — Working

### Stdlib: collection.dict Module

- ✅ `safe_get(d, k, default)` — Working
- ✅ `merge(a, b, mode)` — Working

### Stdlib: test Module

- ✅ `describe(name)` — Line 177
- ✅ `it(description, func)` — Line 197
- ✅ `skip(reason)` — Line 227

### Stdlib: json Module

- ✅ `diff(obj1, obj2)` — Line 588

### Cognitive Features

- ✅ `set_profile(params)` — Working
- ✅ `record_intent(params)` — Working
- ✅ `record_decision(params)` — Working
- ✅ `toggle_trace(params)` — Working
- ✅ `explain_step(params)` — Working
- ✅ `export_trace(params)` — Working

### LSP Server

- ✅ Diagnostics on save — Working
- ✅ Hover documentation — Working
- ✅ Cognitive lint warnings — Working

---

## 🔴 Must Implement for v0.10.1

### 1. Grammar: Selective Imports (HIGH PRIORITY)

**File:** `sona/grammar.lark`

**Current:**

```lark
import_stmt: "import" import_path ["as" NAME] -> import_stmt
```

**Needed:**

```lark
import_stmt: "import" import_path ["as" NAME] -> import_stmt
           | "from" import_path "import" import_list -> from_import_stmt
import_list: import_item ("," import_item)*
import_item: NAME ["as" NAME] -> import_item
```

**Also update:** `sona/ast_nodes.py`, `sona/interpreter.py`

---

### 2. Grammar: Spread in Lists/Dicts (HIGH PRIORITY)

**File:** `sona/grammar.lark`

**Current:** Spread only works in function arguments

```lark
?argument: "..." expr -> spread_arg
```

**Needed:**

```lark
list_elements: list_element ("," list_element)*
?list_element: "..." expr -> spread_list
            | expr

dict_elements: dict_element ("," dict_element)*
?dict_element: "..." expr -> spread_dict
            | dict_pair
```

---

### 3. Grammar: Arrow Functions (MEDIUM PRIORITY)

**File:** `sona/grammar.lark`

**Add:**

```lark
// Arrow functions (expression body only)
arrow_func: "(" [func_params] ")" "=>" expr -> arrow_func
          | NAME "=>" expr -> arrow_func_single

// Add to atom:
?atom: ... | arrow_func
```

**Also update:** `sona/interpreter.py` — convert to `SonaFunction`

---

### 4. Grammar: repeat-until (MEDIUM PRIORITY)

**File:** `sona/grammar.lark`

**Current:**

```lark
repeat_stmt: REPEAT NUMBER "{" statement_list "}" -> repeat_stmt
```

**Needed:**

```lark
repeat_stmt: REPEAT NUMBER "{" statement_list "}" -> repeat_stmt
           | REPEAT "{" statement_list "}" "until" expr -> repeat_until_stmt
```

---

### 5. Cognitive: load_profile / save_profile (HIGH PRIORITY)

**File:** `sona/interpreter.py` — `CognitiveMonitor` class

**Add methods:**

```python
def load_profile(self, params: dict[str, Any]) -> dict[str, Any]:
    """Load a built-in or custom cognitive profile."""
    name = params.get("name") or params.get("arg0")
    # Load from file or built-in profiles
    ...

def save_profile(self, params: dict[str, Any]) -> dict[str, Any]:
    """Save current profile configuration."""
    name = params.get("name") or params.get("arg0")
    config = params.get("config") or params.get("arg1")
    # Save to .sona/profiles/
    ...
```

---

### 6. Cognitive: HTML Report Export (HIGH PRIORITY)

**File:** `run_sona.py`

**Add format option:**

```python
def _render_report_html(payload):
    """Render cognitive report as single-page HTML."""
    # Timeline visualization
    # Decision tree view
    # Error summary
    ...
```

---

### 7. Cognitive: Diff-Aware Tracing (MEDIUM PRIORITY)

**File:** `sona/interpreter.py` — `CognitiveMonitor._record_trace`

**Change from:**

```python
def _record_trace(self, event_type: str, payload: dict[str, Any]) -> None:
    if not self.trace_enabled:
        return
    self.trace_log.append({...})  # Full payload every time
```

**To:**

```python
def _record_trace(self, event_type: str, payload: dict[str, Any]) -> None:
    if not self.trace_enabled:
        return
    # Only log if different from last entry of same type
    diff = self._compute_diff(event_type, payload)
    if diff:
        self.trace_log.append({..., "diff": diff})
```

---

### 8. Stdlib: string.template (HIGH PRIORITY)

**File:** `sona/stdlib/string.py`

**Add:**

```python
def template(text: str, vars: dict) -> str:
    """
    Simple string template interpolation.

    Example:
        template("Hello {name}!", {"name": "World"})  # "Hello World!"
    """
    result = text
    for key, value in vars.items():
        result = result.replace(f"{{{key}}}", str(value))
    return result
```

---

### 9. Stdlib: collection.dict.deep_get (HIGH PRIORITY)

**File:** `sona/stdlib/collection/dict.py`

**Add:**

```python
def deep_get(d, path, default=None):
    """
    Get value from nested dict using dot notation path.

    Example:
        deep_get({"a": {"b": 1}}, "a.b", 0)  # 1
    """
    keys = path.split(".")
    current = d
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current
```

---

### 10. Stdlib: json.stringify_pretty (MEDIUM PRIORITY)

**File:** `sona/stdlib/json.py`

**Add:**

```python
def stringify_pretty(obj: Any, indent: int = 2) -> str:
    """
    Convert object to pretty-printed JSON string.

    Example:
        stringify_pretty({"a": 1}, 2)  # '{\n  "a": 1\n}'
    """
    import json as _json
    return _json.dumps(obj, indent=indent, ensure_ascii=False)
```

---

### 11. Stdlib: assert.deep_equals & throws (HIGH PRIORITY)

**File:** `sona/stdlib/assert.py`

**Add:**

```python
def deep_equals(actual, expected, message=None):
    """Assert deep equality for nested structures."""
    if not _deep_equal(actual, expected):
        msg = message or f"Expected {expected}, got {actual}"
        raise AssertionError(msg)

def _deep_equal(a, b):
    """Recursive deep equality check."""
    if type(a) != type(b):
        return False
    if isinstance(a, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_deep_equal(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return False
        return all(_deep_equal(x, y) for x, y in zip(a, b))
    return a == b

def throws(func, message=None):
    """Assert that function raises an exception."""
    try:
        func()
        msg = message or "Expected function to throw"
        raise AssertionError(msg)
    except AssertionError:
        raise
    except Exception:
        pass  # Expected
```

---

### 12. Stdlib: test.only & snapshot (MEDIUM PRIORITY)

**File:** `sona/stdlib/test.py`

**Add:**

```python
_only_tests = []

def only(description, func):
    """Run only this test (for debugging)."""
    _only_tests.append((description, func))
    return it(description, func)

def snapshot(value, name):
    """Compare value against stored snapshot."""
    # Store in .sona/snapshots/
    ...
```

---

### 13. LSP: Go-to-Definition (MEDIUM PRIORITY)

**File:** `sona/lsp_server.py`

**Enhance existing stub to actually find function definitions.**

---

### 14. Error Format: file:line:col + Codes (HIGH PRIORITY)

**File:** `sona/utils/error_explainer.py` (or create)

**Create unified error formatter:**

```python
def format_error(error, filename, source, line=None, col=None):
    """
    Format error with:
    - file:line:col location
    - Source context
    - Error code (E001, etc.)
    - Human explanation
    - Suggestions
    """
    ...
```

---

## 📋 Implementation Order (Recommended)

### Week 1-2: Parser (Foundation)

1. ✅ Selective imports (`from x import a, b`)
2. ✅ Spread in lists/dicts
3. ✅ Arrow functions
4. ✅ repeat-until

### Week 3-4: Stability & Errors

5. ✅ Error format unification
6. ✅ Trailing comma support (test existing)
7. ✅ Nested control flow fixes (test existing)

### Week 5-6: Stdlib

8. ✅ string.template
9. ✅ dict.deep_get
10. ✅ json.stringify_pretty
11. ✅ assert.deep_equals, throws
12. ✅ test.only, snapshot

### Week 7-8: Cognitive

13. ✅ load_profile / save_profile
14. ✅ HTML report export
15. ✅ Diff-aware tracing
16. ✅ decision.trace()

### Week 9-10: Tooling & Polish

17. ✅ LSP go-to-definition
18. ✅ VS Code syntax updates
19. ✅ Final testing
20. ✅ Release notes

---

## 🚦 Start Here

**Recommended first tasks (in order):**

1. **Grammar: `from x import`** — Unlocks selective imports
2. **Grammar: Spread in lists** — Unlocks `[...a, ...b]`
3. **stdlib: string.template** — Quick win, high value
4. **stdlib: assert.deep_equals** — Enables better testing
5. **Cognitive: load_profile** — Core identity feature

These 5 items provide maximum value with clear implementation paths.

---

_Assessment completed: January 3, 2026_
