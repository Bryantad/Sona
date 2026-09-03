from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSURANCE = ROOT / "docs" / "spec" / "proof" / "assurance.md"
CLAIM_SURFACES = [
    ROOT / "README.md",
    ROOT / "RELEASE_NOTES_v0.15.4.md",
    ROOT / "RELEASE_NOTES_v0.15.5.md",
    ROOT / "docs" / "getting-started" / "README.md",
    ROOT / "docs" / "GUARDIAN_REFERENCE.md",
    ROOT / "docs" / "guides" / "guardian.md",
    ROOT / "docs" / "guides" / "proof-and-guardian.md",
    ROOT / "docs" / "guides" / "proof-mode.md",
    ROOT / "docs" / "reference" / "native-proof-mode.md",
    ROOT / "docs" / "release" / "0.15.5-implementation-report.md",
    *sorted((ROOT / "docs" / "spec" / "proof").glob("*.md")),
    *sorted((ROOT / "examples" / "trusted-workflows").rglob("*.md")),
]


def test_assurance_table_states_the_schema_1_boundary():
    text = ASSURANCE.read_text(encoding="utf-8")

    assert "| Integrity | Available" in text
    assert "| Authentication | Not provided" in text
    assert "| Attestation | Not provided" in text
    assert "| Trusted anchor | Not provided" in text
    assert "can recompute its self-hash" in text
    assert "records a successful local audit check" in text


def test_current_claim_surfaces_do_not_use_rejected_positive_claims():
    rejected = [
        "tamper-evident-after-creation",
        "creates a strong local",
        "the immutable receipt",
        "authenticated field",
        "cryptographically authenticated execution",
    ]

    for path in CLAIM_SURFACES:
        text = path.read_text(encoding="utf-8").lower()
        for phrase in rejected:
            assert phrase not in text, f"{path.relative_to(ROOT)}: {phrase}"


def test_local_attestation_is_explicitly_scoped():
    combined = (
        ROOT / "docs" / "guides" / "proof-and-guardian.md"
    ).read_text(encoding="utf-8")
    guardian = (ROOT / "docs" / "guides" / "guardian.md").read_text(
        encoding="utf-8"
    )

    for text in (combined, guardian):
        assert "local audit" in text
        assert "not cryptographic" in text
        assert "remote" in text
        assert "trusted-runtime attestation" in text
