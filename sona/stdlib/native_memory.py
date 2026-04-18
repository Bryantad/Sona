"""Native bridge factory for the `memory` stdlib module."""

from __future__ import annotations

from sona.integrations.memory.native_module import MemoryNativeModuleBridge


def build_native_bridge(interpreter):
    return MemoryNativeModuleBridge(interpreter)


__all__ = ["build_native_bridge"]
