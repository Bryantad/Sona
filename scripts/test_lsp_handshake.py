"""Minimal stdio LSP handshake test for Sona.

Runs the LSP server as a subprocess, sends initialize/initialized/shutdown/exit,
and asserts it responds and exits.

Usage (Windows PowerShell):
    .venv/Scripts/python.exe scripts/test_lsp_handshake.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


def _encode_lsp(payload: dict) -> bytes:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    return header + body


def _read_exact(stream, n: int) -> bytes:
    data = b""
    while len(data) < n:
        chunk = stream.read(n - len(data))
        if not chunk:
            raise RuntimeError("Unexpected EOF while reading")
        data += chunk
    return data


def _read_message(stream) -> dict:
    # Read headers
    content_length: int | None = None
    while True:
        line = stream.readline()
        if not line:
            raise RuntimeError("Unexpected EOF while reading headers")
        if line in (b"\r\n", b"\n"):
            break
        lower = line.decode("ascii", errors="ignore").strip().lower()
        if lower.startswith("content-length:"):
            content_length = int(lower.split(":", 1)[1].strip())

    if content_length is None:
        raise RuntimeError("Missing Content-Length header")

    body = _read_exact(stream, content_length)
    return json.loads(body.decode("utf-8"))


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]

    # Use the currently running interpreter (expected: workspace .venv)
    cmd = [sys.executable, "-m", "sona.lsp_server", "--stdio"]

    proc = subprocess.Popen(
        cmd,
        cwd=str(repo_root),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert proc.stdin is not None
    assert proc.stdout is not None

    try:
        # initialize
        proc.stdin.write(
            _encode_lsp(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "processId": None,
                        "rootUri": repo_root.as_uri(),
                        "capabilities": {},
                    },
                }
            )
        )
        proc.stdin.flush()

        msg = _read_message(proc.stdout)
        if msg.get("id") != 1 or "result" not in msg:
            raise RuntimeError(f"Unexpected initialize response: {msg}")

        # initialized notification
        proc.stdin.write(
            _encode_lsp(
                {
                    "jsonrpc": "2.0",
                    "method": "initialized",
                    "params": {},
                }
            )
        )
        proc.stdin.flush()

        # shutdown
        proc.stdin.write(
            _encode_lsp(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "shutdown",
                    "params": None,
                }
            )
        )
        proc.stdin.flush()

        msg = _read_message(proc.stdout)
        if msg.get("id") != 2:
            raise RuntimeError(f"Unexpected shutdown response: {msg}")

        # exit notification
        proc.stdin.write(
            _encode_lsp(
                {
                    "jsonrpc": "2.0",
                    "method": "exit",
                    "params": None,
                }
            )
        )
        proc.stdin.flush()

        # Wait for graceful exit
        deadline = time.time() + 5
        while time.time() < deadline:
            code = proc.poll()
            if code is not None:
                if code != 0:
                    stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
                    raise RuntimeError(f"LSP exited with {code}. stderr:\n{stderr}")
                print("OK: LSP initialize/shutdown handshake succeeded")
                return 0
            time.sleep(0.05)

        raise RuntimeError("Timed out waiting for LSP to exit")

    finally:
        if proc.poll() is None:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
