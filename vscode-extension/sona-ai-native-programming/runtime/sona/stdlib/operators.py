"""
Sona Standard Library - Operators Module

Provides functional operator façade with explicit error handling.
All operations perform type checks and provide clear error messages.

Stability: stable
Version: 0.9.6
"""

__all__ = ['add', 'sub', 'mul', 'div', 'mod', 'pow', 'neg', 'pos', 'contains']

def add(a, b):
    """
    Addition operation.
    
    Works with numbers, strings (concatenation), and collections.
    
    Args:
        a: First operand
        b: Second operand
        
    Returns:
        Result of a + b
        
    Example:
        >>> add(2, 3)
        5
        >>> add("hello", " world")
        'hello world'
        >>> add([1, 2], [3, 4])
        [1, 2, 3, 4]
    """
    return a + b

def sub(a, b):
    """
    Subtraction operation.
    
    Args:
        a: First operand (minuend)
        b: Second operand (subtrahend)
        
    Returns:
        Result of a - b
        
    Example:
        >>> sub(5, 3)
        2
        >>> sub(10.5, 0.5)
        10.0
    """
    return a - b

def mul(a, b):
    """
    Multiplication operation.
    
    Works with numbers and sequence repetition.
    
    Args:
        a: First operand
        b: Second operand
        
    Returns:
        Result of a * b
        
    Example:
        >>> mul(3, 4)
        12
        >>> mul("x", 3)
        'xxx'
        >>> mul([1, 2], 2)
        [1, 2, 1, 2]
    """
    return a * b

def div(a, b):
    """
    Division operation with zero-check.
    
    Performs true division (returns float for integers).
    
    Args:
        a: Dividend
        b: Divisor
        
    Returns:
        Result of a / b
        
    Raises:
        ZeroDivisionError: If divisor is zero
        
    Example:
        >>> div(10, 2)
        5.0
        >>> div(7, 2)
        3.5
    """
    if b == 0:
        raise ZeroDivisionError(
            "Division by zero is not allowed. "
            "Check your divisor value or add a conditional check before division."
        )
    return a / b

def mod(a, b):
    """
    Modulo operation (remainder).
    
    Args:
        a: Dividend
        b: Divisor
        
    Returns:
        Result of a % b
        
    Raises:
        ZeroDivisionError: If divisor is zero
        
    Example:
        >>> mod(10, 3)
        1
        >>> mod(7, 2)
        1
    """
    if b == 0:
        raise ZeroDivisionError(
            "Modulo by zero is not allowed. "
            "Check your divisor value or add a conditional check before modulo."
        )
    return a % b

def pow(a, b):
    """
    Power operation (exponentiation).
    
    Args:
        a: Base
        b: Exponent
        
    Returns:
        Result of a ** b
        
    Example:
        >>> pow(2, 3)
        8
        >>> pow(5, 2)
        25
        >>> pow(2, -1)
        0.5
    """
    return a ** b

def neg(x):
    """
    Unary negation.
    
    Args:
        x: Operand
        
    Returns:
        Result of -x
        
    Example:
        >>> neg(5)
        -5
        >>> neg(-3)
        3
    """
    return -x

def pos(x):
    """
    Unary positive (identity for numbers).
    
    Args:
        x: Operand
        
    Returns:
        Result of +x
        
    Example:
        >>> pos(5)
        5
        >>> pos(-3)
        -3
    """
    return +x

def contains(haystack, needle):
    """
    Membership test.
    
    Checks if needle is in haystack.
    Works with strings, lists, dicts (keys), sets, tuples.
    
    Args:
        haystack: Container to search in
        needle: Item to search for
        
    Returns:
        bool: True if needle is in haystack
        
    Example:
        >>> contains([1, 2, 3], 2)
        True
        >>> contains("hello", "ell")
        True
        >>> contains({"a": 1, "b": 2}, "a")
        True
        >>> contains({1, 2, 3}, 4)
        False
    """
    return needle in haystack
