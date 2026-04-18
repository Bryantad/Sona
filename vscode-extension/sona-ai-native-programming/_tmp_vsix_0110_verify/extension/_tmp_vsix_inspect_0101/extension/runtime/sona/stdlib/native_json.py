"""Native glue exposing :mod:`sona.stdlib.json` helpers to Sona."""

from __future__ import annotations

from typing import Any, Optional

from . import json as _json


def json_loads(
    payload: str,
    *,
    allow_comments: bool = False,
    allow_trailing_commas: bool = False,
    strict: bool = True,
) -> Any:
    return _json.loads(
        payload,
        allow_comments=allow_comments,
        allow_trailing_commas=allow_trailing_commas,
        strict=strict,
    )


def json_parse(
    payload: str,
    *,
    allow_comments: bool = False,
    allow_trailing_commas: bool = False,
    strict: bool = True,
) -> Any:
    return _json.parse(
        payload,
        allow_comments=allow_comments,
        allow_trailing_commas=allow_trailing_commas,
        strict=strict,
    )


def json_load(
    path: str,
    *,
    encoding: str = "utf-8",
    allow_comments: bool = False,
    allow_trailing_commas: bool = False,
    strict: bool = True,
) -> Any:
    return _json.load(
        path,
        encoding=encoding,
        allow_comments=allow_comments,
        allow_trailing_commas=allow_trailing_commas,
        strict=strict,
    )


def json_dumps(
    obj: Any,
    *,
    indent: Optional[int] = None,
    sort_keys: bool = False,
    ensure_ascii: bool = False,
    trailing_newline: bool = False,
) -> str:
    return _json.dumps(
        obj,
        indent=indent,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
        trailing_newline=trailing_newline,
    )


def json_stringify(
    obj: Any,
    *,
    indent: Optional[int] = None,
    sort_keys: bool = False,
    ensure_ascii: bool = False,
    trailing_newline: bool = False,
) -> str:
    return _json.stringify(
        obj,
        indent=indent,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
        trailing_newline=trailing_newline,
    )


def json_dump(
    obj: Any,
    path: str,
    *,
    indent: int = 2,
    sort_keys: bool = False,
    ensure_ascii: bool = False,
    encoding: str = "utf-8",
    newline: str = "\n",
    trailing_newline: bool = True,
) -> None:
    _json.dump(
        obj,
        path,
        indent=indent,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
        encoding=encoding,
        newline=newline,
        trailing_newline=trailing_newline,
    )


def json_pretty(obj: Any) -> str:
    return _json.pretty(obj)


def json_normalize(
    obj: Any,
    *,
    sort_keys: bool = True,
    ensure_ascii: bool = False,
) -> str:
    return _json.normalize(
        obj,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
    )


def json_is_valid(
    payload: str,
    *,
    allow_comments: bool = False,
    allow_trailing_commas: bool = False,
) -> bool:
    return _json.is_valid(
        payload,
        allow_comments=allow_comments,
        allow_trailing_commas=allow_trailing_commas,
    )


def json_validate(
    payload: str,
    *,
    allow_comments: bool = False,
    allow_trailing_commas: bool = False,
) -> dict[str, Any]:
    return _json.validate(
        payload,
        allow_comments=allow_comments,
        allow_trailing_commas=allow_trailing_commas,
    )


def json_merge(*objects: Any, deep: bool = True) -> Any:
    return _json.merge(*objects, deep=deep)


def json_pointer_get(
    value: Any,
    pointer: str,
    default: Any = None,
) -> Any:
    return _json.pointer_get(value, pointer, default)


def json_pointer_set(value: Any, pointer: str, new_value: Any) -> Any:
    return _json.pointer_set(value, pointer, new_value)


__all__ = [
    "json_loads",
    "json_load",
    "json_dumps",
    "json_dump",
    "json_pretty",
    "json_normalize",
    "json_is_valid",
    "json_validate",
    "json_merge",
    "json_pointer_get",
    "json_pointer_set",
]
