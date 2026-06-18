from collections import Counter
import sys
from pathlib import Path

from sona.stdlib_manifest import manifest_entries, user_module_names

sys.path.append(str(Path(__file__).resolve().parent))

from _surface_015 import (  # noqa: E402
    EXPERIMENTAL_ACCESSIBILITY,
    PUBLIC_015_SURFACES,
    PUBLIC_DOCS,
    RESILIENCE,
    STABLE_ACCESSIBILITY,
    STABLE_UTILITY,
)


def entries_by_name():
    return {entry["name"]: entry for entry in manifest_entries()}


def test_015_manifest_has_no_duplicate_public_names():
    names = [entry["name"] for entry in manifest_entries()]
    duplicates = [name for name, count in Counter(names).items() if count > 1]
    assert duplicates == []


def test_015_manifest_stability_and_category_labels_are_accurate():
    entries = entries_by_name()

    for name in STABLE_UTILITY:
        assert entries[name]["stability_group"] == "stable"
        assert entries[name]["category"] in {"utility", "developer-experience", "testing"}

    for name in STABLE_ACCESSIBILITY:
        assert entries[name]["stability_group"] == "stable"
        assert entries[name]["category"] == "accessibility"

    for name in EXPERIMENTAL_ACCESSIBILITY:
        assert entries[name]["stability_group"] == "experimental"
        assert entries[name]["stability"] == "experimental"
        assert entries[name]["category"] == "accessibility"

    guardian = entries["guardian"]
    assert guardian["category"] == "resilience"
    assert guardian["stability_group"] == "stable"
    assert guardian["side_effects"] == ["explicit-project-state"]


def test_015_public_user_catalog_includes_release_surfaces_and_hides_internals():
    public_names = set(user_module_names())

    assert PUBLIC_015_SURFACES <= public_names
    for hidden in {"native_bridge", "native_intrinsics", "intrinsics"}:
        assert hidden not in public_names
    assert not any(name.startswith("native_") for name in public_names)


def test_015_documentation_covers_public_surfaces():
    stdlib = PUBLIC_DOCS["utility"].read_text(encoding="utf-8")
    accessibility = PUBLIC_DOCS["accessibility"].read_text(encoding="utf-8")
    guardian = PUBLIC_DOCS["resilience"].read_text(encoding="utf-8")

    for name in STABLE_UTILITY:
        assert f"`{name}`" in stdlib or f"## {name}" in stdlib
    for name in STABLE_ACCESSIBILITY | EXPERIMENTAL_ACCESSIBILITY:
        assert f"`{name}`" in accessibility or f"## {name}" in accessibility
    for name in RESILIENCE:
        assert f"`{name}`" in guardian or f"## {name}" in guardian
