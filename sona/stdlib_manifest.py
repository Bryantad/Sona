"""Canonical static stdlib manifest helpers.

This module is intentionally side-effect light: it reads JSON metadata only and
does not import stdlib modules, execute `.smod` files, or initialize native
bridges. CLI discovery, LSP completions, SPM catalogs, and release inventory
checks should prefer these helpers over ad hoc scans.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parent
STDLIB_ROOT = PACKAGE_ROOT / "stdlib"
SMOD_ROOT = REPO_ROOT / "stdlib"
MANIFEST_PATH = STDLIB_ROOT / "MANIFEST.json"
PRIVATE_MODULES = {"intrinsics", "native_intrinsics", "native_bridge"}

_CATEGORY_ALIASES = {
    "automation": "developer-experience",
    "core": "utility",
    "data_processing": "utility",
    "data_structures": "utility",
    "functional": "utility",
    "io": "utility",
    "utilities": "utility",
}

_STABILITY_ALIASES = {
    "core": "stable",
    "preview": "experimental",
}


def is_private_module(name: str) -> bool:
    return name in PRIVATE_MODULES or name.startswith("native_")


def smod_path_for(name: str) -> Path:
    return SMOD_ROOT.joinpath(*name.split(".")).with_suffix(".smod")


@lru_cache(maxsize=1)
def load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        return {"modules": []}
    try:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"modules": []}
    if not isinstance(payload, dict):
        return {"modules": []}
    payload.setdefault("modules", [])
    return payload


def _category_from_legacy_map(name: str, categories: dict[str, Any]) -> str:
    root_name = name.split(".")[0]
    for category, values in categories.items():
        if not isinstance(values, list):
            continue
        if name in values or root_name in values:
            return _CATEGORY_ALIASES.get(category, category)
    return "utility"


def normalize_stability(value: Any) -> str:
    raw = str(value or "experimental").lower()
    return _STABILITY_ALIASES.get(raw, raw)


def normalize_entry(entry: Any, categories: dict[str, Any] | None = None) -> dict[str, Any] | None:
    categories = categories or {}
    if isinstance(entry, str):
        name = entry
        normalized: dict[str, Any] = {
            "name": name,
            "source": "legacy",
            "stability": "stable" if not name.startswith("native_") else "internal",
        }
    elif isinstance(entry, dict) and isinstance(entry.get("name"), str):
        normalized = dict(entry)
        name = normalized["name"]
        normalized.setdefault("source", "legacy")
        normalized.setdefault("stability", "experimental")
    else:
        return None

    normalized["name"] = str(normalized["name"])
    normalized.setdefault("category", _category_from_legacy_map(normalized["name"], categories))
    normalized.setdefault("profiles", [])
    normalized.setdefault("requires_native", normalized.get("source") in {"intrinsic", "sona+intrinsic", "smod+native"})
    normalized.setdefault("local_only", True)
    normalized.setdefault("side_effects", [])
    normalized.setdefault("description", "")
    normalized["stability_group"] = normalize_stability(normalized.get("stability"))
    normalized["public_smod"] = smod_path_for(normalized["name"]).exists()
    if normalized.get("user_facing") is False or is_private_module(normalized["name"]):
        normalized["user_facing"] = False
        normalized["stability_group"] = "internal"
    else:
        normalized.setdefault("user_facing", True)
    return normalized


def manifest_entries(*, include_private: bool = False) -> list[dict[str, Any]]:
    payload = load_manifest()
    categories = payload.get("categories", {})
    if not isinstance(categories, dict):
        categories = {}
    entries: list[dict[str, Any]] = []
    modules = payload.get("modules", [])
    if not isinstance(modules, list):
        return entries
    for item in modules:
        normalized = normalize_entry(item, categories)
        if not normalized:
            continue
        if not include_private and normalized.get("user_facing") is False:
            continue
        entries.append(normalized)
    return entries


def filter_entries(
    *,
    category: str | None = None,
    stability: str | None = None,
    profile: str | None = None,
    include_private: bool = False,
) -> list[dict[str, Any]]:
    target_category = category.lower() if category else None
    target_stability = normalize_stability(stability) if stability else None
    target_profile = profile.lower() if profile else None
    result = []
    for entry in manifest_entries(include_private=include_private):
        if target_category and entry.get("category") != target_category:
            continue
        if target_stability and entry.get("stability_group") != target_stability:
            continue
        if target_profile:
            profiles = [str(item).lower() for item in entry.get("profiles", [])]
            if target_profile not in profiles and "cross-profile" not in profiles:
                continue
        result.append(entry)
    return result


def user_module_names(entries: list[dict[str, Any]] | None = None) -> list[str]:
    source = entries if entries is not None else manifest_entries()
    return sorted({entry["name"] for entry in source if entry.get("user_facing") is not False})


def static_counts(entries: list[dict[str, Any]] | None = None) -> dict[str, int]:
    source = entries if entries is not None else manifest_entries()
    top_level = [entry for entry in source if "." not in entry["name"]]
    nested = [entry for entry in source if "." in entry["name"]]
    native = [entry for entry in source if entry.get("requires_native")]
    return {
        "modules": len(top_level),
        "native_modules": len(native),
        "nested_modules": len(nested),
        "user_modules": len(user_module_names(source)),
    }


def public_payload(entries: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    source = entries if entries is not None else manifest_entries()
    keys = [
        "name",
        "source",
        "stability",
        "stability_group",
        "category",
        "profiles",
        "requires_native",
        "local_only",
        "side_effects",
        "description",
        "public_smod",
    ]
    return [{key: entry.get(key) for key in keys} for entry in source]
