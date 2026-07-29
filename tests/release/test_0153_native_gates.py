from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def native_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    cargo = shutil.which("cargo")
    assert cargo is not None, "cargo is mandatory for the 0.15.3 native gates"
    target = tmp_path_factory.mktemp("native-target")
    environment = os.environ.copy()
    environment["CARGO_TARGET_DIR"] = str(target)
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
        shell=False,
        timeout=180,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    binary = target / "release" / ("sona.exe" if os.name == "nt" else "sona")
    assert binary.is_file()
    return binary


def test_native_standalone_gate_passes(tmp_path: Path, native_binary: Path):
    process = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tests" / "release" / "run_0153_native_standalone_gate.py"),
            "--native-binary",
            str(native_binary),
            "--output-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        shell=False,
        timeout=120,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    summary = json.loads(
        (tmp_path / "sona-0.15.3-native-standalone.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary["schema_id"] == "sona.native-standalone.schema-1"
    assert summary["python_removed_from_child_path"] is True
    assert summary["result_counters"]["fail"] == 0


def test_differential_conformance_has_exact_accounting(
    tmp_path: Path, native_binary: Path
):
    process = subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "tests"
                / "conformance"
                / "run_0153_differential_conformance.py"
            ),
            "--native-binary",
            str(native_binary),
            "--output-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        shell=False,
        timeout=180,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    summary = json.loads(
        (tmp_path / "sona-0.15.3-differential-conformance.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary["schema_id"] == "sona.differential-conformance.schema-1"
    assert summary["fixtures"] == 20
    assert summary["engine_executions"] == 40
    assert summary["comparisons"] == 20
    assert summary["comparison_pass"] == 20
    assert summary["comparison_fail"] == 0
    assert summary["scope"] == "bounded cross-engine conformance"
