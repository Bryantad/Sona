"""Sona Language Server Protocol support.

The server intentionally exposes a narrow, conservative feature set. Canonical
frontend diagnostics remain the authority for language validity, while editor
navigation uses a non-executing local declaration index that also works for an
incomplete document.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

try:
    from lsprotocol.types import (  # type: ignore[import-not-found]
        TEXT_DOCUMENT_CODE_ACTION,
        TEXT_DOCUMENT_COMPLETION,
        TEXT_DOCUMENT_DEFINITION,
        TEXT_DOCUMENT_DID_CHANGE,
        TEXT_DOCUMENT_DID_CLOSE,
        TEXT_DOCUMENT_DID_OPEN,
        TEXT_DOCUMENT_DOCUMENT_SYMBOL,
        TEXT_DOCUMENT_HOVER,
        WORKSPACE_DID_CHANGE_CONFIGURATION,
        CodeAction,
        CodeActionDisabledType,
        CodeActionKind,
        CodeActionOptions,
        CodeActionParams,
        CompletionItem,
        CompletionItemKind,
        CompletionList,
        CompletionParams,
        DefinitionParams,
        Diagnostic,
        DiagnosticSeverity,
        DocumentSymbol,
        DocumentSymbolParams,
        Hover,
        HoverParams,
        Location,
        MarkupContent,
        MarkupKind,
        OptionalVersionedTextDocumentIdentifier,
        Position,
        Range,
        SymbolKind,
        TextEdit,
        TextDocumentEdit,
        WorkspaceEdit,
    )
    from pygls.server import LanguageServer  # type: ignore[import-not-found]

    _PYGLS_AVAILABLE = True
except ImportError:  # pragma: no cover - dependency isolation covers this path
    _PYGLS_AVAILABLE = False


SONA_ROOT = Path(__file__).resolve().parent.parent
STDLIB_ROOT = SONA_ROOT / "sona" / "stdlib"

_IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"
_IMPORT_RE = re.compile(
    rf"^[ \t]*import[ \t]+(?P<module>{_IDENTIFIER}(?:\.{_IDENTIFIER})*)"
    rf"(?:[ \t]+as[ \t]+(?P<alias>{_IDENTIFIER}))?"
)
_FUNCTION_RE = re.compile(
    rf"^[ \t]*(?:export[ \t]+)?(?:func|def)[ \t]+(?P<name>{_IDENTIFIER})[ \t]*\("
)
_CLASS_RE = re.compile(
    rf"^[ \t]*(?:export[ \t]+)?class[ \t]+(?P<name>{_IDENTIFIER})"
)
_BINDING_RE = re.compile(
    rf"^[ \t]*(?:export[ \t]+)?(?P<binding>let|const)[ \t]+"
    rf"(?P<name>{_IDENTIFIER})[ \t]*="
)
_BARE_ASSIGNMENT_RE = re.compile(
    rf"^[ \t]*(?P<name>{_IDENTIFIER})[ \t]*=(?!=)"
)
_MEMBER_PREFIX_RE = re.compile(
    rf"(?P<module>{_IDENTIFIER}(?:\.{_IDENTIFIER})*)\."
    rf"(?P<prefix>{_IDENTIFIER})?$"
)
_QUALIFIER_RE = re.compile(
    rf"(?P<module>{_IDENTIFIER}(?:\.{_IDENTIFIER})*)\.$"
)

_BARE_ASSIGNMENT_KEYWORDS = frozenset(
    {
        "break",
        "catch",
        "class",
        "const",
        "continue",
        "def",
        "else",
        "export",
        "finally",
        "for",
        "func",
        "if",
        "import",
        "let",
        "match",
        "repeat",
        "return",
        "try",
        "when",
        "while",
    }
)

# Only executable 0.15.x forms are suggested. Recognized-but-uncertified forms
# such as class, export, match, repeat, and statement-form when are omitted.
_KEYWORDS = (
    "break",
    "catch",
    "const",
    "continue",
    "else",
    "false",
    "finally",
    "for",
    "func",
    "if",
    "import",
    "in",
    "let",
    "null",
    "print",
    "return",
    "show",
    "true",
    "try",
    "while",
)


def _eprint(message: str) -> None:
    print(message, file=sys.stderr)


def canonical_diagnostics(uri: str, text: str):
    """Return the same canonical schema-1 diagnostics used by CLI tooling."""
    from .developer_intelligence.frontend import analyze_frontend

    return analyze_frontend(text, file=uri)


def _stdlib_modules() -> list[str]:
    from .stdlib_manifest import user_module_names

    return user_module_names()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _line_at(text: str, line: int) -> str:
    lines = text.splitlines()
    if 0 <= line < len(lines):
        return lines[line]
    return ""


def _utf16_length(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def _codepoint_index(line: str, utf16_character: int) -> int:
    """Convert an LSP UTF-16 character offset to a Python string index."""
    target = max(utf16_character, 0)
    consumed = 0
    for index, character in enumerate(line):
        width = _utf16_length(character)
        if consumed + width > target:
            return index
        consumed += width
        if consumed == target:
            return index + 1
    return len(line)


def _lsp_character(line: str, codepoint_index: int) -> int:
    return _utf16_length(line[: max(codepoint_index, 0)])


def _position_from_one_based(
    text: str,
    line_1: int,
    column_1: int,
) -> Position:
    line_index = max(line_1 - 1, 0)
    line = _line_at(text, line_index)
    character = _lsp_character(line, max(column_1 - 1, 0))
    return Position(line=line_index, character=character)


def _diagnostic_range(
    text: str,
    start_line_1: int,
    start_column_1: int,
    end_line_1: int | None,
    end_column_1: int | None,
) -> Range:
    start = _position_from_one_based(text, start_line_1, start_column_1)
    if end_column_1 is None:
        end_line_1 = start_line_1
        end_column_1 = start_column_1 + 1
    end = _position_from_one_based(
        text,
        end_line_1 or start_line_1,
        end_column_1,
    )
    if end.line == start.line and end.character <= start.character:
        end = Position(line=start.line, character=start.character + 1)
    return Range(start=start, end=end)


def _word_span_at(
    text: str,
    line_number: int,
    utf16_character: int,
) -> tuple[str, int, int]:
    line = _line_at(text, line_number)
    if not line:
        return "", 0, 0

    index = _codepoint_index(line, utf16_character)
    left = index
    while left > 0 and (line[left - 1].isalnum() or line[left - 1] == "_"):
        left -= 1
    right = index
    while right < len(line) and (line[right].isalnum() or line[right] == "_"):
        right += 1
    return line[left:right], left, right


def _mask_non_code(text: str) -> str:
    """Replace comments and quoted text with spaces while preserving offsets."""
    masked: list[str] = []
    index = 0
    quote: str | None = None
    escaped = False
    line_comment = False

    while index < len(text):
        character = text[index]

        if character in "\r\n":
            masked.append(character)
            line_comment = False
            if quote is not None:
                escaped = False
            index += 1
            continue

        if line_comment:
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

        if character == "#" or text.startswith("//", index):
            line_comment = True
            masked.append(" ")
            if character == "/":
                masked.append(" ")
                index += 2
            else:
                index += 1
            continue

        if character in {'"', "'", "`"}:
            quote = character
            masked.append(" ")
            index += 1
            continue

        masked.append(character)
        index += 1

    return "".join(masked)


@dataclass(frozen=True)
class SonaDeclaration:
    """A conservative declaration discovered in the current document."""

    name: str
    display_name: str
    kind: str
    detail: str
    line: int
    start: int
    end: int


def _declaration(
    match: re.Match[str],
    *,
    line: int,
    name_group: str,
    display_name: str,
    kind: str,
    detail: str,
) -> SonaDeclaration:
    name = match.group(name_group)
    return SonaDeclaration(
        name=name,
        display_name=display_name,
        kind=kind,
        detail=detail,
        line=line,
        start=match.start(name_group),
        end=match.end(name_group),
    )


def scan_document_declarations(text: str) -> list[SonaDeclaration]:
    """Index unambiguous top-level declarations without executing the parser."""
    masked_lines = _mask_non_code(text).splitlines()
    original_lines = text.splitlines()
    declarations: list[SonaDeclaration] = []
    brace_depth = 0

    for line_number, masked_line in enumerate(masked_lines):
        original_line = (
            original_lines[line_number]
            if line_number < len(original_lines)
            else masked_line
        )
        if brace_depth == 0:
            import_match = _IMPORT_RE.match(masked_line)
            if import_match:
                module = original_line[
                    import_match.start("module") : import_match.end("module")
                ]
                name_group = "alias" if import_match.group("alias") else "module"
                binding = import_match.group(name_group)
                if name_group == "module" and "." in binding:
                    binding = binding.split(".", 1)[0]
                    declarations.append(
                        SonaDeclaration(
                            name=binding,
                            display_name=module,
                            kind="module",
                            detail=f"import {module}",
                            line=line_number,
                            start=import_match.start("module"),
                            end=import_match.start("module") + len(binding),
                        )
                    )
                else:
                    display = (
                        f"{module} as {binding}"
                        if name_group == "alias"
                        else module
                    )
                    declarations.append(
                        _declaration(
                            import_match,
                            line=line_number,
                            name_group=name_group,
                            display_name=display,
                            kind="module",
                            detail=f"import {module}",
                        )
                    )
            else:
                function_match = _FUNCTION_RE.match(masked_line)
                class_match = _CLASS_RE.match(masked_line)
                binding_match = _BINDING_RE.match(masked_line)
                assignment_match = _BARE_ASSIGNMENT_RE.match(masked_line)

                if function_match:
                    name = function_match.group("name")
                    declarations.append(
                        _declaration(
                            function_match,
                            line=line_number,
                            name_group="name",
                            display_name=name,
                            kind="function",
                            detail="Sona function declaration",
                        )
                    )
                elif class_match:
                    name = class_match.group("name")
                    declarations.append(
                        _declaration(
                            class_match,
                            line=line_number,
                            name_group="name",
                            display_name=name,
                            kind="class",
                            detail="Recognized Sona class declaration",
                        )
                    )
                elif binding_match:
                    name = binding_match.group("name")
                    binding = binding_match.group("binding")
                    declarations.append(
                        _declaration(
                            binding_match,
                            line=line_number,
                            name_group="name",
                            display_name=name,
                            kind="constant" if binding == "const" else "variable",
                            detail=f"Sona {binding} binding",
                        )
                    )
                elif assignment_match:
                    name = assignment_match.group("name")
                    if name not in _BARE_ASSIGNMENT_KEYWORDS:
                        declarations.append(
                            _declaration(
                                assignment_match,
                                line=line_number,
                                name_group="name",
                                display_name=name,
                                kind="variable",
                                detail="Sona assignment",
                            )
                        )

        brace_depth += masked_line.count("{") - masked_line.count("}")
        brace_depth = max(brace_depth, 0)

    return declarations


def _import_bindings(text: str) -> dict[str, str]:
    bindings: dict[str, str] = {}
    for declaration in scan_document_declarations(text):
        if declaration.kind == "module" and declaration.detail.startswith("import "):
            bindings[declaration.name] = declaration.detail.removeprefix("import ")
    return bindings


def _resolve_module_name(text: str, candidate: str) -> str:
    head, separator, tail = candidate.partition(".")
    imported = _import_bindings(text).get(head)
    if imported is None:
        return candidate
    return f"{imported}.{tail}" if separator else imported


def _completion_context(
    line_text: str,
    codepoint_character: int,
) -> tuple[str | None, str | None, str]:
    before = line_text[: max(codepoint_character, 0)]
    stripped = before.lstrip()
    if stripped.startswith("import "):
        return stripped.removeprefix("import ").strip(), None, ""

    member_match = _MEMBER_PREFIX_RE.search(before)
    if member_match:
        return None, member_match.group("module"), member_match.group("prefix") or ""

    prefix_match = re.search(rf"({_IDENTIFIER})$", before)
    return None, None, prefix_match.group(1) if prefix_match else ""


@dataclass(frozen=True)
class StdlibDoc:
    module_doc: str
    symbols: dict[str, str]


def _resolve_stdlib_module_path(module_name: str) -> Path | None:
    candidates = [
        SONA_ROOT / "stdlib" / f"{module_name}.smod",
        STDLIB_ROOT / f"{module_name}.py",
    ]
    if not module_name.startswith("native_"):
        candidates.append(STDLIB_ROOT / f"native_{module_name}.py")
    return next((path for path in candidates if path.exists()), None)


@lru_cache(maxsize=256)
def _stdlib_docs(module_name: str) -> StdlibDoc | None:
    module_path = _resolve_stdlib_module_path(module_name)
    if not module_path:
        return None

    try:
        text = _read_text(module_path)
        if module_path.suffix == ".smod":
            symbols = {
                match.group(1): ""
                for match in re.finditer(
                    rf"^\s*func\s+({_IDENTIFIER})\s*\(",
                    text,
                    re.MULTILINE,
                )
                if not match.group(1).startswith("_")
            }
            first_comment = ""
            for line in text.splitlines():
                stripped = line.strip()
                if not stripped.startswith("#"):
                    continue
                comment = stripped.lstrip("#").strip()
                if not comment or comment.endswith(".smod"):
                    continue
                if comment.lower().startswith("purpose:"):
                    comment = comment.split(":", 1)[1].strip()
                first_comment = comment
                break
            return StdlibDoc(module_doc=first_comment, symbols=symbols)

        tree = ast.parse(text, filename=str(module_path))
    except (OSError, SyntaxError, UnicodeError):
        return None

    module_doc = ast.get_docstring(tree) or ""
    symbols: dict[str, str] = {}
    for node in tree.body:
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ) and not node.name.startswith("_"):
            symbols[node.name] = ast.get_docstring(node) or ""
    return StdlibDoc(module_doc=module_doc, symbols=symbols)


def _declaration_at(
    text: str,
    line: int,
    utf16_character: int,
) -> SonaDeclaration | None:
    word, _, _ = _word_span_at(text, line, utf16_character)
    if not word:
        return None
    matches = [item for item in scan_document_declarations(text) if item.name == word]
    return matches[0] if len(matches) == 1 else None


def _qualified_module_at(
    text: str,
    line_number: int,
    utf16_character: int,
) -> tuple[str | None, str]:
    line = _line_at(text, line_number)
    word, start, _ = _word_span_at(text, line_number, utf16_character)
    if not word:
        return None, ""
    qualifier = _QUALIFIER_RE.search(line[:start])
    module = qualifier.group("module") if qualifier else None
    return module, word


server = None

if _PYGLS_AVAILABLE:

    def _declaration_range(text: str, declaration: SonaDeclaration) -> Range:
        line = _line_at(text, declaration.line)
        return Range(
            start=Position(
                line=declaration.line,
                character=_lsp_character(line, declaration.start),
            ),
            end=Position(
                line=declaration.line,
                character=_lsp_character(line, declaration.end),
            ),
        )


    def _document_source(uri: str) -> str | None:
        try:
            return server.workspace.get_text_document(uri).source
        except Exception:
            return None


    def _field(value, name: str, default=None):
        if isinstance(value, dict):
            return value.get(name, default)
        return getattr(value, name, default)


    def _severity_name(value) -> str:
        if value in {DiagnosticSeverity.Error, 1}:
            return "error"
        if value in {DiagnosticSeverity.Warning, 2}:
            return "warning"
        return "info"


    def _source_position_from_lsp(
        text: str,
        position,
    ) -> tuple[int, int]:
        line_index = int(_field(position, "line", 0))
        utf16_character = int(_field(position, "character", 0))
        line_text = _line_at(text, line_index)
        return line_index + 1, _codepoint_index(line_text, utf16_character) + 1


    def _canonical_from_lsp_diagnostic(uri: str, text: str, lsp_diagnostic):
        from .developer_intelligence.diagnostics import SourceSpan, diagnostic
        from .guide.adapters import diagnostic_from_payload

        data = _field(lsp_diagnostic, "data")
        data = data if isinstance(data, dict) else {}
        if data.get("diagnostic_id"):
            return diagnostic_from_payload(data, uri)
        lsp_range = _field(lsp_diagnostic, "range")
        start = _field(lsp_range, "start", {})
        end = _field(lsp_range, "end", start)
        start_line, start_column = _source_position_from_lsp(text, start)
        end_line, end_column = _source_position_from_lsp(text, end)

        diagnostic_id = str(data.get("diagnostic_id") or _field(lsp_diagnostic, "code") or "")
        if not diagnostic_id:
            return None
        return diagnostic(
            diagnostic_id,
            str(data.get("category") or "lsp"),
            str(data.get("message") or _field(lsp_diagnostic, "message", "")),
            severity=str(data.get("severity") or _severity_name(_field(lsp_diagnostic, "severity"))),
            hint=str(data.get("hint") or ""),
            span=SourceSpan(
                file=str(data.get("file") or uri),
                start_line=int(data.get("start_line") or start_line),
                start_column=int(data.get("start_column") or start_column),
                end_line=int(data.get("end_line") or end_line),
                end_column=int(data.get("end_column") or end_column),
            ),
            source=str(data.get("source") or "sona-lsp"),
            metadata=data.get("metadata") if isinstance(data.get("metadata"), dict) else {},
            legacy_code=str(data["legacy_code"]) if data.get("legacy_code") else None,
        )


    def _code_action_kind_value(kind) -> str:
        return kind.value if hasattr(kind, "value") else str(kind)


    def _code_action_kind_allowed(context, kind) -> bool:
        requested = _field(context, "only") or []
        if not requested:
            return True
        action_kind = _code_action_kind_value(kind)
        for item in requested:
            prefix = _code_action_kind_value(item)
            if action_kind == prefix or action_kind.startswith(f"{prefix}."):
                return True
        return False


    def _guide_fix_to_lsp_action(
        uri: str,
        source: str,
        fix,
        *,
        kind,
        version: int,
        diagnostics: list[Diagnostic] | None = None,
    ) -> CodeAction:
        edits = [
            TextEdit(
                range=Range(
                    start=_position_from_one_based(source, edit.start_line, edit.start_column),
                    end=_position_from_one_based(source, edit.end_line, edit.end_column),
                ),
                new_text=edit.replacement,
            )
            for edit in fix.edits
        ]
        return CodeAction(
            title=f"Sona Guide: {fix.title}",
            kind=kind,
            diagnostics=diagnostics or None,
            is_preferred=fix.confidence in {"exact", "unique"},
            edit=WorkspaceEdit(document_changes=[TextDocumentEdit(
                text_document=OptionalVersionedTextDocumentIdentifier(uri=uri, version=version),
                edits=edits,
            )]),
            data={
                "schema_version": 1,
                "source": "sona-guide",
                "rule_id": fix.rule_id,
                "stale_protection": "document-version",
                "document_version": version,
                "fix": fix.to_dict(),
            },
        )


    def _lsp_code_actions(params: CodeActionParams, source: str, version: int) -> list[CodeAction]:
        from .guide import GuideRequest, preview_diagnostic_fixes, preview_stdlib_api_migration

        uri = params.text_document.uri
        context = _field(params, "context")
        actions: list[CodeAction] = []

        if _code_action_kind_allowed(context, CodeActionKind.QuickFix):
            for lsp_diagnostic in _field(context, "diagnostics") or []:
                if _field(lsp_diagnostic, "source") != "sona":
                    continue
                canonical = _canonical_from_lsp_diagnostic(uri, source, lsp_diagnostic)
                if canonical is None:
                    continue
                fixes = preview_diagnostic_fixes(
                    GuideRequest(canonical.diagnostic_id, canonical),
                    source,
                    document=uri,
                )
                actions.extend(
                    _guide_fix_to_lsp_action(
                        uri,
                        source,
                        fix,
                        kind=CodeActionKind.QuickFix,
                        version=version,
                        diagnostics=[lsp_diagnostic],
                    )
                    for fix in fixes
                )

        if _code_action_kind_allowed(context, CodeActionKind.SourceFixAll):
            actions.extend(
                _guide_fix_to_lsp_action(
                    uri,
                    source,
                    fix,
                    kind=CodeActionKind.SourceFixAll,
                    version=version,
                )
                for fix in preview_stdlib_api_migration(source, document=uri)
            )

        return actions


    def _lsp_diagnostics(uri: str, text: str) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        try:
            canonical = canonical_diagnostics(uri, text)
        except Exception:
            canonical = None

        if canonical is None:
            return [
                Diagnostic(
                    range=Range(
                        start=Position(line=0, character=0),
                        end=Position(line=0, character=1),
                    ),
                    message=(
                        "The canonical diagnostic pipeline encountered an "
                        "infrastructure failure."
                    ),
                    severity=DiagnosticSeverity.Error,
                    source="sona",
                    code="SONA-PARSE-099",
                )
            ]

        for item in canonical:
            severity = {
                "error": DiagnosticSeverity.Error,
                "warning": DiagnosticSeverity.Warning,
            }.get(item.severity, DiagnosticSeverity.Information)
            diagnostics.append(
                Diagnostic(
                    range=_diagnostic_range(
                        text,
                        item.span.start_line,
                        item.span.start_column,
                        item.span.end_line,
                        item.span.end_column,
                    ),
                    message=(
                        item.message + (f" Hint: {item.hint}" if item.hint else "")
                    ),
                    severity=severity,
                    source="sona",
                    code=item.diagnostic_id,
                    data=item.to_dict(),
                )
            )
        return diagnostics


    def _lsp_converter():
        from pygls.protocol import default_converter
        from pygls.protocol.json_rpc import JsonRPCRequestMessage

        converter = default_converter()
        # The generic pygls request adapter converts JSON keys to namedtuple
        # fields, renaming keys such as metadata's "rule-id". Keep Guide JSON
        # intact so transport cannot change canonical diagnostics.
        converter.register_structure_hook(JsonRPCRequestMessage, lambda obj, cls: cls(**obj))
        return converter


    class SonaLsp(LanguageServer):
        def __init__(self):
            super().__init__("sona-lsp", "0.15.6", converter_factory=_lsp_converter)
            self.guide_options = {}

        def validate(self, uri: str, text: str) -> None:
            self.publish_diagnostics(uri, _lsp_diagnostics(uri, text))


    server = SonaLsp()


    def _guide_profile(uri: str):
        from pygls.uris import to_fs_path
        from .guide.profile import default_profile, load_profile_state

        path = to_fs_path(uri)
        if not path:
            return default_profile()
        roots = list(server.workspace.folders)
        if server.workspace.root_uri:
            roots.append(server.workspace.root_uri)
        candidates = []
        for root_uri in roots:
            root_path = to_fs_path(root_uri)
            if root_path and Path(path).resolve().is_relative_to(Path(root_path).resolve()):
                candidates.append(Path(root_path))
        if not candidates:
            return default_profile()
        return load_profile_state(max(candidates, key=lambda root: len(root.parts))).profile


    def _guide_for_document(payload):
        from .guide.models import GuideError
        from .guide.service import guide_request, unavailable

        try:
            if not isinstance(payload, dict):
                return guide_request(payload)
            if not isinstance(payload.get("document", ""), str):
                return guide_request(payload)
            options = payload.get("options", {})
            if not isinstance(options, dict):
                return guide_request(payload)
            request = {**payload, "options": {**server.guide_options, **options}}
            return guide_request(request, profile=_guide_profile(payload.get("document", "")))
        except GuideError as exc:
            return unavailable(exc)
        except (OSError, ValueError, TypeError):
            return unavailable(GuideError(
                "SONA-GUIDE-005", "The project learning profile is unavailable.",
                "Review the selected project and its .sona/learning.json profile.",
            ))


    @server.feature("sona/guide")
    def guide_request(params):
        return _guide_for_document(params)


    @server.feature(WORKSPACE_DID_CHANGE_CONFIGURATION)
    def guide_configuration(params):
        from .guide.service import guide_request as validate_request

        settings = _field(params, "settings", {})
        options = _field(_field(settings, "sona", {}), "guide", {})
        result = validate_request({
            "schema_version": 1, "action": "concept", "concept_id": "variables", "options": options,
        })
        if result["status"] != "unavailable":
            server.guide_options = dict(options)


    def _concept_documentation(identifier: str | None, uri: str):
        if not identifier:
            return None
        result = _guide_for_document({
            "schema_version": 1, "action": "concept", "concept_id": identifier, "document": uri,
        })
        if result["status"] == "unavailable":
            return None
        return MarkupContent(kind=MarkupKind.PlainText, value=result["text"])

    @server.feature(TEXT_DOCUMENT_DID_OPEN)
    def did_open(params) -> None:
        server.validate(params.text_document.uri, params.text_document.text)


    @server.feature(TEXT_DOCUMENT_DID_CHANGE)
    def did_change(params) -> None:
        uri = params.text_document.uri
        source = _document_source(uri)
        if source is None:
            server.publish_diagnostics(uri, _lsp_diagnostics(uri, ""))
            return
        server.validate(uri, source)


    @server.feature(TEXT_DOCUMENT_DID_CLOSE)
    def did_close(params) -> None:
        server.publish_diagnostics(params.text_document.uri, [])


    @server.feature(
        TEXT_DOCUMENT_CODE_ACTION,
        CodeActionOptions(
            code_action_kinds=[
                CodeActionKind.QuickFix,
                CodeActionKind.SourceFixAll,
            ]
        ),
    )
    def code_action(params: CodeActionParams) -> list[CodeAction]:
        try:
            document = server.workspace.text_documents.get(params.text_document.uri)
            if document is None or type(document.version) is not int:
                return []
            actions = _lsp_code_actions(params, document.source, document.version)
            workspace = _field(server.client_capabilities, "workspace")
            supports_versions = _field(_field(workspace, "workspace_edit"), "document_changes")
            if not supports_versions:
                for action in actions:
                    action.edit = None
                    action.disabled = CodeActionDisabledType(
                        reason="Sona Guide fixes require a client supporting versioned document edits.",
                    )
            return actions
        except Exception:
            return []


    @server.feature(TEXT_DOCUMENT_COMPLETION)
    def completion(params: CompletionParams) -> CompletionList:
        from .guide.catalog import KEYWORD_CONCEPTS

        source = _document_source(params.text_document.uri)
        if source is None:
            return CompletionList(is_incomplete=False, items=[])

        try:
            line_text = _line_at(source, params.position.line)
            character = _codepoint_index(line_text, params.position.character)
            import_prefix, member_module, prefix = _completion_context(
                line_text,
                character,
            )
            items: list[CompletionItem] = []

            if import_prefix is not None:
                for module in _stdlib_modules():
                    if not import_prefix or module.startswith(import_prefix):
                        items.append(
                            CompletionItem(
                                label=module,
                                kind=CompletionItemKind.Module,
                                detail="Sona standard-library module",
                                documentation=_concept_documentation(
                                    {"fs": "files", "io": "files", "guardian": "guardian"}.get(module, "modules"),
                                    params.text_document.uri,
                                ),
                            )
                        )
                return CompletionList(is_incomplete=False, items=items)

            if member_module:
                resolved_module = _resolve_module_name(source, member_module)
                docs = _stdlib_docs(resolved_module)
                if docs:
                    for name in sorted(docs.symbols):
                        if not prefix or name.startswith(prefix):
                            items.append(
                                CompletionItem(
                                    label=name,
                                    kind=CompletionItemKind.Function,
                                    detail=f"{resolved_module}.{name}",
                                    documentation=_concept_documentation(
                                        {"fs": "files", "io": "files", "guardian": "guardian"}.get(resolved_module),
                                        params.text_document.uri,
                                    ),
                                )
                            )
                return CompletionList(is_incomplete=False, items=items)

            kind_map = {
                "class": CompletionItemKind.Class,
                "constant": CompletionItemKind.Constant,
                "function": CompletionItemKind.Function,
                "module": CompletionItemKind.Module,
                "variable": CompletionItemKind.Variable,
            }
            labels: set[str] = set()
            for declaration in scan_document_declarations(source):
                if declaration.name in labels or (
                    prefix and not declaration.name.startswith(prefix)
                ):
                    continue
                labels.add(declaration.name)
                items.append(
                    CompletionItem(
                        label=declaration.name,
                        kind=kind_map[declaration.kind],
                        detail=declaration.detail,
                        documentation=_concept_documentation({
                            "variable": "variables", "constant": "variables",
                            "function": "functions", "module": "modules",
                        }.get(declaration.kind), params.text_document.uri),
                    )
                )
            for keyword in _KEYWORDS:
                if keyword not in labels and (not prefix or keyword.startswith(prefix)):
                    items.append(
                        CompletionItem(
                            label=keyword,
                            kind=CompletionItemKind.Keyword,
                            detail="Sona keyword",
                            documentation=_concept_documentation(KEYWORD_CONCEPTS.get(keyword), params.text_document.uri),
                        )
                    )
            return CompletionList(is_incomplete=False, items=items)
        except Exception:
            return CompletionList(is_incomplete=False, items=[])


    @server.feature(TEXT_DOCUMENT_HOVER)
    def hover(params: HoverParams) -> Hover | None:
        from .guide.catalog import KEYWORD_CONCEPTS

        source = _document_source(params.text_document.uri)
        if source is None:
            return None

        try:
            qualifier, word = _qualified_module_at(
                source,
                params.position.line,
                params.position.character,
            )
            if not word:
                return None

            if qualifier:
                module = _resolve_module_name(source, qualifier)
                docs = _stdlib_docs(module)
                if docs and word in docs.symbols:
                    description = docs.symbols[word] or "Sona standard-library member."
                    guide = _concept_documentation(
                        {"fs": "files", "io": "files", "guardian": "guardian"}.get(module),
                        params.text_document.uri,
                    )
                    return Hover(
                        contents=MarkupContent(
                            kind=MarkupKind.PlainText,
                            value=f"{module}.{word}\n\n{description}" + (f"\n\n{guide.value}" if guide else ""),
                        )
                    )

            declaration = _declaration_at(
                source,
                params.position.line,
                params.position.character,
            )
            if declaration:
                if declaration.kind == "module":
                    module = declaration.detail.removeprefix("import ")
                    docs = _stdlib_docs(module)
                    description = (
                        docs.module_doc
                        if docs and docs.module_doc
                        else "Sona standard-library module."
                    )
                else:
                    description = declaration.detail + "."
                concept = {"variable": "variables", "constant": "variables", "function": "functions", "module": "modules"}.get(declaration.kind)
                if declaration.kind == "module":
                    concept = {"fs": "files", "io": "files", "guardian": "guardian"}.get(module, "modules")
                guide = _concept_documentation(concept, params.text_document.uri)
                return Hover(
                    contents=MarkupContent(
                        kind=MarkupKind.PlainText,
                        value=f"{declaration.name}\n\n{description}" + (f"\n\n{guide.value}" if guide else ""),
                    )
                )

            guide = _concept_documentation(KEYWORD_CONCEPTS.get(word), params.text_document.uri)
            if guide:
                return Hover(contents=guide)
            docs = _stdlib_docs(word)
            if docs and docs.module_doc:
                return Hover(
                    contents=MarkupContent(
                        kind=MarkupKind.Markdown,
                        value=f"**{word}**\n\n{docs.module_doc}",
                    )
                )
        except Exception:
            return None
        return None


    @server.feature(TEXT_DOCUMENT_DEFINITION)
    def goto_definition(params: DefinitionParams) -> list[Location]:
        source = _document_source(params.text_document.uri)
        if source is None:
            return []
        try:
            declaration = _declaration_at(
                source,
                params.position.line,
                params.position.character,
            )
            if declaration is None:
                return []
            return [
                Location(
                    uri=params.text_document.uri,
                    range=_declaration_range(source, declaration),
                )
            ]
        except Exception:
            return []


    @server.feature(TEXT_DOCUMENT_DOCUMENT_SYMBOL)
    def document_symbols(params: DocumentSymbolParams) -> list[DocumentSymbol]:
        source = _document_source(params.text_document.uri)
        if source is None:
            return []
        kind_map = {
            "class": SymbolKind.Class,
            "constant": SymbolKind.Constant,
            "function": SymbolKind.Function,
            "module": SymbolKind.Module,
            "variable": SymbolKind.Variable,
        }
        try:
            symbols: list[DocumentSymbol] = []
            for declaration in scan_document_declarations(source):
                selection = _declaration_range(source, declaration)
                line = _line_at(source, declaration.line)
                full_range = Range(
                    start=Position(line=declaration.line, character=0),
                    end=Position(
                        line=declaration.line,
                        character=_utf16_length(line),
                    ),
                )
                symbols.append(
                    DocumentSymbol(
                        name=declaration.display_name,
                        detail=declaration.detail,
                        kind=kind_map[declaration.kind],
                        range=full_range,
                        selection_range=selection,
                    )
                )
            return symbols
        except Exception:
            return []


def main(argv: Iterable[str] | None = None) -> int:
    if not _PYGLS_AVAILABLE:
        _eprint("ERROR: pygls is required to run the Sona LSP.")
        _eprint("Install it with: pip install pygls")
        return 1

    parser = argparse.ArgumentParser(prog="sona-lsp")
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Run over stdio (default)",
    )
    parser.add_argument("--tcp", action="store_true", help="Run over TCP")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2087)
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.tcp and not args.stdio:
        _eprint(f"Starting Sona LSP on tcp://{args.host}:{args.port}")
        server.start_tcp(args.host, args.port)
        return 0

    server.start_io()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
