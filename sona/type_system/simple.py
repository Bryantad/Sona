"""Quarantined placeholder for `sona.type_system.simple`.

Original implementation archived at `legacy/type_system_simple_archived.py`.
Access raises until restored in later refactor phase.
"""

from __future__ import annotations

def __getattr__(name: str):  # pragma: no cover
    raise RuntimeError(
        "'sona.type_system.simple' has been quarantined. See legacy archive and 0.9.4 "
        "repair ticket for restoration."
    )

