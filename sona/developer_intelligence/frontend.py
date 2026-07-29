"""Canonical frontend diagnostic pipeline shared by CLI and LSP."""
from __future__ import annotations

from functools import lru_cache

from .cognitive import analyze_source
from .diagnostics import SourceSpan, diagnostic


@lru_cache(maxsize=1)
def _parser():
    from sona.parser_v090 import create_parser
    return create_parser()


def analyze_frontend(source: str, *, file: str = "<string>", profile: str = "standard"):
    result = _parser().validate_syntax(source, filename=file)
    findings = []
    for item in result.get("diagnostics", []):
        findings.append(diagnostic(
            str(item.get("diagnostic_id", "SONA-PARSE-001")),
            str(item.get("category", "syntax")), str(item.get("message", "Syntax error")),
            hint=str(item.get("hint", "")),
            span=SourceSpan(
                file=str(item.get("file", file)),
                start_line=int(item.get("line", 1)),
                start_column=int(item.get("column", 1)),
                end_line=int(item.get("end_line", item.get("line", 1))),
                end_column=int(item.get("end_column", int(item.get("column", 1)) + 1)),
                node_type="parser_failure",
            ),
            source="parser",
        ))
    for message in result.get("warnings", []):
        findings.append(diagnostic(
            "SONA-PARSE-090", "syntax", str(message), severity="warning",
            span=SourceSpan(file=file), source="parser",
        ))
    if result.get("valid"):
        findings.extend(analyze_source(source, file=file, profile=profile))
    return tuple(findings)
