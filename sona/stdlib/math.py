"""Advanced numeric helpers powering the Sona ``math`` module."""

from __future__ import annotations

import builtins
import math as _math
import statistics
from typing import Iterable, Sequence


Number = float | int


PI = _math.pi
TAU = _math.tau
E = _math.e
PHI = (1 + _math.sqrt(5.0)) / 2.0
INF = _math.inf
NAN = _math.nan


def _ensure_float(value: Number) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"Expected a numeric value, got {value!r}") from exc


def _to_tuple(values: Iterable[Number]) -> tuple[float, ...]:
    if isinstance(values, Sequence):
        seq = tuple(_ensure_float(item) for item in values)
    else:
        seq = tuple(_ensure_float(item) for item in values)
    if not seq:
        raise ValueError("Expected at least one numeric value")
    return seq


def add(a: Number, b: Number) -> float:
    return _ensure_float(a) + _ensure_float(b)


def subtract(a: Number, b: Number) -> float:
    return _ensure_float(a) - _ensure_float(b)


def multiply(a: Number, b: Number) -> float:
    return _ensure_float(a) * _ensure_float(b)


def divide(a: Number, b: Number) -> float:
    denominator = _ensure_float(b)
    if denominator == 0:
        raise ZeroDivisionError("division by zero")
    return _ensure_float(a) / denominator


def safe_divide(a: Number, b: Number, fallback: float = 0.0) -> float:
    denominator = _ensure_float(b)
    return fallback if denominator == 0 else _ensure_float(a) / denominator


def mod(a: Number, b: Number) -> float:
    denominator = _ensure_float(b)
    if denominator == 0:
        raise ZeroDivisionError("modulus by zero")
    return _math.fmod(_ensure_float(a), denominator)


def pow(x: Number, y: Number) -> float:
    return _ensure_float(x) ** _ensure_float(y)


def sqrt(x: Number) -> float:
    value = _ensure_float(x)
    if value < 0:
        raise ValueError("square root domain error")
    return _math.sqrt(value)


def cbrt(x: Number) -> float:
    value = _ensure_float(x)
    return _math.copysign(abs(value) ** (1.0 / 3.0), value)


def sin(x: Number) -> float:
    return _math.sin(_ensure_float(x))


def cos(x: Number) -> float:
    return _math.cos(_ensure_float(x))


def tan(x: Number) -> float:
    return _math.tan(_ensure_float(x))


def asin(x: Number) -> float:
    return _math.asin(_ensure_float(x))


def acos(x: Number) -> float:
    return _math.acos(_ensure_float(x))


def atan(x: Number) -> float:
    return _math.atan(_ensure_float(x))


def atan2(y: Number, x: Number) -> float:
    return _math.atan2(_ensure_float(y), _ensure_float(x))


def log(x: Number, base: Number | None = None) -> float:
    value = _ensure_float(x)
    if value <= 0:
        raise ValueError("logarithm domain error")
    if base is None:
        return _math.log(value)
    base_value = _ensure_float(base)
    if base_value <= 0 or base_value == 1.0:
        raise ValueError("logarithm base must be positive and not equal to 1")
    return _math.log(value, base_value)


def log10(x: Number) -> float:
    return log(x, 10.0)


def exp(x: Number) -> float:
    return _math.exp(_ensure_float(x))


def sigmoid(x: Number) -> float:
    value = _ensure_float(x)
    return 1.0 / (1.0 + _math.exp(-value))


def fma(a: Number, b: Number, c: Number) -> float:
    """Compute fused multiply-add where available, else fall back."""
    try:
        return _math.fma(_ensure_float(a), _ensure_float(b), _ensure_float(c))
    except AttributeError:  # pragma: no cover - Py<3.9 fallback
        return _ensure_float(a) * _ensure_float(b) + _ensure_float(c)


def clamp(value: Number, lower: Number, upper: Number) -> float:
    low = _ensure_float(lower)
    high = _ensure_float(upper)
    if low > high:
        raise ValueError("lower bound must not exceed upper bound")
    return min(max(_ensure_float(value), low), high)


def lerp(start: Number, end: Number, t: Number) -> float:
    start_val = _ensure_float(start)
    end_val = _ensure_float(end)
    return start_val + (end_val - start_val) * _ensure_float(t)


def inv_lerp(start: Number, end: Number, value: Number) -> float:
    start_val = _ensure_float(start)
    end_val = _ensure_float(end)
    if start_val == end_val:
        raise ValueError("cannot compute inverse lerp when start equals end")
    return (_ensure_float(value) - start_val) / (end_val - start_val)


def remap(
    value: Number,
    in_start: Number,
    in_end: Number,
    out_start: Number,
    out_end: Number,
) -> float:
    t = inv_lerp(in_start, in_end, value)
    return lerp(out_start, out_end, t)


def deg2rad(degrees: Number) -> float:
    return _math.radians(_ensure_float(degrees))


def rad2deg(radians: Number) -> float:
    return _math.degrees(_ensure_float(radians))


def floor(x: Number) -> int:
    return _math.floor(_ensure_float(x))


def ceil(x: Number) -> int:
    return _math.ceil(_ensure_float(x))


def round(x: Number, ndigits: int | None = None) -> float:
    value = _ensure_float(x)
    return (
        builtins.round(value, ndigits)
        if ndigits is not None
        else builtins.round(value)
    )


def trunc(x: Number) -> int:
    return _math.trunc(_ensure_float(x))


def abs(x: Number) -> float:  # noqa: A002 - align with stdlib math naming
    return _math.fabs(_ensure_float(x))


def is_nan(value: Number) -> bool:
    return _math.isnan(_ensure_float(value))


def is_inf(value: Number) -> bool:
    return _math.isinf(_ensure_float(value))


def is_finite(value: Number) -> bool:
    return _math.isfinite(_ensure_float(value))


# noqa: A001 - compatibility helper
def sum(values: Iterable[Number]) -> float:
    return _math.fsum(_to_tuple(values))


def product(values: Iterable[Number]) -> float:
    return _math.prod(_to_tuple(values))


def mean(values: Iterable[Number]) -> float:
    return statistics.fmean(_to_tuple(values))


def median(values: Iterable[Number]) -> float:
    data = _to_tuple(values)
    return statistics.median(data)


def variance(values: Iterable[Number], *, sample: bool = False) -> float:
    data = _to_tuple(values)
    if len(data) < 2:
        raise ValueError("variance requires at least two values")
    return statistics.variance(data) if sample else statistics.pvariance(data)


def stddev(values: Iterable[Number], *, sample: bool = False) -> float:
    data = _to_tuple(values)
    if len(data) < 2:
        raise ValueError("standard deviation requires at least two values")
    return statistics.stdev(data) if sample else statistics.pstdev(data)


def minimum(values: Iterable[Number]) -> float:
    data = _to_tuple(values)
    return min(data)


def maximum(values: Iterable[Number]) -> float:
    data = _to_tuple(values)
    return max(data)


def dot(a: Iterable[Number], b: Iterable[Number]) -> float:
    vec_a = _to_tuple(a)
    vec_b = _to_tuple(b)
    if len(vec_a) != len(vec_b):
        raise ValueError("dot product requires vectors of equal length")
    return _math.fsum(x * y for x, y in zip(vec_a, vec_b))


def magnitude(vec: Iterable[Number]) -> float:
    components = _to_tuple(vec)
    return _math.sqrt(
        _math.fsum(component * component for component in components)
    )


def normalize(vec: Iterable[Number]) -> tuple[float, ...]:
    components = _to_tuple(vec)
    length = magnitude(components)
    if length == 0:
        raise ValueError("cannot normalize zero-length vector")
    return tuple(component / length for component in components)


def distance(a: Iterable[Number], b: Iterable[Number]) -> float:
    vec_a = _to_tuple(a)
    vec_b = _to_tuple(b)
    if len(vec_a) != len(vec_b):
        raise ValueError("distance requires vectors of equal length")
    return _math.sqrt(_math.fsum((x - y) ** 2 for x, y in zip(vec_a, vec_b)))


def is_close(
    a: Number,
    b: Number,
    *,
    rel_tol: float = 1e-9,
    abs_tol: float = 0.0,
) -> bool:
    return _math.isclose(
        _ensure_float(a),
        _ensure_float(b),
        rel_tol=rel_tol,
        abs_tol=abs_tol,
    )


def hypot(*values: Number) -> float:
    if not values:
        raise ValueError("hypot requires at least one value")
    return _math.hypot(*(_ensure_float(value) for value in values))


def gcd(a: Number, b: Number) -> int:
    return _math.gcd(int(_ensure_float(a)), int(_ensure_float(b)))


def lcm(a: Number, b: Number) -> int:
    return _math.lcm(int(_ensure_float(a)), int(_ensure_float(b)))


def factorial(n: Number) -> int:
    value = _ensure_float(n)
    if value < 0 or int(value) != value:
        raise ValueError("factorial expects a non-negative integer")
    return _math.factorial(int(value))


def choose(n: Number, k: Number) -> int:
    n_int = int(_ensure_float(n))
    k_int = int(_ensure_float(k))
    if n_int < 0 or k_int < 0 or k_int > n_int:
        raise ValueError("invalid values for n choose k")
    return _math.comb(n_int, k_int)


def permute(n: Number, k: Number) -> int:
    n_int = int(_ensure_float(n))
    k_int = int(_ensure_float(k))
    if n_int < 0 or k_int < 0 or k_int > n_int:
        raise ValueError("invalid values for permutations")
    return _math.perm(n_int, k_int)


def mode(values: Iterable[Number]) -> float:
    """Most frequently occurring value."""
    from collections import Counter
    list_vals = list(values)
    if not list_vals:
        raise ValueError("cannot compute mode of empty sequence")
    counts = Counter(list_vals)
    return float(counts.most_common(1)[0][0])


def range_of(values: Iterable[Number]) -> float:
    """Difference between maximum and minimum."""
    list_vals = list(values)
    if not list_vals:
        raise ValueError("cannot compute range of empty sequence")
    return maximum(list_vals) - minimum(list_vals)


def percentile(values: Iterable[Number], p: Number) -> float:
    """Compute percentile (0-100)."""
    list_vals = sorted(values)
    if not list_vals:
        raise ValueError("cannot compute percentile of empty sequence")
    k = (len(list_vals) - 1) * (float(p) / 100.0)
    f = _math.floor(k)
    c = _math.ceil(k)
    if f == c:
        return float(list_vals[int(k)])
    d0 = float(list_vals[int(f)]) * (c - k)
    d1 = float(list_vals[int(c)]) * (k - f)
    return d0 + d1


def sign(x: Number) -> int:
    """Return sign of number: -1, 0, or 1."""
    val = _ensure_float(x)
    if val > 0:
        return 1
    elif val < 0:
        return -1
    else:
        return 0


def is_even(n: Number) -> bool:
    """Check if number is even."""
    return int(_ensure_float(n)) % 2 == 0


def is_odd(n: Number) -> bool:
    """Check if number is odd."""
    return int(_ensure_float(n)) % 2 != 0


def is_prime(n: Number) -> bool:
    """Check if number is prime."""
    num = int(_ensure_float(n))
    if num < 2:
        return False
    if num == 2:
        return True
    if num % 2 == 0:
        return False
    for i in range(3, int(_math.sqrt(num)) + 1, 2):
        if num % i == 0:
            return False
    return True


def prod(values: Iterable[Number]) -> float:
    """Alias for product to match stdlib naming."""
    return product(values)


def fibonacci(n: Number) -> int:
    """Compute nth Fibonacci number."""
    num = int(_ensure_float(n))
    if num < 0:
        raise ValueError("fibonacci not defined for negative numbers")
    if num <= 1:
        return num
    a, b = 0, 1
    for _ in range(2, num + 1):
        a, b = b, a + b
    return b


def average(*values: Number) -> float:
    """Compute average (alias for mean)."""
    return mean(values)


__all__ = [
    "PI",
    "TAU",
    "E",
    "PHI",
    "add",
    "subtract",
    "multiply",
    "divide",
    "safe_divide",
    "mod",
    "pow",
    "sqrt",
    "cbrt",
    "sin",
    "cos",
    "tan",
    "asin",
    "acos",
    "atan",
    "atan2",
    "log",
    "log10",
    "exp",
    "sigmoid",
    "clamp",
    "lerp",
    "inv_lerp",
    "remap",
    "deg2rad",
    "rad2deg",
    "floor",
    "ceil",
    "round",
    "trunc",
    "abs",
    "sum",
    "product",
    "mean",
    "median",
    "variance",
    "stddev",
    "minimum",
    "maximum",
    "dot",
    "magnitude",
    "normalize",
    "distance",
    "is_close",
    "hypot",
    "gcd",
    "lcm",
    "factorial",
    "choose",
    "permute",
    "mode",
    "range_of",
    "percentile",
    "sign",
    "is_even",
    "is_odd",
    "is_prime",
    "fibonacci",
    "average",
]
