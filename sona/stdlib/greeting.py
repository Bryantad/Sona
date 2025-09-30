"""Sona standard library: friendly greeting helpers."""

from __future__ import annotations

import os


class GreetingModule:
    """Light-weight helper used by Sona programs for greetings."""

    def __init__(self) -> None:
        self._default_name = "friend"

    def say(self, message: str) -> str:
        return str(message)

    def hi(self) -> str:
        return "Hello there!"

    def hello(self, name: str | None = None) -> str:
        target = name or "World"
        return f"Hello, {target}!"

    def greet(self, name: str | None = None) -> str:
        target = name or self._default_name
        return f"Greetings, {target}!"

    def set_default(self, name: str) -> None:
        self._default_name = str(name)


greeting = GreetingModule()
__all__ = ["greeting"]

if (
    os.environ.get("SONA_DEBUG") == "1"
    and os.environ.get("SONA_MODULE_SILENT") != "1"
):
    print("[DEBUG] greeting module loaded")
