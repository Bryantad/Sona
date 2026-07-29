from __future__ import annotations

import random
from contextlib import redirect_stdout
from io import StringIO

import pytest

from sona.errors import SonaSyntaxError
from sona.interpreter import SonaUnifiedInterpreter
from sona.parser_v090 import SonaParserv090


SEED = 1_522_026


def execute(source: str) -> str:
    output = StringIO()
    with redirect_stdout(output):
        SonaUnifiedInterpreter(compatibility_mode="sona").interpret(
            source, filename=f"generated-seed-{SEED}.sona"
        )
    return output.getvalue()


def expression(rng: random.Random, depth: int = 0) -> str:
    if depth >= 3 or rng.random() < 0.28:
        return str(rng.randint(0, 9))
    if rng.random() < 0.2:
        return f"(-{expression(rng, depth + 1)})"
    operator = rng.choice(["+", "-", "*", "%", "**", "<", ">=", "=="])
    left = expression(rng, depth + 1)
    right = str(rng.randint(1, 4)) if operator in {"%", "**"} else expression(rng, depth + 1)
    return f"({left} {operator} {right})"


def test_fixed_seed_generated_valid_programs_parse_transform_and_execute_deterministically():
    rng = random.Random(SEED)
    parser = SonaParserv090()
    programs = []
    for index in range(40):
        expr = expression(rng)
        programs.append(
            f"let value{index} = {expr}; "
            f"func read{index}() {{ value{index}; }} "
            f"if true {{ print(read{index}()); }}"
        )
    programs.extend(
        [
            "let total = 0; for item in [1,2,3] { total = total + item; } print(total);",
            "let count = 0; while count < 3 { count = count + 1; } print(count);",
            "func choose(flag) { if flag { return 1; } return 2; } print(choose(false));",
            "import string; print(string.upper(\"seeded\"));",
        ]
    )
    for source in programs:
        nodes = parser.parse(source, f"generated-seed-{SEED}.sona")
        assert nodes
        assert parser._find_raw_parser_object(nodes) is None
        assert execute(source) == execute(source)


@pytest.mark.parametrize(
    "source",
    [
        "let value = (1 + 2;",
        "let value = 1 + * 2;",
        'print("truncated);',
        "if true { print(1);",
        "func value( { return 1; }",
        "for item in { print(item); }",
        "import ../outside;",
        "let = 2;",
        "print(1 @ 2);",
        "while { print(1); }",
        "return + ;",
        "let value = [1, 2;",
    ],
)
def test_fixed_invalid_mutations_fail_safely_without_fallback(source):
    with pytest.raises(SonaSyntaxError) as caught:
        SonaUnifiedInterpreter(compatibility_mode="auto").interpret(
            source, filename=f"mutation-seed-{SEED}.sona"
        )
    assert caught.value.diagnostic.diagnostic_id in {
        "SONA-PARSE-001", "SONA-PARSE-003", "SONA-SEM-099"
    }


def test_metamorphic_whitespace_comments_parentheses_and_fresh_state_invariants():
    compact = "let left=2;let right=3;print(left+right*4);"
    spaced = """// generated with seed 1522026

let left = 2;
let right = 3; // irrelevant comment
print(left + (right * 4));
"""
    assert execute(compact) == execute(spaced) == "14\n"
    assert execute(compact) == execute(compact)
