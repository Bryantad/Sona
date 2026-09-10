"""Versioned explanation contracts shared by Guide clients."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sona.developer_intelligence.diagnostics import Diagnostic

MODES = ("guided", "balanced", "expert")
STYLES = ("simple", "visual", "technical")
DENSITIES = ("focused", "normal", "complete")


class GuideError(Exception):
    """A safe Guide infrastructure diagnostic; never a compiler error alias."""

    def __init__(self, diagnostic_id: str, message: str, hint: str):
        super().__init__(message)
        self.diagnostic_id = diagnostic_id
        self.message = message
        self.hint = hint

    def to_dict(self) -> dict[str, str]:
        return {
            "diagnostic_id": self.diagnostic_id,
            "category": "guide",
            "severity": "error",
            "message": self.message,
            "hint": self.hint,
        }


@dataclass(frozen=True, slots=True)
class GuideRequest:
    diagnostic_id: str = ""
    diagnostic: Diagnostic | None = None
    mode: str = "guided"
    style: str = "simple"
    density: str = "normal"
    fact_kind: str | None = None
    facts: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.fact_kind is not None or self.facts is not None:
            if (self.fact_kind not in ("proof", "guardian") or not isinstance(self.facts, dict)
                    or self.diagnostic_id or self.diagnostic is not None
                    or self.mode not in MODES or self.style not in STYLES or self.density not in DENSITIES):
                raise GuideError("SONA-GUIDE-002", "The Guide fact request is invalid.",
                                 "Use one provider fact object without a language diagnostic.")
            return
        if (
            not isinstance(self.diagnostic_id, str)
            or not 1 <= len(self.diagnostic_id) <= 96
            or self.mode not in MODES
            or self.style not in STYLES
            or self.density not in DENSITIES
            or (self.diagnostic is not None and not isinstance(self.diagnostic, Diagnostic))
        ):
            raise GuideError(
                "SONA-GUIDE-002", "The Guide request is invalid.",
                "Use a canonical diagnostic and a documented presentation setting.",
            )
        if self.diagnostic is not None and self.diagnostic.diagnostic_id != self.diagnostic_id:
            raise GuideError(
                "SONA-GUIDE-002", "The Guide request does not match its diagnostic.",
                "Keep the original canonical diagnostic identifier.",
            )

    def to_dict(self) -> dict[str, Any]:
        if self.fact_kind is not None:
            from copy import deepcopy
            return {"schema_version": 1, "fact_kind": self.fact_kind, "facts": deepcopy(self.facts),
                    "mode": self.mode, "style": self.style, "density": self.density}
        return {
            "schema_version": 1,
            "diagnostic_id": self.diagnostic_id,
            "diagnostic": self.diagnostic.to_dict() if self.diagnostic is not None else None,
            "mode": self.mode,
            "style": self.style,
            "density": self.density,
        }


@dataclass(frozen=True, slots=True)
class GuideSection:
    key: str
    title: str
    body: str

    def to_dict(self) -> dict[str, str]:
        return {"key": self.key, "title": self.title, "body": self.body}


@dataclass(frozen=True, slots=True)
class SourceEdit:
    document: str
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    expected: str
    replacement: str
    rule_id: str
    title: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if (
            not self.document
            or not self.rule_id
            or not self.title
            or min(self.start_line, self.start_column, self.end_line, self.end_column) < 1
            or not isinstance(self.expected, str)
            or not isinstance(self.replacement, str)
        ):
            raise GuideError(
                "SONA-GUIDE-002",
                "The source edit is invalid.",
                "Use an exact range, expected text, and replacement text.",
            )
        if (self.end_line, self.end_column) < (self.start_line, self.start_column):
            raise GuideError(
                "SONA-GUIDE-002",
                "The source edit range is invalid.",
                "The end position must not come before the start position.",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "document": self.document,
            "range": {
                "start_line": self.start_line,
                "start_column": self.start_column,
                "end_line": self.end_line,
                "end_column": self.end_column,
            },
            "expected": self.expected,
            "replacement": self.replacement,
            "rule_id": self.rule_id,
            "title": self.title,
            "stale_protection": "expected-original",
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class GuideFix:
    rule_id: str
    title: str
    confidence: str
    edits: tuple[SourceEdit, ...]
    rationale: str

    def __post_init__(self) -> None:
        if not self.rule_id or not self.title or not self.edits:
            raise GuideError(
                "SONA-GUIDE-002",
                "The Guide fix is invalid.",
                "A fix must contain at least one stale-protected source edit.",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "edits": [edit.to_dict() for edit in self.edits],
        }


@dataclass(frozen=True, slots=True)
class DiagnosticRelation:
    primary_index: int
    secondary_index: int
    rule_id: str
    confidence: str
    reason: str

    def __post_init__(self) -> None:
        if (
            self.primary_index < 0
            or self.secondary_index < 0
            or self.primary_index == self.secondary_index
            or not self.rule_id
            or not self.confidence
        ):
            raise GuideError(
                "SONA-GUIDE-002",
                "The diagnostic relation is invalid.",
                "Use reviewed relation rules between distinct diagnostics.",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_index": self.primary_index,
            "secondary_index": self.secondary_index,
            "rule_id": self.rule_id,
            "confidence": self.confidence,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class FocusResult:
    density: str
    complete_diagnostics: tuple[Diagnostic, ...]
    visible_indices: tuple[int, ...]
    root_indices: tuple[int, ...]
    relations: tuple[DiagnosticRelation, ...]
    catalog_version: int
    quiet: bool = False

    def __post_init__(self) -> None:
        if self.density not in DENSITIES:
            raise GuideError(
                "SONA-GUIDE-002",
                "The Focus request is invalid.",
                "Use a documented diagnostic density.",
            )
        count = len(self.complete_diagnostics)
        if any(index < 0 or index >= count for index in self.visible_indices + self.root_indices):
            raise GuideError(
                "SONA-GUIDE-002",
                "The Focus result references an unknown diagnostic.",
                "Refresh the diagnostics and compute Focus Mode again.",
            )

    @property
    def suppressed_count(self) -> int:
        return len(self.complete_diagnostics) - len(self.visible_indices)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "status": "focused",
            "density": self.density,
            "quiet": self.quiet,
            "diagnostics": [item.to_dict() for item in self.complete_diagnostics],
            "visible_indices": list(self.visible_indices),
            "visible_diagnostics": [
                self.complete_diagnostics[index].to_dict()
                for index in self.visible_indices
            ],
            "root_indices": list(self.root_indices),
            "relations": [relation.to_dict() for relation in self.relations],
            "suppressed_count": self.suppressed_count,
            "provenance": {
                "source": "sona-guide-focus",
                "catalog_version": self.catalog_version,
                "rules": sorted({relation.rule_id for relation in self.relations}),
            },
        }


@dataclass(frozen=True, slots=True)
class GuideResponse:
    request: GuideRequest
    summary: str
    topic: str
    catalog_version: int
    sections: tuple[GuideSection, ...]
    concept_ids: tuple[str, ...]
    fixes: tuple[GuideFix, ...] = ()

    @property
    def basis(self) -> str:
        return "reported-diagnostic" if self.request.diagnostic is not None else "catalog-reference"

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.request.to_dict(),
            "status": "explained",
            "basis": self.basis,
            "summary": self.summary,
            "sections": [section.to_dict() for section in self.sections],
            "concept_ids": list(self.concept_ids),
            "fixes": [fix.to_dict() for fix in self.fixes],
            "provenance": {
                "source": "sona-guide-catalog",
                "catalog_version": self.catalog_version,
                "topic": self.topic,
            },
        }
