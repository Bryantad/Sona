from __future__ import annotations

import pytest

from tools.validate_release_metadata import release_numeric_suffix


def test_release_numeric_suffix_matches_platform_workflow_convention() -> None:
    assert release_numeric_suffix("0.15.5") == "0155"
    assert release_numeric_suffix("0.15.6") == "0156"
    assert release_numeric_suffix("0.16.0") == "0160"


def test_release_numeric_suffix_rejects_unexpected_version_shapes() -> None:
    with pytest.raises(SystemExit, match="unsupported release version format"):
        release_numeric_suffix("0.15")


def test_0160_platform_release_builder_tracks_matching_candidate_metadata() -> None:
    from tools.release import platform_release_0160 as release

    assert release.VERSION == "0.16.0"
    assert release.WHEEL_NAME == "sona_lang-0.16.0-py3-none-any.whl"
    assert release.VSIX_NAME == "sona-ai-native-programming-0.16.0.vsix"
    assert "sona-native-0.16.0-windows-x86_64.zip" in release.NATIVE_ASSETS
