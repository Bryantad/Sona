"""Advanced time helpers backing the Sona ``time`` standard library module."""

from __future__ import annotations

import time as _time
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

try:  # pragma: no cover - zoneinfo is available on Python 3.9+
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore


_TIMESPEC_DEFAULT = "seconds"
_TIMESPEC_OPTIONS = {
    "auto",
    "hours",
    "minutes",
    "seconds",
    "milliseconds",
    "microseconds",
}

_DIFF_FACTORS = {
    "seconds": 1.0,
    "milliseconds": 1000.0,
    "microseconds": 1_000_000.0,
    "minutes": 1.0 / 60.0,
    "hours": 1.0 / 3600.0,
    "days": 1.0 / 86400.0,
}


def _normalize_timespec(value: Optional[str]) -> str:
    if not value:
        return _TIMESPEC_DEFAULT
    candidate = value.lower()
    if candidate in _TIMESPEC_OPTIONS:
        return candidate
    return _TIMESPEC_DEFAULT


def _resolve_timezone(value: Optional[str]):
    if value is None:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    lowered = candidate.lower()
    if lowered in {"local", "system"}:
        return datetime.now().astimezone().tzinfo
    if lowered in {"utc", "z"}:
        return timezone.utc
    if candidate.startswith(("+", "-")) and len(candidate) >= 6:
        try:
            sign = 1 if candidate[0] == "+" else -1
            hours = int(candidate[1:3])
            minutes = int(candidate[4:6])
            return timezone(sign * timedelta(hours=hours, minutes=minutes))
        except ValueError:
            return None
    if ZoneInfo is not None:
        try:
            return ZoneInfo(candidate)
        except Exception:  # pragma: no cover - depends on host tz database
            return None
    return None


def _local_now():
    return datetime.now().astimezone()


def _parse_iso(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:  # pragma: no cover - exercised via parse()
        raise ValueError(f"Unsupported ISO datetime: {value!r}") from exc


def _apply_timezone(dt: datetime, tz_value: Optional[str]) -> datetime:
    tzinfo = _resolve_timezone(tz_value)
    if tzinfo is None:
        return dt
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tzinfo)
    return dt.astimezone(tzinfo)


def now(timespec: Optional[str] = None, tz: Optional[str] = None) -> str:
    spec = _normalize_timespec(timespec)
    tzinfo = _resolve_timezone(tz)
    current = datetime.now(tzinfo) if tzinfo else _local_now()
    return current.isoformat(timespec=spec)


def utcnow(timespec: Optional[str] = None) -> str:
    spec = _normalize_timespec(timespec)
    return datetime.now(timezone.utc).isoformat(timespec=spec)


def timestamp() -> float:
    return datetime.now(timezone.utc).timestamp()


def from_timestamp(
    value: float,
    timespec: Optional[str] = None,
    tz: Optional[str] = None,
) -> str:
    spec = _normalize_timespec(timespec)
    tzinfo = _resolve_timezone(tz)
    base_tz = tzinfo or _local_now().tzinfo
    current = datetime.fromtimestamp(float(value), tz=base_tz)
    return current.isoformat(timespec=spec)


def to_timestamp(value: str, tz: Optional[str] = None) -> float:
    dt = _apply_timezone(_parse_iso(value), tz)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_local_now().tzinfo)
    return dt.timestamp()


def parse(
    value: str,
    tz: Optional[str] = None,
    timespec: Optional[str] = "microseconds",
) -> Dict[str, object]:
    dt = _apply_timezone(_parse_iso(value), tz)
    spec = _normalize_timespec(timespec)
    offset = dt.utcoffset()
    return {
        "iso": dt.isoformat(timespec=spec),
        "timestamp": dt.timestamp(),
        "year": dt.year,
        "month": dt.month,
        "day": dt.day,
        "hour": dt.hour,
        "minute": dt.minute,
        "second": dt.second,
        "microsecond": dt.microsecond,
        "weekday": dt.isoweekday(),
        "day_of_year": dt.timetuple().tm_yday,
        "tz_name": dt.tzname(),
        "offset_minutes": int(offset.total_seconds() / 60) if offset else None,
    }


def format_iso(
    value: str,
    timespec: Optional[str] = None,
    tz: Optional[str] = None,
) -> str:
    dt = _apply_timezone(_parse_iso(value), tz)
    spec = _normalize_timespec(timespec)
    return dt.isoformat(timespec=spec)


def format(
    value: str,
    pattern: str,
    tz: Optional[str] = None,
) -> str:
    return format_pattern(value, pattern, tz)


def format_pattern(
    value: str,
    pattern: str,
    tz: Optional[str] = None,
) -> str:
    dt = _apply_timezone(_parse_iso(value), tz)
    return dt.strftime(pattern)


def diff(
    start: str,
    end: str,
    unit: str = "seconds",
    absolute: bool = True,
) -> float:
    start_dt = _parse_iso(start)
    end_dt = _parse_iso(end)
    delta = end_dt - start_dt
    seconds = delta.total_seconds()
    if absolute:
        seconds = abs(seconds)
    factor = _DIFF_FACTORS.get(unit.lower(), 1.0)
    if unit.lower() in {"minutes", "hours", "days"}:
        return seconds * factor
    return seconds * factor


def shift(
    value: str,
    options: Optional[Dict[str, object]] = None,
    *,
    weeks: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: float = 0.0,
    milliseconds: float = 0.0,
    microseconds: float = 0.0,
    tz: Optional[str] = None,
    timespec: Optional[str] = None,
) -> str:
    payload = options or {}
    weeks_val = int(payload.get("weeks", weeks) or 0)
    days_val = int(payload.get("days", days) or 0)
    hours_val = int(payload.get("hours", hours) or 0)
    minutes_val = int(payload.get("minutes", minutes) or 0)
    seconds_val = float(payload.get("seconds", seconds) or 0.0)
    milliseconds_val = float(payload.get("milliseconds", milliseconds) or 0.0)
    microseconds_val = float(payload.get("microseconds", microseconds) or 0.0)
    tz_value = payload.get("tz", tz)
    spec_value = payload.get("timespec", timespec)

    dt = _apply_timezone(_parse_iso(value), tz_value)
    delta = timedelta(
        weeks=weeks_val,
        days=days_val,
        hours=hours_val,
        minutes=minutes_val,
        seconds=seconds_val,
        milliseconds=milliseconds_val,
        microseconds=microseconds_val,
    )
    spec = _normalize_timespec(spec_value)
    return (dt + delta).isoformat(timespec=spec)


def sleep(seconds: float) -> None:
    _time.sleep(float(seconds))


def monotonic() -> float:
    return _time.monotonic()


def perf_counter() -> float:
    return _time.perf_counter()


__all__ = [
    "now",
    "utcnow",
    "timestamp",
    "from_timestamp",
    "to_timestamp",
    "parse",
    "format_iso",
    "format",
    "format_pattern",
    "diff",
    "shift",
    "sleep",
    "monotonic",
    "perf_counter",
]
