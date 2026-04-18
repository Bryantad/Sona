"""Environment helpers for the Sona standard library ``env`` module."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional


_TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
_FALSE_VALUES = {"0", "false", "f", "no", "n", "off"}


def _ensure_str(value: Any) -> str:
    return "" if value is None else str(value)


def get(key: str, default: Any = None) -> Optional[str]:
    value = os.environ.get(str(key))
    if value is None:
        return default
    return value


def get_bool(key: str, default: Optional[bool] = None) -> Optional[bool]:
    value = os.environ.get(str(key))
    if value is None:
        return default
    candidate = value.strip().lower()
    if candidate in _TRUE_VALUES:
        return True
    if candidate in _FALSE_VALUES:
        return False
    return default


def get_int(key: str, default: Optional[int] = None) -> Optional[int]:
    value = os.environ.get(str(key))
    if value is None:
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


def get_float(key: str, default: Optional[float] = None) -> Optional[float]:
    value = os.environ.get(str(key))
    if value is None:
        return default
    try:
        return float(value.strip())
    except ValueError:
        return default


def exists(key: str) -> bool:
    return str(key) in os.environ


def set(key: str, value: Any) -> str:
    normalized = _ensure_str(value)
    os.environ[str(key)] = normalized
    return normalized


def set_many(
    values: Mapping[str, Any],
    *,
    overwrite: bool = True,
) -> Dict[str, str]:
    applied: Dict[str, str] = {}
    for raw_key, raw_value in values.items():
        key = str(raw_key)
        if not overwrite and key in os.environ:
            continue
        normalized = _ensure_str(raw_value)
        os.environ[key] = normalized
        applied[key] = normalized
    return applied


def delete(key: str) -> bool:
    return os.environ.pop(str(key), None) is not None


def delete_many(keys: Iterable[str]) -> int:
    removed = 0
    for key in keys:
        if delete(key):
            removed += 1
    return removed


def as_dict(
    prefix: Optional[str] = None,
    *,
    lowercase_keys: bool = False,
    strip_prefix: bool = False,
) -> Dict[str, str]:
    snapshot: Dict[str, str] = {}
    for key, value in os.environ.items():
        if prefix and not key.startswith(prefix):
            continue
        mapped = key
        if prefix and strip_prefix and key.startswith(prefix):
            mapped = key[len(prefix):]
        if lowercase_keys:
            mapped = mapped.lower()
        snapshot[mapped] = value
    return snapshot


def keys(prefix: Optional[str] = None) -> list[str]:
    if prefix is None:
        return sorted(os.environ.keys())
    return sorted([key for key in os.environ.keys() if key.startswith(prefix)])


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        unescaped = value[1:-1]
        return (
            unescaped.replace("\\n", "\n")
            .replace("\\r", "\r")
            .replace("\\t", "\t")
        )
    return value


def parse_dotenv(content: str) -> Dict[str, str]:
    parsed: Dict[str, str] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        raw_value = raw_value.strip()
        value = _strip_quotes(raw_value)
        parsed[key] = value
    return parsed


def load_dotenv(
    path: str | os.PathLike[str] = ".env",
    *,
    override: bool = False,
    encoding: str = "utf-8",
) -> Dict[str, str]:
    location = Path(path)
    if not location.exists():
        return {}
    content = location.read_text(encoding=encoding)
    parsed = parse_dotenv(content)
    applied = {}
    for key, value in parsed.items():
        if override or key not in os.environ:
            os.environ[key] = value
            applied[key] = value
    return applied


def save_dotenv(
    path: str | os.PathLike[str],
    values: Mapping[str, Any],
    *,
    sort_keys: bool = True,
    encoding: str = "utf-8",
) -> int:
    target = Path(path)
    if target.parent and not target.parent.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
    items = values.items()
    if sort_keys:
        items = sorted(
            items,
            key=lambda item: str(item[0]),
        )  # type: ignore[assignment]
    lines = []
    for key, value in items:  # type: ignore[assignment]
        normalized_value = _ensure_str(value)
        if (
            any(character.isspace() for character in normalized_value)
            or "#" in normalized_value
        ):
            quoted = '"' + normalized_value.replace('"', '\\"') + '"'
        else:
            quoted = normalized_value
        lines.append(f"{key}={quoted}")
    target.write_text("\n".join(lines) + "\n", encoding=encoding)
    return len(lines)


def refresh(
    source: Mapping[str, Any],
    *,
    overwrite: bool = True,
) -> Dict[str, str]:
    return set_many(source, overwrite=overwrite)


__all__ = [
    "get",
    "get_bool",
    "get_int",
    "get_float",
    "exists",
    "set",
    "set_many",
    "delete",
    "delete_many",
    "as_dict",
    "keys",
    "parse_dotenv",
    "load_dotenv",
    "save_dotenv",
    "refresh",
]
