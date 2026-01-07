r"""Regex helpers for Sona stdlib.

Overview
--------
Thin, predictable wrappers around Python's :mod:`re` with a small convenience
layer:
- Structured results for match/search (matched/match/groups/named/span)
- Simple options mapping (boolean flags, max_matches, optional timeout)
- Compiled handle that can be reused and overridden per-call

Timeouts: explicit, opt-in modes
--------------------------------
Timeouts are disabled by default. If you specify a positive ``timeout_ms``, you
can choose how it is enforced via ``timeout_mode``:

- ``'none'`` (default): Do not enforce timeouts; operations run inline. This is
    the safest, most portable behavior. Setting ``timeout_ms`` without changing
    the mode keeps inline execution (no worker).
- ``'process'``: Enforce timeouts by running the regex in a separate process
    using only primitive arguments (pattern text, flags, text, etc.). On timeout,
    the worker process is torn down by the executor context manager.

An environment variable can set a default mode when no explicit option is
provided: ``SONA_REGEX_TIMEOUT_MODE`` in {``none``, ``process``}. The option
value takes precedence over the environment.

Platform and behavior notes
---------------------------
- Callable replacements are supported in normal (inline) execution, but are not
    supported in ``process`` timeout mode and will raise ``TypeError`` there.
- Bytes/bytearray/memoryview are rejected for ``pattern`` and ``text`` to avoid
    surprising coercion to strings; always pass ``str``.
- The library does not use signals; there is no ``signal.alarm`` path.

Examples
--------
>>> from sona.stdlib import regex
>>> regex.search(r"t(\w+)", "test")
{'matched': True, 'match': 'test', 'groups': ['est'], 'named': {}, 'span': [0, 4]}

>>> h = regex.compile(r"abc", {"case_insensitive": True})
>>> regex.test(h, "ABC")
True

>>> # Inline timeout mode (no worker); useful for consistent behavior
>>> regex.search(r"abc", "xxabcxx", {"timeout_ms": 100, "timeout_mode": "none"})
{'matched': True, 'match': 'abc', 'groups': [], 'named': {}, 'span': [2, 5]}

>>> # Process timeout mode (opt-in) for protecting against pathological patterns
>>> regex.search(r"abc", "xxabcxx", {"timeout_ms": 200, "timeout_mode": "process"})
{'matched': True, 'match': 'abc', 'groups': [], 'named': {}, 'span': [2, 5]}

"""

from __future__ import annotations

from concurrent.futures import (
    ThreadPoolExecutor,
    ProcessPoolExecutor,
    TimeoutError as FuturesTimeoutError,
)
from dataclasses import dataclass
import os
import codecs
from typing import Any, Callable, Iterable, Mapping, TypeVar

import re as _re


class RegexError(ValueError):
    """Base error for regex helpers."""


class RegexCompileError(RegexError):
    """Raised when a pattern fails to compile."""


class RegexTimeoutError(TimeoutError, RegexError):
    """Raised when a regex operation exceeds the allowed timeout."""


class RegexTimeoutUnsupported(RegexError):
    """Raised when a timeout is requested but the configured mode is disabled/unsupported."""


_T = TypeVar("_T")


@dataclass(slots=True, frozen=True)
class RegexOptions:
    flags: int
    timeout_ms: float | None
    max_matches: int | None
    timeout_mode: str | None
    provided: frozenset[str]

    def merged(self, override: "RegexOptions" | None) -> "RegexOptions":
        if override is None or not override.provided:
            return self
        flags = override.flags if "flags" in override.provided else self.flags
        timeout_ms = (
            override.timeout_ms
            if "timeout_ms" in override.provided
            else self.timeout_ms
        )
        max_matches = (
            override.max_matches
            if "max_matches" in override.provided
            else self.max_matches
        )
        timeout_mode = (
            override.timeout_mode if "timeout_mode" in override.provided else self.timeout_mode
        )
        return RegexOptions(
            flags,
            timeout_ms,
            max_matches,
            timeout_mode,
            self.provided | override.provided,
        )


@dataclass(slots=True, frozen=True)
class RegexHandle:
    pattern: str
    options: RegexOptions
    _compiled: _re.Pattern

    def with_options(
        self, override: "RegexOptions" | None
    ) -> tuple[_re.Pattern, RegexOptions]:
        merged = self.options.merged(override)
        if merged.flags == self.options.flags:
            compiled = self._compiled
        else:
            try:
                compiled = _re.compile(self.pattern, merged.flags)
            except _re.error as exc:
                # pragma: no cover - compile should already succeed
                raise RegexCompileError(str(exc)) from exc
        return compiled, merged


_BOOLEAN_FLAG_MAP: dict[str, int] = {
    "case_insensitive": _re.IGNORECASE,
    "multiline": _re.MULTILINE,
    "dotall": _re.DOTALL,
    "ignore_whitespace": _re.VERBOSE,
}


def compile(
    pattern: Any,
    options: Mapping[str, Any] | None = None,
) -> RegexHandle:
    pattern_text = _normalize_pattern_text(_ensure_text(pattern, "pattern"))
    parsed = _parse_options(options)

    try:
        compiled = _re.compile(pattern_text, parsed.flags)
    except _re.error as exc:
        raise RegexCompileError(str(exc)) from exc

    return RegexHandle(pattern_text, parsed, compiled)


def match(
    pattern: RegexHandle | Any,
    text: Any,
    options: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    compiled, resolved = _resolve_pattern(pattern, options)
    text_s = _ensure_text(text, "text")
    if resolved.timeout_ms is None:
        return _format_match(compiled.match(text_s))
    result = _run_with_timeout_mode(
        op="match",
        pattern_text=compiled.pattern,
        flags=compiled.flags,
        text=text_s,
        message="regex match timed out",
        options=resolved,
    )
    return result


def fullmatch(
    pattern: RegexHandle | Any,
    text: Any,
    options: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Explicit full-string match convenience wrapper."""
    return match(pattern, text, options=options)


def search(
    pattern: RegexHandle | Any,
    text: Any,
    options: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    compiled, resolved = _resolve_pattern(pattern, options)
    text_s = _ensure_text(text, "text")
    if resolved.timeout_ms is None:
        return _format_match(compiled.search(text_s))
    result = _run_with_timeout_mode(
        op="search",
        pattern_text=compiled.pattern,
        flags=compiled.flags,
        text=text_s,
        message="regex search timed out",
        options=resolved,
    )
    return result


def test(
    pattern: RegexHandle | Any,
    text: Any,
    options: Mapping[str, Any] | None = None,
) -> bool:
    compiled, resolved = _resolve_pattern(pattern, options)
    text_s = _ensure_text(text, "text")
    if resolved.timeout_ms is None:
        return compiled.search(text_s) is not None
    return _run_with_timeout_mode(
        op="test",
        pattern_text=compiled.pattern,
        flags=compiled.flags,
        text=text_s,
        message="regex test timed out",
        options=resolved,
    )


def find_all(
    pattern: RegexHandle | Any,
    text: Any,
    options: Mapping[str, Any] | None = None,
) -> list[Any]:
    compiled, resolved = _resolve_pattern(pattern, options)
    text_s = _ensure_text(text, "text")
    if resolved.timeout_ms is None:
        matches = compiled.findall(text_s)
        if resolved.max_matches is not None:
            return matches[: resolved.max_matches]
        return matches
    return _run_with_timeout_mode(
        op="find_all",
        pattern_text=compiled.pattern,
        flags=compiled.flags,
        text=text_s,
        max_matches=resolved.max_matches,
        message="regex find_all timed out",
        options=resolved,
    )


def replace(
    pattern: RegexHandle | Any,
    text: Any,
    replacement: Any,
    options: Mapping[str, Any] | None = None,
    *,
    count: int | None = None,
) -> str:
    options, count_from_options = _maybe_pop_int_option(
        options,
        "count",
        _ensure_count,
    )
    if count is None and count_from_options is not None:
        count = count_from_options

    compiled, resolved = _resolve_pattern(pattern, options)
    replace_count = 0 if count is None else _ensure_count(count)
    text_s = _ensure_text(text, "text")
    # Support callable replacement; only disallow when process timeout mode is active
    if callable(replacement):
        if resolved.timeout_ms is not None:
            raise TypeError("callable replacement is not supported when a timeout is requested")
        return compiled.sub(replacement, text_s, count=replace_count)

    repl_s = _normalize_replacement_text(_ensure_text(replacement, "replacement"))
    if resolved.timeout_ms is None:
        return compiled.sub(repl_s, text_s, count=replace_count)
    return _run_with_timeout_mode(
        op="replace",
        pattern_text=compiled.pattern,
        flags=compiled.flags,
        text=text_s,
        replacement=repl_s,
        count=replace_count,
        message="regex replace timed out",
        options=resolved,
    )


def split(
    pattern: RegexHandle | Any,
    text: Any,
    options: Mapping[str, Any] | None = None,
    *,
    maxsplit: int | None = None,
) -> list[str]:
    options, maxsplit_from_options = _maybe_pop_int_option(
        options,
        "maxsplit",
        _ensure_count,
    )
    if maxsplit is None and maxsplit_from_options is not None:
        maxsplit = maxsplit_from_options

    compiled, resolved = _resolve_pattern(pattern, options)
    split_count = 0 if maxsplit is None else _ensure_count(maxsplit)
    text_s = _ensure_text(text, "text")
    if resolved.timeout_ms is None:
        return compiled.split(text_s, maxsplit=split_count)
    return _run_with_timeout_mode(
        op="split",
        pattern_text=compiled.pattern,
        flags=compiled.flags,
        text=text_s,
        maxsplit=split_count,
        message="regex split timed out",
        options=resolved,
    )


def escape(text: Any) -> str:
    return _re.escape(_ensure_text(text, "text"))


def _run_with_timeout(
    func: Callable[[], _T],
    timeout_ms: float | None,
    message: str,
) -> _T:
    # pragma: no cover - this helper is not used by the exported API paths
    if timeout_ms is None:
        return func()
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(func)
    try:
        return future.result(timeout=timeout_ms / 1000.0)
    except FuturesTimeoutError as exc:
        # Do not wait for the worker thread; best-effort cancel
        try:
            future.cancel()
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
        raise RegexTimeoutError(message) from exc
    except Exception:
        # Ensure we clean up the executor on errors
        executor.shutdown(wait=False, cancel_futures=True)
        raise
    else:
        # Normal completion
        executor.shutdown(wait=False, cancel_futures=True)


def _re_worker(
    op: str,
    pattern_text: str,
    flags: int,
    text: str,
    replacement: str | None,
    count: int,
    maxsplit: int,
    max_matches: int | None,
) -> Any:
    comp = _re.compile(pattern_text, flags)  # pragma: no cover (runs in separate process)
    if op == "match":
        return _format_match(comp.match(text))
    if op == "search":
        return _format_match(comp.search(text))
    if op == "test":
        return comp.search(text) is not None
    if op == "find_all":
        results = comp.findall(text)
        if max_matches is not None:
            return results[: max_matches]
        return results
    if op == "replace":
        if replacement is None:
            raise TypeError("replacement must be provided for replace")
        return comp.sub(replacement, text, count=count)
    if op == "split":
        return comp.split(text, maxsplit=maxsplit)
    raise ValueError(f"unknown op: {op}")


def _run_re_with_timeout(
    *,
    op: str,
    pattern_text: str,
    flags: int,
    text: str,
    message: str,
    timeout_ms: float,
    replacement: str | None = None,
    count: int = 0,
    maxsplit: int = 0,
    max_matches: int | None = None,
) -> Any:
    with ProcessPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(
            _re_worker,
            op,
            pattern_text,
            flags,
            text,
            replacement,
            count,
            maxsplit,
            max_matches,
        )
        try:
            return fut.result(timeout=timeout_ms / 1000.0)
        except FuturesTimeoutError as exc:
            # On timeout, processes are terminated when context exits
            raise RegexTimeoutError(message) from exc


def _effective_timeout_mode(options: RegexOptions) -> tuple[str, float]:
    """Return (mode, timeout_ms) where mode is one of 'none' or 'process'.

    Defaults to 'none' unless explicitly enabled via options or env.
    Env var: SONA_REGEX_TIMEOUT_MODE in {none, process}.
    """
    # Determine timeout from options
    timeout_ms = options.timeout_ms if options.timeout_ms is not None else 0.0
    # Resolve mode precedence: explicit option > env > default
    mode = options.timeout_mode
    if not mode:
        mode = os.getenv("SONA_REGEX_TIMEOUT_MODE", "none").strip().lower()
    if mode not in {"none", "process"}:
        mode = "none"
    if timeout_ms <= 0:
        return "none", 0.0
    return mode, timeout_ms


def _run_with_timeout_mode(
    *,
    op: str,
    pattern_text: str,
    flags: int,
    text: str,
    message: str,
    options: RegexOptions,
    replacement: str | None = None,
    count: int = 0,
    maxsplit: int = 0,
    max_matches: int | None = None,
) -> Any:
    mode, timeout_ms = _effective_timeout_mode(options)
    if mode == "none":
        # Timeouts are disabled; run inline without protection
        if op == "match":
            return _format_match(_re.compile(pattern_text, flags).match(text))
        if op == "search":
            return _format_match(_re.compile(pattern_text, flags).search(text))
        if op == "test":
            return _re.compile(pattern_text, flags).search(text) is not None
        if op == "find_all":
            results = _re.compile(pattern_text, flags).findall(text)
            if max_matches is not None:
                return results[: max_matches]
            return results
        if op == "replace":
            if replacement is None:
                raise TypeError("replacement must be provided for replace")
            return _re.compile(pattern_text, flags).sub(replacement, text, count=count)
        if op == "split":
            return _re.compile(pattern_text, flags).split(text, maxsplit=maxsplit)
        raise ValueError(f"unknown op: {op}")

    if mode == "process":
        return _run_re_with_timeout(
            op=op,
            pattern_text=pattern_text,
            flags=flags,
            text=text,
            replacement=replacement,
            count=count,
            maxsplit=maxsplit,
            max_matches=max_matches,
            message=message,
            timeout_ms=timeout_ms,
        )

    # Fallback: unsupported mode requested
    raise RegexTimeoutUnsupported("requested timeout mode is not supported")


def _resolve_pattern(
    pattern: RegexHandle | Any,
    options: Mapping[str, Any] | None,
) -> tuple[_re.Pattern, RegexOptions]:
    override = _parse_options(options)
    if isinstance(pattern, RegexHandle):
        return pattern.with_options(override)

    pattern_text = _normalize_pattern_text(_ensure_text(pattern, "pattern"))
    try:
        compiled = _re.compile(pattern_text, override.flags)
    except _re.error as exc:
        raise RegexCompileError(str(exc)) from exc
    return compiled, override


def _ensure_text(value: Any, label: str) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        raise TypeError(f"{label} cannot be None")
    # Avoid surprising coercion of bytes/bytearray to "b'..'" strings
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise TypeError(f"{label} must be a string")
    return str(value)


def _normalize_pattern_text(value: str) -> str:
    return _decode_escapes(value)


def _normalize_replacement_text(value: str) -> str:
    return _decode_escapes(value)


def _decode_escapes(value: str) -> str:
    if "\\" not in value:
        return value
    try:
        return codecs.decode(value, "unicode_escape")
    except Exception:
        return value


def _ensure_count(value: Any) -> int:
    if isinstance(value, bool):
        raise TypeError("count must be an integer")
    if isinstance(value, int):
        if value < 0:
            raise ValueError("count must be non-negative")
        return value
    raise TypeError("count must be an integer")


def _parse_options(options: Mapping[str, Any] | None) -> RegexOptions:
    if options is None:
        return RegexOptions(0, None, None, None, frozenset())
    if not isinstance(options, Mapping):
        raise TypeError("options must be a mapping")

    flags = 0
    timeout_ms: float | None = None
    max_matches: int | None = None
    timeout_mode: str | None = None
    provided: set[str] = set()

    for key, flag in _BOOLEAN_FLAG_MAP.items():
        if key in options:
            provided.add("flags")
            if _coerce_bool(options[key], key):
                flags |= flag

    if "flags" in options:
        provided.add("flags")
        flags |= _coerce_flags(options["flags"])

    if "timeout_ms" in options:
        provided.add("timeout_ms")
        timeout_ms = _coerce_timeout(options["timeout_ms"])

    if "max_matches" in options:
        provided.add("max_matches")
        max_matches = _coerce_max_matches(options["max_matches"])

    if "timeout_mode" in options:
        provided.add("timeout_mode")
        raw_mode = _ensure_text(options["timeout_mode"], "timeout_mode").strip().lower()
        if raw_mode not in {"none", "process"}:
            raise ValueError("timeout_mode must be 'none' or 'process'")
        timeout_mode = raw_mode

    return RegexOptions(flags, timeout_ms, max_matches, timeout_mode, frozenset(provided))


def _coerce_bool(value: Any, label: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value != 0
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    raise TypeError(f"{label} must be a boolean")


def _coerce_timeout(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError("timeout_ms must be numeric or null")
    if isinstance(value, (int, float)):
        timeout = float(value)
        if timeout <= 0:
            raise ValueError("timeout_ms must be positive")
        return timeout
    raise TypeError("timeout_ms must be numeric or null")


def _coerce_max_matches(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError("max_matches must be a positive integer or null")
    if isinstance(value, int):
        if value <= 0:
            raise ValueError("max_matches must be positive")
        return value
    raise TypeError("max_matches must be a positive integer or null")


def _coerce_flags(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return _flags_from_iterable(value)
    if isinstance(value, Iterable):
        return _flags_from_iterable(value)
    raise TypeError("flags must be int, string, or iterable of flag names")


def _flags_from_iterable(values: Iterable[Any]) -> int:
    result = 0
    for item in values:
        if isinstance(item, str):
            name = item.strip().upper()
            if not name:
                continue
            try:
                result |= getattr(_re, name)
            except AttributeError as exc:
                raise ValueError(f"unknown regex flag: {item}") from exc
        elif isinstance(item, int):
            result |= item
        else:
            raise TypeError("flag entries must be strings or integers")
    return result


def _format_match(match: _re.Match | None) -> dict[str, Any]:
    if match is None:
        return {
            "matched": False,
            "match": None,
            "groups": [],
            "named": {},
            "span": None,
        }
    return {
        "matched": True,
        "match": match.group(0),
        "groups": list(match.groups()),
        "named": match.groupdict(),
        "span": list(match.span()),
    }


def _maybe_pop_int_option(
    options: Mapping[str, Any] | None,
    key: str,
    coerce: Callable[[Any], int],
) -> tuple[Mapping[str, Any] | None, int | None]:
    if options is None or key not in options:
        return options, None

    value = coerce(options[key])
    if hasattr(options, "items"):
        remaining = dict(options.items())
    else:
        remaining = dict(options)
    remaining.pop(key, None)
    return remaining, value


def finditer(
    pattern: RegexHandle | Any,
    text: Any,
    options: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Find all matches and return iterator results as list of match dicts."""

    compiled, resolved = _resolve_pattern(pattern, options)
    text_s = _ensure_text(text, "text")

    results = []
    for match in compiled.finditer(text_s):
        results.append(_format_match(match))

    return results


def extract_groups(
    pattern: RegexHandle | Any,
    text: Any,
    options: Mapping[str, Any] | None = None,
) -> list[tuple]:
    """Extract all captured groups from matches."""

    compiled, resolved = _resolve_pattern(pattern, options)
    text_s = _ensure_text(text, "text")

    return [match.groups() for match in compiled.finditer(text_s)]


def extract_named_groups(
    pattern: RegexHandle | Any,
    text: Any,
    options: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Extract all named groups from matches."""

    compiled, resolved = _resolve_pattern(pattern, options)
    text_s = _ensure_text(text, "text")

    return [match.groupdict() for match in compiled.finditer(text_s)]


def validate_pattern(pattern: Any) -> dict[str, Any]:
    """Validate regex pattern and return diagnostic info."""

    pattern_text = _ensure_text(pattern, "pattern")

    try:
        _re.compile(pattern_text)
        return {
            "valid": True,
            "error": None,
            "pattern": pattern_text
        }
    except _re.error as exc:
        return {
            "valid": False,
            "error": str(exc),
            "pattern": pattern_text
        }


def is_valid_pattern(pattern: Any) -> bool:
    """Check if pattern is valid regex."""

    return validate_pattern(pattern)["valid"]


def replace_callback(
    pattern: RegexHandle | Any,
    text: Any,
    callback: Callable[[_re.Match], str],
    options: Mapping[str, Any] | None = None,
) -> str:
    """Replace matches using callback function."""
    compiled, resolved = _resolve_pattern(pattern, options)
    text_s = _ensure_text(text, "text")

    if resolved.timeout_ms is not None:
        raise TypeError("callback replacement is not supported when a timeout is requested")

    max_count = resolved.max_matches if resolved.max_matches else 0

    return compiled.sub(callback, text_s, count=max_count)


def count_matches(
    pattern: RegexHandle | Any,
    text: Any,
    options: Mapping[str, Any] | None = None,
) -> int:
    """Count number of matches in text."""

    compiled, resolved = _resolve_pattern(pattern, options)
    text_s = _ensure_text(text, "text")

    return len(compiled.findall(text_s))


__all__ = [
    "RegexHandle",
    "RegexError",
    "RegexCompileError",
    "RegexTimeoutError",
    "RegexTimeoutUnsupported",
    "compile",
    "match",
    "fullmatch",
    "search",
    "test",
    "find_all",
    "replace",
    "split",
    "escape",
    "finditer",
    "extract_groups",
    "extract_named_groups",
    "validate_pattern",
    "is_valid_pattern",
    "replace_callback",
    "count_matches",
]
