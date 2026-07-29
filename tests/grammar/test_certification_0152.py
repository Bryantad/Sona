import json
from pathlib import Path

import pytest

from sona.interpreter import SonaUnifiedInterpreter
from sona.parser_v090 import create_parser


ROOT = Path(__file__).parent


@pytest.mark.parametrize("fixture", sorted((ROOT / "valid").glob("*.sona")))
def test_valid_fixtures_parse_and_execute(fixture):
    source = fixture.read_text(encoding="utf-8")
    parser = create_parser()
    assert parser.validate_syntax(source)["valid"] is True
    SonaUnifiedInterpreter().interpret(source, filename=str(fixture))


@pytest.mark.parametrize("fixture", sorted((ROOT / "invalid").glob("*.sona")))
def test_invalid_fixtures_have_expected_diagnostics(fixture):
    expected = json.loads(fixture.with_suffix(".json").read_text(encoding="utf-8"))
    result = create_parser().validate_syntax(
        fixture.read_text(encoding="utf-8"), filename=str(fixture)
    )
    assert result["valid"] is False
    assert result["errors"]
    assert expected["category"] == "syntax"
    diagnostic = result["diagnostics"][0]
    assert diagnostic["diagnostic_id"] == expected["diagnostic_id"]
    assert diagnostic["category"] == expected["category"]
    assert diagnostic["severity"] == "error"
    assert diagnostic["message"]
    assert diagnostic["hint"]
    assert diagnostic["file"] == str(fixture)
    assert diagnostic["line"] == expected["line"]
    assert diagnostic["column"] == expected["column"]
    assert diagnostic["end_line"] >= diagnostic["line"]
    assert diagnostic["end_column"] > 0


@pytest.mark.parametrize("folder", ["precedence", "strings", "comments", "control_flow", "functions", "imports"])
def test_certification_category(folder):
    fixtures = sorted((ROOT / folder).glob("*.sona"))
    assert fixtures, f"missing fixtures for {folder}"
    for fixture in fixtures:
        source = fixture.read_text(encoding="utf-8")
        assert create_parser().validate_syntax(source)["valid"] is True
        SonaUnifiedInterpreter().interpret(source, filename=str(fixture))


@pytest.mark.parametrize("source", [
    "class Example { };",
    "match value { 1 => print(1); };",
    "let [left, right] = [1, 2];",
    "repeat 2 { print(1); };",
    "export let value = 1;",
    "print(`template`);",
])
def test_uncertified_syntax_has_stable_compatibility_diagnostic(source):
    result = create_parser().validate_syntax(source)
    assert result["valid"] is False
    assert any("SONA-SEM-099" in message for message in result["errors"])


def test_precedence_parentheses_unary_escapes_short_circuit_and_chained_comparisons(capsys):
    source = r'print(2 + 3 * 4); print((2 + 3) * 4); print(2 ** 3 ** 2); print(-2 + 5); print("line\nnext"); print(false and missing); print(1 < 2 < 3);'
    assert create_parser().validate_syntax(source)["valid"] is True
    SonaUnifiedInterpreter().interpret(source)
    assert capsys.readouterr().out.splitlines() == ["14", "20", "512", "3", "line", "next", "False", "True"]
