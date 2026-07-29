import pytest

from sona.errors import SonaImportError
from sona.interpreter import SonaRuntimeError, SonaUnifiedInterpreter
from sona.cli import execute_sona


def test_const_reassignment_is_rejected():
    interpreter = SonaUnifiedInterpreter()
    with pytest.raises(SonaRuntimeError, match="const binding 'answer'"):
        interpreter.interpret("const answer = 42; answer = 43;")
    record = interpreter.memory.global_scope.record("answer")
    assert record is not None and record.is_const is True
    assert record.definition_span is not None


def test_power_is_right_associative_and_boolean_short_circuits(capsys):
    interpreter = SonaUnifiedInterpreter()
    interpreter.interpret("print(2 ** 3 ** 2); print(false and missing);")
    assert capsys.readouterr().out.splitlines() == ["512", "False"]


def test_loop_limit_and_scope_cleanup():
    interpreter = SonaUnifiedInterpreter(maximum_loop_iterations=2)
    with pytest.raises(SonaRuntimeError, match="loop iteration") as raised:
        interpreter.interpret("let i = 0; while i < 5 { i = i + 1; };")
    assert raised.value.diagnostic.diagnostic_id == "SONA-RUNTIME-011"
    assert interpreter.memory.local_scopes == []


def test_persistent_runtime_memory_is_opt_in(tmp_path):
    SonaUnifiedInterpreter(project_root=tmp_path)
    assert not (tmp_path / ".sona" / "runtime_memory.db").exists()


def test_reset_preserves_limits_and_close_is_idempotent(tmp_path):
    interpreter = SonaUnifiedInterpreter(project_root=tmp_path, maximum_loop_iterations=7)
    interpreter.interpret("let temporary = 1;")
    interpreter.reset()
    assert interpreter.maximum_loop_iterations == 7
    assert not interpreter.memory.has_variable("temporary")
    interpreter.close()
    interpreter.close()
    assert interpreter._closed is True


def test_invalid_module_identifiers_are_confined(tmp_path):
    interpreter = SonaUnifiedInterpreter(project_root=tmp_path)
    with pytest.raises(SonaImportError, match="Invalid module path") as invalid:
        interpreter.module_system.import_module("../outside")
    assert invalid.value.diagnostic.diagnostic_id == "SONA-MODULE-003"

    with pytest.raises(SonaImportError, match="Module file not found") as missing:
        interpreter.module_system.import_module("definitely_missing_module")
    assert missing.value.diagnostic.diagnostic_id == "SONA-MODULE-001"


def test_entry_file_modules_resolve_relative_to_entry_not_process_cwd(tmp_path, monkeypatch, capsys):
    project = tmp_path / "project"
    modules = project / ".sona_modules"
    elsewhere = tmp_path / "elsewhere"
    modules.mkdir(parents=True)
    elsewhere.mkdir()
    (modules / "helper.smod").write_text("let message = \"relative\";", encoding="utf-8")
    entry = project / "main.sona"
    entry.write_text("import helper; print(helper.message);", encoding="utf-8")
    monkeypatch.chdir(elsewhere)
    execute_sona(entry.read_text(encoding="utf-8"), file_path=str(entry))
    assert capsys.readouterr().out.strip() == "relative"


def test_module_globals_are_isolated_and_state_restores_after_import_failure(tmp_path):
    modules = tmp_path / ".sona_modules"
    modules.mkdir()
    (modules / "isolated.smod").write_text("let leaked = caller_secret;", encoding="utf-8")
    interpreter = SonaUnifiedInterpreter(project_root=tmp_path)
    interpreter.interpret('let caller_secret = "private";')
    before = dict(interpreter.memory.global_scope)
    with pytest.raises(Exception, match="caller_secret"):
        interpreter.module_system.import_module("isolated")
    assert dict(interpreter.memory.global_scope) == before
    assert interpreter.module_system.import_stack == []


def test_circular_import_reports_trace_and_stable_module_diagnostic(tmp_path):
    modules = tmp_path / ".sona_modules"
    modules.mkdir()
    (modules / "a.smod").write_text("import b;", encoding="utf-8")
    (modules / "b.smod").write_text("import a;", encoding="utf-8")
    interpreter = SonaUnifiedInterpreter(project_root=tmp_path)
    with pytest.raises(SonaImportError, match="a -> b -> a") as circular:
        interpreter.module_system.import_module("a")
    assert circular.value.diagnostic.diagnostic_id == "SONA-MODULE-002"
    assert interpreter.module_system.import_stack == []
