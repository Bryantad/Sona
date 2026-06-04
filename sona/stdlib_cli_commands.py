"""Stdlib inspection helpers for the Sona CLI."""

from __future__ import annotations

import importlib
import json
from pathlib import Path


STDLIB_ROOT = Path(__file__).resolve().parents[1] / "sona" / "stdlib"
SMOD_ROOT = Path(__file__).resolve().parents[1] / "stdlib"
MANIFEST_PATH = STDLIB_ROOT / "MANIFEST.json"
PRIVATE_MODULES = {"intrinsics", "native_intrinsics", "native_bridge"}


def _manifest_entries() -> list[dict]:
    if not MANIFEST_PATH.exists():
        return []
    try:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    entries = []
    for item in payload.get("modules", []):
        if isinstance(item, str):
            entries.append({"name": item, "source": "legacy", "stability": "stable"})
        elif isinstance(item, dict) and isinstance(item.get("name"), str):
            entry = dict(item)
            entry.setdefault("source", "legacy")
            entry.setdefault("stability", "preview")
            entries.append(entry)
    return entries


def _is_private_module(name: str) -> bool:
    return name in PRIVATE_MODULES or name.startswith("native_")


def _iter_stdlib_modules():
    modules: list[str] = []
    native_modules: list[str] = []
    nested_modules: list[str] = []

    entries = _manifest_entries()
    if entries:
        for entry in entries:
            name = entry["name"]
            if entry.get("user_facing") is False or _is_private_module(name):
                continue
            if "." in name:
                nested_modules.append(name)
            else:
                modules.append(name)

        if STDLIB_ROOT.exists():
            for path in STDLIB_ROOT.glob("native_*.py"):
                module_name = path.with_suffix("").name
                public_name = module_name.replace("native_", "", 1)
                if module_name in PRIVATE_MODULES or public_name in PRIVATE_MODULES:
                    continue
                native_modules.append(public_name)
        return sorted(set(modules)), sorted(set(native_modules)), sorted(set(nested_modules))

    if not STDLIB_ROOT.exists():
        return modules, native_modules, nested_modules

    for path in STDLIB_ROOT.rglob("*.py"):
        if path.name == "__init__.py" or path.stem in PRIVATE_MODULES:
            continue
        rel = path.relative_to(STDLIB_ROOT)
        if rel.parts and rel.parts[0] == "__pycache__":
            continue
        module_name = ".".join(rel.with_suffix("").parts)
        if _is_private_module(module_name):
            continue
        if module_name.startswith("native_"):
            native_modules.append(module_name.replace("native_", "", 1))
        elif rel.parts and rel.parts[0] == "collection":
            nested_modules.append(module_name)
        else:
            modules.append(module_name)

    return sorted(modules), sorted(native_modules), sorted(nested_modules)


def _user_module_list(modules, native_modules, nested_modules):
    return sorted(set(modules) | set(nested_modules))


def _import_targets(modules, native_modules, nested_modules):
    targets = []
    entry_map = {entry["name"]: entry for entry in _manifest_entries()}
    for name in modules + nested_modules:
        entry = entry_map.get(name, {})
        if entry.get("source") in {"sona", "sona+intrinsic"}:
            continue
        targets.append(f"sona.stdlib.{name}")
    targets.extend(
        f"sona.stdlib.native_{name}"
        for name in native_modules
        if name not in {"bridge", "intrinsics"}
    )
    return targets


def stdlib_probe() -> int:
    modules, native_modules, nested_modules = _iter_stdlib_modules()
    targets = _import_targets(modules, native_modules, nested_modules)
    user_modules = _user_module_list(modules, native_modules, nested_modules)

    errors: dict[str, str] = {}
    for target in targets:
        try:
            importlib.import_module(target)
        except Exception as exc:
            errors[target] = str(exc)

    smod_errors: dict[str, str] = {}
    try:
        from sona.interpreter import SonaUnifiedInterpreter

        interpreter = SonaUnifiedInterpreter()
        for entry in _manifest_entries():
            name = entry["name"]
            if entry.get("source") not in {"sona", "sona+intrinsic"}:
                continue
            if entry.get("user_facing") is False or _is_private_module(name):
                continue
            try:
                interpreter.module_system.import_module(name)
            except Exception as exc:
                smod_errors[name] = str(exc)
    except Exception as exc:
        smod_errors["<interpreter>"] = str(exc)

    payload = {
        "status": "ok" if not errors and not smod_errors else "error",
        "stdlib_root": str(STDLIB_ROOT),
        "smod_root": str(SMOD_ROOT),
        "counts": {
            "modules": len(modules),
            "native_modules": len(native_modules),
            "nested_modules": len(nested_modules),
            "user_modules": len(user_modules),
            "import_targets": len(targets),
        },
        "errors": errors,
        "smod_errors": smod_errors,
    }
    print(json.dumps(payload, indent=2))
    return 0 if not errors and not smod_errors else 1


def stdlib_doctor_check() -> None:
    modules, native_modules, nested_modules = _iter_stdlib_modules()
    targets = _import_targets(modules, native_modules, nested_modules)
    user_modules = _user_module_list(modules, native_modules, nested_modules)

    errors = []
    for target in targets:
        try:
            importlib.import_module(target)
        except Exception as exc:
            errors.append((target, str(exc)))

    print("  [OK]   Stdlib root:", STDLIB_ROOT)
    print(
        "  [OK]   Modules: {mods} (native {native}, nested {nested}, user {user})".format(
            mods=len(modules),
            native=len(native_modules),
            nested=len(nested_modules),
            user=len(user_modules),
        )
    )
    if errors:
        print(f"  [WARN] Stdlib imports: {len(errors)} failures")
        for target, msg in errors[:5]:
            print(f"         - {target}: {msg}")
        if len(errors) > 5:
            print(f"         ... {len(errors) - 5} more")
    else:
        print("  [OK]   Stdlib imports: all targets loaded")


def stdlib_build_info() -> dict:
    modules, native_modules, nested_modules = _iter_stdlib_modules()
    user_modules = _user_module_list(modules, native_modules, nested_modules)
    entries = _manifest_entries()
    return {
        "root": str(STDLIB_ROOT),
        "smod_root": str(SMOD_ROOT),
        "counts": {
            "modules": len(modules),
            "native_modules": len(native_modules),
            "nested_modules": len(nested_modules),
            "user_modules": len(user_modules),
        },
        "modules": modules,
        "native_modules": native_modules,
        "nested_modules": nested_modules,
        "user_modules": user_modules,
        "manifest_modules": entries,
    }
