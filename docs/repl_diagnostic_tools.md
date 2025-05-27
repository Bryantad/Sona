# Sona REPL Diagnostic Tools

This document describes the advanced developer tools added to Sona REPL v0.5.1 that support real-time runtime inspection and debugging.

## Overview

The Sona REPL now includes several commands that help developers understand and debug their Sona code:

- `:debug` - Show last error and parse tree
- `:profile` - Measure execution time of the last command
- `:watch <var>` - Print live value of a specific variable
- `:apps` - List available REPL tools
- `:run <tool>` - Run a specific REPL tool
- `:trace` - Toggle tracing of function calls and returns

## Detailed Description

### Debug Command (`:debug`)

The `:debug` command shows comprehensive information about the most recent code execution:

- The last interpreter error or syntax failure
- A pretty-printed visualization of the latest parse tree
- All currently visible variable scopes

Example usage:

```
sona> let x = 10
sona> :debug
[DEBUG INFO]
Last Error: None

Last Parse Tree:
start
  var_assign
    x
    number	10

Env Scope:
Global scope:
x = 10
```

### Profile Command (`:profile`)

The `:profile` command measures and displays the execution time of the most recent command:

```
sona> func fibonacci(n) { if n <= 1 { return n } return fibonacci(n-1) + fibonacci(n-2) }
sona> fibonacci(10)
55
sona> :profile
[PROFILE] Last command took 12.48ms
That's a reasonable execution time.
```

### Watch Command (`:watch <var>`)

The `:watch` command displays the current value of a specified variable, along with its type and scope information:

```
sona> let counter = 5
sona> function increment() { counter = counter + 1 }
sona> increment()
sona> :watch counter
[WATCH] counter = 6 (type: int) [scope: global]
```

### Trace Command (`:trace`)

The `:trace` command toggles function call tracing, which logs all function calls and returns:

```
sona> :trace
[TRACE] Function call tracing is now enabled
Example trace output:
  [TRACE] Calling function 'square' with args: [5]
  [TRACE] Returned from 'square': 25
Run any Sona code with function calls to see the trace.
sona> func square(x) { return x * x }
sona> square(5)
[TRACE] Calling function 'square' with args: [5]
[TRACE] Returned from 'square': 25
25
```

## Implementation Notes

- All diagnostic data is stored in a shared `debug_state` dictionary in the REPL
- Tracing is implemented by temporarily patching the `func_call` method in the interpreter
- Profiling uses Python's high-precision `time.perf_counter()` for accurate timing
- The parse tree visualization uses Lark's built-in pretty printing when available

## Environment Variables

- `SONA_DEBUG=1` - Enable debug mode for Sona interpreter (shows internal debug logs)

## Developer Tools Module

The tools are also available in a standalone module at `sona/utils/debug_tools.py`, which can be imported for use in scripts or custom tools:

```python
from sona.utils.debug_tools import run_code_with_trace, run_with_profiling, watch_variable, print_debug_info
```

## Compatibility

These tools are designed to be minimally intrusive to the existing REPL flow and compatible with all standard Sona language features in v0.5.1.

## REPL Tools

Sona v0.5.1+ includes a collection of production-grade utility tools that can be loaded and run directly from the REPL. These tools are written in pure Sona syntax and showcase practical functionality for developers.

### Available Tools

- **api_formatter**: Pretty-prints and validates JSON data with path extraction capabilities
- **color_picker**: Converts between RGB/HEX/HSL colors and provides color manipulation functions
- **markdown_preview**: Converts Markdown to HTML with support for headings, lists, and other elements
- **password_generator**: Creates secure passwords with custom settings and strength evaluation
- **task_manager**: Manages to-do lists with add/list/complete functionality and task priorities
- **time_tracker**: Tracks time spent on tasks with start/stop/pause functionality
- **unit_converter**: Converts between temperature, length, weight, and volume units

### Using REPL Tools

To use these tools in the Sona REPL:

1. List available tools:

   ```
   sona> :apps
   ```

2. Run a specific tool:

   ```
   sona> :run <tool_name>
   ```

   Example:

   ```
   sona> :run unit_converter
   ```

3. Each tool provides its own `show_help()` function for usage information.

### Creating Custom REPL Tools

You can create your own REPL tools by adding new `.sona` files to the `examples/repl_tools` directory. Include a description comment at the top:

```sona
// Description: Brief description of what your tool does
```

Implement a `show_help()` function to display usage information. Your tool will automatically appear in the `:apps` list and be available via the `:run` command.
