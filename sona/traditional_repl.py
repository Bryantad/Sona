"""Quarantined traditional REPL implementation.

The original file was heavily corrupted (invalid inline try blocks, malformed
elif chains, unterminated f-strings). It is disabled for v0.9.3 to keep the
quality pass focused. A clean REPL (possibly unified with cognitive mode) can
be reintroduced in a later version.
"""

from __future__ import annotations

from typing import Any

_NOTICE = (
    "The module 'sona.traditional_repl' is quarantined in v0.9.3 due to "
    "severe source corruption. Use the primary CLI entry points instead."
)


def __getattr__(name: str) -> Any:  # pragma: no cover
    raise RuntimeError(_NOTICE)


__all__: list[str] = []
