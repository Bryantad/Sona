"""Stdlib inspection helpers for the Sona CLI."""

from __future__ import annotations

import json

from .stdlib_manifest import (
    MANIFEST_PATH,
    SMOD_ROOT,
    STDLIB_ROOT,
    filter_entries,
    manifest_entries,
    public_payload,
    static_counts,
    user_module_names,
)


def stdlib_probe(category: str | None = None, stability: str | None = None) -> int:
    entries = filter_entries(category=category, stability=stability)
    payload = {
        "status": "ok",
        "mode": "static",
        "stdlib_root": str(STDLIB_ROOT),
        "smod_root": str(SMOD_ROOT),
        "manifest": str(MANIFEST_PATH),
        "filters": {
            "category": category,
            "stability": stability,
        },
        "counts": static_counts(entries),
        "user_modules": user_module_names(entries),
        "modules": public_payload(entries),
        "errors": {},
        "smod_errors": {},
        "note": "Static probe reads manifest metadata only; it does not import modules.",
    }
    print(json.dumps(payload, indent=2))
    return 0


def accessibility_probe(profile: str | None = None) -> int:
    entries = filter_entries(category="accessibility", profile=profile)
    payload = {
        "status": "ok",
        "mode": "static",
        "profile": profile,
        "counts": static_counts(entries),
        "user_modules": user_module_names(entries),
        "modules": public_payload(entries),
        "note": "Accessibility modules are local-only by default.",
    }
    print(json.dumps(payload, indent=2))
    return 0


def guardian_probe() -> int:
    entries = [
        entry
        for entry in manifest_entries()
        if entry["name"] == "guardian" or entry.get("category") == "resilience"
    ]
    payload = {
        "status": "ok",
        "mode": "static",
        "counts": static_counts(entries),
        "user_modules": user_module_names(entries),
        "modules": public_payload(entries),
        "note": "Guardian remains inactive until initialized for an explicit project root.",
    }
    print(json.dumps(payload, indent=2))
    return 0


def stdlib_doctor_check() -> None:
    entries = manifest_entries()
    counts = static_counts(entries)
    print("  [OK]   Stdlib root:", STDLIB_ROOT)
    print(
        "  [OK]   Modules: {mods} (native {native}, nested {nested}, user {user})".format(
            mods=counts["modules"],
            native=counts["native_modules"],
            nested=counts["nested_modules"],
            user=counts["user_modules"],
        )
    )
    print("  [OK]   Stdlib discovery: static manifest metadata")


def stdlib_build_info() -> dict:
    entries = manifest_entries()
    return {
        "root": str(STDLIB_ROOT),
        "smod_root": str(SMOD_ROOT),
        "manifest": str(MANIFEST_PATH),
        "discovery_mode": "static",
        "counts": static_counts(entries),
        "modules": [
            entry["name"]
            for entry in entries
            if "." not in entry["name"]
        ],
        "native_modules": [
            entry["name"]
            for entry in entries
            if entry.get("requires_native")
        ],
        "nested_modules": [
            entry["name"]
            for entry in entries
            if "." in entry["name"]
        ],
        "user_modules": user_module_names(entries),
        "manifest_modules": public_payload(entries),
    }
