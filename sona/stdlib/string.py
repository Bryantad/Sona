"""Advanced string helpers powering the Sona ``string`` module."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable, Mapping, Optional, Sequence

from . import regex as _regex


_FLAG_MAP = {
    "i": re.IGNORECASE,
    "m": re.MULTILINE,
    "s": re.DOTALL,
    "x": re.VERBOSE,
    "a": re.ASCII,
}


def _ensure_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _parse_flags(flags: Any = None) -> int:
    if not flags:
        return 0
    if isinstance(flags, int):
        return flags
    if isinstance(flags, str):
        value = 0
        for char in flags:
            value |= _FLAG_MAP.get(char.lower(), 0)
        return value
    if isinstance(flags, Iterable):
        value = 0
        for item in flags:
            if isinstance(item, int):
                value |= item
            elif isinstance(item, str):
                value |= _FLAG_MAP.get(item.lower(), 0)
        return value
    raise TypeError("Unsupported flags value")


def _options_from_flags(flags: Any = None) -> dict[str, Any] | None:
    parsed = _parse_flags(flags)
    if parsed == 0:
        return None
    return {"flags": parsed}


def _tokenize_words(value: str) -> list[str]:
    """
    Split text into words handling:
    - Whitespace boundaries
    - camelCase/PascalCase boundaries
    - Non-alphanumeric separators (-, _, etc.)
    
    Examples:
        "hello world" → ["hello", "world"]
        "CamelCaseWord" → ["Camel", "Case", "Word"]
        "foo-bar_baz" → ["foo", "bar", "baz"]
    """
    # First, insert spaces before uppercase letters that follow lowercase/digits
    # This handles camelCase → camel Case
    spaced = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', value)
    
    # Also insert spaces before uppercase sequences followed by lowercase
    # This handles "XMLParser" → "XML Parser"
    spaced = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', spaced)
    
    # Now replace all non-alphanumeric with spaces
    spaced = re.sub(r"[^A-Za-z0-9]+", " ", spaced)
    
    # Split and filter empty
    tokens = [chunk for chunk in spaced.strip().split() if chunk]
    return tokens


def upper(value: Any) -> str:
    return _ensure_text(value).upper()


def lower(value: Any) -> str:
    return _ensure_text(value).lower()


def casefold(value: Any) -> str:
    return _ensure_text(value).casefold()


def capitalize(value: Any) -> str:
    return _ensure_text(value).capitalize()


def title(value: Any) -> str:
    return _ensure_text(value).title()


def swapcase(value: Any) -> str:
    return _ensure_text(value).swapcase()


def repeat(value: Any, count: int) -> str:
    return _ensure_text(value) * max(count, 0)


def trim(value: Any, chars: Optional[str] = None) -> str:
    return _ensure_text(value).strip(chars)


def ltrim(value: Any, chars: Optional[str] = None) -> str:
    return _ensure_text(value).lstrip(chars)


def rtrim(value: Any, chars: Optional[str] = None) -> str:
    return _ensure_text(value).rstrip(chars)


def reverse(value: Any) -> str:
    """
    Reverse a string (Unicode-safe).
    
    Args:
        value: String to reverse (or coercible to string)
        
    Returns:
        Reversed string
        
    Example:
        >>> reverse("hello")
        'olleh'
        >>> reverse("hello 世界")
        '界世 olleh'
    """
    return _ensure_text(value)[::-1]


def ensure_prefix(value: Any, prefix: str) -> str:
    text = _ensure_text(value)
    return text if text.startswith(prefix) else f"{prefix}{text}"


def ensure_suffix(value: Any, suffix: str) -> str:
    text = _ensure_text(value)
    return text if text.endswith(suffix) else f"{text}{suffix}"


def remove_prefix(value: Any, prefix: str) -> str:
    text = _ensure_text(value)
    return text[len(prefix):] if text.startswith(prefix) else text


def remove_suffix(value: Any, suffix: str) -> str:
    text = _ensure_text(value)
    return text[:-len(suffix)] if suffix and text.endswith(suffix) else text


def contains(value: Any, substring: str, *, ignore_case: bool = False) -> bool:
    text = _ensure_text(value)
    needle = _ensure_text(substring)
    if ignore_case:
        return needle.casefold() in text.casefold()
    return needle in text


def startswith(
    value: Any,
    prefix: str | Sequence[str],
    *,
    ignore_case: bool = False,
) -> bool:
    text = _ensure_text(value)
    if not ignore_case:
        return text.startswith(prefix)
    prefixes = (
        tuple(item.casefold() for item in prefix)
        if isinstance(prefix, Sequence) and not isinstance(prefix, str)
        else (_ensure_text(prefix).casefold(),)
    )
    return text.casefold().startswith(prefixes)


def endswith(
    value: Any,
    suffix: str | Sequence[str],
    *,
    ignore_case: bool = False,
) -> bool:
    text = _ensure_text(value)
    if not ignore_case:
        return text.endswith(suffix)
    suffixes = (
        tuple(item.casefold() for item in suffix)
        if isinstance(suffix, Sequence) and not isinstance(suffix, str)
        else (_ensure_text(suffix).casefold(),)
    )
    return text.casefold().endswith(suffixes)


def count(value: Any, substring: str, *, ignore_case: bool = False) -> int:
    text = _ensure_text(value)
    needle = _ensure_text(substring)
    if ignore_case:
        return text.casefold().count(needle.casefold())
    return text.count(needle)


def split(
    value: Any,
    delimiter: Optional[str] = None,
    *,
    maxsplit: int = -1,
    keep_empty: bool = True,
) -> list[str]:
    text = _ensure_text(value)
    parts = text.split(delimiter, maxsplit)
    if keep_empty:
        return parts
    return [segment for segment in parts if segment]


def rsplit(
    value: Any,
    delimiter: Optional[str] = None,
    *,
    maxsplit: int = -1,
) -> list[str]:
    return _ensure_text(value).rsplit(delimiter, maxsplit)


def lines(value: Any, *, keepends: bool = False) -> list[str]:
    return _ensure_text(value).splitlines(keepends)


def words(value: Any) -> list[str]:
    return _tokenize_words(_ensure_text(value))


def join(parts: Iterable[Any], delimiter: str = "") -> str:
    items = [_ensure_text(item) for item in parts]
    return _ensure_text(delimiter).join(items)


def replace(
    value: Any,
    old: str,
    new: str,
    *,
    count: Optional[int] = None,
) -> str:
    text = _ensure_text(value)
    old_text = _ensure_text(old)
    new_text = _ensure_text(new)
    if count is None:
        return text.replace(old_text, new_text)
    return text.replace(old_text, new_text, count)


def replace_many(
    value: Any,
    replacements: Mapping[str, Any],
    *,
    ignore_case: bool = False,
) -> str:
    text = _ensure_text(value)
    if not replacements:
        return text
    mapping = {
        _ensure_text(src): _ensure_text(dst)
        for src, dst in replacements.items()
    }
    if not ignore_case:
        for source, target in mapping.items():
            text = text.replace(source, target)
        return text
    pattern = re.compile(
        "|".join(re.escape(key) for key in mapping.keys()),
        re.IGNORECASE,
    )

    def _replace(match: re.Match[str]) -> str:
        token = match.group(0)
        for key, value in mapping.items():
            if key.casefold() == token.casefold():
                return value
        return token

    return pattern.sub(_replace, text)


def collapse_whitespace(value: Any) -> str:
    text = _ensure_text(value)
    return re.sub(r"\s+", " ", text).strip()


def pad_left(value: Any, width: int, fill: str = " ") -> str:
    fill_char = _ensure_text(fill) or " "
    return _ensure_text(value).rjust(width, fill_char[0])


def pad_right(value: Any, width: int, fill: str = " ") -> str:
    fill_char = _ensure_text(fill) or " "
    return _ensure_text(value).ljust(width, fill_char[0])


def pad_center(value: Any, width: int, fill: str = " ") -> str:
    fill_char = _ensure_text(fill) or " "
    return _ensure_text(value).center(width, fill_char[0])


def truncate(value: Any, length: int, *, suffix: str = "…") -> str:
    text = _ensure_text(value)
    if length <= 0:
        return ""
    if len(text) <= length:
        return text
    slice_len = max(length - len(suffix), 0)
    return f"{text[:slice_len]}{suffix}" if slice_len else suffix[:length]


def is_blank(value: Any) -> bool:
    return collapse_whitespace(value) == ""


def slugify(value: Any, separator: str = "-") -> str:
    text = _ensure_text(value)
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9]+", separator, ascii_text)
    collapsed = re.sub(rf"{re.escape(separator)}+", separator, cleaned)
    return collapsed.strip(separator).lower()


def snake_case(value: Any) -> str:
    tokens = _tokenize_words(_ensure_text(value))
    return "_".join(token.lower() for token in tokens)


def kebab_case(value: Any) -> str:
    tokens = _tokenize_words(_ensure_text(value))
    return "-".join(token.lower() for token in tokens)


def camel_case(value: Any) -> str:
    tokens = _tokenize_words(_ensure_text(value))
    if not tokens:
        return ""
    first, *rest = tokens
    return first.lower() + "".join(token.title() for token in rest)


def pascal_case(value: Any) -> str:
    tokens = _tokenize_words(_ensure_text(value))
    return "".join(token.title() for token in tokens)


def format(
    template: str,
    *args: Any,
    **kwargs: Any,
) -> str:
    return _ensure_text(template).format(*args, **kwargs)


def length(value: Any) -> int:
    return len(_ensure_text(value))


def regex_escape(value: Any) -> str:
    return _regex.escape(value)


def regex_test(
    value: Any,
    pattern: str,
    *,
    flags: Any = None,
) -> bool:
    return _regex.test(pattern, value, options=_options_from_flags(flags))


def regex_match(
    value: Any,
    pattern: str,
    *,
    flags: Any = None,
) -> dict[str, Any]:
    return _regex.match(pattern, value, options=_options_from_flags(flags))


def regex_search(
    value: Any,
    pattern: str,
    *,
    flags: Any = None,
) -> dict[str, Any]:
    return _regex.search(pattern, value, options=_options_from_flags(flags))


def regex_findall(
    value: Any,
    pattern: str,
    *,
    flags: Any = None,
) -> list[Any]:
    return _regex.find_all(pattern, value, options=_options_from_flags(flags))


def regex_replace(
    value: Any,
    pattern: str,
    replacement: str,
    *,
    count: int = 0,
    flags: Any = None,
) -> str:
    return _regex.replace(
        pattern,
        value,
        _ensure_text(replacement),
        count=count,
        options=_options_from_flags(flags),
    )


def regex_split(
    value: Any,
    pattern: str,
    *,
    maxsplit: int = 0,
    flags: Any = None,
) -> list[str]:
    opts = _options_from_flags(flags)
    if opts is None:
        return _regex.split(pattern, value, maxsplit=maxsplit)
    return _regex.split(pattern, value, maxsplit=maxsplit, options=opts)


__all__ = [
    "camel_case",
    "capitalize",
    "casefold",
    "collapse_whitespace",
    "contains",
    "count",
    "endswith",
    "ensure_prefix",
    "ensure_suffix",
    "format",
    "is_blank",
    "join",
    "kebab_case",
    "length",
    "lines",
    "lower",
    "ltrim",
    "pad_center",
    "pad_left",
    "pad_right",
    "pascal_case",
    "regex_escape",
    "regex_findall",
    "regex_match",
    "regex_replace",
    "regex_search",
    "regex_split",
    "regex_test",
    "remove_prefix",
    "remove_suffix",
    "repeat",
    "replace",
    "replace_many",
    "reverse",
    "rsplit",
    "rtrim",
    "slugify",
    "snake_case",
    "split",
    "startswith",
    "swapcase",
    "title",
    "trim",
    "truncate",
    "upper",
    "words",
]
