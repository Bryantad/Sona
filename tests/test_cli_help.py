import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "sona", *args],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        timeout=120,
    )


def test_version_is_single_line():
    result = _run(["--version"])

    assert result.returncode == 0
    assert result.stdout == "Sona 0.14.0\n"
    assert result.stderr == ""


def test_help_is_available():
    result = _run(["--help"])

    assert result.returncode == 0
    assert "Sona Cognitive Programming Language v0.14.0" in result.stdout
    assert "Examples:" in result.stdout
    assert "sona hello.sona" in result.stdout
    assert "sona run examples/hello.sona" in result.stdout
    assert "run" in result.stdout
    assert result.stderr == ""


def test_no_args_prints_help_to_stderr_and_exits_nonzero():
    result = _run([])

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Sona Cognitive Programming Language v0.14.0" in result.stderr
    assert "Examples:" in result.stderr


def test_run_without_file_reports_usage_error():
    result = _run(["run"])

    assert result.returncode != 0
    assert result.stdout == ""
    assert "SonaUsageError:" in result.stderr
    assert "hint: use 'sona --help' for available commands." in result.stderr


def test_unknown_flag_reports_usage_error():
    result = _run(["--unknown"])

    assert result.returncode != 0
    assert result.stdout == ""
    assert "SonaUsageError:" in result.stderr
    assert "hint: use 'sona --help' for available commands." in result.stderr
