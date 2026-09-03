from __future__ import annotations

from sona.lsp_server import (
    _completion_context,
    _resolve_module_name,
    _utf16_length,
    _word_span_at,
    scan_document_declarations,
)


def test_declaration_index_is_top_level_conservative_and_offset_preserving():
    source = """import collection.list as lists;
let count = 1;
const limit = 4;
func double(value) {
    let nested = value;
}
class Preview {
    let field = 1;
}
bare = count;
# let commented = 2;
// func hidden() { }
print("class StringOnly { }");
let incomplete = (;
"""

    declarations = scan_document_declarations(source)

    assert [(item.name, item.kind, item.line) for item in declarations] == [
        ("lists", "module", 0),
        ("count", "variable", 1),
        ("limit", "constant", 2),
        ("double", "function", 3),
        ("Preview", "class", 6),
        ("bare", "variable", 9),
        ("incomplete", "variable", 13),
    ]
    for declaration in declarations:
        line = source.splitlines()[declaration.line]
        assert line[declaration.start : declaration.end] == declaration.name


def test_import_alias_and_completion_context_are_explicit():
    source = "import collection.list as lists;\nlists.ap"

    assert _resolve_module_name(source, "lists") == "collection.list"
    assert _completion_context("import colle", 12) == ("colle", None, "")
    assert _completion_context("lists.ap", 8) == (None, "lists", "ap")


def test_lsp_word_positions_use_utf16_offsets():
    source = 'print("😀"); double(value);'
    line = source.splitlines()[0]
    start = line.index("double")
    lsp_character = _utf16_length(line[: start + 2])

    word, word_start, word_end = _word_span_at(source, 0, lsp_character)

    assert word == "double"
    assert (word_start, word_end) == (start, start + len("double"))


def test_duplicate_declarations_remain_visible_to_callers():
    declarations = scan_document_declarations("let value = 1;\nlet value = 2;\n")

    assert [item.name for item in declarations] == ["value", "value"]

