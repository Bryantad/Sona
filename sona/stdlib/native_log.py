"""Native backing for the public Sona `log` module.

The module keeps configuration in process memory only. It does not open files,
create directories, or mutate user configuration at import time.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any


_LEVELS = {"debug": 10, "info": 20, "warn": 30, "error": 40}
_level = "info"
_format = "plain"
_events: list[dict[str, Any]] = []
_SECRET_KEYS = {"api_key", "apikey", "authorization", "password", "secret", "token"}


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): ("[redacted]" if str(key).lower() in _SECRET_KEYS else _redact(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _record(level: str, message: Any, fields: Any = None, *, name: str | None = None) -> dict[str, Any]:
    event = {
        "timestamp": _timestamp(),
        "level": level,
        "message": str(message),
        "fields": _redact(fields if isinstance(fields, dict) else {}),
    }
    if name is not None:
        event["name"] = str(name)
    if _LEVELS.get(level, 20) >= _LEVELS.get(_level, 20):
        _events.append(event)
    return event


def log_debug(message: Any, fields: Any = None) -> dict[str, Any]:
    return _record("debug", message, fields)


def log_info(message: Any, fields: Any = None) -> dict[str, Any]:
    return _record("info", message, fields)


def log_warn(message: Any, fields: Any = None) -> dict[str, Any]:
    return _record("warn", message, fields)


def log_error(message: Any, fields: Any = None) -> dict[str, Any]:
    return _record("error", message, fields)


def log_event(name: Any, fields: Any = None) -> dict[str, Any]:
    return _record("info", str(name), fields, name=str(name))


def log_set_level(level: Any) -> str:
    global _level
    candidate = str(level).lower()
    if candidate not in _LEVELS:
        raise ValueError(f"Unsupported log level: {level}")
    _level = candidate
    return _level


def log_get_level() -> str:
    return _level


def log_set_format(mode: Any) -> str:
    global _format
    candidate = str(mode).lower()
    if candidate not in {"plain", "structured", "json", "compact"}:
        raise ValueError(f"Unsupported log format: {mode}")
    _format = candidate
    return _format


def log_get_format() -> str:
    return _format


def log_history(limit: Any = 20) -> list[dict[str, Any]]:
    count = max(0, int(limit or 20))
    return list(_events[-count:])


def log_clear() -> bool:
    _events.clear()
    return True


def log_format_event(event: Any, mode: Any = None) -> str:
    target = str(mode or _format).lower()
    payload = event if isinstance(event, dict) else {"message": str(event)}
    if target == "json":
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))
    if target == "compact":
        return f"{payload.get('level', 'info')}:{payload.get('message', '')}"
    if target == "structured":
        return json.dumps(payload, sort_keys=True)
    return f"[{payload.get('level', 'info')}] {payload.get('message', '')}"


__all__ = [
    "log_debug",
    "log_info",
    "log_warn",
    "log_error",
    "log_event",
    "log_set_level",
    "log_get_level",
    "log_set_format",
    "log_get_format",
    "log_history",
    "log_clear",
    "log_format_event",
]
