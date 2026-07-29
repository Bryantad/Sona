from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO

import pytest
from lark import Tree

from sona.errors import SonaError, SonaSyntaxError
from sona.interpreter import SonaRuntimeError, SonaUnifiedInterpreter


def run(source: str, *, interpreter=None) -> tuple[list[str], object]:
    interpreter = interpreter or SonaUnifiedInterpreter(compatibility_mode="sona")
    output = StringIO()
    with redirect_stdout(output):
        result = interpreter.interpret(source, filename="semantics.sona")
    return output.getvalue().splitlines(), result


def test_binding_declaration_reassignment_shadowing_and_compatibility_rules():
    output, _ = run(
        """let value = 1;
value = 2;
func local() { let value = 3; value = 4; value; }
print(local());
print(value);
let value = 5;
print(value);
created_before_declaration = 6;
print(created_before_declaration);
"""
    )
    assert output == ["4", "2", "5", "6"]


def test_nearest_binding_assignment_and_loop_iterator_cleanup():
    output, _ = run(
        """let total = 0;
let item = 9;
func add() {
    for item in [1, 2, 3] { total = total + item; }
}
add();
print(total);
print(item);
"""
    )
    assert output == ["6", "9"]


def test_const_failures_have_stable_id_and_attempt_location():
    with pytest.raises(SonaRuntimeError) as caught:
        run("const answer = 42;\nanswer = 43;")
    diagnostic = caught.value.diagnostic
    assert diagnostic.diagnostic_id == "SONA-SEM-001"
    assert diagnostic.location.file == "semantics.sona"
    assert diagnostic.location.line == 2
    assert diagnostic.location.column == 1


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ('print(null); print(true); print(false);', ["None", "True", "False"]),
        ('print(1); print(1.5); print("text");', ["1", "1.5", "text"]),
        ('print([1, 2]); print({"a": 1});', ["[1, 2]", "{'a': 1}"]),
        ('print("a" + 2); print("x" * 3);', ["a2", "xxx"]),
        ('print([] == []); print({"a": 1} == {"a": 1});', ["True", "True"]),
        ('if [] { print(1); } else { print(0); }', ["0"]),
        ('if [1] { print(1); } else { print(0); }', ["1"]),
    ],
)
def test_runtime_value_construction_printing_equality_and_truthiness(source, expected):
    assert run(source)[0] == expected


def test_function_semantics_cover_arity_returns_recursion_and_experimental_arguments():
    output, _ = run(
        """func zero() { 7; }
func add(left, right=2) { return left + right; }
func gather(first, ...rest) { return first + rest[0]; }
func factorial(value) {
    if value <= 1 { return 1; }
    return value * factorial(value - 1);
}
print(zero());
print(add(3));
print(add(right=4, left=3));
print(gather(...[5, 6]));
print(factorial(5));
"""
    )
    assert output == ["7", "5", "7", "11", "120"]


@pytest.mark.parametrize(
    ("source", "diagnostic_id"),
    [
        ("missing;", "SONA-RUNTIME-003"),
        ("missing();", "SONA-RUNTIME-003"),
        ("let value = 1; value();", "SONA-RUNTIME-002"),
        ("func one(value) { value; } one();", "SONA-RUNTIME-001"),
        ("print(1 / 0);", "SONA-RUNTIME-004"),
        ('print(1 - "x");', "SONA-RUNTIME-005"),
        ("print([1][5]);", "SONA-RUNTIME-006"),
        ('print({"a": 1}.missing);', "SONA-RUNTIME-007"),
        ("break;", "SONA-SEM-002"),
        ("continue;", "SONA-SEM-002"),
        ("return 1;", "SONA-SEM-002"),
    ],
)
def test_runtime_failures_have_stable_ids_and_source_locations(source, diagnostic_id):
    with pytest.raises(SonaError) as caught:
        run(source)
    diagnostic = caught.value.diagnostic
    assert diagnostic.diagnostic_id == diagnostic_id
    assert diagnostic.location.line >= 1
    assert diagnostic.location.column >= 1


def test_control_flow_signals_cleanup_after_nested_loops_and_returns():
    output, _ = run(
        """func find() {
    for outer in [1, 2, 3] {
        for inner in [1, 2, 3] {
            if inner == 1 { continue; }
            if outer == 2 and inner == 2 { return outer + inner; }
            if inner == 3 { break; }
        }
    }
}
print(find());
print("restored");
"""
    )
    assert output == ["4", "restored"]


def test_failed_program_does_not_corrupt_reset_or_fresh_interpreters():
    interpreter = SonaUnifiedInterpreter(compatibility_mode="sona")
    run("let retained = 1;", interpreter=interpreter)
    with pytest.raises(SonaRuntimeError):
        run("missing();", interpreter=interpreter)
    assert run("print(retained);", interpreter=interpreter)[0] == ["1"]
    interpreter.reset()
    with pytest.raises(SonaRuntimeError):
        run("print(retained);", interpreter=interpreter)
    with pytest.raises(SonaRuntimeError):
        run("print(retained);")


def test_auto_compatibility_is_limited_to_explicit_python_only_syntax_and_warns():
    with pytest.warns(FutureWarning, match="Legacy Python compatibility"):
        result = SonaUnifiedInterpreter(compatibility_mode="auto").interpret(
            "value = lambda: 2\nvalue() + 3"
        )
    assert result == 5

    with pytest.raises(SonaSyntaxError) as caught:
        SonaUnifiedInterpreter(compatibility_mode="auto").interpret("let value = ;")
    assert caught.value.diagnostic.diagnostic_id == "SONA-PARSE-001"


def test_raw_lark_tree_is_rejected_and_never_reinterpreted_as_python():
    with pytest.raises(SonaRuntimeError) as caught:
        SonaUnifiedInterpreter(compatibility_mode="sona").execute(Tree("raw", []))
    assert caught.value.diagnostic.diagnostic_id == "SONA-PARSE-099"

