from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from sona.stdlib.errors import StdlibError
from sona.stdlib.native_http import build_native_bridge


class _Interpreter:
    def __init__(self, root: Path, *, safe: bool = False) -> None:
        self.project_root = root
        self.safe_mode = safe
        self.stdlib_capabilities = None


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):  # noqa: A002
        return

    def _send(self, status: int, body: bytes, **headers: str) -> None:
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Sona-Fixture", "yes")
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _reply(self) -> None:
        if self.path == "/redirect":
            self._send(302, b"", Location="/ok")
            return
        if self.path == "/missing":
            self._send(404, b"missing")
            return
        if self.path == "/large":
            self._send(200, b"x" * 64)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        payload = json.dumps(
            {"method": self.command, "body": body.decode("utf-8")},
            sort_keys=True,
        ).encode("utf-8")
        self._send(200, payload, **{"Content-Type": "application/json"})

    do_GET = _reply
    do_POST = _reply
    do_PUT = _reply
    do_PATCH = _reply
    do_DELETE = _reply
    do_HEAD = _reply


@pytest.fixture()
def http_endpoint():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_http_supports_bounded_verbs_redirects_and_non_2xx(tmp_path, http_endpoint):
    http = build_native_bridge(_Interpreter(tmp_path))

    response = http.http_get(f"{http_endpoint}/ok")
    assert response["status"] == 200
    assert response["ok"] is True
    assert response["headers"]["x-sona-fixture"] == "yes"
    assert json.loads(response["body"])["method"] == "GET"

    for method in ("POST", "PUT", "PATCH", "DELETE"):
        response = http.http_request(method, f"{http_endpoint}/echo", {"body": "sona"})
        assert json.loads(response["body"]) == {"body": "sona", "method": method}

    redirected = http.http_get(f"{http_endpoint}/redirect")
    assert redirected["status"] == 200
    assert redirected["url"].endswith("/ok")

    missing = http.http_get(f"{http_endpoint}/missing")
    assert missing == {
        "status": 404,
        "ok": False,
        "body": "missing",
        "headers": missing["headers"],
        "url": f"{http_endpoint}/missing",
    }


def test_http_json_helpers_and_body_limit(tmp_path, http_endpoint):
    http = build_native_bridge(_Interpreter(tmp_path))
    value = http.http_post_json(f"{http_endpoint}/echo", {"b": 2, "a": 1})
    assert value["method"] == "POST"
    assert json.loads(value["body"]) == {"a": 1, "b": 2}

    with pytest.raises(StdlibError) as caught:
        http.http_get(f"{http_endpoint}/large", {"max_body_bytes": 8})
    assert caught.value.diagnostic.diagnostic_id == "SONA-HTTP-004"
    assert caught.value.code == "E0502"


def test_http_safe_mode_denial_is_stable_and_redacts_url_secrets(tmp_path):
    http = build_native_bridge(_Interpreter(tmp_path, safe=True))
    url = "http://user:password@example.invalid/private?token=secret"
    with pytest.raises(StdlibError) as caught:
        http.http_get(url)

    error = caught.value
    assert error.diagnostic.diagnostic_id == "SONA-HTTP-005"
    assert error.code == "E0600"
    assert error.target == "http://example.invalid/private"
    assert "password" not in error.diagnostic.message
    assert "token" not in error.diagnostic.message
    assert "secret" not in error.diagnostic.message


def test_http_invalid_url_is_a_structured_diagnostic(tmp_path):
    http = build_native_bridge(_Interpreter(tmp_path))
    with pytest.raises(StdlibError) as caught:
        http.http_get("file:///not-http")
    assert caught.value.diagnostic.diagnostic_id == "SONA-HTTP-001"
    assert caught.value.code == "E0501"
