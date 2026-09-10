"""Adapters for canonical Python and Native diagnostic JSON."""

from __future__ import annotations

from sona.developer_intelligence.diagnostics import Diagnostic, SourceSpan

from .models import GuideError


def diagnostic_from_payload(payload, default_file: str = "<unknown>") -> Diagnostic:
    try:
        if not isinstance(payload, dict):
            raise TypeError
        if isinstance(payload.get("diagnostic"), dict):
            payload = payload["diagnostic"]
        identifier = payload.get("diagnostic_id")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError
        location = payload.get("location") or {}
        if not isinstance(location, dict):
            raise TypeError

        def span(item, fallback=None):
            fallback = fallback or {}
            start_line = item.get("start_line", fallback.get("line", 1))
            start_column = item.get("start_column", fallback.get("column", 1))
            end_line = item.get("end_line", fallback.get("end_line"))
            end_column = item.get("end_column", fallback.get("end_column"))
            for value in (start_line, start_column, end_line, end_column):
                if value is not None and (type(value) is not int or value < 1):
                    raise ValueError
            return SourceSpan(
                file=item.get("file") or fallback.get("file") or default_file,
                start_line=start_line, start_column=start_column,
                end_line=end_line, end_column=end_column, node_type=item.get("node_type"),
            )

        severity = payload.get("severity", "error")
        if severity not in {"error", "warning", "info", "hint"}:
            raise ValueError
        for key in ("category", "message", "hint", "source", "suggestion"):
            if key in payload and not isinstance(payload[key], str):
                raise ValueError
        metadata = payload.get("metadata", {})
        if not isinstance(metadata, dict):
            raise TypeError
        return Diagnostic(
            diagnostic_id=identifier,
            category=payload.get("category", "runtime"),
            severity=severity,
            message=payload.get("message", "Diagnostic reported by Sona."),
            hint=payload.get("hint", payload.get("suggestion", "")),
            span=span(payload, location),
            source=payload.get("source", "sona"),
            related_locations=tuple(span(item) for item in payload.get("related_locations", [])),
            metadata=dict(metadata), legacy_code=payload.get("legacy_code", payload.get("code")),
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise GuideError(
            "SONA-GUIDE-002", "The diagnostic JSON is invalid.",
            "Pass the original canonical diagnostic object printed by Sona.",
        ) from exc
