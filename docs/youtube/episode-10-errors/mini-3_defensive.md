# Mini-Episode 10.3: Defensive Coding 🛡️

> Prevent errors before they happen

---

## What Is Defensive Coding?

Writing code that **anticipates problems** and handles them gracefully.

Like wearing a seatbelt - you hope you don't need it, but you're glad it's there!

---

## Rule 1: Validate Input Early

```sona
func create_user(name, age) {
    // Check inputs FIRST
    if name == "" or name == null {
        print("Error: Name is required")
        return null
    }
    
    if age < 0 or age > 150 {
        print("Error: Invalid age")
        return null
    }
    
    // Now safe to proceed
    return {"name": name, "age": age}
}
```

---

## Rule 2: Use Default Values

```sona
func greet(name = "Friend") {
    print(f"Hello, {name}!")
}

greet()          // Hello, Friend!
greet("Alice")   // Hello, Alice!

// For dictionaries:
let config = settings.get("theme", "light")
```

---

## Rule 3: Check Before Using

```sona
// Check list has items
if len(items) > 0 {
    let first = items[0]
}

// Check key exists
if "email" in user {
    send_email(user["email"])
}

// Check file exists
import fs
if fs.exists(filename) {
    let content = read_file(filename)
}
```

---

## Rule 4: Guard Clauses

Exit early when something is wrong:

```sona
func process_order(order) {
    // Guard clauses - exit early if problems
    if order == null {
        return "No order provided"
    }
    
    if len(order["items"]) == 0 {
        return "Order is empty"
    }
    
    if order["total"] <= 0 {
        return "Invalid total"
    }
    
    // Main logic (only reached if everything OK)
    // ... process the order ...
    return "Order processed!"
}
```

---

## Rule 5: Provide Meaningful Errors

```sona
func divide(a, b) {
    if b == 0 {
        raise Error("Cannot divide by zero. Please provide a non-zero divisor.")
    }
    return a / b
}

// Clear error message helps debugging!
```

---

## Defensive Pattern: Safe Get

```sona
func safe_get(list, index, default = null) {
    if index >= 0 and index < len(list) {
        return list[index]
    }
    return default
}

let colors = ["red", "blue"]
print(safe_get(colors, 0))    // red
print(safe_get(colors, 10))   // null
print(safe_get(colors, 10, "unknown"))  // unknown
```

---

## Defensive Pattern: Safe Execute

```sona
func safe_execute(func_to_run, default = null) {
    try {
        return func_to_run()
    } catch error {
        print(f"Operation failed: {error}")
        return default
    }
}

// Use it
let result = safe_execute(
    lambda: risky_operation(),
    "fallback value"
)
```

---

## Complete Example: Robust Calculator

```sona
func calculator(operation, a, b) {
    // Validate operation
    let valid_ops = ["+", "-", "*", "/"]
    if operation not in valid_ops {
        return {"success": false, "error": "Invalid operation"}
    }
    
    // Validate numbers
    if not is_number(a) or not is_number(b) {
        return {"success": false, "error": "Inputs must be numbers"}
    }
    
    // Special case for division
    if operation == "/" and b == 0 {
        return {"success": false, "error": "Cannot divide by zero"}
    }
    
    // Perform calculation
    let result = match operation {
        "+" => a + b,
        "-" => a - b,
        "*" => a * b,
        "/" => a / b
    }
    
    return {"success": true, "result": result}
}
```

---

## Checklist ✅

Before your function does its main job:

- [ ] Are all required parameters provided?
- [ ] Are parameters the right type?
- [ ] Are values in valid range?
- [ ] Do files/resources exist?
- [ ] Is the data not empty?
