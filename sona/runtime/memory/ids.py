"""ID and timestamp helpers for the persistent memory subsystem."""

from __future__ import annotations

from datetime import datetime, timezone
import uuid


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp with second precision."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def make_prefixed_id(prefix: str) -> str:
    """Create a compact prefixed identifier for stored memory objects."""
    normalized = prefix.strip().lower().replace(" ", "_") or "obj"
    return f"{normalized}_{uuid.uuid4().hex}"
