# Mini-Lesson 13.2: Debugging & Testing

## Bugs Happen to Everyone

Even expert programmers spend time debugging. The key is having a system!

---

## Types of Bugs

| Type | What It Is | Example |
|------|-----------|---------|
| **Syntax Error** | Code won't run | Missing `}` |
| **Runtime Error** | Crashes while running | Divide by zero |
| **Logic Error** | Wrong result | Off-by-one error |

---

## Debugging Strategy: The 4 Steps

### 1. Reproduce
Can you make the bug happen again?

```sona
// Bug: "It crashes sometimes"
// Reproduce: What input causes it?

// Test different inputs
func test_inputs() {
    calculate(10)    // Works
    calculate(0)     // Works
    calculate(-5)    // CRASH! Found it!
}
```

### 2. Isolate
Find the exact line causing the problem:

```sona
// Add print statements to narrow down
func calculate(x) {
    print("Step 1: x = " + x)
    let a = x * 2
    print("Step 2: a = " + a)
    let b = 100 / x      // 💥 Crashes here when x=0
    print("Step 3: b = " + b)
    return a + b
}
```

### 3. Understand
Why is it happening?

```sona
// Division by zero when x is 0
// 100 / 0 = Error!
```

### 4. Fix
Make the change:

```sona
func calculate(x) {
    if x == 0 {
        return 0  // Handle the edge case
    }
    let a = x * 2
    let b = 100 / x
    return a + b
}
```

---

## Print Debugging

The simplest debugging technique:

```sona
func processOrder(order) {
    print("DEBUG: Starting processOrder")
    print("DEBUG: order = " + order)
    
    let total = 0
    for item in order.items {
        print("DEBUG: Processing item: " + item)
        total = total + item.price
        print("DEBUG: Running total: " + total)
    }
    
    print("DEBUG: Final total: " + total)
    return total
}
```

### Make It Toggleable

```sona
let DEBUG = true

func debug(message) {
    if DEBUG {
        print("[DEBUG] " + message)
    }
}

func processOrder(order) {
    debug("Starting processOrder")
    debug("order = " + str(order))
    // ... rest of code
}

// To disable: just change DEBUG = false
```

---

## Common Bugs and Fixes

### 1. Off-by-One Error

```sona
// Bug: Missing the last item
let items = ["a", "b", "c"]
for i in range(items.length() - 1) {  // ❌ Wrong!
    print(items[i])
}
// Prints: a, b (missing c!)

// Fix:
for i in range(items.length()) {  // ✅ Correct
    print(items[i])
}
```

### 2. Wrong Comparison

```sona
// Bug: Assignment instead of comparison
if x = 5 {  // ❌ This assigns 5 to x!
    print("x is 5")
}

// Fix:
if x == 5 {  // ✅ This compares
    print("x is 5")
}
```

### 3. String vs Number

```sona
// Bug: Comparing different types
let input = "5"
if input == 5 {  // ❌ "5" is not equal to 5
    print("It's five!")
}

// Fix:
if int(input) == 5 {  // ✅ Convert first
    print("It's five!")
}
```

### 4. Not Returning a Value

```sona
// Bug: Forgetting return
func double(x) {
    let result = x * 2
    // Oops! No return statement
}
let y = double(5)  // y is null!

// Fix:
func double(x) {
    let result = x * 2
    return result  // ✅ Don't forget!
}
```

### 5. Modifying While Iterating

```sona
// Bug: Removing from list while looping
let numbers = [1, 2, 3, 4, 5]
for n in numbers {
    if n % 2 == 0 {
        numbers.remove(n)  // ❌ Causes problems!
    }
}

// Fix: Build a new list
let numbers = [1, 2, 3, 4, 5]
let odds = numbers.filter(func(n) { return n % 2 != 0 })
```

---

## Writing Tests

Tests check that your code works correctly:

```sona
// The function to test
func add(a, b) {
    return a + b
}

// Tests!
func testAdd() {
    // Test normal cases
    assert add(2, 3) == 5, "2 + 3 should be 5"
    assert add(0, 0) == 0, "0 + 0 should be 0"
    assert add(-1, 1) == 0, "-1 + 1 should be 0"
    
    // Test edge cases
    assert add(999999, 1) == 1000000, "Large numbers"
    
    print("✅ All tests passed!")
}

testAdd()
```

### Testing a Class

```sona
class Counter {
    func init(start = 0) {
        self.value = start
    }
    
    func increment() {
        self.value = self.value + 1
    }
    
    func decrement() {
        self.value = self.value - 1
    }
    
    func reset() {
        self.value = 0
    }
}

func testCounter() {
    // Test init
    let c = Counter()
    assert c.value == 0, "Should start at 0"
    
    let c2 = Counter(10)
    assert c2.value == 10, "Should start at 10"
    
    // Test increment
    c.increment()
    assert c.value == 1, "Should be 1 after increment"
    
    // Test decrement
    c.decrement()
    assert c.value == 0, "Should be 0 after decrement"
    
    // Test reset
    c.value = 100
    c.reset()
    assert c.value == 0, "Should be 0 after reset"
    
    print("✅ Counter tests passed!")
}

testCounter()
```

---

## Test-Driven Development (TDD)

Write tests FIRST, then code:

```sona
// Step 1: Write the test
func testIsValidEmail() {
    assert isValidEmail("user@example.com") == true
    assert isValidEmail("invalid") == false
    assert isValidEmail("") == false
    assert isValidEmail("a@b.c") == true
    print("✅ Email validation tests passed!")
}

// Step 2: Run test (it fails - function doesn't exist yet!)

// Step 3: Write code to make test pass
func isValidEmail(email) {
    if email.length() < 5 {
        return false
    }
    if "@" not in email {
        return false
    }
    if "." not in email {
        return false
    }
    return true
}

// Step 4: Run test again (it passes!)
testIsValidEmail()
```

---

## Organizing Tests

```sona
// tests/test_math.sona

import "../src/math" as math

func testAdd() {
    assert math.add(1, 2) == 3
    assert math.add(-1, -1) == -2
    print("✅ add() tests passed")
}

func testMultiply() {
    assert math.multiply(3, 4) == 12
    assert math.multiply(0, 100) == 0
    print("✅ multiply() tests passed")
}

func testDivide() {
    assert math.divide(10, 2) == 5
    assert math.divide(7, 2) == 3.5
    // Test error case
    let result = math.divide(1, 0)
    assert result == null, "Division by zero should return null"
    print("✅ divide() tests passed")
}

func runAllTests() {
    print("Running math tests...")
    testAdd()
    testMultiply()
    testDivide()
    print("\n🎉 All math tests passed!")
}

runAllTests()
```

---

## Practice

### Exercise 1
Debug this function (it has 3 bugs):

```sona
func findMax(numbers) {
    let max = 0
    for i in range(numbers.length() - 1) {
        if numbers[i] = max {
            max = numbers[i]
        }
    }
    return max
}
```

### Exercise 2
Write tests for a `Calculator` class with `add`, `subtract`, `multiply`, and `divide` methods.

### Exercise 3
Find and fix the bug:

```sona
func reverseString(s) {
    let result = ""
    for i in range(s.length()) {
        result = result + s[s.length() - i]
    }
    return result
}
```

---

→ Next: [mini-3: Example Projects](mini-3_examples.md)
