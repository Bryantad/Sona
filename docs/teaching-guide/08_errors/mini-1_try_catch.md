# Mini-Lesson 8.1: Try/Catch

## The Problem

When code fails, the program crashes:

```sona
let result = 10 / 0  // CRASH! Can't divide by zero
print("This never runs")
```

**Output:**
```
Error: Division by zero
Program terminated
```

---

## The Solution: Try/Catch

Wrap risky code in `try`, handle errors in `catch`:

```sona
try {
    let result = 10 / 0
    print(result)
} catch e {
    print("Oops! Something went wrong.")
}

print("Program continues normally!")
```

**Output:**
```
Oops! Something went wrong.
Program continues normally!
```

The program doesn't crash—it recovers!

---

## How Try/Catch Works

```
┌─────────────────────────────────────┐
│  try {                              │
│      // Code that might fail        │──→ If OK, skip catch
│  }                                  │
└─────────────────────────────────────┘
          │
          │ If error occurs
          ▼
┌─────────────────────────────────────┐
│  catch e {                          │
│      // Handle the error            │
│  }                                  │
└─────────────────────────────────────┘
          │
          ▼
     Continue program...
```

---

## The Error Object

The `e` in `catch e` contains error information:

```sona
try {
    let x = int("not a number")
} catch e {
    print("Error type: " + e.type)
    print("Message: " + e.message)
}
```

**Output:**
```
Error type: ValueError
Message: invalid literal for int(): 'not a number'
```

---

## Multiple Risky Operations

```sona
try {
    let file = io.read("data.txt")       // Might fail
    let parsed = json.parse(file)         // Might fail
    let value = parsed["missing_key"]     // Might fail
    print(value)
} catch e {
    print("Something failed: " + e.message)
}
```

If ANY line fails, execution jumps to `catch`.

---

## Finally Block

Code in `finally` ALWAYS runs, whether there was an error or not:

```sona
try {
    print("Opening connection...")
    riskyOperation()
    print("Operation successful")
} catch e {
    print("Operation failed: " + e.message)
} finally {
    print("Cleaning up...")  // Always runs!
}
```

**With error:**
```
Opening connection...
Operation failed: Something broke
Cleaning up...
```

**Without error:**
```
Opening connection...
Operation successful
Cleaning up...
```

---

## Common Use Cases

### Reading Files Safely

```sona
import io

func readFileSafely(filename) {
    try {
        return io.read(filename)
    } catch e {
        print("Could not read {filename}: {e.message}")
        return ""
    }
}

let content = readFileSafely("maybe_missing.txt")
```

### Parsing User Input

```sona
func getNumber(text) {
    try {
        return int(text)
    } catch e {
        return null
    }
}

let num = getNumber("42")     // Returns 42
let bad = getNumber("hello")  // Returns null
```

### Safe List Access

```sona
func safeGet(list, index, default = null) {
    try {
        return list[index]
    } catch e {
        return default
    }
}

let items = [1, 2, 3]
print(safeGet(items, 0))       // 1
print(safeGet(items, 99))      // null
print(safeGet(items, 99, -1))  // -1
```

---

## Nested Try/Catch

```sona
try {
    try {
        riskyOperation1()
    } catch e {
        print("Operation 1 failed, trying backup...")
        riskyOperation2()  // This can also fail!
    }
} catch e {
    print("Both operations failed!")
}
```

---

## Don't Catch Everything Blindly

❌ **Bad:** Hiding all errors

```sona
try {
    doSomething()
} catch e {
    // Silently ignore - BAD!
}
```

✅ **Good:** Handle appropriately

```sona
try {
    doSomething()
} catch e {
    print("Warning: {e.message}")
    // Log the error
    // Use a default value
    // Or re-throw if it's critical
}
```

---

## Practice

### Exercise 1
Write code that tries to divide 100 by a variable. If division fails, print "Can't divide" instead of crashing.

### Exercise 2
Create a function `parseJSON(text)` that returns the parsed object or `null` if parsing fails.

### Exercise 3
What will this print?
```sona
try {
    print("A")
    let x = 1 / 0
    print("B")
} catch e {
    print("C")
} finally {
    print("D")
}
print("E")
```

<details>
<summary>Answer</summary>

```
A
C
D
E
```

"B" is skipped because the error occurs before it.

</details>

---

## Summary

| Concept | Purpose |
|---------|---------|
| `try { }` | Wrap code that might fail |
| `catch e { }` | Handle the error |
| `finally { }` | Always runs (cleanup) |
| `e.message` | Error description |
| `e.type` | Error category |

---

→ Next: [mini-2: Error Types](mini-2_error_types.md)
