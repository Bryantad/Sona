"""
Persisted environment helpers for Sona CLI.

Stores AI mode preferences under ~/.sona/ai-mode.json by default.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _sona_home() -> Path:
    override = os.getenv("SONA_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".sona"


def get_ai_mode_config_path() -> Path:
    return _sona_home() / "ai-mode.json"


def load_ai_mode_preferences() -> dict[str, Any]:
    path = get_ai_mode_config_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        "enable_cache": bool(data.get("enable_cache")),
        "enable_breaker": bool(data.get("enable_breaker")),
    }


def save_ai_mode_preferences(enable_cache: bool, enable_breaker: bool) -> Path:
    path = get_ai_mode_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "enable_cache": bool(enable_cache),
        "enable_breaker": bool(enable_breaker),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def clear_ai_mode_preferences() -> Path | None:
    path = get_ai_mode_config_path()
    if not path.exists():
        return None
    try:
        path.unlink()
    except Exception:
        return None
    return path


__all__ = [
    "get_ai_mode_config_path",
    "load_ai_mode_preferences",
    "save_ai_mode_preferences",
    "clear_ai_mode_preferences",
]
