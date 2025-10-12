"""Advanced date helpers backing the Sona ``date`` standard library module."""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional

try:  # pragma: no cover - zoneinfo is available on Python 3.9+
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore


ISO_DATE = "%Y-%m-%d"

_DEFAULT_WEEK_START = 1
_DIFF_UNITS = {"days", "weeks"}


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


def _current_datetime(tz_value: Optional[str]) -> datetime:
    tzinfo = _resolve_timezone(tz_value)
    if tzinfo is None:
        return datetime.now().astimezone()
    return datetime.now(tzinfo)


def _parse_iso_datetime(value: str) -> datetime:
    raw = value.strip()
    if not raw:
        raise ValueError("Date value cannot be empty")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:  # pragma: no cover - exercised via parse()
        raise ValueError(f"Unsupported ISO date: {value!r}") from exc


def _to_timezone(dt: datetime, tz_value: Optional[str]) -> datetime:
    tzinfo = _resolve_timezone(tz_value)
    if tzinfo is None:
        return dt
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tzinfo)
    return dt.astimezone(tzinfo)


def _coerce_date(value: str, tz_value: Optional[str]) -> date:
    dt = _parse_iso_datetime(value)
    adjusted = _to_timezone(dt, tz_value)
    return adjusted.date()


def _days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def _add_years(value: date, years: int) -> date:
    if years == 0:
        return value
    target_year = value.year + years
    day = min(value.day, _days_in_month(target_year, value.month))
    return value.replace(year=target_year, day=day)


def _add_months(value: date, months: int) -> date:
    if months == 0:
        return value
    month_index = value.month - 1 + months
    target_year = value.year + month_index // 12
    target_month = month_index % 12 + 1
    day = min(value.day, _days_in_month(target_year, target_month))
    return value.replace(year=target_year, month=target_month, day=day)


def _apply_shift(
    value: date,
    *,
    years: int = 0,
    months: int = 0,
    weeks: int = 0,
    days: int = 0,
) -> date:
    result = value
    if years:
        result = _add_years(result, years)
    if months:
        result = _add_months(result, months)
    if weeks or days:
        result = result + timedelta(weeks=weeks, days=days)
    return result


def _normalize_week_start(value: Optional[int]) -> int:
    if value is None:
        return _DEFAULT_WEEK_START
    candidate = int(value)
    if 1 <= candidate <= 7:
        return candidate
    raise ValueError("week_start must be between 1 (Monday) and 7 (Sunday)")


def today(tz: Optional[str] = None) -> str:
    """Return current date in ISO format (YYYY-MM-DD)."""

    return _current_datetime(tz).date().isoformat()


def yesterday(tz: Optional[str] = None) -> str:
    """Return yesterday's date relative to *tz*."""

    return (_current_datetime(tz).date() - timedelta(days=1)).isoformat()


def tomorrow(tz: Optional[str] = None) -> str:
    """Return tomorrow's date relative to *tz*."""

    return (_current_datetime(tz).date() + timedelta(days=1)).isoformat()


def from_timestamp(ts: float, tz: Optional[str] = None) -> str:
    """Convert a Unix timestamp to an ISO date string."""

    tzinfo = _resolve_timezone(tz)
    if tzinfo is not None:
        current = datetime.fromtimestamp(float(ts), tzinfo)
    else:
        current = datetime.fromtimestamp(float(ts)).astimezone()
    return current.date().isoformat()


def parse(value: str, tz: Optional[str] = None) -> Dict[str, object]:
    """Parse *value* into calendar components."""

    dt = _to_timezone(_parse_iso_datetime(value), tz)
    d = dt.date()
    iso = d.isoformat()
    iso_calendar = dt.isocalendar()
    return {
        "iso": iso,
        "year": d.year,
        "month": d.month,
        "day": d.day,
        "weekday": d.isoweekday(),
        "iso_week": iso_calendar.week,
        "iso_year": iso_calendar.year,
        "quarter": (d.month - 1) // 3 + 1,
        "day_of_year": dt.timetuple().tm_yday,
        "is_leap_year": calendar.isleap(d.year),
    }


def format_iso(value: str, tz: Optional[str] = None) -> str:
    """Normalise *value* to ``YYYY-MM-DD`` optionally applying *tz*."""

    return _coerce_date(value, tz).isoformat()


def format(value: str, pattern: str, tz: Optional[str] = None) -> str:
    """Render *value* using a ``strftime`` pattern."""

    dt = _to_timezone(_parse_iso_datetime(value), tz)
    return dt.strftime(pattern)


def strftime(pattern: str, dt: Optional[datetime] = None) -> str:
    """Compatibility wrapper mapping to :func:`format`."""

    target = dt or datetime.now().astimezone()
    return target.strftime(pattern)


def diff(
    start: str,
    end: str,
    unit: str = "days",
    absolute: bool = True,
    tz: Optional[str] = None,
) -> float:
    """Return the distance between *start* and *end* in the requested unit."""

    start_date = _coerce_date(start, tz)
    end_date = _coerce_date(end, tz)
    delta_days = (end_date - start_date).days
    if absolute:
        delta_days = abs(delta_days)
    unit_key = unit.lower()
    if unit_key not in _DIFF_UNITS:
        unit_key = "days"
    if unit_key == "weeks":
        return delta_days / 7.0
    return float(delta_days)


def shift(
    value: str,
    options: Optional[Dict[str, object]] = None,
    *,
    years: int = 0,
    months: int = 0,
    weeks: int = 0,
    days: int = 0,
    tz: Optional[str] = None,
) -> str:
    """Adjust *value* by the provided offsets."""

    payload = options or {}
    years_val = int(payload.get("years", years) or 0)
    months_val = int(payload.get("months", months) or 0)
    weeks_val = int(payload.get("weeks", weeks) or 0)
    days_val = int(payload.get("days", days) or 0)
    tz_value = payload.get("tz", tz)

    base = _coerce_date(value, tz_value)
    shifted = _apply_shift(
        base,
        years=years_val,
        months=months_val,
        weeks=weeks_val,
        days=days_val,
    )
    return shifted.isoformat()


def start_of_week(
    value: str,
    week_start: Optional[int] = None,
    tz: Optional[str] = None,
) -> str:
    """Return the Monday-based start of the week containing *value*."""

    target = _coerce_date(value, tz)
    anchor = _normalize_week_start(week_start)
    current = target.isoweekday()
    delta = (current - anchor) % 7
    return (target - timedelta(days=delta)).isoformat()


def end_of_week(
    value: str,
    week_start: Optional[int] = None,
    tz: Optional[str] = None,
) -> str:
    """Return the end-of-week date for *value* respecting *week_start*."""

    start_value = start_of_week(value, week_start, tz)
    return shift(start_value, days=6)


def start_of_month(value: str, tz: Optional[str] = None) -> str:
    """Return the first day of the month for *value*."""

    target = _coerce_date(value, tz)
    return target.replace(day=1).isoformat()


def end_of_month(value: str, tz: Optional[str] = None) -> str:
    """Return the final day of the month for *value*."""

    target = _coerce_date(value, tz)
    days = _days_in_month(target.year, target.month)
    return target.replace(day=days).isoformat()


def range(
    start: str,
    end: str,
    step: int = 1,
    inclusive: bool = False,
    tz: Optional[str] = None,
) -> List[str]:
    """Produce a sequence of ISO dates between *start* and *end*."""

    if step <= 0:
        raise ValueError("step must be a positive integer")
    start_date = _coerce_date(start, tz)
    end_date = _coerce_date(end, tz)
    if start_date == end_date:
        return [start_date.isoformat()] if inclusive else []
    direction = 1 if end_date > start_date else -1
    step_delta = timedelta(days=step * direction)
    current = start_date
    results: List[str] = []

    def _should_continue(candidate: date) -> bool:
        if direction > 0:
            return candidate < end_date or (
                inclusive and candidate <= end_date
            )
        return candidate > end_date or (
            inclusive and candidate >= end_date
        )

    while _should_continue(current):
        results.append(current.isoformat())
        current = current + step_delta
    return results


def closest(
    candidates: Iterable[str],
    target: str,
    tz: Optional[str] = None,
) -> Optional[str]:
    """Return candidate nearest to *target* (ties prefer earlier dates)."""

    target_date = _coerce_date(target, tz)
    best_value: Optional[str] = None
    best_distance: Optional[int] = None
    for candidate in candidates:
        candidate_date = _coerce_date(candidate, tz)
        distance = abs((candidate_date - target_date).days)
        if best_distance is None or distance < best_distance or (
            distance == best_distance
            and candidate_date
            < _coerce_date(best_value, tz)  # type: ignore[arg-type]
        ):
            best_value = candidate_date.isoformat()
            best_distance = distance
    return best_value


def sleep(seconds: float) -> None:
    """Deprecated compatibility wrapper; prefer :mod:`sona.stdlib.time`."""

    import time as _time

    _time.sleep(float(seconds))


__all__ = [
    "today",
    "yesterday",
    "tomorrow",
    "from_timestamp",
    "parse",
    "format_iso",
    "format",
    "strftime",
    "diff",
    "shift",
    "start_of_week",
    "end_of_week",
    "start_of_month",
    "end_of_month",
    "range",
    "closest",
    "sleep",
    "ISO_DATE",
]

# Backwards compatibility
fromtimestamp = from_timestamp
