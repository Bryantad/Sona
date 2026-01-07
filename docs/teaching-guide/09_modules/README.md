# Module 09: Modules & Imports

## Overview
As programs grow, you need to organize code into separate files. Modules let you split code, reuse functionality, and use the standard library.

**Target Audience:** Ages 12-55, neurodivergent-friendly  
**Prerequisites:** Modules 01-08  
**Duration:** 40-50 minutes

---

## Learning Objectives
By the end of this module, you will:
- Import and use standard library modules
- Create your own modules
- Organize code across multiple files
- Understand module scope and namespaces

---

## Why Modules Matter

Imagine all your code in one giant file. It would be:
- Hard to find anything
- Easy to break things
- Impossible to reuse code

Modules solve this by letting you:
- **Organize** - Keep related code together
- **Reuse** - Use the same code in different projects
- **Share** - Use code others have written

---

## Mini-Lessons in This Module

| Mini | Topic | Focus |
|------|-------|-------|
| [mini-1](mini-1_importing.md) | Importing | Using standard library modules |
| [mini-2](mini-2_creating.md) | Creating Modules | Making your own modules |
| [mini-3](mini-3_organizing.md) | Code Organization | Best practices for project structure |

---

## Key Vocabulary

| Term | Simple Definition | Example |
|------|-------------------|---------|
| **Module** | A file containing code | `math.sona` |
| **Import** | Load a module for use | `import math` |
| **Standard Library** | Built-in modules | `io`, `math`, `time` |
| **Namespace** | Module's name prefix | `math.sqrt()` |

---

## Quick Reference

```sona
// Import entire module
import math
print(math.sqrt(16))  // 4

// Import specific items
from math import sqrt, pow
print(sqrt(16))  // 4 (no prefix needed)

// Import with alias
import math as m
print(m.sqrt(16))  // 4

// Import your own module
import mymodule
import utils.helpers
```

---

## Standard Library Highlights

| Module | Purpose |
|--------|---------|
| `io` | File reading/writing |
| `math` | Mathematical operations |
| `random` | Random numbers |
| `time` | Date and time |
| `string` | Text manipulation |
| `json` | JSON parsing |
| `path` | File path operations |

---

## Practice Challenges

### Challenge 1: Math Module
Use the math module to calculate the area of a circle (π × r²).

### Challenge 2: Random Picker
Use the random module to pick a random item from a list.

### Challenge 3: Create a Module
Create a module with helper functions and use it in another file.

---

## Next Steps
→ Continue to [Module 10: Object-Oriented Programming](../10_oop/README.md)
