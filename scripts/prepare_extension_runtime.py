#!/usr/bin/env python3
"""
prepare_extension_runtime.py

Build-time staging for the VS Code extension runtime. Copies the Sona core
runtime (stdlib only) from the repo into the extension's transient
runtime/ directory before packaging. Do NOT commit the staged runtime.

Behavior:
 - Reads sona/stdlib/MANIFEST.json for module list
 - Copies `sona/__init__.py` and each MANIFEST module into
   vscode-extension/sona-ai-native-programming/runtime/sona/**
 - Verifies ≥22 modules are present after copy
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
    return modules


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
    print(f"Modules (≥22): {count}")
    # Show a short sample
    preview = "\n".join([f" - {p}" for p in copied[:10]])
    if preview:
        print("Sample:")
        print(preview)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
import json, shutil, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXT_ROOT = REPO_ROOT / 'vscode-extension' / 'sona-ai-native-programming'
RUNTIME = EXT_ROOT / 'runtime'
SRC_SONA = REPO_ROOT / 'sona'
MANIFEST = SRC_SONA / 'stdlib' / 'MANIFEST.json'


def main():
    if not MANIFEST.exists():
        print('ERROR: MANIFEST.json not found at', MANIFEST)
        sys.exit(1)

    with MANIFEST.open('r', encoding='utf-8') as fh:
        data = json.load(fh)
    modules = data.get('modules') or data
    if not isinstance(modules, list):
        print('ERROR: MANIFEST.json invalid format: expected {"modules": [...]} or [...].')
        sys.exit(1)
    if len(modules) < 22:
        print(f'ERROR: too few modules in MANIFEST ({len(modules)} < 22)')
        sys.exit(1)

    # Clean runtime staging dir
    if RUNTIME.exists():
        shutil.rmtree(RUNTIME)
    (RUNTIME / 'sona' / 'stdlib').mkdir(parents=True, exist_ok=True)

    # Copy controller script used by the extension
    # The extension expects runtime/sonactl.py at package-time; recreate a minimal shim
    sonactl = RUNTIME / 'sonactl.py'
    sonactl.write_text(
        'import sys, os, code\n' \
        'print("Sona runtime staged. Import from sona.stdlib.*")\n' \
        'code.interact(banner="Sona runtime staged.")\n',
        encoding='utf-8'
    )

    copied = 0
    # Copy sona core and stdlib packages
    for rel in ['__init__.py', 'stdlib']:
        src = SRC_SONA / rel
        dst = RUNTIME / 'sona' / rel
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        elif src.is_dir():
            shutil.copytree(src, dst)
        copied += 1

    # Verify presence of modules declared in MANIFEST
    def present(mod: str) -> bool:
        return (
            (RUNTIME / 'sona' / 'stdlib' / f'{mod}.py').exists()
            or (RUNTIME / 'sona' / 'stdlib' / mod / '__init__.py').exists()
        )

    missing = [m for m in modules if not present(m)]
    if missing:
        print('ERROR: missing staged stdlib modules:\n - ' + '\n - '.join(missing))
        sys.exit(1)

    print(f'OK: staged {copied} top-level items; {len(modules)} stdlib modules available.')
    print('Staged runtime at:', RUNTIME)


if __name__ == '__main__':
    main()
