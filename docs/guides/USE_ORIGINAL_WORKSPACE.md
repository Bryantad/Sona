# ✅ Simple Solution: Use Sona from the Original Workspace

**The minimal extraction revealed:** Sona has many interdependent modules. Instead of extracting, work directly in `F:\Sona`.

---

## 🎯 Quick Start Guide (Works Immediately)

### Option 1: Use the Full CLI (Recommended)

```powershell
cd F:\Sona
sona run your_program.sona
```

### Option 2: Use Python Module

```powershell
cd F:\Sona
python -m sona.cli run your_program.sona
```

### Option 3: Direct Interpreter (Programmatic)

```python
# F:\Sona\run_program.py
from sona.parser_v090 import SonaParserv090
from sona.interpreter import SonaUnifiedInterpreter

def run_sona(filename):
    # Read
    with open(filename, 'r', encoding='utf-8') as f:
        source = f.read()
    
    # Parse
    parser = SonaParserv090()
    ast_nodes = parser.parse(source, filename)
    
    # Execute
    if ast_nodes:
        interpreter = SonaUnifiedInterpreter()
        for node in ast_nodes:
            result = interpreter.execute_ast_node(node)
            if result is not None:
                print(result)

if __name__ == "__main__":
    import sys
    run_sona(sys.argv[1])
```

**Usage:**
```powershell
cd F:\Sona
python run_program.py test.sona
```

---

## 📝 Create a Test Program

```sona
// test.sona
let message = "Hello from Sona!"
print(message)

let x = 10
let y = 20
let sum = x + y
print("Sum:", sum)
```

**Run it:**
```powershell
sona run test.sona
```

---

## 🎓 Learn the Core Architecture

**To understand how Sona works**, read these files in order:

1. **`sona/grammar_v091_fixed.lark`** - Language syntax rules
2. **`sona/parser_v090.py`** - Converts source code → AST
3. **`sona/ast_nodes_v090.py`** - AST node definitions
4. **`sona/interpreter.py`** - Executes AST nodes
5. **`stdlib/*.smod`** - Standard library module interfaces

All files are in `F:\Sona` - no extraction needed!

---

## 🚀 Bottom Line

**You don't need SonaMinimal.**  
**Just use F:\Sona directly** - all dependencies are already there and working.

---

**File:** `F:\SonaMinimal\USE_ORIGINAL_WORKSPACE.md`  
**Status:** Simple alternative to extraction
