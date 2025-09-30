"""Quarantined placeholder for `sona.utils.suppress`.

Original corrupted version archived at `legacy/utils_suppress_archived.py`.
Access now raises to prevent reliance until repaired.
"""

from __future__ import annotations

def __getattr__(name: str):  # pragma: no cover
    raise RuntimeError(
        "'sona.utils.suppress' has been quarantined. See legacy archive and 0.9.4 "
        "repair ticket for planned restoration."
    )

