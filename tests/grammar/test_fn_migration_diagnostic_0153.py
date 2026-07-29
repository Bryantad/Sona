from __future__ import annotations

import pytest

from sona.errors import SonaSyntaxError
from sona.parser_v090 import SonaParserv090


def test_fn_declaration_has_exact_migration_diagnostic():
    with pytest.raises(SonaSyntaxError) as caught:
        SonaParserv090().parse(
            "fn add(value) { return value; }",
            "legacy-fn.sona",
        )
    diagnostic = caught.value.diagnostic
    assert diagnostic.diagnostic_id == "SONA-PARSE-001"
    assert diagnostic.code.value == "E0001"
    assert diagnostic.message == "The 'fn' keyword is not supported in Sona."
    assert diagnostic.suggestion == "Use 'func' to declare a function."
    assert diagnostic.location.file == "legacy-fn.sona"
    assert diagnostic.location.line == 1
    assert diagnostic.location.column == 1


@pytest.mark.parametrize(
    "source",
    [
        'let fn = "value"; print(fn);',
        "let fn_name = 1; print(fn_name);",
        'print("fn example");',
        "// fn ignored(value) {}\nprint(1);",
        "# fn ignored(value) {}\nprint(1);",
        "let module = {fn: 1}; print(module.fn);",
        "func add(value) { return value; }; print(add(1));",
    ],
)
def test_fn_outside_declaration_keyword_position_is_not_migration_syntax(source):
    parser = SonaParserv090()
    try:
        parser.parse(source, "control.sona")
    except SonaSyntaxError as error:
        assert error.diagnostic.message != "The 'fn' keyword is not supported in Sona."


def test_earlier_unrelated_syntax_error_wins_over_later_fn_text():
    with pytest.raises(SonaSyntaxError) as caught:
        SonaParserv090().parse(
            "let value = ;\nfn add(value) { return value; }",
            "unrelated.sona",
        )
    assert caught.value.diagnostic.message != "The 'fn' keyword is not supported in Sona."
