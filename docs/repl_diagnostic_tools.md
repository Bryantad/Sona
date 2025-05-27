# Sona REPL Diagnostic Tools

This document describes the advanced developer tools added to Sona REPL v0.5.1 that support real-time runtime inspection and debugging.

## Overview

The Sona REPL now includes several commands that help developers understand and debug their Sona code:

- `:debug` - Show last error and parse tree
- `:profile` - Measure execution time of the last command
- `:watch <var>` - Print live value of a specific variable
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
