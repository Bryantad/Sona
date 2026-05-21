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
        timeout=180,
    )


def test_run_command_executes_hello_example():
    result = _run(["run", "examples/hello.sona"])

    assert result.returncode == 0
    assert "Hello from Sona 0.14.0!" in result.stdout


def test_direct_file_executes_hello_example():
    result = _run(["examples/hello.sona"])

    assert result.returncode == 0
    assert "Hello from Sona 0.14.0!" in result.stdout


def test_missing_file_reports_user_error_on_stderr():
    result = _run(["run", "examples/does_not_exist.sona"])

    assert result.returncode == 1
    assert "SonaFileError: file not found: examples/does_not_exist.sona" in result.stderr
    assert "hint:" in result.stderr


def test_direct_missing_file_reports_user_error_on_stderr():
    result = _run(["does_not_exist.sona"])

    assert result.returncode == 1
    assert "SonaFileError: file not found: does_not_exist.sona" in result.stderr
    assert "hint:" in result.stderr
