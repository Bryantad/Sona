"""Canonical structured diagnostics for Sona developer intelligence."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


# Reserved schema-1 identifiers.  Keeping this table centralized prevents
# providers, the CLI, LSP, runtime, and Guardian from inventing overlapping IDs.
DIAGNOSTIC_IDS = {
    "parse_failure": "SONA-PARSE-001",
    "parse_infrastructure": "SONA-PARSE-099",
    "unsupported_feature": "SONA-SEM-099",
    "const_reassignment": "SONA-SEM-001",
    "invalid_control_flow": "SONA-SEM-002",
    "arity": "SONA-RUNTIME-001",
    "non_callable": "SONA-RUNTIME-002",
    "undefined_name": "SONA-RUNTIME-003",
    "division_by_zero": "SONA-RUNTIME-004",
    "invalid_operand": "SONA-RUNTIME-005",
    "invalid_index": "SONA-RUNTIME-006",
    "missing_property": "SONA-RUNTIME-007",
    "call_depth_limit": "SONA-RUNTIME-010",
    "loop_iteration_limit": "SONA-RUNTIME-011",
    "elapsed_time_limit": "SONA-RUNTIME-012",
    "output_size_limit": "SONA-RUNTIME-013",
    "module_missing": "SONA-MODULE-001",
    "module_circular": "SONA-MODULE-002",
    "module_invalid": "SONA-MODULE-003",
    "policy_denial": "SONA-GOV-001",
    "policy_approval": "SONA-GOV-003",
    "provider_unavailable": "SONA-AI-002",
    "cognitive_rule": "SONA-COG-001",
    "guardian_failure": "SONA-GUARD-001",
    "guardian_drift": "SONA-GUARD-002",
    "guardian_read_only": "SONA-GUARD-003",
}


@dataclass(frozen=True, slots=True)
class SourceSpan:
    file: str = "<unknown>"
    start_line: int = 1
    start_column: int = 1
    end_line: int | None = None
    end_column: int | None = None
    node_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Diagnostic:
    diagnostic_id: str
    category: str
    severity: str
    message: str
    hint: str = ""
    span: SourceSpan = field(default_factory=SourceSpan)
    source: str = "sona"
    related_locations: tuple[SourceSpan, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    legacy_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        from .redaction import redact
        return redact({
            "diagnostic_id": self.diagnostic_id,
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "hint": self.hint,
            "file": self.span.file,
            "start_line": self.span.start_line,
            "start_column": self.span.start_column,
            "end_line": self.span.end_line,
            "end_column": self.span.end_column,
            "node_type": self.span.node_type,
            "source": self.source,
            "related_locations": [item.to_dict() for item in self.related_locations],
            "metadata": dict(self.metadata),
            "legacy_code": self.legacy_code,
        })


def diagnostic(
    diagnostic_id: str,
    category: str,
    message: str,
    *,
    severity: str = "error",
    hint: str = "",
    span: SourceSpan | None = None,
    source: str = "sona",
    metadata: dict[str, Any] | None = None,
    legacy_code: str | None = None,
) -> Diagnostic:
    return Diagnostic(
        diagnostic_id=diagnostic_id,
        category=category,
        severity=severity,
        message=message,
        hint=hint,
        span=span or SourceSpan(),
        source=source,
        metadata=metadata or {},
        legacy_code=legacy_code,
    )
