from types import SimpleNamespace

import pytest

from sona.cli import _repl_source_complete, handle_repl_command


def _run_repl(monkeypatch, inputs):
    iterator = iter(inputs)
    prompts = []

    def scripted_input(prompt):
        prompts.append(prompt)
        return next(iterator)

    monkeypatch.setattr("builtins.input", scripted_input)
    result = handle_repl_command(SimpleNamespace(ai=False))
    return result, prompts


def test_repl_buffer_detects_multiline_and_incomplete_input():
    assert not _repl_source_complete("if true {")
    assert not _repl_source_complete('print("unterminated')
    assert _repl_source_complete("if true {\nprint(1);\n}")
    assert _repl_source_complete("print(1));")


def test_repl_persists_state_and_reset_is_deterministic(monkeypatch, capsys):
    status, _prompts = _run_repl(
        monkeypatch,
        ["let value = 41;", "value = value + 1;", "value", ":reset", "value", "1 + 1", "exit"],
    )
    output = capsys.readouterr().out
    assert status == 0
    assert "=> 42" in output
    assert "REPL state reset" in output
    assert "SONA-RUNTIME-003" in output
    assert output.rstrip().endswith("=> 2")


def test_repl_multiline_function_import_and_error_recovery(monkeypatch, capsys):
    status, prompts = _run_repl(
        monkeypatch,
        [
            "func twice(value) {",
            "return value * 2;",
            "}",
            "twice(4)",
            "import math;",
            "1 / 0",
            "twice(5)",
            "quit",
        ],
    )
    output = capsys.readouterr().out
    assert status == 0
    assert "...> " in prompts
    assert "=> 8" in output
    assert "SONA-RUNTIME-004" in output
    assert output.rstrip().endswith("=> 10")


def test_repl_eof_exits_cleanly(monkeypatch):
    def eof(_prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", eof)
    assert handle_repl_command(SimpleNamespace(ai=False)) == 0

