"""Numeric helpers."""
from __future__ import annotations

import math

INF = math.inf
NAN = math.nan
NEG_INF = -math.inf


def clamp(value: float, minimum: float, maximum: float) -> float:
    if minimum > maximum:
        raise ValueError("minimum cannot be greater than maximum")
    return max(minimum, min(maximum, value))


def is_nan(value: float) -> bool:
    return math.isnan(value)


def is_inf(value: float) -> bool:
    return math.isinf(value)


def is_finite(value: float) -> bool:
    return math.isfinite(value)


def safe_divide(value: float, divisor: float, fallback: float = 0.0) -> float:
    if divisor == 0:
        return fallback
    return value / divisor


def is_prime(value: int) -> bool:
    if value <= 1:
        return False
    if value <= 3:
        return True
    if value % 2 == 0 or value % 3 == 0:
        return False
    factor = 5
    while factor * factor <= value:
        if value % factor == 0 or value % (factor + 2) == 0:
            return False
        factor += 6
    return True


def is_even(value: int) -> bool:
    """
    Check if a number is even.

    Args:
        value: Integer to check

    Returns:
        True if even, False otherwise

    Example:
        is_even(4)  # True
        is_even(5)  # False
    """
    return value % 2 == 0


def is_odd(value: int) -> bool:
    """
    Check if a number is odd.

    Args:
        value: Integer to check

    Returns:
        True if odd, False otherwise

    Example:
        is_odd(5)  # True
        is_odd(4)  # False
    """
    return value % 2 != 0


def is_positive(value: float) -> bool:
    """Return True when value > 0."""
    return value > 0


def is_negative(value: float) -> bool:
    """Return True when value < 0."""
    return value < 0


def gcd(a: int, b: int) -> int:
    """
    Calculate greatest common divisor using Euclidean algorithm.

    Args:
        a: First integer
        b: Second integer

    Returns:
        Greatest common divisor

    Example:
        gcd(48, 18)  # 6
    """
    while b:
        a, b = b, a % b
    return abs(a)


def lcm(a: int, b: int) -> int:
    """
    Calculate least common multiple.

    Args:
        a: First integer
        b: Second integer

    Returns:
        Least common multiple

    Example:
        lcm(12, 18)  # 36
    """
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // gcd(a, b)


def factorial(n: int) -> int:
    """
    Calculate factorial of n.

    Args:
        n: Non-negative integer

    Returns:
        Factorial of n

    Example:
        factorial(5)  # 120
    """
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n <= 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def fibonacci(n: int) -> int:
    """
    Calculate nth Fibonacci number.

    Args:
        n: Index in Fibonacci sequence (0-indexed)

    Returns:
        nth Fibonacci number

    Example:
        fibonacci(6)  # 8
    """
    if n < 0:
        raise ValueError("Fibonacci not defined for negative indices")
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def is_perfect_square(value: int) -> bool:
    """
    Check if a number is a perfect square.

    Args:
        value: Integer to check

    Returns:
        True if perfect square, False otherwise

    Example:
        is_perfect_square(16)  # True
        is_perfect_square(15)  # False
    """
    if value < 0:
        return False
    root = int(value ** 0.5)
    return root * root == value


def is_power_of_two(value: int) -> bool:
    """
    Check if a number is a power of 2.

    Args:
        value: Integer to check

    Returns:
        True if power of 2, False otherwise

    Example:
        is_power_of_two(8)   # True
        is_power_of_two(10)  # False
    """
    return value > 0 and (value & (value - 1)) == 0


def round_to(value: float, precision: int = 0) -> float:
    """
    Round number to specified precision.

    Args:
        value: Number to round
        precision: Number of decimal places

    Returns:
        Rounded number

    Example:
        round_to(3.14159, 2)  # 3.14
    """
    return round(value, precision)


def in_range(value: float, minimum: float, maximum: float, inclusive: bool = True) -> bool:
    """
    Check if value is within range.

    Args:
        value: Value to check
        minimum: Minimum bound
        maximum: Maximum bound
        inclusive: Include bounds (default True)

    Returns:
        True if in range, False otherwise

    Example:
        in_range(5, 0, 10)  # True
        in_range(10, 0, 10, inclusive=False)  # False
    """
    if inclusive:
        return minimum <= value <= maximum
    return minimum < value < maximum


def sign(value: float) -> int:
    """
    Get sign of a number.

    Args:
        value: Number to check

    Returns:
        1 for positive, -1 for negative, 0 for zero

    Example:
        sign(5.3)   # 1
        sign(-2.1)  # -1
        sign(0)     # 0
    """
    if value > 0:
        return 1
    elif value < 0:
        return -1
    return 0


def digits(value: int) -> list[int]:
    """
    Get list of digits in a number.

    Args:
        value: Integer

    Returns:
        List of digits

    Example:
        digits(12345)  # [1, 2, 3, 4, 5]
    """
    return [int(d) for d in str(abs(value))]


__all__ = [
    "INF", "NEG_INF", "NAN",
    "clamp", "is_prime", "is_even", "is_odd", "gcd", "lcm",
    "factorial", "fibonacci", "is_perfect_square", "is_power_of_two",
    "round_to", "in_range", "sign", "digits",
    "is_nan", "is_inf", "is_finite", "safe_divide"
]
