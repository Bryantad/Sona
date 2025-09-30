# 🚀 Sona — The World’s First **AI-Native** Programming Language

**Human × AI collaboration with cognitive accessibility at the core.**

[![Version](https://img.shields.io/badge/version-0.9.4.1-blue.svg)](https://github.com/Bryantad/Sona/releases/tag/v0.9.4.1)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://python.org)
[![Marketplace Installs](https://img.shields.io/visual-studio-marketplace/i/Waycoreinc.sona-ai-native-programming?label=VS%20Code%20Installs)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)
[![Marketplace Rating](https://img.shields.io/visual-studio-marketplace/r/Waycoreinc.sona-ai-native-programming?label=VS%20Code%20Rating)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)
[![GitHub Stars](https://img.shields.io/github/stars/Bryantad/Sona?style=social)](https://github.com/Bryantad/Sona/stargazers)
[![YouTube](https://img.shields.io/youtube/channel/subscribers/UCFWuiQHiQPrJSAeAVi5raZA?style=social)](https://www.youtube.com/channel/UCFWuiQHiQPrJSAeAVi5raZA)
[![X (Twitter) Follow](https://img.shields.io/twitter/follow/sona_org?style=social)](https://x.com/sona_org)

> Sona lets you think in code and code in plain language—with accessibility choices that respect how different brains work.

## ✨ What’s solid right now (v0.9.4 baseline)

- JSON
  - RFC 7396 Merge Patch: `merge_patch(target, patch)` (documented & tested)
  - JSON Pointer helpers (with “pointer gotchas” documented)
  - deep_update: `deep_update(target, patch, *, list_strategy="replace", make_copy=True)`
    - Dicts recurse; lists replace by default (`append` / `extend_unique` available)
    - Back-compat shim accepts legacy `copy=` (emits `DeprecationWarning`)
- Collections: `chunk`, `unique_by`, `group_by` (exported & tested)
- Quality (Windows, Python 3.12, `SONA_DEBUG=1`)
  - Tests: PASS
  - Coverage: 87.09% (gate ≥85% met)
  - Deterministic: no network deps in tests
- Architecture & docs
  - ADR-0001: keep AI out of stdlib; future `sona-ai` package with fake transport & clear error taxonomy
  - `STDLIB_GAPS_ROADMAP.md`, `AI_PROVIDER_TEST_PLAN.md`

> Hotfix v0.9.4.1 (this release) corrects public packaging (wires the modules) and adds this Overview to the VS Code listing.

## 🚀 Quick Start

> Requires Python 3.12+.

```bash
pip install sona==0.9.4.1
# Optional extras
pip install "sona[ai]==0.9.4.1"
pip install "sona[dev]==0.9.4.1"
```

Verify:

```bash
sona build-info
sona doctor
```

REPL:

```bash
sona repl
```

<!-- Run-from-source section intentionally omitted in v0.9.4.1 repo prep to keep commit docs-free. -->

## Docs & Resources

- Wiki: https://github.com/Bryantad/Sona/wiki
- Language Reference & Guides: see `/docs/*`
- VS Code Guide: `docs/vscode-extension.md`

## License

MIT — see LICENSE.

# 🚀 Sona - The World's First AI-Native Programming Language

**Revolutionary AI-Powered Development with Cognitive Accessibility**

[![Version](https://img.shields.io/badge/version-0.9.3-blue.svg)](https://github.com/Bryantad/Sona/releases/tag/v0.9.3)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![Coverage](https://img.shields.io/badge/coverage-pending-lightgrey.svg)](#)
[![AI-Native](https://img.shields.io/badge/AI--Native-Revolutionary-purple.svg)](docs/ai-features.md)
[![VS Code Extension](https://img.shields.io/badge/VS%20Code-Extension%20Available-brightgreen.svg)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)

> **The world's first programming language with integrated AI collaboration, natural language programming, and cognitive accessibility features.**

Sona v0.9.3 represents a paradigm shift in programming. Write code that thinks with you, explains itself, and adapts to your cognitive needs. Experience true human-AI collaboration in software development.

## 🔄 What's New in 0.9.3

Focused resilience & infrastructure release (no breaking changes):

| Area            | Enhancement                                                     |
| --------------- | --------------------------------------------------------------- |
| Feature Flags   | Centralized, documented, all new features default OFF           |
| Caching         | LRU + TTL cache (gated)                                         |
| Circuit Breaker | Error-rate with half-open probing (gated)                       |
| Micro-Batching  | Time-window aggregation (gated)                                 |
| Policy Engine   | JSON-based deny patterns & provider scoping                     |
| Perf Logging    | Rotating JSONL logs (gated) + directory override                |
| AI Capabilities | Deterministic ai-plan / ai-review (graceful degrade w/o extras) |
| CLI             | New commands: ai-plan, ai-review, build-info, doctor, probe     |
| Security        | Default policy template + probe diagnostics                     |
| Docs            | Tutorial + Teacher's Guide + Feature Flags reference            |

Install with optional AI extras:

```bash
pip install "sona-lang[ai]"
```

Or minimal core only:

```bash
pip install sona-lang
```

Feature flags reference: see [FEATURE_FLAGS.md](FEATURE_FLAGS.md) for all environment variables and rollout guidance.

### Performance Logging (Optional)

Enable lightweight JSONL performance event logging:

```bash
export SONA_PERF_LOGS=1            # turn on logging
export SONA_PERF_DIR=.sona/.perf   # (optional) custom directory (auto-created)
```

Each event line (rotated daily) contains: `{"ts": <epoch>, "event": "name", ...custom fields}`. Safe to enable in development; I/O errors are swallowed.

### Security Policy & Governance

Baseline policy file `.sona-policy.json` included (deny high‑risk operations by default). Extend by editing and pointing `SONA_POLICY_PATH` to a reviewed version. See `SECURITY.md` for reporting process.

See `FEATURE_FLAGS.md` for enabling infrastructure features safely.

## ✨ Revolutionary Features

### 🤖 AI-Native Programming (World's First)

```sona
// AI-powered code completion and explanation
ai_complete("create a secure login function")
ai_explain(complex_code, "beginner")
ai_debug("null pointer", "authentication context")
ai_optimize("slow database queries")
ai_review(code_context)
```

### 🧠 Cognitive Programming (Accessibility Pioneer)

```sona
// Cognitive accessibility features
working_memory("user authentication flow", "load")
focus_mode("debugging session", "25min")
cognitive_check("high complexity")
simplify("OAuth implementation", "intermediate")
break_down("complex user interface")
```

### 💭 Natural Language Programming

```sona
// Conversational programming
explain("This function validates user input and handles edge cases")
think("What's the best way to optimize this algorithm?")
intend("create a secure, scalable user management system")
```

## 🚀 Quick Start

### Installation

```bash
# Clone the revolutionary Sona repository
git clone https://github.com/Bryantad/Sona.git
cd Sona

# Install dependencies
pip install -r requirements.txt

# Optional: Set up AI APIs for enhanced features
cp .env.example .env
# Add your OpenAI and Claude API keys to .env
```

### Your First AI-Native Program

```bash
# Start the interactive AI-powered REPL
sona

# Experience revolutionary programming:
```

```sona
# Natural language programming
explain("Learning the world's first AI-native language!")

# AI collaboration
ai_complete("function to process user data securely")
think("What's the best approach for error handling?")

# Cognitive accessibility
working_memory("data processing concept", "load")
cognitive_check("normal")
focus_mode("learning Sona", "20min")

# Get AI explanations
ai_explain("function authenticate(user) { return jwt.sign(user); }", "beginner")
```

## 🌟 Why Sona v0.9.3 is Revolutionary

### Paradigm-Shifting Innovations

- **🤖 First AI-Native Language**: Built for human-AI collaboration from the ground up
- **🧠 Cognitive Accessibility**: Programming that adapts to different thinking styles
- **💭 Conversational Coding**: Natural language becomes executable code
- **🔮 Predictive Development**: AI anticipates and prevents issues

### Real-World Impact

- **Learning**: AI explains concepts as you code
- **Accessibility**: Supports neurodivergent and diverse cognitive styles
- **Productivity**: AI assistance accelerates development
- **Quality**: Predictive analysis prevents bugs before they occur

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

## 🔁 Rollback & Verification

If you encounter issues with 0.9.3 you can rollback safely (no schema/state migrations were introduced):

```bash
pip install --upgrade 'Sona==0.9.2'
```

Post‑install verification steps:

```bash
sona build-info
python -m pytest -q
```

Confirm the reported version and a green test run to match CI expectations.

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
