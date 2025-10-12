"""Native glue exposing :mod:`sona.stdlib.string` helpers to Sona."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from . import string as _string


def string_upper(value: Any) -> str:
    return _string.upper(value)


def string_lower(value: Any) -> str:
    return _string.lower(value)


def string_casefold(value: Any) -> str:
    return _string.casefold(value)


def string_capitalize(value: Any) -> str:
    return _string.capitalize(value)


def string_title(value: Any) -> str:
    return _string.title(value)


def string_swapcase(value: Any) -> str:
    return _string.swapcase(value)


def string_repeat(value: Any, count: int) -> str:
    return _string.repeat(value, count)


def string_trim(value: Any, chars: Optional[str] = None) -> str:
    return _string.trim(value, chars)


def string_ltrim(value: Any, chars: Optional[str] = None) -> str:
    return _string.ltrim(value, chars)


def string_rtrim(value: Any, chars: Optional[str] = None) -> str:
    return _string.rtrim(value, chars)


def string_ensure_prefix(value: Any, prefix: str) -> str:
    return _string.ensure_prefix(value, prefix)


def string_ensure_suffix(value: Any, suffix: str) -> str:
    return _string.ensure_suffix(value, suffix)


def string_remove_prefix(value: Any, prefix: str) -> str:
    return _string.remove_prefix(value, prefix)


def string_remove_suffix(value: Any, suffix: str) -> str:
    return _string.remove_suffix(value, suffix)


def string_contains(
    value: Any,
    substring: str,
    ignore_case: bool = False,
) -> bool:
    return _string.contains(value, substring, ignore_case=ignore_case)


def string_startswith(
    value: Any,
    prefix: Any,
    *,
    ignore_case: bool = False,
) -> bool:
    return _string.startswith(value, prefix, ignore_case=ignore_case)


def string_endswith(
    value: Any,
    suffix: Any,
    *,
    ignore_case: bool = False,
) -> bool:
    return _string.endswith(value, suffix, ignore_case=ignore_case)


def string_count(value: Any, substring: str, ignore_case: bool = False) -> int:
    return _string.count(value, substring, ignore_case=ignore_case)


def string_split(
    value: Any,
    delimiter: Optional[str] = None,
    *,
    maxsplit: int = -1,
    keep_empty: bool = True,
) -> list[str]:
    return _string.split(
        value,
        delimiter,
        maxsplit=maxsplit,
        keep_empty=keep_empty,
    )


def string_rsplit(
    value: Any,
    delimiter: Optional[str] = None,
    *,
    maxsplit: int = -1,
) -> list[str]:
    return _string.rsplit(value, delimiter, maxsplit=maxsplit)


def string_lines(value: Any, keepends: bool = False) -> list[str]:
    return _string.lines(value, keepends=keepends)


def string_words(value: Any) -> list[str]:
    return _string.words(value)


def string_join(parts: Iterable[Any], delimiter: str = "") -> str:
    return _string.join(parts, delimiter)


def string_replace(
    value: Any,
    old: str,
    new: str,
    *,
    count: Optional[int] = None,
) -> str:
    return _string.replace(value, old, new, count=count)


def string_replace_many(
    value: Any,
    replacements: Mapping[str, Any],
    *,
    ignore_case: bool = False,
) -> str:
    return _string.replace_many(value, replacements, ignore_case=ignore_case)


def string_collapse_whitespace(value: Any) -> str:
    return _string.collapse_whitespace(value)


def string_pad_left(value: Any, width: int, fill: str = " ") -> str:
    return _string.pad_left(value, width, fill)


def string_pad_right(value: Any, width: int, fill: str = " ") -> str:
    return _string.pad_right(value, width, fill)


def string_pad_center(value: Any, width: int, fill: str = " ") -> str:
    return _string.pad_center(value, width, fill)


def string_truncate(value: Any, length: int, suffix: str = "…") -> str:
    return _string.truncate(value, length, suffix=suffix)


def string_is_blank(value: Any) -> bool:
    return _string.is_blank(value)


def string_slugify(value: Any, separator: str = "-") -> str:
    return _string.slugify(value, separator)


def string_snake_case(value: Any) -> str:
    return _string.snake_case(value)


def string_kebab_case(value: Any) -> str:
    return _string.kebab_case(value)


def string_camel_case(value: Any) -> str:
    return _string.camel_case(value)


def string_pascal_case(value: Any) -> str:
    return _string.pascal_case(value)


def string_format(
    template: str,
    args: Optional[Iterable[Any]] = None,
    kwargs: Optional[Mapping[str, Any]] = None,
) -> str:
    positional = list(args or [])
    keyword_args = dict(kwargs or {})
    return _string.format(template, *positional, **keyword_args)


def string_length(value: Any) -> int:
    return _string.length(value)


def string_regex_escape(value: Any) -> str:
    return _string.regex_escape(value)


def string_regex_test(value: Any, pattern: str, flags: Any = None) -> bool:
    return _string.regex_test(value, pattern, flags=flags)


def string_regex_match(
    value: Any,
    pattern: str,
    flags: Any = None,
) -> dict[str, Any]:
    return _string.regex_match(value, pattern, flags=flags)


def string_regex_search(
    value: Any,
    pattern: str,
    flags: Any = None,
) -> dict[str, Any]:
    return _string.regex_search(value, pattern, flags=flags)


def string_regex_findall(
    value: Any,
    pattern: str,
    flags: Any = None,
) -> list[Any]:
    return _string.regex_findall(value, pattern, flags=flags)


def string_regex_replace(
    value: Any,
    pattern: str,
    replacement: str,
    *,
    count: int = 0,
    flags: Any = None,
) -> str:
    return _string.regex_replace(
        value,
        pattern,
        replacement,
        count=count,
        flags=flags,
    )


def string_regex_split(
    value: Any,
    pattern: str,
    *,
    maxsplit: int = 0,
    flags: Any = None,
) -> list[str]:
    return _string.regex_split(
        value,
        pattern,
        maxsplit=maxsplit,
        flags=flags,
    )


__all__ = [
    "string_upper",
    "string_lower",
    "string_casefold",
    "string_capitalize",
    "string_title",
    "string_swapcase",
    "string_repeat",
    "string_trim",
    "string_ltrim",
    "string_rtrim",
    "string_ensure_prefix",
    "string_ensure_suffix",
    "string_remove_prefix",
    "string_remove_suffix",
    "string_contains",
    "string_startswith",
    "string_endswith",
    "string_count",
    "string_split",
    "string_rsplit",
    "string_lines",
    "string_words",
    "string_join",
    "string_replace",
    "string_replace_many",
    "string_collapse_whitespace",
    "string_pad_left",
    "string_pad_right",
    "string_pad_center",
    "string_truncate",
    "string_is_blank",
    "string_slugify",
    "string_snake_case",
    "string_kebab_case",
    "string_camel_case",
    "string_pascal_case",
    "string_format",
    "string_length",
    "string_regex_escape",
    "string_regex_test",
    "string_regex_match",
    "string_regex_search",
    "string_regex_findall",
    "string_regex_replace",
    "string_regex_split",
]
