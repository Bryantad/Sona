# Sona v0.5.0 - Quick Start Guide

## Installation

1. **Clone or download** the Sona repository

2. **Install dependencies**:

   ```bash
   cd sona_core
   python3.10 tools/install.py
   ```

   For a virtual environment:

   ```bash
   python3.10 tools/install.py --venv
   source venv/bin/activate  # On Linux/macOS
   ```

3. **Verify installation**:
   ```bash
   python3.10 -m sona.sona_cli -c "print('Hello from Sona!')"
   ```

## Running Sona Programs

### Command Line

Run a Sona file:

```bash
python3.10 -m sona.sona_cli path/to/file.sona
```

### Interactive REPL

Start the interactive REPL:

```bash
python3.10 -m sona.repl
```

Type Sona code directly. Press Enter twice to execute.

## Language Features

### Basic Syntax

```sona
// Comments start with double slash

// Variables
let name = "Sona"
const VERSION = "0.5.0"

// Printing
print("Hello, " + name + "!")

// Conditionals
if name == "Sona" {
    print("This is Sona v" + VERSION)
} else {
    print("Unknown language")
}

// Loops
let i = 0
while i < 5 {
    print("Count: " + i)
    i = i + 1
}

// For loops
for j in 0..5 {
    print("Iteration " + j)
}
```

### Functions

```sona
// Function definition
func greet(name) {
    return "Hello, " + name + "!"
}

// Function call
print(greet("User"))
```

### NEW: Multi-line Strings (v0.5.0)

```sona
let message = """
Welcome to Sona v0.5.0!
This is a multi-line string
that preserves whitespace and formatting.
"""

print(message)
```

### NEW: Import Aliasing (v0.5.0)

```sona
// Import with alias
import utils.math.smod as math

print("PI = " + math.to_str(math.PI))
print("Square root of 16: " + math.to_str(math.sqrt(16)))
```

## Examples

Try running the included examples:

```bash
# Hello World
python3.10 -m sona.sona_cli examples/hello_world.sona

# Calculator
python3.10 -m sona.sona_cli examples/calculator.sona

# More examples in the examples/ directory
```

## Testing

Run the test suite:

```bash
python3.10 tools/run_tests.py
```

## Getting Help

- Check `docs/syntax_guide.md` for language reference
- Look at examples in the `examples/` directory
- Read the `RELEASE_NOTES_v0.5.0.md` file for detailed feature information
