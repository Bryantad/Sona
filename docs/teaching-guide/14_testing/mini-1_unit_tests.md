# Mini-Lesson 14.1: Unit Testing

## What is Unit Testing?

**Unit testing** = Testing individual pieces of code

Think of it like checking each ingredient before cooking:
- Is the flour fresh? ✓
- Are the eggs good? ✓
- Is the milk not expired? ✓

---

## Your First Test

```sona
// The function to test
func add(a, b) {
    return a + b
}

// The test
func test_add() {
    let result = add(2, 3)
    assert result == 5, "Expected 5, got {result}"
}

// Run it
test_add()
print("✅ Test passed!")
```

---

## The Assert Statement

`assert` checks if something is true:

```sona
// If condition is true: nothing happens
assert 1 + 1 == 2

// If condition is false: error with message
assert 1 + 1 == 3, "Math is broken!"
// Error: Math is broken!
```

### Common Assertions

```sona
// Equality
assert value == expected, "Should equal"

// Not equal
assert value != wrong, "Should not equal"

// Boolean
assert isValid, "Should be true"
assert !isEmpty, "Should be false"

// Comparisons
assert count > 0, "Should be positive"
assert length <= max, "Should not exceed max"

// Contains
assert item in list, "Should be in list"
assert "hello" in text, "Should contain hello"

// Type checking
assert type(value) == "string", "Should be string"

// Null checks
assert value != null, "Should not be null"
```

---

## Testing Structure: AAA Pattern

**A**rrange, **A**ct, **A**ssert:

```sona
func test_shopping_cart_total() {
    // ARRANGE - Set up what you need
    let cart = ShoppingCart()
    cart.addItem("Apple", 1.50)
    cart.addItem("Bread", 2.00)
    
    // ACT - Do the thing you're testing
    let total = cart.getTotal()
    
    // ASSERT - Check the result
    assert total == 3.50, "Total should be $3.50"
}
```

---

## Testing Different Scenarios

Test normal cases AND edge cases:

```sona
func divide(a, b) {
    if b == 0 {
        return null
    }
    return a / b
}

// Test normal cases
func test_divide_normal() {
    assert divide(10, 2) == 5, "10/2 = 5"
    assert divide(9, 3) == 3, "9/3 = 3"
    assert divide(7, 2) == 3.5, "7/2 = 3.5"
}

// Test edge cases
func test_divide_edge_cases() {
    // Division by zero
    assert divide(5, 0) == null, "Divide by zero returns null"
    
    // Zero dividend
    assert divide(0, 5) == 0, "0/5 = 0"
    
    // Negative numbers
    assert divide(-6, 2) == -3, "-6/2 = -3"
    assert divide(6, -2) == -3, "6/-2 = -3"
    assert divide(-6, -2) == 3, "-6/-2 = 3"
}

// Test with decimals
func test_divide_decimals() {
    assert divide(1, 3) == 0.333333, "1/3 ≈ 0.333"  // May need tolerance!
}
```

---

## Testing with Tolerance

For floating-point numbers:

```sona
func approximately(actual, expected, tolerance = 0.0001) {
    return abs(actual - expected) < tolerance
}

func test_division_precision() {
    let result = divide(1, 3)
    assert approximately(result, 0.3333, 0.001), "1/3 ≈ 0.3333"
}

func test_sqrt() {
    let result = sqrt(2)
    assert approximately(result, 1.4142, 0.0001), "√2 ≈ 1.4142"
}
```

---

## Organizing Tests

### By Feature

```sona
// tests/test_user.sona

func test_user_creation() {
    let user = User("Alice", "alice@test.com")
    assert user.name == "Alice"
    assert user.email == "alice@test.com"
}

func test_user_validation() {
    let validUser = User("Bob", "bob@test.com")
    assert validUser.isValid()
    
    let invalidUser = User("", "")
    assert !invalidUser.isValid()
}

func test_user_full_name() {
    let user = User("Alice", "alice@test.com")
    user.lastName = "Smith"
    assert user.fullName() == "Alice Smith"
}

func runUserTests() {
    print("Running User tests...")
    test_user_creation()
    test_user_validation()
    test_user_full_name()
    print("✅ All User tests passed!")
}
```

### Test Runner

```sona
// tests/run_all.sona

import "test_user" as userTests
import "test_cart" as cartTests
import "test_order" as orderTests

func runAllTests() {
    print("=" * 50)
    print("  🧪 RUNNING ALL TESTS")
    print("=" * 50)
    
    let passed = 0
    let failed = 0
    
    try {
        userTests.runUserTests()
        passed = passed + 1
    } catch e {
        print("❌ User tests failed: " + e.message)
        failed = failed + 1
    }
    
    try {
        cartTests.runCartTests()
        passed = passed + 1
    } catch e {
        print("❌ Cart tests failed: " + e.message)
        failed = failed + 1
    }
    
    try {
        orderTests.runOrderTests()
        passed = passed + 1
    } catch e {
        print("❌ Order tests failed: " + e.message)
        failed = failed + 1
    }
    
    print("\n" + "=" * 50)
    print("  RESULTS: {passed} passed, {failed} failed")
    print("=" * 50)
}

runAllTests()
```

---

## Testing Classes

```sona
class Counter {
    func init(start = 0) {
        self.value = start
    }
    
    func increment() {
        self.value = self.value + 1
    }
    
    func decrement() {
        if self.value > 0 {
            self.value = self.value - 1
        }
    }
    
    func reset() {
        self.value = 0
    }
}

// Tests
func test_counter_init() {
    let c1 = Counter()
    assert c1.value == 0, "Default starts at 0"
    
    let c2 = Counter(10)
    assert c2.value == 10, "Can start at custom value"
}

func test_counter_increment() {
    let c = Counter()
    c.increment()
    assert c.value == 1, "Value should be 1"
    
    c.increment()
    c.increment()
    assert c.value == 3, "Value should be 3"
}

func test_counter_decrement() {
    let c = Counter(5)
    c.decrement()
    assert c.value == 4, "Value should be 4"
    
    // Test boundary
    let c2 = Counter(0)
    c2.decrement()
    assert c2.value == 0, "Should not go negative"
}

func test_counter_reset() {
    let c = Counter(100)
    c.reset()
    assert c.value == 0, "Reset should set to 0"
}

func runCounterTests() {
    test_counter_init()
    test_counter_increment()
    test_counter_decrement()
    test_counter_reset()
    print("✅ Counter tests passed!")
}
```

---

## Testing Error Cases

```sona
func test_throws_error() {
    let threw = false
    
    try {
        // This should throw an error
        riskyFunction(-1)
    } catch e {
        threw = true
        assert "invalid" in e.message.lower(), "Should mention invalid"
    }
    
    assert threw, "Should have thrown an error"
}

// Helper function
func expectError(operation, expectedMessage = null) {
    try {
        operation()
        assert false, "Expected an error but none was thrown"
    } catch e {
        if expectedMessage != null {
            assert expectedMessage in e.message, 
                "Expected '{expectedMessage}' in error"
        }
        return true
    }
}

// Usage
func test_validation_errors() {
    expectError(func() {
        User("", "bad-email")
    }, "name required")
    
    expectError(func() {
        User("Alice", "not-an-email")
    }, "invalid email")
}
```

---

## Practice

### Exercise 1
Write tests for a `Stack` class with `push`, `pop`, `peek`, and `isEmpty` methods.

### Exercise 2
Test a `validatePassword` function that should:
- Return false if less than 8 characters
- Return false if no uppercase letter
- Return false if no number
- Return true otherwise

### Exercise 3
Write tests for edge cases:
- Empty inputs
- Very long strings
- Special characters
- Null values

---

→ Next: [mini-2: Test-Driven Development](mini-2_tdd.md)
