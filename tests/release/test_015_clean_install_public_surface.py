import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from _surface_015 import ROOT  # noqa: E402


def test_release_hardening_script_validates_clean_install_public_surface():
    script = (ROOT / "scripts" / "release_hardening.ps1").read_text(encoding="utf-8")

    required_fragments = [
        "sona-release-hardening-$ExpectedVersion",
        "Clean-install smoke root must be outside the repository",
        "python\" @(\"-m\", \"build\", \"--wheel\", \"--sdist\"",
        "pip\", \"install\", \"--disable-pip-version-check\"",
        "sona\", \"--version\"",
        "sona\", \"probe\", \"stdlib\"",
        "sona\", \"build-info\"",
        "sona.__file__",
        "stable_modules = [",
        "\"profile\", \"simplify\", \"breadcrumb\", \"flow\"",
        "\"boundary\", \"routine\", \"strict\", \"certainty\", \"sensory\", \"guardian\"",
        "for hidden in [\"native_bridge\", \"native_intrinsics\", \"intrinsics\"]",
        "guardian-fixture",
        "sona\", \"guard\", \"init\"",
        "sona\", \"guard\", \"verify\"",
    ]

    for fragment in required_fragments:
        assert fragment in script


def test_release_hardening_script_reports_artifact_hashes():
    script = (ROOT / "scripts" / "release_hardening.ps1").read_text(encoding="utf-8")

    assert "Get-FileHash -Algorithm SHA256" in script
    assert "Wheel:" in script
    assert "Sdist:" in script
    assert "SHA-256" in script
