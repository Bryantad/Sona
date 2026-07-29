from __future__ import annotations

import json
from pathlib import Path

import pytest

from sona.errors import SonaSyntaxError
from sona.parser_v090 import SonaParserv090


def test_missing_lark_dependency_is_an_infrastructure_diagnostic(monkeypatch, capsys):
    import sona.parser_v090 as parser_module

    monkeypatch.setattr(parser_module, "Lark", None)
    parser = parser_module.SonaParserv090()
    with pytest.raises(SonaSyntaxError) as caught:
        parser.parse("print(1);", "missing-lark.sona")
    assert caught.value.diagnostic.diagnostic_id == "SONA-PARSE-099"
    assert "dependency" in caught.value.diagnostic.message.lower()
    assert capsys.readouterr().out == ""


def test_missing_and_corrupt_grammar_are_not_replaced_by_embedded_fallback(tmp_path, capsys):
    missing = SonaParserv090(grammar_file=str(tmp_path / "missing.lark"))
    with pytest.raises(SonaSyntaxError) as caught:
        missing.parse("print(1);", "missing-grammar.sona")
    assert caught.value.diagnostic.diagnostic_id == "SONA-PARSE-099"

    corrupt_path = tmp_path / "corrupt.lark"
    corrupt_path.write_text("start: (((", encoding="utf-8")
    corrupt = SonaParserv090(grammar_file=str(corrupt_path))
    with pytest.raises(SonaSyntaxError) as caught:
        corrupt.parse("print(1);", "corrupt-grammar.sona")
    assert caught.value.diagnostic.diagnostic_id == "SONA-PARSE-099"
    assert capsys.readouterr().out == ""


def test_transformer_defect_is_sanitized_and_not_reported_as_user_syntax(monkeypatch):
    parser = SonaParserv090()

    def fail_transform(_tree):
        raise AttributeError("private transformer detail")

    monkeypatch.setattr(parser.transformer, "transform", fail_transform)
    with pytest.raises(SonaSyntaxError) as caught:
        parser.parse("print(1);", "transformer.sona")
    diagnostic = caught.value.diagnostic
    assert diagnostic.diagnostic_id == "SONA-PARSE-099"
    assert "private transformer detail" not in diagnostic.message


def test_missing_or_corrupt_stdlib_manifest_is_a_stable_module_failure(tmp_path):
    from sona.errors import SonaImportError
    from sona.interpreter import SonaUnifiedInterpreter

    interpreter = SonaUnifiedInterpreter(project_root=tmp_path)
    missing_root = tmp_path / "missing-stdlib"
    missing_root.mkdir()
    interpreter.module_system.stdlib_path = missing_root
    with pytest.raises(SonaImportError) as caught:
        interpreter.module_system._load_manifest_payload()
    assert caught.value.diagnostic.diagnostic_id == "SONA-MODULE-003"

    manifest = missing_root / "MANIFEST.json"
    manifest.write_text("{broken", encoding="utf-8")
    interpreter.module_system._manifest_payload = None
    with pytest.raises(SonaImportError) as caught:
        interpreter.module_system._load_manifest_payload()
    assert caught.value.diagnostic.diagnostic_id == "SONA-MODULE-003"


def test_lsp_missing_optional_dependency_returns_clean_nonzero(monkeypatch, capsys):
    import sona.lsp_server as lsp

    monkeypatch.setattr(lsp, "_PYGLS_AVAILABLE", False)
    assert lsp.main([]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "pygls is required" in captured.err
    assert "Traceback" not in captured.err

