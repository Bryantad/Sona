# Mini-Episode 21.2: Assertions 🎯

> Different ways to check correctness

---

## Basic Assertions

```sona
assert condition              // Fails if false
assert condition, "message"   // Fails with message
```

---

## Equality

```sona
// Check exact equality
assert result == expected
assert calculate(5) == 25

// Check inequality
assert result != 0
assert user["role"] != "guest"
```

---

## Comparison

```sona
// Greater/less than
assert age >= 18
assert count < 100
assert score > 0

// Range check
let value = 50
assert value >= 0 and value <= 100
```

---

## Boolean Checks

```sona
// True/false
assert is_valid == true
assert not is_empty

// Truthiness
assert result        // Passes if result is truthy
assert not errors    // Passes if errors is empty/false
```

---

## Collection Assertions

```sona
// Check contains
assert "apple" in fruits
assert key in dictionary

// Check length
assert len(items) == 3
assert len(items) > 0

// Check empty
assert len(items) == 0
assert items == []
```

---

## Type Checks

```sona
// Check type
assert type(result) == "int"
assert type(name) == "str"
assert type(items) == "list"
```

---

## String Assertions

```sona
let text = "Hello, World!"

assert text.startswith("Hello")
assert text.endswith("!")
assert "World" in text
assert len(text) == 13
```

---

## Approximate Equality (Floats)

```sona
// Floats can have precision issues
let result = 0.1 + 0.2  // Might be 0.30000000000000004

// Use approximate comparison
func approx_equal(a, b, tolerance = 0.0001) {
    return abs(a - b) < tolerance
}

assert approx_equal(result, 0.3)
```

---

## Custom Assert Functions

```sona
func assert_between(value, min, max) {
    assert value >= min and value <= max,
        f"Expected {value} to be between {min} and {max}"
}

func assert_contains_all(list, items) {
    for item in items {
        assert item in list, f"Missing: {item}"
    }
}

func assert_raises(func) {
    try {
        func()
        assert false, "Expected exception was not raised"
    } catch {
        // Expected!
    }
}
```

---

## Testing Exceptions

```sona
func test_divide_by_zero() {
    try {
        let result = divide(10, 0)
        assert false, "Should have raised error!"
    } catch error {
        assert "divide by zero" in str(error).lower()
    }
}
```

---

## Assertion Messages

Always add helpful messages:

```sona
// ❌ Bad - no context when it fails
assert user["age"] >= 18

// ✅ Good - tells you what went wrong
assert user["age"] >= 18,
    f"User must be adult, got age {user['age']}"
```
