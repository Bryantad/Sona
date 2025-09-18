# 🚀 Sona — The World’s First **AI-Native** Programming Language

**Human × AI collaboration with cognitive accessibility at the core.**

[![Version](https://img.shields.io/badge/version-0.9.3-blue.svg)](https://github.com/Bryantad/Sona/releases/tag/v0.9.3)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![Marketplace Installs](https://img.shields.io/visual-studio-marketplace/i/Waycoreinc.sona-ai-native-programming?label=VS%20Code%20Installs)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)
[![Marketplace Rating](https://img.shields.io/visual-studio-marketplace/r/Waycoreinc.sona-ai-native-programming?label=VS%20Code%20Rating)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)
[![GitHub Stars](https://img.shields.io/github/stars/Bryantad/Sona?style=social)](https://github.com/Bryantad/Sona/stargazers)
[![YouTube](https://img.shields.io/youtube/channel/subscribers/UCFWuiQHiQPrJSAeAVi5raZA?style=social)](https://www.youtube.com/channel/UCFWuiQHiQPrJSAeAVi5raZA)
[![X (Twitter) Follow](https://img.shields.io/twitter/follow/sona_org?style=social)](https://x.com/sona_org)

> Sona lets you **think in code** and **code in plain language**—with accessibility features that respect how different brains work.

---

## TL;DR

- **AI-Native from first principles.** Sona speaks *with* you as you build—explain, review, plan, optimize.
- **Cognitive accessibility, seriously.** Focus Mode, working memory patterns, and design choices meant for real humans, not idealized robots.
- **Pragmatic interop.** Transpile to JS/TS/Python/C#/Go/Rust when you need to meet teams where they are.

If you like where this is going, **⭐️ star this repo**. Stars signal demand and help us prioritize features you’ll actually use.

---

## ✨ What’s New in v0.9.3 (Foundation Release)

This release is about **infrastructure and reliability**—so cognitive features can land on solid ground.

- **CLI & Diagnostics:** `doctor`, `build-info`, `ai-plan`, `ai-review`, `probe`
- **Resilience:** circuit breaker, micro-batching queue, LRU+TTL cache (flagged)
- **Observability:** JSONL performance logs (daily-rotated)
- **Policy Engine:** `.sona-policy.json` with allow/deny rules + `probe` checks
- **Feature Flags:** new infra is **off by default** until you opt in
- **VS Code:** Focus Mode toggle + settings framework (early)

> You’re not looking for hype; you’re looking for a backbone. v0.9.3 is structural steel.

---

## 🧠 AI-Native Programming (First-Class)

```sona
// AI-powered collaboration
ai_complete("create a secure login function")
ai_explain(complex_code, "beginner")
ai_debug("null pointer", "authentication context")
ai_optimize("slow database queries")
ai_review(code_context)
```

## 🧭 Cognitive Programming (Accessibility Pioneer)

```sona
// Reduce cognitive load, on purpose
working_memory("user authentication flow", "load")
focus_mode("debugging session", "25min")
cognitive_check("high complexity")
simplify("OAuth implementation", "intermediate")
break_down("complex user interface")
```

## 💬 Natural Language Programming

```sona
// Conversational thinking to executable steps
explain("This function validates user input and handles edge cases")
think("What's the best way to optimize this algorithm?")
intend("create a secure, scalable user management system")
```

---

## 🚀 Quick Start

### Install (Python 3.11+)

```bash
pip install sona==0.9.3
# or with extras
pip install "sona[ai]==0.9.3"     # AI-related deps
pip install "sona[dev]==0.9.3"    # tooling for devs
```

### Verify Your Environment

```bash
sona build-info
sona doctor
```

### First Run

```bash
# REPL
sona repl
```

```sona
// inside REPL
explain("Learning the world's first AI-native language!")
ai_complete("function to process user data securely")
working_memory("data processing concept", "load")
focus_mode("learning Sona", "20min")
```

---

## 🧩 VS Code Integration

- Install the extension: **Sona — AI-Native Programming**
- Try **Focus Mode** (early) and command palette actions
- Marketplace: https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming

> The extension brings Sona’s cognitive patterns into your daily workflow without fighting your editor muscle memory.

---

## 🔧 CLI (0.9.3)

```bash
sona init <project>           # Create new project
sona run <file>               # Execute Sona files
sona repl                     # Interactive REPL
sona transpile <file>         # Convert to other languages
sona format <file>            # Format code
sona check <file>             # Syntax validation
sona info                     # Environment information
sona build-info               # Build metadata + feature flags
sona doctor                   # System diagnostics (0.9.3+)
sona ai-plan <ctx>            # Deterministic planning stub (0.9.3+)
sona ai-review <file>         # Deterministic review stub (0.9.3+)
sona probe                    # Policy/permissions probe (0.9.3+)
sona clean                    # Clean generated files
sona docs                     # Open documentation
```

---

## 🔀 Multi-Language Transpilation

```bash
sona transpile app.sona --target javascript
sona transpile app.sona --target typescript
sona transpile app.sona --target python
sona transpile app.sona --target csharp
sona transpile app.sona --target go
sona transpile app.sona --target rust
```

> Use Sona to think clearly; emit to the stack your team ships.

---

## 🧪 Cognitive Example (Short)

```sona
working_memory {
  current_task = "Data processing";
  cognitive_load = "medium";
  next_steps = ["validate", "process", "save"];
}

when data_arrives {
  think("New data needs processing");
  focus("Data validation");
  result = validate_input(data);

  if (result.valid) {
    process_data(result.data);
  } else {
    handle_error(result.errors);
  }
}
```

Output:
```
[THINK] New data needs processing
[FOCUS] Data validation
Processing complete: 42 records
```

---

## Who Uses Sona Today?

- **Neurodivergent devs** who want tools that respect focus, pacing, and cognitive load.  
- **Educators & students** who want explanations *as they code*.  
- **Professional teams** shipping in multiple languages that want **one thinking surface** and **many targets**.

If that resonates, **⭐️ star now** and watch the roadmap land.

---

## Docs & Resources

- **Wiki:** https://github.com/Bryantad/Sona/wiki  
- Getting Started: `docs/installation.md`, `docs/quickstart.md`  
- Language Reference: `docs/language-reference.md`  
- Cognitive Features: `docs/cognitive-features.md`  
- CLI Reference: `docs/cli-reference.md`  
- Transpilation: `docs/transpilation.md`  
- VS Code Guide: `docs/vscode-extension.md`  

**0.9.3 Docs Add-ons**
- `FEATURE_FLAGS.md` — toggles & safe defaults  
- `SECURITY.md` — `.sona-policy.json` + `probe`  
- `RESEARCH_AUDIT.md` — what’s built vs. what’s aspirational

---

## Roadmap (to 1.0)

- ✅ 0.9.3: Infra, flags, diagnostics, policy engine  
- 🔜 Cognitive metrics + profiles grounding (ADHD, dyslexia)  
- 🔜 AI policy routing + adaptive prompts (from runtime signals)  
- 🔜 First-class module system for cognitive primitives  
- 🔜 Expanded transpilation fidelity + static analysis

> Stars help prioritize. If you want these faster, hit ⭐️ and open a discussion.

---

## Community

- **Issues:** https://github.com/Bryantad/Sona/issues  
- **Discussions:** https://github.com/Bryantad/Sona/discussions  
- **Contributing:** See [CONTRIBUTING.md](CONTRIBUTING.md)  

If you build something cool with Sona, we’ll showcase it.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Acknowledgments

To the neurodivergent community and accessibility researchers who keep us honest, and to open-source contributors who want developer tools that meet people where they are.
