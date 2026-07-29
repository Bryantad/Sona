"""Shared deterministic secret redaction."""
from __future__ import annotations

import re
from typing import Any

_KEY = re.compile(
    r"(?i)(?:^credential$|(?:^|[_-])(api[_-]?key|authorization|password|secret|"
    r"(?:access|refresh|id|auth)[_-]?token|token)$)"
)
_VALUE = re.compile(
    r"(?i)\b(bearer\s+\S+|(?:api[_-]?key|password|secret|token)\s*[:=]\s*[^\s,;]+)"
)


def redact_text(value: str) -> str:
    return _VALUE.sub("[redacted]", str(value))


def is_sensitive_key(key: str) -> bool:
    return bool(_KEY.search(str(key)))


def redact(value: Any, *, key: str = "") -> Any:
    if key and is_sensitive_key(key):
        return "[redacted]"
    if isinstance(value, dict):
        return {str(k): redact(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value
