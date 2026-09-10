from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from sona.guide import GuideRequest, explain, render_text

ROOT = Path(__file__).resolve().parents[2]


def run_why(directory: Path, *arguments: str):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    environment["SONA_NATIVE_BINARY"] = "missing-native-do-not-launch"
    return subprocess.run(
        [sys.executable, "-m", "sona", "why", *arguments],
        cwd=directory, env=environment, capture_output=True, text=True,
        timeout=10, check=False,
    )


@pytest.mark.parametrize("mode", ["guided", "balanced", "expert"])
def test_cli_text_and_json_match_shared_guide_response(tmp_path, mode):
    response = explain(GuideRequest("SONA-RUNTIME-003", mode=mode))
    text = run_why(tmp_path, "SONA-RUNTIME-003", "--mode", mode)
    assert text.returncode == 0 and text.stderr == ""
    assert text.stdout.strip() == render_text(response)
    output = run_why(tmp_path, "SONA-RUNTIME-003", "--mode", mode, "--json")
    assert output.returncode == 0 and output.stderr == ""
    assert json.loads(output.stdout) == response.to_dict()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("style", ["simple", "visual", "technical"])
def test_cli_style_uses_catalog_without_execution(tmp_path, style):
    result = run_why(tmp_path, "SONA-FS-005", "--style", style, "--json")
    assert result.returncode == 0 and result.stderr == ""
    assert json.loads(result.stdout) == explain(GuideRequest("SONA-FS-005", style=style)).to_dict()
    assert list(tmp_path.iterdir()) == []


def test_unknown_id_has_nonzero_exit_and_structured_guide_diagnostic(tmp_path):
    result = run_why(tmp_path, "SONA-NAME-001", "--json")
    assert result.returncode == 1 and result.stderr == ""
    result_json = json.loads(result.stdout)
    assert result_json["status"] == "unavailable"
    assert result_json["diagnostic"]["diagnostic_id"] == "SONA-GUIDE-001"
    assert "Traceback" not in result.stdout


def test_help_explains_offline_command_and_invalid_mode_is_usage_failure(tmp_path):
    result = run_why(tmp_path, "--help")
    assert result.returncode == 0
    assert "--mode" in result.stdout and "--json" in result.stdout
    invalid = run_why(tmp_path, "SONA-FS-005", "--mode", "adhd")
    assert invalid.returncode == 2 and "invalid choice" in invalid.stderr


def test_why_has_no_parser_interpreter_or_ai_provider_dependency(tmp_path):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    script = """import builtins, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.startswith(('sona.ai', 'sona.interpreter', 'sona.parser', 'torch', 'transformers')):
        raise AssertionError('Guide imported an execution or provider dependency: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from sona.cli import main
sys.argv = ['sona', 'why', 'PROOF-VERIFY-005', '--json']
raise SystemExit(main())
"""
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=tmp_path, env=environment,
        capture_output=True, text=True, timeout=10, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["basis"] == "catalog-reference"
    assert list(tmp_path.iterdir()) == []
