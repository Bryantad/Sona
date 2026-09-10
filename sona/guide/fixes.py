"""Deterministic Sona Guide fix previews.

The rules in this module inspect source text and canonical diagnostics only.
They do not execute Sona programs and they do not call AI providers.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import fields, is_dataclass, replace
from pathlib import Path
from typing import Any

from sona.developer_intelligence.diagnostics import Diagnostic
from sona.errors import SonaError

from .explain import explain
from .models import GuideError, GuideFix, GuideRequest, GuideResponse, SourceEdit
from .source import (
    apply_source_edits,
    line_column_to_offset,
    offset_to_line_column,
    preferred_newline,
)

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_NAME_RE = re.compile(r"(?:Name|Function|Undefined name|Undefined function) '([^']+)'")
_API_RE = re.compile(r"\bio\.(read_file|write_file)\b")

_UNDEFINED_NAME_IDS = {"SONA-RUNTIME-003", "SONA-NATIVE-RUNTIME-003"}
_FIX_CONCEPTS = {
    "guide.undefined-name.closest-binding": ("variables", "scope"),
    "guide.stdlib-api-migration": ("files", "modules"),
}


def explain_with_fixes(
    request: GuideRequest,
    source: str,
    *,
    document: str,
) -> GuideResponse:
    response = explain(request)
    return replace(
        response,
        fixes=preview_diagnostic_fixes(request, source, document=document),
    )


def preview_diagnostic_fixes(
    request: GuideRequest,
    source: str,
    *,
    document: str,
) -> tuple[GuideFix, ...]:
    if request.diagnostic is None or request.diagnostic_id not in _UNDEFINED_NAME_IDS:
        return ()
    return _undefined_name_fix(request.diagnostic, source, document=document)


def preview_stdlib_api_migration(
    source: str,
    *,
    document: str,
) -> tuple[GuideFix, ...]:
    replacements = _manifest_move_replacements()
    if not {"io.read_file", "io.write_file"} & set(replacements):
        return ()
    if not _has_bare_import(source, "io"):
        return ()
    if not _migration_bindings_are_unambiguous(source):
        return ()

    masked = _mask_non_code(source)
    edits: list[SourceEdit] = []
    for match in _API_RE.finditer(masked):
        if masked[:match.start()].rstrip().endswith("."):
            continue
        legacy = f"io.{match.group(1)}"
        replacement = replacements.get(legacy)
        if replacement is None:
            continue
        start_line, start_column = offset_to_line_column(source, match.start())
        end_line, end_column = offset_to_line_column(source, match.end())
        expected = source[match.start():match.end()]
        edits.append(SourceEdit(
            document=document,
            start_line=start_line,
            start_column=start_column,
            end_line=end_line,
            end_column=end_column,
            expected=expected,
            replacement=replacement,
            rule_id="guide.stdlib-api-migration",
            title=f"Replace `{legacy}` with `{replacement}`",
            metadata={"legacy": legacy, "canonical": replacement},
        ))

    if not edits:
        return ()
    if not _has_bare_import(source, "fs"):
        line, column = _fs_import_insertion_position(source)
        edits.insert(0, SourceEdit(
            document=document,
            start_line=line,
            start_column=column,
            end_line=line,
            end_column=column,
            expected="",
            replacement=f"import fs;{preferred_newline(source)}",
            rule_id="guide.stdlib-api-migration",
            title="Import `fs` for canonical filesystem APIs",
            metadata={"module": "fs"},
        ))
    return (GuideFix(
        rule_id="guide.stdlib-api-migration",
        title="Migrate legacy `io` file APIs to `fs`",
        confidence="exact",
        edits=tuple(edits),
        rationale=(
            "The stdlib manifest marks io.read_file and io.write_file as moved "
            "to fs.read_text and fs.write_text."
        ),
    ),)


def apply_fixes(source: str, fixes: Iterable[GuideFix]) -> str:
    return apply_source_edits(
        source,
        [edit for fix in fixes for edit in fix.edits],
    )


def concepts_for_fixes(fixes: Iterable[GuideFix]) -> tuple[str, ...]:
    concepts: list[str] = []
    for fix in fixes:
        concepts.extend(_FIX_CONCEPTS.get(fix.rule_id, ()))
    return tuple(dict.fromkeys(concepts))


def _undefined_name_fix(
    diagnostic: Diagnostic,
    source: str,
    *,
    document: str,
) -> tuple[GuideFix, ...]:
    missing = _missing_name(diagnostic)
    if missing is None or not _IDENTIFIER.match(missing):
        return ()
    span = diagnostic.span
    try:
        start = line_column_to_offset(source, span.start_line, span.start_column)
    except GuideError:
        return ()
    end = start + len(missing)
    if source[start:end] != missing:
        return ()
    masked = _mask_non_code(source)
    if (
        masked[start:end] != missing
        or masked[:start].rstrip().endswith(".")
        or (start > 0 and (source[start - 1].isalnum() or source[start - 1] == "_"))
        or (end < len(source) and (source[end].isalnum() or source[end] == "_"))
    ):
        return ()

    candidates = _visible_bindings(source, diagnostic)
    if missing in candidates:
        return ()
    best = _unique_closest(missing, candidates)
    if best is None:
        return ()
    line, column = offset_to_line_column(source, start)
    end_line, end_column = offset_to_line_column(source, end)
    edit = SourceEdit(
        document=document,
        start_line=line,
        start_column=column,
        end_line=end_line,
        end_column=end_column,
        expected=missing,
        replacement=best,
        rule_id="guide.undefined-name.closest-binding",
        title=f"Rename `{missing}` to `{best}`",
        metadata={
            "missing": missing,
            "candidate": best,
            "distance": _levenshtein(missing.lower(), best.lower()),
        },
    )
    return (GuideFix(
        rule_id="guide.undefined-name.closest-binding",
        title=f"Rename `{missing}` to `{best}`",
        confidence="unique",
        edits=(edit,),
        rationale="Exactly one visible binding has the closest safe spelling match.",
    ),)


def _missing_name(diagnostic: Diagnostic) -> str | None:
    value = diagnostic.metadata.get("name")
    if isinstance(value, str):
        return value
    match = _NAME_RE.search(diagnostic.message)
    return match.group(1) if match else None


def _unique_closest(missing: str, candidates: Iterable[str]) -> str | None:
    names = sorted({name for name in candidates if name != missing and _IDENTIFIER.match(name)})
    if not names:
        return None
    scored = [(_levenshtein(missing.lower(), name.lower()), name) for name in names]
    scored.sort()
    threshold = max(2, min(4, (max(len(missing), len(scored[0][1])) + 1) // 2))
    if scored[0][0] > threshold:
        return None
    if len(scored) > 1 and scored[1][0] == scored[0][0]:
        return None
    return scored[0][1]


def _visible_bindings(source: str, diagnostic: Diagnostic) -> tuple[str, ...]:
    try:
        from sona.ast_nodes import (
            CatchClause,
            EnhancedForLoop,
            EnhancedIfStatement,
            EnhancedTryStatement,
            EnhancedWhileLoop,
            FunctionDefinition,
            ImportStatement,
            VariableAssignment,
        )
        from sona.parser_v090 import create_parser

        nodes = create_parser().parse(source, filename=diagnostic.span.file) or []
    except (AttributeError, ImportError, OSError, SonaError, TypeError, ValueError):
        return ()

    target = line_column_to_offset(source, diagnostic.span.start_line, diagnostic.span.start_column)

    def before(node: Any) -> bool:
        span = getattr(node, "span", None)
        if span is None:
            return False
        return line_column_to_offset(source, span.start_line, span.start_column) < target

    def contains(value: Any) -> bool:
        span = getattr(value, "span", None)
        if span is not None:
            start = line_column_to_offset(source, span.start_line, span.start_column)
            end = line_column_to_offset(
                source,
                span.end_line or span.start_line,
                span.end_column or span.start_column + 1,
            )
            if start <= target < end:
                return True
        if is_dataclass(value):
            return any(contains(getattr(value, item.name)) for item in fields(value))
        if isinstance(value, (list, tuple)):
            return any(contains(item) for item in value)
        if isinstance(value, dict):
            return any(contains(item) for item in value.values())
        return False

    def declaration(node: Any) -> str | None:
        if isinstance(node, VariableAssignment):
            return node.name
        if isinstance(node, FunctionDefinition):
            return node.name
        if isinstance(node, ImportStatement):
            return node.alias or node.module_path.split(".", 1)[0]
        return None

    def collect(statements: Iterable[Any], visible: tuple[str, ...]) -> tuple[str, ...]:
        names = list(visible)
        for statement in statements:
            if contains(statement):
                if isinstance(statement, FunctionDefinition):
                    return collect(statement.body, (*names, *statement.parameters))
                if isinstance(statement, EnhancedForLoop):
                    if contains(statement.iterable):
                        return tuple(names)
                    return collect(statement.body, (*names, statement.iterator_var))
                if isinstance(statement, EnhancedIfStatement):
                    if contains(statement.condition):
                        return tuple(names)
                    branches = (statement.if_body, *(item.body for item in statement.elif_clauses))
                    for branch in branches:
                        if contains(branch):
                            return collect(branch, tuple(names))
                    if statement.else_body and contains(statement.else_body):
                        return collect(statement.else_body, tuple(names))
                    return tuple(names)
                if isinstance(statement, EnhancedWhileLoop):
                    if contains(statement.condition):
                        return tuple(names)
                    return collect(statement.body, tuple(names))
                if isinstance(statement, EnhancedTryStatement):
                    for branch in (statement.try_body, statement.finally_body or []):
                        if contains(branch):
                            return collect(branch, tuple(names))
                    for clause in statement.catch_clauses:
                        if contains(clause.body):
                            clause_names = [*names]
                            if isinstance(clause, CatchClause) and clause.var_name:
                                clause_names.append(clause.var_name)
                            return collect(clause.body, tuple(clause_names))
                    return tuple(names)
                return tuple(names)
            name = declaration(statement)
            if name and before(statement):
                names.append(name)
        return tuple(names)

    return collect(nodes, ())


def _manifest_move_replacements() -> dict[str, str]:
    manifest = json.loads(
        (Path(__file__).resolve().parents[1] / "stdlib" / "MANIFEST.json").read_text(
            encoding="utf-8",
        )
    )
    replacements: dict[str, str] = {}
    for module in manifest.get("modules", []):
        module_name = str(module.get("name", ""))
        for export in module.get("exports", []):
            if export.get("disposition") != "MOVE":
                continue
            replacement = export.get("replacement")
            name = export.get("name")
            if isinstance(name, str) and isinstance(replacement, str):
                replacements[f"{module_name}.{name}"] = replacement
    return replacements


def _migration_bindings_are_unambiguous(source: str) -> bool:
    """Only migrate a top-level stdlib binding with no conflicting declarations.

    Ambiguous shadowing anywhere in the document suppresses this whole-file
    migration; no scope-sensitive or member-object rewrites are inferred.
    """
    from sona.ast_nodes import (
        CatchClause,
        EnhancedForLoop,
        FunctionDefinition,
        ImportFromStatement,
        ImportStatement,
        VariableAssignment,
    )
    from sona.developer_intelligence.frontend import _parser

    try:
        nodes = _parser().parse(source, filename="<guide-migration>") or []
    except (SonaError, AttributeError, TypeError, ValueError, RecursionError):
        return False
    top_imports = {id(node) for node in nodes if isinstance(node, ImportStatement)}
    if not any(isinstance(node, ImportStatement) and node.module_path == "io" and not node.alias for node in nodes):
        return False
    protected = {"io", "fs"}

    def unambiguous(value):
        if isinstance(value, ImportStatement):
            binding = value.alias or value.module_path.split(".", 1)[0]
            if binding in protected:
                return id(value) in top_imports and value.module_path == binding and not value.alias
        if isinstance(value, ImportFromStatement):
            return False
        if isinstance(value, (VariableAssignment, FunctionDefinition)) and value.name in protected:
            return False
        if isinstance(value, FunctionDefinition) and protected.intersection(value.parameters):
            return False
        if isinstance(value, EnhancedForLoop) and value.iterator_var in protected:
            return False
        if isinstance(value, CatchClause) and value.var_name in protected:
            return False
        if is_dataclass(value):
            return all(unambiguous(getattr(value, item.name)) for item in fields(value))
        if isinstance(value, (list, tuple)):
            return all(unambiguous(item) for item in value)
        if isinstance(value, dict):
            return all(unambiguous(item) for item in value.values())
        return True

    return unambiguous(nodes)


def _has_bare_import(source: str, module_name: str) -> bool:
    pattern = re.compile(
        rf"^[ \t]*import[ \t]+{re.escape(module_name)}[ \t]*;?[ \t]*$",
    )
    return any(pattern.match(line) for line in _mask_non_code(source).splitlines())


def _fs_import_insertion_position(source: str) -> tuple[int, int]:
    masked_lines = _mask_non_code(source).splitlines()
    last_import = 0
    for index, line in enumerate(masked_lines, start=1):
        if re.match(
            r"^[ \t]*import[ \t]+[A-Za-z_][A-Za-z0-9_.]*(?:[ \t]+as[ \t]+[A-Za-z_][A-Za-z0-9_]*)?[ \t]*;?[ \t]*$",
            line,
        ):
            last_import = index
            continue
        if line.strip():
            break
    return last_import + 1 if last_import else 1, 1


def _mask_non_code(source: str) -> str:
    masked: list[str] = []
    index = 0
    quote: str | None = None
    escaped = False
    comment = False
    while index < len(source):
        character = source[index]
        if character in "\r\n":
            masked.append(character)
            comment = False
            if quote is not None:
                escaped = False
            index += 1
            continue
        if comment:
            masked.append(" ")
            index += 1
            continue
        if quote is not None:
            masked.append(" ")
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            index += 1
            continue
        if character == "#" or source.startswith("//", index):
            comment = True
            masked.append(" ")
            if character == "/":
                masked.append(" ")
                index += 2
            else:
                index += 1
            continue
        if character in {'"', "'"}:
            quote = character
            masked.append(" ")
            index += 1
            continue
        masked.append(character)
        index += 1
    return "".join(masked)


def _levenshtein(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_char in enumerate(right, start=1):
            current.append(min(
                previous[right_index] + 1,
                current[right_index - 1] + 1,
                previous[right_index - 1] + (left_char != right_char),
            ))
        previous = current
    return previous[-1]
