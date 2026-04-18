"""Native bindings exposing :mod:`sona.stdlib.env` helpers to Sona."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Optional

from . import env as _env


def env_get(key: str, default: Optional[str] = None) -> Optional[str]:
    return _env.get(key, default)


def env_get_bool(key: str, default: Optional[bool] = None) -> Optional[bool]:
    return _env.get_bool(key, default)


def env_get_int(key: str, default: Optional[int] = None) -> Optional[int]:
    return _env.get_int(key, default)


def env_get_float(
    key: str,
    default: Optional[float] = None,
) -> Optional[float]:
    return _env.get_float(key, default)


def env_exists(key: str) -> bool:
    return _env.exists(key)


def env_has(key: str) -> bool:
    return _env.exists(key)


def env_set(key: str, value: Any) -> str:
    return _env.set(key, value)


def env_set_many(
    values: Mapping[str, Any],
    overwrite: bool = True,
) -> Dict[str, str]:
    return _env.set_many(values, overwrite=overwrite)


def env_delete(key: str) -> bool:
    return _env.delete(key)


def env_delete_many(keys: Iterable[str]) -> int:
    return _env.delete_many(keys)


def env_as_dict(
    prefix: Optional[str] = None,
    lowercase_keys: bool = False,
    strip_prefix: bool = False,
) -> Dict[str, str]:
    return _env.as_dict(
        prefix,
        lowercase_keys=lowercase_keys,
        strip_prefix=strip_prefix,
    )


def env_keys(prefix: Optional[str] = None) -> list[str]:
    return _env.keys(prefix)


def env_parse_dotenv(content: str) -> Dict[str, str]:
    return _env.parse_dotenv(content)


def env_load_dotenv(
    path: str = ".env",
    override: bool = False,
    encoding: str = "utf-8",
) -> Dict[str, str]:
    return _env.load_dotenv(path, override=override, encoding=encoding)


def env_save_dotenv(
    path: str,
    values: Mapping[str, Any],
    sort_keys: bool = True,
    encoding: str = "utf-8",
) -> int:
    return _env.save_dotenv(
        path,
        values,
        sort_keys=sort_keys,
        encoding=encoding,
    )


def env_refresh(
    source: Mapping[str, Any],
    overwrite: bool = True,
) -> Dict[str, str]:
    return _env.refresh(source, overwrite=overwrite)


__all__ = [
    "env_get",
    "env_get_bool",
    "env_get_int",
    "env_get_float",
    "env_exists",
    "env_has",
    "env_set",
    "env_set_many",
    "env_delete",
    "env_delete_many",
    "env_as_dict",
    "env_keys",
    "env_parse_dotenv",
    "env_load_dotenv",
    "env_save_dotenv",
    "env_refresh",
]
