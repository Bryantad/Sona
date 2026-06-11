"""Native backing for terminal-safe ANSI styling."""

from __future__ import annotations

import os
import re
import sys
from typing import Any


_enabled = False
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _supported() -> bool:
    return not os.getenv("NO_COLOR") and bool(getattr(sys.stdout, "isatty", lambda: False)())


def color_enable() -> bool:
    global _enabled
    _enabled = _supported()
    return _enabled


def color_disable() -> bool:
    global _enabled
    _enabled = False
    return _enabled


def color_is_enabled() -> bool:
    return _enabled and not os.getenv("NO_COLOR")


def _wrap(code: str, value: Any) -> str:
    text = str(value)
    if not color_is_enabled():
        return text
    return f"\x1b[{code}m{text}\x1b[0m"


def color_red(value: Any) -> str:
    return _wrap("31", value)


def color_green(value: Any) -> str:
    return _wrap("32", value)


def color_yellow(value: Any) -> str:
    return _wrap("33", value)


def color_blue(value: Any) -> str:
    return _wrap("34", value)


def color_bold(value: Any) -> str:
    return _wrap("1", value)


def color_dim(value: Any) -> str:
    return _wrap("2", value)


def color_reset() -> str:
    return "\x1b[0m" if color_is_enabled() else ""


def color_strip(value: Any) -> str:
    return _ANSI.sub("", str(value))


__all__ = [
    "color_enable",
    "color_disable",
    "color_is_enabled",
    "color_red",
    "color_green",
    "color_yellow",
    "color_blue",
    "color_bold",
    "color_dim",
    "color_reset",
    "color_strip",
]
