# Module 14: Testing & Quality

## Overview
Professional code needs tests. This module teaches you how to write reliable, maintainable code through testing and quality practices.

**Target Audience:** Ages 12-55, neurodivergent-friendly  
**Prerequisites:** Modules 01-13  
**Duration:** 60-75 minutes

---

## Learning Objectives
- Write effective unit tests
- Use test-driven development (TDD)
- Measure code coverage
- Apply quality best practices

---

## Mini-Lessons

| Mini | Topic | Focus |
|------|-------|-------|
| [mini-1](mini-1_unit_tests.md) | Unit Testing | Writing and running tests |
| [mini-2](mini-2_tdd.md) | Test-Driven Development | Write tests first |
| [mini-3](mini-3_quality.md) | Code Quality | Best practices and patterns |

---

## Quick Reference

```sona
// Basic test
func test_addition() {
    assert 2 + 2 == 4, "Math is broken!"
}

// Test with setup
func test_user_creation() {
    let user = User("Alice", "alice@example.com")
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
    assert user.isValid()
}

// Run all tests
func runTests() {
    test_addition()
    test_user_creation()
    print("✅ All tests passed!")
}
```

---

## Next Steps
→ Continue to [Module 15: Advanced Topics](../15_advanced/README.md)
