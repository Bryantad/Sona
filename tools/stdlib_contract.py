#!/usr/bin/env python3
"""Build and verify the schema-2 standard-library contract inventory."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "sona" / "stdlib" / "MANIFEST.json"
CATALOG = ROOT / "docs" / "stdlib" / "catalog.json"
SUPPORT = {"PASS", "PARTIAL", "UNSUPPORTED", "EXPERIMENTAL"}
DISPOSITIONS = {"KEEP", "RENAME", "MOVE", "DEPRECATE", "REMOVE", "PRIVATE"}

REPLACEMENTS = {
    ("collection", "shuffle"): ("MOVE", "random.shuffle"),
    ("collection", "sample"): ("MOVE", "random.sample"),
    ("date", "sleep"): ("MOVE", "time.sleep"),
    ("fs", "read"): ("RENAME", "fs.read_text"),
    ("fs", "write"): ("RENAME", "fs.write_text"),
    ("fs", "append"): ("RENAME", "fs.append_text"),
    ("fs", "mkdir"): ("RENAME", "fs.create_dir"),
    ("io", "input"): ("MOVE", "stdin.read"),
    ("json", "loads"): ("RENAME", "json.parse"),
    ("json", "dumps"): ("RENAME", "json.stringify"),
    ("json", "load"): ("MOVE", "json.parse(fs.read_text(path))"),
    ("json", "dump"): ("MOVE", "fs.write_text(path, json.stringify(value))"),
    ("random", "random"): ("RENAME", "random.float"),
    ("random", "randint"): ("RENAME", "random.integer"),
    ("string", "startswith"): ("RENAME", "string.starts_with"),
    ("string", "endswith"): ("RENAME", "string.ends_with"),
}

for _name in (
    "read_file",
    "write_file",
    "read",
    "write",
    "append",
    "exists",
    "isfile",
    "isdir",
    "remove",
    "mkdir",
    "listdir",
    "copy",
    "read_bytes",
    "write_bytes",
    "read_lines",
    "write_lines",
    "move",
    "size",
    "print_to_file",
):
    REPLACEMENTS[("io", _name)] = ("MOVE", f"fs.{_name}")


def _signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    values: list[str] = []
    positional = [*node.args.posonlyargs, *node.args.args]
    first_default = len(positional) - len(node.args.defaults)
    for index, arg in enumerate(positional):
        text = arg.arg
        if index >= first_default:
            default = node.args.defaults[index - first_default]
            try:
                text += f"={ast.unparse(default)}"
            except Exception:
                text += "=..."
        values.append(text)
    if node.args.vararg:
        values.append(f"*{node.args.vararg.arg}")
    values.extend(f"{arg.arg}=..." for arg in node.args.kwonlyargs)
    if node.args.kwarg:
        values.append(f"**{node.args.kwarg.arg}")
    return f"({', '.join(values)})"


def python_exports(name: str) -> list[dict[str, Any]]:
    path = ROOT / "sona" / "stdlib" / Path(*name.split(".")).with_suffix(".py")
    if not path.exists():
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = {
        node.name: _signature(node)
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    declared: list[str] | None = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
            continue
        try:
            value = ast.literal_eval(node.value)
        except Exception:
            value = None
        if isinstance(value, (list, tuple)):
            declared = [str(item) for item in value]
    names = declared if declared is not None else sorted(functions)
    return [{"name": item, "signature": functions.get(item)} for item in names]


def smod_exports(name: str) -> list[dict[str, Any]]:
    path = ROOT / "stdlib" / Path(*name.split(".")).with_suffix(".smod")
    if not path.exists():
        return []
    source = path.read_text(encoding="utf-8-sig")
    records = []
    for match in re.finditer(
        r"(?m)^\s*func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)", source
    ):
        params = " ".join(match.group(2).split())
        records.append({"name": match.group(1), "signature": f"({params})"})
    for match in re.finditer(r"(?m)^\s*const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", source):
        records.append({"name": match.group(1), "signature": None})
    return records


def classify(module: str, record: dict[str, Any]) -> dict[str, Any]:
    name = record["name"]
    if name.startswith("__"):
        disposition, replacement = "PRIVATE", None
    else:
        disposition, replacement = REPLACEMENTS.get((module, name), ("KEEP", None))
    result = dict(record)
    result["disposition"] = disposition
    if replacement:
        result["replacement"] = replacement
    return result


def build_inventory(payload: dict[str, Any]) -> dict[str, Any]:
    contracts = payload.get("foundation_contracts", {})
    for item in payload.get("modules", []):
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            continue
        name = item["name"]
        exports = smod_exports(name) or python_exports(name)
        item["exports"] = [classify(name, record) for record in exports]
        contract = contracts.get(name)
        if contract:
            item["runtime_support"] = {
                key: contract[key] for key in ("python", "native", "standalone")
            }
    return payload


def build_catalog(payload: dict[str, Any]) -> dict[str, Any]:
    modules = []
    for item in payload.get("modules", []):
        if not isinstance(item, dict):
            continue
        modules.append(
            {
                "name": item.get("name"),
                "type": "stdlib",
                "status": item.get("stability", "preview"),
                "source": item.get("source", "legacy"),
                "category": item.get("category", "utility"),
                "description": item.get("description", ""),
            }
        )
    return {
        "schema": 1,
        "schema_id": "sona.stdlib.catalog.schema-1",
        "version": payload.get("version"),
        "generated_from": "sona/stdlib/MANIFEST.json",
        "source_manifest_hash": payload.get("manifest_hash"),
        "moduleCount": len(modules),
        "modules": modules,
    }


def validate(payload: dict[str, Any], catalog: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema") != 2 or payload.get("schema_id") != "sona.stdlib.manifest.schema-2":
        errors.append("manifest must use sona.stdlib.manifest.schema-2")
    modules = payload.get("modules", [])
    names = [item.get("name") for item in modules if isinstance(item, dict)]
    if len(names) != len(set(names)):
        errors.append("manifest contains duplicate module names")
    if payload.get("stdlib_cap") != len(names):
        errors.append("stdlib_cap does not match module count")
    for name in payload.get("foundation_modules", []):
        if name not in names:
            errors.append(f"foundation module is missing: {name}")
        contract = payload.get("foundation_contracts", {}).get(name)
        if not contract or not contract.get("exports"):
            errors.append(f"foundation contract is missing exports: {name}")
            continue
        if {contract.get(key) for key in ("python", "native", "standalone")} - SUPPORT:
            errors.append(f"foundation support value is invalid: {name}")
    for item in modules:
        for export in item.get("exports", []):
            if export.get("disposition") not in DISPOSITIONS:
                errors.append(f"invalid disposition: {item.get('name')}.{export.get('name')}")
    if catalog != build_catalog(payload):
        errors.append("docs/stdlib/catalog.json is not the manifest projection")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="rewrite manifest inventory and catalog")
    args = parser.parse_args()
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    payload = build_inventory(payload)
    catalog = build_catalog(payload)
    if args.write:
        MANIFEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        CATALOG.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    current_catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    errors = validate(payload, current_catalog)
    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"stdlib contract ok: {len(payload['modules'])} modules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
