import sys

from sona import cli


def _run_cli(args, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["sona"] + args)
    return cli.main()


def test_errors_both_prints_explain_then_trace(tmp_path, capsys, monkeypatch):
    source = tmp_path / "fail.sona"
    source.write_text("let x = 1 + [2];", encoding="utf-8")

    exit_code = _run_cli(["run", str(source), "--errors=both"], monkeypatch)
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert exit_code == 1
    explain_idx = output.find("This operation tried to apply")
    trace_idx = output.find("Traceback (most recent call last)")
    assert explain_idx != -1
    assert trace_idx != -1
    assert explain_idx < trace_idx
    assert output.count("This operation tried to apply") == 1
