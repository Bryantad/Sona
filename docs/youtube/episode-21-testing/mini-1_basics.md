# Mini-Episode 21.1: Testing Basics 🧪

> Why and how to test

---

## Why Write Tests?

Tests help you:

- **Catch bugs** before users do
- **Refactor** with confidence
- **Document** how code should work
- **Save time** debugging later

---

## A Simple Test

```sona
// The function to test
func add(a, b) {
    return a + b
}

// The test
func test_add() {
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0
    print("✓ test_add passed!")
}

test_add()
```

---

## The assert Statement

`assert` checks if something is true:

```sona
assert 2 + 2 == 4        // Passes silently
assert 2 + 2 == 5        // Raises AssertionError!
```

---

## Test Structure: AAA

**Arrange** → **Act** → **Assert**

```sona
func test_discount() {
    // Arrange - Set up test data
    let price = 100
    let discount = 0.2

    // Act - Do the thing
    let final = apply_discount(price, discount)

    // Assert - Check the result
    assert final == 80
}
```

---

## What to Test

```sona
func test_divide() {
    // Normal cases
    assert divide(10, 2) == 5
    assert divide(9, 3) == 3

    // Edge cases
    assert divide(0, 5) == 0
    assert divide(5, 1) == 5

    // Error cases
    try {
        divide(5, 0)
        assert false  // Should not reach here!
    } catch {
        assert true   // Expected error
    }
}
```

---

## Test Naming

Name tests clearly:

```sona
// ✅ Good - describes what's being tested
func test_add_positive_numbers() { }
func test_add_negative_numbers() { }
func test_add_with_zero() { }

// ❌ Bad - unclear
func test1() { }
func test_add() { }  // Too vague
```

---

## Running Tests

```sona
// Simple test runner
func run_tests() {
    let tests = [
        test_add,
        test_subtract,
        test_multiply,
        test_divide
    ]

    let passed = 0
    let failed = 0

    for test in tests {
        try {
            test()
            passed = passed + 1
        } catch error {
            print(f"✗ {test.name}: {error}")
            failed = failed + 1
        }
    }

    print(f"\nResults: {passed} passed, {failed} failed")
}
```

---

## Quick Tips

1. **Test early** - Don't wait until the end
2. **Test often** - Run tests after changes
3. **Keep tests simple** - One thing per test
4. **Test edge cases** - Empty, zero, negative
