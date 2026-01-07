"""Statistical helpers for Sona programs.

Lightweight wrappers around common descriptive statistics so that users get
deterministic math utilities without pulling in heavy dependencies.
"""
from __future__ import annotations

import math
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


def min(data: Iterable[float | int]) -> float | int:
    values = _as_sequence(data)
    if not values:
        raise ValueError("min() requires at least one data point")
    return __builtins__["min"](values)


def max(data: Iterable[float | int]) -> float | int:
    values = _as_sequence(data)
    if not values:
        raise ValueError("max() requires at least one data point")
    return __builtins__["max"](values)


def median(data: Iterable[float | int]) -> float:
    values = sorted(_as_sequence(data))
    length = len(values)
    if length == 0:
        raise ValueError("median() requires at least one data point")
    mid = length // 2
    if length % 2:
        return float(values[mid])
    return (float(values[mid - 1]) + float(values[mid])) / 2.0


def median_low(data: Iterable[float | int]) -> float | int:
    values = sorted(_as_sequence(data))
    length = len(values)
    if length == 0:
        raise ValueError("median_low() requires at least one data point")
    mid = (length - 1) // 2
    return values[mid]


def median_high(data: Iterable[float | int]) -> float | int:
    values = sorted(_as_sequence(data))
    length = len(values)
    if length == 0:
        raise ValueError("median_high() requires at least one data point")
    mid = length // 2
    return values[mid]


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


def pvariance(data: Iterable[float | int]) -> float:
    """Alias for population variance."""
    return variance(data, sample=False)


def pstdev(data: Iterable[float | int]) -> float:
    """Alias for population standard deviation."""
    return stdev(data, sample=False)


def stdev(data: Iterable[float | int], sample: bool = False) -> float:
    """
    Calculate standard deviation.

    Args:
        data: Numeric data
        sample: If True, use sample std dev (n-1)

    Returns:
        Standard deviation

    Example:
        sd = statistics.stdev([1, 2, 3, 4, 5])
    """
    import math
    return math.sqrt(variance(data, sample=sample))


def quantile(data: Iterable[float | int], q: float) -> float:
    """
    Calculate quantile/percentile.

    Args:
        data: Numeric data
        q: Quantile (0.0 to 1.0, e.g., 0.5 = median)

    Returns:
        Quantile value

    Example:
        p75 = statistics.quantile([1, 2, 3, 4, 5], 0.75)
    """
    values = sorted(_as_sequence(data))
    if not values:
        raise ValueError("quantile() requires at least one data point")

    if q < 0 or q > 1:
        raise ValueError("quantile must be between 0 and 1")

    if q == 0:
        return float(values[0])
    if q == 1:
        return float(values[-1])

    idx = q * (len(values) - 1)
    lower = int(idx)
    upper = lower + 1
    weight = idx - lower

    if upper >= len(values):
        return float(values[lower])

    return float(values[lower]) * (1 - weight) + float(values[upper]) * weight


def quantiles(data: Iterable[float | int], n: int = 4) -> list[float]:
    if n < 1:
        raise ValueError("n must be at least 1")
    values = sorted(_as_sequence(data))
    if not values:
        raise ValueError("quantiles() requires at least one data point")
    result = []
    for q in range(1, n):
        result.append(quantile(values, q / n))
    return result


def min_value(data: Iterable[float | int]) -> float | int:
    """
    Get minimum value.

    Args:
        data: Numeric data

    Returns:
        Minimum value

    Example:
        minimum = statistics.min_value([5, 2, 8, 1])
    """
    values = _as_sequence(data)
    if not values:
        raise ValueError("min_value() requires at least one data point")
    return min(values)


def max_value(data: Iterable[float | int]) -> float | int:
    """
    Get maximum value.

    Args:
        data: Numeric data

    Returns:
        Maximum value

    Example:
        maximum = statistics.max_value([5, 2, 8, 1])
    """
    values = _as_sequence(data)
    if not values:
        raise ValueError("max_value() requires at least one data point")
    return max(values)


def range_value(data: Iterable[float | int]) -> float:
    """
    Calculate range (max - min).

    Args:
        data: Numeric data

    Returns:
        Range value

    Example:
        r = statistics.range_value([1, 2, 3, 4, 5])  # 4
    """
    values = _as_sequence(data)
    if not values:
        raise ValueError("range_value() requires at least one data point")
    return float(max(values) - min(values))


def sum_values(data: Iterable[float | int]) -> float:
    """
    Calculate sum of values.

    Args:
        data: Numeric data

    Returns:
        Sum

    Example:
        total = statistics.sum_values([1, 2, 3, 4, 5])
    """
    return float(sum(_as_sequence(data)))


def count(data: Iterable[float | int]) -> int:
    """
    Count number of values.

    Args:
        data: Data

    Returns:
        Count

    Example:
        n = statistics.count([1, 2, 3])
    """
    return len(_as_sequence(data))


def correlation(x: Iterable[float | int], y: Iterable[float | int]) -> float:
    """
    Calculate Pearson correlation coefficient.

    Args:
        x: First dataset
        y: Second dataset

    Returns:
        Correlation (-1 to 1)

    Example:
        r = statistics.correlation([1, 2, 3], [2, 4, 6])
    """
    import math

    x_vals = _as_sequence(x)
    y_vals = _as_sequence(y)

    if len(x_vals) != len(y_vals):
        raise ValueError("x and y must have same length")
    if len(x_vals) < 2:
        raise ValueError("correlation requires at least two data points")

    mean_x = mean(x_vals)
    mean_y = mean(y_vals)

    numerator = sum((float(xi) - mean_x) * (float(yi) - mean_y)
                   for xi, yi in zip(x_vals, y_vals))

    sum_sq_x = sum((float(xi) - mean_x) ** 2 for xi in x_vals)
    sum_sq_y = sum((float(yi) - mean_y) ** 2 for yi in y_vals)

    denominator = math.sqrt(sum_sq_x * sum_sq_y)

    if denominator == 0:
        return 0.0

    return numerator / denominator


def geometric_mean(data: Iterable[float | int]) -> float:
    values = _as_sequence(data)
    if not values:
        raise ValueError("geometric_mean() requires at least one data point")
    product = 1.0
    for value in values:
        product *= float(value)
    return product ** (1.0 / len(values))


def harmonic_mean(data: Iterable[float | int]) -> float:
    values = _as_sequence(data)
    if not values:
        raise ValueError("harmonic_mean() requires at least one data point")
    if any(float(v) == 0.0 for v in values):
        raise ValueError("harmonic mean is undefined for zero values")
    return len(values) / sum(1.0 / float(v) for v in values)


def z_score(value: float, data: Iterable[float | int]) -> float:
    """
    Calculate z-score for a value.

    Args:
        value: Value to score
        data: Dataset for reference

    Returns:
        Z-score

    Example:
        z = statistics.z_score(75, [60, 65, 70, 75, 80])
    """
    values = _as_sequence(data)
    avg = mean(values)
    sd = stdev(values)

    if sd == 0:
        return 0.0

    return (value - avg) / sd


__all__ = [
    "mean", "median", "median_low", "median_high", "mode",
    "variance", "pvariance", "stdev", "pstdev",
    "quantile", "quantiles", "min_value", "max_value", "range_value",
    "sum_values", "count", "correlation", "z_score",
    "geometric_mean", "harmonic_mean"
]
