# Sona v0.5.1 Release Notes

**Release Date: May 23, 2025**

## Overview

Sona v0.5.1 introduces powerful diagnostic tools to the REPL environment, making it easier than ever for developers to debug their Sona applications. This update also addresses critical function parameter handling issues and includes various bug fixes to improve language stability.

## New Features

### Advanced REPL Diagnostic Tools

The Sona REPL now includes a comprehensive suite of developer tools:

1. **`:debug` Command**

   - Displays the last error message with detailed context
   - Shows a visualization of the parse tree for the last executed command
   - Lists all variable scopes with their current values

2. **`:profile` Command**

   - Measures and displays execution time of commands
   - Provides context on performance characteristics

3. **`:watch <var>` Command**

   - Inspects variable values in real-time
   - Shows type information and scope location

4. **`:trace` Command**
   - Toggles function call tracing
   - Logs all function calls with arguments and return values
   - Helps understand program flow and execution

## Bug Fixes

1. **Function Parameter Handling**

   - Fixed scope handling to ensure parameters are correctly accessed within function bodies
   - Prevented global variable shadowing issues in nested functions

2. **Type Consistency**

   - Improved numeric type handling in if/else statements
   - Fixed inconsistent conversion between integers and floats
   - Ensured string concatenation returns the correct types

3. **Control Flow Improvements**
   - Fixed loop body execution in while statements
   - Enhanced block handling across control structures

## Documentation

- Added comprehensive documentation for the new diagnostic tools
- Created a reusable debug tools module for programmatic access
- Updated help command with information about the new features

## Compatibility

This release maintains full compatibility with Sona v0.5.0 code and modules.

## Next Steps

For full details on how to use the new diagnostic tools, see the documentation in `docs/repl_diagnostic_tools.md`.

## Contributors

Thanks to everyone who contributed to making this release possible.
