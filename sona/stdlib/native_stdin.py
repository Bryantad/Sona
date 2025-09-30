"""Native stdin helpers used by Sona's runtime."""

from __future__ import annotations

import os


class StdinModule:
    def input(self, prompt: str = "") -> str:
        return __builtins__["input"](str(prompt))

    def read_line(self, prompt: str = "") -> str:
        return self.input(prompt)


native_stdin = StdinModule()


if os.environ.get("DEBUG", "").lower() in ("1", "true", "yes"):
    print("[DEBUG] native_stdin module loaded")


__all__ = ["native_stdin"]
