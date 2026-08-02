"""Governance-aware HTTP transport for the public ``http`` module."""

from __future__ import annotations

import json as _json
import socket
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .errors import StdlibError
from .runtime_context import StdlibRuntimeContext


DEFAULT_TIMEOUT = 10.0
DEFAULT_MAX_BODY_BYTES = 10 * 1024 * 1024
_OPTION_KEYS = {
    "timeout",
    "headers",
    "body",
    "json",
    "follow_redirects",
    "max_body_bytes",
}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class _BoundHTTP:
    def __init__(self, interpreter=None) -> None:
        self.context = StdlibRuntimeContext(interpreter)

    @staticmethod
    def _options(
        method: str,
        options: Any = None,
        *,
        legacy_json: Any = None,
        legacy_timeout: Any = None,
        legacy_headers: Any = None,
    ) -> dict[str, Any]:
        if isinstance(options, dict) and (_OPTION_KEYS & set(options)):
            result = dict(options)
        elif method in {"POST", "PUT", "PATCH"} and options is not None:
            result = {"body": options}
        elif options is not None and not isinstance(options, dict):
            result = {"timeout": options}
        else:
            result = {}
        if legacy_json is not None:
            result["json"] = legacy_json
        if legacy_timeout is not None:
            result["timeout"] = legacy_timeout
        if legacy_headers is not None:
            result["headers"] = legacy_headers
        return result

    def _request(self, method: str, url: object, options: dict[str, Any]) -> dict[str, Any]:
        self.context.require("network", f"http.{method.lower()}", url)
        try:
            parts = urlsplit(str(url))
        except (TypeError, ValueError) as error:
            raise self._invalid(method, url, "URL could not be parsed", error) from error
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            raise self._invalid(method, url, "URL must use http or https and include a host")

        try:
            timeout = float(options.get("timeout", DEFAULT_TIMEOUT))
            max_body = int(options.get("max_body_bytes", DEFAULT_MAX_BODY_BYTES))
        except (TypeError, ValueError) as error:
            raise self._invalid(method, url, "timeout and max_body_bytes must be numeric", error) from error
        if timeout <= 0 or max_body <= 0:
            raise self._invalid(method, url, "timeout and max_body_bytes must be positive")

        headers = options.get("headers") or {}
        if not isinstance(headers, dict):
            raise self._invalid(method, url, "headers must be a map")
        request_headers = {str(key): str(value) for key, value in headers.items()}
        body_value = options.get("body")
        json_value = options.get("json")
        if body_value is not None and json_value is not None:
            raise self._invalid(method, url, "body and json are mutually exclusive")
        if json_value is not None:
            try:
                body = _json.dumps(json_value, ensure_ascii=False, sort_keys=True).encode("utf-8")
            except (TypeError, ValueError) as error:
                raise self._invalid(method, url, "json body is not serializable", error) from error
            request_headers.setdefault("Content-Type", "application/json")
        elif body_value is None:
            body = None
        elif isinstance(body_value, bytes):
            body = body_value
        elif isinstance(body_value, list) and all(isinstance(item, int) for item in body_value):
            try:
                body = bytes(body_value)
            except ValueError as error:
                raise self._invalid(method, url, "body byte values must be between 0 and 255", error) from error
        else:
            body = str(body_value).encode("utf-8")

        request = urllib.request.Request(
            str(url), data=body, headers=request_headers, method=method
        )
        opener = (
            urllib.request.build_opener()
            if bool(options.get("follow_redirects", True))
            else urllib.request.build_opener(_NoRedirect())
        )
        try:
            with opener.open(request, timeout=timeout) as response:
                return self._response(response, max_body)
        except urllib.error.HTTPError as response:
            return self._response(response, max_body)
        except (TimeoutError, socket.timeout) as error:
            raise StdlibError(
                "SONA-HTTP-002",
                "HTTP request timed out",
                operation=f"http.{method.lower()}",
                target=url,
                suggestion="Increase the timeout or verify that the endpoint is responsive.",
                is_url=True,
                cause=error,
            ) from error
        except urllib.error.URLError as error:
            if isinstance(getattr(error, "reason", None), (TimeoutError, socket.timeout)):
                raise StdlibError(
                    "SONA-HTTP-002",
                    "HTTP request timed out",
                    operation=f"http.{method.lower()}",
                    target=url,
                    suggestion="Increase the timeout or verify that the endpoint is responsive.",
                    is_url=True,
                    cause=error,
                ) from error
            raise StdlibError(
                "SONA-HTTP-003",
                "HTTP transport failed",
                operation=f"http.{method.lower()}",
                target=url,
                suggestion="Check DNS, TLS, proxy, and endpoint availability.",
                is_url=True,
                cause=error,
            ) from error

    @staticmethod
    def _invalid(method: str, url: object, message: str, cause=None) -> StdlibError:
        return StdlibError(
            "SONA-HTTP-001",
            message,
            operation=f"http.{method.lower()}",
            target=url,
            suggestion="Pass a valid URL and HTTP options map.",
            is_url=True,
            cause=cause,
        )

    @staticmethod
    def _response(response, max_body: int) -> dict[str, Any]:
        payload = response.read(max_body + 1)
        if len(payload) > max_body:
            raise StdlibError(
                "SONA-HTTP-004",
                "HTTP response exceeded max_body_bytes",
                operation="http.response",
                target=response.geturl(),
                suggestion="Increase max_body_bytes only for a trusted endpoint.",
                is_url=True,
            )
        try:
            body = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise StdlibError(
                "SONA-HTTP-004",
                "HTTP response body is not valid UTF-8",
                operation="http.response",
                target=response.geturl(),
                suggestion="Use an endpoint that returns UTF-8 text.",
                is_url=True,
                cause=error,
            ) from error
        status = int(getattr(response, "status", getattr(response, "code", 0)))
        return {
            "status": status,
            "ok": 200 <= status < 300,
            "body": body,
            "headers": {str(key).lower(): str(value) for key, value in response.headers.items()},
            "url": str(response.geturl()),
        }

    def http_get(self, url, options=None, headers=None, max_retries=None, retry_delay=None):
        return self._request("GET", url, self._options("GET", options, legacy_headers=headers))

    def http_post(self, url, options=None, json=None, timeout=None, headers=None, max_retries=None, retry_delay=None):
        return self._request("POST", url, self._options("POST", options, legacy_json=json, legacy_timeout=timeout, legacy_headers=headers))

    def http_put(self, url, options=None, json=None, timeout=None, headers=None):
        return self._request("PUT", url, self._options("PUT", options, legacy_json=json, legacy_timeout=timeout, legacy_headers=headers))

    def http_patch(self, url, options=None, json=None, timeout=None, headers=None):
        return self._request("PATCH", url, self._options("PATCH", options, legacy_json=json, legacy_timeout=timeout, legacy_headers=headers))

    def http_delete(self, url, options=None, headers=None):
        return self._request("DELETE", url, self._options("DELETE", options, legacy_headers=headers))

    def http_head(self, url, options=None, headers=None):
        return self._request("HEAD", url, self._options("HEAD", options, legacy_headers=headers))

    def http_request(self, method, url, options=None):
        return self._request(str(method).upper(), url, self._options(str(method).upper(), options))

    def http_get_json(self, url, options=None):
        response = self.http_get(url, options)
        try:
            return _json.loads(response["body"])
        except (TypeError, ValueError) as error:
            raise StdlibError(
                "SONA-JSON-001",
                "HTTP response was not valid JSON",
                operation="http.get_json",
                target=url,
                suggestion="Verify that the endpoint returns JSON.",
                is_url=True,
                cause=error,
            ) from error

    def http_post_json(self, url, value=None, options=None):
        merged = dict(options or {})
        merged["json"] = value
        response = self.http_post(url, merged)
        try:
            return _json.loads(response["body"])
        except (TypeError, ValueError) as error:
            raise StdlibError(
                "SONA-JSON-001",
                "HTTP response was not valid JSON",
                operation="http.post_json",
                target=url,
                suggestion="Verify that the endpoint returns JSON.",
                is_url=True,
                cause=error,
            ) from error

    def http_download(self, url, filename, options=None):
        target = self.context.resolve_path(filename, write=True, operation="http.download")
        response = self.http_get(url, options)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(response["body"], encoding="utf-8")
        return target.as_posix()

    def http_upload(self, url, filename, options=None):
        source = self.context.resolve_path(filename, write=False, operation="http.upload")
        merged = dict(options or {})
        merged["body"] = source.read_bytes()
        return self.http_post(url, merged)


def build_native_bridge(interpreter):
    return _BoundHTTP(interpreter)


_default = _BoundHTTP()
http_get = _default.http_get
http_post = _default.http_post
http_put = _default.http_put
http_patch = _default.http_patch
http_delete = _default.http_delete
http_head = _default.http_head
http_request = _default.http_request
http_get_json = _default.http_get_json
http_post_json = _default.http_post_json
http_download = _default.http_download
http_upload = _default.http_upload


__all__ = [
    "http_get",
    "http_post",
    "http_put",
    "http_patch",
    "http_delete",
    "http_head",
    "http_request",
    "http_get_json",
    "http_post_json",
    "http_download",
    "http_upload",
    "build_native_bridge",
]
