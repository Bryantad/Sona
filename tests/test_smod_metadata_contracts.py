from pathlib import Path


STDLIB_ROOT = Path("stdlib")

NATIVE_SMOD_MODULES = (
    "csv",
    "date",
    "env",
    "fs",
    "hashing",
    "io",
    "json",
    "math",
    "memory",
    "path",
    "queue",
    "random",
    "regex",
    "stack",
    "string",
    "time",
    "uuid",
)

NESTED_NATIVE_SMOD_MODULES = (
    ("utils", "convert"),
    ("utils", "validate", "validate"),
)


def _read_module_text(module_name: str) -> str:
    return (STDLIB_ROOT / f"{module_name}.smod").read_text(encoding="utf-8")


def _read_nested_module_text(*parts: str) -> str:
    return STDLIB_ROOT.joinpath(*parts).with_suffix(".smod").read_text(encoding="utf-8")


def test_all_stdlib_smod_files_are_bridge_free():
    for smod_file in sorted(STDLIB_ROOT.rglob("*.smod")):
        text = smod_file.read_text(encoding="utf-8")
        assert "__native__" not in text, f"{smod_file} still uses __native__"
        assert "smod-bridge" not in text, f"{smod_file} still declares smod-bridge"


def test_top_level_smod_modules_have_native_contract_metadata():
    for module_name in NATIVE_SMOD_MODULES:
        text = _read_module_text(module_name)
        assert 'const module_format = "smod-runtime"' in text, (
            f"{module_name} missing module_format"
        )
        assert 'const runtime_backend = "smod"' in text, (
            f"{module_name} missing native runtime_backend"
        )


def test_nested_smod_modules_have_native_contract_metadata():
    for module_parts in NESTED_NATIVE_SMOD_MODULES:
        text = _read_nested_module_text(*module_parts)
        module_name = "/".join(module_parts)
        assert 'const module_format = "smod-runtime"' in text, (
            f"{module_name} missing module_format"
        )
        assert 'const runtime_backend = "smod"' in text, (
            f"{module_name} missing native runtime_backend"
        )
