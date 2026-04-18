"""Native glue exposing :mod:`sona.stdlib.receipt` helpers to Sona.

Provides receipt-context primitives so running Sona code can append
structured events into the active execution receipt.
"""

from __future__ import annotations

from typing import Any


def receipt_append_event(
    event_type: Any,
    payload: Any = None,
    classification: Any = None,
) -> dict | None:
    """Append a structured event to the active receipt.

    Returns the event dict, or ``None`` if no context is active.
    """
    from sona.receipts import append_receipt_event

    et = str(event_type) if event_type is not None else "unknown"
    cls = str(classification) if classification not in (None, "") else "internal"
    pl: dict | None = None
    if payload is not None:
        if isinstance(payload, dict):
            pl = payload
        else:
            pl = {"value": payload}
    return append_receipt_event(et, payload=pl, classification=cls)


def receipt_has_context() -> bool:
    """Return *True* if a receipt context is currently active."""
    from sona.receipts import get_active_receipt

    return get_active_receipt() is not None


def receipt_current_id() -> str | None:
    """Return the receipt hash of the active receipt, or ``None``."""
    from sona.receipts import get_active_receipt

    ctx = get_active_receipt()
    if ctx is None:
        return None
    return ctx.get("receipt_hash")


def receipt_event_count() -> int:
    """Return the number of events in the active receipt context."""
    from sona.receipts import get_active_receipt

    ctx = get_active_receipt()
    if ctx is None:
        return 0
    return len(ctx.get("execution", {}).get("events", []))


__all__ = [
    "receipt_append_event",
    "receipt_has_context",
    "receipt_current_id",
    "receipt_event_count",
]
