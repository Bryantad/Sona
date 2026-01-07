"""Stdlib inspection helpers for the Sona CLI."""

from __future__ import annotations

import importlib
import json
from pathlib import Path


STDLIB_ROOT = Path(__file__).resolve().parents[1] / "sona" / "stdlib"


def _iter_stdlib_modules():
    modules: list[str] = []
    native_modules: list[str] = []
    nested_modules: list[str] = []

    if not STDLIB_ROOT.exists():
        return modules, native_modules, nested_modules

    for path in STDLIB_ROOT.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(STDLIB_ROOT)
        if rel.parts and rel.parts[0] == "__pycache__":
            continue
        module_name = ".".join(rel.with_suffix("").parts)
        if module_name.startswith("native_"):
            native_modules.append(module_name.replace("native_", "", 1))
        elif rel.parts and rel.parts[0] == "collection":
            nested_modules.append(module_name)
        else:
            modules.append(module_name)

    return sorted(modules), sorted(native_modules), sorted(nested_modules)


def _user_module_list(modules, native_modules, nested_modules):
    return sorted(set(modules) | set(native_modules) | set(nested_modules))


def _import_targets(modules, native_modules, nested_modules):
    targets = []
    targets.extend(f"sona.stdlib.{name}" for name in modules)
    targets.extend(f"sona.stdlib.native_{name}" for name in native_modules)
    targets.extend(f"sona.stdlib.{name}" for name in nested_modules)
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

    payload = {
        "status": "ok" if not errors else "error",
        "stdlib_root": str(STDLIB_ROOT),
        "counts": {
            "modules": len(modules),
            "native_modules": len(native_modules),
            "nested_modules": len(nested_modules),
            "user_modules": len(user_modules),
            "import_targets": len(targets),
        },
        "errors": errors,
    }
    print(json.dumps(payload, indent=2))
    return 0 if not errors else 1


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
    return {
        "root": str(STDLIB_ROOT),
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
    }
