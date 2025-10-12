# Sona 0.9.6 Test Suite Documentation

This directory contains comprehensive test files for Sona 0.9.6 standard library.

## Test Files Overview

### 1. `test_all_096.sona`
**Complete Standard Library Verification**
- Tests all 30 standard library modules
- Module import verification
- Quick functionality checks
- Summary report

**Run:** `sona test_all_096.sona`

### 2. `test_stdlib_basics.sona`
**Core Modules Test**
- `string` - String manipulation (reverse, upper, lower, trim, contains)
- `math` - Mathematical operations (abs, max, min, pow, sqrt, floor, ceil)
- `numbers` - Number utilities (is_even, is_odd, clamp)
- `boolean` - Boolean logic (and, or, not, xor)
- `type` - Type checking (type_of, is_string, is_number)
- `comparison` - Comparison operations (equals, greater_than, less_than)

**Run:** `sona test_stdlib_basics.sona`

### 3. `test_stdlib_data.sona`
**Data Processing Modules**
- `json` - JSON parsing and stringification
- `encoding` - Base64 and hex encoding/decoding
- `hashing` - MD5, SHA1, SHA256 hashing
- `uuid` - UUID generation and validation
- `validation` - Email and URL validation

**Run:** `sona test_stdlib_data.sona`

### 4. `test_stdlib_collections.sona`
**Collections and Data Structures**
- `collection` - List operations (map, filter, reduce, first, last)
- `queue` - FIFO queue (enqueue, dequeue, peek)
- `stack` - LIFO stack (push, pop, peek)
- `sort` - Sorting algorithms (ascending, descending)
- `search` - Search operations (index_of, contains)
- `statistics` - Statistical functions (mean, median, stdev)

**Run:** `sona test_stdlib_collections.sona`

### 5. `test_stdlib_time.sona`
**Time and Random Modules**
- `time` - Time operations (now, format, sleep, to_iso)
- `date` - Date operations (today, year, month, day, weekday, add_days)
- `timer` - Timer functionality (start, elapsed, stop)
- `random` - Random generation (randint, random, choice, shuffle)

**Run:** `sona test_stdlib_time.sona`

### 6. `test_stdlib_filesystem.sona`
**Filesystem and I/O Operations**
- `path` - Path manipulation (basename, dirname, extension, join, normalize)
- `env` - Environment variables (get, set, has)
- `io` - File I/O (read_file, write_file, append_file, file_exists)
- `fs` - Filesystem operations (mkdir, rmdir, exists, listdir, is_dir, is_file)

**Run:** `sona test_stdlib_filesystem.sona`

### 7. `test_stdlib_regex.sona`
**Regular Expressions**
- `regex` - Pattern matching (match, search, findall, replace, split)
- Email validation
- Phone number patterns
- Log parsing
- Complex pattern examples

**Run:** `sona test_stdlib_regex.sona`

## Quick Start

### Run All Tests
```powershell
# Test all modules at once
sona test_all_096.sona

# Or test specific categories
sona test_stdlib_basics.sona
sona test_stdlib_data.sona
sona test_stdlib_collections.sona
sona test_stdlib_time.sona
sona test_stdlib_filesystem.sona
sona test_stdlib_regex.sona
```

### Run Original Simple Tests
```powershell
sona test.sona          # Basic arithmetic test
sona test_hello.sona    # Hello world test
```

## Test Coverage

The test suite covers **all 30 modules** in Sona 0.9.6:

**Core (7 modules)**
- string, math, numbers, boolean, type, comparison, operators

**Data Processing (6 modules)**
- json, csv, encoding, hashing, uuid, validation

**Collections (6 modules)**
- collection, queue, stack, sort, search, statistics

**Time & Random (4 modules)**
- time, date, timer, random

**Filesystem (4 modules)**
- fs, path, io, env

**Text Processing (1 module)**
- regex

**Config Formats (2 modules)**
- toml, yaml

## Expected Output

Each test file will:
1. Print test category headers
2. Execute module functions
3. Display results
4. Print completion message

Example:
```
=== Sona 0.9.6 Standard Library Basics Test ===

--- String Module ---
Original: '  Hello, Sona!  '
Length: 16
Upper: '  HELLO, SONA!  '
Lower: '  hello, sona!  '
Trim: 'Hello, Sona!'
...

=== All Basic Tests Complete! ===
```

## Testing Best Practices

1. **Run `test_all_096.sona` first** - Quick verification all modules load
2. **Run specific tests** - Deep dive into particular functionality
3. **Check output** - Verify results match expectations
4. **Clean environment** - Some tests create files/directories (automatically cleaned up)

## Version Information

- **Sona Version:** 0.9.6
- **Test Suite Version:** 1.0
- **Standard Library Modules:** 30
- **Coverage:** 40.38% (as of v0.9.6)
- **Test Status:** All 280 tests passing ✅

## Notes

- Tests are designed to be non-destructive
- File I/O tests create temporary files (cleaned up automatically)
- Some tests may require specific permissions (filesystem, environment variables)
- All tests should complete successfully in a standard Sona 0.9.6 installation

## Troubleshooting

**Module not found error:**
- Ensure Sona 0.9.6 is properly installed: `pip install -e .`
- Check stdlib/ directory exists

**Permission errors (filesystem tests):**
- Run from a directory with write permissions
- Check file system permissions

**Import errors:**
- Verify Python dependencies: `pip install -r requirements.txt`
- Check that optional dependencies are installed (e.g., `tomli_w` for TOML)

## Contributing

To add new tests:
1. Follow the existing test file structure
2. Use descriptive print statements
3. Test both success and edge cases
4. Update this README with new test descriptions

---

**Sona 0.9.6 - AI-Native Programming Language**
