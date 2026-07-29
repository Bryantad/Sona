from __future__ import annotations

from pathlib import Path

import pytest

from sona.errors import SonaError
from sona.interpreter import SonaRuntimeError, SonaUnifiedInterpreter


def call(fn, *args):
    if hasattr(fn, "call"):
        return fn.call(list(args), {})
    return fn(*args)


def run(source: str, *, project_root: Path | None = None, filename: str = "<string>"):
    return SonaUnifiedInterpreter(
        project_root=project_root,
        compatibility_mode="sona",
    ).interpret(source, filename=filename)


@pytest.mark.parametrize(
    ("source", "assertion"),
    [
        (
            "cognitive_check();",
            lambda result: result["cognitive_load"] in {"low", "medium", "high"}
            and result["task"] == "",
        ),
        (
            'cognitive_check("test");',
            lambda result: result["task"] == "test"
            and result["cognitive_load"] in {"low", "medium", "high"},
        ),
        (
            "focus_mode();",
            lambda result: result["status"] == "ok"
            and result["session"]["description"] == "focus",
        ),
        (
            'focus_mode("analysis");',
            lambda result: result["status"] == "ok"
            and result["session"]["description"] == "analysis",
        ),
        (
            'focus_mode(mode="analysis", minutes=25);',
            lambda result: result["status"] == "ok"
            and result["session"]["description"] == "analysis"
            and result["session"]["minutes"] == 25,
        ),
        (
            "working_memory();",
            lambda result: result == {"status": "ok", "size": 0, "keys": []},
        ),
        (
            'working_memory("status");',
            lambda result: result == {"status": "ok", "size": 0, "keys": []},
        ),
        (
            'working_memory("store", "x", 10);',
            lambda result: result["status"] == "ok"
            and result["stored"] is True
            and result["key"] == "x"
            and result["value"] == 10,
        ),
        (
            'working_memory(action="store", key="x", value=10);',
            lambda result: result["status"] == "ok"
            and result["stored"] is True
            and result["key"] == "x"
            and result["value"] == 10,
        ),
        (
            "intent();",
            lambda result: result["status"] == "ok"
            and result["intent"]["goal"] is None
            and result["intent"]["meta"] == {},
        ),
        (
            'intent("finish task");',
            lambda result: result["status"] == "ok"
            and result["intent"]["goal"] == "finish task",
        ),
        (
            "profile();",
            lambda result: result["status"] == "error"
            and "profile name" in result["message"],
        ),
        (
            'profile("adhd");',
            lambda result: result["status"] == "ok" and result["profile"] == "adhd",
        ),
    ],
)
def test_cognitive_empty_optional_positional_and_keyword_forms(source, assertion):
    result = run(source)
    assert assertion(result)


def test_malformed_cognitive_spread_uses_sona_diagnostic():
    with pytest.raises(SonaRuntimeError) as raised:
        run("focus_mode(...5);", filename="cognitive.sona")

    assert "AttributeError" not in str(raised.value)
    assert raised.value.diagnostic.diagnostic_id == "SONA-COG-001"
    assert raised.value.diagnostic.location.file == "cognitive.sona"
    assert raised.value.diagnostic.suggestion


def test_guardian_public_facade_check_and_doctor_are_safe(tmp_path):
    project = tmp_path / "fixture"
    project.mkdir()
    (project / "app.sona").write_text('print("hello");\n', encoding="utf-8")

    before = sorted(p.relative_to(project).as_posix() for p in project.rglob("*"))
    interp = SonaUnifiedInterpreter(project_root=project, compatibility_mode="sona")
    module = interp.module_system.import_module("guardian")
    after_import = sorted(p.relative_to(project).as_posix() for p in project.rglob("*"))

    assert after_import == before
    for name in ("status", "verify", "check", "diff", "doctor", "graph"):
        assert hasattr(module, name), name

    assert call(module.status, str(project))["initialized"] is False
    assert call(module.verify, str(project))["status"] == "uninitialized"
    assert call(module.check, str(project))["status"] == "uninitialized"
    assert call(module.doctor, str(project))["initialized"] is False

    after_calls = sorted(p.relative_to(project).as_posix() for p in project.rglob("*"))
    assert after_calls == before


def test_guardian_check_rejects_invalid_project_root_without_missing_method():
    interp = SonaUnifiedInterpreter(compatibility_mode="sona")
    result = interp.execute('import guardian; guardian.check("hello");')
    assert result["status"] == "invalid-project-root"
    assert result["diagnostic_id"] == "SONA-GUARD-001"
    assert "Object has no method" not in result["message"]


def test_imported_module_repr_is_sona_native(capsys):
    run("import receipt; print(receipt);")
    run("import guardian; print(guardian);")
    assert capsys.readouterr().out.splitlines() == [
        "<module 'receipt'>",
        "<module 'guardian'>",
    ]


@pytest.mark.parametrize(
    ("source", "code", "diagnostic_id", "hint"),
    [
        ("print(not_defined);", "E0401", "SONA-RUNTIME-003", "Declare"),
        ("unknown_function();", "E0402", "SONA-RUNTIME-003", "function"),
        ("print(1 / 0);", "E0301", "SONA-RUNTIME-004", "nonzero"),
        ("print(1 % 0);", "E0301", "SONA-RUNTIME-004", "nonzero"),
        ("let x=[1]; print(x[2]);", "E0302", "SONA-RUNTIME-006", "in-range"),
        ('let x={"a": 1}; print(x["b"]);', "E0302", "SONA-RUNTIME-006", "in-range"),
        ("func f(a) { return a; }; f();", "E0300", "SONA-RUNTIME-001", "arguments"),
        ("import guardian; guardian.nope();", "E0300", "SONA-RUNTIME-007", "method"),
    ],
)
def test_runtime_errors_have_stable_diagnostics(source, code, diagnostic_id, hint):
    with pytest.raises(SonaRuntimeError) as raised:
        run(source, filename="diagnostics.sona")

    diagnostic = raised.value.diagnostic
    assert diagnostic.code.value == code
    assert diagnostic.diagnostic_id == diagnostic_id
    assert hint.lower() in diagnostic.suggestion.lower()
    assert diagnostic.location.file == "diagnostics.sona"
    assert "Traceback" not in str(raised.value)


def test_undefined_identifier_called_uses_function_oriented_message():
    with pytest.raises(SonaRuntimeError) as raised:
        run("unknown_function();", filename="functions.sona")

    assert raised.value.diagnostic.code.value == "E0402"
    assert raised.value.diagnostic.message == "Function 'unknown_function' is not defined."


def test_default_operator_coercion_contract_remains_backward_compatible(capsys):
    run(
        """
        print("hello" + 5);
        print(5 + "hello");
        print(true + 5);
        print([1,2] + [3,4]);
        """
    )
    assert capsys.readouterr().out.splitlines() == [
        "hello5",
        "5hello",
        "6",
        "[1, 2, 3, 4]",
    ]


@pytest.mark.parametrize("source", ["fn add(a, b) { return a + b; }", "use math;"])
def test_unsupported_legacy_syntax_has_stable_parse_diagnostic(source):
    with pytest.raises(SonaError) as raised:
        run(source, filename="syntax.sona")
    assert raised.value.diagnostic.diagnostic_id.startswith("SONA-PARSE-")
    assert raised.value.diagnostic.location.file == "syntax.sona"
