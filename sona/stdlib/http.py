"""High level HTTP helpers for Sona programs."""

from __future__ import annotations

from typing import Any

try:  # pragma: no cover - fallback for standalone imports
    from . import native_http  # type: ignore
except ImportError:  # pragma: no cover
    import native_http  # type: ignore


def get(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 10,
) -> Any:
    return native_http.http_get(url, headers=headers, timeout=timeout)


def post(
    url: str,
    data: Any | None = None,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 10,
) -> Any:
    return native_http.http_post(
        url,
        data=data,
        headers=headers,
        timeout=timeout,
    )


__all__ = ["get", "post"]
