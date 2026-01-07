# Mini-Episode 21.3: Test Organization 📁

> Structure tests professionally

---

## File Structure

```
my_project/
├── src/
│   ├── calculator.sona
│   └── utils.sona
└── tests/
    ├── test_calculator.sona
    └── test_utils.sona
```

Name test files: `test_<module>.sona`

---

## Test File Template

```sona
// test_calculator.sona
from src.calculator import add, subtract, multiply, divide

// Test fixtures (shared test data)
let NUMBERS = [0, 1, -1, 100, -100]

// Test functions
func test_add_basics() {
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
}

func test_subtract_basics() {
    assert subtract(5, 3) == 2
}

// Run all tests
func run_all() {
    let tests = [test_add_basics, test_subtract_basics]
    // ... run them
}
```

---

## Group Related Tests

```sona
// Tests for User class
class TestUser {
    func test_create_user() {
        let user = User("Alice", "alice@test.com")
        assert user.name == "Alice"
    }

    func test_update_email() {
        let user = User("Bob", "old@test.com")
        user.update_email("new@test.com")
        assert user.email == "new@test.com"
    }

    func run_all() {
        self.test_create_user()
        self.test_update_email()
        print("✓ All User tests passed!")
    }
}
```

---

## Setup and Teardown

```sona
class TestDatabase {
    func setup() {
        // Run before EACH test
        self.db = Database(":memory:")
        self.db.create_table("users")
    }

    func teardown() {
        // Run after EACH test
        self.db.close()
    }

    func test_insert() {
        self.setup()
        self.db.insert("users", {"name": "Test"})
        assert self.db.count("users") == 1
        self.teardown()
    }
}
```

---

## Test Fixtures

Reusable test data:

```sona
// fixtures.sona
let SAMPLE_USER = {
    "name": "Test User",
    "email": "test@example.com",
    "age": 25
}

let SAMPLE_PRODUCTS = [
    {"name": "Apple", "price": 1.50},
    {"name": "Banana", "price": 0.75}
]

func create_test_user(overrides = {}) {
    let user = SAMPLE_USER.copy()
    for key, value in overrides.items() {
        user[key] = value
    }
    return user
}
```

---

## Test Runner

```sona
// test_runner.sona

func discover_tests(module) {
    let tests = []
    for name in dir(module) {
        if name.startswith("test_") {
            tests.append(getattr(module, name))
        }
    }
    return tests
}

func run_tests(tests) {
    let results = {"passed": 0, "failed": 0, "errors": []}

    for test in tests {
        try {
            test()
            results["passed"] += 1
            print(f"  ✓ {test.name}")
        } catch error {
            results["failed"] += 1
            results["errors"].append({"test": test.name, "error": error})
            print(f"  ✗ {test.name}: {error}")
        }
    }

    print(f"\n{'='*40}")
    print(f"Passed: {results['passed']}, Failed: {results['failed']}")
    return results
}
```

---

## Best Practices

1. **One test = one thing**
2. **Tests should be independent**
3. **Use descriptive names**
4. **Clean up after tests**
5. **Test edge cases**
6. **Keep tests fast**

---

## Test Coverage Checklist

For each function, test:

- [ ] Normal inputs
- [ ] Edge cases (0, empty, null)
- [ ] Boundary values
- [ ] Invalid inputs
- [ ] Error conditions
