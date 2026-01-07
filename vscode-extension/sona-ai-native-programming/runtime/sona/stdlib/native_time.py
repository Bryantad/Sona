"""Native glue exposing :mod:`sona.stdlib.time` helpers to Sona."""

from __future__ import annotations

from typing import Optional

from . import time as _time


def time_now(timespec: Optional[str] = None, tz: Optional[str] = None) -> str:
    return _time.now(timespec, tz)


def time_utcnow(timespec: Optional[str] = None) -> str:
    return _time.utcnow(timespec)


def time_timestamp() -> float:
    return _time.timestamp()


def time_from_timestamp(
    value: float,
    timespec: Optional[str] = None,
    tz: Optional[str] = None,
) -> str:
    return _time.from_timestamp(value, timespec, tz)


def time_to_timestamp(value: str, tz: Optional[str] = None) -> float:
    return _time.to_timestamp(value, tz)


def time_parse(
    value: str,
    tz: Optional[str] = None,
    timespec: Optional[str] = "microseconds",
) -> dict:
    return _time.parse(value, tz, timespec)


def time_format_iso(
    value: str,
    timespec: Optional[str] = None,
    tz: Optional[str] = None,
) -> str:
    return _time.format_iso(value, timespec, tz)


def time_to_iso(
    value: str,
    timespec: Optional[str] = None,
    tz: Optional[str] = None,
) -> str:
    return _time.format_iso(value, timespec, tz)


def time_format_pattern(
    value: str,
    pattern: str,
    tz: Optional[str] = None,
) -> str:
    return _time.format_pattern(value, pattern, tz)


def time_format(
    value: str,
    pattern: str,
    tz: Optional[str] = None,
) -> str:
    return _time.format_pattern(value, pattern, tz)


def time_diff(
    start: str,
    end: str,
    unit: str = "seconds",
    absolute: bool = True,
) -> float:
    return _time.diff(start, end, unit, absolute)


def time_shift(value: str, options: Optional[dict] = None) -> str:
    return _time.shift(value, options)


def time_sleep(seconds: float) -> None:
    _time.sleep(seconds)


def time_monotonic() -> float:
    return _time.monotonic()


def time_perf_counter() -> float:
    return _time.perf_counter()


__all__ = [
    "time_now",
    "time_utcnow",
    "time_timestamp",
    "time_from_timestamp",
    "time_to_timestamp",
    "time_parse",
    "time_format_iso",
    "time_to_iso",
    "time_format_pattern",
    "time_format",
    "time_diff",
    "time_shift",
    "time_sleep",
    "time_monotonic",
    "time_perf_counter",
]
