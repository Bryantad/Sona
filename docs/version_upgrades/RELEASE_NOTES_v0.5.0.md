# Sona v0.5.0 - Release Notes

## Introduction

Sona v0.5.0 is a significant update focused on improving the language's usability and fixing several important issues related to variable scoping and imports. This release enhances both the language syntax and the interpreter implementation.

## New Features and Improvements

### 1. Import Aliasing

- **Added support for the `as` keyword** in import statements
- Syntax: `import module.path as alias`
- Example: `import utils.math.smod as math`
- This allows for more concise code and better organization of modules

### 2. Multi-line String Support

- **Added triple-quoted strings** (`"""` or `'''`)
- Preserves all whitespace, indentation, and line breaks
- Perfect for formatted text, documentation, or multi-line content
- Example:
  ```sona
  let welcome_message = """
      Welcome to Sona v0.5.0!
      This is a multi-line string
      that preserves all formatting.
  """
  ```

### 3. Enhanced Error Reporting

- **Line and column information** in error messages
- More specific error messages for various error types
- Makes debugging much easier, especially for larger programs
- Example: `NameError: Variable 'x' not found at line 5, column 10`

### 4. Fixed Function Parameter Scope

- **Parameters are now properly accessible** within function bodies
- Resolved nested scope issues for parameter lookup
- Improved variable resolution in nested functions
- Example:
  ```sona
  func calculate(x) {
      return x * 2  // Now correctly accesses the parameter 'x'
  }
  ```

## Project Organization

The project structure has been reorganized for better maintainability:

```
sona_core/
├── sona/              # Core language implementation
├── stdlib/            # Standard library modules
├── examples/          # Example Sona programs
├── tests/             # Test files
└── tools/             # Utility scripts
    ├── cleanup.py     # Project cleanup utility
    ├── install.py     # Installation helper
    └── run_tests.py   # Test runner
```

## Getting Started

1. **Installation**:

   ```bash
   python3.10 tools/install.py
   ```

2. **Running Sona programs**:

   ```bash
   python3.10 -m sona.sona_cli path/to/program.sona
   ```

3. **Running tests**:
   ```bash
   python3.10 tools/run_tests.py
   ```

## Documentation

For more detailed information about Sona v0.5.0:

- See `docs/syntax_guide.md` for language syntax reference
- Check `examples/` for code examples demonstrating new features
- Visit `CHANGELOG.md` for detailed version history

## Known Issues and Limitations

- Certain edge cases in nested function parameters may still have issues
- Error highlighting in the REPL needs improvement
- Triple-quoted strings do not yet support escape sequences

## Future Development

Planned for future versions:

- Native data structures (maps, sets)
- Additional standard library modules
- Enhanced debugging tools
