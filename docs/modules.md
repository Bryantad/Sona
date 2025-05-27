# Sona Module System

This document covers the module system in Sona v0.5.1, including both standard library modules and the new native function bridging system.

## Module Architecture

Modules in Sona use a combined approach with two file types:

- `.smod` files: Sona Module Definition Files - contain public API and function definitions
- Native bindings: Python implementation files in the interpreter that provide the underlying functionality

### Native Function Integration

Sona's module system now supports native function calls through the `__native__` namespace. These functions act as a bridge between Sona code and the underlying Python implementation.

#### How Native Functions Work

1. Modules define function signatures in `.smod` files
2. Function implementations call into `__native__` namespace functions
3. The interpreter maps these calls to the corresponding Python functions

For example, the `fs.exists` function in `fs.smod` is defined as:

```sona
func exists(path) {
    return __native__.fs_exists(path)
}
```

## File System Module (fs.smod)

The file system module provides functionality to work with files and directories:

```sona
import fs.smod

# Check if file exists
fs.exists("path/to/file")

# Read from a file
let content = fs.read_file("example.txt")

# Write to a file
fs.write_file("output.txt", "Hello, Sona!")

# Create a directory
fs.makedirs("new_directory")

# List directory contents
let files = fs.listdir(".")
```

## HTTP Module (http.smod)

The HTTP module provides functions for making web requests:

```sona
import http.smod

# Make a GET request
let response = http.get("https://example.com")

# Make a POST request with data
let data = {"name": "Sona", "version": "0.5.1"}
let post_response = http.post("https://example.com/api", data)
```

## Console Module

The console module provides functions for terminal manipulation including:

- Cursor positioning and visibility
- Color text output
- Screen clearing
- Box drawing and area filling
- Cross-platform support (Windows and ANSI-compatible terminals)

### Usage Example

```sona
import console from "stdlib/console"

# Hide cursor and clear screen
console.hide_cursor()
console.clear()

# Draw colored text
console.move_cursor(5, 5)
console.write("Hello", "green")

# Draw a box with title
console.draw_box(10, 3, 40, 10, "Game Window")

# Fill an area
console.fill_area(12, 5, 36, 6, ".")

# Get terminal size
width, height = console.get_terminal_size()
console.move_cursor(0, height - 1)
console.write("Terminal size: " + width + "x" + height)

# Reset
console.show_cursor()
```

## Stdin Module

The stdin module provides non-blocking input functions:

- `read_key(timeout_ms)`: Read a key with timeout (returns empty string if no key pressed)
- `readline()`: Read a full line of input

### Usage Example

```sona
import stdin from "stdlib/stdin"

# Non-blocking input with 100ms timeout
let key = stdin.read_key(100)
if key == "q" {
    # Handle quit
}

# Blocking input
let name = stdin.readline()
```

## Platform Compatibility

Both modules are designed for cross-platform compatibility:

- **Windows**: Uses Win32 console API
- **Unix/macOS**: Uses ANSI escape sequences

## Example Applications

- Snake Game: `examples/games/snake_game.sona`
