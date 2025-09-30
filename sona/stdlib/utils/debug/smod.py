"""Debug utilities for Sona."""

from __future__ import annotations

import os
from typing import Any


def debug(msg: Any) -> None:
    if os.environ.get("SONA_DEBUG") == "1":
        print(f"[DEBUG] {msg}")


class DebugModule:
    def type_of(self, value: Any) -> str:
        return type(value).__name__

    def dir_of(self, value: Any) -> list[str]:
        return dir(value)


debug_module = DebugModule()
__all__ = ["debug", "debug_module"]
