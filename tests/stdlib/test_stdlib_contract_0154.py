from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "sona" / "stdlib" / "MANIFEST.json"
CATALOG = ROOT / "docs" / "stdlib" / "catalog.json"


FOUNDATION = {
    "collection": {"first", "last", "take", "drop", "flatten", "unique", "frequencies", "push", "pop"},
    "date": {"today", "from_timestamp", "parse", "format"},
    "fs": {"read_text", "write_text", "append_text", "exists", "is_file", "is_dir", "list_dir", "create_dir", "remove", "rename", "copy"},
    "http": {"get", "post", "put", "patch", "delete"},
    "io": {"write_stdout", "write_stderr", "flush"},
    "json": {"parse", "stringify"},
    "math": {"abs", "minimum", "maximum", "round", "sqrt", "pow"},
    "random": {"float", "integer", "choice", "shuffle", "seed"},
    "stdin": {"read"},
    "string": {"length", "upper", "lower", "trim", "split", "join", "replace", "contains", "starts_with", "ends_with"},
    "time": {"now", "monotonic", "sleep"},
}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_schema_two_manifest_is_complete_and_bounded():
    payload = _manifest()
    modules = payload["modules"]
    names = [item["name"] for item in modules]

    assert payload["schema"] == 2
    assert payload["schema_id"] == "sona.stdlib.manifest.schema-2"
    assert payload["stdlib_cap"] == len(modules) == 146
    assert len(names) == len(set(names))
    assert set(payload["foundation_modules"]) == set(FOUNDATION)
    assert set(payload["support_values"]) == {"PASS", "PARTIAL", "UNSUPPORTED", "EXPERIMENTAL"}
    assert set(payload["disposition_values"]) == {"KEEP", "RENAME", "MOVE", "DEPRECATE", "REMOVE", "PRIVATE"}


def test_foundation_contracts_and_export_inventory_match():
    payload = _manifest()
    modules = {item["name"]: item for item in payload["modules"]}

    for name, required_exports in FOUNDATION.items():
        contract = payload["foundation_contracts"][name]
        inventoried = {item["name"] for item in modules[name]["exports"]}
        assert required_exports <= set(contract["exports"])
        assert required_exports <= inventoried
        assert set(contract) >= {"exports", "python", "native", "standalone"}

    assert payload["foundation_contracts"]["http"]["native"] == "UNSUPPORTED"
    assert payload["foundation_contracts"]["http"]["standalone"] == "UNSUPPORTED"


def test_compatibility_aliases_have_explicit_replacements():
    payload = _manifest()
    modules = {item["name"]: item for item in payload["modules"]}
    expected = {
        ("fs", "read"): "fs.read_text",
        ("fs", "write"): "fs.write_text",
        ("fs", "append"): "fs.append_text",
        ("fs", "mkdir"): "fs.create_dir",
        ("json", "loads"): "json.parse",
        ("json", "dumps"): "json.stringify",
        ("random", "random"): "random.float",
        ("random", "randint"): "random.integer",
        ("string", "startswith"): "string.starts_with",
        ("string", "endswith"): "string.ends_with",
    }
    for (module_name, export_name), replacement in expected.items():
        exports = {item["name"]: item for item in modules[module_name]["exports"]}
        assert exports[export_name]["disposition"] == "RENAME"
        assert exports[export_name]["replacement"] == replacement


def test_catalog_is_exact_deterministic_manifest_projection():
    manifest = _manifest()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert catalog["schema_id"] == "sona.stdlib.catalog.schema-1"
    assert catalog["generated_from"] == "sona/stdlib/MANIFEST.json"
    assert catalog["moduleCount"] == manifest["stdlib_cap"]
    assert [item["name"] for item in catalog["modules"]] == [
        item["name"] for item in manifest["modules"]
    ]

    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "stdlib_contract.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == "stdlib contract ok: 146 modules\n"
    assert result.stderr == ""
