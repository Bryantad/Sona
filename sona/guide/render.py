"""Presentation density only; canonical diagnostic data is never filtered here."""

from __future__ import annotations

from .models import GuideResponse


def _terminal_text(text: str) -> str:
    """Keep lines and tabs readable without allowing embedded terminal controls."""
    return "".join(
        char if char in "\n\t" or char.isprintable() else f"\\u{ord(char):04x}"
        for char in text
    )


def render_text(response: GuideResponse) -> str:
    request = response.request
    if request.mode == "expert":
        code = request.diagnostic.legacy_code if request.diagnostic is not None else None
        prefix = f"{code} " if code else ""
        where = next((section.body for section in response.sections if section.key == "where"), "")
        location = f" ({where})" if where else ""
        return _terminal_text(f"{prefix}{request.diagnostic_id}: {response.summary}{location}")

    lines = [f"Sona Guide - {request.diagnostic_id}"]
    if response.basis == "catalog-reference":
        lines.extend(("", "Reference explanation; no program or receipt was examined."))
    selected = response.sections
    if request.mode == "balanced":
        selected = tuple(section for section in selected if section.key in {"what", "where", "next"})
    for section in selected:
        lines.extend(("", section.title, section.body))
    return _terminal_text("\n".join(lines))
