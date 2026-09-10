from __future__ import annotations

import pytest

from tools.validate_release_metadata import release_numeric_suffix


def test_release_numeric_suffix_matches_platform_workflow_convention() -> None:
    assert release_numeric_suffix("0.15.5") == "0155"
    assert release_numeric_suffix("0.15.6") == "0156"


def test_release_numeric_suffix_rejects_unexpected_version_shapes() -> None:
    with pytest.raises(SystemExit, match="unsupported release version format"):
        release_numeric_suffix("0.15")
