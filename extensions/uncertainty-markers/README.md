# Uncertainty Markers

[![Version](https://img.shields.io/badge/version-0.11.0-blue.svg)](https://github.com/Bryantad/Sona/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Marketplace](https://img.shields.io/badge/VS%20Code-Marketplace-blue)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.uncertainty-markers)
[![Part of Sona](https://img.shields.io/badge/part%20of-Sona%20Ecosystem-purple)](https://github.com/Bryantad/Sona)

---

A Visual Studio Code extension that gives uncertainty a **first-class representation** in code.

Not TODOs. Not bugs.

Just honest: **“I’m not fully sure about this.”**

---

## Overview

Developers are rarely allowed to leave “I don’t know” in code.

But uncertainty is real — and forgetting that you were unsure is how fragile code gets re-trusted.

Uncertainty Markers let you:

- select a line or block
- run **Mark as Uncertain**
- get a subtle gutter `?` marker + hover message

Optional expiration keeps markers from living forever.

---

## Key Features

- **Gutter marker** — subtle `?` icon
- **Hover note** — a short explanation of what’s uncertain
- **Private-by-default** — stored in VS Code workspace state
- **Optional expiration** — never / 1 day / 7 days / 30 days / default
- **Quick navigation** — list all markers and jump to them

---

## Commands

| Command                            | Description                               |
| ---------------------------------- | ----------------------------------------- |
| Mark as Uncertain                  | Add a marker to selection or current line |
| Clear Uncertainty Marker at Cursor | Remove marker(s) on the current line      |
| Show All Uncertainty Markers       | Quick pick list of all markers            |
| Toggle Uncertainty Markers         | Enable/disable rendering                  |

---

## Settings

```json
{
  "uncertaintyMarkers.enabled": true,
  "uncertaintyMarkers.defaultExpiryDays": 0
}
```

---

## Use Cases

### “Future me needs the truth”

You’ll see you were uncertain — before you trust it blindly.

### Code reviews

Mark “copied from reference” or “edge cases unknown” without commenting noise.

### Stabilization passes

Set markers to expire in 7 days so you naturally revisit them.

---

## License

MIT License — see [LICENSE](LICENSE).
