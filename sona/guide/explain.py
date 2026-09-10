"""Pure catalog lookup and explanation of caller-supplied canonical diagnostics."""

from __future__ import annotations

from .catalog import CATALOG, CATALOG_VERSION
from .models import GuideError, GuideRequest, GuideResponse, GuideSection


def explain(request: GuideRequest) -> GuideResponse:
    entry = CATALOG.get(request.diagnostic_id)
    if entry is None:
        raise GuideError(
            "SONA-GUIDE-001",
            "Sona Guide has no explanation for this diagnostic identifier.",
            "Use the exact identifier from Sona's diagnostic. "
            "The original diagnostic remains authoritative.",
        )
    supplied = request.diagnostic
    # Retain the canonical redaction boundary for any caller-supplied text.
    original = supplied.to_dict() if supplied is not None else None
    summary = original["message"] if original is not None else entry.summary
    why = getattr(entry, request.style)
    sections = [
        GuideSection("what", "What happened" if original else "Meaning", summary),
        GuideSection("why", "Why this happens", why),
    ]
    if original is not None and original["file"] != "<unknown>":
        sections.append(GuideSection(
            "where", "Where",
            f"{original['file']}:{original['start_line']}:{original['start_column']}",
        ))
    next_step = entry.next_step
    if original is not None and original["hint"]:
        next_step = original["hint"] + "\n" + next_step
    sections.extend((
        GuideSection("next", "Next step", next_step),
        GuideSection("example", "Example", entry.example),
        GuideSection("concepts", "Related concepts", ", ".join(entry.concepts)),
    ))
    return GuideResponse(
        request=request, summary=summary, topic=entry.topic,
        catalog_version=CATALOG_VERSION, sections=tuple(sections), concept_ids=entry.concepts,
    )
