from __future__ import annotations

from pathlib import Path

import pytest

from sona.errors import SonaImportError
from sona.interpreter import SonaUnifiedInterpreter


def interpreter_with_modules(root: Path) -> tuple[SonaUnifiedInterpreter, Path]:
    modules = root / ".sona_modules"
    modules.mkdir(parents=True)
    return SonaUnifiedInterpreter(project_root=root), modules


def test_workspace_module_precedes_stdlib_and_suffix_aliases_share_cache(tmp_path):
    interpreter, modules = interpreter_with_modules(tmp_path / "workspace with spaces 雪")
    (modules / "string.smod").write_text('let origin = "workspace";', encoding="utf-8")
    first = interpreter.module_system.import_module("string")
    second = interpreter.module_system.import_module("string.smod", alias="text")
    assert first is second
    assert first.origin == "workspace"
    assert interpreter.memory.get_variable("text") is first


def test_module_bindings_constants_and_caller_state_are_isolated(tmp_path):
    interpreter, modules = interpreter_with_modules(tmp_path)
    (modules / "values.smod").write_text(
        'const fixed = 2; let mutable = 3; func total() { fixed + mutable; }',
        encoding="utf-8",
    )
    interpreter.interpret("let mutable = 99;")
    module = interpreter.module_system.import_module("values")
    assert module.fixed == 2
    assert module.mutable == 3
    assert module.total.call([], {}) == 5
    assert interpreter.memory.get_variable("mutable") == 99


def test_failed_module_does_not_poison_cache_and_can_be_reimported(tmp_path):
    interpreter, modules = interpreter_with_modules(tmp_path)
    path = modules / "repairable.smod"
    path.write_text("let value = ;", encoding="utf-8")
    with pytest.raises(SonaImportError) as caught:
        interpreter.module_system.import_module("repairable")
    assert caught.value.diagnostic.diagnostic_id == "SONA-MODULE-003"
    assert "repairable" not in interpreter.module_system.loaded_by_path
    assert interpreter.module_system.import_stack == []

    path.write_text("let value = 7;", encoding="utf-8")
    module = interpreter.module_system.import_module("repairable")
    assert module.value == 7


@pytest.mark.parametrize(
    "module_name",
    ["../outside", "a/b", "a\\b", "C:outside", "", "native_bridge", "intrinsics"],
)
def test_invalid_absolute_relative_and_private_module_names_are_rejected(tmp_path, module_name):
    interpreter = SonaUnifiedInterpreter(project_root=tmp_path)
    with pytest.raises(SonaImportError) as caught:
        interpreter.module_system.import_module(module_name)
    assert caught.value.diagnostic.diagnostic_id == "SONA-MODULE-003"


def test_resolved_symlink_escape_is_rejected_without_platform_specific_symlink_setup(
    tmp_path, monkeypatch
):
    interpreter, modules = interpreter_with_modules(tmp_path / "project")
    candidate = modules / "escape.smod"
    candidate.write_text("let value = 1;", encoding="utf-8")
    outside = (tmp_path / "outside.smod").resolve()
    original_resolve = Path.resolve

    def controlled_resolve(path, *args, **kwargs):
        if path == candidate:
            return outside
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", controlled_resolve)
    with pytest.raises(SonaImportError) as caught:
        interpreter.module_system.import_module("escape")
    assert caught.value.diagnostic.diagnostic_id == "SONA-MODULE-003"


def test_multimodule_circular_trace_is_complete_and_cache_remains_clean(tmp_path):
    interpreter, modules = interpreter_with_modules(tmp_path)
    (modules / "a.smod").write_text("import b;", encoding="utf-8")
    (modules / "b.smod").write_text("import c;", encoding="utf-8")
    (modules / "c.smod").write_text("import a;", encoding="utf-8")
    with pytest.raises(SonaImportError, match="a -> b -> c -> a") as caught:
        interpreter.module_system.import_module("a")
    assert caught.value.diagnostic.diagnostic_id == "SONA-MODULE-002"
    assert not {"a", "b", "c"} & set(interpreter.module_system.loaded_by_path)
    assert interpreter.module_system.import_stack == []

