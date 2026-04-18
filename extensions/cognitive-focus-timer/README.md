# Cognitive Focus Timer: Neurodivergent-Friendly Pomodoro

[![Version](https://img.shields.io/badge/version-0.11.0-blue.svg)](https://github.com/Bryantad/Sona/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Marketplace](https://img.shields.io/badge/VS%20Code-Marketplace-blue)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.cognitive-focus-timer)
[![Part of Sona](https://img.shields.io/badge/part%20of-Sona%20Ecosystem-purple)](https://github.com/Bryantad/Sona)

---

A Visual Studio Code extension providing a **neurodivergent-friendly focus timer** with Pomodoro cycles, streak tracking, and session logging. Part of the **Sona cognitive accessibility ecosystem**.

> Built for minds that work differently — ADHD, autism, dyslexia, and anyone who needs structure without stress.

---

## Overview

Traditional timers demand attention. This one respects it.

The Cognitive Focus Timer lives quietly in your status bar, tracking focus sessions without interrupting your flow. It builds streaks to encourage consistency and logs sessions for self-reflection — all without popups, alerts, or guilt.

---

## Key Features

### Status Bar Widget

- **Live Countdown** — `🍅 23:45` always visible
- **Session State** — focus, break, paused indicators
- **Click to Control** — start, pause, skip without leaving your code

### Pomodoro Cycles

- **Configurable Durations** — focus (25min default), short break (5min), long break (15min)
- **Auto-Start Breaks** — optional automatic transitions
- **Long Break After N Sessions** — every 4 focus sessions by default
- **Audio Cues** — gentle optional sounds (can be disabled)

### Streak Tracking

- **Daily Goals** — set target focus sessions per day
- **Streak Counter** — consecutive days meeting your goal
- **Persistence** — survives VS Code restarts
- **No Shame Mode** — streaks reset quietly, no guilt messaging

### Session Logging

- **Automatic Recording** — every completed session saved
- **JSON Export** — `.focus-timer/sessions.json` in workspace
- **History View** — browse past sessions with timestamps
- **Stats Dashboard** — total focus time, average session length

### Accessibility First

- **Minimal Distractions** — no popups unless you want them
- **Gentle Transitions** — smooth state changes
- **Keyboard Friendly** — all commands via Command Palette
- **Theme Aware** — respects your color preferences

---

## Commands

| Command                   | Description                          |
| ------------------------- | ------------------------------------ |
| Focus Timer: Start        | Begin a focus session                |
| Focus Timer: Pause        | Pause current timer                  |
| Focus Timer: Stop         | End session and log                  |
| Focus Timer: Skip         | Skip to next phase (break → focus)   |
| Focus Timer: Show Stats   | Open statistics dashboard            |
| Focus Timer: Show History | Browse past sessions                 |
| Focus Timer: Reset Streak | Clear streak (confirmation required) |
| Focus Timer: Configure    | Open settings                        |

---

## Settings

```json
{
  "focusTimer.focusDuration": 25,
  "focusTimer.shortBreakDuration": 5,
  "focusTimer.longBreakDuration": 15,
  "focusTimer.sessionsBeforeLongBreak": 4,
  "focusTimer.autoStartBreaks": true,
  "focusTimer.autoStartFocus": false,
  "focusTimer.dailyGoal": 8,
  "focusTimer.enableSounds": false,
  "focusTimer.showNotifications": false,
  "focusTimer.logSessions": true
}
```

---

## Session Log Format

Sessions are stored in `.focus-timer/sessions.json`:

```json
{
  "sessions": [
    {
      "type": "focus",
      "startTime": "2025-01-20T10:00:00Z",
      "endTime": "2025-01-20T10:25:00Z",
      "duration": 25,
      "completed": true
    }
  ],
  "streaks": {
    "current": 5,
    "longest": 12,
    "lastActiveDate": "2025-01-20"
  }
}
```

---

## Use Cases

### Deep Work Sessions

> "I need to focus for 2 hours without checking my phone"

Stack multiple Pomodoro cycles with automatic breaks.

### ADHD Time Blindness

> "I have no sense of how long I've been working"

The status bar keeps you grounded in time.

### Building Habits

> "I want to code every day but keep forgetting"

Streaks create gentle accountability.

### Self-Reflection

> "How much did I actually focus this week?"

Session logs provide honest data.

---

## Neurodivergent Design Principles

This timer was built with specific accessibility goals:

1. **No Guilt** — missed streaks reset without shame messaging
2. **No Interruption** — notifications are opt-in, not default
3. **No Pressure** — pause and resume anytime
4. **No Complexity** — one click to start, one click to stop
5. **No Judgment** — your sessions, your pace

---

## Part of the Sona Ecosystem

Cognitive Focus Timer complements Sona's accessibility features:

- **Focus Mode** — reduce visual noise during focus sessions
- **Working Memory** — capture thoughts without breaking flow
- **Cognitive Load Awareness** — know when you're overextending

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
  <i>Built with 🍅 by WayCore Inc.</i>
</p>
