# Sona v0.5.1 Release

## Major Highlights

- **Advanced REPL Diagnostic Tools** - New commands for debugging, profiling, variable watching, and function tracing
- **Fixed Function Parameter Handling** - Resolved critical issues with function parameter scoping
- **Improved Project Organization** - Better directory structure and file organization
- **Enhanced Documentation** - Comprehensive documentation for new features

## REPL Diagnostic Tools

The highlight of this release is a comprehensive suite of REPL diagnostic tools:

- **`:debug`** - Shows last error and parse tree
- **`:profile`** - Measures execution time
- **`:watch <var>`** - Displays variable values
- **`:trace`** - Toggles function call tracing

## Bug Fixes

This release addresses several critical bugs:

- Fixed function parameter scope handling
- Fixed numeric type handling in if/else statements
- Fixed loop body execution in while statements
- Improved error reporting with more context

## Project Organization

The codebase has been reorganized for better maintainability:

- Structured directories for development files
- Organized test files into appropriate categories
- Comprehensive directory documentation
- Release tools directory with cleanup and deployment scripts

## Documentation

- Added detailed documentation for the new diagnostic tools
- Created a reusable debug tools module
- Added directory-specific README files explaining the project structure
- Updated main documentation to reflect the new organization

## Security Improvements

- Fixed function parameter scope handling to prevent variable shadowing issues
- Added validation checks for module imports to prevent path traversal
- Implemented input size limits to prevent DoS attacks

## Getting Started

```bash
git clone https://github.com/Bryantad/Sona.git
cd Sona
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
sona --version
```

For full documentation on the new diagnostic tools, see `docs/repl_diagnostic_tools.md`.

For information about the project organization changes, see `docs/PROJECT_ORGANIZATION.md`.
