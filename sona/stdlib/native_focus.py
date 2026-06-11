"""Native backing for local focus-session helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


_current: dict[str, Any] | None = None
_history: list[dict[str, Any]] = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def focus_begin(name: Any, description: Any = "") -> dict[str, Any]:
    global _current
    _current = {
        "name": str(name),
        "description": str(description or ""),
        "started_at": _now(),
    }
    return dict(_current)


def focus_current() -> dict[str, Any] | None:
    return dict(_current) if _current else None


def focus_end(summary: Any = "") -> dict[str, Any] | None:
    global _current
    if _current is None:
        return None
    completed = dict(_current)
    completed["ended_at"] = _now()
    completed["summary"] = str(summary or "")
    _history.append(completed)
    _current = None
    return completed


end = focus_end


def focus_history() -> list[dict[str, Any]]:
    return list(_history)


def focus_is_active() -> bool:
    return _current is not None


def focus_clear() -> bool:
    global _current
    _current = None
    _history.clear()
    return True


__all__ = [
    "focus_begin",
    "focus_current",
    "focus_end",
    "end",
    "focus_history",
    "focus_is_active",
    "focus_clear",
]
