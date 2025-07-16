# 🧠 Sona Programming Language v0.8.0

## Neurodivergent-First Development Environment

[![Version](https://img.shields.io/badge/version-0.8.0-blue.svg)](https://github.com/Bryantad/Sona/releases/tag/v0.8.0)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![VS Code](https://img.shields.io/badge/VS%20Code-Extension-blue.svg)](https://marketplace.visualstudio.com/items?itemName=sona-lang.sona-language-support)

Sona is a revolutionary programming language designed with cognitive accessibility at its core, making programming more accessible and enjoyable for neurodivergent developers including those with ADHD, autism, dyslexia, and other cognitive differences.

---

## 🎯 What Makes Sona Special

### Neurodivergent-First Design

* `think()`, `remember()`, `focus()` cognitive keywords
* Flow state monitoring and hyperfocus protection
* ADHD, autism, and dyslexia-friendly UI
* Gentle, supportive error messages

### Professional Development Tools

* Full CLI toolchain with 10+ commands
* Transpile to Python, JS, TS, Java, C#, Go, Rust
* Complete VS Code integration (13 commands)
* Full project lifecycle support

### Accessibility Features

* Working memory & executive function aids
* Adaptive attention and sensory load tools
* Minimal distractions and structured UI
* High contrast themes, readable fonts

---

## 🚀 Quick Start

### Installation

```bash
pip install sona
```

### Create and Run Your First Project

```bash
sona init my-project
cd my-project
sona run main.sona
```

### Example Program

```sona
function greet(name) {
    think("Creating greeting for " + name);
    return "Hello, " + name + "! Welcome to Sona!";
}

function main() {
    remember("My first Sona program");
    message = greet("World");
    print(message);
    focus("Learning accessible programming");
}

main();
```

---

## 🔧 CLI Toolchain

```bash
sona init <project>       # Create new project
sona run <file>           # Execute Sona or Python files
sona repl                 # Launch REPL
sona transpile <file>     # Convert to other languages
sona format <file>        # Code formatting
sona check <file>         # Syntax check
sona info                 # Show environment info
sona clean                # Remove cache & gen files
sona docs                 # View documentation
```

---

## 🎨 VS Code Extension

* Syntax highlighting, IntelliSense
* Right-click & Command Palette access
* Neurodivergent-friendly themes
* Full CLI integration inside editor

---

## 🌈 Accessibility Support

### ADHD

* Gentle break reminders, high-contrast UI
* Task chunking and hyperfocus protection

### Autism

* Predictable interface, low sensory noise
* Consistent routines and familiar structure

### Dyslexia

* Readable fonts, visual spacing
* Meaningful color coding

---

## 📆 Multi-Language Transpilation

### Web

```bash
sona transpile app.sona --target javascript
sona transpile app.sona --target typescript
```

### Backend

```bash
sona transpile server.sona --target python
sona transpile server.sona --target java
sona transpile server.sona --target csharp
```

### Systems

```bash
sona transpile system.sona --target go
sona transpile system.sona --target rust
```

---

## 📖 Documentation

### Getting Started

* [Installation Guide](docs/installation.md)
* [Quick Start](docs/quickstart.md)
* [Language Reference](docs/language-reference.md)
* [Cognitive Features](docs/cognitive-features.md)

### Advanced Topics

* [CLI Command Reference](docs/cli-reference.md)
* [VS Code Extension](docs/vscode-extension.md)
* [Transpilation Guide](docs/transpilation.md)
* [Accessibility](docs/accessibility.md)

### Developer Resources

* [Contributing](CONTRIBUTING.md)
* [API Docs](docs/api.md)
* [Extension Dev](docs/extension-dev.md)

---

## 📚 Examples

### Cognitive Syntax

```sona
when user_clicks_button {
    think("User clicked");
    remember("Validate input");
    focus("Process form");
}

working_memory {
    current_task = "Validate input";
    next_steps = ["check", "submit"];
    cognitive_load = "medium";
}
```

### Traditional Syntax

```sona
function process(input) {
    if (input.length > 0) {
        return input.map(x => x * 2);
    }
    return [];
}

class Processor {
    constructor() { this.data = []; }
    add(item) { this.data.push(item); }
}
```

---

## 🎯 Who Should Use Sona?

### Neurodivergent Developers

* Designed for your cognitive strengths
* Reduce fatigue and improve clarity

### Educators

* Teach with inclusive tools
* Ideal for diverse classrooms

### Teams & Orgs

* Build neuroinclusive pipelines
* Improve team well-being and productivity

---

## 🤝 Community & Contribution

### Get Help

* [GitHub Issues](https://github.com/Bryantad/Sona/issues)
* [Discussions](https://github.com/Bryantad/Sona/discussions)
* [inquire@waycore.com](mailto:inquire@waycore.com)

### Contribute

* Bug reports & fixes
* Feature suggestions
* Docs & translation
* Theme development

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## 📄 License

Sona is licensed under the [MIT License](LICENSE).

---

## 🙏 Acknowledgments

* Neurodivergent communities
* Cognitive UX researchers
* VS Code & Python ecosystems
* All open-source contributors

---

```bash
# Try it now!
pip install sona
sona init my-accessible-project
cd my-accessible-project
sona run main.sona
```
