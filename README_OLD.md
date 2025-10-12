# Sona v0.9.6 - AI-Native Programming Language# Sona 0.9.6 Official Workspace

**Status**: Production Ready ✅ This is the official, minimal workspace for Sona 0.9.6 and onwards.

**Core Features**: 18/18 Fully Functional

**Stdlib Modules**: 16 Verified + 10 Experimental ## Quick Start

Sona is a modern, expressive programming language with built-in AI capabilities, designed for rapid development of automation tools, data processing pipelines, and AI-assisted applications.### 1. Setup Virtual Environment

---```powershell

python -m venv .venv

## 🚀 Quick Start.\.venv\Scripts\Activate.ps1 # Windows

# source .venv/bin/activate # Linux/macOS

### 1. Setup Virtual Environment```

````powershell### 2. Install Dependencies

python -m venv .venv

.\.venv\Scripts\Activate.ps1  # Windows```bash

# source .venv/bin/activate   # Linux/macOSpip install -r requirements.txt

````

### 2. Install Dependencies### 3. Install Sona

`bash`bash

pip install -r requirements.txtpip install -e .

````



### 3. Install Sona### 4. Test Installation



```bash```bash

pip install -e .# Test import

```python -c "from sona.interpreter import *; print('âœ“ Sona loaded')"



### 4. Test Installation# Run a program

sona test.sona

```bash```

# Test import

python -c "from sona.interpreter import *; print('✅ Sona loaded')"## Directory Structure



# Run a program```

sona test.sonasona/               # Core interpreter

stdlib/             # Standard library (30 modules)

# Or use the direct runner (no install needed)test.sona           # Test file

python run_sona.py test.sonarun_sona.py         # Direct runner (no install needed)

````

---## Running Sona Programs

## ✨ Features### Method 1: Direct Runner (No Installation)

### Core Language (All Working ✅)```bash

python run_sona.py your_program.sona

**Foundation**```

- Variables (`let`, `const`)

- Functions (`func`, `def`) ### Method 2: Installed CLI

- Control flow (`if`, `else`, `elif`)

- Loops (`for`, `while`, `break`, `continue`)```bash

- Return statementssona your_program.sona

- Comments (`//` single-line, `/* */` multi-line)```

**Data Types & Operations**### Method 3: Python Module

- Arrays `[1, 2, 3]`

- Objects `{"key": "value"}````bash

- Strings with interpolationpython -m sona.cli your_program.sona

- Numbers (int, float)```

- Booleans

- Type checking## Documentation

**Advanced**- **FEATURE_FLAGS.md** - Available features

- Error handling (`try`/`catch`/`finally`)- **CHANGELOG.md** - Version history

- Modules (`import`/`export`)- **.sona-policy.json** - Security policies

- Lambda expressions- **sona/stdlib/MANIFEST.json** - Stdlib module listing

- Higher-order functions

- Spread operator `...`## Version

- Async/await support

Sona 0.9.6 - AI-Native Programming Language

**Operators (Correct Precedence)**

- Arithmetic: `+`, `-`, `*`, `/`, `%`, `**`## License

- Comparison: `==`, `!=`, `<`, `>`, `<=`, `>=`

- Logical: `and`, `or`, `not`See LICENSE file

- Bitwise: `&`, `|`, `^`, `~`
- Assignment: `=`, `+=`, `-=`, etc.

### Standard Library

**16 Verified Modules** ✅

```sona
import json;      // JSON parse/stringify
import string;    // String manipulation
import math;      // Math operations
import regex;     // Regular expressions
import fs;        // File system
import path;      // Path manipulation
import io;        // Input/output
import env;       // Environment variables
import csv;       // CSV processing
import date;      // Date operations
import time;      // Time operations
import numbers;   // Number utilities
import boolean;   // Boolean operations
import type;      // Type checking
import comparison;// Comparisons
import operators; // Operator utilities
```

**10 Experimental Modules** ⚠️

```sona
// Available but not fully tested
import random; import encoding; import timer;
import validation; import statistics; import sort;
import search; import uuid; import toml; import hashing;
```

---

## 📝 Example Programs

### Hello World

```sona
print("Hello from Sona v0.9.6!");
```

### Variables and Functions

```sona
let name = "Sona";
const version = "0.9.6";

func greet(who) {
    return "Hello, " + who + "!";
};

print(greet(name));
```

### Loops and Control Flow

```sona
// For loop with break
for i in [1, 2, 3, 4, 5] {
    if i == 3 {
        break;  // ← NEW in v0.9.6!
    };
    print("Number: " + i);
};

// While loop with continue
let n = 0;
while n < 5 {
    n = n + 1;
    if n % 2 == 0 {
        continue;  // ← NEW in v0.9.6!
    };
    print("Odd: " + n);
};
```

### File Operations

```sona
import fs; import io; import json;

// Read file
let content = io.read_file("data.txt");
print(content);

// Write JSON
let data = {"name": "Sona", "version": "0.9.6"};
io.write_file("config.json", json.stringify(data));

// List directory
let files = fs.list_dir(".");
for f in files {
    print(f);
};
```

### Error Handling

```sona
try {
    let data = json.parse('{"invalid": }');
} catch e {
    print("Parse error: " + e);
} finally {
    print("Cleanup complete");
};
```

---

## 🗂️ Directory Structure

```
sona/               # Core interpreter & parser
  ├── interpreter.py
  ├── parser_v090.py
  ├── ast_nodes_v090.py
  ├── grammar_v091_fixed.lark
  └── stdlib/       # Standard library modules
stdlib/             # .smod module files
test.sona           # Example test file
run_sona.py         # Direct runner (no install needed)
```

---

## 🏃 Running Sona Programs

### Method 1: Direct Runner (No Installation)

```bash
python run_sona.py your_program.sona
```

### Method 2: Installed CLI

```bash
sona your_program.sona
```

### Method 3: Python Module

```bash
python -m sona.cli your_program.sona
```

---

## 📚 Documentation

| Document                    | Description                                        |
| --------------------------- | -------------------------------------------------- |
| `FEATURE_AUDIT_096.md`      | Complete feature testing matrix                    |
| `FINAL_RELEASE_STATUS.md`   | Pre-release status and recommendations             |
| `RESEARCH_SONA_PROJECTS.md` | 8 project ideas you can build with Sona            |
| `BREAK_CONTINUE_FIX.md`     | Technical details of break/continue implementation |
| `CHANGELOG.md`              | Version history                                    |
| `sona/stdlib/MANIFEST.json` | Standard library module listing                    |

---

## 🎯 What Can You Build?

Sona v0.9.6 is production-ready for:

1. **CLI Automation Tools** - File organizers, log parsers, dev utilities
2. **Data Processing** - ETL pipelines, CSV/JSON transforms, analytics
3. **API Clients** - Integration scripts, webhook handlers, sync tools
4. **AI-Assisted Development** - Code generators, scaffolding tools
5. **Task Automation** - Schedulers, background workers, cron jobs
6. **Microservices** - Small APIs, internal tools, endpoints
7. **CI/CD Tools** - Test runners, build scripts, deployment automation
8. **Educational Projects** - Teaching programming, interactive exercises

See `RESEARCH_SONA_PROJECTS.md` for detailed project architectures and code examples.

---

## 🆕 What's New in v0.9.6

### Fixed

- ✅ **Break and Continue statements** - Now fully functional in all loops
- ✅ **Operator precedence** - All operators have correct priority
- ✅ **Standard library** - Verified 16 core modules

### Added

- ✅ **Export statement** - Module exports work correctly
- ✅ **Comprehensive testing** - Full feature audit completed

### Documentation

- ✅ **Feature matrix** - Complete testing coverage documented
- ✅ **Project ideas** - 8 detailed project architectures
- ✅ **Module manifest** - Accurate stdlib listing

---

## 🔬 Testing

Run the test suite:

```bash
python run_sona.py test_all_features.sona
python run_sona.py test_break_continue.sona
```

All 18 core features have passing tests.

---

## 🤝 Contributing

This is a stable release workspace. For experimental features and development:

- Match statements (syntax exists, runtime TBD)
- When expressions (planned for v0.9.7)
- Classes (planned for v0.10.0)
- Destructuring (planned for v0.10.0)

---

## 📄 License

See LICENSE file for details.

---

## 🆚 Version

**Sona v0.9.6** - "Stable Core, Growing Ecosystem"  
Released: October 2025  
Python Compatibility: 3.8+  
Platform: Windows, Linux, macOS

---

**Ready to build? Run `python run_sona.py test.sona` to get started!**
