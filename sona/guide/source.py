"""Source ranges and stale-text protected edits for Sona Guide."""

from __future__ import annotations

from collections.abc import Iterable

from .models import GuideError, SourceEdit


def line_column_to_offset(source: str, line: int, column: int) -> int:
    if line < 1 or column < 1:
        raise GuideError(
            "SONA-GUIDE-002",
            "The source range is invalid.",
            "Use one-based line and column numbers from a canonical diagnostic.",
        )
    lines = source.splitlines(keepends=True)
    if not lines:
        if line == 1 and column == 1:
            return 0
        raise GuideError(
            "SONA-GUIDE-002",
            "The source range is outside the document.",
            "Refresh the diagnostic against the current document.",
        )
    if line > len(lines):
        if line == len(lines) + 1 and column == 1:
            return len(source)
        raise GuideError(
            "SONA-GUIDE-002",
            "The source range is outside the document.",
            "Refresh the diagnostic against the current document.",
        )
    base = sum(len(item) for item in lines[: line - 1])
    text = lines[line - 1]
    content_length = len(text.rstrip("\r\n"))
    if column > content_length + 1:
        raise GuideError(
            "SONA-GUIDE-002",
            "The source range is outside the line.",
            "Refresh the diagnostic against the current document.",
        )
    return base + column - 1


def offset_to_line_column(source: str, offset: int) -> tuple[int, int]:
    if offset < 0 or offset > len(source):
        raise GuideError(
            "SONA-GUIDE-002",
            "The source offset is outside the document.",
            "Refresh the diagnostic against the current document.",
        )
    line = 1
    column = 1
    for index, character in enumerate(source):
        if index == offset:
            return line, column
        if character == "\n":
            line += 1
            column = 1
        else:
            column += 1
    return line, column


def text_at_range(source: str, edit: SourceEdit) -> str:
    start = line_column_to_offset(source, edit.start_line, edit.start_column)
    end = line_column_to_offset(source, edit.end_line, edit.end_column)
    return source[start:end]


def apply_source_edits(source: str, edits: Iterable[SourceEdit]) -> str:
    indexed = [
        (
            line_column_to_offset(source, edit.start_line, edit.start_column),
            line_column_to_offset(source, edit.end_line, edit.end_column),
            edit,
        )
        for edit in edits
    ]
    indexed.sort(key=lambda item: item[0])

    previous_end = -1
    for start, end, edit in indexed:
        if start < previous_end:
            raise GuideError(
                "SONA-GUIDE-004",
                "The proposed fixes overlap.",
                "Apply one fix at a time or refresh the preview.",
            )
        if source[start:end] != edit.expected:
            raise GuideError(
                "SONA-GUIDE-003",
                "The source changed after this fix was previewed.",
                "Refresh the diagnostic and preview the edit again.",
            )
        previous_end = end

    updated = source
    for start, end, edit in reversed(indexed):
        updated = updated[:start] + edit.replacement + updated[end:]
    return updated


def preferred_newline(source: str) -> str:
    return "\r\n" if "\r\n" in source else "\n"
