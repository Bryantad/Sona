# Sona Programming Language v0.7.0

![Version](https://img.shields.io/badge/version-0.7.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Language](https://img.shields.io/badge/language-Python-yellow.svg)

Sona is a modern, interpreted programming language featuring object-oriented programming, advanced dictionary operations, and an intuitive module system. Designed for readability and ease of use, Sona combines familiar syntax with powerful features.

## ✨ Key Features

### Object-Oriented Programming

- **Classes and Inheritance**: Full support for class definitions, method calls, and inheritance chains
- **Property Access**: Clean dotted notation for accessing object properties and methods
- **Method Calls**: Intuitive syntax for calling methods on objects

### Advanced Dictionary Support

- **Dictionary Literals**: Create dictionaries with `{key: value}` syntax
- **Dotted Property Access**: Access dictionary values using dot notation (`dict.property`)
- **Dynamic Properties**: Set and get properties dynamically at runtime

### Enhanced Module System

- **Dotted Imports**: Import modules with clean dotted notation
- **Standard Library**: Rich collection of built-in modules for common operations
- **Custom Modules**: Easy creation and sharing of custom module files

### Developer-Friendly Features

- **Interactive REPL**: Full-featured read-eval-print loop for rapid development
- **Detailed Error Messages**: Comprehensive error reporting with line/column information
- **Cross-Platform**: Runs on Windows, macOS, and Linux

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

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

## 📚 Quick Start

### GUI Interface (Recommended for New Users)

```bash
# Clone and run with graphical interface
git clone https://github.com/Bryantad/Sona.git
cd Sona
python launcher.py
```

The GUI launcher provides:

- 📁 **Example Browser** - Browse and run all Sona examples
- 💻 **Interactive REPL** - Test code snippets in real-time
- 🎮 **Embedded Apps** - Run games and demos directly in the interface
- 📝 **Code Editor** - View and edit Sona files with syntax highlighting

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

- `dictionary_operations.sona` - Advanced dictionary usage
- `module_system.sona` - Module import and usage patterns
- `object_oriented.sona` - Class definitions and inheritance
- `basic_features.sona` - Core language functionality

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

- **Enhanced OOP Support**: Improved class syntax and inheritance mechanisms
- **Dictionary Enhancements**: Better performance and cleaner syntax for dictionary operations
- **Module System Improvements**: More intuitive import syntax and better standard library organization
- **Developer Experience**: Enhanced error messages and debugging capabilities
- **Performance Optimizations**: Faster execution and reduced memory usage

## 🤝 Contributing

We welcome contributions from the community! Please read our [Contributing Guidelines](Contributing.md) for details on:

- Code of conduct
- Development workflow
- Coding standards
- Testing requirements
- Pull request process

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Documentation**: [docs/](docs/)
- **Examples**: [examples/](examples/)
- **Issues**: [GitHub Issues](https://github.com/Bryantad/Sona/issues)
- **Releases**: [GitHub Releases](https://github.com/Bryantad/Sona/releases)

---

**Happy coding with Sona! 🎵**
