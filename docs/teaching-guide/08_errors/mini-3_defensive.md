# Mini-Lesson 8.3: Defensive Coding

## What is Defensive Coding?

**Defensive coding** means writing code that anticipates and prevents errors before they happen. Instead of waiting for things to break, you check first.

Think of it like:
- Looking both ways before crossing the street
- Checking if the stove is off before leaving
- Verifying your keys are in your pocket before locking the door

---

## Check Before You Act

### ❌ Optimistic (Risky)
```sona
let result = data[index]  // Might crash if index is invalid
```

### ✅ Defensive (Safe)
```sona
if index >= 0 and index < data.length() {
    let result = data[index]
} else {
    print("Index out of range")
}
```

---

## Common Defensive Patterns

### Pattern 1: Guard Clauses

Check bad conditions first and return early:

```sona
func processUser(user) {
    // Guard clauses - check problems first
    if user == null {
        return "Error: No user provided"
    }
    
    if user.name.is_empty() {
        return "Error: Name is required"
    }
    
    if user.age < 0 {
        return "Error: Invalid age"
    }
    
    // Main logic - only runs if all checks pass
    return "Welcome, " + user.name
}
```

---

### Pattern 2: Default Values

Provide fallbacks for missing data:

```sona
func greet(name = "Guest") {
    print("Hello, " + name)
}

greet("Alex")  // "Hello, Alex"
greet()        // "Hello, Guest"
```

```sona
func getConfig(key, default = null) {
    if key in config {
        return config[key]
    }
    return default
}

let theme = getConfig("theme", "light")
```

---

### Pattern 3: Type Checking

Verify data types before using:

```sona
func add(a, b) {
    if typeof(a) != "number" or typeof(b) != "number" {
        throw TypeError("Both arguments must be numbers")
    }
    return a + b
}
```

---

### Pattern 4: Range Validation

Ensure values are within acceptable bounds:

```sona
func setVolume(level) {
    // Clamp to valid range
    if level < 0 {
        level = 0
    }
    if level > 100 {
        level = 100
    }
    
    speaker.volume = level
}

setVolume(150)  // Sets to 100, not 150
setVolume(-10)  // Sets to 0, not -10
```

---

### Pattern 5: Null Checking

Handle missing values:

```sona
func displayName(user) {
    if user == null {
        return "Unknown"
    }
    
    if user.name == null or user.name.is_empty() {
        return "Anonymous"
    }
    
    return user.name
}
```

---

## Safe Access Helpers

Create helper functions for common risky operations:

### Safe Dictionary Access
```sona
func safeGet(dict, key, default = null) {
    if key in dict {
        return dict[key]
    }
    return default
}

let user = {"name": "Alex"}
let age = safeGet(user, "age", 0)  // Returns 0, not error
```

### Safe List Access
```sona
func safeIndex(list, index, default = null) {
    if index >= 0 and index < list.length() {
        return list[index]
    }
    return default
}

let items = [1, 2, 3]
let item = safeIndex(items, 99, -1)  // Returns -1
```

### Safe Division
```sona
func safeDivide(a, b, default = 0) {
    if b == 0 {
        return default
    }
    return a / b
}

let result = safeDivide(10, 0)  // Returns 0, not error
```

---

## Validating Input

Always validate user input:

```sona
func createAccount(email, password) {
    let errors = []
    
    // Email validation
    if email.is_empty() {
        errors.push("Email is required")
    } else if not email.contains("@") {
        errors.push("Invalid email format")
    }
    
    // Password validation
    if password.length() < 8 {
        errors.push("Password must be at least 8 characters")
    }
    
    if password.lower() == password {
        errors.push("Password must contain uppercase letters")
    }
    
    // Return errors or proceed
    if errors.length() > 0 {
        return {"success": false, "errors": errors}
    }
    
    // Create the account...
    return {"success": true}
}
```

---

## Defensive vs Try/Catch

| Situation | Use Defensive | Use Try/Catch |
|-----------|--------------|---------------|
| Can check beforehand | ✅ | |
| Failure is predictable | ✅ | |
| External resources (files, network) | | ✅ |
| Multiple things can fail | | ✅ |
| Need specific error info | | ✅ |

**Best:** Combine both approaches!

```sona
func loadUserData(userId) {
    // Defensive: Check input
    if userId == null or userId.is_empty() {
        return null
    }
    
    // Try/catch: Handle file operations
    try {
        let filename = "users/{userId}.json"
        if io.exists(filename) {
            return json.parse(io.read(filename))
        }
        return null
    } catch e {
        print("Error loading user data: " + e.message)
        return null
    }
}
```

---

## Code Review Checklist

When writing code, ask yourself:

- [ ] What if this value is null?
- [ ] What if this list is empty?
- [ ] What if this index is out of bounds?
- [ ] What if this key doesn't exist?
- [ ] What if the user enters unexpected input?
- [ ] What if the file doesn't exist?
- [ ] What if the network is unavailable?

---

## Practice

### Exercise 1
Make this code defensive:
```sona
func getFirst(list) {
    return list[0]
}
```

### Exercise 2
Write a function `calculateAverage(numbers)` that handles:
- Empty list
- Null input
- Non-numeric values

### Exercise 3
Create a validation function for a registration form that checks:
- Username: 3-20 characters, not empty
- Email: contains @ and .
- Age: between 13 and 120

<details>
<summary>Exercise 1 Answer</summary>

```sona
func getFirst(list, default = null) {
    if list == null or list.length() == 0 {
        return default
    }
    return list[0]
}
```

</details>

---

## Summary

**Defensive Coding Principles:**

1. **Check inputs** - Validate before using
2. **Use defaults** - Provide fallback values
3. **Guard clauses** - Return early on bad conditions
4. **Safe helpers** - Create reusable safe-access functions
5. **Validate ranges** - Ensure values are in bounds
6. **Combine approaches** - Use both defensive checks AND try/catch

---

## Module 08 Complete! 🎉

You've learned:
- ✅ Try/catch for handling errors
- ✅ Different error types
- ✅ Defensive coding techniques

→ Next: [Module 09: Modules & Imports](../09_modules/README.md)
