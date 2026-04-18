# Cognitive Drift Detector

[![Version](https://img.shields.io/badge/version-0.11.0-blue.svg)](https://github.com/Bryantad/Sona/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Marketplace](https://img.shields.io/badge/VS%20Code-Marketplace-blue)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.cognitive-drift-detector)
[![Part of Sona](https://img.shields.io/badge/part%20of-Sona%20Ecosystem-purple)](https://github.com/Bryantad/Sona)

---

A Visual Studio Code extension that detects when your **mental context has drifted**.

This is attention analytics — not productivity analytics.

---

## Overview

Cognitive Drift Detector watches patterns, not performance:

- lots of file jumping
- repeated backtracking (A → B → A)
- long idle gaps while still switching context

It shows a passive status indicator:

- 🟢 Drift: Low
- 🟡 Drift: Medium
- 🔴 Drift: High

When drift is high, click the indicator for gentle “re-orient” actions.

---

## Key Features

- **Drift scoring** — based on file switches, backtracking, and idle time
- **Status bar indicator** — always passive
- **Re-orient actions** — open Recent Files / Open Editors / Explorer
- **Notifications are off by default** — optional gentle reminder

---

## Commands

| Command                                 | Description                     |
| --------------------------------------- | ------------------------------- |
| Cognitive Drift: Show Re-Orient Actions | Quick pick of re-orient actions |
| Cognitive Drift: Reset                  | Clear the drift history         |
| Toggle Cognitive Drift Detector         | Enable/disable the detector     |

---

## Settings

```json
{
  "cognitiveDrift.enabled": true,
  "cognitiveDrift.lookbackMinutes": 8,
  "cognitiveDrift.switchesForHigh": 10,
  "cognitiveDrift.idleSeconds": 90,
  "cognitiveDrift.notifications": false
}
```

---

## Use Cases

### “I’m bouncing and not progressing”

The indicator helps you notice drift early.

### Re-orienting without guilt

Use the built-in actions to re-anchor.

---

## License

MIT License — see [LICENSE](LICENSE).
