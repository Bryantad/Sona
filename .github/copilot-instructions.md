# Sona AI-Native Programming Language - Copilot Instructions

## Project Overview

Sona is the world's first **AI-native programming language** with built-in cognitive accessibility features. It combines traditional programming with conversational AI integration and neurodivergent-friendly syntax patterns.

### Core Architecture

- **Transpiler-based**: Sona code transpiles to Python, JavaScript, TypeScript, Java, C#, Go, and Rust
- **Dual-syntax**: Supports both traditional programming syntax and cognitive/conversational patterns
- **AI Integration**: Built-in AI functions (`ai_complete`, `ai_explain`, `ai_debug`, etc.)
- **Modular Standard Library**: Located in `sona/stdlib/` with feature flags and lazy loading

## Key Components

### Main Entry Points
- `cli.py` - Root CLI with multi-provider AI setup commands
- `sona/cli.py` - Core interpreter CLI with execution, transpilation, and type checking
- `sona_transpiler.py` - Multi-language code generation engine
- `sona/interpreter.py` - Main runtime interpreter (1900+ lines)

### Core Runtime
- `sona/parser_v090.py` + `sona/grammar.lark` - Lark-based parser with cognitive syntax support
- `sona/ast_nodes_v090.py` - AST node definitions including AI statement nodes
- `sona/type_system/` - Runtime type checking with configurable modes (`off`/`on`/`warn`)
- `sona/stdlib/` - Standard library modules (math, string, json, http, fs, etc.)

### AI Integration
- `sona/ai/` - GPT-2 based code completion and cognitive assistance
- Multi-provider support: Azure OpenAI, OpenAI, Anthropic, Google Gemini
- Fake transport layer for testing without real API calls

## Development Workflows

### Running Sona Code
```bash
# Direct execution
sona run file.sona

# Interactive REPL with AI features
sona repl

# Transpile to other languages  
sona transpile file.sona --target python
```

### Testing
```bash
# Core tests with coverage gate (≥85%)
pytest --cov=sona --cov-report=term:skip-covered

# Stdlib tests with debug mode
SONA_DEBUG=1 pytest -c pytest-stdlib.ini

# Type system tests
pytest tests/test_type_system_runtime.py
```

### Build and Package
```bash
# Install in development mode
pip install -e .[dev]

# Generate stdlib manifest for VS Code extension
python scripts/generate_stdlib_manifest.py

# Package VS Code extension
cd vscode-extension && npm run package
```

## Code Patterns and Conventions

### Sona Language Syntax
```sona
# Traditional syntax
let x = 10
print("Hello World")

# Cognitive syntax
think("Planning the solution")
remember("User input validation is important")
working_memory("current_task", "load")
focus_mode("debugging", "20min")

# AI integration
ai_complete("create a secure login function")
ai_explain(code, "beginner")
ai_debug("null pointer", "authentication context")
```

### Python Integration Patterns
- **Lazy imports**: Use `__getattr__` in `__init__.py` for performance
- **Feature flags**: Check `sona/flags.py` for environment-controlled features
- **Error handling**: Wrap AI calls with graceful degradation fallbacks
- **Type checking**: Use `sona/type_config.py` for runtime type validation

### AI Provider Pattern
```python
# Always provide fallback for missing AI providers
if not hasattr(self, 'real_ai'):
    self._setup_real_ai_provider()
if self.real_ai:
    try:
        response = self.real_ai.ai_function(...)
        return str(response)
    except Exception as e:
        return f"AI function failed: {e}"
else:
    return "Real AI not available - check configuration"
```

## Configuration System

### Environment Variables
- `SONA_DEBUG=1` - Enable detailed logging
- `SONA_TYPES=on/off/warn` - Runtime type checking mode
- `SONA_PERF_LOGS=1` - Enable performance logging
- `SONA_POLICY_PATH` - Custom security policy file

### Config Files
- `sona.config.json` - Project-level type checking and feature configuration
- `.sona-policy.json` - Security policy with deny patterns
- `~/.sona/config.json` - User AI provider credentials (Azure OpenAI, etc.)

## Testing and Quality

### Coverage Requirements
- Core package: ≥85% coverage gate enforced in CI
- Stdlib: Separate test suite with debug mode validation
- Type system: Comprehensive runtime validation tests

### CI Pipeline
- Multi-Python version testing (3.11, 3.12)
- Ruff linting, MyPy type checking (best effort)
- VS Code extension packaging on release tags
- Windows-specific validation for final releases

## Common Gotchas

### Import Resolution
- Interpreter has complex import path resolution due to multiple entry points
- Use absolute imports within `sona/` package
- Parser and AST imports have fallback patterns for development vs. installed modes

### AI Integration
- All AI functions must handle missing providers gracefully
- Mock/fake implementations exist for testing without API keys
- Real AI setup requires user-provided credentials via `sona setup` commands

### Type System
- Runtime type checking is **optional** and configurable
- Default mode is `off` - only enabled explicitly via config/environment
- File exclusion patterns supported for gradual adoption

### Grammar and Parsing
- Dual grammar support: traditional + cognitive syntax
- Lark parser with custom transformers for AST generation
- Complex expression parsing with precedence handling

When working on Sona, always consider the cognitive accessibility mission - code should be readable and inclusive for neurodivergent developers. The dual syntax system allows both traditional programming patterns and more conversational, documented approaches.