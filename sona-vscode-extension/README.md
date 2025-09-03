# Sona Language Support for VS Code

![Sona Logo](https://raw.githubusercontent.com/Bryantad/Sona/main/docs/sona-logo.png)

Official VS Code extension for the **Sona Programming Language v0.9.2** - A neurodivergent-first programming language designed for accessibility, cognitive support, and multi-language transpilation.

## ✨ Features

### 🧠 Neurodivergent-First Design

- **Cognitive Profile Support**: ADHD, Autism, Dyslexia-friendly features
- **Flow State Monitoring**: Real-time coding flow detection and optimization
- **Focus Mode**: Distraction-free coding environment (`Ctrl+Shift+Alt+F`)
- **Accessible Themes**: Specialized color schemes for different cognitive needs

### 🔄 Multi-Language Transpilation

- Transpile Sona code to **Python**, **JavaScript**, **Rust**, **Go**, and **C++**
- Real-time syntax validation and error checking
- Intelligent code formatting and optimization

### 🤖 AI-Native Programming

- Built-in AI functions: `ai_simplify()`, `ai_debug()`, `ai_optimize()`
- Code explanation and suggestions
- Intelligent code completion and refactoring

### 🛠️ Developer Experience

- **Syntax Highlighting**: Rich, cognitive-aware syntax highlighting
- **IntelliSense**: Smart code completion and suggestions
- **Integrated Terminal**: Run, profile, and benchmark Sona code
- **Code Snippets**: Pre-built templates for common patterns

## 🚀 Quick Start

1. **Install the Extension**: Search for "Sona Language Support" in VS Code Extensions
2. **Install Sona**: `pip install sona-lang`
3. **Create a .sona file** and start coding!
4. **Run your code**: Press `Ctrl+F5` or use Command Palette > "Sona: Run"

### Example Sona Code

```sona
// Cognitive-friendly function definition
def greet_user(name) {
    remember("last_user", name)
    print(f"Hello, {name}! Welcome to Sona!")

    // AI-powered code suggestion
    suggestion = ai_simplify("Make this greeting more personal")
    return suggestion
}

// Flow-state optimized main function
focus {
    user_name = input("Enter your name: ")
    greeting = greet_user(user_name)
    print(greeting)
}
```

## 🎯 Commands

| Command                   | Keybinding         | Description                    |
| ------------------------- | ------------------ | ------------------------------ |
| `Sona: Run`               | `Ctrl+F5`          | Execute current Sona file      |
| `Sona: Transpile`         | `Ctrl+Shift+T`     | Transpile to other languages   |
| `Sona: Format`            | `Ctrl+Shift+F`     | Format Sona code               |
| `Sona: Toggle Focus Mode` | `Ctrl+Shift+Alt+F` | Toggle distraction-free mode   |
| `Sona: Check Syntax`      | -                  | Validate syntax                |
| `Sona: AI Explain`        | -                  | Get AI code explanation        |
| `Sona: AI Suggest`        | -                  | Get AI suggestions             |
| `Sona: Setup Environment` | -                  | Configure Sona and AI features |

## ⚙️ Configuration

### Cognitive Profile

```json
{
  "sona.cognitiveProfile": "ADHD", // Auto, ADHD, Autism, Dyslexia, Neurotypical
  "sona.accessibilityLevel": "Enhanced", // Standard, Enhanced, Maximum
  "sona.focusMode.enabled": true
}
```

### AI Features

```json
{
  "sona.aiFeatures.enabled": true, // Requires setup
  "sona.defaultTranspileTarget": "python"
}
```

### Development

```json
{
  "sona.pythonPath": "python", // Path to Python executable
  "sona.autoTranspile": false,
  "sona.flowState.monitoring": true
}
```

## 🎨 Themes

Choose from cognitive-optimized themes:

- **Sona Flow (Dark)**: Standard dark theme with flow-optimized colors
- **Sona Focus (Light)**: Clean light theme for maximum focus
- **Sona ADHD**: High-contrast theme optimized for ADHD
- **Sona Dyslexia Friendly**: Dyslexia-friendly colors and contrast

## 🤖 AI Setup

1. Run `Sona: Setup Environment` from Command Palette
2. Choose manual setup for Azure OpenAI
3. Follow the prompts to configure your AI credentials
4. Enable AI features in settings: `"sona.aiFeatures.enabled": true`

## 🧩 Cognitive Features

### Memory Functions

```sona
remember("important_data", user_input)  // Store in cognitive memory
value = recall("important_data")        // Retrieve from memory
```

### Flow State Optimization

```sona
focus {
    // This block is optimized for flow state
    // Reduces distractions and cognitive load
}

mindfully {
    // Encourages mindful, deliberate coding
}
```

### AI-Powered Development

```sona
simplified = ai_simplify("Complex algorithm here")
optimized = ai_optimize(my_function)
explanation = ai_debug("Why isn't this working?")
```

## 📚 Documentation

- [Sona Language Guide](https://github.com/Bryantad/Sona#readme)
- [Neurodivergent Programming Principles](https://github.com/Bryantad/Sona/docs/neurodivergent-guide.md)
- [Multi-Language Transpilation](https://github.com/Bryantad/Sona/docs/transpilation.md)
- [AI Integration Guide](https://github.com/Bryantad/Sona/docs/ai-features.md)

## 🐛 Issues & Support

- **Bug Reports**: [GitHub Issues](https://github.com/Bryantad/Sona/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/Bryantad/Sona/discussions)
- **Community**: Join our neurodivergent-friendly community

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/Bryantad/Sona/blob/main/Contributing.md) for details.

## 📄 License

MIT License - see [LICENSE](https://github.com/Bryantad/Sona/blob/main/LICENSE) for details.

---

**Made with 💜 for the neurodivergent community**

_Sona: Where cognitive diversity drives innovation_
