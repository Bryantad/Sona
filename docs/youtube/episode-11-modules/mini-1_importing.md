# Mini-Episode 11.1: Importing Modules 📦

> Use code from other files

---

## What Are Modules?

**Modules** = Files containing reusable code

Instead of writing everything from scratch, import what you need!

---

## Basic Import

```sona
import math

// Now use functions from math module
let result = math.sqrt(16)  // 4.0
let pi = math.pi            // 3.14159...
```

---

## Import Specific Items

```sona
// Only import what you need
from math import sqrt, pi

// Use directly (no math. prefix)
let result = sqrt(16)  // 4.0
print(pi)              // 3.14159...
```

---

## Import Everything (Use Sparingly)

```sona
from math import *

// All math functions available
print(sqrt(25))    // 5.0
print(floor(3.7))  // 3
print(ceil(3.2))   // 4
```

⚠️ Not recommended - can cause naming conflicts!

---

## Import with Alias

```sona
import math as m

// Shorter name
let result = m.sqrt(100)
```

Useful for modules with long names!

---

## Common Standard Library Modules

```sona
import math      // Math functions
import random    // Random numbers
import time      // Time and dates
import json      // JSON handling
import fs        // File system operations
import http      // Web requests
```

---

## Import Order Convention

```sona
// 1. Standard library
import math
import json

// 2. Third-party modules
import some_library

// 3. Your own modules
import my_helpers
```

---

## What Happens When You Import?

1. Sona finds the module file
2. Runs the code in that file
3. Makes its functions/variables available to you

```sona
// helper.sona
print("Helper module loaded!")  // This runs on import!

func greet() {
    print("Hello!")
}
```

```sona
// main.sona
import helper  // Prints: "Helper module loaded!"
helper.greet() // Prints: "Hello!"
```

---

## Import Errors

```sona
import nonexistent_module  // Error: Module not found
```

**Fix:** Check spelling, check if module is installed

---

## Quick Reference

| Syntax | What It Does |
|--------|--------------|
| `import x` | Import module x |
| `from x import y` | Import y from x |
| `import x as z` | Import x, call it z |
| `from x import *` | Import everything |
