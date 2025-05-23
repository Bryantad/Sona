
```markdown
# Sona Programming Language + SonaCore AI

[![Stars](https://img.shields.io/github/stars/Bryantad/Sona?style=social)]
[![Forks](https://img.shields.io/github/forks/Bryantad/Sona?style=social)]
[![Release](https://img.shields.io/github/v/release/Bryantad/Sona)]
[![Sponsor](https://img.shields.io/badge/Sponsor-Sona-blue)]
[![Buy Me a Coffee](https://img.shields.io/badge/Buy_Me_A_Coffee-Donate-yellow)]

**Sona** is a modern, modular, and AI-forward programming language designed to empower developers, creators, and neurodivergent thinkers. It merges the accessibility of Python, the modularity of Go, the discipline of Rust, and the creative freedom of JavaScript, wrapped in a system you own.

> “If Python taught you to code, Sona will teach you to build legacies.”

---

## Releases

- **v0.5.1**
  - Advanced REPL diagnostic tools (`:debug`, `:profile`, `:watch`, `:trace`)
  - Bug fixes for function parameter handling
  - Improved error reporting

- **v0.5.0**
  - Robust module system with nested imports (`import utils.math.smod`)
  - Dotted access (`math.PI`, `fs.exists()`)
  - Immutable constants and enhanced error reporting
  - Expanded standard library (algebra, trigonometry, I/O)
  - CLI improvements and script execution

- **v0.4.3**
  - Core interpreter: variables, control flow, functions
  - REPL enhancements: multiline functions, `:env`, `:clear`, `:reload`
  - 12+ core modules (`fs`, `http`, `json`, `env`, `stdin`)
  - Graceful error messages and fast iteration

---

## Quick Start

```bash
git clone https://github.com/Bryantad/Sona.git
cd Sona
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -r requirements.txt   # or `pip install lark-parser`
pip install -e .
sona --version
```

---

## What is Sona?

- Human-first syntax
- AI-enhanced
- Modular-by-default via `.smod` modules
- Built from scratch with Lark and a custom interpreter

---

## Core Features

- Clean syntax: `let`, `const`, `func`, `if`, `for`, `while`, `return`
- Dual structure: indentation or braces
- Fully working interpreter and REPL
- Built-in standard modules: `math.smod`, `fs.smod`, `env.smod`, `stdin.smod`
- CLI execution: `sona file.sona`
- Future-ready: SonaCore AI, transpiler support, IDE integration

---

## Example Code

```sona
func greet(name) {
    print("Welcome, " + name)
}

const creator = "Sona"

if (creator == "Sona") {
    greet(creator)
} else {
    print("Unknown caller")
}
```

---

## Project Layout

```
sona/
├── sona_core/       # Interpreter, grammar, CLI
├── smod/            # Standard `.smod` modules
├── examples/        # Demo programs (snake_game.sona, calculator.sona, ...)
├── tests/           # Unit tests
├── datasets/        # SonaCore training data
├── docs/            # Developer guide and references
├── setup.py         # Installation config
├── README.md        # Project overview
├── LICENSE          # MIT License
└── CONTRIBUTING.md  # Contribution guidelines
```

---

## REPL Commands

Sona v0.5.1 includes a robust REPL environment with several helpful commands:

```
:help        - Show this help message
:exit, :quit - Exit the REPL
:calc        - Launch calculator application
:quiz        - Launch quiz application
:clear       - Clear the screen
:version     - Show Sona version
:test        - Run diagnostic tests
```

You can also exit by typing `exit` or `quit` without the colon prefix.

---

## Contribute or Join the Movement

1. Fork this repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Make your changes and write tests
4. Submit a Pull Request

---

## Support

Your support keeps Sona and SonaCore moving forward.  
Stars, forks, pull requests, and donations are all welcome.

[![Sponsor](https://img.shields.io/badge/Sponsor-Sona-blue)](https://github.com/sponsors/Bryantad)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy_Me_A_Coffee-Donate-yellow)](https://ko-fi.com/Bryantad)

---

## License

MIT License. Sona is free to use, build on, and share.  
Proudly created by Netcore Solutions LLC, a subsidiary of Waycore Inc.
```

---

**Explanation of Fixes:**
1. **Release Notes**: Merged unique points from both branches, removed duplication/conflict markers.
2. **Quick Start**: Kept the most recent and complete block, removed extra conflict markers.
3. **Feature Lists**: Chose consistent bullet style and included all unique features.
4. **REPL Commands**: Preserved the more detailed/updated list from v0.5.1.
5. **Support Section**: Combined both branch notes—encouraging both support and general contributions.
6. **Removed all conflict markers**: All <<<<<<<, =======, >>>>>>> are gone.

Let me know if you need this in a different format, or want a commit message for the fix!