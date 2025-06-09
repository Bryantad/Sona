## [0.6.0] - 2025-06-09

### Added

- Enhanced interpreter with improved error handling and stability
- Advanced grammar features for better syntax support
- Enhanced standard library modules:
  - Improved math module with additional functions
  - Enhanced string manipulation capabilities
  - Better I/O operations and file handling
  - Enhanced environment variable support
  - Improved time and date functions
- New example programs showcasing v0.6.0 features
- Enhanced function parameter handling and scope management
- Improved module system with better import resolution

### Improved

- Interpreter performance optimizations
- Better error messages with more context
- Enhanced REPL functionality
- Improved syntax highlighting and parsing
- Better memory management
- Enhanced testing framework

### Fixed

- Function parameter scope issues
- Module import resolution bugs
- String parsing edge cases
- Numeric type conversion issues
- Loop execution stability
- Variable assignment consistency

### Security

- Enhanced input validation
- Improved module loading security
- Better error handling to prevent information leakage

## [0.5.1] - 2025-05-23

### Added

- Advanced REPL diagnostic tools:
  - `:debug` command to display last error, parse tree, and environment scopes
  - `:profile` command to measure execution time of commands
  - `:watch <var>` command to inspect variable values
  - `:trace` command to log function calls and returns
- Added detailed documentation for debugging tools
- Added a debug tools module in `sona/utils/debug_tools.py`
- Improved project organization:
  - Created structured directories for development files
  - Organized test files into appropriate categories
  - Added comprehensive directory documentation
  - Created a release tools directory with cleanup script

### Security

- Fixed function parameter scope handling to prevent variable shadowing issues
- Added validation checks for module imports to prevent path traversal
- Implemented input size limits to prevent DoS attacks

### Bug Fixes

- Fixed multi-line string handling with triple quotes
- Fixed numeric type handling in if/else statements
- Fixed loop body execution in while statements
- Improved type consistency throughout the interpreter
- Improved error reporting with more context around error locations
- Fixed edge cases in import aliasing with certain module paths
- Corrected several memory leaks in the interpreter
- Fixed `:test` command in REPL to correctly run the diagnostic tests

### REPL Enhancements

- Added `:calc` and `:quiz` commands to launch calculator and quiz applications
- Added support for exiting REPL without colon prefix (by typing "exit" or "quit")
- Fixed `:test` command implementation to run the diagnostic test suite

### Documentation

- Added security recommendations in SECURITY.md
- Updated examples to demonstrate fixed functionality

# Sona Language - Version 0.5.0

## What's New

This release introduces several new features, improvements, and bug fixes to enhance the Sona programming experience. The focus is on expanding the demo programs, improving documentation, and refining the REPL environment.

### New Language Features

- **Import Aliases**: Added support for `import ... as ...` syntax
- **Multi-line Strings**: Added support for triple-quoted strings (`"""` or `'''`)
- **Enhanced Error Messages**: Improved error messages with line and column information
- **Inline Comments**: Added better support for inline comments at the end of statements
- **Function Parameter Fixes**: Improved function parameter access in function bodies

### New Features

#### Demo Programs

- **Fixed & Enhanced `snake_game_fixed.sona`**: Fixed syntax issues with comparison operators and boolean values
- **Added `timer.sona`**: Implemented countdown timer and stopwatch functionality using the time module
- **Added `todo.sona`**: Created in-memory todo list application with add, list, and complete functionality
- **Added `file_writer.sona`**: Implemented file operations demo with write, append, read capabilities and timestamped logging
- **Added `http_get.sona`**: Created HTTP client demo with JSON response handling and simulated endpoints
- **Added `data_analyzer.sona`**: Created statistical analysis tool with data processing and visualization capabilities
- **Added `ascii_visualization.sona`**: Implemented text-based charts and visualization toolkit with multiple chart types
- **Added `pattern_matcher.sona`**: Created text processing utility with pattern matching and string manipulation functions
- **Added `memory_game.sona`**: Implemented interactive card matching game with array operations and state management

#### Documentation

- **Added comprehensive README.md** for examples directory with usage instructions and syntax guidelines
- **Documented common Sona syntax patterns** and workarounds for comparison operators, boolean values, and variable reassignment

#### IDE & Playground

- **Created web scaffold for Sona Playground** with code editor, example loader, documentation browser, and simulated execution

### Improvements

- **Enhanced snake_game implementation**: Fixed comparison operator handling with helper functions
- **Standardized boolean representation**: Used integers (0/1) for boolean values consistently across all examples
- **Improved variable reassignment patterns**: Ensured all examples properly use `let` keyword for reassignment
- **Created REPL-ready modules**: All demo programs are structured to be accessible through the REPL

### Bug Fixes

- **Fixed empty return statements**: Ensured all return statements include expressions
- **Fixed boolean logic issues**: Replaced direct boolean operators with math.eq() and custom comparison functions
- **Resolved parsing errors** in snake_game related to comparison operators and boolean values

### Known Issues

- Variable reassignment requires using `let` keyword each time
- Direct comparison operators (`<`, `>`, `<=`, `>=`) are not supported
- Boolean literals (`true`, `false`) are not supported, use integers (1,0) instead
- All functions must include return values, empty returns are not allowed

# Sona Language - Version 0.4.9

## What's New

This release improves the module import system, enhances REPL functionality, and provides better documentation and examples.

### New Features

#### Module System Enhancements

- Improved module import resolution for nested module paths
- Enhanced stdlib module documentation and examples
- Added support for the `:modules`, `:doc`, and `:example` REPL commands
- Fixed module preloading in REPL initialization

#### REPL Improvements

- New commands added:
  - `:modules` – List available modules
  - `:doc` – Show module documentation (e.g. `:doc math`)
  - `:example` – Show example code (e.g. `:example random`)
- Better error handling for module imports
- Improved module documentation display
- Enhanced help command with new features

#### Standard Library Updates

- Enhanced math module integration
- Added comprehensive random module
- Improved string module functionality
- Better type conversion support
- Enhanced validation utilities

### Bug Fixes

- Fixed module import path resolution on Windows
- Improved error handling for missing modules
- Fixed REPL environment variable display

### New Features

#### Core Interpreter Enhancements

- Fully working dotted attribute access (e.g. `math.PI`, `fs.exists()`)
- New dotted function call support: `math.add(1, 2)`
- Nested module import resolution (e.g. `import utils.math.smod`)
- Better environment inspection & variable scoping in REPL
- Constants (like `math.PI`, `math.E`) now accessible via modules

#### REPL Enhancements v0.4.3

New Commands:

- `:env` – Dump current environment variables
- `:clear` – Reset scope and functions
- `:reload` – Reload interpreter + grammar
- `:help` – Show built-in REPL command list

Improvements:

- Function definitions now supported interactively
- Multi-line `func` block entry via `{}` handling
- REPL command parsing bypasses grammar to avoid false parsing errors

#### Array Support

- Array literal syntax: `[1, 2, 3]`
- Built-in array module with essential operations:
  - `array.push(arr, item)` - Add element to end of array
  - `array.pop(arr)` - Remove and return last element
  - `array.length(arr)` - Get array size
  - `array.get(arr, index)` - Access element by index
  - `array.set(arr, index, value)` - Modify element at index
  - `array.slice(arr, start, end)` - Get array subset
  - `array.concat(arr1, arr2)` - Combine two arrays
  - `array.contains(arr, item)` - Check for element existence
- Nested array support with proper type handling

#### Math Module Highlights

- Constants: `PI`, `E`, `TAU`
- Algebra: `add`, `subtract`, `multiply`, `divide`, `modulo`, `abs`, `pow`
- Trigonometry: `sin`, `cos`, `tan`, `degrees`, `radians`
- Log/Exp: `log`, `log10`, `exp`
- Geometry: `hypot`, `sqrt`

#### Module System (.smod)

- Fully working dotted attribute access (e.g. `math.PI`, `fs.exists()`)
- Nested module import resolution (e.g. `import utils.math.smod`)
- Support for module method and property access
- Modules implemented:
  - `utils.math.smod` – Advanced algebra, trigonometry, constants
  - `utils.string.smod` – String manipulation utilities
  - `utils.array.smod` – Array operations
  - `utils.convert.smod` – Type conversion utilities
  - `utils.validate.smod` – Value validation
  - `utils.debug.smod` – REPL diagnostics

### Technical Improvements

- Added proper index validation for array operations
- Implemented array method error handling
- Fixed double-nesting issues with array literals
- Improved module loading mechanism
- Enhanced dotted name resolution
- `func_call()` now checks both dict and object-style modules
- `get_var()` supports full dotted-name traversal
- Grammar updated to handle `NAME.NAME.NAME` dotted variable access
- Lark parser gracefully handles nested dotted functions/attributes

#### Cross Platform Support 🖥️

- Enhanced file path handling using `pathlib.Path` for cross-platform compatibility
- Standardized line endings and file encodings (UTF-8)
- Unified module import behavior across Windows and Unix systems
- Platform-agnostic file system operations in `fs.smod`
- Cross-platform terminal output handling
- Environment variable management that works on all OS
- OS-independent path resolution for `.smod` files
- Standardized newline handling in REPL
- Fixed Windows-specific file locking issues
- Improved path separator handling in module imports

### Documentation Updates

- Added array usage examples
- Updated module import documentation
- Added new test files demonstrating array functionality
- Improved code comments and docstrings
- Added REPL command documentation

### Bug Fixes

- Fixed array method float-to-int conversion
- Fixed nested array creation
- Resolved module import path issues
- Fixed scope issues with method calls
- Corrected array operation return values
- Fixed attribute resolution for dotted names
- Corrected `math` module not exposing static constants
- Fixed REPL buffer not flushing on multi-line errors
- Resolved REPL not recognizing user-defined functions
- Eliminated import failures with scoped Python modules
- Patched float vs int handling in math operations

## Breaking Changes

None. All new features are backward compatible.

## Coming Next

- Built-in modules: `fs.smod`, `http.smod`, `env.smod`, `stdin.smod`
- Multi-dimensional array support
- Advanced array operations (map, filter, reduce)
- Array destructuring and comprehensions
- Type annotations (beginner-friendly)
- Class support / object literals
- Error stack traces w/ file + line number support
- CLI tools for .smod management (build, test, doc)
- Script execution mode with REPL context preloading

## How to Upgrade

```bash
# For Unix-like systems (macOS, Linux)
git pull origin main
pip install -e .
sona repl  # Try :help to see new features

# For Windows systems
git pull origin main
pip install -e .
python -m sona repl  # Try :help to see new features
```

## Platform Notes

### Windows Users

- File paths use backslashes by default but forward slashes are also supported
- Environment variables use Windows conventions (%PATH% vs $PATH)
- Command line usage: `python -m sona <filename.sona>`
- REPL available through `python -m sona repl`

### macOS/Linux Users

- File paths use forward slashes
- Environment variables use Unix conventions ($PATH)
- Direct command line usage: `sona <filename.sona>`
- REPL available through `sona repl`

### Common Features (All Platforms)

- UTF-8 encoding for all files
- Network paths supported where applicable
- Relative and absolute paths handled consistently
- Cross-platform line endings managed automatically
- Identical module import behavior
- All stdlib functions work identically
- Debug mode available with `--debug` flag (e.g., `sona --debug` or `python -m sona --debug`)
- Regular mode runs by default without extra flags
- REPL-ready example programs that can be imported directly in the REPL
- All demos work in both debug and regular modes

## REPL Command Reference

The Sona REPL provides several special commands to help with development and exploration:

### Core Commands

- `:help` - Display a list of available REPL commands
- `:env` - Display the current environment variables and their values
- `:clear` - Clear the current REPL environment (reset variables and functions)
- `:reload` - Reload the interpreter and grammar
- `:exit` or `:quit` - Exit the REPL

### Module Commands

- `:modules` - List all available modules
- `:doc <module>` - Display documentation for a specific module (e.g., `:doc math`)
- `:example <module>` - Show usage examples for a specific module (e.g., `:example array`)

### Debug Commands

- `:ast <expression>` - Display the abstract syntax tree for an expression
- `:trace <expression>` - Enable tracing for an expression evaluation
- `:debug on|off` - Toggle debug mode within the REPL

### Import Examples

```sona
import utils.math.smod as math
import utils.string.smod as string
import utils.array.smod as array
import examples.snake_game_fixed
```

## Examples

```sona
// Basic array usage
let numbers = [1, 2, 3]
array.push(numbers, 4)
print(array.length(numbers))  // Output: 4

// Array operations
let first = array.get(numbers, 0)
array.set(numbers, 1, 10)
let subset = array.slice(numbers, 1, 3)

// Array concatenation
let moreNumbers = [5, 6, 7]
let combined = array.concat(numbers, moreNumbers)

// Math module usage
print(math.PI)              // 3.14159...
print(math.add(2, 3))      // 5
print(math.factorial(5))    // 120
print(math.gcd(20, 8))     // 4
print(math.degrees(3.14))   // 179.909...
```
