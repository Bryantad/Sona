from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from sona.developer_intelligence.frontend import analyze_frontend
from sona.lsp_server import canonical_diagnostics


ROOT = Path(__file__).resolve().parents[2]


def cli(*args: str, cwd: Path = ROOT):
    return subprocess.run(
        [sys.executable, "-m", "sona", *args],
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )


@pytest.mark.parametrize("command", ["check", "explain", "suggest"])
def test_json_clients_share_parse_diagnostic_and_nonzero_exit(tmp_path, command):
    source = "let value = (1;"
    path = tmp_path / "invalid source 雪.sona"
    path.write_text(source, encoding="utf-8")
    result = cli(command, str(path), "--format", "json")
    assert result.returncode != 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == 1
    diagnostics = payload["diagnostics"]
    assert diagnostics
    assert diagnostics[0]["diagnostic_id"] == "SONA-PARSE-003"
    assert diagnostics[0]["start_line"] == 1
    assert diagnostics[0]["start_column"] >= 1
    assert "\x1b" not in result.stdout


def test_run_and_lsp_report_same_unsupported_construct_without_traceback(tmp_path):
    source = "class Example { }"
    path = tmp_path / "unsupported.sona"
    path.write_text(source, encoding="utf-8")
    result = cli("run", str(path), "--compatibility", "sona")
    combined = result.stdout + result.stderr
    assert result.returncode != 0
    assert "SONA-SEM-099" in combined
    assert "Traceback" not in combined

    lsp = canonical_diagnostics(path.as_uri(), source)
    frontend = analyze_frontend(source, file=path.as_uri())
    assert [item.to_dict() for item in lsp] == [item.to_dict() for item in frontend]
    assert lsp[0].diagnostic_id == "SONA-SEM-099"
    assert lsp[0].span.start_line == 1
    assert lsp[0].span.start_column == 1


def test_unicode_and_crlf_columns_match_cli_and_lsp(tmp_path):
    source = '// 雪\r\nlet value = ;\r\n'
    path = tmp_path / "columns.sona"
    path.write_text(source, encoding="utf-8", newline="")
    result = cli("check", str(path), "--format", "json")
    payload = json.loads(result.stdout)
    cli_diag = payload["diagnostics"][0]
    lsp_diag = canonical_diagnostics(path.as_uri(), source)[0]
    assert (cli_diag["start_line"], cli_diag["start_column"]) == (
        lsp_diag.span.start_line,
        lsp_diag.span.start_column,
    )
    assert cli_diag["start_line"] == 2


def test_missing_file_and_directory_are_structured_failures(tmp_path):
    missing = cli("check", str(tmp_path / "missing.sona"), "--format", "json")
    assert missing.returncode != 0
    assert json.loads(missing.stdout)["diagnostics"][0]["diagnostic_id"] == "SONA-MODULE-001"

    directory = cli("check", str(tmp_path), "--format", "json")
    assert directory.returncode != 0
    payload = json.loads(directory.stdout)
    assert payload["diagnostics"][0]["diagnostic_id"] == "SONA-MODULE-003"
    assert directory.stderr == ""


def test_permission_failure_is_sanitized_structured_and_nonzero(tmp_path, monkeypatch, capsys):
    from sona import cli as cli_module

    target = tmp_path / "permission denied.sona"
    target.write_text("print(1);", encoding="utf-8")

    def denied(_path):
        raise PermissionError("private host detail")

    monkeypatch.setattr(cli_module, "read_text_safe", denied)
    status = cli_module.handle_check_command(
        SimpleNamespace(file=str(target), format="json", json=False)
    )
    captured = capsys.readouterr()
    assert status != 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["diagnostics"][0]["diagnostic_id"] == "SONA-PARSE-099"
    assert "private host detail" not in captured.out


def test_version_and_help_do_not_load_parser_or_heavy_ai_modules():
    code = (
        "import sys,sona.cli; sys.argv=['sona','--version']; "
        "assert sona.cli.main() == 0; "
        "blocked=('lark','torch','transformers','accelerate','openai','anthropic'); "
        "assert not [name for name in blocked if name in sys.modules]"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert result.returncode == 0, result.stderr
