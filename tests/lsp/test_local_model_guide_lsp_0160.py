"""Custom asynchronous LSP request for direct local Guide inference."""

from __future__ import annotations

import asyncio

import pytest


def test_local_model_edit_lsp_request_is_registered_and_fails_closed_without_default(
    tmp_path, monkeypatch
):
    pytest.importorskip("pygls")
    from sona import lsp_server

    if not lsp_server._PYGLS_AVAILABLE:
        pytest.skip("pygls is unavailable")
    monkeypatch.setenv("SONA_HOME", str(tmp_path / "sona-home"))
    monkeypatch.setattr(lsp_server, "_guide_profile", lambda _document: None)
    handler = lsp_server.server.lsp.fm._features.get("sona/guide/local_model_edit")
    assert callable(handler)

    try:
        result = asyncio.run(
            handler(
                {
                    "schema_version": 1,
                    "action": "local_model_proposal",
                    "document": "untitled:guide",
                    "source": "print(0);",
                    "instruction": "change the value",
                }
            )
        )
    finally:
        lsp_server._close_local_guide_model()

    assert result["status"] == "unavailable"
    assert result["diagnostic"]["diagnostic_id"] == "SONA-GUIDE-006"
