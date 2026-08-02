"""Sona Language Server (LSP).

This module provides an stdio-based LSP server for `.sona` files.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional

try:
    from pygls.server import LanguageServer  # type: ignore[import-not-found]
    from lsprotocol.types import (  # type: ignore[import-not-found]
        TEXT_DOCUMENT_COMPLETION,
        TEXT_DOCUMENT_DID_CHANGE,
        TEXT_DOCUMENT_DID_OPEN,
        TEXT_DOCUMENT_HOVER,
        TEXT_DOCUMENT_DEFINITION,
        TEXT_DOCUMENT_REFERENCES,
        TEXT_DOCUMENT_DOCUMENT_SYMBOL,
        TEXT_DOCUMENT_FORMATTING,
        CompletionItem,
        CompletionItemKind,
        CompletionList,
        CompletionParams,
        DefinitionParams,
        ReferenceParams,
        DocumentSymbolParams,
        DocumentFormattingParams,
        Diagnostic,
        DiagnosticSeverity,
        Hover,
        HoverParams,
        Location,
        MarkupContent,
        MarkupKind,
        Position,
        Range,
        SymbolInformation,
        SymbolKind,
        TextEdit,
    )

    _PYGLS_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYGLS_AVAILABLE = False


SONA_ROOT = Path(__file__).resolve().parent.parent
STDLIB_ROOT = SONA_ROOT / "sona" / "stdlib"


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def canonical_diagnostics(uri: str, text: str):
    """Return the same canonical schema-1 diagnostics used by CLI tooling."""
    from .developer_intelligence.frontend import analyze_frontend
    return analyze_frontend(text, file=uri)


def _stdlib_modules() -> list[str]:
    from .stdlib_manifest import user_module_names
    return user_module_names()


def _pos(line_1: int, col_1: int) -> Position:
    return Position(line=max(line_1 - 1, 0), character=max(col_1 - 1, 0))


def _range_from_point(line_1: int, col_1: int) -> Range:
    start = _pos(line_1, col_1)
    end = Position(line=start.line, character=start.character + 1)
    return Range(start=start, end=end)


def _word_at(text: str, line: int, character: int) -> str:
    lines = text.splitlines()
    if line < 0 or line >= len(lines):
        return ""
    s = lines[line]
    if not s:
        return ""

    i = min(max(character, 0), len(s))
    left = i
    while left > 0 and (s[left - 1].isalnum() or s[left - 1] == "_"):
        left -= 1
    right = i
    while right < len(s) and (s[right].isalnum() or s[right] == "_"):
        right += 1
    return s[left:right]


def _completion_context(
    line_text: str, character: int
) -> tuple[Optional[str], Optional[str]]:
    """Returns (import_prefix, member_context_module).

    - If cursor is in an `import <prefix>` statement, returns import_prefix.
    - If cursor is after `<module>.`, returns member_context_module.
    """
    before = line_text[: max(character, 0)]

    # Member access: foo.<cursor>
    dot = before.rfind(".")
    if dot != -1 and dot > 0:
        mod = before[:dot].strip().split()[-1]
        if mod.isidentifier():
            return None, mod

    # Import statement: import <prefix>
    stripped = before.lstrip()
    if stripped.startswith("import "):
        prefix = stripped[len("import "):].strip()
        return prefix, None

    return None, None


@dataclass(frozen=True)
class StdlibDoc:
    module_doc: str
    symbols: dict[str, str]


def _resolve_stdlib_module_path(module_name: str) -> Optional[Path]:
    candidates = [
        SONA_ROOT / "stdlib" / f"{module_name}.smod",
        STDLIB_ROOT / f"{module_name}.py",
    ]
    if not module_name.startswith("native_"):
        candidates.append(STDLIB_ROOT / f"native_{module_name}.py")
    for p in candidates:
        if p.exists():
            return p
    return None


@lru_cache(maxsize=256)
def _stdlib_docs(module_name: str) -> Optional[StdlibDoc]:
    module_path = _resolve_stdlib_module_path(module_name)
    if not module_path:
        return None

    if module_path.suffix == ".smod":
        text = _read_text(module_path)
        symbols = {
            match.group(1): ""
            for match in re.finditer(r"^\s*func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", text, re.MULTILINE)
            if not match.group(1).startswith("_")
        }
        first_comment = ""
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                comment = stripped.lstrip("#").strip()
                if not comment or comment.endswith(".smod"):
                    continue
                if comment.lower().startswith("purpose:"):
                    comment = comment.split(":", 1)[1].strip()
                first_comment = comment
                break
        return StdlibDoc(module_doc=first_comment, symbols=symbols)

    try:
        tree = ast.parse(_read_text(module_path), filename=str(module_path))
    except Exception:
        return None

    module_doc = ast.get_docstring(tree) or ""
    symbols: dict[str, str] = {}

    for node in tree.body:
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            name = node.name
            if name.startswith("_"):
                continue
            symbols[name] = ast.get_docstring(node) or ""

    return StdlibDoc(module_doc=module_doc, symbols=symbols)


server = None

if _PYGLS_AVAILABLE:

    class SonaLsp(LanguageServer):
        def __init__(self):
            super().__init__("sona-lsp", "0.15.4")

        def validate(self, uri: str, text: str) -> None:
            diags: list[Diagnostic] = []
            try:
                for item in canonical_diagnostics(uri, text):
                    severity = (
                        DiagnosticSeverity.Error if item.severity == "error" else
                        DiagnosticSeverity.Warning if item.severity == "warning" else
                        DiagnosticSeverity.Information
                    )
                    diags.append(Diagnostic(
                        range=Range(
                            start=_pos(item.span.start_line, item.span.start_column),
                            end=_pos(item.span.end_line or item.span.start_line, item.span.end_column or item.span.start_column + 1),
                        ),
                        message=item.message + (f" Hint: {item.hint}" if item.hint else ""),
                        severity=severity, source="sona", code=item.diagnostic_id,
                    ))
            except Exception:
                diags.append(
                    Diagnostic(
                        range=_range_from_point(1, 1),
                        message="The canonical diagnostic pipeline encountered an infrastructure failure.",
                        severity=DiagnosticSeverity.Error,
                        source="sona",
                        code="SONA-PARSE-099",
                    )
                )

            self.publish_diagnostics(uri, diags)

    server = SonaLsp()
    _eprint("[sona-lsp] Server instance created")

    @server.feature(TEXT_DOCUMENT_DID_OPEN)
    def did_open(params):
        _eprint(f"[sona-lsp] did_open: {params.text_document.uri}")
        doc = server.workspace.get_text_document(params.text_document.uri)
        _eprint(f"[sona-lsp] doc source length: {len(doc.source)}")
        server.validate(doc.uri, doc.source)

    @server.feature(TEXT_DOCUMENT_DID_CHANGE)
    def did_change(params):
        _eprint(f"[sona-lsp] did_change: {params.text_document.uri}")
        doc = server.workspace.get_text_document(params.text_document.uri)
        server.validate(doc.uri, doc.source)

    @server.feature(TEXT_DOCUMENT_COMPLETION)
    def completion(params: CompletionParams) -> CompletionList:
        doc = server.workspace.get_text_document(params.text_document.uri)
        line = params.position.line
        character = params.position.character
        lines = doc.source.splitlines()
        line_text = lines[line] if 0 <= line < len(lines) else ""

        import_prefix, member_module = _completion_context(
            line_text, character
        )

        items: list[CompletionItem] = []

        if member_module:
            docs = _stdlib_docs(member_module)
            if docs:
                for name in sorted(docs.symbols.keys()):
                    items.append(
                        CompletionItem(
                            label=name,
                            kind=CompletionItemKind.Function,
                            detail=f"{member_module}.{name}",
                        )
                    )
            return CompletionList(is_incomplete=False, items=items)

        modules = _stdlib_modules()
        if import_prefix is not None:
            for module in modules:
                if not import_prefix or module.startswith(import_prefix):
                    items.append(
                        CompletionItem(
                            label=module,
                            kind=CompletionItemKind.Module,
                            detail="Sona stdlib module",
                        )
                    )
            return CompletionList(is_incomplete=False, items=items)

        for module in modules[:200]:
            items.append(
                CompletionItem(
                    label=module,
                    kind=CompletionItemKind.Module,
                    detail="Sona stdlib module",
                )
            )

        return CompletionList(is_incomplete=True, items=items)

    @server.feature(TEXT_DOCUMENT_HOVER)
    def hover(params: HoverParams) -> Hover:
        doc = server.workspace.get_text_document(params.text_document.uri)
        word = _word_at(
            doc.source, params.position.line, params.position.character
        )
        if not word:
            return Hover(
                contents=MarkupContent(kind=MarkupKind.Markdown, value="")
            )

        docs = _stdlib_docs(word)
        if docs and docs.module_doc:
            return Hover(
                contents=MarkupContent(
                    kind=MarkupKind.Markdown,
                    value=f"**{word}**\n\n{docs.module_doc}",
                )
            )

        lines = doc.source.splitlines()
        if 0 <= params.position.line < len(lines):
            line_text = lines[params.position.line]
        else:
            line_text = ""
        before = line_text[: params.position.character]
        dot = before.rfind(".")
        if dot != -1:
            left = before[:dot].strip().split()[-1]
            if left.isidentifier():
                md = _stdlib_docs(left)
                if md and word in md.symbols and md.symbols[word]:
                    return Hover(
                        contents=MarkupContent(
                            kind=MarkupKind.Markdown,
                            value=(
                                f"**{left}.{word}**\n\n{md.symbols[word]}"
                            ),
                        )
                    )

        return Hover(
            contents=MarkupContent(
                kind=MarkupKind.Markdown, value=f"**{word}**"
            )
        )

    # =========================================================================
    # Go to Definition
    # =========================================================================
    @server.feature(TEXT_DOCUMENT_DEFINITION)
    def goto_definition(params: DefinitionParams) -> list[Location]:
        """Find the definition of a symbol (function, class, variable)."""
        doc = server.workspace.get_text_document(params.text_document.uri)
        word = _word_at(doc.source, params.position.line, params.position.character)
        if not word:
            return []

        locations: list[Location] = []
        lines = doc.source.splitlines()

        # Search for function/class definitions
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Match the canonical function declaration spelling.
            if stripped.startswith(f"func {word}(") or stripped.startswith(f"func {word} ("):
                col = line.find(f"func {word}") + 5  # Position at name
                locations.append(Location(
                    uri=params.text_document.uri,
                    range=Range(
                        start=Position(line=i, character=col),
                        end=Position(line=i, character=col + len(word))
                    )
                ))
            # Match: variable assignment at start of line: name = 
            elif stripped.startswith(f"{word} =") or stripped.startswith(f"{word}="):
                col = line.find(word)
                locations.append(Location(
                    uri=params.text_document.uri,
                    range=Range(
                        start=Position(line=i, character=col),
                        end=Position(line=i, character=col + len(word))
                    )
                ))

        return locations

    # =========================================================================
    # Find References
    # =========================================================================
    @server.feature(TEXT_DOCUMENT_REFERENCES)
    def find_references(params: ReferenceParams) -> list[Location]:
        """Find all references to a symbol in the document."""
        doc = server.workspace.get_text_document(params.text_document.uri)
        word = _word_at(doc.source, params.position.line, params.position.character)
        if not word:
            return []

        locations: list[Location] = []
        lines = doc.source.splitlines()
        import re
        pattern = re.compile(r'\b' + re.escape(word) + r'\b')

        for i, line in enumerate(lines):
            for match in pattern.finditer(line):
                locations.append(Location(
                    uri=params.text_document.uri,
                    range=Range(
                        start=Position(line=i, character=match.start()),
                        end=Position(line=i, character=match.end())
                    )
                ))

        return locations

    # =========================================================================
    # Document Symbols (Outline)
    # =========================================================================
    @server.feature(TEXT_DOCUMENT_DOCUMENT_SYMBOL)
    def document_symbols(params: DocumentSymbolParams) -> list[SymbolInformation]:
        """Provide document symbols for the Outline view."""
        doc = server.workspace.get_text_document(params.text_document.uri)
        lines = doc.source.splitlines()
        symbols: list[SymbolInformation] = []
        import re

        fn_pattern = re.compile(r'^\s*func\s+(\w+)\s*\(')
        import_pattern = re.compile(r'^\s*import\s+(\w+)')
        var_pattern = re.compile(r'^(\w+)\s*=\s*')

        for i, line in enumerate(lines):
            # Functions
            fn_match = fn_pattern.match(line)
            if fn_match:
                name = fn_match.group(1)
                col = line.find(f"func {name}") + 5
                symbols.append(SymbolInformation(
                    name=name,
                    kind=SymbolKind.Function,
                    location=Location(
                        uri=params.text_document.uri,
                        range=Range(
                            start=Position(line=i, character=col),
                            end=Position(line=i, character=col + len(name))
                        )
                    )
                ))
                continue

            # Imports
            import_match = import_pattern.match(line)
            if import_match:
                name = import_match.group(1)
                col = line.find(f"import {name}") + 7
                symbols.append(SymbolInformation(
                    name=name,
                    kind=SymbolKind.Module,
                    location=Location(
                        uri=params.text_document.uri,
                        range=Range(
                            start=Position(line=i, character=col),
                            end=Position(line=i, character=col + len(name))
                        )
                    )
                ))
                continue

            # Top-level variables (only at column 0)
            if not line.startswith(' ') and not line.startswith('\t'):
                var_match = var_pattern.match(line)
                if var_match:
                    name = var_match.group(1)
                    if name not in ('if', 'for', 'while', 'match', 'when', 'try', 'class', 'func', 'def'):
                        symbols.append(SymbolInformation(
                            name=name,
                            kind=SymbolKind.Variable,
                            location=Location(
                                uri=params.text_document.uri,
                                range=Range(
                                    start=Position(line=i, character=0),
                                    end=Position(line=i, character=len(name))
                                )
                            )
                        ))

        return symbols

    # =========================================================================
    # Code Formatting
    # =========================================================================
    @server.feature(TEXT_DOCUMENT_FORMATTING)
    def formatting(params: DocumentFormattingParams) -> list[TextEdit]:
        """Format the document with consistent style."""
        doc = server.workspace.get_text_document(params.text_document.uri)
        lines = doc.source.splitlines()
        formatted_lines: list[str] = []
        
        # Access FormattingOptions attributes directly (not a dict)
        tab_size = params.options.tab_size if params.options.tab_size else 4
        use_spaces = params.options.insert_spaces if params.options.insert_spaces is not None else True
        indent_char = " " * tab_size if use_spaces else "\t"

        for line in lines:
            # Preserve empty lines
            if not line.strip():
                formatted_lines.append("")
                continue

            # Calculate current indentation level
            stripped = line.lstrip()
            current_indent = len(line) - len(stripped)
            
            # Normalize indentation (convert tabs to spaces or vice versa)
            if use_spaces:
                # Count logical indent level
                indent_level = 0
                i = 0
                while i < len(line) and line[i] in ' \t':
                    if line[i] == '\t':
                        indent_level += 1
                    elif i + tab_size <= current_indent:
                        # Check if we have tab_size spaces
                        if line[i:i+tab_size] == ' ' * tab_size:
                            indent_level += 1
                            i += tab_size - 1
                    i += 1
                # Approximate: use current spaces / tab_size
                indent_level = current_indent // tab_size
                new_indent = indent_char * indent_level
            else:
                indent_level = current_indent // tab_size
                new_indent = "\t" * indent_level

            # Apply formatting rules
            formatted = stripped
            
            # Ensure space after keywords
            for kw in ['if', 'elif', 'else', 'for', 'while', 'func', 'def', 'class', 'return', 'import', 'from', 'match', 'when', 'try', 'catch', 'finally']:
                if formatted.startswith(kw) and len(formatted) > len(kw):
                    next_char = formatted[len(kw)]
                    if next_char not in ' \t({':
                        formatted = kw + ' ' + formatted[len(kw):]

            # Ensure space around operators (basic)
            import re
            # Add space around = but not == or !=
            formatted = re.sub(r'(?<!=)=(?!=)', ' = ', formatted)
            # Clean up multiple spaces
            formatted = re.sub(r'  +', ' ', formatted)
            # Remove space before semicolon
            formatted = re.sub(r'\s+;', ';', formatted)
            # Ensure space after comma
            formatted = re.sub(r',(?!\s)', ', ', formatted)
            
            formatted_lines.append(new_indent + formatted)

        new_text = '\n'.join(formatted_lines)
        if doc.source.endswith('\n'):
            new_text += '\n'

        # Return single edit replacing entire document
        return [TextEdit(
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=len(lines), character=0)
            ),
            new_text=new_text
        )]


def main(argv: Optional[Iterable[str]] = None) -> int:
    if not _PYGLS_AVAILABLE:
        _eprint("ERROR: pygls is required to run the Sona LSP.")
        _eprint("Install it with: pip install pygls")
        return 1

    parser = argparse.ArgumentParser(prog="sona-lsp")
    parser.add_argument(
        "--stdio", action="store_true", help="Run over stdio (default)"
    )
    parser.add_argument("--tcp", action="store_true", help="Run over TCP")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2087)
    args = parser.parse_args(list(argv) if argv is not None else None)

    # Default to stdio unless explicitly using TCP.
    if args.tcp and not args.stdio:
        _eprint(f"Starting Sona LSP on tcp://{args.host}:{args.port}")
        server.start_tcp(args.host, args.port)
        return 0

    server.start_io()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
