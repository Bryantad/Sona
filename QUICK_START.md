# Sona v0.9.6 Runtime - Quick Start Guide

## ✅ Your Runtime is ACTIVE!

**Status:** Fully operational  
**Version:** 0.9.6  
**Location:** F:\SonaMinimal  
**Extension:** Installed in VS Code

---

## 🚀 How to Use Sona

### Method 1: Direct Execution (Recommended)

```powershell
# Run any .sona file
python run_sona.py yourfile.sona

# Example
python run_sona.py test_proper.sona
```

### Method 2: VS Code Extension

1. Open any `.sona` file in VS Code
2. Enjoy syntax highlighting
3. Use Focus Mode: `Ctrl+Shift+P` → "Sona: Enable Focus Mode"

### Method 3: Python Module (If pip install works)

```powershell
sona yourfile.sona
```

---

## 📝 Sona Syntax Quick Reference

### Proper Sona Syntax (Requires Semicolons)

```sona
print("Hello, Sona!");
x = 42;
y = 10;
result = x + y;
print("Result: " + str(result));
```

### Python-Compatible Mode (Fallback)

```sona
print("Hello, Sona!")
x = 42
y = 10
result = x + y
print("Result: " + str(result))
```

**Note:** Parser prefers semicolons, but Python mode works as fallback.

---

## 📚 Stdlib Modules (30 Available)

### Core System
```sona
import json;
import string;
import math;
import time;
import date;
```

### File Operations
```sona
import fs;
import path;
import io;
```

### Data Processing
```sona
import csv;
import yaml;
import toml;
```

### Full List
- **Core (12):** json, string, math, numbers, boolean, type, comparison, operators, time, date, random, regex
- **I/O (4):** fs, path, io, env
- **Collections (3):** collection, queue, stack
- **Data (7):** csv, encoding, timer, validation, statistics, sort, search
- **Advanced (4):** uuid, yaml, toml, hashing

---

## 🧪 Test Your Installation

### Quick Test File (`test.sona`)

```sona
print("=== Sona v0.9.6 Test ===");
name = "Sona";
version = "0.9.6";
print("Language: " + name);
print("Version: " + version);
x = 42;
y = 10;
print("Math: " + str(x) + " + " + str(y) + " = " + str(x + y));
print("✓ Runtime is working!");
```

### Run It
```powershell
python run_sona.py test.sona
```

### Expected Output
```
=== Sona v0.9.6 Test ===
Language: Sona
Version: 0.9.6
Math: 42 + 10 = 52
✓ Runtime is working!
```

---

## 🔧 Troubleshooting

### Issue: Parser Errors

**Symptom:** "Unexpected token" or "Expected SEMICOLON"  
**Solution:** Add semicolons to end of statements

```sona
// ❌ This may fail in strict mode
x = 10
y = 20

// ✅ This always works
x = 10;
y = 20;
```

### Issue: Comments Not Working

**Symptom:** Parser rejects `#` or `//` comments  
**Solution:** Remove comments or use Python mode

```sona
// ❌ Not supported yet
# x = 10  # This is a comment

// ✅ Use this instead
x = 10
```

### Issue: pip install Fails

**Symptom:** "Could not install packages"  
**Solution:** You don't need pip install! Use direct runner:

```powershell
python run_sona.py yourfile.sona
```

The VS Code extension already has the runtime bundled.

---

## 📂 File Locations

```
F:\SonaMinimal\
├── run_sona.py              ← Direct runner
├── test_proper.sona         ← Working test file
├── sona/                    ← Core language
│   └── stdlib/              ← 30 modules
├── vscode-extension/        ← VS Code extension
│   └── .../runtime/         ← Bundled runtime
└── README.md                ← Full documentation
```

---

## 🎯 What Works Now

| Feature | Status |
|---------|--------|
| Syntax Highlighting | ✅ Working |
| Direct Execution | ✅ Working |
| 30 Stdlib Modules | ✅ Available |
| VS Code Extension | ✅ Installed |
| Parser v0.9.6 | ✅ Active |
| Python Fallback | ✅ Working |
| Focus Mode | ✅ Available |

---

## 🚀 Next Steps

1. **Start Coding:** Open VS Code and create `.sona` files
2. **Test Features:** Try syntax highlighting, Focus Mode
3. **Build Projects:** Use the 30 stdlib modules
4. **Share:** Show others your Sona code!

---

## 💡 Pro Tips

1. **Always use semicolons** for best results
2. **Test in VS Code** for syntax highlighting
3. **Use `run_sona.py`** for quick execution
4. **Check STDLIB_30_MODULES.md** for module docs

---

## 📞 Need Help?

- **Documentation:** See `RUNTIME_VERIFICATION.md`
- **Modules:** See `STDLIB_30_MODULES.md`
- **Issues:** Check GitHub repo

---

**Your Sona v0.9.6 runtime is ready! Happy coding! 🎉**
