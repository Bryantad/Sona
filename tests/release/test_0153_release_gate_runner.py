from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "tests" / "release" / "run_0153_release_gate.py"
SPEC = importlib.util.spec_from_file_location("release_gate_0153", RUNNER_PATH)
assert SPEC is not None and SPEC.loader is not None
release_gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = release_gate
SPEC.loader.exec_module(release_gate)


def test_release_gate_uses_exact_positive_and_negative_schema(tmp_path):
    process = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tests" / "release" / "run_0153_release_gate.py"),
            "--output-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        shell=False,
        timeout=60,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    json_path = tmp_path / f"sona-{release_gate.SONA_VERSION}-release-gate.json"
    markdown_path = tmp_path / f"sona-{release_gate.SONA_VERSION}-release-gate.md"
    summary = json.loads(json_path.read_text(encoding="utf-8"))
    assert summary["schema_id"] == "sona.release-gate.schema-2"
    assert summary["schema"] == 2
    assert summary["positive_pass"] == 5
    assert summary["negative_pass"] == 5
    assert summary["fail"] == 0
    assert summary["warning"] == 0
    assert len(summary["results"]) == 10
    assert {result["name"] for result in summary["results"]} == {
        "canonical-func",
        "cognitive-empty",
        "cognitive-malformed-spread",
        "core-language",
        "division-by-zero",
        "guardian-check",
        "legacy-fn-syntax",
        "legacy-use-syntax",
        "module-repr",
        "undefined-function",
    }
    assert all(not result["failures"] for result in summary["results"])
    assert "Positive pass: 5" in markdown_path.read_text(encoding="utf-8")


def test_release_gate_rejects_repository_output():
    process = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tests" / "release" / "run_0153_release_gate.py"),
            "--output-dir",
            str(ROOT / ".release-artifacts" / "forbidden"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        shell=False,
        timeout=30,
    )
    assert process.returncode != 0
    assert "must resolve outside the repository" in process.stderr


def test_negative_match_fails_when_any_reviewed_field_differs():
    baseline = next(
        case
        for case in release_gate._load_cases()
        if case["name"] == "legacy-fn-syntax"
    )
    assert release_gate._evaluate(baseline).status == "negative_pass"

    for field, value in baseline["expected"].items():
        changed = deepcopy(baseline)
        if isinstance(value, bool):
            changed["expected"][field] = not value
        elif isinstance(value, int):
            changed["expected"][field] = value + 1
        elif value is None:
            changed["expected"][field] = "unexpected"
        else:
            changed["expected"][field] = f"{value} unexpected"
        result = release_gate._evaluate(changed)
        assert result.status == "fail", field
        assert field in result.failures


def test_negative_match_rejects_wrong_mode_and_unexpected_success():
    negative = next(
        case
        for case in release_gate._load_cases()
        if case["name"] == "legacy-fn-syntax"
    )
    wrong_mode = deepcopy(negative)
    wrong_mode["execution_mode"] = "native"
    assert release_gate._evaluate(wrong_mode).failures == ["execution_mode"]

    positive_source = next(
        case["source"]
        for case in release_gate._load_cases()
        if case["name"] == "canonical-func"
    )
    unexpected_success = deepcopy(negative)
    unexpected_success["source"] = positive_source
    assert release_gate._evaluate(unexpected_success).status == "fail"
