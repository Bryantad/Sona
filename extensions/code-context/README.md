# Code Context: Developer Intent Memory

[![Version](https://img.shields.io/badge/version-0.11.0-blue.svg)](https://github.com/Bryantad/Sona/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Marketplace](https://img.shields.io/badge/VS%20Code-Marketplace-blue)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.code-context)
[![Part of Sona](https://img.shields.io/badge/part%20of-Sona%20Ecosystem-purple)](https://github.com/Bryantad/Sona)

---

A Visual Studio Code extension that **remembers _why_ code exists**, not just what it does. Part of the **Sona cognitive accessibility ecosystem**.

> "Code Context is a memory layer, not a documentation or automation tool."

---

## Overview

Developers don't forget **syntax** — they forget **decisions**.

- Comments explain _what_
- Docs explain _how_
- Git explains _when_

Nothing explains: **"Why did I do this again?"**

Code Context fills this gap by letting you attach invisible intent notes to any code block. No polluting comments. No guessing. No cognitive decay.

---

## Key Features

### Context Notes

- **Add Context Note** (`Ctrl+Shift+N`) — attach intent memory to selected code
- **Category Quick-Pick** — 💡 Decision, 🐛 Bug Fix, ⚠️ Temporary, 🔄 Refactor, 📝 Note
- **Reason Types** — semantic tags: TEMP, WORKAROUND, SECURITY, PERFORMANCE, LEGACY
- **Hover Display** — rich tooltips with note, age, and git commit hint

### Cognitive Awareness

- **Stale Intent Reminders** — "⚠️ This decision is 92 days old" (passive, no popups)
- **Context Density Indicator** — status bar shows `💭 3 (⚠️ 1 stale)`
- **Git Blame Hint** — "near commit abc123" for temporal context

### Organization

- **Explorer Sidebar** — "Context Notes" tree view grouped by file
- **Quick Navigation** — click to jump to any note
- **Export to Markdown** — document your decisions

### Storage Options

- **Workspace State** — private, local-only (default)
- **Git Sync** — `.code-context.json` for team sharing (opt-in)

---

## Commands

| Command             | Keybinding     | Description                       |
| ------------------- | -------------- | --------------------------------- |
| Add Context Note    | `Ctrl+Shift+N` | Attach a note to selected code    |
| View Context Note   | —              | View note at current line         |
| Edit Context Note   | —              | Modify existing note              |
| Delete Context Note | —              | Remove a note                     |
| Show All Notes      | —              | Quick pick all notes in workspace |
| Export Notes        | —              | Export as Markdown documentation  |
| Clear Stale Notes   | —              | Bulk remove old notes             |

---

## Settings

```json
{
  "codeContext.showInlineMarkers": true,
  "codeContext.showHoverNotes": true,
  "codeContext.markerStyle": "emoji",
  "codeContext.staleAfterDays": 30,
  "codeContext.syncWithGit": false,
  "codeContext.showGitBlameHint": true,
  "codeContext.showStatusBarIndicator": true
}
```

---

## Use Cases

### Personal Development

> "I wrote this at 2am... why?"

Now you'll know.

### Code Reviews

> "Why is this code structured this way?"

Leave context before the review.

### Onboarding

> "This looks weird but it's intentional"

New team members see reasoning instantly.

### Technical Debt

> "Leave this until after refactor phase 2"

Track temporary code without comment clutter.

---

## Part of the Sona Ecosystem

Code Context is designed to complement **Sona's cognitive accessibility features**:

- **Focus Mode** — reduce distraction during deep work
- **Working Memory** — track short-term goals and decisions
- **Intent Declarations** — explicit goal tracking at the language level

Together, these tools create a **cognitive platform** for developers who think differently.

---

## Philosophy

This extension follows three principles:

1. **Preserve intent, not syntax** — we remember _why_, not _what_
2. **Stay passive, not intrusive** — no popups, no notifications
3. **Enable recall, not enforcement** — suggestions, not requirements

---

## Requirements

- VS Code 1.74.0 or higher
- No additional dependencies

---

## Links

- [Sona Language](https://github.com/Bryantad/Sona)
- [Report Issues](https://github.com/Bryantad/Sona/issues)
- [Changelog](CHANGELOG.md)

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <i>Built with 💭 by WayCore Inc.</i>
</p>
