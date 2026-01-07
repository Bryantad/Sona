# Mini-Lesson 14.3: Code Quality

## What is "Good Code"?

Good code is:
- ✅ **Readable** - Others can understand it
- ✅ **Maintainable** - Easy to change
- ✅ **Reliable** - Does what it should
- ✅ **Tested** - Verified to work

---

## Naming Things Well

Names should explain PURPOSE, not implementation:

```sona
// ❌ Bad names
let x = users.length()
let temp = getUser(id)
func proc(d) { ... }
let flag = true

// ✅ Good names
let userCount = users.length()
let currentUser = getUser(id)
func processOrder(order) { ... }
let isLoggedIn = true
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Variables | camelCase | `userName` |
| Functions | camelCase | `getUserById()` |
| Classes | PascalCase | `ShoppingCart` |
| Constants | UPPER_SNAKE | `MAX_RETRIES` |
| Boolean | is/has/can | `isValid`, `hasItems` |

---

## Keep Functions Small

Each function should do ONE thing:

```sona
// ❌ Does too much
func processUser(user) {
    // Validate
    if user.name == "" { return false }
    if user.email == "" { return false }
    if !user.email.contains("@") { return false }
    
    // Save
    let data = json.stringify(user)
    io.write("users/" + user.id + ".json", data)
    
    // Send email
    email.send(user.email, "Welcome!", "Hello " + user.name)
    
    // Log
    print("User processed: " + user.name)
}

// ✅ Split into focused functions
func validateUser(user) {
    if user.name == "" { return false }
    if user.email == "" { return false }
    if !user.email.contains("@") { return false }
    return true
}

func saveUser(user) {
    let data = json.stringify(user)
    io.write("users/{user.id}.json", data)
}

func sendWelcomeEmail(user) {
    email.send(user.email, "Welcome!", "Hello {user.name}")
}

func processUser(user) {
    if !validateUser(user) { return false }
    saveUser(user)
    sendWelcomeEmail(user)
    print("User processed: {user.name}")
    return true
}
```

---

## Avoid Deep Nesting

```sona
// ❌ Deeply nested
func process(data) {
    if data != null {
        if data.items != null {
            for item in data.items {
                if item.active {
                    if item.price > 0 {
                        // Finally do something!
                        processItem(item)
                    }
                }
            }
        }
    }
}

// ✅ Early returns
func process(data) {
    if data == null { return }
    if data.items == null { return }
    
    for item in data.items {
        if !item.active { continue }
        if item.price <= 0 { continue }
        
        processItem(item)
    }
}
```

---

## Don't Repeat Yourself (DRY)

```sona
// ❌ Repeated code
func printUserInfo(user) {
    print("Name: " + user.name)
    print("Email: " + user.email)
    print("Role: " + user.role)
}

func printAdminInfo(admin) {
    print("Name: " + admin.name)
    print("Email: " + admin.email)
    print("Role: " + admin.role)
    print("Permissions: " + admin.permissions)
}

// ✅ Reuse
func printPersonInfo(person) {
    print("Name: {person.name}")
    print("Email: {person.email}")
    print("Role: {person.role}")
}

func printUserInfo(user) {
    printPersonInfo(user)
}

func printAdminInfo(admin) {
    printPersonInfo(admin)
    print("Permissions: {admin.permissions}")
}
```

---

## Meaningful Comments

```sona
// ❌ Useless comments
let x = x + 1  // Add 1 to x

// ❌ Obvious comments
// Loop through users
for user in users {
    ...
}

// ✅ Explain WHY, not WHAT
// Retry 3 times because the API sometimes fails on first attempt
for i in range(3) {
    if tryConnect() { break }
}

// ✅ Explain complex logic
// Use binary search for O(log n) performance on sorted data
func findIndex(sortedList, target) {
    ...
}

// ✅ Document edge cases
// Returns null if user not found (don't throw error - may be expected)
func findUser(id) {
    ...
}
```

---

## Error Handling

```sona
// ❌ Silent failures
func getUser(id) {
    try {
        return database.find(id)
    } catch {
        return null  // Caller doesn't know what happened!
    }
}

// ✅ Meaningful error handling
func getUser(id) {
    try {
        let user = database.find(id)
        if user == null {
            return {"success": false, "error": "User not found"}
        }
        return {"success": true, "data": user}
    } catch e {
        log("Database error: " + e.message)
        return {"success": false, "error": "Database unavailable"}
    }
}

// Usage
let result = getUser(123)
if result.success {
    print("Hello, {result.data.name}!")
} else {
    print("Error: {result.error}")
}
```

---

## Code Organization

### Group Related Code

```sona
// ❌ Mixed up
let userName = ""
func saveOrder() { ... }
let orderTotal = 0
func validateUser() { ... }
let userEmail = ""
func processOrder() { ... }

// ✅ Grouped logically
// --- User ---
let userName = ""
let userEmail = ""
func validateUser() { ... }

// --- Order ---
let orderTotal = 0
func processOrder() { ... }
func saveOrder() { ... }
```

### File Organization

```
project/
├── main.sona           # Entry point
├── config.sona         # Configuration
│
├── models/             # Data structures
│   ├── user.sona
│   └── order.sona
│
├── services/           # Business logic
│   ├── auth.sona
│   └── payment.sona
│
├── utils/              # Helpers
│   ├── validation.sona
│   └── formatting.sona
│
└── tests/              # Tests
    ├── test_user.sona
    └── test_order.sona
```

---

## Constants Over Magic Numbers

```sona
// ❌ Magic numbers
if password.length() < 8 { ... }
if retries > 3 { ... }
let tax = price * 0.08

// ✅ Named constants
let MIN_PASSWORD_LENGTH = 8
let MAX_RETRIES = 3
let TAX_RATE = 0.08

if password.length() < MIN_PASSWORD_LENGTH { ... }
if retries > MAX_RETRIES { ... }
let tax = price * TAX_RATE
```

---

## Code Review Checklist

Before finishing code, ask:

### Correctness
- [ ] Does it work for normal cases?
- [ ] Does it handle edge cases?
- [ ] Are errors handled properly?

### Readability
- [ ] Are names clear and descriptive?
- [ ] Is the code well-organized?
- [ ] Are complex parts commented?

### Maintainability
- [ ] Are functions small and focused?
- [ ] Is there repeated code to extract?
- [ ] Is it easy to change later?

### Testing
- [ ] Are there tests for main features?
- [ ] Are edge cases tested?
- [ ] Do all tests pass?

---

## Refactoring Example

Transform messy code into clean code:

```sona
// ❌ Before refactoring
func x(d) {
    let t = 0
    for i in range(d.length()) {
        if d[i].a == true {
            t = t + d[i].p * d[i].q
        }
    }
    if t > 100 {
        t = t * 0.9
    }
    return t
}

// ✅ After refactoring
let DISCOUNT_THRESHOLD = 100
let DISCOUNT_RATE = 0.9

func calculateOrderTotal(items) {
    let subtotal = calculateSubtotal(items)
    return applyDiscount(subtotal)
}

func calculateSubtotal(items) {
    let total = 0
    for item in items {
        if item.active {
            total = total + (item.price * item.quantity)
        }
    }
    return total
}

func applyDiscount(amount) {
    if amount > DISCOUNT_THRESHOLD {
        return amount * DISCOUNT_RATE
    }
    return amount
}
```

---

## Module 14 Complete! 🎉

You've learned:
- ✅ Writing effective unit tests
- ✅ Test-driven development
- ✅ Code quality best practices

→ Next: [Module 15: Advanced Topics](../15_advanced/README.md)
