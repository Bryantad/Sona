"""Read-only concept lookup and canonical-parser selection analysis."""

from __future__ import annotations

from .catalog import CATALOG_VERSION, CONCEPTS, SYNTAX_CONCEPTS
from .models import MODES, STYLES, GuideError
from .source import line_column_to_offset


def concept_payload(identifier: str, *, mode: str = "guided", style: str = "simple") -> dict:
    if identifier not in CONCEPTS or mode not in MODES or style not in STYLES:
        raise GuideError(
            "SONA-GUIDE-002", "The concept request is unsupported.",
            "Use a reviewed Sona Guide concept and documented presentation settings.",
        )
    concept = CONCEPTS[identifier]
    text = concept.summary
    if mode != "expert":
        text += "\n\n" + getattr(concept, style)
    if mode == "guided":
        text += "\n\nExample\n" + concept.example
    return {
        "id": identifier, "title": concept.title, "summary": concept.summary,
        "text": text, "provenance": {"source": "sona-guide-concepts", "catalog_version": CATALOG_VERSION},
    }


def selection_concepts(source: str, selection: dict | None = None) -> tuple[str, ...]:
    """Describe only reviewed grammar constructs overlapping the exact selection.

    The caller first runs the canonical frontend. The same parser's positioned
    syntax tree is used here because not every transformed AST value has a span.
    Neither path executes statements or imports a selected program's modules.
    """
    from sona.developer_intelligence.frontend import _parser

    start, end = 0, len(source)
    if selection is not None:
        start = line_column_to_offset(source, selection["start_line"], selection["start_column"])
        end = line_column_to_offset(source, selection["end_line"], selection["end_column"])
        if start >= end:
            raise GuideError("SONA-GUIDE-002", "The selection is empty or reversed.", "Select Sona source to explain.")
    tree = _parser().parser.parse(source)
    found: list[str] = []
    for node in tree.iter_subtrees_topdown():
        node_start = getattr(node.meta, "start_pos", None)
        node_end = getattr(node.meta, "end_pos", None)
        if node_start is None or node_end is None or node_start >= end or node_end <= start:
            continue
        identifier = SYNTAX_CONCEPTS.get(str(node.data))
        if identifier:
            found.append(identifier)
        if str(node.data) == "import_path":
            module = ".".join(str(child) for child in node.children)
            if module in {"fs", "io"}:
                found.append("files")
            elif module == "guardian":
                found.append("guardian")
    return tuple(dict.fromkeys(found))
