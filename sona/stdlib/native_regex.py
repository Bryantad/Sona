"""Native glue exposing :mod:`sona.stdlib.regex` helpers to Sona."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping

from . import regex as _regex


def _normalize_options(options: Any) -> Mapping[str, Any] | None:
    if options is None:
        return None
    if isinstance(options, dict):
        return options
    if isinstance(options, MutableMapping):
        return dict(options)
    if hasattr(options, "items"):
        return dict(options.items())
    raise TypeError("options must be a mapping if provided")


def regex_compile(pattern: Any, options: Any = None) -> _regex.RegexHandle:
    return _regex.compile(pattern, _normalize_options(options))


def regex_match(
    pattern: Any,
    text: Any,
    *,
    options: Any = None,
) -> dict[str, Any]:
    return _regex.match(pattern, text, options=_normalize_options(options))


def regex_fullmatch(
    pattern: Any,
    text: Any,
    *,
    options: Any = None,
) -> dict[str, Any]:
    return _regex.fullmatch(pattern, text, options=_normalize_options(options))


def regex_search(
    pattern: Any,
    text: Any,
    *,
    options: Any = None,
) -> dict[str, Any]:
    return _regex.search(pattern, text, options=_normalize_options(options))


def regex_test(
    pattern: Any,
    text: Any,
    *,
    options: Any = None,
) -> bool:
    return _regex.test(pattern, text, options=_normalize_options(options))


def regex_find_all(
    pattern: Any,
    text: Any,
    *,
    options: Any = None,
) -> list[Any]:
    return _regex.find_all(pattern, text, options=_normalize_options(options))


def regex_replace(
    pattern: Any,
    text: Any,
    replacement: Any,
    *,
    count: int | None = None,
    options: Any = None,
) -> str:
    return _regex.replace(
        pattern,
        text,
        replacement,
        count=count,
        options=_normalize_options(options),
    )


def regex_replace_callback(
    pattern: Any,
    text: Any,
    callback: Any,
    *,
    options: Any = None,
) -> str:
    return _regex.replace_callback(
        pattern,
        text,
        callback,
        options=_normalize_options(options),
    )


def regex_split(
    pattern: Any,
    text: Any,
    *,
    maxsplit: int | None = None,
    options: Any = None,
) -> list[str]:
    return _regex.split(
        pattern,
        text,
        maxsplit=maxsplit,
        options=_normalize_options(options),
    )


def regex_escape(text: Any) -> str:
    return _regex.escape(text)


__all__ = [
    "regex_compile",
    "regex_match",
    "regex_fullmatch",
    "regex_search",
    "regex_test",
    "regex_find_all",
    "regex_replace",
    "regex_replace_callback",
    "regex_split",
    "regex_escape",
]
