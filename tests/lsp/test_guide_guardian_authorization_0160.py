"""LSP independently checks the exact live document, selection and proposal."""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

import pytest


def test_lsp_prepare_and_consume_require_live_exact_local_sona_document(tmp_path, monkeypatch):
    pytest.importorskip("pygls")
    from sona import lsp_server

    if not lsp_server._PYGLS_AVAILABLE:
        pytest.skip("pygls is unavailable")
    root = tmp_path / "project"
    root.mkdir()
    (root / "app.sona").write_text("print(1);\n", encoding="utf-8")
    uri = (root / "app.sona").as_uri()
    source = "print(1);\n"
    document = SimpleNamespace(version=9, source=source)
    workspace = SimpleNamespace(folders=[], root_uri=root.as_uri(), text_documents={uri: document})
    monkeypatch.setattr(lsp_server.server.lsp, "_workspace", workspace)
    request = {
        "schema_version": 1,
        "document": uri,
        "document_version": 9,
        "selection": {"start": {"line": 0, "character": 6}, "end": {"line": 0, "character": 7}},
        "expected_source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "proposed_source": "print(2);\n",
        "replacement": "2",
    }

    prepared = lsp_server._guide_buffer_edit(request, consume=False)
    assert prepared["status"] == "prepared"
    assert prepared["effect"] == "EDITOR.BUFFER_REPLACE"
    consumed = lsp_server._guide_buffer_edit(
        {**request, "handle": prepared["handle"]}, consume=True
    )
    assert consumed["status"] == "authorized"

    prepared = lsp_server._guide_buffer_edit(request, consume=False)
    document.version = 10
    stale = lsp_server._guide_buffer_edit({**request, "handle": prepared["handle"]}, consume=True)
    assert stale["status"] == "denied"
    assert stale["diagnostic_id"] == "SONA-GUIDE-003"

    document.version = 9
    wrong_selection = {
        **request,
        "selection": {"start": {"line": 0, "character": 5}, "end": request["selection"]["end"]},
    }
    mismatch = lsp_server._guide_buffer_edit(wrong_selection, consume=False)
    assert mismatch["status"] == "denied"
    assert mismatch["diagnostic_id"] == "SONA-GUIDE-AUTH-SELECTION-MISMATCH"

    untitled = "untitled:guide"
    workspace.text_documents[untitled] = SimpleNamespace(version=9, source=source)
    rejected = lsp_server._guide_buffer_edit({**request, "document": untitled}, consume=False)
    assert rejected["status"] == "denied"
    assert rejected["diagnostic_id"] == "SONA-GUIDE-AUTH-LOCAL-WORKSPACE-REQUIRED"

    python_uri = (root / "notes.py").as_uri()
    workspace.text_documents[python_uri] = SimpleNamespace(version=9, source=source)
    rejected = lsp_server._guide_buffer_edit({**request, "document": python_uri}, consume=False)
    assert rejected["status"] == "denied"
    assert rejected["diagnostic_id"] == "SONA-GUIDE-AUTH-SONA-DOCUMENT-REQUIRED"
