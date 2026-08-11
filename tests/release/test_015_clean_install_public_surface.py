import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from _surface_015 import ROOT  # noqa: E402


def test_release_hardening_script_delegates_to_external_orchestrator():
    script = (ROOT / "scripts" / "release_hardening.ps1").read_text(encoding="utf-8")

    required_fragments = [
        '[string]$ExpectedVersion = "0.15.4"',
        "$env:SONA_CERT_ROOT",
        "tools/release/certify_0153.py",
        "python,native,gates,extension,packaging",
        "native,gates,extension,packaging",
    ]

    for fragment in required_fragments:
        assert fragment in script


def test_release_hardening_script_never_builds_inside_repository():
    script = (ROOT / "scripts" / "release_hardening.ps1").read_text(encoding="utf-8")

    assert ".release-artifacts" not in script
    assert "python -m build" not in script
    assert "npm ci" not in script
    assert "cargo build" not in script
