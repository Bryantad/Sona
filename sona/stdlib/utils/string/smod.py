"""Quarantined corrupted stdlib string module.

The original implementation was syntactically invalid. For v0.9.3 quality
work it is replaced with a minimal stub to prevent import-time failures.
"""

from __future__ import annotations

from typing import Any

_MSG = (
    "The experimental stdlib string module is quarantined in v0.9.3 due to "
    "corrupted source. Provide a clean implementation before re‑enabling."
)


def __getattr__(name: str) -> Any:  # pragma: no cover
    raise RuntimeError(_MSG)


__all__: list[str] = []
