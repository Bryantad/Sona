"""Quarantined placeholder for `sona.features.string_interpolation`.

Original archived at `legacy/features_string_interpolation_archived.py`.
Disabled during 0.9.3 stabilization due to severe syntax corruption. A clean
rewrite will land in a later release.
"""
from __future__ import annotations

__all__ = ["__getattr__"]


def __getattr__(name: str):  # pragma: no cover - quarantine guard
    raise RuntimeError(
        "`sona.features.string_interpolation` is quarantined. See legacy "
        "archive and planned rewrite ticket (>=0.9.4)."
    )
