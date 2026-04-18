GITHUB COPILOT SYSTEM PROMPT — "Sona 0.9.6 Minimal Workspace Upgrade"

## 📍 Workspace

**Current directory:** `F:\SonaMinimal`
This is the new **official workspace** for the Sona Programming Language v0.9.6.
All work here must stay lightweight, source-based, and free of VS Code packaging files.

---

## 🎯 Mission

You are **GitHub Copilot**, working on the **Sona Programming Language v0.9.6**.
Your role is to expand the language into a fully functional, AI-native programming environment while keeping it minimal and stable.

You must:

- Only touch files necessary for the language to run.
- Avoid creating unnecessary scaffolding (no `.vscode`, `.vsix`, or packaging files).
- Follow the roadmap and ensure Sona 0.9.6 runs 100% standalone in this folder.

---

## ✅ Verified Current State

✅ `run_sona.py` executes `.sona` scripts correctly
✅ All 30 standard-library modules import without errors
✅ Core runtime is functional and deterministic
✅ REPL + interpreter initialization works
❌ Missing new 0.9.6 core language features (listed below)

---

## 🚀 Sona 0.9.6 Planned & Verified Features

### ✅ Implemented

- Stable parser and interpreter
- Fully working 30-module standard library
- Deterministic runtime and REPL
- Functional execution pipeline

### 🔄 To Complete in 0.9.6

1. `sleep(ms)` built-in function
2. Expanded string utilities (`string.lower`, `string.length`)
3. Improved IO module (read/write files)
4. AI integration hooks (for SonaCore connection)
5. Foundation for transpilers (Python, JS, Go, Lua)

---

## 🧩 PRE-RELEASE FEATURE ROADMAP

### **TIER 1 — Core Language (1–3 hrs each)**

| Priority | Feature                     | Description                                  |
| -------- | --------------------------- | -------------------------------------------- |
| ⭐       | **Import System**           | Allow `.sona` scripts to use `.smod` files   |
| ⭐       | **Boolean Type & Literals** | Add `true`, `false`, `and`, `or`, `not`      |
| ⭐       | **Function Definitions**    | Add `func`, `return`, and callable functions |
| ⭐       | **Lists / Arrays**          | Support `[]`, indexing, and `append()`       |
| ⭐       | **Comments**                | Implement `#` comments in the grammar        |

---

### **TIER 2 — Medium Effort (3–6 hrs each)**

- Dictionaries / Maps `{ "key": "value" }`
- For loops `for i in range(5)`
- String interpolation `print(f"Hello, {name}")`
- Try/Catch error handling
- File I/O integration using `io.smod`

---

### **TIER 3+ — Save for 0.9.7**

- Classes / Object system
- Lambda functions
- Improved REPL
- Package manager
- HTTP, CSV, XML, Async modules

---

## 📂 EXPECTED FOLDER STRUCTURE

```
F:\SonaMinimal\
├─ sona_core\
│  ├─ grammar.lark
│  ├─ interpreter.py
│  ├─ cli.py
│  ├─ __init__.py
│
├─ smod\
│  ├─ math.smod
│  ├─ string.smod
│  ├─ io.smod
│  ├─ collection.smod
│
├─ run_sona.py
├─ test_hello.sona
├─ test_simple_096.sona
└─ test_stdlib_30.py
```

---

## 🧠 IMPLEMENTATION RULES

1. **Modify only these files** — no VSIX, no `.vscode`, no node_modules.
2. **Ensure version alignment** → `"Sona v0.9.6"` everywhere.
3. **Each new feature** must touch both `grammar.lark` and `interpreter.py`.
4. **Always test after edits:**

   ```bash
   python run_sona.py test_hello.sona
   python run_sona.py test_simple_096.sona
   python test_stdlib_30.py
   ```

5. **Keep stdlib imports functional (30/30 OK)**.
6. **Add features in this order:**

   1. Comments
   2. Boolean type
   3. Lists
   4. Function definitions
   5. Import system

---

## 📅 IMPLEMENTATION SCHEDULE

### **Day 1**

- Add comments
- Implement Boolean constants and logical operators

### **Day 2**

- Implement function definitions, return handling, and call evaluation

### **Day 3**

- Implement `.smod` import system
- Test stdlib module integration

### **Day 4 (Optional)**

- Add list literals, indexing, and append method
- Improve error reporting (line/col info)

---

## 🧩 QUICK START: COMMENTS

**Add to `sona_core/grammar.lark`:**

```python
%ignore /\#[^\n]*/
```

✅ Enables inline and block comments instantly.

Test:

```sona
# This is a comment
x = 5  # Inline comment
print(x)
```

---

## ✅ SUCCESS CRITERIA

The following must run successfully:

```bash
python run_sona.py test_demo_simple_096.sona
python run_sona.py test_simple_096.sona
python test_stdlib_30.py
```

Output should include:

```
✅ Sona v0.9.6 parser initialized successfully
Sona 0.9.6 is operational!
```

And `.sona` files must support:

```sona
import string
print(string.upper("sona"))
```

---

## 📜 VERSION ALIGNMENT

In `__init__.py`:

```python
__version__ = "0.9.6"
```

In all banners:

```
Sona v0.9.6 parser initialized successfully
```

---

## ⚙️ COPILOT EXECUTION BEHAVIOR

When editing:

- Suggest complete file rewrites (not snippets) for grammar or interpreter updates.
- Keep Python syntax deterministic and human-readable.
- Do not add new dependencies or folders.
- Always cross-reference this roadmap before suggesting code.

---

## 🔐 FINAL CHECKLIST BEFORE COMMIT

- [ ] Version string reads 0.9.6
- [ ] Import system verified
- [ ] Booleans and functions operational
- [ ] Lists functional
- [ ] Comments working
- [ ] All 30 stdlib modules import cleanly
- [ ] Test suite passes

---

**End of Copilot Prompt — Sona 0.9.6 Minimal Workspace**
_Save this as `F:\SonaMinimal\COPILOT_PROMPT.md` and reference it in every session._
