# Contributing to Sona

Thank you for your interest in contributing to Sona! This document provides guidelines and instructions for contributing.

## 🎯 Ways to Contribute

- 🐛 **Report Bugs** - Found an issue? Let us know!
- ✨ **Suggest Features** - Have an idea? We'd love to hear it!
- 📝 **Improve Documentation** - Help make our docs clearer
- 🔧 **Submit Code** - Fix bugs or add features
- 🧪 **Write Tests** - Improve test coverage
- 📚 **Create Examples** - Show what Sona can do

---

## 🚀 Getting Started

### 1. Fork & Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/SonaMinimal.git
cd SonaMinimal
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
# source .venv/bin/activate    # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### 3. Verify Setup

```bash
# Run tests
python run_sona.py test_all_features.sona

# Verify all modules
python run_sona.py test_all_30_imports.sona
```

---

## 🔧 Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

- Write clear, readable code
- Follow existing code style
- Add comments for complex logic
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run all tests
python run_sona.py test_all_features.sona

# Test specific functionality
python run_sona.py your_test.sona

# Verify no regressions
python run_sona.py test_all_30_imports.sona
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: Add new feature description"
# or
git commit -m "fix: Fix bug description"
```

**Commit Message Format:**

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `style:` Code style changes
- `chore:` Maintenance tasks

### 5. Push & Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:

- Clear title and description
- Reference any related issues
- List of changes made
- Test results

---

## 📝 Code Style Guidelines

### Python Code

```python
# Good
def import_module(self, module_path: str, alias: str | None = None):
    """Import a module and make it available in the interpreter."""
    if module_path in self.loaded_modules:
        return self.loaded_modules[module_path]
    # Load module logic...

# Use type hints
# Add docstrings
# Clear variable names
# Consistent indentation (4 spaces)
```

### Sona Code

```sona
// Good
import json;
import string;

func process_data(input) {
    let result = string.upper(input);
    return result;
}

// Use semicolons
// Clear function names
// Consistent formatting
```

---

## 🧪 Testing Guidelines

### Writing Tests

1. **Create test file**: `test_your_feature.sona`
2. **Import required modules**
3. **Write clear test cases**
4. **Verify output**

```sona
// test_my_feature.sona
import io;

print("Testing my feature...");

// Test case 1
let result = my_function(10);
if result == 20 {
    print("✅ Test 1 passed");
} else {
    print("❌ Test 1 failed: expected 20, got " + result);
}

// Test case 2
let result2 = my_function(5);
if result2 == 10 {
    print("✅ Test 2 passed");
} else {
    print("❌ Test 2 failed: expected 10, got " + result2);
}
```

### Test Coverage

- ✅ Test happy path
- ✅ Test error cases
- ✅ Test edge cases
- ✅ Test with different inputs
- ✅ Document expected behavior

---

## 📚 Documentation Guidelines

### Code Documentation

```python
def function_name(param1: type, param2: type) -> return_type:
    """
    Brief description of what the function does.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ErrorType: When this error occurs

    Example:
        >>> function_name("test", 42)
        "result"
    """
    # Implementation
```

### Documentation Files

- Use clear headings
- Add code examples
- Include cross-references
- Keep formatting consistent
- Update table of contents

---

## 🐛 Bug Reports

### Good Bug Report Includes:

1. **Clear Title** - Summarize the issue
2. **Description** - What happened vs. what should happen
3. **Steps to Reproduce**:
   ```
   1. Import module X
   2. Call function Y with Z
   3. See error
   ```
4. **Expected Behavior** - What should happen
5. **Actual Behavior** - What actually happens
6. **Environment**:
   - OS: Windows 11 / Linux / macOS
   - Python version: 3.12
   - Sona version: 0.9.8
7. **Code Sample** - Minimal reproducible example
8. **Error Message** - Full error output

---

## ✨ Feature Requests

### Good Feature Request Includes:

1. **Clear Title** - What feature you want
2. **Problem Statement** - What problem does it solve?
3. **Proposed Solution** - How should it work?
4. **Alternatives** - Other ways to solve it
5. **Examples** - Code examples of usage
6. **Use Cases** - When would you use this?

---

## 🔍 Code Review Process

### What We Look For:

- ✅ Code works as intended
- ✅ Tests pass
- ✅ No regressions
- ✅ Clear, readable code
- ✅ Proper documentation
- ✅ Follows style guidelines
- ✅ Performance considerations

### Review Timeline:

- Initial response: Within 2-3 days
- Full review: Within 1 week
- Feedback addressed: Ongoing discussion

---

## 📂 Project Structure

Understanding the codebase:

```
sona/
├── interpreter.py       # Main interpreter logic
├── parser_v090.py       # Parser implementation
├── ast_nodes_v090.py    # AST node definitions
├── grammar_v091_fixed.lark  # Language grammar
├── stdlib/              # Standard library modules
│   ├── native_*.py      # Native Python modules
│   └── *.py             # Regular modules
├── ai/                  # AI integration
├── core/                # Core utilities
├── control/             # Control flow
└── type_system/         # Type checking
```

### Key Files to Know:

- **interpreter.py** - Executes AST, manages scope, loads modules
- **parser_v090.py** - Parses Sona code into AST
- **grammar_v091_fixed.lark** - Defines Sona syntax
- **stdlib/MANIFEST.json** - Lists all stdlib modules

---

## 🎓 Learning Resources

### Understanding the Code:

1. **Start with**: `docs/development/IMPLEMENTATION_SUMMARY.md`
2. **Read**: `docs/features/FEATURE_AUDIT_096.md`
3. **Review**: `docs/troubleshooting/` for common issues
4. **Explore**: Test files to see examples

### Key Concepts:

- **AST (Abstract Syntax Tree)** - How code is represented
- **Visitor Pattern** - How AST is processed
- **Scope Management** - Variable and function scope
- **Module System** - How imports work

---

## 🤝 Community Guidelines

### Be Respectful

- Welcome newcomers
- Be patient with questions
- Provide constructive feedback
- Celebrate contributions

### Be Professional

- Stay on topic
- No spam or self-promotion
- Respect maintainer decisions
- Follow code of conduct

---

## 📈 Contribution Areas

### High Priority:

1. **Bug Fixes** - Especially regressions
2. **Documentation** - Examples, tutorials, API docs
3. **Tests** - Increase coverage
4. **Performance** - Optimization opportunities

### Medium Priority:

5. **New Features** - From roadmap
6. **Stdlib Modules** - New or enhanced modules
7. **Error Messages** - Clearer error reporting
8. **Examples** - Real-world use cases

### Nice to Have:

9. **Tooling** - VS Code extension, linters
10. **Integrations** - IDE support, CI/CD
11. **Benchmarks** - Performance comparisons
12. **Community** - Blog posts, tutorials

---

## ❓ Questions?

- **Documentation**: Check `docs/` folder first
- **Bugs**: See `docs/troubleshooting/`
- **Features**: Review `docs/features/FEATURE_ROADMAP.md`
- **Development**: Read `docs/development/`

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for contributing to Sona!** 🎉

Every contribution, no matter how small, helps make Sona better for everyone.
