# Sona Minimal Runtime - Complete Extraction Guide

**Date:** October 9, 2025  
**Purpose:** Extract minimal Sona language runtime from F:\Sona workspace

---

## ❌ Reality Check: Full CLI Has Too Many Dependencies

After attempting minimal extraction, we discovered that `sona/cli.py` requires:
- `sona/type_system/` (entire directory)
- `sona/type_config.py`
- `sona/ai/` (for AI commands)
- `sona/providers/` (for AI provider management)
- `sona/perf/` (for performance monitoring)
- Many other internal modules

**The CLI is NOT minimal** - it's the full-featured production interface.

---

## ✅ What Actually Works: Direct Interpreter Usage

Instead of copying the CLI, you can use the interpreter directly in two ways:

### Method 1: Direct Python Execution (Works in Original Workspace)

Stay in `F:\Sona` and use the installed package:

```powershell
cd F:\Sona
sona run test.sona
```

Or if you have dependencies:
```powershell
cd F:\Sona
python -m sona.cli run test.sona
```

### Method 2: Programmatic Execution (Minimal Dependencies)

Create your own runner script that calls the interpreter directly.

---

## 📦 True Minimal Files (For Understanding the Core)

If you want to extract **just** the core parsing + execution logic for study:

### Required Core Files (Tier A - Parser + Interpreter)

```
sona/
  __init__.py           # Package marker
  parser_v090.py        # Parser (converts text → AST)
  ast_nodes_v090.py     # AST node definitions
  interpreter.py        # Executes AST nodes
  grammar_v090.lark     # Lark grammar rules
  grammar_v091_fixed.lark  # Fixed grammar (multi-param)
```

### Stdlib (Tier B - Only if Programs Import Them)

```
stdlib/
  math.smod             # Module interface
  math.py               # Python implementation
  string.smod
  string.py
  io.smod
  json.smod
```

---

## 🔬 Current Minimal Extraction Status

**Location:** `F:\SonaMinimal`

**Files Copied:**
```
F:\SonaMinimal\
  sona/
    __init__.py
    cli.py               # ⚠️ Has too many dependencies
    interpreter.py
    grammar.lark
    parser_v090.py
    ast_nodes_v090.py
    grammar_v090.lark
    grammar_v091_fixed.lark
  stdlib/
    math.smod
    math.py
    string.smod
    string.py
    io.smod
    json.smod
  run_sona.py           # Custom minimal runner (better than CLI)
  test_hello.sona       # Test file
```

**Issues Encountered:**
1. ✅ `cli.py` needs `type_system/` → Too many dependencies
2. ✅ Parser needs `ast_nodes_v090.py` → Copied
3. ✅ Parser needs grammar files → Copied
4. ❌ Unicode encoding issues on Windows → Need to fix

---

## 🎯 Recommended Approach: Stay in Original Workspace

**Instead of extracting**, work directly in `F:\Sona`:

### Quick Test Script (In Original Workspace)

```python
# F:\Sona\quick_test.py
from sona.parser_v090 import SonaParserv090
from sona.interpreter import SonaUnifiedInterpreter

# Read source
with open("test.sona", "r", encoding="utf-8") as f:
    source = f.read()

# Parse
parser = SonaParserv090()
ast_nodes = parser.parse(source, "test.sona")

# Execute
if ast_nodes:
    interpreter = SonaUnifiedInterpreter()
    for node in ast_nodes:
        result = interpreter.execute_ast_node(node)
        if result is not None:
            print(result)
```

**Usage:**
```powershell
cd F:\Sona
python quick_test.py
```

This works because all dependencies are already in place!

---

## 📋 Dependencies That Would Need Copying for True Standalone

If you really want a standalone extraction, you'd need to copy these additional directories:

```
sona/
  __init__.py
  parser_v090.py
  ast_nodes_v090.py
  interpreter.py
  grammar_v090.lark
  grammar_v091_fixed.lark
  
  # Additional dependencies
  type_system/          # Type checking system (entire dir)
  type_config.py        # Type configuration
  perf/                 # Performance monitoring
  providers/            # AI providers
  ai/                   # AI integration
  features/             # Feature flags
  control/              # Control flow
  core/                 # Core utilities
  utils/                # Utility functions
  vm/                   # Virtual machine components
  
stdlib/
  *.smod               # All module interfaces
  *.py                 # All Python implementations
  __init__.py
  utils/               # Stdlib utilities
```

**This is ~50+ files** - not really "minimal" anymore!

---

## 💡 Alternative: Use the Installed Package

If Sona is installed via `pip install -e .`:

```python
# Anywhere on your system
import sona
from sona.parser_v090 import SonaParserv090
from sona.interpreter import SonaUnifiedInterpreter

# Your code here
```

---

## 🚀 Best Practices

### For Development
- **Stay in F:\Sona** workspace
- Use `sona run file.sona` or `python -m sona.cli run file.sona`
- All dependencies available

### For Distribution
- Package with `pip install -e .`
- Creates `sona` command globally
- Proper Python package structure

### For Learning the Core
- Read `sona/parser_v090.py` - see how parsing works
- Read `sona/interpreter.py` - see how execution works
- Read `sona/grammar_v091_fixed.lark` - see language syntax
- Don't try to extract - too many interdependencies

---

## 🔧 Fixing the Minimal Extraction (If You Really Want It)

To fix the current `F:\SonaMinimal`:

### Step 1: Copy Missing Dependencies

```powershell
$src = "F:\Sona"
$dst = "F:\SonaMinimal"

# Copy additional required modules
Copy-Item "$src\sona\type_config.py" "$dst\sona\" -Force
New-Item -ItemType Directory -Force -Path "$dst\sona\type_system" | Out-Null
Copy-Item "$src\sona\type_system\*" "$dst\sona\type_system\" -Recurse -Force
```

### Step 2: Fix Unicode Issues

Edit `sona/parser_v090.py` and replace emoji with plain text:
```python
# Change:
print("\u2705 Sona v0.9.0 parser initialized successfully")
# To:
print("[OK] Sona v0.9.0 parser initialized successfully")
```

### Step 3: Use Custom Runner

Don't use `cli.py` - use the custom `run_sona.py` that's already in `F:\SonaMinimal`.

---

## 📊 Complexity Summary

| Approach | Files Needed | Complexity | Works? |
|----------|--------------|------------|--------|
| **Stay in F:\Sona** | 0 (use existing) | ✅ Simple | ✅ Yes |
| **Minimal extraction** | 6-10 core files | ⚠️ Medium | ⚠️ Partial |
| **Full extraction** | 50+ files + dirs | ❌ Complex | ❌ Not worth it |
| **Install package** | 0 (pip handles it) | ✅ Simple | ✅ Yes |

---

## ✅ Recommendation

**Don't extract to SonaMinimal.** Instead:

1. **Work in F:\Sona** directly - everything already works there
2. **Or install properly:** `pip install -e .` from F:\Sona
3. **Or use the original CLI:** `sona run file.sona`

The "minimal extraction" approach revealed that Sona is an integrated system where components are tightly coupled. Extracting individual pieces breaks dependencies.

---

**File:** `F:\SonaMinimal\EXTRACTION_REALITY_CHECK.md`  
**Created:** October 9, 2025  
**Status:** Attempted extraction, discovered high coupling  
**Recommendation:** Work in original workspace instead
