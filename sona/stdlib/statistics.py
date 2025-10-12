"""Statistical helpers for Sona programs.

Lightweight wrappers around common descriptive statistics so that users get
deterministic math utilities without pulling in heavy dependencies.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable, Sequence


def _as_sequence(data: Iterable[float | int]) -> Sequence[float | int]:
    if isinstance(data, (list, tuple)):
        return data  # type: ignore[return-value]
    return tuple(data)


def mean(data: Iterable[float | int]) -> float:
    """Return the arithmetic mean of *data*.

    Raises:
        ValueError: if *data* is empty.
    """

    values = _as_sequence(data)
    if not values:
        raise ValueError("mean() requires at least one data point")
    return float(sum(values)) / len(values)


def median(data: Iterable[float | int]) -> float:
    values = sorted(_as_sequence(data))
    length = len(values)
    if length == 0:
        raise ValueError("median() requires at least one data point")
    mid = length // 2
    if length % 2:
        return float(values[mid])
    return (float(values[mid - 1]) + float(values[mid])) / 2.0


def mode(data: Iterable[float | int]) -> float | int:
    values = _as_sequence(data)
    if not values:
        raise ValueError("mode() requires at least one data point")
    counts = Counter(values)
    # Deterministic tie-breaking by selecting the smallest value with max count
    max_count = max(counts.values())
    return min(val for val, cnt in counts.items() if cnt == max_count)


def variance(data: Iterable[float | int], sample: bool = False) -> float:
    values = _as_sequence(data)
    n = len(values)
    if n < 2:
        raise ValueError("variance() requires at least two data points")
    avg = mean(values)
    ss = sum((float(x) - avg) ** 2 for x in values)
    denom = n - 1 if sample else n
    if denom == 0:
        raise ValueError("sample variance requires at least two data points")
    return ss / denom


__all__ = ["mean", "median", "mode", "variance"]
