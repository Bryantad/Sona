# Mini-Lesson 14.2: Test-Driven Development (TDD)

## What is TDD?

**TDD** = Write tests BEFORE writing code

The cycle:
1. 🔴 **Red** - Write a failing test
2. 🟢 **Green** - Write minimum code to pass
3. 🔵 **Refactor** - Improve the code

---

## Why TDD?

| Without TDD | With TDD |
|-------------|----------|
| Write code, then test | Write test, then code |
| "Does it work?" | "What should it do?" |
| May forget edge cases | Forces you to think |
| Tests optional | Tests required |

---

## TDD Example: Building a Password Validator

### Step 1: Write the First Test 🔴

```sona
// What should password validation do?
// - At least 8 characters
// - Contains uppercase
// - Contains number

func test_password_minimum_length() {
    assert validatePassword("short") == false, "Too short"
    assert validatePassword("longenough") == true, "8+ chars OK"
}

// Run test - it fails! (function doesn't exist)
test_password_minimum_length()
```

### Step 2: Make It Pass 🟢

```sona
// Write MINIMUM code to pass
func validatePassword(password) {
    return password.length() >= 8
}

// Run test - it passes!
test_password_minimum_length()
print("✅ Test passed!")
```

### Step 3: Add Next Test 🔴

```sona
func test_password_uppercase() {
    assert validatePassword("alllower1") == false, "Needs uppercase"
    assert validatePassword("HasUpper1") == true, "Has uppercase"
}

// Run test - it fails!
```

### Step 4: Make It Pass 🟢

```sona
func validatePassword(password) {
    if password.length() < 8 {
        return false
    }
    
    // Check for uppercase
    let hasUpper = false
    for char in password {
        if char >= "A" and char <= "Z" {
            hasUpper = true
            break
        }
    }
    if !hasUpper {
        return false
    }
    
    return true
}

// Run tests - both pass!
```

### Step 5: Add Next Test 🔴

```sona
func test_password_number() {
    assert validatePassword("NoNumber!") == false, "Needs number"
    assert validatePassword("HasNumber1") == true, "Has number"
}

// Run test - it fails!
```

### Step 6: Make It Pass 🟢

```sona
func validatePassword(password) {
    if password.length() < 8 {
        return false
    }
    
    let hasUpper = false
    let hasNumber = false
    
    for char in password {
        if char >= "A" and char <= "Z" {
            hasUpper = true
        }
        if char >= "0" and char <= "9" {
            hasNumber = true
        }
    }
    
    return hasUpper and hasNumber
}

// All tests pass!
```

### Step 7: Refactor 🔵

```sona
// Clean up the code
func hasUppercase(text) {
    for char in text {
        if char >= "A" and char <= "Z" {
            return true
        }
    }
    return false
}

func hasNumber(text) {
    for char in text {
        if char >= "0" and char <= "9" {
            return true
        }
    }
    return false
}

func validatePassword(password) {
    if password.length() < 8 {
        return false
    }
    return hasUppercase(password) and hasNumber(password)
}

// Run all tests - still pass!
```

---

## Complete TDD Walkthrough: Shopping Cart

Let's build a shopping cart using TDD:

### Test 1: Create Empty Cart

```sona
func test_empty_cart() {
    let cart = ShoppingCart()
    assert cart.itemCount() == 0, "New cart should be empty"
    assert cart.total() == 0, "Empty cart total is 0"
}
```

Make it pass:

```sona
class ShoppingCart {
    func init() {
        self.items = []
    }
    
    func itemCount() {
        return self.items.length()
    }
    
    func total() {
        return 0
    }
}
```

### Test 2: Add Item

```sona
func test_add_item() {
    let cart = ShoppingCart()
    cart.addItem("Apple", 1.50)
    
    assert cart.itemCount() == 1, "Should have 1 item"
    assert cart.total() == 1.50, "Total should be 1.50"
}
```

Make it pass:

```sona
class ShoppingCart {
    func init() {
        self.items = []
    }
    
    func itemCount() {
        return self.items.length()
    }
    
    func total() {
        let sum = 0
        for item in self.items {
            sum = sum + item.price
        }
        return sum
    }
    
    func addItem(name, price) {
        self.items.push({"name": name, "price": price, "qty": 1})
    }
}
```

### Test 3: Add Multiple of Same Item

```sona
func test_add_quantity() {
    let cart = ShoppingCart()
    cart.addItem("Apple", 1.50, 3)  // 3 apples
    
    assert cart.itemCount() == 1, "Still 1 unique item"
    assert cart.total() == 4.50, "3 × 1.50 = 4.50"
}
```

Make it pass:

```sona
func addItem(name, price, qty = 1) {
    self.items.push({"name": name, "price": price, "qty": qty})
}

func total() {
    let sum = 0
    for item in self.items {
        sum = sum + (item.price * item.qty)
    }
    return sum
}
```

### Test 4: Remove Item

```sona
func test_remove_item() {
    let cart = ShoppingCart()
    cart.addItem("Apple", 1.50)
    cart.addItem("Bread", 2.00)
    
    cart.removeItem("Apple")
    
    assert cart.itemCount() == 1, "Should have 1 item"
    assert cart.total() == 2.00, "Only bread remains"
}
```

Make it pass:

```sona
func removeItem(name) {
    for i, item in enumerate(self.items) {
        if item.name == name {
            self.items.remove(i)
            return true
        }
    }
    return false
}
```

### Test 5: Clear Cart

```sona
func test_clear_cart() {
    let cart = ShoppingCart()
    cart.addItem("Apple", 1.50)
    cart.addItem("Bread", 2.00)
    
    cart.clear()
    
    assert cart.itemCount() == 0, "Cart should be empty"
    assert cart.total() == 0, "Total should be 0"
}
```

Make it pass:

```sona
func clear() {
    self.items = []
}
```

### Final Shopping Cart

```sona
class ShoppingCart {
    func init() {
        self.items = []
    }
    
    func itemCount() {
        return self.items.length()
    }
    
    func total() {
        let sum = 0
        for item in self.items {
            sum = sum + (item.price * item.qty)
        }
        return sum
    }
    
    func addItem(name, price, qty = 1) {
        // Check if item exists
        for item in self.items {
            if item.name == name {
                item.qty = item.qty + qty
                return
            }
        }
        self.items.push({"name": name, "price": price, "qty": qty})
    }
    
    func removeItem(name) {
        for i, item in enumerate(self.items) {
            if item.name == name {
                self.items.remove(i)
                return true
            }
        }
        return false
    }
    
    func clear() {
        self.items = []
    }
}

// All tests
func runCartTests() {
    test_empty_cart()
    test_add_item()
    test_add_quantity()
    test_remove_item()
    test_clear_cart()
    print("✅ All ShoppingCart tests passed!")
}

runCartTests()
```

---

## TDD Tips

### Start Simple
❌ Don't start with: "Test the entire checkout flow"  
✅ Start with: "Test creating an empty cart"

### One Thing at a Time
Each test should check ONE thing:

```sona
// ❌ Too many things
func test_cart() {
    let cart = ShoppingCart()
    cart.addItem("A", 1)
    cart.addItem("B", 2)
    cart.removeItem("A")
    assert cart.total() == 2
    cart.clear()
    assert cart.isEmpty()
}

// ✅ One thing each
func test_add_item() { ... }
func test_remove_item() { ... }
func test_clear() { ... }
```

### Test Behavior, Not Implementation
```sona
// ❌ Testing implementation
assert cart.items[0].name == "Apple"

// ✅ Testing behavior
assert cart.contains("Apple")
assert cart.total() == 1.50
```

---

## Practice

### Exercise 1
Use TDD to build a `Stack` class with:
- `push(item)` - add to top
- `pop()` - remove and return top
- `peek()` - see top without removing
- `isEmpty()` - check if empty

Write tests first!

### Exercise 2
Use TDD to build a `StringCalculator`:
- `add("1,2,3")` returns 6
- `add("")` returns 0
- `add("1")` returns 1

### Exercise 3
Use TDD to build a `FizzBuzz` function:
- Returns "Fizz" for multiples of 3
- Returns "Buzz" for multiples of 5
- Returns "FizzBuzz" for multiples of both
- Returns the number otherwise

---

→ Next: [mini-3: Code Quality](mini-3_quality.md)
