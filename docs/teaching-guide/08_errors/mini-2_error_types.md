# Mini-Lesson 8.2: Error Types

## Categories of Errors

Not all errors are the same. Understanding types helps you handle them correctly.

---

## Syntax Errors

**What:** Code that doesn't follow the rules  
**When:** Before the program runs  
**Fix:** Correct the code

```sona
// Missing closing brace
if true {
    print("Hello")
// ERROR: Expected '}'

// Missing quotes
print(Hello)
// ERROR: 'Hello' is not defined
```

**You can't catch syntax errors** - they prevent the program from starting.

---

## Runtime Errors

**What:** Errors that happen while running  
**When:** During execution  
**Fix:** Use try/catch

### Common Runtime Errors

#### Division by Zero
```sona
let x = 10 / 0  // ZeroDivisionError
```

#### Invalid Index
```sona
let list = [1, 2, 3]
let item = list[99]  // IndexError: list index out of range
```

#### Key Not Found
```sona
let dict = {"a": 1}
let value = dict["z"]  // KeyError: 'z'
```

#### Type Mismatch
```sona
let result = "hello" + 5  // TypeError: can't add string and int
```

#### File Not Found
```sona
import io
let content = io.read("nonexistent.txt")  // FileNotFoundError
```

---

## Catching Specific Errors

You can catch different errors differently:

```sona
try {
    riskyOperation()
} catch TypeError as e {
    print("Wrong type: " + e.message)
} catch ValueError as e {
    print("Bad value: " + e.message)
} catch e {
    print("Some other error: " + e.message)
}
```

The most specific catch runs. The generic `catch e` is a fallback.

---

## Error Type Reference

| Error Type | Cause | Example |
|------------|-------|---------|
| `ZeroDivisionError` | Dividing by zero | `10 / 0` |
| `IndexError` | Invalid list index | `list[999]` |
| `KeyError` | Missing dictionary key | `dict["missing"]` |
| `TypeError` | Wrong type for operation | `"a" + 1` |
| `ValueError` | Right type, wrong value | `int("abc")` |
| `FileNotFoundError` | File doesn't exist | `io.read("x.txt")` |
| `PermissionError` | No access rights | Reading protected file |
| `AttributeError` | Missing property/method | `x.nonexistent()` |

---

## Creating Your Own Errors

Use `throw` to signal an error:

```sona
func setAge(age) {
    if age < 0 {
        throw ValueError("Age cannot be negative")
    }
    if age > 150 {
        throw ValueError("Age seems unrealistic")
    }
    return age
}

try {
    setAge(-5)
} catch ValueError as e {
    print("Invalid age: " + e.message)
}
```

---

## Custom Error Types

```sona
class ValidationError extends Error {
    func init(field, message) {
        self.field = field
        self.message = message
    }
}

func validateUser(user) {
    if user.name.is_empty() {
        throw ValidationError("name", "Name is required")
    }
    if user.age < 0 {
        throw ValidationError("age", "Age must be positive")
    }
}

try {
    validateUser({"name": "", "age": 25})
} catch ValidationError as e {
    print("Validation failed for {e.field}: {e.message}")
}
```

---

## When to Use Which Approach

### Catch Specific Errors When:
- You can handle different errors differently
- You need to take specific recovery actions
- You want to re-throw some errors

### Catch All Errors When:
- Any failure should be handled the same way
- You're at the top level of your program
- You want to log then continue

---

## Error Handling Patterns

### Pattern 1: Try Alternative
```sona
func loadConfig() {
    try {
        return io.read("config.json")
    } catch FileNotFoundError {
        return io.read("default_config.json")
    }
}
```

### Pattern 2: Convert Error to Value
```sona
func parseNumber(text) {
    try {
        return int(text)
    } catch ValueError {
        return 0
    }
}
```

### Pattern 3: Log and Re-throw
```sona
func processData(data) {
    try {
        return transform(data)
    } catch e {
        log("Error processing data: " + e.message)
        throw e  // Let caller handle it
    }
}
```

### Pattern 4: Collect All Errors
```sona
func validateAll(items) {
    let errors = []
    
    for item in items {
        try {
            validate(item)
        } catch e {
            errors.push(e.message)
        }
    }
    
    return errors
}
```

---

## Practice

### Exercise 1
Write code that catches `ZeroDivisionError` specifically and prints "Cannot divide by zero".

### Exercise 2
Create a function that throws a custom error if a password is less than 8 characters.

### Exercise 3
Handle these different errors with different messages:
- IndexError → "Invalid position"
- KeyError → "Missing key"
- Any other → "Unknown error"

<details>
<summary>Exercise 3 Answer</summary>

```sona
try {
    riskyOperation()
} catch IndexError as e {
    print("Invalid position")
} catch KeyError as e {
    print("Missing key")
} catch e {
    print("Unknown error")
}
```

</details>

---

## Summary

| Error Type | Common Cause | Example |
|------------|--------------|---------|
| Syntax | Bad code structure | Missing `}` |
| Runtime | Problems during execution | Division by zero |
| Logical | Wrong results | Using `<` instead of `>` |

**Key Points:**
- Different errors need different handling
- Use specific catches when behavior should differ
- Create custom errors for domain-specific problems
- `throw` lets you signal errors in your own code

---

→ Next: [mini-3: Defensive Coding](mini-3_defensive.md)
