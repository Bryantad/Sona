from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_sona(directory: Path, *arguments: str, stdin: str | None = None):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    environment["SONA_NATIVE_BINARY"] = "missing-native-do-not-launch"
    return subprocess.run(
        [sys.executable, "-m", "sona", *arguments],
        input=stdin,
        cwd=directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_cli_profile_show_uses_defaults_without_creating_state(tmp_path):
    result = run_sona(tmp_path, "guide", "profile", "--json")

    assert result.returncode == 0 and result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["persisted"] is False
    assert payload["profile_path"] == ".sona/learning.json"
    assert payload["profile"]["guidance_mode"] == "guided"
    assert str(tmp_path) not in result.stdout
    assert not (tmp_path / ".sona").exists()

    text = run_sona(tmp_path, "guide", "profile")
    assert text.returncode == 0 and text.stderr == ""
    assert "Sona Guide Profile" in text.stdout
    assert "Status       DEFAULT" in text.stdout
    assert ".sona/learning.json" in text.stdout


def test_cli_profile_set_learn_and_reset_are_explicit_project_local_writes(tmp_path):
    set_result = run_sona(
        tmp_path,
        "guide",
        "profile",
        "set",
        "--mode",
        "balanced",
        "--density",
        "focused",
        "--style",
        "technical",
        "--quiet",
        "--json",
    )

    assert set_result.returncode == 0 and set_result.stderr == ""
    payload = json.loads(set_result.stdout)
    assert payload["persisted"] is True
    assert payload["profile"]["guidance_mode"] == "balanced"
    assert payload["profile"]["diagnostic_density"] == "focused"
    assert payload["profile"]["explanation_style"] == "technical"
    assert payload["profile"]["quiet"] is True

    learn_result = run_sona(
        tmp_path,
        "guide",
        "profile",
        "learn",
        "variables",
        "--familiarity",
        "comfortable",
        "--json",
    )

    assert learn_result.returncode == 0 and learn_result.stderr == ""
    assert json.loads(learn_result.stdout)["profile"]["concepts"] == {
        "variables": "comfortable",
    }

    reset_result = run_sona(tmp_path, "guide", "profile", "reset", "--json")

    assert reset_result.returncode == 0 and reset_result.stderr == ""
    reset_payload = json.loads(reset_result.stdout)
    assert reset_payload["profile"]["guidance_mode"] == "guided"
    assert reset_payload["profile"]["diagnostic_density"] == "normal"
    assert reset_payload["profile"]["concepts"] == {}


def test_cli_profile_errors_are_structured_and_sanitized(tmp_path):
    result = run_sona(tmp_path, "guide", "profile", "set", "--json")

    assert result.returncode == 1 and result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["status"] == "unavailable"
    assert payload["diagnostic"]["diagnostic_id"] == "SONA-GUIDE-002"
    assert "Traceback" not in result.stdout

    profile = tmp_path / ".sona" / "learning.json"
    profile.parent.mkdir()
    profile.write_text("{not valid", encoding="utf-8")
    failed = run_sona(tmp_path, "guide", "profile", "--json")

    assert failed.returncode == 1 and failed.stderr == ""
    failed_payload = json.loads(failed.stdout)
    assert failed_payload["diagnostic"]["diagnostic_id"] == "SONA-GUIDE-005"
    assert "not valid" not in failed.stdout


def test_cli_why_uses_learning_profile_but_explicit_mode_wins(tmp_path):
    for concept in ("variables", "scope"):
        learned = run_sona(
            tmp_path,
            "guide",
            "profile",
            "learn",
            concept,
            "--familiarity",
            "comfortable",
            "--json",
        )
        assert learned.returncode == 0

    profiled = run_sona(tmp_path, "why", "SONA-RUNTIME-003", "--json")

    assert profiled.returncode == 0 and profiled.stderr == ""
    assert json.loads(profiled.stdout)["mode"] == "balanced"

    explicit = run_sona(tmp_path, "why", "SONA-RUNTIME-003", "--mode", "guided", "--json")
    assert explicit.returncode == 0
    assert json.loads(explicit.stdout)["mode"] == "guided"

    profile = tmp_path / ".sona" / "learning.json"
    profile.write_text("{not valid", encoding="utf-8")
    bypassed = run_sona(tmp_path, "why", "SONA-RUNTIME-003", "--no-profile", "--json")

    assert bypassed.returncode == 0
    assert json.loads(bypassed.stdout)["mode"] == "guided"


def test_cli_focus_uses_profile_density_and_preserves_explicit_override(tmp_path):
    configured = run_sona(
        tmp_path,
        "guide",
        "profile",
        "set",
        "--density",
        "focused",
        "--json",
    )
    assert configured.returncode == 0
    diagnostics = [
        {
            "diagnostic_id": "SONA-PARSE-003",
            "category": "syntax",
            "severity": "error",
            "message": "Incomplete syntax.",
            "hint": "",
            "file": "broken.sona",
            "start_line": 1,
            "start_column": 13,
        },
        {
            "diagnostic_id": "SONA-RUNTIME-003",
            "category": "runtime",
            "severity": "error",
            "message": "Name 'value' is not defined.",
            "hint": "",
            "file": "broken.sona",
            "start_line": 2,
            "start_column": 7,
        },
    ]

    profiled = run_sona(
        tmp_path,
        "focus",
        "--diagnostics-json",
        "-",
        "--json",
        stdin=json.dumps(diagnostics),
    )
    explicit = run_sona(
        tmp_path,
        "focus",
        "--diagnostics-json",
        "-",
        "--density",
        "complete",
        "--json",
        stdin=json.dumps(diagnostics),
    )

    assert profiled.returncode == 0 and profiled.stderr == ""
    assert json.loads(profiled.stdout)["density"] == "focused"
    assert json.loads(profiled.stdout)["suppressed_count"] == 1
    assert explicit.returncode == 0 and explicit.stderr == ""
    assert json.loads(explicit.stdout)["density"] == "complete"
    assert json.loads(explicit.stdout)["visible_indices"] == [0, 1]


def test_cli_successful_fix_updates_learning_profile_only_after_apply(tmp_path):
    source = "let quantity = 3;\nprint(quant);\n"
    target = tmp_path / "cart.sona"
    target.write_text(source, encoding="utf-8")

    preview = run_sona(
        tmp_path,
        "fix",
        str(target),
        "--diagnostic-id",
        "SONA-RUNTIME-003",
        "--name",
        "quant",
        "--line",
        "2",
        "--column",
        "7",
        "--json",
    )

    assert preview.returncode == 0 and preview.stderr == ""
    assert json.loads(preview.stdout)["learning_profile"]["updated"] is False
    assert not (tmp_path / ".sona").exists()

    applied = run_sona(
        tmp_path,
        "fix",
        str(target),
        "--diagnostic-id",
        "SONA-RUNTIME-003",
        "--name",
        "quant",
        "--line",
        "2",
        "--column",
        "7",
        "--apply",
        "--json",
    )

    assert applied.returncode == 0 and applied.stderr == ""
    payload = json.loads(applied.stdout)
    assert payload["status"] == "applied"
    assert payload["learning_profile"]["updated"] is True
    assert payload["learning_profile"]["concepts"] == ["variables", "scope"]
    profile = json.loads((tmp_path / ".sona" / "learning.json").read_text(encoding="utf-8"))
    assert profile["concepts"] == {"scope": "learning", "variables": "learning"}


def test_cli_fix_profile_update_can_be_disabled(tmp_path):
    target = tmp_path / "legacy.sona"
    target.write_text("import io;\nlet body = io.read_file(\"in.txt\");\n", encoding="utf-8")

    result = run_sona(
        tmp_path,
        "fix",
        str(target),
        "--rule",
        "stdlib-api-migration",
        "--apply",
        "--no-profile-update",
        "--json",
    )

    assert result.returncode == 0 and result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["learning_profile"]["updated"] is False
    assert payload["learning_profile"]["reason"] == "disabled"
    assert "fs.read_text" in target.read_text(encoding="utf-8")
    assert not (tmp_path / ".sona").exists()
