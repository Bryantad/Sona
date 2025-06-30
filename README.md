# Sona Programming Language v0.7.1

![Version](https://img.shields.io/badge/version-0.7.1-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Language](https://img.shields.io/badge/language-Python-yellow.svg)
![Performance](https://img.shields.io/badge/performance-6.5K%20ops/sec-green.svg)

Sona is a modern, high-performance interpreted programming language featuring object-oriented programming, advanced dictionary operations, and an intuitive module system. With major performance improvements in v0.7.1 and experimental type system features, Sona combines familiar syntax with powerful capabilities for production-ready applications.

## ✨ Key Features

### Object-Oriented Programming

-   **Classes and Inheritance**: Full support for class definitions, method calls, and inheritance chains
-   **Property Access**: Clean dotted notation for accessing object properties and methods
-   **Method Calls**: Intuitive syntax for calling methods on objects

### Advanced Dictionary Support

-   **Dictionary Literals**: Create dictionaries with `{key: value}` syntax
-   **Dotted Property Access**: Access dictionary values using dot notation (`dict.property`)
-   **Dynamic Properties**: Set and get properties dynamically at runtime

### Enhanced Module System

-   **Dotted Imports**: Import modules with clean dotted notation
-   **Standard Library**: Rich collection of built-in modules for common operations
-   **Custom Modules**: Easy creation and sharing of custom module files

### Developer-Friendly Features

-   **Interactive REPL**: Full-featured read-eval-print loop for rapid development
-   **Detailed Error Messages**: Comprehensive error reporting with line/column information
-   **Cross-Platform**: Runs on Windows, macOS, and Linux

## ⚡ Performance & New Features (v0.7.1)

### 🚀 Major Performance Improvements

-   **650x Performance Boost**: Critical interpreter bottleneck fixed
-   **Production-Ready Speed**: Average 5,282 operations per second
-   **Comprehensive Benchmarking**: Performance metrics and monitoring tools included

### 🧪 Experimental Type System (Preview)

-   **Type Inference**: Basic static type checking and inference (experimental)
-   **Type-Aware Interpreter**: Enhanced development experience with optional typing
-   **Future-Ready**: Foundation for advanced type system in v0.8.0

### 📊 Performance Metrics

-   Integer Arithmetic: **6,106 ops/sec**
-   String Operations: **9,847 ops/sec**
-   Function Calls: **1,981 ops/sec**
-   Variable Assignment: **4,139 ops/sec**

> **Backward Compatibility**: All existing Sona code works unchanged. Experimental features are optional and disabled by default.

## 📚 Documentation & Wiki

📖 **[Complete Sona Wiki](docs/Sona.wiki/)** - Comprehensive guides, tutorials, and references

-   [Getting Started Guide](docs/Sona.wiki/Home.md)
-   [Performance Optimization](docs/Sona.wiki/Chapter-13-Language-Internals-and-Advanced-Optimization.md)
-   [Advanced Language Features](docs/Sona.wiki/Chapter-10-Advanced-Language-Features.md)
-   [v0.7.1 Performance Guide](docs/Sona.wiki/Performance-Guide-v0.7.1.md) _(New)_
-   [Experimental Type System](docs/Sona.wiki/Type-System-Preview.md) _(New)_

## 🚀 Installation

### Prerequisites

-   Python 3.8 or higher
-   pip package manager

### Install from PyPI

```bash
pip install sona
```

### Install from Source

```bash
git clone https://github.com/Bryantad/Sona.git
cd Sona
pip install -e .
```

### Verify Installation

```bash
sona --version
```

### Verify Performance (v0.7.1)

```bash
# Test the major performance improvements
python performance_baseline_fixed.py

# Expected output:
# ✅ Sona v0.7.1 Performance Baseline
# Integer Arithmetic: 6,106 ops/sec
# String Operations: 9,847 ops/sec
# Function Calls: 1,981 ops/sec
# Variable Assignment: 4,139 ops/sec
# Average Performance: 5,282 ops/sec
```

## 📚 Quick Start

### GUI Interface (Recommended for New Users)

```bash
# Clone and run with graphical interface
git clone https://github.com/Bryantad/Sona.git
cd Sona
python launcher.py
```

The GUI launcher provides:

-   📁 **Example Browser** - Browse and run all Sona examples
-   💻 **Interactive REPL** - Test code snippets in real-time
-   🎮 **Embedded Apps** - Run games and demos directly in the interface
-   📝 **Code Editor** - View and edit Sona files with syntax highlighting

For the enhanced modern interface, install PySide6:

```bash
pip install PySide6
python launcher.py
```

### Command Line Interface

```bash
# Run Sona files directly
python -m sona examples/hello_world.sona

# Start interactive REPL
python -m sona

# Get help
python -m sona --help
```

### Basic Syntax Examples

#### Variables and Functions

```sona
// Variables and basic operations
let name = "Sona"
let version = 0.7

func greet(user) {
    return "Welcome to " + name + " v" + str(version) + ", " + user + "!"
}

print(greet("Developer"))
```

#### Object-Oriented Programming

```sona
class Person {
    func init(name, age) {
        self.name = name
        self.age = age
    }

    func introduce() {
        return "Hi, I'm " + self.name + " and I'm " + str(self.age) + " years old."
    }
}

let person = Person("Alice", 30)
print(person.introduce())
```

### 🧪 Experimental Features (v0.7.1)

#### Type-Aware Interpreter (Optional)

```python
# Access experimental type system features
from sona.type_aware_interpreter import TypeAwareSonaInterpreter

# Create type-aware interpreter
interpreter = TypeAwareSonaInterpreter(
    strict_typing=False,  # Gradual typing
    enable_type_optimizations=True
)

# Get performance statistics
stats = interpreter.get_type_statistics()
print(f"Type optimizations applied: {stats['type_optimizations_applied']}")
```

#### Performance Benchmarking

```bash
# Run comprehensive performance tests
python -c "
from sona.type_aware_interpreter import TypeAwareSonaInterpreter
import time

interpreter = TypeAwareSonaInterpreter(enable_type_optimizations=True)
start = time.time()
# ... run your Sona code ...
duration = time.time() - start
print(f'Execution time: {duration:.4f} seconds')
"
```

#### Dictionary Operations

```sona
// Dictionary literals with dotted access
let config = {
    app_name: "My App",
    version: "1.0.0",
    debug: true
}

print("Running " + config.app_name + " v" + config.version)

// Dynamic property setting
config.environment = "production"
```

#### Module System

```sona
import math
import string

let result = math.sqrt(25)
print("Square root: " + str(result))

let text = "hello world"
print("Capitalized: " + string.capitalize(text))
```

## 📖 Language Guide

### Control Flow

```sona
// Conditional statements
if (condition) {
    // code
} else if (other_condition) {
    // code
} else {
    // code
}

// Pattern matching
match value {
    case 1: print("One")
    case 2: print("Two")
    default: print("Other")
}

// Loops
for (let i = 0; i < 10; i += 1) {
    print(i)
}

while (condition) {
    // code
}
```

### Error Handling

```sona
try {
    // risky code
} catch (error) {
    print("Error occurred: " + str(error))
}
```

## 🧪 Examples

Explore the `examples/` directory for comprehensive code samples:

-   `dictionary_operations.sona` - Advanced dictionary usage
-   `module_system.sona` - Module import and usage patterns
-   `object_oriented.sona` - Class definitions and inheritance
-   `basic_features.sona` - Core language functionality

## 🎯 What's New in v0.7.1

### Major Improvements

✅ **650x Performance Boost** - Critical interpreter bottleneck fixed
✅ **Production-Ready Speed** - Average 5,282 operations per second
✅ **Experimental Type System** - Preview of v0.8.0 type inference features
✅ **Enhanced Development Tools** - Performance monitoring and benchmarking
✅ **100% Backward Compatibility** - All existing code works unchanged

### Performance Comparison

| Operation           | v0.7.0      | v0.7.1        | Improvement     |
| ------------------- | ----------- | ------------- | --------------- |
| Integer Arithmetic  | ~10 ops/sec | 6,106 ops/sec | **610x faster** |
| String Operations   | ~10 ops/sec | 9,847 ops/sec | **984x faster** |
| Function Calls      | ~10 ops/sec | 1,981 ops/sec | **198x faster** |
| Variable Assignment | ~10 ops/sec | 4,139 ops/sec | **413x faster** |

### Experimental Features

-   **Type Inference Engine**: Basic static type checking (optional)
-   **Type-Aware Interpreter**: Enhanced development experience
-   **Performance Optimizations**: Type-guided code optimizations
-   **Future Foundation**: Infrastructure for v0.8.0 advanced type system

> **Note**: Experimental features are completely optional and don't affect existing Sona code. Enable them only if you want to preview upcoming v0.8.0 features.

## 🔧 Development

### Setting Up Development Environment

```bash
git clone https://github.com/Bryantad/Sona.git
cd Sona
pip install -e .[dev]
```

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

We follow PEP 8 guidelines. Format code using:

```bash
black sona/
```

## 📋 Version 0.7.0 Highlights

-   **Enhanced OOP Support**: Improved class syntax and inheritance mechanisms
-   **Dictionary Enhancements**: Better performance and cleaner syntax for dictionary operations
-   **Module System Improvements**: More intuitive import syntax and better standard library organization
-   **Developer Experience**: Enhanced error messages and debugging capabilities
-   **Performance Optimizations**: Faster execution and reduced memory usage

## 🤝 Contributing

We welcome contributions from the community! Please read our [Contributing Guidelines](Contributing.md) for details on:

-   Code of conduct
-   Development workflow
-   Coding standards
-   Testing requirements
-   Pull request process

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

-   **Documentation**: [docs/](docs/)
-   Standalone Transpiler: (https://github.com/Bryantad/Sona-Transpiler.git)
-   **Examples**: [examples/](examples/)
-   **Issues**: [GitHub Issues](https://github.com/Bryantad/Sona/issues)
-   **Releases**: [GitHub Releases](https://github.com/Bryantad/Sona/releases)

---

**Happy coding with Sona! 🎵**
