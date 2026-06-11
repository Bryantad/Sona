"""Native backing for the public Sona `profile` accessibility module.

Profile state is process-local and optional. Profile names are presets, not
diagnoses, and no state is persisted by this module.
"""

from __future__ import annotations

from typing import Any


_AVAILABLE = ["adhd", "dyslexia", "autism", "low-stimulation", "custom"]
_active: list[str] = []
_options: dict[str, Any] = {}


def _normalize_name(name: Any) -> str:
    candidate = str(name).strip().lower()
    if candidate not in _AVAILABLE:
        raise ValueError(f"Unsupported profile preset: {name}")
    return candidate


def profile_activate(name: Any) -> dict[str, Any]:
    candidate = _normalize_name(name)
    _active.clear()
    _active.append(candidate)
    return profile_current()


def profile_activate_many(names: Any) -> dict[str, Any]:
    if not isinstance(names, list):
        raise ValueError("profiles must be a list")
    selected = []
    for name in names:
        candidate = _normalize_name(name)
        if candidate not in selected:
            selected.append(candidate)
    _active[:] = selected
    return profile_current()


def profile_current() -> dict[str, Any]:
    return {"active": list(_active), "options": dict(_options)}


def profile_available() -> list[str]:
    return list(_AVAILABLE)


def profile_reset() -> dict[str, Any]:
    _active.clear()
    _options.clear()
    return profile_current()


def profile_configure(options: Any) -> dict[str, Any]:
    if not isinstance(options, dict):
        raise ValueError("profile options must be a map")
    _options.update(options)
    return profile_current()


__all__ = [
    "profile_activate",
    "profile_activate_many",
    "profile_current",
    "profile_available",
    "profile_reset",
    "profile_configure",
]
