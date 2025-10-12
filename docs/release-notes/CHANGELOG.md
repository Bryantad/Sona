# CHANGELOG - Sona Programming Language

## [0.9.6] - 2025-10-06 — Truth-First Stabilization (Zero-Red Tests + 40% Coverage) ✅

### Added

- `string.reverse(text: str) -> str` (Unicode-safe) and exported via `__all__`.
- `string` case conversion suite: Fixed `words()`, `camel_case()`, `snake_case()`, `kebab_case()` with proper camelCase boundary detection.
- API-contract guardrails across 18 modules (json, numbers, env, time, csv, path, collection, string, math, random, io, queue, stack, hashing, timer, toml, validation, encoding).
- Behavior tests (**83 total**: 21 original + 62 new across 16 modules) for comprehensive coverage without inventing APIs.
- Extended test suites for: hashing, timer, queue/stack, time, io, json, env, collection, comparison, string.

### Fixed

- `string`: Restored `rtrim` to `__all__`; resolved missing export drift.
- `string`: Fixed 4 case conversion functions (words, camel_case, snake_case, kebab_case) with Unicode-safe camelCase splitting.
- `toml`: Added writer dependency support via `tomli_w`; tests now pass when the optional extra is installed.

### Tooling / CI

- Enforced **API-first** discipline:
  - Modules declare canonical exports via `__all__`.
  - Contract tests assert existence/shape; tests may not reference non-exported symbols.
- Introduced helper utilities for contract assertions under `tests/utils/`.

### Documentation

- `WORKING_DEFINITION.md`: Canonical criteria for a "working" module (import + tests + docs).
- `TESTING.md`: API-first rubric (Inventory → Contract → Behavior) and guardrail rules.
- `EXECUTION_SUMMARY_OCT6_2025.md`: Session report with metrics and verification steps.
- `PR_TRUTH_FIRST_STABILIZATION.md`: Comprehensive PR description.
- `MERGE_READY_ARTIFACTS.md`: All merge workflow artifacts.
- `NEXT_PR_PLAN.md`: Roadmap for v0.9.7 (target 50%+ coverage).
- `TEST_ACCURACY_AUDIT_V096.md`: Complete audit of all 280 tests verifying accuracy.
- `V096_RELEASE_COMPLETE.md`: Final release report with all metrics.

### Metrics (Before → After → Δ)

- Tests: 176 → **280** (**+104**)
- Passing: 166 → **280** (**+114**, **ZERO failures** 🎉)
- Failing: 10 → **0** (**-10**, **100% pass rate**)
- Coverage: 27.92% → **40.38%** (**+12.46pp**, **40% TARGET EXCEEDED** ✅)

### Module-Level Improvements (Top 10)

- timer: 43.33% → 96.67% (+53.34pp) 🚀
- io: 46.15% → 87.18% (+41.03pp) 🚀
- hashing: 25.00% → 87.50% (+62.50pp) 🚀
- collection: 19.49% → 81.36% (+61.87pp) 🚀
- numbers: 12.90% → 74.19% (+61.29pp) 🚀
- path: 29.63% → 64.81% (+35.18pp) 🚀
- env: 12.97% → 40.54% (+27.57pp) 🚀
- csv: 15.57% → 40.98% (+25.41pp) 🚀
- json: 12.00% → 35.27% (+23.27pp) 🚀
- time: 18.24% → 41.89% (+23.65pp) 🚀

### Notes / Follow-ups

- **Primary Objective Achieved**: Zero failing tests (psychological "all green" milestone) ✅
- **Secondary Objective Achieved**: 40% coverage target exceeded (40.38%) ✅
- Working modules by definition: 4 → 8 (boolean, type, operators, math, validation, uuid, timer, io, hashing).
- Next cohort (17 remaining modules) targeted for v0.9.7 to push coverage above 50%.
- All 280 tests verified accurate via `TEST_ACCURACY_AUDIT_V096.md` - zero invented APIs.

---

## [0.9.5] - 2025-09-30 — Marketplace Hotfix (VS Code Extension)

### Changed

- **VS Code Marketplace**: Relabeled v0.9.4.1 as v0.9.5 for Marketplace publishing requirements
- **Extension Polish**: Proper Overview, icon, banner, screenshots, keywords, and Q&A enabled
- **Stdlib Packaging**: Wired and validated (22+ modules), MANIFEST.json added to prevent drift

### Fixed

- Marketplace presentation and stdlib packaging integrity
- Extension metadata for better discoverability

### Notes

- Core language features identical to v0.9.4.1
- JSON upgrades (RFC 7396 merge_patch, JSON Pointer, deep_update) held steady
- Deterministic testing: Windows + Python 3.12, stdlib-only coverage gate ≥85%
- Regex: explicit timeout semantics retained

---

## [0.9.4] - 2025-09-23

### 🎯 Type System MVP & Infrastructure

**Added**

- **Union Type Support**: Enhanced `@check_types` decorator with `int|str|bool` syntax parsing
- **Runtime Type Validation**: Parameter and return value type checking with clear error messages
- **Bool/Int Distinction**: Fixed Python bool-int inheritance issue for precise type validation
- **Comprehensive Test Suite**: 24 total tests including 5 new union type test cases
- **Demo Script**: `day3_union_type_demo.py` showcasing all union type functionality
- **Feature Flag Integration**: TypeCheckingConfig.enabled for performance control
- **Deterministic Packaging**: Lockfile system with generate/verify tools, SHA256 checksums
- **Enhanced Glob Support**: /\*\* pattern expansion for reliable Windows file enumeration
- **PowerShell Integration**: Improved QUICK_CHECK_LOCK.ps1 with root resolution

**Technical Implementation**

- Enhanced `TypeChecker.parse_union_type()` method for union syntax parsing
- Added `validate_single_type()` with special bool/int handling
- Extended `validate_type()` to support union type validation
- Improved error messages with parameter names and expected/actual types
- Fixed bool type matching to prevent inheritance confusion with int types

**Developer Experience**

- VS Code tasks integration for lockfile verification
- Debug environment variables for lockfile troubleshooting
- Clear error messages for type validation failures
- Working demonstration script with comprehensive examples

**Strategic Impact**

- Addresses Technical Debt: Type system runtime enforcement gap closed
- Meets 90-Day Priority: "@check_types for args/returns; 10+ tests; clear error UX"
- Foundation for Advanced Types: Extensible architecture for future enhancements

## [0.9.3] - 2025-09-14

### ♻️ Resilience & Infrastructure (No Breaking Changes)

**Added**

- Feature flag system documented (all new infra OFF by default)
- LRU + TTL in-memory cache (gated)
- Circuit breaker with error-rate threshold & half-open retry
- Micro-batching queue (time + size flush)
- Policy engine (JSON rules, deny patterns, provider allow-list)
- Performance logging (daily rotated JSONL, env dir override)
- Deterministic `ai-plan` / `ai-review` capability stubs
- CLI commands: `ai-plan`, `ai-review`, `build-info`, `doctor`, `probe`
- Default security policy template & probe diagnostics
- Optional AI extras group (`[ai]`) for heavy dependencies
- Developer extras group (`[dev]`) for tooling
- Python version raised to 3.11+ (match syntax / typing usage)

**Changed**

- Entry point now `sona.cli:main` (legacy `sona_cli` retained but not default)
- README updated (What’s New 0.9.3, badges, extras install)
- Ruff config modernized (removed deprecated top-level selects)

**Security**

- Default `.sona-policy.json` baseline with conservative operations
- Probe command surfaces potential risks / misconfiguration

**Docs**

- Added tutorial + teacher guide
- Feature flags documentation (environment variable matrix)

**Internal**

- Lazy import strategy for diagnostic commands (torch not required)
- Graceful degrade path when AI extras not installed

**No Breaking Changes**: Existing 0.9.2 user workflows continue to function unchanged with new features dormant until enabled.

**Rollback & Verification**:

- Roll back with `pip install Sona==0.9.2` (no migrations introduced).
- After install/upgrade run `sona build-info` to verify version + feature flags.
- Run `python -m pytest -q` locally; should be green to match CI matrix (3.11/3.12).

---

## [0.9.2] - 2025-09-03

### 🚀 **Version Update Release**

#### 🔧 **Core Language Updates**

- **✅ Version Synchronization** - Updated all core components to v0.9.2
- **✅ Interpreter Updates** - Enhanced interpreter with v0.9.2 compatibility
- **✅ Transpiler Updates** - Updated transpiler to v0.9.2 with improved stability
- **✅ CLI Updates** - Command-line interface updated to v0.9.2
- **✅ Type System Updates** - Type system components updated to v0.9.2

#### 🐛 **Bug Fixes**

- **✅ Version Consistency** - Resolved version inconsistencies across modules
- **✅ Package Metadata** - Updated setup.py and pyproject.toml with correct version
- **✅ Documentation Updates** - Updated README and documentation with v0.9.2 references

#### 📦 **Infrastructure Updates**

- **✅ Build System** - Updated build configuration for v0.9.2
- **✅ Cognitive Core** - Updated cognitive accessibility features to v0.9.2
- **✅ Type System** - Enhanced type system stability and version alignment

---

## [0.9.0] - 2025-08-07

All notable changes to the Sona Programming Language project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] - 2025-08-15

### 🎉 **Major Release: Development Environment**

#### 🔧 **Complete CLI System**

- **✅ NEW: 10+ Professional Commands** - Full-featured command-line interface
  - `sona run` - Execute Python and Sona files with advanced options
  - `sona repl` - Interactive REPL with cognitive enhancements
  - `sona transpile` - Multi-language transpilation (7 targets)
  - `sona format` - Code formatting with cognitive considerations
  - `sona check` - Syntax validation and error detection
  - `sona info` - Environment and dependency information
  - `sona init` - Project initialization with templates
  - `sona clean` - Intelligent file cleanup
  - `sona docs` - Documentation access
  - `sona --help` - Comprehensive help system

#### 🎨 **Enhanced VS Code Integration**

- **✅ NEW: 13 Integrated Commands** - All CLI features accessible from VS Code
- **✅ NEW: Professional Keybindings** - Efficient shortcuts for common operations
- **✅ NEW: Context Menu Integration** - Right-click access to major features
- **✅ NEW: Interactive Language Selection** - Choose from 7 transpilation targets
- **✅ IMPROVED: Command Palette** - All commands accessible via `Ctrl+Shift+P`
- **✅ IMPROVED: Terminal Integration** - Professional terminal handling

#### 🔄 **Multi-Language Transpilation System**

- **✅ NEW: 7 Target Languages** - Python, JavaScript, TypeScript, Java, C#, Go, Rust
- **✅ NEW: Advanced Transpiler** - Comprehensive syntax support
- **✅ NEW: Output Optimization** - Target-specific code generation
- **✅ NEW: Cognitive Block Extraction** - Preserves thinking patterns
- **✅ NEW: Error Recovery** - Robust transpilation error handling

#### 🧠 **Cognitive Accessibility Enhancements**

- **✅ IMPROVED: Flow State Monitoring** - Enhanced typing pattern analysis
- **✅ IMPROVED: Accessibility Themes** - ADHD, Autism, Dyslexia-friendly designs
- **✅ IMPROVED: Focus Mode** - Advanced distraction minimization
- **✅ IMPROVED: Cognitive Load Analysis** - Code complexity assessment
- **✅ IMPROVED: Error Messages** - Neurodivergent-friendly error reporting

#### 📦 **Production-Ready Infrastructure**

- **✅ NEW: Comprehensive Testing** - All major features tested
- **✅ NEW: Professional Documentation** - Complete user guides
- **✅ NEW: Error Handling** - Robust error management and recovery
- **✅ NEW: Dependency Management** - Automated dependency verification
- **✅ NEW: Cross-Platform Support** - Windows, macOS, Linux compatibility

#### 🎯 **Developer Experience Improvements**

- **✅ NEW: Project Management** - Complete project lifecycle support
- **✅ NEW: Interactive Help** - Context-aware assistance
- **✅ NEW: Professional UI** - Consistent design language
- **✅ NEW: Performance Optimization** - Faster execution and transpilation
- **✅ NEW: Comprehensive Examples** - Real-world usage examples

### 🔧 **Technical Improvements**

- **✅ IMPROVED: CLI Architecture** - Modular, extensible command system
- **✅ IMPROVED: Extension Integration** - Seamless CLI-VSCode communication
- **✅ IMPROVED: Package Structure** - Professional Python package layout
- **✅ IMPROVED: Version Synchronization** - Consistent versioning across components
- **✅ IMPROVED: Configuration Management** - Centralized settings system

### 🐛 **Bug Fixes**

- **✅ FIXED: Command Parsing** - Improved argument handling
- **✅ FIXED: File Path Resolution** - Cross-platform path handling
- **✅ FIXED: Dependency Detection** - Reliable package verification
- **✅ FIXED: Extension Commands** - Proper CLI command integration
- **✅ FIXED: Error Reporting** - Clear, actionable error messages

### 📚 **Documentation Updates**

- **✅ NEW: Installation Guide** - Step-by-step setup instructions
- **✅ NEW: CLI Reference** - Complete command documentation
- **✅ NEW: VS Code Guide** - Extension feature documentation
- **✅ NEW: Transpilation Guide** - Multi-language development guide
- **✅ NEW: Cognitive Features Guide** - Accessibility feature documentation

### 🎯 **Breaking Changes**

- **CLI Command Format**: Updated from `--repl` to `repl` for consistency
- **File Execution**: Now use `sona run file.sona` instead of `sona file.sona`
- **Package Structure**: Reorganized for better maintainability

### 🔮 **Upcoming in v0.9.0**

- Advanced debugging tools
- Web-based development environment
- Mobile development support
- AI-powered code suggestions
- Enhanced game development features

---

## [0.7.0] - 2025-07-11

### 🚀 Major Features

#### Object-Oriented Programming

- **✅ Class Definitions** - Full support for class creation with methods and properties
- **✅ Inheritance** - Complete inheritance system with method overriding
- **✅ Method Calls** - Clean dotted notation for method invocation (`object.method()`)
- **✅ Property Access** - Direct property access and assignment (`object.property = value`)
- **✅ Constructor Support** - `init` method support for object initialization

#### Dictionary Enhancements

- **✅ Dictionary Literals** - Native `{key: value}` syntax support
- **✅ Dotted Property Access** - Access dictionary values using dot notation (`dict.key`)
- **✅ Dynamic Properties** - Runtime property creation and modification
- **✅ Nested Dictionaries** - Support for complex nested data structures
- **✅ Performance Optimizations** - Faster dictionary operations and memory efficiency

#### Module System Improvements

- **✅ Enhanced Import Syntax** - Cleaner module import with better error handling
- **✅ Standard Library Expansion** - Extended built-in modules with new functionality
- **✅ Module Documentation** - Comprehensive documentation for all standard modules
- **✅ Custom Module Support** - Improved support for user-defined modules

### 🔧 Developer Experience

- **✅ Enhanced Error Messages** - More detailed error reporting with context
- **✅ Better REPL Experience** - Improved interactive shell with better completions
- **✅ Debugging Support** - Enhanced debugging capabilities and introspection
- **✅ Performance Monitoring** - Built-in performance profiling tools

### 🏗️ Infrastructure

- **✅ Code Quality** - Comprehensive code review and refactoring
- **✅ Test Coverage** - Expanded test suite covering all new features
- **✅ Documentation** - Professional documentation overhaul
- **✅ Public Release Preparation** - Sanitized codebase for public GitHub deployment

### 🐛 Bug Fixes

- Fixed class method resolution in inheritance chains
- Improved memory management for large dictionary operations
- Enhanced error handling in module imports
- Better scope management in nested function calls
- Fixed edge cases in dotted property access

### 📚 Documentation

- Complete API reference documentation
- Language guide with comprehensive examples
- Migration guide from v0.6.x to v0.7.0
- Best practices and coding standards
- Developer contribution guidelines

### ⚡ Performance Improvements

- 25% faster dictionary operations
- 15% reduction in memory usage for large programs
- Optimized module loading and caching
- Improved garbage collection for objects and dictionaries

### 🔄 Breaking Changes

- Dictionary access syntax changes (backwards compatible mode available)
- Module import path resolution improvements
- Some internal API changes for better consistency

---

## [0.6.1] - 2025-06-18

### 🎮 RPG Engine Features Added

- **✅ Fixed Variable Assignment** - `let` keyword now works properly with `var_assign` handler
- **✅ Enhanced Dictionary Access** - Improved dot notation for objects (player.hp, enemy.attack)
- **✅ Better Function Returns** - Fixed function return value assignment to variables
- **✅ Struct-like Objects** - Enhanced dictionary handling for game entities
- **✅ String Interpolation** - Better string formatting for game text
- **✅ RPG-Ready Modules** - Support for complex .smod imports for game systems
- **✅ Global Game State** - Persistent state management between functions
- **✅ Enhanced Error Messages** - Better debugging with line/column information
- **✅ Memory Management** - Improved scope handling for large RPG codebases
- **✅ Performance Optimization** - Faster execution for real-time gameplay

### New Language Features

- `let` and `const` variable declarations now work correctly
- Enhanced dotted name resolution for nested objects
- Better function parameter scope management
- Improved module import system for game components
- String interpolation for dynamic game text
- Enhanced error reporting with source location

### Bug Fixes

- Fixed variable assignment not working in functions
- Fixed function return values not being assignable
- Fixed scope resolution for function parameters
- Fixed module import path resolution
- Improved error handling for undefined variables

### RPG Game Engine Support

- Added support for player/enemy stat management
- Enhanced combat system data structures
- Morality tracking and consequence systems
- Inventory and equipment management
- Scene transition and state persistence
- AI integration for dynamic narratives

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
