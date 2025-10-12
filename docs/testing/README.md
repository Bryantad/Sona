# Testing Documentation

This folder contains all testing-related documentation for Sona v0.9.6.

## 📚 Main Testing Guides

### [TESTING_GUIDE.md](./TESTING_GUIDE.md)

**START HERE** - Complete guide to testing Sona code.

**Topics:**

- How to run tests
- Writing test files
- Test file naming conventions
- Common testing patterns
- Debugging failed tests

---

### [TEST_QUICK_REFERENCE.md](./TEST_QUICK_REFERENCE.md)

Quick reference card for common testing tasks.

**Use this for:**

- Fast lookup of test commands
- Common test patterns
- Quick syntax reminders

---

## 📋 Test Catalogs

### [TEST_INDEX.md](./TEST_INDEX.md)

Complete index of all test files in the repository.

**Contents:**

- Test file locations
- What each test covers
- Test categories

---

### [TEST_FILES_COMPLETE.md](./TEST_FILES_COMPLETE.md)

Detailed listing of all test files with descriptions.

---

### [TEST_SUITE_SUMMARY.md](./TEST_SUITE_SUMMARY.md)

High-level overview of the test suite structure and coverage.

**Metrics:**

- Total test files
- Coverage by feature
- Pass/fail statistics

---

## 🔖 Version-Specific

### [TESTS_096_README.md](./TESTS_096_README.md)

Testing documentation specific to v0.9.6 release.

**Topics:**

- v0.9.6 test additions
- New features tested
- Regression tests

---

## Quick Start

### Run All Tests

```powershell
python run_sona.py test_all_features.sona
```

### Run Specific Test

```powershell
python run_sona.py test_break_continue.sona
```

### Test All 30 Modules

```powershell
python run_sona.py test_all_30_imports.sona
```

---

## Test Organization

Tests are organized by category:

```
tests/
├── core/           # Core language features
├── stdlib/         # Standard library modules
├── control/        # Control flow (loops, conditionals)
├── features/       # Advanced features
└── regression/     # Regression tests for bug fixes
```

---

## Coverage Status (v0.9.6)

- ✅ **Core Features**: 18/18 tested
- ✅ **Stdlib Modules**: 30/30 tested
- ✅ **Control Flow**: break, continue, loops tested
- ✅ **Error Handling**: try/catch tested
- ⚠️ **Grammar Features**: 6/12 tested (match, when, classes need more tests)

---

## Writing New Tests

1. Create `.sona` file in appropriate test directory
2. Import required modules
3. Write test cases with clear output
4. Run and verify output
5. Document in TEST_INDEX.md

**Example:**

```sona
// test_my_feature.sona
import io;

print("Testing feature X...");

// Test case 1
let result = my_function(10);
if result == 20 {
    print("✅ Test 1 passed");
} else {
    print("❌ Test 1 failed: expected 20, got " + result);
};
```

---

**See Also:**

- [../troubleshooting/](../troubleshooting/) - Debugging failed tests
- [../features/FEATURE_AUDIT_096.md](../features/FEATURE_AUDIT_096.md) - Feature status
- [../development/](../development/) - Implementation notes
