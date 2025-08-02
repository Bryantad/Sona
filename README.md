# Sona Programming Language

**Neurodivergent-First Development Environment**

[![Version](https://img.shields.io/badge/version-0.8.1-blue.svg)](https://github.com/Bryantad/Sona/releases/tag/v0.8.1)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![VS Code](https://img.shields.io/badge/VS%20Code-Extension-blue.svg)](https://marketplace.visualstudio.com/items?itemName=sona-lang.sona-language-support)

Sona is a programming language that gives developers cognitive accessibility features and seamless integration with multiple target languages. It provides powerful development tools for neurodivergent programmers and may also be used to create accessible applications for diverse cognitive needs. The language supports both traditional programming syntax and cognitive accessibility patterns, allowing developers to choose the approach that works best for their thinking style.

## Writing Cognitive-Accessible Code

Sona allows cognitive accessibility features to be treated essentially as natural language constructs.

```sona
// Cognitive syntax - natural thinking patterns
think("Processing user input");
remember("Validate before saving");
focus("Error handling is critical");

when user_clicks_button {
    process_input();
}
```

To use traditional programming syntax, simply write familiar patterns:

```sona
// Traditional syntax - familiar programming
print("Processing user input");
console.log("Debug information");

function process_data(input) {
    if (input.length > 0) {
        return input.map(item => item * 2);
    }
    return [];
}
```

By default, both syntax styles work together seamlessly. For details on cognitive accessibility features, please refer to the [documentation](docs/).

## Multi-Language Transpilation

If you need to target specific languages, transpiling your Sona code to other languages just requires using the CLI:

```bash
sona transpile app.sona --target javascript
sona transpile app.sona --target python
sona transpile app.sona --target typescript
```

For .NET integration:

```bash
sona transpile app.sona --target csharp
```

## Cognitive Accessibility Features

You must configure your development environment for optimal cognitive support. The language adapts to different thinking patterns and attention styles.

Example cognitive-aware program:

```sona
// Cognitive load monitoring
working_memory {
    current_task = "Processing data";
    cognitive_load = "medium";
    break_needed = false;
}

// Natural language patterns
when data_arrives {
    think("New data needs processing");
    remember("Check validation rules");

    if (cognitive_load > "high") {
        suggest_break("Take a 5-minute break");
    }

    focus("Data validation");
    result = validate_input(data);

    if (result.valid) {
        think("Data is clean, proceeding");
        process_data(result.data);
    } else {
        remember("Invalid data - need to handle gracefully");
        handle_error(result.errors);
    }
}
```

Output:

```
[THINK] New data needs processing
[REMEMBER] Check validation rules
[FOCUS] Data validation
[THINK] Data is clean, proceeding
Processing complete: 42 records
```

## Installation

Install Sona using pip:

```bash
pip install sona
```

Or clone from source:

```bash
git clone https://github.com/Bryantad/Sona.git
cd Sona
pip install -e .
```

## Quick Start

Create and run your first Sona program:

```bash
# Create a new project
sona init hello-world
cd hello-world

# Write your first program
echo 'think("Hello, accessible world!");' > hello.sona

# Run it
sona run hello.sona
```

## CLI Commands

```bash
sona init <project>           # Create new project
sona run <file>               # Execute Sona files
sona repl                     # Interactive REPL
sona transpile <file>         # Convert to other languages
sona format <file>            # Format code
sona check <file>             # Syntax validation
sona info                     # Environment information
sona clean                    # Clean generated files
sona docs                     # Open documentation
```

## Cognitive Accessibility

Sona provides comprehensive support for neurodivergent developers:

### ADHD Support

- Hyperfocus protection with automatic break suggestions
- Attention restoration through structured workflow
- High contrast themes with reduced visual noise
- Task chunking for manageable development

### Autism Support

- Predictable patterns and consistent behavior
- Sensory-friendly interface with calming colors
- Clear hierarchical structure and organization
- Familiar workflows and routine support

### Dyslexia Support

- Dyslexia-friendly typography and fonts
- Meaningful color coding for comprehension
- Improved visual separation and spacing
- Optional audio feedback and confirmation

## Target Language Support

Transpile your Sona code to multiple languages:

**Web Development:**

```bash
sona transpile app.sona --target javascript
sona transpile app.sona --target typescript
```

**Backend Development:**

```bash
sona transpile server.sona --target python
sona transpile server.sona --target java
sona transpile server.sona --target csharp
```

**Systems Programming:**

```bash
sona transpile system.sona --target go
sona transpile system.sona --target rust
```

## Resources

Information on installation, usage, cognitive accessibility features, and projects using Sona can be found in the documentation:

**Documentation:** https://github.com/Bryantad/Sona/wiki

**Getting Started:**

- [Installation Guide](docs/installation.md)
- [Quick Start Tutorial](docs/quickstart.md)
- [Language Reference](docs/language-reference.md)
- [Cognitive Features Guide](docs/cognitive-features.md)

**Advanced Features:**

- [CLI Command Reference](docs/cli-reference.md)
- [Multi-Language Transpilation](docs/transpilation.md)
- [Accessibility Features](docs/accessibility.md)
- [VS Code Extension Guide](docs/vscode-extension.md)

## Community

**Issues:** https://github.com/Bryantad/Sona/issues  
**Discussions:** https://github.com/Bryantad/Sona/discussions  
**Contributing:** See [Contributing.md](CONTRIBUTING.md)

## Examples

### Cognitive Syntax

```sona
// Natural thinking patterns
when user_input_received {
    think("Processing new data");
    remember("Validation is required");
    focus("Check input format");

    if (input.valid) {
        process_safely(input);
    }
}

// Working memory support
working_memory {
    current_task = "Data processing";
    cognitive_load = "medium";
    next_steps = ["validate", "process", "save"];
}
```

### Traditional Syntax

```sona
// Familiar programming patterns
function processData(input) {
    console.log("Processing data");

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

## Who Is This For?

**Neurodivergent Developers:** Experience programming designed for diverse cognitive styles with reduced cognitive load and adaptive attention patterns.

**Educators & Students:** Teach and learn programming with cognitive accessibility features and inclusive learning environments.

**Professional Teams:** Build inclusive development environments supporting neurodivergent team members with powerful multi-language tools.

## License

Sona is open source software licensed under the [MIT License](LICENSE).

## Acknowledgments

This project is supported by the neurodivergent developer community and cognitive accessibility researchers.

**Special thanks to:**

- The Neurodivergent Community for accessibility guidance
- Cognitive Accessibility Researchers for evidence-based design
- Open Source Contributors for feedback and improvements
- VS Code Team for excellent extension APIs
- Python Community for the foundational framework
