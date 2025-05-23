"""Sona standard library: utils.math.smod"""

import math as python_math
import os
from .. import random

# Math module implementation for Sona v0.5.1

# Constants
PI = python_math.pi
E = python_math.e

class MathModule:
    def __init__(self):
        # Define mathematical constants
        self.PI = python_math.pi
        self.E = python_math.e
        if os.environ.get("SONA_DEBUG") == "1" and os.environ.get("SONA_MODULE_SILENT") != "1":
            print(f"[DEBUG] math module loaded: {self.PI}")

    # Basic arithmetic operations
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Division by zero")
        return a / b

    # Comparison operations
    def eq(self, a, b):
        """Equality comparison function"""
        return a == b

    def not_eq(self, a, b):
        return a != b

    def lt(self, a, b):
        return a < b

    def lte(self, a, b):
        return a <= b

    def gt(self, a, b):
        return a > b

    def gte(self, a, b):
        return a >= b

    # Utility functions
    def to_str(self, n):
        """Convert number to string"""
        return str(n)

    def parse_float(self, s):
        """Convert string to float"""
        try:
            return float(s)
        except ValueError:
            raise ValueError(f"Cannot convert '{s}' to number")

    def parse_int(self, s):
        """Convert string to integer"""
        try:
            return int(s)
        except ValueError:
            raise ValueError(f"Cannot convert '{s}' to integer")

    # Additional math functions
    def sqrt(self, x):
        if x < 0:
            raise ValueError("Cannot take square root of negative number")
        return python_math.sqrt(x)

    def pow(self, base, exp):
        return base ** exp

    def abs(self, x):
        return abs(x)

    def sin(self, x):
        return python_math.sin(x)

    def cos(self, x):
        return python_math.cos(x)

    def tan(self, x):
        return python_math.tan(x)

# ✅ Export as instance (required by Sona's dynamic loader)
math = MathModule()
__all__ = ["math"]
print("[DEBUG] math module loaded:", math.PI)
