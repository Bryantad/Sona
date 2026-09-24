"""Run the 0.16.0 flagship runtime examples in isolated directories."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"


def _run(relative_script: str, *arguments: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    return subprocess.run(
        [sys.executable, str(EXAMPLES / relative_script), *arguments],
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def test_durable_workflow_example_interrupts_inertly_then_explicitly_recovers(tmp_path):
    journal_root = tmp_path / ".sona"
    interrupted = _run(
        "durable-workflow/run_pipeline.py", "--root", str(journal_root), "--interrupt", cwd=tmp_path
    )
    assert interrupted.returncode == 0, interrupted.stdout + interrupted.stderr
    assert "Interrupted after durable start" in interrupted.stdout

    inert = _run("durable-workflow/run_pipeline.py", "--root", str(journal_root), cwd=tmp_path)
    assert inert.returncode == 2, inert.stdout + inert.stderr
    assert "Recovery is inert" in inert.stdout

    resumed = _run(
        "durable-workflow/run_pipeline.py",
        "--root",
        str(journal_root),
        "--resume-interrupted",
        cwd=tmp_path,
    )
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert "Workflow " in resumed.stdout and "succeeded (3/3 steps)" in resumed.stdout


def test_supervised_service_example_restarts_only_its_failing_service(tmp_path):
    result = _run("supervised-service/run_worker.py", cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "attempts=2; restarts=1" in result.stdout
    assert "Cooperative stop: completed" in result.stdout


def test_typed_event_and_bounded_channel_example_runs_without_services(tmp_path):
    result = _run("events/run_events.py", cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Received sona-demo.zip: success=True" in result.stdout
    assert "data only" in result.stdout


def test_direct_local_model_example_runs_when_gguf_fixture_is_configured(tmp_path):
    model_path = os.getenv("SONA_TEST_GGUF")
    if not model_path:
        pytest.skip("SONA_TEST_GGUF is not configured")
    result = _run("local-ai/run_local.py", model_path, "--device", "cpu", cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Provider: local (local; no fallback)" in result.stdout
