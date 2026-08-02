"""Canonical console-input module for Sona programs."""

from __future__ import annotations

from .errors import StdlibError


def read(prompt: str | None = None) -> str:
    try:
        return input("" if prompt is None else str(prompt))
    except (EOFError, OSError) as error:
        raise StdlibError(
            "SONA-IO-001",
            "console input is unavailable",
            operation="stdin.read",
            suggestion="Provide standard input or avoid interactive input in this run.",
            cause=error,
        ) from error


__all__ = ["read"]
