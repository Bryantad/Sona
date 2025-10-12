"""Input validation helpers."""
from __future__ import annotations

import re
from urllib.parse import urlparse

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def is_email(value: str) -> bool:
    return bool(EMAIL_REGEX.match(value))


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and parsed.netloc)


def ensure_non_empty(value: str, *, field: str = "value") -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field} must not be empty")
    return cleaned


__all__ = ["is_email", "is_url", "ensure_non_empty"]
