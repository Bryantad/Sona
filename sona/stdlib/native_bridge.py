"""Native bridge for .smod wrappers to access Python stdlib glue."""

from __future__ import annotations

import importlib


class NativeModuleProxy:
    """Expose native module attributes with optional prefix fallback."""

    def __init__(self, module, prefix: str):
        self._module = module
        self._prefix = prefix

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        if hasattr(self._module, name):
            return getattr(self._module, name)
        prefixed = f"{self._prefix}{name}"
        if hasattr(self._module, prefixed):
            return getattr(self._module, prefixed)
        raise AttributeError(name)


class NativeBridge:
    """Bridge exposing native stdlib helpers to .smod modules."""

    def __init__(self, module_name: str):
        self._module_name = module_name
        self._native = self._load_native(module_name)
        self._proxy = NativeModuleProxy(self._native, f"{module_name}_")

    def _load_native(self, module_name: str):
        candidates = [
            f"sona.stdlib.native_{module_name}",
            f"sona.stdlib.{module_name}",
        ]
        last_error = None
        for candidate in candidates:
            try:
                return importlib.import_module(candidate)
            except Exception as exc:
                last_error = exc
        raise ImportError(
            f"Could not load native layer for {module_name}: {last_error}"
        )

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        if name == self._module_name:
            return self._proxy
        if hasattr(self._native, name):
            return getattr(self._native, name)
        prefixed = f"{self._module_name}_{name}"
        if hasattr(self._native, prefixed):
            return getattr(self._native, prefixed)
        raise AttributeError(name)
