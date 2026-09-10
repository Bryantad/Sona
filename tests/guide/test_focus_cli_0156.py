from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from sona.developer_intelligence.diagnostics import SourceSpan, diagnostic
from sona.guide import focus_diagnostics

ROOT = Path(__file__).resolve().parents[2]


def run_focus(directory: Path, *arguments: str, stdin: str | None = None):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    environment["SONA_NATIVE_BINARY"] = "missing-native-do-not-launch"
    return subprocess.run(
        [sys.executable, "-m", "sona", "focus", *arguments],
        input=stdin,
        cwd=directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_cli_focus_recomputes_current_source_without_project_state(tmp_path):
    target = tmp_path / "broken.sona"
    target.write_text("let value = (1;\n", encoding="utf-8")

    broken = run_focus(tmp_path, str(target), "--density", "complete", "--json")

    assert broken.returncode == 0 and broken.stderr == ""
    payload = json.loads(broken.stdout)
    assert payload["diagnostics"][0]["diagnostic_id"] == "SONA-PARSE-003"
    assert payload["visible_indices"] == [0]

    target.write_text("let value = (1);\n", encoding="utf-8")
    fixed = run_focus(tmp_path, str(target), "--json")

    assert fixed.returncode == 0 and fixed.stderr == ""
    assert json.loads(fixed.stdout)["diagnostics"] == []
    assert sorted(item.name for item in tmp_path.iterdir()) == ["broken.sona"]


def test_cli_focus_accepts_canonical_diagnostic_json_from_stdin(tmp_path):
    diagnostics = [
        diagnostic(
            "SONA-PARSE-003",
            "syntax",
            "Incomplete syntax.",
            span=SourceSpan(file="broken.sona", start_line=1, start_column=13),
        ).to_dict(),
        diagnostic(
            "SONA-RUNTIME-003",
            "runtime",
            "Name 'value' is not defined.",
            span=SourceSpan(file="broken.sona", start_line=2, start_column=7),
        ).to_dict(),
    ]

    result = run_focus(
        tmp_path,
        "--diagnostics-json",
        "-",
        "--density",
        "focused",
        "--json",
        stdin=json.dumps(diagnostics),
    )

    assert result.returncode == 0 and result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload == focus_diagnostics(
        tuple(
            diagnostic(
                item["diagnostic_id"],
                item["category"],
                item["message"],
                severity=item["severity"],
                hint=item["hint"],
                span=SourceSpan(
                    file=item["file"],
                    start_line=item["start_line"],
                    start_column=item["start_column"],
                ),
            )
            for item in diagnostics
        ),
        density="focused",
    ).to_dict()
    assert payload["suppressed_count"] == 1


def test_cli_focus_text_mentions_complete_density_when_items_are_grouped(tmp_path):
    diagnostics = [
        diagnostic(
            "SONA-PARSE-003",
            "syntax",
            "Incomplete syntax.",
            span=SourceSpan(file="broken.sona", start_line=1, start_column=13),
        ).to_dict(),
        diagnostic(
            "SONA-PARSE-001",
            "syntax",
            "Unexpected syntax.",
            span=SourceSpan(file="broken.sona", start_line=2, start_column=1),
        ).to_dict(),
    ]

    result = run_focus(tmp_path, "--diagnostics-json", "-", stdin=json.dumps(diagnostics))

    assert result.returncode == 0 and result.stderr == ""
    assert "Use --density complete" in result.stdout
    assert "2 total, 1 shown, 1 grouped" in result.stdout


def test_cli_focus_invalid_inputs_are_safe_failures(tmp_path):
    malformed = run_focus(tmp_path, "--diagnostics-json", "-", "--json", stdin="{")
    assert malformed.returncode == 1
    assert json.loads(malformed.stdout)["diagnostic"]["diagnostic_id"] == "SONA-GUIDE-002"

    missing = run_focus(tmp_path, "--json")
    assert missing.returncode == 1
    assert json.loads(missing.stdout)["diagnostic"]["diagnostic_id"] == "SONA-GUIDE-002"

    invalid_density = run_focus(tmp_path, "--density", "hide-errors")
    assert invalid_density.returncode == 2
    assert "invalid choice" in invalid_density.stderr
