"""Native backing for deterministic human-readable formatting."""

from __future__ import annotations

from typing import Any


def format_number(value: Any, decimals: Any = 2) -> str:
    return f"{float(value):.{int(decimals)}f}"


def format_integer(value: Any) -> str:
    return f"{int(value):d}"


def format_percent(value: Any, decimals: Any = 1) -> str:
    return f"{float(value) * 100:.{int(decimals)}f}%"


def format_pad_left(value: Any, width: Any, fill: Any = " ") -> str:
    return str(value).rjust(int(width), str(fill or " ")[0])


def format_pad_right(value: Any, width: Any, fill: Any = " ") -> str:
    return str(value).ljust(int(width), str(fill or " ")[0])


def format_center(value: Any, width: Any, fill: Any = " ") -> str:
    return str(value).center(int(width), str(fill or " ")[0])


def format_table(rows: Any, headers: Any = None) -> str:
    headers = headers or []
    rows = rows or []
    table_rows = [list(headers)] if headers else []
    table_rows.extend([list(row.values()) if isinstance(row, dict) else list(row) for row in rows])
    if not table_rows:
        return ""
    widths = [max(len(str(row[idx])) if idx < len(row) else 0 for row in table_rows) for idx in range(max(len(row) for row in table_rows))]
    rendered = []
    for row in table_rows:
        rendered.append(" | ".join(str(row[idx] if idx < len(row) else "").ljust(widths[idx]) for idx in range(len(widths))).rstrip())
    return "\n".join(rendered)


def format_progress(current: Any, total: Any, width: Any = 20) -> str:
    width_i = max(1, int(width))
    total_f = float(total)
    ratio = 0.0 if total_f <= 0 else max(0.0, min(1.0, float(current) / total_f))
    filled = int(round(ratio * width_i))
    return "[" + "#" * filled + "-" * (width_i - filled) + f"] {ratio * 100:.0f}%"


def format_truncate(value: Any, width: Any, suffix: Any = "...") -> str:
    text = str(value)
    limit = int(width)
    end = str(suffix)
    if len(text) <= limit:
        return text
    if limit <= len(end):
        return end[:limit]
    return text[: limit - len(end)] + end


__all__ = [
    "format_number",
    "format_integer",
    "format_percent",
    "format_pad_left",
    "format_pad_right",
    "format_center",
    "format_table",
    "format_progress",
    "format_truncate",
]
