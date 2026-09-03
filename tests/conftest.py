from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def native_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build the real locked Native CLI once for cross-implementation gates."""

    cargo = shutil.which("cargo")
    assert cargo is not None, "cargo is mandatory for the active native gates"
    target = tmp_path_factory.mktemp("native-target")
    environment = os.environ.copy()
    environment["CARGO_TARGET_DIR"] = str(target)
    environment["SONA_SOURCE_COMMIT"] = "1" * 40
    process = subprocess.run(
        [
            cargo,
            "build",
            "--manifest-path",
            str(ROOT / "native" / "Cargo.toml"),
            "--release",
            "--locked",
            "-p",
            "sona-cli",
        ],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        shell=False,
        timeout=180,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    binary = target / "release" / ("sona.exe" if os.name == "nt" else "sona")
    assert binary.is_file()
    return binary
