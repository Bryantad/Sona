"""HTTP client helpers used by the high level ``http`` module."""

from __future__ import annotations

import json
from typing import Any
from urllib import error, request


def _decode_response(body: bytes, content_type: str) -> str | dict[str, Any]:
    text = body.decode("utf-8", errors="replace")
    if "application/json" in content_type:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    return text


def http_get(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 10,
) -> Any:
    req = request.Request(url, headers=headers or {}, method="GET")
    try:
        with request.urlopen(  # type: ignore[arg-type]
            req,
            timeout=timeout,
        ) as resp:
            content_type = resp.headers.get("Content-Type", "")
            return _decode_response(resp.read(), content_type)
    except error.URLError as exc:
        return {"error": str(exc)}


def http_post(
    url: str,
    data: Any | None = None,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 10,
) -> Any:
    payload: bytes | None = None
    request_headers = headers.copy() if headers else {}
    if data is not None:
        if isinstance(data, (dict, list)):
            payload = json.dumps(data).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")
        elif isinstance(data, str):
            payload = data.encode("utf-8")
            request_headers.setdefault(
                "Content-Type",
                "text/plain; charset=utf-8",
            )
        else:
            payload = str(data).encode("utf-8")
            request_headers.setdefault(
                "Content-Type",
                "text/plain; charset=utf-8",
            )

    req = request.Request(
        url,
        data=payload,
        headers=request_headers,
        method="POST",
    )
    try:
        with request.urlopen(  # type: ignore[arg-type]
            req,
            timeout=timeout,
        ) as resp:
            content_type = resp.headers.get("Content-Type", "")
            return _decode_response(resp.read(), content_type)
    except error.URLError as exc:
        return {"error": str(exc)}


__all__ = ["http_get", "http_post"]
