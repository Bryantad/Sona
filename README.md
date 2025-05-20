````markdown
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
````

---

## What is Sona?

* Human-first syntax
* AI-enhanced 
* Modular-by-default via `.smod` modules
* Built from scratch with Lark and a custom interpreter

---

## Core Features

* Clean syntax: `let`, `const`, `func`, `if`, `for`, `while`, `return`
* Dual structure: indentation or braces
* Fully working interpreter and REPL
* Built-in standard modules: `math.smod`, `fs.smod`, `env.smod`, `stdin.smod`
* CLI execution: `sona file.sona`
* Future-ready: SonaCore AI, transpiler support, IDE integration

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

## Contribute or Join the Movement

1. Fork this repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Make your changes and write tests
4. Submit a Pull Request

---

## Support

Your support keeps Sona and SonaCore moving forward:

[![Sponsor](https://img.shields.io/badge/Sponsor-Sona-blue)](https://github.com/sponsors/Bryantad)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy_Me_A_Coffee-Donate-yellow)](https://ko-fi.com/Bryantad)

Stars, forks, pull requests, and donations are all welcome.

---

## License

MIT License. Sona is free to use, build on, and share.
Proudly created by Netcore Solutions LLC, a subsidiary of Waycore Inc.
