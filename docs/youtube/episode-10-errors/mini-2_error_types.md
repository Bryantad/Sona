# Mini-Episode 10.2: Error Types ⚠️

> Understanding different kinds of errors

---

## Common Error Types

Different problems cause different errors:

| Error Type | When It Happens |
|------------|-----------------|
| ValueError | Wrong value (can't convert "abc" to number) |
| TypeError | Wrong type (adding string + number) |
| FileNotFoundError | File doesn't exist |
| KeyError | Dictionary key doesn't exist |
| IndexError | List index out of range |
| ZeroDivisionError | Dividing by zero |

---

## ValueError

```sona
try {
    let num = int("hello")  // Can't convert!
} catch error {
    print("Invalid number format")
}
```

**When:** Converting strings to numbers that aren't numbers

---

## TypeError

```sona
try {
    let result = "hello" + 5  // Can't add string + number
} catch error {
    print("Type mismatch!")
}
```

**When:** Mixing incompatible types

---

## FileNotFoundError

```sona
import fs

try {
    let content = read_file("nonexistent.txt")
} catch error {
    print("File not found!")
}
```

**When:** Trying to read/open missing file

---

## KeyError

```sona
let user = {"name": "Alice"}

try {
    print(user["age"])  // Key doesn't exist!
} catch error {
    print("Key not found!")
}
```

**Better approach:**
```sona
// Use .get() with default
let age = user.get("age", "unknown")
```

---

## IndexError

```sona
let numbers = [1, 2, 3]

try {
    print(numbers[10])  // Only 3 items!
} catch error {
    print("Index out of range!")
}
```

**When:** Accessing list index that doesn't exist

---

## Catching Specific Errors

```sona
try {
    let data = read_file("data.txt")
    let value = int(data)
} catch FileNotFoundError {
    print("File is missing!")
} catch ValueError {
    print("File doesn't contain a valid number!")
} catch error {
    print(f"Unknown error: {error}")
}
```

Order matters! Specific errors first, general last.

---

## Pattern: Validate Before Try

Sometimes it's better to **check first**:

```sona
// Instead of try/catch for file
import fs

if fs.exists("file.txt") {
    let content = read_file("file.txt")
} else {
    print("File not found")
}

// Instead of try/catch for dictionary
if "age" in user {
    print(user["age"])
} else {
    print("No age specified")
}
```

---

## When to Use Each Approach

**Use try/catch when:**
- Error is unexpected
- Checking beforehand is expensive
- Multiple things could go wrong

**Use validation when:**
- Easy to check first
- You expect the condition often
- Code is clearer with if/else

---

## Create Your Own Errors

```sona
func withdraw(account, amount) {
    if amount > account["balance"] {
        raise Error("Insufficient funds!")
    }
    account["balance"] = account["balance"] - amount
}

try {
    withdraw(my_account, 1000000)
} catch error {
    print(f"Transaction failed: {error}")
}
```
