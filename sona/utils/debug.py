"""Quarantined placeholder for `sona.utils.debug`.

Original corrupted version archived at `legacy/utils_debug_archived.py`.
Any access raises to prevent silent reliance during the 0.9.3 quality sweep.
"""

from __future__ import annotations

def __getattr__(name: str):  # pragma: no cover - guard
    raise RuntimeError(
        "'sona.utils.debug' has been quarantined. See legacy archive and 0.9.4 "
        "repair ticket for reimplementation."
    )

