import sys
from pathlib import Path

from sona.interpreter import SonaUnifiedInterpreter
from sona.stdlib_manifest import manifest_entries, smod_path_for

sys.path.append(str(Path(__file__).resolve().parent))

from _surface_015 import (  # noqa: E402
    EXPERIMENTAL_ACCESSIBILITY,
    PUBLIC_015_SURFACES,
    RESILIENCE,
    ROOT,
    STABLE_ACCESSIBILITY,
    STABLE_UTILITY,
)


def test_015_public_surface_inventory_is_exact():
    assert len(STABLE_UTILITY) == 11
    assert len(STABLE_ACCESSIBILITY) == 21
    assert len(EXPERIMENTAL_ACCESSIBILITY) == 34
    assert len(RESILIENCE) == 1
    assert len(PUBLIC_015_SURFACES) == 67


def test_015_public_surfaces_have_manifest_and_public_smod():
    entries = {entry["name"]: entry for entry in manifest_entries()}

    assert PUBLIC_015_SURFACES <= set(entries)
    for name in sorted(PUBLIC_015_SURFACES):
        entry = entries[name]
        assert entry["user_facing"] is True
        assert entry["public_smod"] is True
        assert smod_path_for(name).exists()
        assert entry.get("description") or entry["category"] == "utility"


def test_015_public_surfaces_import_from_user_runtime(tmp_path):
    interp = SonaUnifiedInterpreter(project_root=tmp_path)

    imported = {}
    for name in sorted(PUBLIC_015_SURFACES):
        imported[name] = interp.module_system.import_module(name)

    assert set(imported) == PUBLIC_015_SURFACES


def test_015_public_surfaces_have_behavior_test_references():
    behavior_files = {
        "utility": [
            ROOT / "tests" / "stdlib" / "test_utility_modules_015.py",
            ROOT / "tests" / "regression" / "test_stdlib_repairs_015.py",
            ROOT / "tests" / "test_sona_native_stdlib_0141.py",
        ],
        "stable_accessibility": [
            ROOT / "tests" / "accessibility" / "test_stable_accessibility_modules_015.py",
            ROOT / "tests" / "accessibility" / "test_profile_runtime_015.py",
        ],
        "experimental_accessibility": [
            ROOT / "tests" / "accessibility" / "test_experimental_accessibility_modules_015.py",
        ],
        "resilience": [
            ROOT / "tests" / "guardian" / "test_guardian_mvp_015.py",
        ],
    }

    utility_text = "\n".join(path.read_text(encoding="utf-8") for path in behavior_files["utility"])
    stable_text = "\n".join(
        path.read_text(encoding="utf-8") for path in behavior_files["stable_accessibility"]
    )
    experimental_text = "\n".join(
        path.read_text(encoding="utf-8") for path in behavior_files["experimental_accessibility"]
    )
    resilience_text = "\n".join(
        path.read_text(encoding="utf-8") for path in behavior_files["resilience"]
    )

    for name in STABLE_UTILITY:
        assert f'"{name}"' in utility_text or f"load({name!r})" in utility_text
    for name in STABLE_ACCESSIBILITY:
        assert f'"{name}"' in stable_text or f"load({name!r})" in stable_text
    for name in EXPERIMENTAL_ACCESSIBILITY:
        assert f'"{name}"' in experimental_text
    for name in RESILIENCE:
        assert name in resilience_text
