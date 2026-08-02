from __future__ import annotations

import json
from pathlib import Path

import pytest

from sona.stdlib.errors import StdlibError
from sona.stdlib.native_fs import build_native_bridge as build_fs
from sona.stdlib.native_io import build_native_bridge as build_io
from sona.stdlib.native_json import json_parse, json_stringify
from sona.stdlib import random as random_module
from sona.stdlib import string as string_module
from sona.interpreter import SonaUnifiedInterpreter


class _Interpreter:
    def __init__(self, root: Path, *, safe: bool = False) -> None:
        self.project_root = root
        self.safe_mode = safe
        self.stdlib_capabilities = None


def _assert_error(error: StdlibError, diagnostic_id: str, code: str) -> None:
    assert error.diagnostic.diagnostic_id == diagnostic_id
    assert error.code == code
    assert error.diagnostic.suggestion
    assert "operation=" in error.diagnostic.message


def test_canonical_filesystem_api_is_utf8_sorted_and_alias_compatible(tmp_path):
    fs = build_fs(_Interpreter(tmp_path))
    nested = tmp_path / "nested" / "snow-\N{SNOWMAN}.txt"

    assert fs.fs_write_text(nested, "Sona \N{CHECK MARK}") == 6
    assert fs.fs_append_text(nested, "!") == 1
    assert fs.fs_read_text(nested) == "Sona \N{CHECK MARK}!"
    assert fs.fs_read(nested) == fs.fs_read_text(nested)
    assert fs.fs_exists(nested) is True
    assert fs.fs_is_file(nested) is True
    assert fs.fs_is_dir(nested.parent) is True
    assert fs.fs_list_dir(tmp_path) == ["nested"]
    assert fs.fs_list_dir(tmp_path, True) == ["nested", "nested/snow-\N{SNOWMAN}.txt"]

    renamed = tmp_path / "renamed.txt"
    copied = tmp_path / "copied.txt"
    assert Path(fs.fs_rename(nested, renamed)) == renamed
    assert Path(fs.fs_copy(renamed, copied)) == copied
    assert fs.fs_remove(copied) is True
    assert fs.fs_remove(copied) is False


def test_filesystem_failures_are_stable_structured_diagnostics(tmp_path):
    fs = build_fs(_Interpreter(tmp_path))
    with pytest.raises(StdlibError) as caught:
        fs.fs_read_text(tmp_path / "missing.txt")
    _assert_error(caught.value, "SONA-FS-002", "E0601")

    with pytest.raises(StdlibError) as caught:
        fs.fs_read_text(tmp_path / "x", "utf-16")
    _assert_error(caught.value, "SONA-FS-006", "E0603")


def test_safe_mode_confines_reads_and_denies_writes_and_secret_files(tmp_path):
    public = tmp_path / "public.txt"
    public.write_text("ok", encoding="utf-8")
    secret = tmp_path / ".env"
    secret.write_text("TOKEN=not-returned", encoding="utf-8")
    local_secret = tmp_path / ".env.local"
    local_secret.write_text("TOKEN=also-not-returned", encoding="utf-8")
    fs = build_fs(_Interpreter(tmp_path, safe=True))

    assert fs.fs_read_text("public.txt") == "ok"
    for operation in (
        lambda: fs.fs_write_text("new.txt", "blocked"),
        lambda: fs.fs_read_text("../outside.txt"),
        lambda: fs.fs_read_text(".env"),
        lambda: fs.fs_read_text(".env.local"),
    ):
        with pytest.raises(StdlibError) as caught:
            operation()
        _assert_error(caught.value, "SONA-FS-005", "E0600")
        assert "not-returned" not in caught.value.diagnostic.message
        assert "also-not-returned" not in caught.value.diagnostic.message


def test_json_random_and_string_canonical_names_preserve_aliases():
    value = json_parse('{"b":2,"a":1}')
    assert json_stringify(value) == '{"a": 1, "b": 2}'
    assert json.loads(json_stringify(value, indent=2)) == value
    with pytest.raises(StdlibError) as caught:
        json_parse("{")
    _assert_error(caught.value, "SONA-JSON-001", "E0501")

    random_module.seed(57)
    canonical = (random_module.integer(1, 10), random_module.float())
    random_module.seed(57)
    aliases = (random_module.randint(1, 10), random_module.random())
    assert canonical == aliases

    assert string_module.starts_with("sona", "so") is True
    assert string_module.startswith("sona", "so") is True
    assert string_module.ends_with("sona", "na") is True
    assert string_module.endswith("sona", "na") is True


def test_stdin_and_io_are_split_without_removing_the_legacy_input_alias(tmp_path, monkeypatch):
    interpreter = _Interpreter(tmp_path)
    io = build_io(interpreter)
    prompts: list[str] = []

    def fake_input(prompt=""):
        prompts.append(prompt)
        return "answer"

    monkeypatch.setattr("builtins.input", fake_input)
    assert io.stdin_read("Question? ") == "answer"
    assert io.io_input("Legacy? ") == "answer"
    assert prompts == ["Question? ", "Legacy? "]


def test_stdlib_failure_points_to_the_application_call_not_internal_smod(tmp_path):
    interpreter = SonaUnifiedInterpreter(project_root=tmp_path)
    with pytest.raises(StdlibError) as caught:
        interpreter.interpret(
            'import json\njson.parse("{")',
            filename="app/broken.sona",
        )

    location = caught.value.diagnostic.location
    assert location.file == "app/broken.sona"
    assert location.line == 2
    assert location.column == 1
