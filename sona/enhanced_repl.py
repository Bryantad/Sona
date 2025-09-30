"""Quarantined placeholder for `sona.enhanced_repl`.

The original experimental enhanced REPL implementation was syntactically
corrupted and has been archived at `legacy/enhanced_repl_archived.py`.
Feature disabled for 0.9.3 stabilization.
"""
from __future__ import annotations

def __getattr__(name: str):  # pragma: no cover - quarantine guard
    raise RuntimeError(
        "`sona.enhanced_repl` is quarantined. See legacy archive and planned "
        "rewrite."
    )
