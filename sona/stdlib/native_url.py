"""Native backing for public URL helpers."""

from __future__ import annotations

from urllib.parse import parse_qs, quote, unquote, urlencode, urljoin, urlparse, urlunparse
from typing import Any


def url_parse(value: Any) -> dict[str, Any]:
    parsed = urlparse(str(value))
    return {
        "scheme": parsed.scheme,
        "host": parsed.netloc,
        "path": parsed.path,
        "params": parsed.params,
        "query": parse_qs(parsed.query) if parsed.query else {},
        "fragment": parsed.fragment,
    }


def url_build(parts: Any) -> str:
    if not isinstance(parts, dict):
        raise ValueError("url.build expects a map")
    query = parts.get("query", "")
    query_string = urlencode(query, doseq=True) if isinstance(query, dict) else str(query or "")
    return urlunparse((
        str(parts.get("scheme", "http")),
        str(parts.get("host", parts.get("netloc", ""))),
        str(parts.get("path", "")),
        str(parts.get("params", "")),
        query_string,
        str(parts.get("fragment", "")),
    ))


def url_encode(value: Any) -> str:
    return quote(str(value))


def url_decode(value: Any) -> str:
    return unquote(str(value))


def url_query_encode(mapping: Any) -> str:
    if not isinstance(mapping, dict):
        raise ValueError("url.query_encode expects a map")
    return urlencode(mapping, doseq=True)


def url_query_decode(value: Any) -> dict[str, list[str]]:
    return parse_qs(str(value), keep_blank_values=True)


def url_join(base: Any, relative: Any) -> str:
    return urljoin(str(base), str(relative))


__all__ = [
    "url_parse",
    "url_build",
    "url_encode",
    "url_decode",
    "url_query_encode",
    "url_query_decode",
    "url_join",
]
