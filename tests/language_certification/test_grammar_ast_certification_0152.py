from __future__ import annotations

from contextlib import redirect_stdout
from dataclasses import fields, is_dataclass
from io import StringIO

import pytest
from lark import Token, Tree

from sona.errors import SonaSyntaxError
from sona.interpreter import SonaUnifiedInterpreter
from sona.parser_v090 import SonaParserv090


def execute(source: str) -> list[str]:
    output = StringIO()
    with redirect_stdout(output):
        SonaUnifiedInterpreter(compatibility_mode="sona").interpret(
            source, filename="certification.sona"
        )
    return output.getvalue().splitlines()


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("", []),
        ("// comment without newline", []),
        ("# hash comment\r\nprint(1)", ["1"]),
        ("\t let value = 2;\r\n\tprint(value);", ["2"]),
        ('print("");', [""]),
        ('print("Unicode: λ雪");', ["Unicode: λ雪"]),
        ('print("// not a comment # either");', ["// not a comment # either"]),
        ('print("quote: \\\" slash: \\\\ newline:\\nend");', ['quote: " slash: \\ newline:', "end"]),
        ("print(0); print(-2); print(2.5)", ["0", "-2", "2.5"]),
        ("print(999999999999999999999999999999999999);", ["999999999999999999999999999999999999"]),
    ],
)
def test_lexical_contract(source, expected):
    assert execute(source) == expected


@pytest.mark.parametrize(
    "source",
    [
        "let café = 1;",
        "let if = 1;",
        "print(1e3);",
        "print(1.2.3);",
        'print("unterminated);',
        'print("bad \\q escape");',
        "let value = ;",
        "if true { print(1);",
        "func incomplete( { }",
        "print(@);",
    ],
)
def test_invalid_lexical_and_grammar_inputs_have_stable_parse_diagnostic(source):
    with pytest.raises(SonaSyntaxError) as caught:
        SonaParserv090().parse(source, "invalid.sona")
    diagnostic = caught.value.diagnostic
    assert diagnostic.diagnostic_id in {"SONA-PARSE-001", "SONA-PARSE-003"}
    assert diagnostic.location.file == "invalid.sona"
    assert diagnostic.location.line >= 1
    assert diagnostic.location.column >= 1
    assert diagnostic.suggestion


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("2 + 3 * 4", "14"),
        ("(2 + 3) * 4", "20"),
        ("2 ** 3 ** 2", "512"),
        ("-2 ** 2", "-4"),
        ("(-2) ** 2", "4"),
        ("2 ** -2", "0.25"),
        ("10 - 3 - 2", "5"),
        ("20 / 5 * 2", "8.0"),
        ("1 + 2 < 4", "True"),
        ("3 < 2 < 1", "False"),
        ("1 < 2 < 3", "True"),
        ("true == false or true", "True"),
        ("not true == false", "True"),
        ("false and missing", "False"),
        ("true or missing", "True"),
    ],
)
def test_complete_operator_precedence_matrix(expression, expected):
    assert execute(f"print({expression});") == [expected]


def test_empty_if_body_does_not_swap_else_semantics():
    assert execute('if false { } else { print("else"); };') == ["else"]
    assert execute('if true { } else { print("else"); };') == []


@pytest.mark.parametrize(
    ("feature", "source"),
    [
        ("class", "class Example { }"),
        ("match", "match 1 { 1 => print(1); }"),
        ("destructuring", "let [left, right] = [1, 2];"),
        ("repeat", "repeat 2 { print(1); }"),
        ("export", "export let value = 1;"),
        ("template string", "print(`value`);"),
        ("show", 'show("value");'),
        ("think", 'think("value");'),
        ("calculate", "calculate(1);"),
        ("statement-form when", "when true { true => print(1); }"),
    ],
)
def test_recognized_uncertified_constructs_are_rejected(feature, source):
    with pytest.raises(SonaSyntaxError) as caught:
        SonaParserv090().parse(source, "unsupported.sona")
    assert caught.value.diagnostic.diagnostic_id == "SONA-SEM-099"
    assert feature in str(caught.value)
    assert caught.value.diagnostic.location.column >= 1


def _raw_parser_objects(value, seen=None):
    seen = seen or set()
    if id(value) in seen:
        return []
    seen.add(id(value))
    if isinstance(value, (Tree, Token)):
        return [value]
    if is_dataclass(value):
        return sum(
            (_raw_parser_objects(getattr(value, item.name), seen) for item in fields(value)),
            [],
        )
    if isinstance(value, (list, tuple)):
        return sum((_raw_parser_objects(item, seen) for item in value), [])
    if isinstance(value, dict):
        return sum((_raw_parser_objects(item, seen) for item in value.values()), [])
    return []


def test_stable_ast_shapes_have_no_raw_parser_objects_and_precise_spans():
    source = """let value = 1;
value = value + 1;
func read(flag) {
    if flag { return value; }
}
import string;
while false { continue; }
read(true);
"""
    nodes = SonaParserv090().parse(source, "shape.sona")
    assert _raw_parser_objects(nodes) == []

    by_type = {}
    pending = list(nodes)
    seen = set()
    while pending:
        item = pending.pop()
        if id(item) in seen:
            continue
        seen.add(id(item))
        if is_dataclass(item):
            by_type.setdefault(type(item).__name__, []).append(item)
            pending.extend(getattr(item, field.name) for field in fields(item))
        elif isinstance(item, (list, tuple)):
            pending.extend(item)
        elif isinstance(item, dict):
            pending.extend(item.values())

    required = {
        "VariableAssignment",
        "BinaryOperatorExpression",
        "FunctionDefinition",
        "EnhancedIfStatement",
        "ReturnStatement",
        "ImportStatement",
        "EnhancedWhileLoop",
        "ContinueStatement",
        "CallExpression",
    }
    assert required <= set(by_type)
    for node_type in required:
        for node in by_type[node_type]:
            span = getattr(node, "span", None)
            assert span is not None, node_type
            assert span.file == "shape.sona"
            assert span.start_line >= 1
            assert span.start_column >= 1
            assert span.end_line >= span.start_line
