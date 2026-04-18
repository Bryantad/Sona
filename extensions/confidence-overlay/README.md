# Confidence Overlay

[![Version](https://img.shields.io/badge/version-0.11.0-blue.svg)](https://github.com/Bryantad/Sona/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Marketplace](https://img.shields.io/badge/VS%20Code-Marketplace-blue)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.confidence-overlay)
[![Part of Sona](https://img.shields.io/badge/part%20of-Sona%20Ecosystem-purple)](https://github.com/Bryantad/Sona)

---

A Visual Studio Code extension that lets you mark **your confidence** in code blocks.

Not quality.

Not correctness.

Confidence.

---

## Overview

Some code is trusted.

Some code is fragile in the author’s mind — even if it works.

Confidence Overlay lets you select a region and label it:

- High
- Medium
- Low

The editor subtly tints the background.

Private by default.

---

## Key Features

- **Subtle background tints** — High (green), Medium (yellow), Low (red)
- **Hover details** — see confidence + timestamp
- **Quick commands** — set/clear without leaving the editor
- **Private-by-default** — stored in VS Code workspace state

---

## Commands

| Command                            | Description                              |
| ---------------------------------- | ---------------------------------------- |
| Set Confidence: High               | Apply High overlay to selection          |
| Set Confidence: Medium             | Apply Medium overlay to selection        |
| Set Confidence: Low                | Apply Low overlay to selection           |
| Clear Confidence Overlay at Cursor | Remove overlays covering the cursor line |
| Clear Confidence Overlays in File  | Remove all overlays in current file      |
| Toggle Confidence Overlay          | Enable/disable rendering                 |

---

## Settings

```json
{
  "confidenceOverlay.enabled": true
}
```

---

## Use Cases

### Confidence decays faster than correctness

This captures your intuition before it’s lost.

### Triaging fragile areas

Mark low-confidence zones for later strengthening.

---

## License

MIT License — see [LICENSE](LICENSE).
