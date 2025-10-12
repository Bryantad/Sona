"""Native glue exposing :mod:`sona.stdlib.math` helpers to Sona."""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from . import math as _math


def _coerce_iterable(values: Any) -> Iterable[Any]:
    if values is None:
        raise TypeError("Expected an iterable of numbers")
    if isinstance(values, (list, tuple, set)):
        return values
    return list(values)


math_PI = _math.PI
math_TAU = _math.TAU
math_E = _math.E
math_PHI = _math.PHI


def math_add(a: Any, b: Any) -> float:
    return _math.add(a, b)


def math_subtract(a: Any, b: Any) -> float:
    return _math.subtract(a, b)


def math_multiply(a: Any, b: Any) -> float:
    return _math.multiply(a, b)


def math_divide(a: Any, b: Any) -> float:
    return _math.divide(a, b)


def math_safe_divide(a: Any, b: Any, fallback: Any = 0.0) -> float:
    return _math.safe_divide(a, b, float(fallback))


def math_mod(a: Any, b: Any) -> float:
    return _math.mod(a, b)


def math_pow(x: Any, y: Any) -> float:
    return _math.pow(x, y)


def math_sqrt(x: Any) -> float:
    return _math.sqrt(x)


def math_cbrt(x: Any) -> float:
    return _math.cbrt(x)


def math_sin(x: Any) -> float:
    return _math.sin(x)


def math_cos(x: Any) -> float:
    return _math.cos(x)


def math_tan(x: Any) -> float:
    return _math.tan(x)


def math_asin(x: Any) -> float:
    return _math.asin(x)


def math_acos(x: Any) -> float:
    return _math.acos(x)


def math_atan(x: Any) -> float:
    return _math.atan(x)


def math_atan2(y: Any, x: Any) -> float:
    return _math.atan2(y, x)


def math_log(x: Any, base: Any | None = None) -> float:
    return _math.log(x, base)


def math_log10(x: Any) -> float:
    return _math.log10(x)


def math_exp(x: Any) -> float:
    return _math.exp(x)


def math_sigmoid(x: Any) -> float:
    return _math.sigmoid(x)


def math_clamp(value: Any, lower: Any, upper: Any) -> float:
    return _math.clamp(value, lower, upper)


def math_lerp(start: Any, end: Any, t: Any) -> float:
    return _math.lerp(start, end, t)


def math_inv_lerp(start: Any, end: Any, value: Any) -> float:
    return _math.inv_lerp(start, end, value)


def math_remap(
    value: Any,
    in_start: Any,
    in_end: Any,
    out_start: Any,
    out_end: Any,
) -> float:
    return _math.remap(value, in_start, in_end, out_start, out_end)


def math_deg2rad(degrees: Any) -> float:
    return _math.deg2rad(degrees)


def math_rad2deg(radians: Any) -> float:
    return _math.rad2deg(radians)


def math_floor(x: Any) -> int:
    return _math.floor(x)


def math_ceil(x: Any) -> int:
    return _math.ceil(x)


def math_round(x: Any, ndigits: Any | None = None) -> float:
    digits = int(ndigits) if ndigits is not None else None
    return _math.round(x, digits)


def math_trunc(x: Any) -> int:
    return _math.trunc(x)


def math_abs(x: Any) -> float:
    return _math.abs(x)


def math_sum(values: Any) -> float:
    return _math.sum(_coerce_iterable(values))


def math_product(values: Any) -> float:
    return _math.product(_coerce_iterable(values))


def math_mean(values: Any) -> float:
    return _math.mean(_coerce_iterable(values))


def math_median(values: Any) -> float:
    return _math.median(_coerce_iterable(values))


def math_variance(values: Any, sample: bool = False) -> float:
    return _math.variance(_coerce_iterable(values), sample=sample)


def math_stddev(values: Any, sample: bool = False) -> float:
    return _math.stddev(_coerce_iterable(values), sample=sample)


def math_minimum(values: Any) -> float:
    return _math.minimum(_coerce_iterable(values))


def math_maximum(values: Any) -> float:
    return _math.maximum(_coerce_iterable(values))


def math_dot(a: Any, b: Any) -> float:
    return _math.dot(_coerce_iterable(a), _coerce_iterable(b))


def math_magnitude(vec: Any) -> float:
    return _math.magnitude(_coerce_iterable(vec))


def math_normalize(vec: Any) -> Sequence[float]:
    return _math.normalize(_coerce_iterable(vec))


def math_distance(a: Any, b: Any) -> float:
    return _math.distance(_coerce_iterable(a), _coerce_iterable(b))


def math_is_close(
    a: Any,
    b: Any,
    rel_tol: float = 1e-9,
    abs_tol: float = 0.0,
) -> bool:
    return _math.is_close(a, b, rel_tol=rel_tol, abs_tol=abs_tol)


def math_hypot(values: Any) -> float:
    if values is None:
        raise TypeError("Expected an iterable of numbers")
    if isinstance(values, (list, tuple, set)):
        seq = values
    else:
        seq = list(values)
    return _math.hypot(*seq)


def math_gcd(a: Any, b: Any) -> int:
    return _math.gcd(a, b)


def math_lcm(a: Any, b: Any) -> int:
    return _math.lcm(a, b)


def math_factorial(n: Any) -> int:
    return _math.factorial(n)


def math_choose(n: Any, k: Any) -> int:
    return _math.choose(n, k)


def math_permute(n: Any, k: Any) -> int:
    return _math.permute(n, k)


__all__ = [
    "math_PI",
    "math_TAU",
    "math_E",
    "math_PHI",
    "math_add",
    "math_subtract",
    "math_multiply",
    "math_divide",
    "math_safe_divide",
    "math_mod",
    "math_pow",
    "math_sqrt",
    "math_cbrt",
    "math_sin",
    "math_cos",
    "math_tan",
    "math_asin",
    "math_acos",
    "math_atan",
    "math_atan2",
    "math_log",
    "math_log10",
    "math_exp",
    "math_sigmoid",
    "math_clamp",
    "math_lerp",
    "math_inv_lerp",
    "math_remap",
    "math_deg2rad",
    "math_rad2deg",
    "math_floor",
    "math_ceil",
    "math_round",
    "math_trunc",
    "math_abs",
    "math_sum",
    "math_product",
    "math_mean",
    "math_median",
    "math_variance",
    "math_stddev",
    "math_minimum",
    "math_maximum",
    "math_dot",
    "math_magnitude",
    "math_normalize",
    "math_distance",
    "math_is_close",
    "math_hypot",
    "math_gcd",
    "math_lcm",
    "math_factorial",
    "math_choose",
    "math_permute",
]
