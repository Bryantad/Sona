from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_fix(directory: Path, *arguments: str, stdin: str | None = None):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    environment["SONA_NATIVE_BINARY"] = "missing-native-do-not-launch"
    return subprocess.run(
        [sys.executable, "-m", "sona", "fix", *arguments],
        input=stdin,
        cwd=directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_cli_previews_and_applies_undefined_name_fix(tmp_path):
    source = "let price = 10;\nlet quantity = 3;\nlet total = price * quant;\n"
    target = tmp_path / "cart.sona"
    target.write_text(source, encoding="utf-8")

    preview = run_fix(
        tmp_path,
        str(target),
        "--diagnostic-id",
        "SONA-RUNTIME-003",
        "--name",
        "quant",
        "--line",
        "3",
        "--column",
        "21",
        "--json",
    )

    assert preview.returncode == 0 and preview.stderr == ""
    payload = json.loads(preview.stdout)
    assert payload["status"] == "preview"
    assert payload["fixes"][0]["edits"][0]["expected"] == "quant"
    assert target.read_text(encoding="utf-8") == source

    applied = run_fix(
        tmp_path,
        str(target),
        "--diagnostic-id",
        "SONA-RUNTIME-003",
        "--name",
        "quant",
        "--line",
        "3",
        "--column",
        "21",
        "--apply",
        "--json",
    )

    assert applied.returncode == 0 and applied.stderr == ""
    assert json.loads(applied.stdout)["status"] == "applied"
    assert "price * quantity" in target.read_text(encoding="utf-8")


def test_cli_accepts_diagnostic_json_from_stdin(tmp_path):
    target = tmp_path / "cart.sona"
    target.write_text("let quantity = 3;\nprint(quant);\n", encoding="utf-8")
    diagnostic = {
        "diagnostic_id": "SONA-RUNTIME-003",
        "category": "runtime",
        "severity": "error",
        "message": "Name 'quant' is not defined.",
        "file": str(target),
        "start_line": 2,
        "start_column": 7,
    }

    result = run_fix(tmp_path, str(target), "--diagnostic-json", "-", "--json", stdin=json.dumps(diagnostic))

    assert result.returncode == 0 and result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["fixes"][0]["edits"][0]["replacement"] == "quantity"


def test_cli_applies_manifest_backed_stdlib_migration(tmp_path):
    target = tmp_path / "legacy.sona"
    target.write_text("import io;\nlet body = io.read_file(\"in.txt\");\n", encoding="utf-8")

    preview = run_fix(tmp_path, str(target), "--rule", "stdlib-api-migration")
    assert preview.returncode == 0 and preview.stderr == ""
    assert "No files changed" in preview.stdout
    assert "io.read_file" in target.read_text(encoding="utf-8")

    applied = run_fix(tmp_path, str(target), "--rule", "stdlib-api-migration", "--apply", "--json")

    assert applied.returncode == 0 and applied.stderr == ""
    payload = json.loads(applied.stdout)
    assert payload["status"] == "applied"
    updated = target.read_text(encoding="utf-8")
    assert "import fs;" in updated
    assert "fs.read_text" in updated


def test_cli_reports_no_fix_without_traceback(tmp_path):
    target = tmp_path / "plain.sona"
    target.write_text("print(1);\n", encoding="utf-8")

    result = run_fix(tmp_path, str(target), "--rule", "stdlib-api-migration", "--json")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "unavailable"
    assert payload["diagnostic"]["diagnostic_id"] == "SONA-GUIDE-004"
    assert "Traceback" not in result.stdout + result.stderr
