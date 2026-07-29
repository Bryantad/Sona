"""Compatibility characterization for behavior inherited from Sona 0.15.1."""
import warnings

import pytest

from sona.cli import execute_sona
from sona.interpreter import SonaRuntimeError, SonaUnifiedInterpreter


def test_function_preserves_implicit_final_statement_value(capsys):
    SonaUnifiedInterpreter().interpret("func value() { 7; }; print(value());")
    assert capsys.readouterr().out.strip() == "7"


def test_function_parameter_shadowing_does_not_replace_global(capsys):
    code = "let value = 1; func read(value) { return value; }; print(read(2)); print(value);"
    SonaUnifiedInterpreter().interpret(code)
    assert capsys.readouterr().out.splitlines() == ["2", "1"]


def test_loop_iterator_uses_temporary_frame_without_replacing_outer_binding(capsys):
    SonaUnifiedInterpreter().interpret("let item = 9; for item in [1, 2] { print(item); }; print(item);")
    assert capsys.readouterr().out.splitlines() == ["1", "2", "9"]


def test_bare_assignment_updates_nearest_binding_including_global(capsys):
    SonaUnifiedInterpreter().interpret("let total = 1; func bump() { total = 2; }; bump(); print(total);")
    assert capsys.readouterr().out.strip() == "2"


def test_function_scope_is_restored_after_error():
    interpreter = SonaUnifiedInterpreter()
    with pytest.raises(SonaRuntimeError) as raised:
        interpreter.interpret("func fail(arg) { missing(); }; fail(1);")
    assert "function:fail" in raised.value.diagnostic.call_stack
    assert interpreter.memory.local_scopes == []
    assert interpreter.memory.call_stack == []


def test_arity_errors_remain_actionable():
    interpreter = SonaUnifiedInterpreter()
    with pytest.raises(SonaRuntimeError, match="missing required argument: right") as raised:
        interpreter.interpret("func add(left, right) { return left + right; }; add(1);")
    assert raised.value.diagnostic.diagnostic_id == "SONA-RUNTIME-001"


def test_non_callable_and_invalid_control_flow_have_stable_compatibility_diagnostics():
    with pytest.raises(SonaRuntimeError) as non_callable:
        SonaUnifiedInterpreter(compatibility_mode="python").interpret("value = 1\nvalue()")
    assert non_callable.value.diagnostic.diagnostic_id == "SONA-RUNTIME-002"
    with pytest.raises(SonaRuntimeError) as sona_non_callable:
        SonaUnifiedInterpreter().interpret("let value = 1;\nvalue();", filename="fixture.sona")
    assert sona_non_callable.value.diagnostic.diagnostic_id == "SONA-RUNTIME-002"
    assert sona_non_callable.value.location.file == "fixture.sona"

    with pytest.raises(SonaRuntimeError) as control_flow:
        SonaUnifiedInterpreter().interpret("break;")
    assert control_flow.value.diagnostic.diagnostic_id == "SONA-SEM-002"
    with pytest.raises(SonaRuntimeError) as invalid_return:
        SonaUnifiedInterpreter().interpret("return 1;")
    assert invalid_return.value.diagnostic.diagnostic_id == "SONA-SEM-002"


def test_separate_cli_program_executions_are_isolated():
    execute_sona("let only_first = 1;")
    with pytest.raises(Exception, match="only_first"):
        execute_sona("print(only_first);")


def test_auto_python_fallback_is_preserved_with_migration_guidance():
    interpreter = SonaUnifiedInterpreter(compatibility_mode="auto")
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        assert interpreter.interpret("value = lambda: 2\nvalue() + 3") == 5
    assert any("compatibility fallback" in str(item.message) for item in captured)


def test_explicit_python_compatibility_api():
    assert SonaUnifiedInterpreter(compatibility_mode="python").interpret("2 + 3") == 5


def test_canonical_only_mode_does_not_fallback():
    with pytest.raises(Exception):
        SonaUnifiedInterpreter(compatibility_mode="sona").interpret("value = lambda: 1")


def test_execute_string_respects_configured_compatibility_mode():
    with pytest.raises(Exception):
        SonaUnifiedInterpreter(compatibility_mode="sona").execute("value = lambda: 1")

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        assert SonaUnifiedInterpreter(compatibility_mode="auto").execute("value = lambda: 2\nvalue() + 3") == 5
    assert any("compatibility fallback" in str(item.message) for item in captured)

    assert SonaUnifiedInterpreter(compatibility_mode="python").execute("2 + 3") == 5


def test_recognized_unsupported_syntax_never_falls_back_to_python():
    with pytest.raises(Exception, match="SONA-SEM-099"):
        SonaUnifiedInterpreter(compatibility_mode="auto").interpret("class Example { }")
