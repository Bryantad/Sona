#!/usr/bin/env python3
"""
Legacy/manual VS Code runtime staging helper.

This script is not part of the primary 0.14.1 VSIX packaging path. The primary
VSIX continues to use a separately installed Sona Python runtime. Keep this
helper available only for manual legacy staging checks.

Behavior:
 - Reads sona/stdlib/MANIFEST.json for module list
 - Copies `sona/__init__.py` and each MANIFEST module into
   vscode-extension/sona-ai-native-programming/runtime/sona/**
 - Verifies >=22 modules are present after copy
 - Prints a short summary

Usage (PowerShell):
  $env:SONA_DEBUG="1"
  python scripts/generate_stdlib_manifest.py
  python scripts/prepare_extension_runtime.py
"""
import json
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SONA_SRC = REPO_ROOT / "sona"
STDLIB_SRC = SONA_SRC / "stdlib"
MANIFEST_PATH = STDLIB_SRC / "MANIFEST.json"
EXT_ROOT = REPO_ROOT / "vscode-extension" / "sona-ai-native-programming"
RUNTIME_ROOT = EXT_ROOT / "runtime" / "sona"


def load_manifest() -> list[str]:
    if not MANIFEST_PATH.exists():
        print(f"ERROR: MANIFEST not found: {MANIFEST_PATH}")
        sys.exit(2)
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    modules = data.get("modules") if isinstance(data, dict) else data
    if not isinstance(modules, list):
        print("ERROR: MANIFEST.json malformed: expected list or {\"modules\": [...]}\n" \
              f"Got: {type(modules)}")
        sys.exit(2)
    result: list[str] = []
    for entry in modules:
        if isinstance(entry, str):
            result.append(entry)
        elif isinstance(entry, dict) and isinstance(entry.get("name"), str):
            if entry.get("user_facing") is not False:
                result.append(entry["name"])
    return result


def ensure_clean_runtime_dir():
    # Remove previously staged runtime (if any)
    if RUNTIME_ROOT.exists():
        shutil.rmtree(RUNTIME_ROOT)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)


def copy_core(modules: list[str]) -> tuple[int, list[str]]:
    # Always copy `sona/__init__.py`
    (RUNTIME_ROOT / "__init__.py").write_text(
        (SONA_SRC / "__init__.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    copied: list[str] = []
    for mod in modules:
        # support dotted like "stdlib/utils/convert" if present
        rel = mod.replace(".", "/").replace("\\", "/")
        # Normalize to live under sona/stdlib
        if not rel.startswith("stdlib/") and not rel.startswith("stdlib\\"):
            rel = f"stdlib/{rel}"
        src_py = STDLIB_SRC / (rel.split("stdlib/")[-1] + ".py")
        src_pkg = STDLIB_SRC / rel.split("stdlib/")[-1]

        dst_base = RUNTIME_ROOT / "stdlib"
        dst_base.mkdir(parents=True, exist_ok=True)

        if src_py.exists():
            dst_file = dst_base / src_py.name
            shutil.copy2(src_py, dst_file)
            copied.append(str(dst_file.relative_to(RUNTIME_ROOT)))
        elif src_pkg.exists() and src_pkg.is_dir():
            # copy package directory recursively
            dst_dir = dst_base / src_pkg.name
            shutil.copytree(src_pkg, dst_dir)
            copied.append(str(dst_dir.relative_to(RUNTIME_ROOT)) + "/")
        else:
            print(f"WARN: module path not found for '{mod}' -> '{src_py}' or '{src_pkg}'")
    return len(copied), copied


def main() -> int:
    modules = load_manifest()
    ensure_clean_runtime_dir()
    count, copied = copy_core(modules)
    # Verify threshold
    if count < 22:
        print(f"ERROR: Only {count} modules staged (< 22). Aborting.")
        return 3
    print(f"Staged Sona runtime -> {RUNTIME_ROOT}")
    print(f"Modules (>=22): {count}")
    # Show a short sample
    preview = "\n".join([f" - {p}" for p in copied[:10]])
    if preview:
        print("Sample:")
        print(preview)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
