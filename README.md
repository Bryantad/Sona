# 🎵 Sona v0.10.1

**AI-Native Programming Language with 91-Module Standard Library**

[![Version](https://img.shields.io/badge/version-0.10.1-blue.svg)](https://github.com/Bryantad/Sona)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

Sona is a modern, expressive programming language designed for rapid development with built-in AI capabilities. Perfect for automation, data processing, web services, and AI-assisted applications.

---

## ?s? What's New in v0.10.1

- ?o. **Cognitive Preview** ??" Intent, decision provenance, trace, and cognitive scopes.
- ?o. **Cognitive reports** ??" Exportable report artifacts and linting (runtime + LSP).
- ?o. **Profile annotations** ??" ADHD/dyslexia profile metadata surfaced in the editor.
- dY"" **Version sync** ??" Packaging/runtime/docs aligned on v0.10.1.

[See Full Release Notes ?+'](SONA_0.10.0_RELEASE_NOTES.md)

---

## Cognitive Features

Example 1: Intent anchors

```sona
@intent "parse user config safely";
```

Example 2: Focus blocks with validation

```sona
import json;

func validate(cfg) {
    return cfg;
}

@intent "parse user config safely";
focus {
    let cfg = json.parse(text);
    validate(cfg);
}
```

Example 3: Explainable checkpoints

```sona
cognitive_trace(enabled=true);
explain_step(note="checkpoint before export");
```

Note: Each `@intent` is recorded as an intent entry in cognitive reports.

---

## 🚀 Quick Start

### Installation

```powershell
# 1. Clone or download
git clone https://github.com/Bryantad/Sona.git
cd Sona

# 2. Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
# source .venv/bin/activate   # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Sona
pip install -e .
```

### Your First Program

Create `hello.sona`:

```sona
// Simple greeting
print("Hello from Sona v0.10.0!");

// Use stdlib
import json;
let data = {"version": "0.10.0", "modules": 91};
print(json.stringify(data));
```

Run it:

```bash
python run_sona.py hello.sona
```

---

## 🎯 Core Features

### ✅ All Tier 1 Features (Production Ready)

| Feature            | Description                           | Status |
| ------------------ | ------------------------------------- | ------ |
| **Variables**      | `let x = 10;` `const PI = 3.14;`      | ✅     |
| **Functions**      | `func add(a, b) { return a + b; }`    | ✅     |
| **Control Flow**   | `if`, `when`, `match`, `while`, `for` | ✅     |
| **Loop Control**   | `break`, `continue`, `repeat`         | ✅     |
| **Collections**    | Lists, Dicts, Sets, Tuples            | ✅     |
| **Destructuring**  | `let [a, b] = [1, 2];`                | ✅     |
| **Error Handling** | `try/catch` blocks                    | ✅     |
| **Modules**        | `import json;` `export func;`         | ✅     |
| **Classes**        | OOP with inheritance                  | ✅     |
| **Operators**      | Arithmetic, logical, comparison       | ✅     |

---

## 📦 Standard Library (91 Modules)

### 🔵 Core System (7 modules)

```sona
import json;        // JSON parsing/serialization
import math;        // Mathematical operations
import string;      // String manipulation
import regex;       // Regular expressions
import boolean;     // Boolean utilities
import type;        // Type checking
import comparison;  // Comparison utilities
```

### 📊 Data Structures (7 modules)

```sona
import collection;  // Collections namespace
import queue;       // Queue operations
import stack;       // Stack operations
import graph;       // Graph algorithms
import tree;        // Tree structures
import heap;        // Min/Max heaps
import matrix;      // 2D matrices
```

### 📁 I/O & Formats (8 modules)

```sona
import fs;          // File system operations
import path;        // Path manipulation
import io;          // Input/output
import csv;         // CSV processing
import yaml;        // YAML serialization
import toml;        // TOML configuration
import compression; // Gzip/zip compression
import xml;         // XML parsing/building
```

### 🌐 Network & Web (9 modules)

```sona
import http;        // HTTP client
import url;         // URL parsing/building
import cookies;     // Cookie management
import session;     // HTTP sessions
import websocket;   // WebSocket client
import dns;         // DNS resolution
import smtp;        // Email sending
import proxy;       // HTTP proxy
import ftp;         // FTP client
import oauth;       // OAuth2 flows
```

### 💾 Database & Storage (6 modules)

```sona
import sqlite;      // SQLite database
import cache;       // In-memory cache
import redis;       // Redis client
import orm;         // Simple ORM
import query;       // SQL query builder
import migration;   // Database migrations
```

### 🔒 Security & Auth (6 modules)

```sona
import jwt;         // JWT tokens
import crypto;      // Cryptographic hashing
import password;    // Password hashing
import hashing;     // General hashing
import secrets;     // Secure random
import permissions; // RBAC system
```

### ⚡ Async & Concurrency (5 modules)

```sona
import async;       // Async utilities
import thread;      // Threading
import process;     // Process management
import pool;        // Thread/process pools
import promise;     // Promise/Future pattern
```

### 🧪 Testing & Quality (5 modules)

```sona
import test;        // Test framework
import assert;      // Assertions
import mock;        // Mock objects
import benchmark;   // Performance testing
import profiler;    // Code profiling
```

### 🛠️ Utilities (13 modules)

```sona
import env;         // Environment variables
import date;        // Date operations
import time;        // Time operations
import timer;       // Timer utilities
import random;      // Random generation
import encoding;    // Base64/URL encoding
import uuid;        // UUID generation
import validation;  // Input validation
import statistics;  // Statistical functions
import sort;        // Sorting algorithms
import search;      // Search algorithms
import numbers;     // Number utilities
import operators;   // Operator utilities
```

### 🤖 Automation (7 modules)

```sona
import cli;         // CLI argument parsing
import logging;     // Logging system
import config;      // Configuration management
import scheduler;   // Task scheduling
import signal;      // Event system
import shell;       // Shell commands
import bitwise;     // Bitwise operations
```

### 🔧 Functional Programming (4 modules)

```sona
import functional;  // Composition, currying
import decorator;   // Common decorators
import iterator;    // Iterator utilities
import color;       // Color manipulation
```

### 📝 Templates & Processing (3 modules)

```sona
import template;    // Template engine
import markdown;    // Markdown to HTML
import xml;         // XML processing
```

---

## 💡 Code Examples

### Web Scraping with Sessions

```sona
import session;
import json;

// Create HTTP session
let s = session.create();
s.set_header("User-Agent", "Sona/0.10.0");

// Make requests
let response = s.get("https://api.example.com/data");
let data = json.parse(response.body);

print("Fetched " + data.length + " items");
```

### Database Operations

```sona
import sqlite;
import orm;

// Connect to database
let db = sqlite.connect("app.db");
db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)");

// Insert data
db.insert("users", {"name": "Alice", "email": "alice@example.com"});
db.insert("users", {"name": "Bob", "email": "bob@example.com"});

// Query
let users = db.query("SELECT * FROM users WHERE name LIKE ?", ["A%"]);
for user in users {
    print(user.name + ": " + user.email);
}
```

### JWT Authentication

```sona
import jwt;
import password;

// Hash password
let hashed = password.hash("secretpassword");
print("Hashed: " + hashed);

// Create JWT token
let payload = {
    "user_id": 123,
    "username": "alice",
    "role": "admin"
};

let token = jwt.encode(payload, "my-secret-key", exp_minutes=60);
print("Token: " + token);

// Verify token
let decoded = jwt.decode(token, "my-secret-key");
print("User ID: " + decoded.user_id);
```

### Graph Algorithms

```sona
import graph;

// Create graph
let g = graph.create();
g.add_edge("A", "B");
g.add_edge("B", "C");
g.add_edge("A", "C");
g.add_edge("C", "D");

// Find shortest path
let path = g.shortest_path("A", "D");
print("Path: " + path.join(" -> "));  // A -> C -> D

// Check for cycles
let has_cycle = g.has_cycle();
print("Has cycle: " + has_cycle);
```

### Testing with Assertions

```sona
import test;
import assert;

// Create test suite
let suite = test.suite("Math Tests");

suite.add_test("addition", func() {
    let result = 2 + 2;
    assert.equal(result, 4);
});

suite.add_test("division", func() {
    let result = 10 / 2;
    assert.equal(result, 5);
});

// Run tests
let results = suite.run();
print("Passed: " + results.passed + "/" + results.total);
```

### Template Rendering

```sona
import template;

// Create template
let tmpl = "Hello {{name}}, you have {{count}} messages.";

// Render
let output = template.render(tmpl, {
    "name": "Alice",
    "count": 5
});

print(output);  // Hello Alice, you have 5 messages.
```

### Functional Programming

```sona
import functional;

// Function composition
let add_one = func(x) { return x + 1; };
let double = func(x) { return x * 2; };

let f = functional.pipe(add_one, double);
let result = f(5);  // (5 + 1) * 2 = 12

print("Result: " + result);

// Currying
let multiply = func(a, b) { return a * b; };
let triple = functional.curry(multiply)(3);
print("Triple 7: " + triple(7));  // 21
```

---

## 📚 Documentation

- **[Quick Start Guide](QUICK_START.md)** - Get up and running in 5 minutes
- **[API Reference](API.md)** - Complete API documentation
- **[Release Notes](SONA_0.10.0_RELEASE_NOTES.md)** - What's new in v0.10.0
- **[Examples](examples/)** - Sample projects and code snippets

---

## ✅ Verification

Run the comprehensive test suite:

```powershell
# PowerShell
.\run_all_tests.ps1

# Or run test file directly
python run_sona.py test_all_097.sona
```

Expected output:

```
✅ ALL 91 MODULES VERIFIED SUCCESSFULLY!

Module Categories:
  • Core System:        7 modules
  • Data Structures:    7 modules
  • I/O & Formats:      8 modules
  • Network & Web:      9 modules
  • Database:           6 modules
  • Security:           6 modules
  • Async:              5 modules
  • Testing:            5 modules
  • Utilities:         13 modules
  • Automation:         7 modules
  • Functional:         4 modules
  • Templates:          3 modules
                      ────────────
    TOTAL:               91 modules
```

---

## 🏗️ Architecture

### Zero Dependencies

Sona's standard library has **zero external dependencies**. Everything is built on Python's standard library, ensuring:

- ✅ Fast installation
- ✅ No version conflicts
- ✅ Maximum stability
- ✅ Easy deployment

### Module Design

Each module follows consistent patterns:

```python
# Comprehensive docstrings
def function(param: type) -> type:
    """
    Description of what function does.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Example:
        >>> result = function(value)
        >>> print(result)
    """
    # Implementation
    pass
```

### Category Organization

Modules are organized into 12 logical categories:

1. **Core System** - Fundamental operations
2. **Data Structures** - Collections and algorithms
3. **I/O & Formats** - File and format handling
4. **Network & Web** - HTTP, WebSocket, DNS, etc.
5. **Database & Storage** - Data persistence
6. **Security & Auth** - Cryptography and authentication
7. **Async & Concurrency** - Parallel execution
8. **Testing & Quality** - Test and debug tools
9. **Utilities** - Common helper functions
10. **Automation** - CLI, logging, scheduling
11. **Functional Programming** - FP patterns
12. **Templates & Processing** - Text processing

---

## 🛣️ Roadmap

### v0.10.x (Cognitive Preview)

- Cognitive report schema stabilization
- LSP cognitive diagnostics depth
- Export workflow integrations
- Runtime coverage consistency

### v1.0.0 (Target: Q2 2024)

- Production-grade stability
- Comprehensive test coverage
- Package manager (npm-like)
- VS Code extension

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas for Contribution

- 📝 Documentation improvements
- 🧪 Additional test cases
- 🐛 Bug fixes
- ✨ New module proposals
- 🌍 Internationalization

---

## 📄 License

Sona is released under the MIT License. See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with ❤️ using:

- **Python** - Core runtime
- **Lark** - Parser generator
- **Community feedback** - Feature requests and bug reports

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Bryantad/Sona/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Bryantad/Sona/discussions)
- **Documentation**: [docs/](docs/)

---

<div align="center">

**Sona v0.10.0** - 91 Modules, Zero Dependencies, Infinite Possibilities

Made with 🎵 by the Sona Team

</div>
