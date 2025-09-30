"""Quarantined placeholder for `sona.unified_interpreter`.

Original implementation was syntactically corrupted and has been archived under
`legacy/unified_interpreter_archived.py`. Accessing this module directly now
raises a RuntimeError to prevent accidental runtime usage during 0.9.3 cycle.
"""

from __future__ import annotations

def __getattr__(name: str):  # pragma: no cover - deliberate guard
    raise RuntimeError(
        "The original 'sona.unified_interpreter' module is quarantined due to "
        "severe syntax corruption. See 'legacy/unified_interpreter_archived.py' "
        "and the 0.9.4 repair ticket for restoration work."
    )

