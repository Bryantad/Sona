# Sona v0.5.0 Test Suite

This file contains a collection of examples for Sona v0.5.0 that demonstrate language features.

## Running the Tests

To run any of these test files:

```bash
cd "/path/to/sona_core"
python -m sona examples/compatibility_tests/[filename].sona
```

## Test Files

1. `basic_operations.sona`: Tests basic arithmetic and string operations
2. `imports.sona`: Tests importing and using modules correctly
3. `conditionals.sona`: Tests if-else structures
4. `variables.sona`: Tests variable declaration and reassignment
5. `functions.sona`: Tests function definition and parameter usage
6. `multiline_strings.sona`: Demonstrates multi-line string literals with triple quotes
7. `error_handling.sona`: Shows improved error messages with line information
8. `comments.sona`: Demonstrates inline and multi-line comments

## Features

- Import syntax supports the `as` keyword for module aliases
- Function parameters work correctly
- Type conversions must be explicit when concatenating strings with other types
- If-else statements are properly nested
- Multi-line strings using triple quotes (`"""` or `'''`)
- Enhanced error messages with line and column information
- Improved comment handling including inline comments

See `docs/version_compatibility.md` for detailed information on Sona v0.5.0 features.
