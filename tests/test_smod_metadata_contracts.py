from pathlib import Path


# Wave-1: original bridge modules (env, fs, io, json, path)
WAVE1_BRIDGE_MODULES = ("env", "fs", "io", "json", "path")

# Wave-2: native pure-Sona modules (runtime_backend = "smod")
WAVE2_NATIVE_MODULES = ("queue", "stack", "random", "uuid", "regex")

# Wave-2 bridge: native modules that still use __native__ calls
WAVE2_BRIDGE_MODULES = ("hashing",)

# Wave-3: remaining stdlib bridge modules newly annotated in 0.11.0
WAVE3_BRIDGE_MODULES = ("csv", "date", "math", "string", "time")


def _read_module_text(module_name: str) -> str:
    path = Path("stdlib") / f"{module_name}.smod"
    return path.read_text(encoding="utf-8")


def _read_nested_module_text(*parts: str) -> str:
    path = Path("stdlib").joinpath(*parts).with_suffix(".smod")
    return path.read_text(encoding="utf-8")


def test_wave1_bridge_modules_have_explicit_contract_metadata():
    for module_name in WAVE1_BRIDGE_MODULES:
        text = _read_module_text(module_name)
        assert 'const module_format = "smod-runtime"' in text, (
            f"{module_name} missing module_format"
        )
        assert 'const runtime_backend = "smod-bridge"' in text, (
            f"{module_name} missing runtime_backend"
        )


def test_wave2_native_modules_have_smod_backend():
    """Pure-Sona modules declare runtime_backend = 'smod'."""
    for module_name in WAVE2_NATIVE_MODULES:
        text = _read_module_text(module_name)
        assert 'const module_format = "smod-runtime"' in text, (
            f"{module_name} missing module_format"
        )
        assert 'const runtime_backend = "smod"' in text, (
            f"{module_name} missing runtime_backend"
        )


def test_utils_convert_nested_module_has_smod_backend():
    text = _read_nested_module_text("utils", "convert")
    assert 'const module_format = "smod-runtime"' in text
    assert 'const runtime_backend = "smod"' in text


def test_wave2_bridge_modules_have_bridge_backend():
    """Hashing uses __native__ calls → smod-bridge."""
    for module_name in WAVE2_BRIDGE_MODULES:
        text = _read_module_text(module_name)
        assert 'const module_format = "smod-runtime"' in text, (
            f"{module_name} missing module_format"
        )
        assert 'const runtime_backend = "smod-bridge"' in text, (
            f"{module_name} missing runtime_backend"
        )


def test_wave3_bridge_modules_have_explicit_contract_metadata():
    """csv, date, math, string, time — newly annotated in 0.11.0."""
    for module_name in WAVE3_BRIDGE_MODULES:
        text = _read_module_text(module_name)
        assert 'const module_format = "smod-runtime"' in text, (
            f"{module_name} missing module_format"
        )
        assert 'const runtime_backend = "smod-bridge"' in text, (
            f"{module_name} missing runtime_backend"
        )


def test_memory_bridge_module_has_explicit_contract_metadata():
    text = _read_module_text("memory")
    assert 'const module_format = "smod-runtime"' in text
    assert 'const runtime_backend = "smod-bridge"' in text


def test_all_stdlib_modules_declare_module_format():
    """Every .smod file in stdlib/ must have module_format metadata."""
    stdlib = Path("stdlib")
    for smod_file in sorted(stdlib.glob("*.smod")):
        text = smod_file.read_text(encoding="utf-8")
        assert 'const module_format = "smod-runtime"' in text, (
            f"{smod_file.name} missing module_format declaration"
        )
