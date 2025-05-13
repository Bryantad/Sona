# Sona Programming Language

**Sona** is a modern, modular, and AI-forward programming language designed to empower developers, creators, and neurodivergent thinkers. It merges the accessibility of Python, the modularity of Go, the discipline of Rust, and the creative freedom of JavaScript—wrapped in a system you own.

> _“If Python taught you to code, Sona will teach you to build legacies.”_

---

## What is Sona?

Sona is a clean, expressive programming language that’s:
- Human-first** in syntax
- AI-enhanced** with its own model (SonaCore)
- Modular-by-default** using `.smod` files
- Built from scratch**, using Lark (Python parser toolkit) and a custom interpreter

It’s made for:
- The solo dev tired of overhead
- The beginner who wants to _understand_, not memorize
- The builder who refuses to be boxed in

---

## Core Features (v0.4.3)

✅ Clean syntax: `let`, `const`, `func`, `if`, `for`, `while`, `return`  
✅ Dual structure: indentation or braces (your choice)  
✅ Fully working interpreter + REPL (cross-platform)  
✅ Built-in standard modules (e.g. `math.smod`, `fs.smod`, `env.smod`)  
✅ CLI execution: `sona file.sona`  
✅ Modular import system  
✅ Future-ready: SonaCore AI, transpiler support, and IDE integration

---

## Example Code

```sona
func greet(name) {
    print("Welcome, " + name);
}

const creator = "Sona"

if (creator == "Sona") {
    greet(creator);
} else {
    print("Unknown caller.");
}
````


-- Getting Started --

1. Install Required Tools

```bash
pip install lark-parser
```

2. Clone and Run REPL

```bash
git clone https://github.com/YOUR_USERNAME/Sona.git
cd sona-lang
python sona_core/interpreter.py
```

Type or paste Sona code directly into the REPL. Press Enter twice to run a block. Type `exit` to quit.

-- The Sona Philosophy --

* Creativity before complexity
* Coding should feel like expressing, not wrestling
* Learning should be like storytelling, not memorization
* Power belongs to those who write, test, and ship

---

Project Layout

```
sona/
├── sona_core/       # Interpreter, grammar, CLI
│   └── grammar.lark
├── smod/            # Sona-native standard modules
├── examples/        # Demo apps (e.g., calculator, chatbot)
├── tests/           # Unit tests
├── docs/            # Guides and references
├── datasets/        # For future SonaCore training
```

---

What’s Coming Next

* 🧪 Built-in unit testing syntax
* 🔁 `match` expressions and pattern destructuring
* 📦 Full SonaCore LLM integration
* 🛠️ IDE auto-complete plugin (powered by SonaCore)
* 🔄 Transpilers: Sona → Python / JS / Go
* 🌐 Deployment to [Sona.org](http://Sona.org)

---

Contribute or Join the Movement

Sona is built **openly and publicly** — and we want you involved.

Ways to contribute:

* Help build `.smod` modules
* Add features to the interpreter
* Test core behavior
* Write example programs
* Help train SonaCore’s brain

Setup to Contribute

```bash
git clone https://github.com/YOUR_USERNAME/sona-lang.git
cd sona-lang
git checkout -b feature/your-feature
```

Then:

1. Make your changes
2. Write tests (if applicable)
3. Submit a Pull Request

---

Projects Built in Sona (examples/)

* 🐍 `snake_game.sona`
* ➕ `calculator.sona`
* 🤖 `chatbot.sona`
* ✨ `auto-completion.sona` (hooks into SonaCore)

---

License

MIT – Sona is free to use, build on, and share.
Proudly created by **Netcore Solutions LLC**, a subsidiary of **Waycore Inc.**

---

Ready to build something meaningful?

> Fork it. Write it. Shape the future with us.

```

Let me know if you want this broken into multiple language versions (like Spanish, French, etc.) or turned into a GitHub Pages landing site.
```
