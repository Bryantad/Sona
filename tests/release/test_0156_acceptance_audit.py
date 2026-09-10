from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs" / "release" / "0.15.6-acceptance-audit.md"
RELEASE_NOTES = ROOT / "RELEASE_NOTES_v0.15.6.md"
CHECKLIST = ROOT / "docs" / "release" / "0.15.6-finalization-checklist.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_acceptance_audit_keeps_release_candidate_boundary() -> None:
    text = read(AUDIT)

    assert "0.15.6 is a swept release candidate" in text
    assert "complete authoritative artifact set" in text
    assert "matching-host Windows/Linux/macOS certification" in text
    assert "| Final `0.15.6` version sweep | Proved locally |" in text
    assert (
        "| Final wheel, sdist, VSIX, and Native archive rebuild | "
        "Partial |"
    ) in text
    assert (
        "| Linux and macOS matching-host certification | Pending external |"
    ) in text
    assert "| Rust tests | Proved locally |" in text


def test_acceptance_audit_tracks_core_0156_contracts() -> None:
    text = read(AUDIT)

    expected_rows = [
        "| Preserve existing Sona syntax | Proved locally |",
        "| Add deterministic Sona Guide layer under `sona/guide` | Proved locally |",
        (
            "| Keep canonical diagnostics and runtime facts unchanged by "
            "presentation mode | Proved locally |"
        ),
        (
            "| Guided, Balanced, and Expert are density choices, not diagnoses | "
            "Proved locally |"
        ),
        "| Offer quick fixes only for deterministic exact edits | Proved locally |",
        "| Make every edit previewable before application | Proved locally |",
        (
            "| Keep learning state local, bounded, inspectable, and resettable | "
            "Proved locally |"
        ),
        (
            "| Focus Mode preserves complete machine-readable diagnostics | "
            "Proved locally |"
        ),
        (
            "| Proof Mode and Guardian explanations describe checked fields only | "
            "Proved locally |"
        ),
        (
            "| Preserve 0.15.5 commands, project state, and schema-1 compatibility | "
            "Proved locally |"
        ),
        "| Support 0.15.4 receipt compatibility | Proved locally |",
    ]

    for row in expected_rows:
        assert row in text


def test_acceptance_audit_is_linked_from_release_docs() -> None:
    notes = read(RELEASE_NOTES)
    checklist = read(CHECKLIST)

    assert "docs/release/0.15.6-acceptance-audit.md" in notes
    assert "docs/release/0.15.6-acceptance-audit.md" in checklist
