from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from sona import example_runner
from sona.example_catalog import (
    ExampleError,
    asset_text,
    load_manifest,
    validate_manifest,
)
from sona.guide.catalog import CONCEPTS
from sona.guide.learning import lesson, lessons
from sona.guide.profile import LearningProfile

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = load_manifest()
PYTHON_NAMES = [entry["name"] for entry in MANIFEST["examples"] if entry["runtime"] == "python"]


def _cli(*arguments, cwd, environment=None):
    env = os.environ.copy()
    env.update(environment or {})
    env["PYTHONPATH"] = str(ROOT)
    return subprocess.run([sys.executable, "-m", "sona", *arguments], cwd=cwd, env=env,
                          capture_output=True, text=True, encoding="utf-8", timeout=60, check=False)


@pytest.mark.parametrize("name", PYTHON_NAMES)
def test_all_packaged_python_examples_execute_real_checks(name, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sentinel = tmp_path / ".sona" / "keep.txt"
    sentinel.parent.mkdir()
    sentinel.write_text("user state", encoding="utf-8")
    result = example_runner.run_example(name)
    assert result["status"] == "passed", result
    assert result["runtime"] == "python"
    assert result["receipt"] is None
    assert result["progress_recorded"] is False
    assert all(check["passed"] for check in result["checks"])
    assert sentinel.read_text(encoding="utf-8") == "user state"
    assert sorted(path.name for path in tmp_path.iterdir()) == [".sona"]


@pytest.mark.parametrize("name", ["guardian", "proof-mode"])
def test_native_examples_use_real_receipts_and_guardian(name, native_binary, monkeypatch):
    monkeypatch.setenv("SONA_NATIVE_BINARY", str(native_binary))
    result = example_runner.run_example(name)
    assert result["status"] == "passed", result
    facts = result["receipt"]
    assert facts["status"] == "valid"
    assert facts["engine"]["fallback_used"] is False
    assert facts["engine"]["python_required"] is False
    if name == "guardian":
        assert facts["execution"]["status"] == "failed"
        assert facts["execution"]["diagnostic"]["id"] == "SONA-FS-005"
        assert facts["guardian_bound"] is True
        assert result["guardian"]["status"] == "ok"
    else:
        assert facts["execution"]["status"] == "ok"


@pytest.mark.parametrize("mode", ["guided", "balanced", "expert"])
def test_all_nine_lessons_share_catalog_and_canonical_manifest(mode):
    profile = LearningProfile()
    rows = lessons(profile)
    assert {row["concept"] for row in rows} == set(CONCEPTS)
    for row in rows:
        result = lesson(row["concept"], profile, mode=mode)
        assert result["explanation"]["summary"] == CONCEPTS[row["concept"]].summary
        assert result["explanation"]["provenance"]["source"] == "sona-guide-concepts"
        assert result["example"] in {entry["name"] for entry in MANIFEST["examples"]}


def test_listing_and_exploring_do_not_write_profile(tmp_path):
    for arguments in [("examples",), ("learn",), ("learn", "variables")]:
        result = _cli(*arguments, "--json", cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["status"] == "ok"
    assert not list(tmp_path.iterdir())


def test_explicit_practice_progress_is_minimal_and_preserves_comfortable(tmp_path):
    first = _cli("learn", "run", "variables", "--json", cwd=tmp_path)
    assert first.returncode == 0, first.stdout + first.stderr
    result = json.loads(first.stdout)
    assert result["progress_recorded"] is True
    profile_path = tmp_path / ".sona" / "learning.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    assert profile["concepts"] == {"variables": "learning"}
    assert set(profile) == {"schema", "guidance_mode", "diagnostic_density", "explanation_style", "quiet", "concepts"}
    profile["concepts"]["variables"] = "comfortable"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    original = profile_path.read_bytes()
    second = _cli("learn", "run", "variables", "--json", cwd=tmp_path)
    assert second.returncode == 0, second.stdout + second.stderr
    assert profile_path.read_bytes() == original


def test_no_profile_practice_ignores_corrupt_state(tmp_path):
    state = tmp_path / ".sona" / "learning.json"
    state.parent.mkdir()
    state.write_text("broken state must stay untouched", encoding="utf-8")
    result = _cli("learn", "run", "files", "--no-profile", "--json", cwd=tmp_path)
    assert result.returncode == 0, result.stdout
    assert json.loads(result.stdout)["progress_recorded"] is False
    assert state.read_text(encoding="utf-8") == "broken state must stay untouched"
    assert not (tmp_path / "practice.txt").exists()


@pytest.mark.parametrize("arguments", [("examples", "run", "../../secret"), ("learn", "unknown"), ("learn", "run")])
def test_unknown_names_fail_without_echoing_untrusted_input(arguments, tmp_path):
    result = _cli(*arguments, "--json", cwd=tmp_path)
    assert result.returncode == 1
    assert json.loads(result.stdout)["diagnostic"]["diagnostic_id"] == "SONA-EXAMPLE-001"
    assert "secret" not in result.stdout
    assert not list(tmp_path.iterdir())


def test_native_unavailable_never_fakes_success_or_progress(tmp_path):
    result = _cli("learn", "run", "proof-mode", "--json", cwd=tmp_path,
                  environment={"SONA_NATIVE_BINARY": str(tmp_path / "missing-private-native.exe")})
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "unavailable"
    assert payload["diagnostic"]["diagnostic_id"] == "SONA-NATIVE-LAUNCH-001"
    assert "missing-private" not in result.stdout
    assert not list(tmp_path.iterdir())


def test_failed_checks_do_not_record_practice(monkeypatch, tmp_path, capsys):
    from argparse import Namespace

    from sona.learning_cli import handle_learning_command

    monkeypatch.setattr(example_runner, "run_example", lambda name: {
        "status": "failed", "checks": [{"id": "expected-stdout", "passed": False}],
        "example": name, "progress_recorded": False,
    })
    args = Namespace(command="learn", topic="run", lesson="variables", mode=None, json=True,
                     no_profile=False, project_root=str(tmp_path))
    assert handle_learning_command(args) == 1
    assert json.loads(capsys.readouterr().out)["progress_recorded"] is False
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("bad", [True, 1.0, "1", 0, 2, None])
def test_manifest_schema_is_strict(bad):
    payload = copy.deepcopy(MANIFEST)
    payload["schema"] = bad
    with pytest.raises(ExampleError, match="SONA-EXAMPLE-002"):
        validate_manifest(payload)


@pytest.mark.parametrize("bad", ["../outside.sona", "C:/private.sona", "/tmp/private.sona", "x\\y.sona", "x//y.sona", ".sona/private.sona"])
def test_manifest_path_escape_and_hidden_assets_rejected(bad):
    payload = copy.deepcopy(MANIFEST)
    payload["examples"][0]["source"] = bad
    with pytest.raises(ExampleError):
        validate_manifest(payload)
    with pytest.raises(ExampleError):
        asset_text(bad)


def test_manifest_duplicate_name_and_concept_rejected():
    for field in ("name", "concept"):
        payload = copy.deepcopy(MANIFEST)
        payload["examples"][0][field] = payload["examples"][1][field]
        with pytest.raises(ExampleError):
            validate_manifest(payload)


def test_manifest_retains_all_original_official_sources():
    assert {entry["source"] for entry in MANIFEST["examples"]}.issuperset({
        "hello.sona", "variables_math.sona", "functions.sona", "control_flow.sona", "stdlib_math.sona",
        "stdlib_string.sona", "stdlib_json.sona", "stdlib_fs.sona", "calculator.sona",
    })


def test_runtime_timeout_and_output_limits(monkeypatch, tmp_path):
    monkeypatch.setattr(example_runner, "TIMEOUT_SECONDS", 0.2)
    with pytest.raises(ExampleError) as timed:
        example_runner._execute([sys.executable, "-c", "import time; time.sleep(5)"], tmp_path, os.environ.copy())
    assert timed.value.diagnostic_id == "SONA-EXAMPLE-004"
    monkeypatch.setattr(example_runner, "TIMEOUT_SECONDS", 10)
    with pytest.raises(ExampleError) as output:
        example_runner._execute([sys.executable, "-c", "print('x' * 100000)"], tmp_path, os.environ.copy())
    assert output.value.diagnostic_id == "SONA-EXAMPLE-004"


def test_bad_expected_output_fails_a_real_run(monkeypatch):
    entry = copy.deepcopy(MANIFEST["examples"][0])
    entry["stdout"] = "This must not be treated as a pass.\n"
    monkeypatch.setattr(example_runner, "find_example", lambda _name: entry)
    result = example_runner.run_example("hello")
    assert result["status"] == "failed"
    assert result["execution"]["exit_code"] == 0
    assert result["diagnostic"]["diagnostic_id"] == "SONA-EXAMPLE-005"
    assert result["progress_recorded"] is False


def test_launch_failure_is_redacted(monkeypatch, tmp_path):
    def fail(*_args, **_kwargs):
        raise PermissionError("secret-path credential-value")

    monkeypatch.setattr(example_runner.subprocess, "Popen", fail)
    with pytest.raises(ExampleError) as error:
        example_runner._execute(["unused"], tmp_path, {})
    assert error.value.diagnostic_id == "SONA-EXAMPLE-003"
    assert "secret" not in json.dumps(error.value.to_dict())


def test_profile_write_failure_keeps_passed_execution_evidence(monkeypatch, tmp_path, capsys):
    from argparse import Namespace

    from sona.guide import learning
    from sona.guide.models import GuideError
    from sona.learning_cli import handle_learning_command

    def fail(*_args, **_kwargs):
        raise GuideError("SONA-GUIDE-006", "Profile write failed.", "Review project permissions.")

    monkeypatch.setattr(learning, "record_practice", fail)
    args = Namespace(command="learn", topic="run", lesson="variables", mode=None, json=True,
                     no_profile=False, project_root=str(tmp_path))
    assert handle_learning_command(args) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "unavailable"
    assert result["execution"]["exit_code"] == 0
    assert all(check["passed"] for check in result["checks"])
    assert result["progress_recorded"] is False
    assert not list(tmp_path.iterdir())
