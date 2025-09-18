"""Quarantined placeholder for `sona.working_memory`.

The original implementation is archived at `legacy/working_memory_archived.py`.
Access raises to prevent usage during 0.9.3 stabilization.
"""

from __future__ import annotations

def __getattr__(name: str):  # pragma: no cover - guard
    raise RuntimeError(
        "'sona.working_memory' has been quarantined. See legacy archive and 0.9.4 "
        "repair ticket for restoration."
    )

