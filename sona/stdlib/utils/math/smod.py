"""Compatibility shim for legacy ``utils.math.smod`` imports."""

from __future__ import annotations

from sona.stdlib import math as _math


math = _math
__all__ = ["math"]
