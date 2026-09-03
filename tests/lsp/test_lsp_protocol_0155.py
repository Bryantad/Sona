from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
URI = "file:///sona-lsp-protocol-0155.sona"


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


def test_stdio_protocol_lifecycle_and_narrow_feature_contract():
    source = """import math as m;
let total = 4;
func double(value) {
    return value + value;
}
print(double(total));
m.sq
print("😀"); let broken = (1;
"""
    messages = [
        _request(
            1,
            "initialize",
            {"processId": None, "rootUri": None, "capabilities": {}},
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
            "textDocument/completion",
            {
                "textDocument": {"uri": URI},
                "position": {"line": 0, "character": 9},
            },
        ),
        _request(
            3,
            "textDocument/completion",
            {
                "textDocument": {"uri": URI},
                "position": {"line": 6, "character": 4},
            },
        ),
        _request(
            4,
            "textDocument/hover",
            {
                "textDocument": {"uri": URI},
                "position": {"line": 5, "character": 9},
            },
        ),
        _request(
            5,
            "textDocument/definition",
            {
                "textDocument": {"uri": URI},
                "position": {"line": 5, "character": 9},
            },
        ),
        _request(
            6,
            "textDocument/documentSymbol",
            {"textDocument": {"uri": URI}},
        ),
        _request(
            7,
            "textDocument/hover",
            {
                "textDocument": {"uri": "file:///not-open.sona"},
                "position": {"line": 0, "character": 0},
            },
        ),
        _notification(
            "textDocument/didChange",
            {
                "textDocument": {"uri": URI, "version": 2},
                "contentChanges": [{"text": "let ready = 1;\n"}],
            },
        ),
        _notification(
            "textDocument/didClose",
            {"textDocument": {"uri": URI}},
        ),
        _request(8, "shutdown", None),
        _notification("exit", None),
    ]

    process = subprocess.Popen(
        [sys.executable, "-m", "sona.lsp_server", "--stdio"],
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate(
        b"".join(_frame(message) for message in messages),
        timeout=20,
    )

    decoded_stderr = stderr.decode("utf-8", errors="replace")
    assert process.returncode == 0, decoded_stderr
    assert "Traceback" not in decoded_stderr
    assert URI not in decoded_stderr

    responses = _parse_frames(stdout)
    assert all("error" not in message for message in responses)
    by_id = {message["id"]: message for message in responses if "id" in message}

    capabilities = by_id[1]["result"]["capabilities"]
    assert capabilities["positionEncoding"] == "utf-16"
    assert capabilities["completionProvider"] == {}
    assert capabilities["hoverProvider"] is True
    assert capabilities["definitionProvider"] is True
    assert capabilities["documentSymbolProvider"] is True
    assert "referencesProvider" not in capabilities
    assert "documentFormattingProvider" not in capabilities
    assert "renameProvider" not in capabilities

    diagnostic_batches = [
        message["params"]["diagnostics"]
        for message in responses
        if message.get("method") == "textDocument/publishDiagnostics"
    ]
    assert diagnostic_batches[0][0]["code"] == "SONA-PARSE-003"
    assert diagnostic_batches[0][0]["range"]["start"] == {
        "line": 7,
        "character": 28,
    }
    assert diagnostic_batches[-2:] == [[], []]

    import_labels = {item["label"] for item in by_id[2]["result"]["items"]}
    member_labels = {item["label"] for item in by_id[3]["result"]["items"]}
    assert "math" in import_labels
    assert "sqrt" in member_labels

    assert "Sona function declaration" in by_id[4]["result"]["contents"]["value"]
    assert by_id[5]["result"] == [
        {
            "uri": URI,
            "range": {
                "start": {"line": 2, "character": 5},
                "end": {"line": 2, "character": 11},
            },
        }
    ]
    assert [symbol["name"] for symbol in by_id[6]["result"]] == [
        "math as m",
        "total",
        "double",
    ]
    assert by_id[7]["result"] is None
    assert by_id[8]["result"] is None

