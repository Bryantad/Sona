from collections import Counter
from pathlib import Path

from sona.stdlib_manifest import manifest_entries, smod_path_for


ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "docs" / "release" / "0.15.0-module-matrix.md"

STABLE_ACCESSIBILITY = {
    "profile",
    "simplify",
    "breadcrumb",
    "flow",
    "explain",
    "pace",
    "affirm",
    "chunk",
    "timer",
    "noise",
    "tone",
    "readability",
    "linewidth",
    "mirror",
    "chunk_read",
    "contract",
    "boundary",
    "routine",
    "strict",
    "certainty",
    "sensory",
}

EXPERIMENTAL_ACCESSIBILITY = {
    "interrupt",
    "hyperfocus",
    "priority",
    "drift",
    "scaffold",
    "reentry",
    "reward",
    "context",
    "momentum",
    "rotate",
    "start",
    "alias",
    "phonetic",
    "visual",
    "symbol",
    "sequence",
    "memory",
    "contrast",
    "template",
    "spoken",
    "pattern",
    "trace",
    "transition",
    "detail",
    "anchor",
    "overload",
    "mono",
    "system",
    "mastery",
    "shutdown",
    "energy",
    "narrative",
    "journal",
    "adapt",
}

UTILITY_SURFACES = {
    "path",
    "format",
    "color",
    "assert",
    "uuid",
    "url",
    "csv",
    "pipe",
    "intent",
    "focus",
    "log",
}


def entries_by_name():
    return {entry["name"]: entry for entry in manifest_entries()}


def test_cognitive_accessibility_inventory_counts_and_metadata():
    entries = entries_by_name()
    accessibility = {
        name: entry
        for name, entry in entries.items()
        if entry.get("category") == "accessibility"
    }

    assert set(accessibility) == STABLE_ACCESSIBILITY | EXPERIMENTAL_ACCESSIBILITY
    assert len(accessibility) == 55
    assert {name for name, entry in accessibility.items() if entry["stability_group"] == "stable"} == STABLE_ACCESSIBILITY
    assert {name for name, entry in accessibility.items() if entry["stability_group"] == "experimental"} == EXPERIMENTAL_ACCESSIBILITY

    for name, entry in accessibility.items():
        assert entry["source"] == "intrinsic"
        assert entry["requires_native"] is True
        assert entry["local_only"] is True
        assert entry["public_smod"] is True
        assert smod_path_for(name).exists()
        assert entry.get("description")


def test_utility_surfaces_and_guardian_exist():
    entries = entries_by_name()
    assert UTILITY_SURFACES <= set(entries)
    assert (ROOT / "stdlib" / "guardian.smod").exists()
    assert entries["guardian"]["category"] == "resilience"
    assert entries["guardian"]["stability_group"] == "stable"


def test_no_duplicate_public_module_names_and_all_have_metadata():
    names = [entry["name"] for entry in manifest_entries()]
    duplicates = [name for name, count in Counter(names).items() if count > 1]
    assert duplicates == []

    for entry in manifest_entries():
        assert entry.get("name")
        assert entry.get("source")
        assert entry.get("stability")
        assert entry.get("stability_group")
        assert entry.get("category")


def test_cognitive_modules_have_behavior_tests_and_documentation():
    stable_tests = (ROOT / "tests" / "accessibility" / "test_stable_accessibility_modules_015.py").read_text(encoding="utf-8")
    experimental_tests = (ROOT / "tests" / "accessibility" / "test_experimental_accessibility_modules_015.py").read_text(encoding="utf-8")
    guardian_tests = (ROOT / "tests" / "guardian" / "test_guardian_mvp_015.py").read_text(encoding="utf-8")
    matrix = MATRIX.read_text(encoding="utf-8")

    for name in STABLE_ACCESSIBILITY:
        assert f'"{name}"' in stable_tests or f"load(\"{name}\")" in stable_tests
        assert f"| {name} |" in matrix

    for name in EXPERIMENTAL_ACCESSIBILITY:
        assert f'"{name}"' in experimental_tests
        assert f"| {name} |" in matrix

    assert "guardian" in guardian_tests
    assert "| guardian |" in matrix
