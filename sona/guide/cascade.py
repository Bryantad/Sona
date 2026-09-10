"""Reviewed Focus Mode grouping for canonical diagnostics.

Focus Mode is a presentation layer. It never changes, rewrites, or drops the
complete canonical diagnostic sequence.
"""

from __future__ import annotations

from collections.abc import Sequence

from sona.developer_intelligence.diagnostics import Diagnostic

from .catalog import CATALOG_VERSION
from .models import DiagnosticRelation, FocusResult, GuideError

_DELIMITER_ROOTS = {"SONA-PARSE-003"}
_DELIMITER_SECONDARIES = {
    "SONA-PARSE-001",
    "SONA-PARSE-003",
    "SONA-RUNTIME-003",
    "SONA-NATIVE-RUNTIME-003",
}
_DELIMITER_RULE = "guide.cascade.unclosed-delimiter-downstream"


def focus_diagnostics(
    diagnostics: Sequence[Diagnostic],
    *,
    density: str = "normal",
    quiet: bool = False,
) -> FocusResult:
    canonical = tuple(diagnostics)
    if type(quiet) is not bool or any(not isinstance(item, Diagnostic) for item in canonical):
        raise GuideError(
            "SONA-GUIDE-002",
            "The Focus request contains a non-canonical diagnostic.",
            "Pass diagnostics produced by Sona's canonical diagnostic pipeline.",
        )

    relations = _reviewed_relations(canonical)
    secondary_indices = {relation.secondary_index for relation in relations}
    root_indices = tuple(
        index for index in _ranked_indices(canonical, relations)
        if index not in secondary_indices
    )

    eligible = tuple(index for index, item in enumerate(canonical) if not quiet or item.severity == "error")
    visible_roots = tuple(index for index in root_indices if index in eligible)
    if density == "complete":
        visible_indices = eligible
    elif density == "focused":
        visible_indices = (visible_roots or eligible)[:1]
    elif density == "normal":
        visible_indices = visible_roots or eligible
    else:
        raise GuideError(
            "SONA-GUIDE-002",
            "The Focus request is invalid.",
            "Use focused, normal, or complete diagnostic density.",
        )

    return FocusResult(
        density=density,
        complete_diagnostics=canonical,
        visible_indices=visible_indices,
        root_indices=root_indices,
        relations=relations,
        catalog_version=CATALOG_VERSION,
        quiet=quiet,
    )


def render_focus_text(result: FocusResult) -> str:
    payload = result.to_dict()
    lines = [
        "Sona Guide Focus",
        "",
        f"Density      {result.density}",
        f"Quiet        {str(result.quiet).lower()}",
        (
            f"Diagnostics  {len(result.complete_diagnostics)} total, "
            f"{len(result.visible_indices)} shown, {result.suppressed_count} "
            f"{'deferred' if result.quiet else 'grouped'}"
        ),
    ]
    if not result.complete_diagnostics:
        lines.extend(("", "No diagnostics reported."))
        return _terminal_text("\n".join(lines))

    related_counts: dict[int, int] = {}
    for relation in result.relations:
        related_counts[relation.primary_index] = related_counts.get(relation.primary_index, 0) + 1

    for display_index, diagnostic_index in enumerate(result.visible_indices, start=1):
        diagnostic = payload["diagnostics"][diagnostic_index]
        location = _location(diagnostic)
        lines.extend((
            "",
            f"[{display_index}] {diagnostic['diagnostic_id']}: {diagnostic['message']}",
        ))
        if location:
            lines.append(f"    {location}")
        if diagnostic.get("hint"):
            lines.append(f"    hint: {diagnostic['hint']}")
        grouped = related_counts.get(diagnostic_index, 0)
        if grouped:
            lines.append(f"    {grouped} related diagnostic(s) grouped by reviewed rules")
    if result.suppressed_count:
        lines.extend(("", "Use --density complete --no-quiet to see every canonical diagnostic."))
    return _terminal_text("\n".join(lines))


def _reviewed_relations(diagnostics: tuple[Diagnostic, ...]) -> tuple[DiagnosticRelation, ...]:
    relations: list[DiagnosticRelation] = []
    for primary_index, primary in enumerate(diagnostics):
        if primary.diagnostic_id not in _DELIMITER_ROOTS:
            continue
        for secondary_index, secondary in enumerate(diagnostics):
            if secondary_index <= primary_index:
                continue
            if _is_delimiter_secondary(primary, secondary):
                relations.append(DiagnosticRelation(
                    primary_index=primary_index,
                    secondary_index=secondary_index,
                    rule_id=_DELIMITER_RULE,
                    confidence="reviewed",
                    reason=(
                        "An unclosed delimiter can cause later parser/name "
                        "diagnostics in the same file to be presentation noise."
                    ),
                ))
    return tuple(relations)


def _is_delimiter_secondary(primary: Diagnostic, secondary: Diagnostic) -> bool:
    if secondary.diagnostic_id not in _DELIMITER_SECONDARIES:
        return False
    if secondary.diagnostic_id == primary.diagnostic_id:
        return False
    if primary.span.file != secondary.span.file:
        return False
    return _position_key(secondary) >= _position_key(primary)


def _ranked_indices(
    diagnostics: tuple[Diagnostic, ...],
    relations: tuple[DiagnosticRelation, ...],
) -> tuple[int, ...]:
    primary_with_dependents = {relation.primary_index for relation in relations}
    return tuple(sorted(
        range(len(diagnostics)),
        key=lambda index: (
            0 if index in primary_with_dependents else 1,
            _severity_rank(diagnostics[index].severity),
            _position_key(diagnostics[index]),
            diagnostics[index].diagnostic_id,
            index,
        ),
    ))


def _severity_rank(severity: str) -> int:
    return {"error": 0, "warning": 1, "info": 2, "hint": 3}.get(severity, 4)


def _position_key(diagnostic: Diagnostic) -> tuple[str, int, int, int]:
    return (
        diagnostic.span.file,
        diagnostic.span.start_line,
        diagnostic.span.start_column,
        diagnostic.span.end_column or diagnostic.span.start_column + 1,
    )


def _location(diagnostic: dict) -> str:
    file = diagnostic.get("file")
    if not file or file == "<unknown>":
        return ""
    return f"{file}:{diagnostic.get('start_line', 1)}:{diagnostic.get('start_column', 1)}"


def _terminal_text(text: str) -> str:
    return "".join(
        char if char in "\n\t" or char.isprintable() else f"\\u{ord(char):04x}"
        for char in text
    )
