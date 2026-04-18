# Cognitive Load Meter

[![Version](https://img.shields.io/badge/version-0.11.0-blue.svg)](https://github.com/Bryantad/Sona/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Marketplace](https://img.shields.io/badge/VS%20Code-Marketplace-blue)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.cognitive-load-meter)
[![Part of Sona](https://img.shields.io/badge/part%20of-Sona%20Ecosystem-purple)](https://github.com/Bryantad/Sona)

---

A Visual Studio Code extension that shows a **passive, live indicator of cognitive strain** for the current file.

Not cyclomatic complexity. Not “clean code score”.

This is **human load over time** — what your brain is carrying while you work.

---

## Overview

Cognitive load is real:

- Big files feel heavier.
- Deep nesting costs working memory.
- Jumping across regions increases strain.
- Rapid edits increase mental stack pressure.

This extension turns those signals into a simple status bar meter:

- 🟢 Light
- 🟡 Moderate
- 🔴 Heavy

No warnings. No nags.

---

## Key Features

- **Status Bar Load Meter** — always visible, always passive
- **Time-based signals** — uses a rolling edit lookback window
- **Nesting estimate** — brace depth or indentation depth (language-aware)
- **Region spread** — how many areas of the file you touched recently
- **Edit frequency** — how intense the recent activity has been

---

## Commands

| Command                     | Description                                   |
| --------------------------- | --------------------------------------------- |
| Toggle Cognitive Load Meter | Enable/disable the meter                      |
| Show Load Details           | Show a one-line breakdown of the current load |
| Reset Load History          | Clear recent edit history (fresh start)       |

---

## Settings

```json
{
  "cognitiveLoadMeter.enabled": true,
  "cognitiveLoadMeter.lookbackMinutes": 10,
  "cognitiveLoadMeter.debounceMs": 350,
  "cognitiveLoadMeter.maxLinesForNesting": 2000
}
```

---

## Use Cases

### Feeling “stuck”

The meter gives you a quick signal that you’re carrying too much context.

### Choosing the next step

If load is heavy, you might:

- split the file
- reduce nesting
- add context notes (pair with Code Context)
- take a short break

---

## Part of the Sona Ecosystem

Cognitive Load Meter aligns with Sona’s themes:

- cognitive programming
- attention preservation
- developer wellness

---

## License

MIT License — see [LICENSE](LICENSE).
