import sys

from sona import cli


def _run_cli(args, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["sona"] + args)
    return cli.main()


def test_errors_explain_prints_compact_diagnostic(tmp_path, capsys, monkeypatch):
    source = tmp_path / "fail_explain.sona"
    source.write_text("let x = 1 + [2];", encoding="utf-8")

    exit_code = _run_cli(["run", str(source), "--errors=explain"], monkeypatch)
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert exit_code == 1
    assert "SonaTypeError:" in output
    assert "hint:" in output
    assert "Traceback (most recent call last)" not in output


def test_errors_trace_prints_traceback_only(tmp_path, capsys, monkeypatch):
    source = tmp_path / "fail_trace.sona"
    source.write_text("let x = 1 + [2];", encoding="utf-8")

    exit_code = _run_cli(["run", str(source), "--errors=trace"], monkeypatch)
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert exit_code == 1
    assert "Traceback (most recent call last)" in output
    assert "hint:" not in output


def test_errors_both_prints_explain_then_trace(tmp_path, capsys, monkeypatch):
    source = tmp_path / "fail.sona"
    source.write_text("let x = 1 + [2];", encoding="utf-8")

    exit_code = _run_cli(["run", str(source), "--errors=both"], monkeypatch)
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert exit_code == 1
    explain_idx = output.find("SonaTypeError:")
    trace_idx = output.find("Traceback (most recent call last)")
    assert explain_idx != -1
    assert trace_idx != -1
    assert explain_idx < trace_idx
    assert output.count("SonaTypeError:") == 1
    assert "hint:" in output
