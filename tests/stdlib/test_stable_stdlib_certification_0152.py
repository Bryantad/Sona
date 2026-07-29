from __future__ import annotations

import sys
from pathlib import Path

from sona.interpreter import SonaUnifiedInterpreter
from sona.stdlib_manifest import manifest_entries, smod_path_for


DOCUMENTED_CALLABLES = {
    "csv": {"parse", "parse_file", "stringify", "write_file", "validate", "extract_fields"},
    "date": {"today", "yesterday", "tomorrow", "parse", "format_iso", "diff"},
    "env": {"get", "get_bool", "get_int", "exists", "set", "delete", "keys", "parse_dotenv"},
    "fs": {"read", "write", "exists", "is_file", "is_dir", "list_dir", "mkdir", "remove"},
    "hashing": {"md5", "sha1", "sha256", "sha512", "sha3_256", "sha3_512", "hash", "checksum"},
    "io": {"input", "write_file", "read_file"},
    "json": {"loads", "load", "dumps", "dump", "pretty", "is_valid", "validate"},
    "math": {"add", "subtract", "multiply", "divide", "sqrt", "pow", "clamp", "round"},
    "path": {"join", "normalize", "basename", "dirname", "extension", "is_absolute", "is_relative", "resolve"},
    "string": {"upper", "lower", "title", "trim", "contains", "starts_with", "ends_with", "split"},
    "time": {"now", "utcnow", "timestamp", "from_timestamp", "parse", "format_iso", "diff"},
    "profile": {"available", "activate", "activate_many", "current", "configure", "reset"},
}


def _callable(value) -> bool:
    return callable(value) or callable(getattr(value, "call", None))


def test_every_stable_manifest_module_has_source_exports_and_no_placeholder_markers(tmp_path):
    interpreter = SonaUnifiedInterpreter(project_root=tmp_path)
    stable = [
        item for item in manifest_entries()
        if item.get("stability") in {"stable", "core"}
    ]
    assert stable
    for entry in stable:
        name = entry["name"]
        module = interpreter.module_system.import_module(name)
        public = {
            attr: getattr(module, attr)
            for attr in dir(module)
            if not attr.startswith("_")
        }
        assert public, name
        assert any(
            _callable(value) or isinstance(value, (str, int, float, bool, list, dict, tuple))
            for value in public.values()
        ), name
        if entry.get("public_smod"):
            source = smod_path_for(name)
            assert source.exists(), name
            text = source.read_text(encoding="utf-8").lower()
            assert "notimplemented" not in text
            assert "placeholder" not in text
            assert "todo" not in text

    assert not {
        "torch", "transformers", "accelerate", "openai", "anthropic"
    } & set(sys.modules)


def test_every_detailed_stable_reference_symbol_exists_and_is_usable(tmp_path):
    interpreter = SonaUnifiedInterpreter(project_root=tmp_path)
    for module_name, symbols in DOCUMENTED_CALLABLES.items():
        module = interpreter.module_system.import_module(module_name)
        missing = sorted(symbol for symbol in symbols if not hasattr(module, symbol))
        assert missing == [], (module_name, missing)
        noncallable = sorted(
            symbol for symbol in symbols
            if not _callable(getattr(module, symbol))
        )
        assert noncallable == [], (module_name, noncallable)


def test_representative_stable_stdlib_behavior(tmp_path):
    interpreter = SonaUnifiedInterpreter(project_root=tmp_path)

    def call(module_name, symbol, *args):
        value = getattr(interpreter.module_system.import_module(module_name), symbol)
        if callable(getattr(value, "call", None)):
            return value.call(list(args), {})
        return value(*args)

    assert call("math", "sqrt", 16) == 4
    assert call("string", "upper", "sona") == "SONA"
    assert call("json", "is_valid", '{"ok": true}') is True
    assert call("hashing", "sha256", "sona") == "9a5a846499c7f4597a8430d1c3df5478d84160d89b68cdfebc4a847e213504d2"
    assert call("path", "basename", "folder/example.sona") == "example.sona"
    assert call("url", "encode", "a b") == "a%20b"
