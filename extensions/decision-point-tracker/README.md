# Decision Point Tracker

[![Version](https://img.shields.io/badge/version-0.11.0-blue.svg)](https://github.com/Bryantad/Sona/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Marketplace](https://img.shields.io/badge/VS%20Code-Marketplace-blue)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.decision-point-tracker)
[![Part of Sona](https://img.shields.io/badge/part%20of-Sona%20Ecosystem-purple)](https://github.com/Bryantad/Sona)

---

A Visual Studio Code extension that helps you track **moments of decision**, not just changes.

Git tracks what changed.

This tracks _decision gravity_.

---

## Overview

Some edits are routine.

Others are turning points:

- refactors
- restructures
- deletions
- renames

Decision Point Tracker detects **significant edits** and quietly offers a prompt in the status bar:

**🧭 Decision point?**

If you confirm, it adds a minimal gutter marker with timestamp and optional reason.

---

## Key Features

- **Significant edit detection** — based on changed chars/lines
- **Non-intrusive prompt** — status bar only (no modal popups)
- **Decision markers** — gutter icon + hover details
- **Decision timeline** — quick pick list of all decision points

---

## Commands

| Command                        | Description                                    |
| ------------------------------ | ---------------------------------------------- |
| Decision Point: Confirm        | Confirm or dismiss the pending decision prompt |
| Show All Decision Points       | List + jump to decision markers                |
| Clear Decision Point at Cursor | Remove marker at current line                  |
| Toggle Decision Point Tracker  | Enable/disable detection and rendering         |

---

## Settings

```json
{
  "decisionPointTracker.enabled": true,
  "decisionPointTracker.minChangedChars": 80,
  "decisionPointTracker.minChangedLines": 4
}
```

---

## Use Cases

### Reasoning topology

Over time, your codebase gains a “decision map” you can revisit.

### Refactor documentation

Capture “why we changed this structure” without heavy docs.

---

## License

MIT License — see [LICENSE](LICENSE).
