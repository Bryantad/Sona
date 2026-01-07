"""Native glue exposing :mod:`sona.stdlib.date` helpers to Sona."""

from __future__ import annotations

from typing import Iterable, Optional

from . import date as _date


def date_today(tz: Optional[str] = None) -> str:
    return _date.today(tz)


def date_year(value: str, tz: Optional[str] = None) -> int:
    return _date.year(value, tz)


def date_month(value: str, tz: Optional[str] = None) -> int:
    return _date.month(value, tz)


def date_day(value: str, tz: Optional[str] = None) -> int:
    return _date.day(value, tz)


def date_weekday(value: str, tz: Optional[str] = None) -> str:
    return _date.weekday(value, tz)


def date_add_days(value: str, days: int, tz: Optional[str] = None) -> str:
    return _date.add_days(value, days, tz)


def date_subtract_days(value: str, days: int, tz: Optional[str] = None) -> str:
    return _date.subtract_days(value, days, tz)


def date_yesterday(tz: Optional[str] = None) -> str:
    return _date.yesterday(tz)


def date_tomorrow(tz: Optional[str] = None) -> str:
    return _date.tomorrow(tz)


def date_from_timestamp(
    value: float, tz: Optional[str] = None
) -> str:
    return _date.from_timestamp(value, tz)


def date_parse(value: str, tz: Optional[str] = None) -> dict:
    return _date.parse(value, tz)


def date_format_iso(value: str, tz: Optional[str] = None) -> str:
    return _date.format_iso(value, tz)


def date_format_pattern(
    value: str,
    pattern: str,
    tz: Optional[str] = None,
) -> str:
    return _date.format(value, pattern, tz)


def date_diff(
    start: str,
    end: str,
    unit: str = "days",
    absolute: bool = True,
    tz: Optional[str] = None,
) -> float:
    return _date.diff(start, end, unit, absolute, tz)


def date_shift(value: str, options: Optional[dict] = None) -> str:
    return _date.shift(value, options)


def date_start_of_week(
    value: str,
    week_start: Optional[int] = None,
    tz: Optional[str] = None,
) -> str:
    return _date.start_of_week(value, week_start, tz)


def date_end_of_week(
    value: str,
    week_start: Optional[int] = None,
    tz: Optional[str] = None,
) -> str:
    return _date.end_of_week(value, week_start, tz)


def date_start_of_month(value: str, tz: Optional[str] = None) -> str:
    return _date.start_of_month(value, tz)


def date_end_of_month(value: str, tz: Optional[str] = None) -> str:
    return _date.end_of_month(value, tz)


def date_range(
    start: str,
    end: str,
    step: int = 1,
    inclusive: bool = False,
    tz: Optional[str] = None,
) -> list[str]:
    return _date.range(start, end, step, inclusive=inclusive, tz=tz)


def date_closest(
    candidates: Iterable[str],
    target: str,
    tz: Optional[str] = None,
) -> Optional[str]:
    return _date.closest(candidates, target, tz)


def date_sleep(seconds: float) -> None:
    _date.sleep(seconds)


__all__ = [
    "date_today",
    "date_year",
    "date_month",
    "date_day",
    "date_weekday",
    "date_add_days",
    "date_subtract_days",
    "date_yesterday",
    "date_tomorrow",
    "date_from_timestamp",
    "date_parse",
    "date_format_iso",
    "date_format_pattern",
    "date_diff",
    "date_shift",
    "date_start_of_week",
    "date_end_of_week",
    "date_start_of_month",
    "date_end_of_month",
    "date_range",
    "date_closest",
    "date_sleep",
]
