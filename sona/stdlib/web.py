"""Web utilities for Sona programs."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode, urljoin

try:  # pragma: no cover
    from . import native_http  # type: ignore
except ImportError:  # pragma: no cover
    import native_http  # type: ignore


def fetch(
    url: str,
    method: str = "GET",
    data: Any | None = None,
    **kwargs: Any,
) -> Any:
    verb = method.upper()
    if verb == "GET":
        return native_http.http_get(url, **kwargs)
    if verb == "POST":
        return native_http.http_post(url, data=data, **kwargs)
    raise ValueError(f"Unsupported method: {method}")


def build_url(
    base: str,
    path: str = "",
    params: dict[str, Any] | None = None,
) -> str:
    url = urljoin(base, path)
    if params:
        return f"{url}?{urlencode(params)}"
    return url


def encode_params(params: dict[str, Any]) -> str:
    return urlencode(params)


__all__ = ["fetch", "build_url", "encode_params"]
