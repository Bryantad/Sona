"""Sona standard library: math module"""

import math


def sin(x): return math.sin(x)


def cos(x): return math.cos(x)


def tan(x): return math.tan(x)


def sqrt(x): return math.sqrt(x)


def pow(x, y): return x**y


def log(x, base = math.e): return math.log(x, base)


def floor(x): return math.floor(x)


def ceil(x): return math.ceil(x)


# ——— New helpers ———


def abs(x): """Absolute value"""
    return math.fabs(x)


def exp(x): """e**x"""
    return math.exp(x)


def log10(x): """Base‑10 logarithm"""
    return math.log10(x)


def hypot(x, y): """sqrt(x*x + y*y)"""
    return math.hypot(x, y)


def gcd(a, b): """Greatest Common Divisor"""
    return math.gcd(int(a), int(b))


def factorial(n): """n! for integer n ≥ 0"""
    return math.factorial(int(n))
