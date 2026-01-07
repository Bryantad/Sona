# Guides & Tutorials

This folder contains getting started guides, tutorials, and how-to documentation.

## 📖 Getting Started

### Quick Start

1. **Install Dependencies**

   ```powershell
   pip install -r requirements.txt
   ```

2. **Run Your First Sona Script**

   ```powershell
   python run_sona.py test_hello.sona
   ```

3. **Try the Examples**
   ```powershell
   python run_sona.py test.sona
   ```

---

## 📚 Available Guides

### [COPILOT_PROMPT.md](./COPILOT_PROMPT.md)

GitHub Copilot integration and usage guide.

**Topics:**

- Setting up Copilot with Sona
- Getting better code suggestions
- Copilot best practices
- Example prompts

---

### [USE_ORIGINAL_WORKSPACE.md](./USE_ORIGINAL_WORKSPACE.md)

Workspace setup and organization guide.

**Topics:**

- Workspace structure
- File organization
- Configuration
- Best practices

---

## 🚀 Quick Reference

### Running Sona Scripts

```powershell
# Basic script execution
python run_sona.py script.sona

# With verbose output
python run_sona.py -v script.sona

# Run tests
python run_sona.py test_all_30_imports.sona
```

---

### Basic Sona Syntax

#### Variables

```sona
let x = 10;
let name = "Sona";
let flag = true;
```

#### Functions

```sona
func greet(name) {
    return "Hello, " + name;
}

print(greet("World"));
```

#### Loops

```sona
for i in [1, 2, 3, 4, 5] {
    print(i);
}

let x = 0;
while x < 5 {
    print(x);
    x = x + 1;
}
```

#### Conditionals

```sona
if x > 10 {
    print("Greater than 10");
} elif x > 5 {
    print("Greater than 5");
} else {
    print("5 or less");
}
```

#### Importing Modules

```sona
import json;
import string;
import math;

let data = json.parse('{"key": "value"}');
let upper = string.upper("hello");
let sqrt = math.sqrt(16);
```

---

## 🎓 Learning Path

### Level 1: Basics

1. Variables and types
2. Basic operators
3. Print statements
4. Simple functions

**Example:**

```sona
let name = "Learner";
let age = 25;
print("Hello, " + name + "! You are " + age + " years old.");
```

---

### Level 2: Control Flow

1. If/else statements
2. For loops
3. While loops
4. Break/continue

**Example:**

```sona
for i in [1, 2, 3, 4, 5] {
    if i == 3 {
        continue;  // Skip 3
    }
    if i == 5 {
        break;     // Stop at 5
    }
    print(i);      // Prints: 1, 2, 4
}
```

---

### Level 3: Functions & Modules

1. Function definitions
2. Return values
3. Module imports
4. Module functions

**Example:**

```sona
import math;

func circle_area(radius) {
    return math.pi() * radius * radius;
}

print("Area: " + circle_area(5));
```

---

### Level 4: Data Structures

1. Arrays
2. Objects
3. Collection utilities
4. Data manipulation

**Example:**

```sona
import collection;

let numbers = [1, 2, 3, 4, 5];
print("Length: " + collection.len(numbers));
print("First: " + collection.first(numbers));
print("Last: " + collection.last(numbers));
```

---

### Level 5: File I/O

1. Reading files
2. Writing files
3. Path manipulation
4. Directory operations

**Example:**

```sona
import io;
import fs;
import path;

// Write file
io.write_file("output.txt", "Hello, Sona!");

// Read file
let content = io.read_file("output.txt");
print(content);

// List directory
let files = fs.list_dir(".");
for f in files {
    print(f);
}
```

---

### Level 6: Data Processing

1. JSON parsing
2. CSV reading
3. Data transforms
4. Statistics

**Example:**

```sona
import json;
import csv;

// JSON
let obj = {"name": "Sona", "version": "0.9.6"};
let json_str = json.stringify(obj);
print(json_str);

// CSV
let rows = csv.reader("data.csv");
for row in rows {
    print(row);
}
```

---

## 🔧 Common Patterns

### Error Handling

```sona
try {
    // Risky operation
    let result = dangerous_function();
    print(result);
} catch e {
    print("Error: " + e);
}
```

### Working with APIs

```sona
import http;
import json;

let response = http.get("https://api.example.com/data");
if response["status"] == 200 {
    let data = json.parse(response["body"]);
    print(data);
}
```

### File Processing

```sona
import io;
import string;

let content = io.read_file("input.txt");
let lines = string.split(content, "\n");
let processed = [];

for line in lines {
    processed.append(string.upper(line));
}

io.write_file("output.txt", string.join(processed, "\n"));
```

---

## 🐛 Debugging Tips

### Enable Verbose Mode

```powershell
python run_sona.py -v script.sona
```

### Add Debug Prints

```sona
print("DEBUG: Variable x = " + x);
print("DEBUG: Entering function");
```

### Check Types

```sona
import type;

print(type.of(x));  // Check variable type
```

### Test Incrementally

- Test small pieces of code first
- Build up complexity gradually
- Verify each step works before moving on

---

## 📦 Module Reference

All 30 stdlib modules are available. Quick reference:

| Category    | Modules                                 |
| ----------- | --------------------------------------- |
| Data        | json, csv, toml, yaml                   |
| Files       | fs, path, io                            |
| Text        | string, regex, encoding                 |
| Math        | math, random, statistics                |
| Time        | date, time, timer                       |
| Collections | collection, queue, stack, sort, search  |
| System      | env, type, validation, uuid, hashing    |
| Operators   | boolean, numbers, comparison, operators |

**Full documentation:** [../features/STDLIB_30_MODULES.md](../features/STDLIB_30_MODULES.md)

---

## 🎯 Project Ideas

Want to build something? Check out:

- [../projects/RESEARCH_SONA_PROJECTS.md](../projects/RESEARCH_SONA_PROJECTS.md)

8 fully detailed project ideas with roadmaps, from CLI utilities to AI code generators.

---

## ❓ Getting Help

### Documentation

- **Features** → [../features/](../features/)
- **Testing** → [../testing/](../testing/)
- **Troubleshooting** → [../troubleshooting/](../troubleshooting/)
- **Development** → [../development/](../development/)

### Common Issues

- Module not found? → [../troubleshooting/MODULE_LOADER_FIX.md](../troubleshooting/MODULE_LOADER_FIX.md)
- Break/continue not working? → [../troubleshooting/BREAK_CONTINUE_FIX.md](../troubleshooting/BREAK_CONTINUE_FIX.md)
- Syntax errors? → Check grammar in `sona/grammar.lark`

---

## 🌟 Best Practices

1. **Always import modules at the top**

   ```sona
   import json;
   import fs;
   import io;
   ```

2. **Use meaningful variable names**

   ```sona
   let user_count = 10;  // Good
   let x = 10;           // Bad
   ```

3. **Add comments for complex logic**

   ```sona
   // Calculate compound interest
   let result = principal * math.pow(1 + rate, years);
   ```

4. **Handle errors gracefully**

   ```sona
   try {
       fs.read_file("data.txt");
   } catch e {
       print("File not found: " + e);
   }
   ```

5. **Test your code**
   ```sona
   // Write tests
   if result == expected {
       print("✅ Test passed");
   } else {
       print("❌ Test failed");
   }
   ```

---

**Ready to start coding?** Pick a tutorial level above and dive in!
