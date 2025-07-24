# 🧠 Sona Programming Language v0.8.1

## Neurodivergent-First Development Environment

[![Version](https://img.shields.io/badge/version-0.8.1-blue.svg)](https://github.com/Bryantad/Sona/releases/tag/v0.8.1)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![VS Code](https://img.shields.io/badge/VS%20Code-Extension-blue.svg)](https://marketplace.visualstudio.com/items?itemName=sona-lang.sona-language-support)

Sona is a revolutionary programming language designed with cognitive accessibility at its core, making programming more accessible and enjoyable for neurodivergent developers including those with ADHD, autism, dyslexia, and other cognitive differences.

## 🎯 **What Makes Sona Special**

### **Neurodivergent-First Design**

- **Cognitive Keywords**: `think()`, `remember()`, `focus()` for natural expression
- **Flow State Monitoring**: Automatic detection and protection of hyperfocus
- **Accessibility Themes**: ADHD, autism, and dyslexia-friendly interfaces
- **Gentle Error Messages**: Supportive, non-judgmental feedback

### **Professional Development Tools**

- **Complete CLI System**: 10+ professional commands for full development workflow
- **Multi-Language Transpilation**: Convert to Python, JavaScript, TypeScript, Java, C#, Go, Rust
- **VS Code Integration**: Full IDE support with 13 integrated commands
- **Project Management**: Complete project lifecycle support

### **Cognitive Accessibility Features**

- **Working Memory Support**: External memory aids and cognitive load monitoring
- **Attention Pattern Adaptation**: System adapts to hyperfocus and burst patterns
- **Executive Function Support**: Task chunking, prioritization, and organization
- **Sensory Sensitivity Accommodation**: Reduced cognitive noise and distractions

## 🚀 **Quick Start**

### **Installation**

```bash
pip install sona
```

### **Create Your First Project**

```bash
sona init my-first-project
cd my-first-project
sona run main.sona
```

### **Your First Sona Program**

```sona
// hello.sona
function greet(name) {
    think("Creating a warm greeting for " + name);
    return "Hello, " + name + "! Welcome to accessible programming!";
}

function main() {
    remember("This is my first Sona program");
    message = greet("World");
    print(message);

    focus("I'm learning neurodivergent-first programming");
}

main();
```

### **Run Your Program**

```bash
sona run hello.sona
```

## 🔧 **Development Environment**

### **CLI Commands**

```bash
sona init <project>           # Create new project
sona run <file>               # Execute Sona or Python files
sona repl                     # Interactive REPL
sona transpile <file>         # Convert to other languages
sona format <file>            # Format code
sona check <file>             # Syntax validation
sona info                     # Environment information
sona clean                    # Clean generated files
sona docs                     # Open documentation
```

### **VS Code Extension**

Install the official VS Code extension for:

- Syntax highlighting and IntelliSense
- Right-click context menus
- Professional keybindings
- Cognitive accessibility themes
- Integrated terminal commands

## 🌈 **Cognitive Accessibility**

### **ADHD Support**

- **Hyperfocus Protection**: Automatic detection and gentle interruption
- **Attention Restoration**: Structured break suggestions
- **High Contrast Themes**: Reduced visual noise
- **Task Chunking**: Break large tasks into manageable pieces

### **Autism Support**

- **Predictable Patterns**: Consistent interface and behavior
- **Sensory Considerations**: Calming colors and reduced animations
- **Clear Structure**: Logical, hierarchical organization
- **Routine Support**: Familiar workflows and commands

### **Dyslexia Support**

- **Readable Fonts**: Dyslexia-friendly typography
- **Color Coding**: Meaningful use of color for comprehension
- **Clear Spacing**: Improved visual separation
- **Audio Feedback**: Optional verbal confirmation

## 🔄 **Multi-Language Support**

Transpile your Sona code to:

### **Web Development**

```bash
sona transpile app.sona --target javascript
sona transpile app.sona --target typescript
```

### **Backend Development**

```bash
sona transpile server.sona --target python
sona transpile server.sona --target java
sona transpile server.sona --target csharp
```

### **Systems Programming**

```bash
sona transpile system.sona --target go
sona transpile system.sona --target rust
```

## 📚 **Documentation**

### **Getting Started**

- [Installation Guide](docs/installation.md)
- [Quick Start Tutorial](docs/quickstart.md)
- [Language Reference](docs/language-reference.md)
- [Cognitive Features Guide](docs/cognitive-features.md)

### **Advanced Features**

- [CLI Command Reference](docs/cli-reference.md)
- [VS Code Extension Guide](docs/vscode-extension.md)
- [Multi-Language Transpilation](docs/transpilation.md)
- [Accessibility Features](docs/accessibility.md)

### **Developer Resources**

- [Contributing Guide](CONTRIBUTING.md)
- [API Documentation](docs/api.md)
- [Extension Development](docs/extension-dev.md)

## 💡 **Examples**

### **Cognitive Syntax**

```sona
// Natural language patterns
when user_clicks_button {
    think("User wants to submit the form");
    remember("Validate input before processing");
    focus("Form validation is critical");
}

// Working memory support
working_memory {
    current_task = "Processing user input";
    next_steps = ["validate", "process", "respond"];
    cognitive_load = "medium";
}
```

### **Traditional Syntax**

```sona
// Familiar programming patterns
function process_data(input) {
    if (input.length > 0) {
        return input.map(item => item * 2);
    }
    return [];
}

class DataProcessor {
    constructor() {
        this.data = [];
    }

    add(item) {
        this.data.push(item);
    }
}
```

## 🎯 **Who Is This For?**

### **Neurodivergent Developers**

- Experience programming designed for your cognitive style
- Reduce cognitive load and mental fatigue
- Access tools that adapt to your attention patterns
- Join a community that understands your needs

### **Educators & Students**

- Teach programming with cognitive accessibility in mind
- Provide inclusive learning environments
- Access resources designed for diverse learning styles
- Support students with different cognitive needs

### **Professional Teams**

- Build inclusive development environments
- Support neurodivergent team members
- Access powerful multi-language development tools
- Improve team productivity and satisfaction

## 🤝 **Community & Support**

### **Getting Help**

- 📖 **Documentation**: Comprehensive guides and references
- 🐛 **Issues**: Report bugs on GitHub Issues
- 💬 **Discussions**: Join our GitHub Discussions
- 📧 **Email**: Contact us at info@waycore.com

### **Contributing**

We welcome contributions from everyone! See our [Contributing Guide](CONTRIBUTING.md) for:

- 🐛 Bug reports and fixes
- 💡 Feature suggestions
- 📖 Documentation improvements
- 🌍 Translations and internationalization
- 🎨 Accessibility theme development

## 📄 **License**

Sona is open source software licensed under the [MIT License](LICENSE).

## 🙏 **Acknowledgments**

Special thanks to:

- **The Neurodivergent Community**: For guidance on accessibility features
- **Cognitive Accessibility Researchers**: For evidence-based design principles
- **Open Source Contributors**: For feedback and improvements
- **VS Code Team**: For excellent extension APIs
- **Python Community**: For the foundation this project builds upon

---

**🎯 Ready to experience neurodivergent-first programming?**

```bash
pip install sona
sona init my-accessible-project
cd my-accessible-project
sona run main.sona
```

**Join us in making programming accessible for everyone! 🚀**

## What's New in 0.8.0

### 🎉 Unified Syntax Support

Version 0.8.0 introduces a unified syntax system that supports both traditional programming patterns and cognitive accessibility features:

- **Traditional syntax**: Familiar programming patterns (`print`, `function`, `if`, `for`)
- **Cognitive syntax**: Neurodivergent-friendly syntax (`think`, `show`, `when`, `repeat`)

Both syntax styles can be used interchangeably, allowing users to choose the approach that works best for them.

### Documentation

- [Unified Syntax Guide](docs/unified_syntax_guide.md) - Comprehensive guide to using both syntax styles
- [Cognitive Syntax Examples](tests/test_cognitive_syntax.sona) - Examples using cognitive syntax
- [Traditional Syntax Examples](tests/test_traditional_syntax.sona) - Examples using traditional syntax

## Getting Started

```bash
# Run a Sona program
python sona/sona_unified_cli.py my_program.sona

# Interactive mode
python sona/sona_unified_cli.py

# Run tests
python test_unified_interpreter.py
```

## Cognitive Syntax Example

```
# Variable assignment
name = "Sona"

# Output
think "Hello from " + name
show "Welcome to " + name

# Function definition
when add_numbers(a, b) {
    return a + b
}

# Conditional
when x > 5 {
    think "x is greater than 5"
}

# Loop
repeat 3 times {
    think "Looping..."
}
```

## Traditional Syntax Example

```
# Variable assignment
name = "Sona"

# Output
print("Hello from " + name)
display("Welcome to " + name)

# Function definition
function add_numbers(a, b) {
    return a + b
}

# Conditional
if x > 5 {
    print("x is greater than 5")
}

# Loop
for i in range(3) {
    print("Looping...")
}
```

## Contributing

Contributions are welcome! See [Contributing.md](Contributing.md) for details.

## License

Sona is open source software licensed under the MIT license.
