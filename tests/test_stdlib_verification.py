from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import run_sona
from tools.run_all_tests import TEST_PLAN


@pytest.mark.stdlib
def test_stdlib_verification(capsys):
    for _label, rel_path in TEST_PLAN:
        path = ROOT / rel_path
        assert path.exists(), f"Missing test file: {rel_path}"
        exit_code, _source, error = run_sona.run_sona_file(str(path))
        capsys.readouterr()
        assert exit_code == 0, f"{rel_path} failed: {error}"
