"""Sona Package Manager (spm) — v0.10 baseline.

This is intentionally minimal and offline-first.

- Manifest: sona.json
- Lock file: sona.lock.json
- Install location: .sona_modules/
- Dependency sources: local paths only (file or directory)

The initial goal is to make Sona projects "package-ready" without
introducing registry/security complexity yet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST_NAME = "sona.json"
DEFAULT_LOCK_NAME = "sona.lock.json"
DEFAULT_MODULES_DIR = ".sona_modules"
MANIFEST_SCHEMA_VERSION = 2


class SpmError(RuntimeError):
    pass


@dataclass(frozen=True)
class DependencySpec:
    name: str
    path: str
    version: str = ""
    integrity: str = ""


@dataclass
class LockEntry:
    name: str
    version: str
    path: str
    integrity: str
    installed_at: str = ""


def _project_root(explicit: str | None) -> Path:
    return Path(explicit).resolve() if explicit else Path.cwd().resolve()


def _manifest_path(root: Path) -> Path:
    return root / DEFAULT_MANIFEST_NAME


def _lock_path(root: Path) -> Path:
    return root / DEFAULT_LOCK_NAME


def _load_manifest(root: Path) -> dict[str, Any]:
    path = _manifest_path(root)
    if not path.exists():
        raise SpmError(f"No {DEFAULT_MANIFEST_NAME} found in {root}. Run 'spm init' first.")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SpmError(f"Failed to read {DEFAULT_MANIFEST_NAME}: {exc}") from exc


def _write_manifest(root: Path, manifest: dict[str, Any]) -> None:
    path = _manifest_path(root)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _load_lock(root: Path) -> dict[str, Any]:
    path = _lock_path(root)
    if not path.exists():
        return {"schema": 1, "packages": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"schema": 1, "packages": {}}


def _write_lock(root: Path, lock: dict[str, Any]) -> None:
    path = _lock_path(root)
    path.write_text(json.dumps(lock, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _compute_integrity(src: Path) -> str:
    """Compute sha256 hash of a file or directory (deterministic)."""
    h = hashlib.sha256()
    if src.is_file():
        h.update(src.read_bytes())
    elif src.is_dir():
        for p in sorted(src.rglob("*")):
            if p.is_file():
                rel = p.relative_to(src).as_posix()
                h.update(rel.encode("utf-8"))
                h.update(p.read_bytes())
    return f"sha256-{h.hexdigest()}"


def init_project(root: Path, *, name: str | None = None, version: str = "0.10.1") -> Path:
    path = _manifest_path(root)
    if path.exists():
        return path

    manifest: dict[str, Any] = {
        "name": name or root.name,
        "version": version,
        "description": "",
        "author": "",
        "license": "MIT",
        "keywords": [],
        "repository": "",
        "sona": {
            "minVersion": "0.10.1",
        },
        "dependencies": {},
        "devDependencies": {},
        "spm": {
            "schema": MANIFEST_SCHEMA_VERSION,
            "modulesDir": DEFAULT_MODULES_DIR,
        },
    }
    _write_manifest(root, manifest)
    return path


def add_dependency(root: Path, dep_name: str, dep_path: str, *, dev: bool = False) -> None:
    manifest = _load_manifest(root)
    key = "devDependencies" if dev else "dependencies"
    deps = manifest.setdefault(key, {})
    if not isinstance(deps, dict):
        raise SpmError(f"Manifest '{key}' must be an object")

    src = (root / dep_path).resolve() if not os.path.isabs(dep_path) else Path(dep_path).resolve()
    if not src.exists():
        raise SpmError(f"Dependency path not found: {src}")

    deps[dep_name] = {
        "path": os.path.relpath(src, root),
        "version": "*",
    }
    _write_manifest(root, manifest)


def _iter_dependencies(manifest: dict[str, Any], *, include_dev: bool = False) -> list[DependencySpec]:
    result: list[DependencySpec] = []

    for key in ["dependencies"] + (["devDependencies"] if include_dev else []):
        deps_raw = manifest.get(key, {})
        if not isinstance(deps_raw, dict):
            continue

        for name, payload in deps_raw.items():
            if not isinstance(name, str) or not name:
                continue
            if isinstance(payload, str):
                result.append(DependencySpec(name=name, path=payload))
                continue
            if isinstance(payload, dict) and isinstance(payload.get("path"), str):
                result.append(DependencySpec(
                    name=name,
                    path=payload["path"],
                    version=payload.get("version", "*"),
                    integrity=payload.get("integrity", ""),
                ))
                continue
    return result


def _install_target(root: Path, modules_dir: Path, dep_name: str, src: Path) -> Path:
    # dotted deps become nested directories
    parts = dep_name.split(".")
    if src.is_file() and src.suffix == ".smod":
        return modules_dir.joinpath(*parts).with_suffix(".smod")

    # directory deps or non-.smod file deps become package folder
    return modules_dir.joinpath(*parts)


def install(root: Path, *, include_dev: bool = False) -> dict[str, Any]:
    manifest = _load_manifest(root)
    modules_dir_name = DEFAULT_MODULES_DIR
    spm_cfg = manifest.get("spm")
    if isinstance(spm_cfg, dict) and isinstance(spm_cfg.get("modulesDir"), str):
        modules_dir_name = spm_cfg["modulesDir"]

    modules_dir = (root / modules_dir_name).resolve()
    modules_dir.mkdir(parents=True, exist_ok=True)

    installed: list[str] = []
    errors: dict[str, str] = {}
    lock_entries: dict[str, dict[str, str]] = {}

    for dep in _iter_dependencies(manifest, include_dev=include_dev):
        try:
            src = (root / dep.path).resolve() if not os.path.isabs(dep.path) else Path(dep.path).resolve()
            if not src.exists():
                raise SpmError(f"Missing path: {src}")

            target = _install_target(root, modules_dir, dep.name, src)
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()

            target.parent.mkdir(parents=True, exist_ok=True)

            if src.is_dir():
                shutil.copytree(src, target)
            else:
                # For non-.smod single files: install into folder as __init__.smod if possible
                if src.suffix == ".smod":
                    shutil.copy2(src, target)
                else:
                    target.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, target / src.name)

            integrity = _compute_integrity(src)
            installed.append(dep.name)
            lock_entries[dep.name] = {
                "version": dep.version or "*",
                "path": dep.path,
                "integrity": integrity,
                "installedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        except Exception as exc:
            errors[dep.name] = str(exc)

    # Update lock file
    lock = _load_lock(root)
    lock.setdefault("packages", {}).update(lock_entries)
    lock["lockedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _write_lock(root, lock)

    return {"installed": installed, "errors": errors, "modulesDir": str(modules_dir)}


def list_deps(root: Path) -> list[DependencySpec]:
    manifest = _load_manifest(root)
    return _iter_dependencies(manifest, include_dev=True)


# ---------------------------------------------------------------------------
# Lock file operations
# ---------------------------------------------------------------------------

def lock(root: Path) -> dict[str, Any]:
    """Generate or update sona.lock.json from current manifest + installed modules."""
    manifest = _load_manifest(root)
    modules_dir_name = DEFAULT_MODULES_DIR
    spm_cfg = manifest.get("spm")
    if isinstance(spm_cfg, dict) and isinstance(spm_cfg.get("modulesDir"), str):
        modules_dir_name = spm_cfg["modulesDir"]

    modules_dir = (root / modules_dir_name).resolve()

    lock_entries: dict[str, dict[str, str]] = {}

    for dep in _iter_dependencies(manifest, include_dev=True):
        src = (root / dep.path).resolve() if not os.path.isabs(dep.path) else Path(dep.path).resolve()
        if src.exists():
            integrity = _compute_integrity(src)
        else:
            integrity = ""

        lock_entries[dep.name] = {
            "version": dep.version or "*",
            "path": dep.path,
            "integrity": integrity,
        }

    lock_data: dict[str, Any] = {
        "schema": 1,
        "lockedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "packages": lock_entries,
    }
    _write_lock(root, lock_data)
    return lock_data


def verify_lock(root: Path) -> dict[str, Any]:
    """Verify installed packages match the lock file integrity hashes."""
    lock_data = _load_lock(root)
    packages = lock_data.get("packages", {})

    modules_dir_name = DEFAULT_MODULES_DIR
    manifest = _load_manifest(root)
    spm_cfg = manifest.get("spm")
    if isinstance(spm_cfg, dict) and isinstance(spm_cfg.get("modulesDir"), str):
        modules_dir_name = spm_cfg["modulesDir"]

    modules_dir = (root / modules_dir_name).resolve()

    ok: list[str] = []
    mismatched: list[dict[str, str]] = []
    missing: list[str] = []

    for name, entry in packages.items():
        expected_integrity = entry.get("integrity", "")
        parts = name.split(".")
        # Try .smod file first, then directory
        installed = modules_dir.joinpath(*parts).with_suffix(".smod")
        if not installed.exists():
            installed = modules_dir.joinpath(*parts)

        if not installed.exists():
            missing.append(name)
            continue

        actual_integrity = _compute_integrity(installed)
        if expected_integrity and actual_integrity != expected_integrity:
            mismatched.append({"name": name, "expected": expected_integrity, "actual": actual_integrity})
        else:
            ok.append(name)

    return {"ok": ok, "mismatched": mismatched, "missing": missing}


# ---------------------------------------------------------------------------
# Catalog generator (from stdlib MANIFEST.json)
# ---------------------------------------------------------------------------

def generate_catalog(stdlib_path: Path | None = None, output: Path | None = None) -> dict[str, Any]:
    """Generate a module catalog from stdlib MANIFEST.json."""
    if stdlib_path is None:
        stdlib_path = Path(__file__).parent / "stdlib"

    manifest_file = stdlib_path / "MANIFEST.json"
    if not manifest_file.exists():
        raise SpmError(f"MANIFEST.json not found at {manifest_file}")

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))

    modules_list = manifest.get("modules", [])
    categories = manifest.get("categories", {})

    # Build catalog entries
    catalog_entries: list[dict[str, Any]] = []
    for mod_name in modules_list:
        if mod_name.startswith("native_"):
            continue  # Skip internal native modules

        entry: dict[str, Any] = {
            "name": mod_name,
            "type": "stdlib",
            "status": "stable",
        }

        # Find category
        for cat_name, cat_modules in categories.items():
            if mod_name in cat_modules or mod_name.split(".")[0] in cat_modules:
                entry["category"] = cat_name
                break

        # Check if .py file exists and extract docstring
        mod_file = stdlib_path / f"{mod_name.replace('.', '/')}.py"
        if not mod_file.exists():
            mod_file = stdlib_path / f"{mod_name}.py"

        if mod_file.exists():
            try:
                content = mod_file.read_text(encoding="utf-8")
                # Extract first docstring
                if content.startswith('"""'):
                    end = content.find('"""', 3)
                    if end > 3:
                        docstring = content[3:end].strip().split("\n")[0]
                        entry["description"] = docstring
            except Exception:
                pass

        catalog_entries.append(entry)

    catalog: dict[str, Any] = {
            "version": manifest.get("version", "0.10.1"),
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "moduleCount": len(catalog_entries),
        "categories": list(categories.keys()),
        "modules": catalog_entries,
    }

    if output:
        output.write_text(json.dumps(catalog, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    return catalog


def _cmd_init(args: argparse.Namespace) -> int:
    root = _project_root(args.root)
    path = init_project(root, name=args.name, version=args.version)
    print(f"Initialized {path}")
    return 0


def _cmd_add(args: argparse.Namespace) -> int:
    root = _project_root(args.root)
    dev = getattr(args, "dev", False)
    add_dependency(root, args.name, args.path, dev=dev)
    dep_type = "dev dependency" if dev else "dependency"
    print(f"Added {dep_type} '{args.name}' -> {args.path}")
    return 0


def _cmd_install(args: argparse.Namespace) -> int:
    root = _project_root(args.root)
    include_dev = getattr(args, "dev", False)
    result = install(root, include_dev=include_dev)
    for name in result.get("installed", []):
        print(f"Installed: {name}")
    errors = result.get("errors", {})
    if errors:
        print("Errors:")
        for name, err in errors.items():
            print(f"  - {name}: {err}")
        return 1
    print(f"Modules dir: {result.get('modulesDir')}")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    root = _project_root(args.root)
    deps = list_deps(root)
    if not deps:
        print("No dependencies")
        return 0
    for dep in deps:
        print(f"{dep.name} -> {dep.path}")
    return 0


def _cmd_lock(args: argparse.Namespace) -> int:
    root = _project_root(args.root)
    result = lock(root)
    packages = result.get("packages", {})
    print(f"Locked {len(packages)} package(s) to sona.lock.json")
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    root = _project_root(args.root)
    result = verify_lock(root)
    ok_count = len(result.get("ok", []))
    mismatched = result.get("mismatched", [])
    missing = result.get("missing", [])

    print(f"Verified: {ok_count} OK")

    if missing:
        print(f"Missing ({len(missing)}):")
        for name in missing:
            print(f"  - {name}")

    if mismatched:
        print(f"Integrity mismatch ({len(mismatched)}):")
        for item in mismatched:
            print(f"  - {item['name']}: expected {item['expected'][:16]}..., got {item['actual'][:16]}...")
        return 1

    if missing:
        return 1

    print("All packages verified.")
    return 0


def _cmd_catalog(args: argparse.Namespace) -> int:
    output = Path(args.output) if args.output else None
    catalog = generate_catalog(output=output)

    if output:
        print(f"Catalog written to {output}")
    else:
        # Print summary
        print(f"Sona stdlib v{catalog['version']}")
        print(f"Total modules: {catalog['moduleCount']}")
        print(f"Categories: {', '.join(catalog['categories'])}")

        if args.verbose:
            print("\nModules:")
            for mod in catalog["modules"]:
                cat = mod.get("category", "uncategorized")
                desc = mod.get("description", "")
                if desc:
                    print(f"  [{cat}] {mod['name']}: {desc}")
                else:
                    print(f"  [{cat}] {mod['name']}")
    return 0


def build_parser(prog: str = "spm") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=prog, description="Sona Package Manager (spm)")
    parser.add_argument("--root", help="Project root (defaults to cwd)", default=None)

    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="Create sona.json manifest")
    p_init.add_argument("--name", default=None, help="Project name")
    p_init.add_argument("--version", default="0.10.1", help="Project version")
    p_init.set_defaults(func=_cmd_init)

    p_add = sub.add_parser("add", help="Add a local-path dependency")
    p_add.add_argument("name", help="Dependency name (import name)")
    p_add.add_argument("path", help="Local path to dependency (file or folder)")
    p_add.add_argument("--dev", "-D", action="store_true", help="Add as dev dependency")
    p_add.set_defaults(func=_cmd_add)

    p_install = sub.add_parser("install", help="Install deps into .sona_modules")
    p_install.add_argument("--dev", "-D", action="store_true", help="Also install dev dependencies")
    p_install.set_defaults(func=_cmd_install)

    p_list = sub.add_parser("list", help="List dependencies")
    p_list.set_defaults(func=_cmd_list)

    p_lock = sub.add_parser("lock", help="Generate/update sona.lock.json")
    p_lock.set_defaults(func=_cmd_lock)

    p_verify = sub.add_parser("verify", help="Verify installed packages against lock file")
    p_verify.set_defaults(func=_cmd_verify)

    p_catalog = sub.add_parser("catalog", help="Generate module catalog from stdlib MANIFEST.json")
    p_catalog.add_argument("--output", "-o", help="Output file path (omit for summary)")
    p_catalog.add_argument("--verbose", "-v", action="store_true", help="Show all modules")
    p_catalog.set_defaults(func=_cmd_catalog)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    func = getattr(args, "func", None)
    if not callable(func):
        parser.print_help()
        return 2

    try:
        return int(func(args))
    except SpmError as exc:
        print(f"spm error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
