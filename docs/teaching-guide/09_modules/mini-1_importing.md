# Mini-Lesson 9.1: Importing Modules

## What is Importing?

**Importing** loads code from another file so you can use it. Think of it like borrowing tools from a toolbox.

---

## Basic Import

```sona
import math

print(math.sqrt(16))   // 4
print(math.pi)         // 3.14159...
print(math.pow(2, 3))  // 8
```

The module name (`math`) becomes a prefix for all its functions.

---

## Import Specific Items

When you only need certain things:

```sona
from math import sqrt, pi

print(sqrt(16))  // 4 (no "math." needed)
print(pi)        // 3.14159...
```

---

## Import with Alias

Give a module a shorter name:

```sona
import math as m

print(m.sqrt(16))
print(m.pi)
```

Useful for long module names:
```sona
import string_utilities as su
```

---

## Import Everything (Not Recommended)

```sona
from math import *

print(sqrt(16))  // Works but risky!
```

**Why it's risky:** You don't know what names you're importing. They might conflict with your own variables.

---

## Standard Library Modules

Sona comes with many useful modules:

### Math Module
```sona
import math

print(math.sqrt(25))     // 5
print(math.pow(2, 8))    // 256
print(math.abs(-10))     // 10
print(math.round(3.7))   // 4
print(math.floor(3.9))   // 3
print(math.ceil(3.1))    // 4
print(math.pi)           // 3.14159...
print(math.e)            // 2.71828...
```

### Random Module
```sona
import random

print(random.random())           // 0.0 to 1.0
print(random.randint(1, 10))     // Random 1-10
print(random.choice([1, 2, 3]))  // Random item
random.shuffle(myList)           // Shuffles in place
```

### Time Module
```sona
import time

print(time.now())         // Current datetime
time.sleep(1)             // Wait 1 second
print(time.timestamp())   // Unix timestamp
```

### IO Module
```sona
import io

let content = io.read("file.txt")
io.write("output.txt", "Hello!")
let exists = io.exists("file.txt")
```

### String Module
```sona
import string

print(string.upper("hello"))        // "HELLO"
print(string.reverse("hello"))      // "olleh"
print(string.pad_left("42", 5))     // "   42"
```

### JSON Module
```sona
import json

let data = json.parse('{"name": "Alex"}')
print(data.name)  // "Alex"

let text = json.stringify({"score": 100})
print(text)  // '{"score": 100}'
```

### Path Module
```sona
import path

let full = path.join("data", "users", "file.txt")
let name = path.basename("data/file.txt")  // "file.txt"
let dir = path.dirname("data/file.txt")    // "data"
let ext = path.extension("photo.jpg")      // ".jpg"
```

---

## Where to Put Imports

**Always at the top of your file:**

```sona
// Good - imports at the top
import math
import io
import random

func main() {
    let r = random.random()
    // ...
}
```

```sona
// Bad - imports scattered around
func calculate() {
    import math  // Don't do this!
    return math.sqrt(x)
}
```

---

## Checking What's Available

List functions in a module:

```sona
import math

print(dir(math))
// ["sqrt", "pow", "pi", "e", "abs", "round", ...]
```

Get help on a function:

```sona
help(math.sqrt)
// "Returns the square root of x"
```

---

## Practice

### Exercise 1
Import the `math` module and calculate:
- Square root of 144
- 2 raised to the power of 10
- Pi times 5

### Exercise 2
Use the `random` module to:
- Generate a random number between 1 and 100
- Pick a random color from `["red", "blue", "green"]`

### Exercise 3
What's wrong with this code?
```sona
print(sqrt(16))
```

<details>
<summary>Answer</summary>

The `math` module isn't imported. Fix:
```sona
import math
print(math.sqrt(16))
```
or
```sona
from math import sqrt
print(sqrt(16))
```

</details>

---

## Summary

| Syntax | Effect |
|--------|--------|
| `import math` | Load module, use as `math.func()` |
| `from math import sqrt` | Import `sqrt` directly |
| `import math as m` | Load module with alias `m` |
| `from math import *` | Import all (not recommended) |

---

→ Next: [mini-2: Creating Modules](mini-2_creating.md)
