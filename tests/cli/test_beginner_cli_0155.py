from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _sona(*arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    return subprocess.run(
        [sys.executable, "-m", "sona", *arguments],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def test_top_level_help_shows_run_proof_and_guardian_beginner_paths():
    result = _sona("--help")

    assert result.returncode == 0
    assert "simple programs with optional execution evidence" in result.stdout
    assert "ordinary run (no Proof Mode receipt)" in result.stdout
    assert "sona proof verify hello.sproof" in result.stdout
    assert "sona guardian check --project-root ." in result.stdout


def test_proof_help_explains_capabilities_and_trust_boundary():
    result = _sona("proof", "--help")

    assert result.returncode == 0
    assert "never falls back to Python" in result.stdout
    assert "--allow-fs-read" in result.stdout
    assert "--guardian-root PATH" in result.stdout
    assert "never overwritten" in result.stdout
    assert "does not authenticate" in result.stdout


def test_guardian_help_explains_safe_first_steps():
    result = _sona("guardian", "--help")

    assert result.returncode == 0
    assert "sona guardian init --project-root ." in result.stdout
    assert "check and explain are read-only" in result.stdout
    assert "Read-only readiness check" in result.stdout
    assert "Explain capability decisions" in result.stdout


def test_missing_file_error_is_short_and_actionable():
    result = _sona("run", "missing-beginner-example.sona")

    assert result.returncode == 1
    assert "SonaFileError: file not found" in result.stderr
    assert "check the path and run the command again" in result.stderr
    assert "Traceback" not in result.stdout + result.stderr


def test_sona_new_remains_deferred_without_a_scaffolding_contract():
    plan = (ROOT / "docs" / "plans" / "0.15.5-beginner-cli.md").read_text(
        encoding="utf-8"
    )
    result = _sona("new", "hello")

    assert "Adding `sona new`" in plan
    assert result.returncode == 2
    assert "invalid choice: 'new'" in result.stderr
    assert "use 'sona --help'" in result.stderr
