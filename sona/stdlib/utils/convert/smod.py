"""Type conversion helpers."""

from __future__ import annotations

import os
from typing import Any


class Convert:
    def to_str(self, value: Any) -> str:
        return str(value)

    def to_float(self, value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def to_int(self, value: Any) -> int | None:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None


convert = Convert()
__all__ = ["convert"]


if (
    os.environ.get("SONA_DEBUG") == "1"
    and os.environ.get("SONA_MODULE_SILENT") != "1"
):
    print("[DEBUG] convert module loaded")
