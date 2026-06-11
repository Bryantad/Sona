"""Shared in-memory cognitive accessibility runtime.

The runtime is local-only by default. It does not persist state or transmit
data unless a future caller explicitly opts into a storage backend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AccessibilityRegistry:
    modules: dict[str, dict[str, Any]] = field(default_factory=dict)

    def register(self, name: str, metadata: dict[str, Any]) -> dict[str, Any]:
        payload = {"name": name, **metadata}
        self.modules[name] = payload
        return dict(payload)

    def list(self) -> list[dict[str, Any]]:
        return [dict(self.modules[name]) for name in sorted(self.modules)]


@dataclass
class AccessibilitySession:
    config: dict[str, Any] = field(default_factory=dict)
    notes: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)

    def reset(self) -> None:
        self.config.clear()
        self.notes.clear()
        self.history.clear()


registry = AccessibilityRegistry()
session = AccessibilitySession()
