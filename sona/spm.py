"""Sona Package Manager (SPM).

SPM is intentionally offline-first and local-only in Sona 0.15.x. Hardened
project and dependency state operations live in :mod:`sona.spm_core`; this
module preserves the public Python API, catalog generator, and command-line
surface.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from .spm_core import (
    DEFAULT_LOCK_NAME,
    DEFAULT_MANIFEST_NAME,
    DEFAULT_MODULES_DIR,
    DEFAULT_PROJECT_VERSION,
    LOCK_INTEGRITY_ALGORITHM,
    LOCK_SCHEMA_VERSION,
    MANIFEST_SCHEMA_VERSION,
    DependencySpec,
    SpmError,
    _project_root,
    add_dependency,
    init_project,
    install,
    list_deps,
    lock,
    verify_lock,
)

__all__ = [
    "DEFAULT_LOCK_NAME",
    "DEFAULT_MANIFEST_NAME",
    "DEFAULT_MODULES_DIR",
    "DEFAULT_PROJECT_VERSION",
    "LOCK_INTEGRITY_ALGORITHM",
    "LOCK_SCHEMA_VERSION",
    "MANIFEST_SCHEMA_VERSION",
    "DependencySpec",
    "SpmError",
    "add_dependency",
    "build_parser",
    "generate_catalog",
    "init_project",
    "install",
    "list_deps",
    "lock",
    "main",
    "verify_lock",
]


def generate_catalog(
    stdlib_path: Path | None = None,
    output: Path | None = None,
) -> dict[str, Any]:
    """Generate a user-facing module catalog from stdlib ``MANIFEST.json``."""
    if stdlib_path is None:
        stdlib_path = Path(__file__).parent / "stdlib"

    manifest_file = stdlib_path / "MANIFEST.json"
    if not manifest_file.exists():
        raise SpmError("Standard-library MANIFEST.json is unavailable.", "SPM-CATALOG-001")
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SpmError(
            "Standard-library MANIFEST.json could not be read safely.",
            "SPM-CATALOG-002",
        ) from error

    categories = manifest.get("categories", {})
    try:
        from .stdlib_manifest import manifest_entries as canonical_entries

        modules_list = canonical_entries()
        canonical = True
    except Exception:
        modules_list = manifest.get("modules", [])
        canonical = False

    catalog_entries: list[dict[str, Any]] = []
    for module_entry in modules_list:
        if canonical and isinstance(module_entry, dict):
            module_name = module_entry["name"]
            source = module_entry.get("source", "legacy")
            status = module_entry.get("stability", "experimental")
            user_facing = module_entry.get("user_facing") is not False
        elif isinstance(module_entry, str):
            module_name = module_entry
            source = "legacy"
            status = "stable"
            user_facing = True
        elif isinstance(module_entry, dict) and isinstance(
            module_entry.get("name"),
            str,
        ):
            module_name = module_entry["name"]
            source = module_entry.get("source", "legacy")
            status = module_entry.get("stability", "preview")
            user_facing = module_entry.get("user_facing") is not False
        else:
            continue

        if (
            not user_facing
            or module_name.startswith("native_")
            or module_name
            in {"intrinsics", "native_intrinsics", "native_bridge"}
        ):
            continue

        entry: dict[str, Any] = {
            "name": module_name,
            "type": "stdlib",
            "status": status,
            "source": source,
        }
        if isinstance(module_entry, dict) and module_entry.get("category"):
            entry["category"] = module_entry["category"]

        if "category" not in entry and isinstance(categories, dict):
            for category_name, category_modules in categories.items():
                if (
                    isinstance(category_modules, list)
                    and (
                        module_name in category_modules
                        or module_name.split(".")[0] in category_modules
                    )
                ):
                    entry["category"] = category_name
                    break

        relative_module = module_name.replace(".", "/")
        smod_file = (
            Path(__file__).resolve().parents[1]
            / "stdlib"
            / f"{relative_module}.smod"
        )
        module_file = (
            smod_file
            if smod_file.exists()
            else stdlib_path / f"{relative_module}.py"
        )
        if not module_file.exists():
            module_file = stdlib_path / f"{module_name}.py"
        description = _module_description(module_file)
        if description:
            entry["description"] = description
        catalog_entries.append(entry)

    catalog: dict[str, Any] = {
        "version": manifest.get("version", DEFAULT_PROJECT_VERSION),
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "moduleCount": len(catalog_entries),
        "categories": list(categories.keys()) if isinstance(categories, dict) else [],
        "modules": catalog_entries,
    }
    if output:
        try:
            output.write_text(
                json.dumps(catalog, indent=2, ensure_ascii=True) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        except OSError as error:
            raise SpmError(
                "Catalog output could not be written.",
                "SPM-CATALOG-003",
            ) from error
    return catalog


def _module_description(module_file: Path) -> str:
    if not module_file.exists() or not module_file.is_file():
        return ""
    try:
        content = module_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""
    if module_file.suffix == ".smod":
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped.startswith("#"):
                continue
            comment = stripped.lstrip("#").strip()
            if not comment or comment.endswith(".smod"):
                continue
            if comment.lower().startswith("purpose:"):
                comment = comment.split(":", 1)[1].strip()
            return comment
        return ""
    if content.startswith('"""'):
        end = content.find('"""', 3)
        if end > 3:
            return content[3:end].strip().split("\n")[0]
    return ""


def _cmd_init(args: argparse.Namespace) -> int:
    root = _project_root(args.root)
    path = init_project(root, name=args.name, version=args.version)
    print(f"Initialized {path}")
    return 0


def _cmd_add(args: argparse.Namespace) -> int:
    root = _project_root(args.root)
    development = bool(getattr(args, "dev", False))
    add_dependency(root, args.name, args.path, dev=development)
    dependency_type = "dev dependency" if development else "dependency"
    print(f"Added {dependency_type} '{args.name}' -> {args.path}")
    return 0


def _cmd_install(args: argparse.Namespace) -> int:
    root = _project_root(args.root)
    result = install(root, include_dev=bool(getattr(args, "dev", False)))
    for name in result["installed"]:
        print(f"Installed: {name}")
    print(f"Modules dir: {result['modulesDir']}")
    print(
        f"Lock: schema-{result['lockSchema']} "
        f"({result['integrityAlgorithm']})"
    )
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    root = _project_root(args.root)
    dependencies = list_deps(root)
    if not dependencies:
        print("No dependencies")
        return 0
    for dependency in dependencies:
        print(f"{dependency.name} -> {dependency.path}")
    return 0


def _cmd_lock(args: argparse.Namespace) -> int:
    root = _project_root(args.root)
    result = lock(root)
    print(
        f"Locked {len(result['packages'])} package(s) to {DEFAULT_LOCK_NAME} "
        f"with {result['integrityAlgorithm']}"
    )
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    root = _project_root(args.root)
    result = verify_lock(root)
    mismatched = result["mismatched"]
    missing = result["missing"]
    manifest_mismatched = result["manifestMismatched"]
    print(f"Verified: {len(result['ok'])} OK")
    print(
        f"Lock: schema-{result['schema']} "
        f"({result['integrityAlgorithm']})"
    )

    if missing:
        print(f"Missing ({len(missing)}):")
        for name in missing:
            print(f"  - {name}")
    if mismatched:
        print(f"Integrity mismatch ({len(mismatched)}):")
        for item in mismatched:
            print(
                f"  - {item['name']}: expected {item['expected'][:16]}..., "
                f"got {item['actual'][:16]}..."
            )
    if manifest_mismatched:
        print(f"Manifest mismatch ({len(manifest_mismatched)}):")
        for name in manifest_mismatched:
            print(f"  - {name}")
    if missing or mismatched or manifest_mismatched:
        return 1
    print("All packages verified.")
    return 0


def _cmd_catalog(args: argparse.Namespace) -> int:
    output = Path(args.output) if args.output else None
    catalog = generate_catalog(output=output)
    if output:
        print(f"Catalog written to {output}")
        return 0

    print(f"Sona stdlib v{catalog['version']}")
    print(f"Total modules: {catalog['moduleCount']}")
    print(f"Categories: {', '.join(catalog['categories'])}")
    if args.verbose:
        print("\nModules:")
        for module in catalog["modules"]:
            category = module.get("category", "uncategorized")
            description = module.get("description", "")
            suffix = f": {description}" if description else ""
            print(f"  [{category}] {module['name']}{suffix}")
    return 0


def build_parser(prog: str = "spm") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Sona Package Manager (local paths only)",
    )
    parser.add_argument("--root", help="Project root (defaults to cwd)", default=None)
    subcommands = parser.add_subparsers(dest="command")

    init_parser = subcommands.add_parser("init", help="Create sona.json manifest")
    init_parser.add_argument("--name", default=None, help="Project name")
    init_parser.add_argument(
        "--version",
        default=DEFAULT_PROJECT_VERSION,
        help="Project version",
    )
    init_parser.set_defaults(func=_cmd_init)

    add_parser = subcommands.add_parser("add", help="Add a local-path dependency")
    add_parser.add_argument("name", help="Dependency name (import name)")
    add_parser.add_argument("path", help="Local path to dependency (file or folder)")
    add_parser.add_argument(
        "--dev",
        "-D",
        action="store_true",
        help="Add as dev dependency",
    )
    add_parser.set_defaults(func=_cmd_add)

    install_parser = subcommands.add_parser(
        "install",
        help="Stage, verify, and atomically install local dependencies",
    )
    install_parser.add_argument(
        "--dev",
        "-D",
        action="store_true",
        help="Also install dev dependencies",
    )
    install_parser.set_defaults(func=_cmd_install)

    list_parser = subcommands.add_parser("list", help="List dependencies")
    list_parser.set_defaults(func=_cmd_list)

    lock_parser = subcommands.add_parser(
        "lock",
        help=f"Generate deterministic {DEFAULT_LOCK_NAME}",
    )
    lock_parser.set_defaults(func=_cmd_lock)

    verify_parser = subcommands.add_parser(
        "verify",
        help="Verify installed packages against the dependency lock",
    )
    verify_parser.set_defaults(func=_cmd_verify)

    catalog_parser = subcommands.add_parser(
        "catalog",
        help="Generate module catalog from stdlib MANIFEST.json",
    )
    catalog_parser.add_argument("--output", "-o", help="Output file path")
    catalog_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show all modules",
    )
    catalog_parser.set_defaults(func=_cmd_catalog)
    return parser


def main(argv: list[str] | None = None, *, prog: str = "spm") -> int:
    parser = build_parser(prog)
    args = parser.parse_args(argv)
    function = getattr(args, "func", None)
    if not callable(function):
        parser.print_help()
        return 2
    try:
        return int(function(args))
    except SpmError as error:
        print(f"spm error: {error}")
        return 1
    except Exception:
        print("spm error: SPM-900: Package command failed safely.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
