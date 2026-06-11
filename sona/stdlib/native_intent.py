"""Native backing for local in-process intent notes."""

from __future__ import annotations

from typing import Any


_intents: dict[str, str] = {}


def intent_set(name: Any, description: Any) -> dict[str, str]:
    key = str(name)
    _intents[key] = str(description)
    return {"name": key, "description": _intents[key]}


def intent_get(name: Any) -> str | None:
    return _intents.get(str(name))


def intent_has(name: Any) -> bool:
    return str(name) in _intents


def intent_list() -> list[dict[str, str]]:
    return [
        {"name": name, "description": description}
        for name, description in sorted(_intents.items())
    ]


def intent_clear(name: Any) -> bool:
    return _intents.pop(str(name), None) is not None


def intent_clear_all() -> bool:
    _intents.clear()
    return True


__all__ = [
    "intent_set",
    "intent_get",
    "intent_has",
    "intent_list",
    "intent_clear",
    "intent_clear_all",
]
