from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
URI = "file:///sona-lsp-guide-actions-0156.sona"


def _frame(message: dict[str, Any]) -> bytes:
    body = json.dumps(message, separators=(",", ":")).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body


def _parse_frames(payload: bytes) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    position = 0
    while position < len(payload):
        header_end = payload.find(b"\r\n\r\n", position)
        assert header_end >= 0, payload[position:]
        headers = payload[position:header_end].decode("ascii")
        length_header = next(
            line
            for line in headers.split("\r\n")
            if line.lower().startswith("content-length:")
        )
        length = int(length_header.split(":", 1)[1])
        body_start = header_end + 4
        body_end = body_start + length
        assert body_end <= len(payload)
        messages.append(json.loads(payload[body_start:body_end]))
        position = body_end
    return messages


def _request(request_id: int, method: str, params: Any) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params,
    }


def _notification(method: str, params: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "method": method, "params": params}


def _exchange(messages):
    process = subprocess.Popen(
        [sys.executable, "-m", "sona.lsp_server", "--stdio"],
        cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        stdout, stderr = process.communicate(
            b"".join(_frame(message) for message in messages), timeout=20,
        )
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        raise
    decoded_stderr = stderr.decode("utf-8", errors="replace")
    assert process.returncode == 0, decoded_stderr
    assert "Traceback" not in decoded_stderr
    assert URI not in decoded_stderr
    responses = _parse_frames(stdout)
    assert all("error" not in message for message in responses), responses
    return {message["id"]: message for message in responses if "id" in message}


def _apply_versioned_edit(source, version, action):
    """Model an LSP client's version check and UTF-16 TextDocumentEdit application."""
    change, = action["edit"]["documentChanges"]
    if change["textDocument"]["version"] != version:
        raise ValueError("stale document")
    assert change["textDocument"]["uri"] == URI
    lines = source.splitlines(keepends=True)

    def offset(position):
        line = position["line"]
        prefix = lines[line].encode("utf-16-le")[:position["character"] * 2]
        return sum(map(len, lines[:line])) + len(prefix.decode("utf-16-le"))

    edits = [
        (offset(edit["range"]["start"]), offset(edit["range"]["end"]), edit["newText"])
        for edit in change["edits"]
    ]
    for start, end, replacement in sorted(edits, reverse=True):
        source = source[:start] + replacement + source[end:]
    return source


def test_lsp_guide_code_actions_reuse_shared_fix_rules_without_execution():
    source = (
        "import io;\n"
        "let quantity = 3;\n"
        "print(quant);\n"
        "let body = io.read_file(\"in.txt\");\n"
    )
    messages = [
        _request(
            1,
            "initialize",
            {"processId": None, "rootUri": None, "capabilities": {
                "workspace": {"workspaceEdit": {"documentChanges": True}},
            }},
        ),
        _notification("initialized", {}),
        _notification(
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": URI,
                    "languageId": "sona",
                    "version": 1,
                    "text": source,
                }
            },
        ),
        _request(
            2,
            "textDocument/codeAction",
            {
                "textDocument": {"uri": URI},
                "range": {
                    "start": {"line": 2, "character": 6},
                    "end": {"line": 2, "character": 11},
                },
                "context": {
                    "only": ["quickfix"],
                    "diagnostics": [
                        {
                            "range": {
                                "start": {"line": 2, "character": 6},
                                "end": {"line": 2, "character": 11},
                            },
                            "message": "Name 'quant' is not defined.",
                            "severity": 1,
                            "source": "sona",
                            "code": "SONA-RUNTIME-003",
                        }
                    ],
                },
            },
        ),
        _request(
            3,
            "textDocument/codeAction",
            {
                "textDocument": {"uri": URI},
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 3, "character": 35},
                },
                "context": {
                    "only": ["source.fixAll"],
                    "diagnostics": [],
                },
            },
        ),
        _request(4, "shutdown", None),
        _notification("exit", None),
    ]

    by_id = _exchange(messages)

    provider = by_id[1]["result"]["capabilities"]["codeActionProvider"]
    assert set(provider["codeActionKinds"]) >= {"quickfix", "source.fixAll"}

    quickfixes = by_id[2]["result"]
    assert len(quickfixes) == 1
    quickfix = quickfixes[0]
    assert quickfix["kind"] == "quickfix"
    assert quickfix["title"] == "Sona Guide: Rename `quant` to `quantity`"
    assert quickfix["edit"]["documentChanges"][0]["edits"][0] == {
        "range": {
            "start": {"line": 2, "character": 6},
            "end": {"line": 2, "character": 11},
        },
        "newText": "quantity",
    }
    assert quickfix["data"]["source"] == "sona-guide"
    assert quickfix["data"]["stale_protection"] == "document-version"
    assert quickfix["data"]["fix"]["edits"][0]["expected"] == "quant"

    migrations = by_id[3]["result"]
    assert len(migrations) == 1
    migration = migrations[0]
    assert migration["kind"] == "source.fixAll"
    assert migration["data"]["rule_id"] == "guide.stdlib-api-migration"
    replacements = [
        edit["newText"]
        for edit in migration["edit"]["documentChanges"][0]["edits"]
    ]
    assert replacements == ["import fs;\n", "fs.read_text"]
    assert "io.read_file" not in json.dumps(migration["edit"])
    assert _apply_versioned_edit(source, 1, quickfix) == source.replace("print(quant)", "print(quantity)")
    assert _apply_versioned_edit(source, 1, migration) == source.replace(
        "import io;\n", "import io;\nimport fs;\n",
    ).replace("io.read_file", "fs.read_text")
    with pytest.raises(ValueError, match="stale document"):
        _apply_versioned_edit(source + "# changed\n", 2, migration)
    assert by_id[4]["result"] is None


@pytest.mark.parametrize("versioned", [True, False])
def test_migration_edits_preserve_utf16_crlf_and_refresh_after_changes(versioned):
    source = 'import io;\r\nprint("😀"); let body = io.read_file("in.txt");\r\n'
    params = {
        "textDocument": {"uri": URI},
        "range": {"start": {"line": 0, "character": 0}, "end": {"line": 1, "character": 0}},
        "context": {"only": ["source.fixAll"], "diagnostics": []},
    }
    messages = [
        _request(1, "initialize", {"capabilities": {
            "workspace": {"workspaceEdit": {"documentChanges": versioned}},
        }}),
        _notification("initialized", {}),
        _notification("textDocument/didOpen", {"textDocument": {
            "uri": URI, "languageId": "sona", "version": 7, "text": source,
        }}),
        _request(2, "textDocument/codeAction", params),
        _notification("textDocument/didChange", {
            "textDocument": {"uri": URI, "version": 8},
            "contentChanges": [{"text": source.replace("io.read_file", "fs.read_text")}],
        }),
        _request(3, "textDocument/codeAction", params),
        _notification("textDocument/didClose", {"textDocument": {"uri": URI}}),
        _request(4, "textDocument/codeAction", params),
        _request(5, "shutdown", None),
        _notification("exit", None),
    ]
    by_id = _exchange(messages)
    action, = by_id[2]["result"]
    if versioned:
        updated = _apply_versioned_edit(source, 7, action)
        assert updated == source.replace("import io;\r\n", "import io;\r\nimport fs;\r\n").replace(
            "io.read_file", "fs.read_text",
        )
    else:
        assert "edit" not in action
        assert "versioned document edits" in action["disabled"]["reason"]
    assert by_id[3]["result"] == []
    assert by_id[4]["result"] == []


def test_lsp_guide_request_and_hover_share_catalog_with_cli_service():
    from sona.guide.service import guide_request

    payloads = [
        {"schema_version": 1, "action": "diagnostic", "diagnostic_id": "SONA-RUNTIME-003", "options": {"mode": mode}}
        for mode in ("guided", "balanced", "expert")
    ]
    payloads.extend([
        {"schema_version": 1, "action": "diagnostic", "diagnostic": {
            "diagnostic_id": "SONA-RUNTIME-003", "message": "Name 'quant' is not defined.",
            "metadata": {"rule-id": "canonical", "name": "quant"},
        }},
        {"schema_version": 1, "action": "selection", "source": "let values = [1, 2];"},
        {"schema_version": 1, "action": "diagnostic", "diagnostic_id": "not-a-diagnostic"},
        {"schema_version": 1, "action": "concept", "concept_id": "variables"},
        [],
    ])
    messages = [
        _request(1, "initialize", {"capabilities": {}}),
        _notification("initialized", {}),
        *[_request(index, "sona/guide", payload) for index, payload in enumerate(payloads, 2)],
        _notification("textDocument/didOpen", {"textDocument": {
            "uri": URI, "languageId": "sona", "version": 1, "text": "let quantity = 3;\n",
        }}),
        _request(20, "textDocument/hover", {"textDocument": {"uri": URI}, "position": {"line": 0, "character": 1}}),
        _request(21, "textDocument/completion", {"textDocument": {"uri": URI}, "position": {"line": 0, "character": 0}}),
        _notification("workspace/didChangeConfiguration", {"settings": {"sona": {"guide": {"mode": "expert"}}}}),
        _request(22, "textDocument/hover", {"textDocument": {"uri": URI}, "position": {"line": 0, "character": 1}}),
        _request(30, "shutdown", None), _notification("exit", None),
    ]
    by_id = _exchange(messages)
    for index, payload in enumerate(payloads, 2):
        assert by_id[index]["result"] == guide_request(payload)
    concept = guide_request({"schema_version": 1, "action": "concept", "concept_id": "variables"})
    assert by_id[20]["result"]["contents"]["value"] == concept["text"]
    items = by_id[21]["result"]["items"]
    assert next(item for item in items if item["label"] == "let")["documentation"]["value"] == concept["text"]
    expert = guide_request({"schema_version": 1, "action": "concept", "concept_id": "variables", "options": {"mode": "expert"}})
    assert by_id[22]["result"]["contents"]["value"] == expert["text"]
