# 🧪 Sona 0.9.6 Testing Guide

Welcome to the Sona 0.9.6 test suite! This guide will help you run tests and verify that your Sona installation is working correctly.

## Quick Start

### Test Your Installation Right Now

```powershell
# Run the simple test (works immediately)
python run_sona.py test_simple_096.sona
```

Expected output:
```
=== Sona 0.9.6 Simple Test ===
x = 42
y = 10
Sum = 52
Difference = 32
Product = 420
...
=== Test Complete ===
```

## Available Tests

### 🟢 Basic Tests (Work Now)

| File | Description | Run Command |
|------|-------------|-------------|
| `test.sona` | Original arithmetic test | `python run_sona.py test.sona` |
| `test_hello.sona` | Hello world | `python run_sona.py test_hello.sona` |
| `test_simple_096.sona` | Extended simple test | `python run_sona.py test_simple_096.sona` |

### 🟡 Standard Library Tests (Ready for Import System)

These tests are fully written and will work once the `import` statement is implemented:

| File | Modules Tested | Description |
|------|----------------|-------------|
| `test_stdlib_basics.sona` | string, math, numbers, boolean, type, comparison | Core module functionality |
| `test_stdlib_data.sona` | json, encoding, hashing, uuid, validation | Data processing |
| `test_stdlib_collections.sona` | collection, queue, stack, sort, search, statistics | Collections & algorithms |
| `test_stdlib_time.sona` | time, date, timer, random | Time and random functions |
| `test_stdlib_filesystem.sona` | fs, path, io, env | Filesystem operations |
| `test_stdlib_regex.sona` | regex | Regular expressions |
| `test_all_096.sona` | All 30 modules | Complete verification |

## Running Tests

### Method 1: Individual Tests

```powershell
# Run a specific test
python run_sona.py test_simple_096.sona
```

### Method 2: Using Direct Runner

```powershell
# Same as above, more explicit
python run_sona.py path\to\test.sona
```

### Method 3: Using Sona CLI (if installed)

```powershell
sona test_simple_096.sona
```

### Method 4: Run All Tests (Future)

Once all features are implemented:

```powershell
# PowerShell
.\run_all_tests.ps1

# Command Prompt
.\run_all_tests.bat
```

## What Each Test Verifies

### test_simple_096.sona
✅ Variables and assignment  
✅ Arithmetic operations (+, -, *, /)  
✅ String concatenation  
✅ Comparisons (<, >, ==, !=)  
✅ Type conversion (str())  
✅ Print statements  

### test_stdlib_basics.sona (Requires imports)
- String manipulation (reverse, upper, lower, trim)
- Math operations (abs, max, min, pow, sqrt, floor, ceil)
- Number utilities (is_even, is_odd, clamp)
- Boolean logic (and, or, not, xor)
- Type checking (type_of, is_string, is_number)
- Comparisons (equals, greater_than, less_than)

### test_stdlib_data.sona (Requires imports)
- JSON parsing and stringification
- Base64 and hex encoding/decoding
- Hash functions (MD5, SHA1, SHA256)
- UUID generation and validation
- Email and URL validation

### test_stdlib_collections.sona (Requires imports)
- List operations (map, filter, reduce)
- Queue operations (FIFO)
- Stack operations (LIFO)
- Sorting algorithms
- Search functions
- Statistical calculations

### test_stdlib_time.sona (Requires imports)
- Current time and timestamps
- Date operations
- Timer functionality
- Random number generation

### test_stdlib_filesystem.sona (Requires imports)
- Path manipulation
- Environment variables
- File I/O operations
- Directory management

### test_stdlib_regex.sona (Requires imports)
- Pattern matching
- String searching
- Find all matches
- Replace operations
- String splitting

## Troubleshooting

### Error: "Variable 'modulename' is not defined"

This means the test file uses `import` statements which aren't fully implemented yet. Use the basic tests instead:

```powershell
python run_sona.py test_simple_096.sona
```

### Error: "File not found"

Make sure you're in the SonaMinimal directory:

```powershell
cd F:\SonaMinimal
python run_sona.py test_simple_096.sona
```

### No output or hangs

Check that Python 3.8+ is installed:

```powershell
python --version
```

## Python Unit Tests

In addition to `.sona` test files, there are Python unit tests:

```powershell
# Test module imports (Python level)
python test_stdlib_30.py

# Test advanced cognitive functions
python test_advanced_cognitive_functions.py
```

## Test Suite Statistics

- **Total test files**: 17
- **Working now**: 3 basic tests
- **Ready for imports**: 7 stdlib tests  
- **Advanced features**: 4 additional tests
- **Documentation files**: 3

### Coverage (when fully operational)

- **30 modules** in standard library
- **280+ test cases** total
- **40%+ code coverage**
- **100% pass rate** target

## Next Steps

1. ✅ **Now**: Run basic tests (`test_simple_096.sona`)
2. 🚧 **Soon**: Import system implementation
3. 🎯 **Then**: Full stdlib test suite activation
4. 🚀 **Future**: Automated CI/CD testing

## Contributing New Tests

To add a new test file:

1. Create a `.sona` file following the naming pattern
2. Use simple syntax (no imports for now)
3. Include descriptive print statements
4. Test with: `python run_sona.py your_test.sona`
5. Document in this README

### Test File Template

```sona
print("=== My Test Name ===");
# Your test code here
x = 10;
y = 20;
print("Result: " + str(x + y));
print("=== Test Complete ===");
```

## Support & Documentation

- 📖 **Full test docs**: See `TESTS_096_README.md`
- 📊 **Test summary**: See `TEST_SUITE_SUMMARY.md`
- 📝 **Changelog**: See `CHANGELOG.md`
- 🔧 **Standard library**: See `STDLIB_30_MODULES.md`

## Success Criteria

A test passes if:
- ✅ No runtime errors
- ✅ All print statements execute
- ✅ Output matches expected values
- ✅ No warnings or exceptions

A test fails if:
- ❌ Runtime error occurs
- ❌ Unexpected output
- ❌ Variable not defined errors
- ❌ Syntax errors

---

**Last Updated**: October 9, 2025  
**Sona Version**: 0.9.6  
**Test Suite Status**: Partially operational (basic tests working, stdlib tests ready)

Happy Testing! 🎉
