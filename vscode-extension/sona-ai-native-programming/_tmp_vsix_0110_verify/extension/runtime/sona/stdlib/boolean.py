"""
Sona Standard Library - Boolean Operations Module

Provides deterministic boolean logic operations with explicit coercion rules.
All operations are pure and side-effect free.

Stability: stable
Version: 0.9.6
"""

__all__ = ['and_', 'or_', 'not_', 'xor', 'coerce', 'is_truthy', 'is_falsy',
           'nand', 'nor', 'implies', 'all_true', 'any_true']

def coerce(x):
    """
    Convert common truthy/falsy values to True/False.
    
    Coercion rules:
    - None, 0, 0.0, "", [], {}, set(), () → False
    - Non-empty strings, non-zero numbers, non-empty collections → True
    - Explicit booleans pass through
    
    Args:
        x: Any value to coerce to boolean
        
    Returns:
        bool: True or False
        
    Example:
        >>> coerce(1)
        True
        >>> coerce(0)
        False
        >>> coerce("yes")
        True
        >>> coerce("")
        False
    """
    return bool(x)

def is_truthy(x):
    """
    Check if value is truthy (coerces to True).
    
    Args:
        x: Value to check
        
    Returns:
        bool: True if value is truthy
        
    Example:
        >>> is_truthy("yes")
        True
        >>> is_truthy(0)
        False
    """
    return coerce(x)

def is_falsy(x):
    """
    Check if value is falsy (coerces to False).
    
    Args:
        x: Value to check
        
    Returns:
        bool: True if value is falsy
        
    Example:
        >>> is_falsy("")
        True
        >>> is_falsy(1)
        False
    """
    return not coerce(x)

def and_(a, b):
    """
    Logical AND operation with explicit coercion.
    
    Args:
        a: First operand (will be coerced to bool)
        b: Second operand (will be coerced to bool)
        
    Returns:
        bool: True if both operands are truthy
        
    Example:
        >>> and_(True, True)
        True
        >>> and_(1, 0)
        False
    """
    return coerce(a) and coerce(b)

def or_(a, b):
    """
    Logical OR operation with explicit coercion.
    
    Args:
        a: First operand (will be coerced to bool)
        b: Second operand (will be coerced to bool)
        
    Returns:
        bool: True if either operand is truthy
        
    Example:
        >>> or_(False, True)
        True
        >>> or_(0, 0)
        False
    """
    return coerce(a) or coerce(b)

def not_(x):
    """
    Logical NOT operation (negation).
    
    Args:
        x: Operand (will be coerced to bool)
        
    Returns:
        bool: Negation of coerced value
        
    Example:
        >>> not_(True)
        False
        >>> not_(0)
        True
    """
    return not coerce(x)

def xor(a, b):
    """
    Logical XOR (exclusive or) operation.
    
    Returns True if exactly one operand is truthy.
    
    Args:
        a: First operand (will be coerced to bool)
        b: Second operand (will be coerced to bool)
        
    Returns:
        bool: True if exactly one operand is truthy
        
    Example:
        >>> xor(True, False)
        True
        >>> xor(True, True)
        False
        >>> xor(1, 0)
        True
    """
    return coerce(a) != coerce(b)


def nand(a, b):
    """
    Logical NAND (NOT AND) operation.
    
    Returns True unless both operands are truthy.
    
    Args:
        a: First operand (will be coerced to bool)
        b: Second operand (will be coerced to bool)
        
    Returns:
        bool: NOT (a AND b)
        
    Example:
        >>> nand(True, True)
        False
        >>> nand(True, False)
        True
    """
    return not (coerce(a) and coerce(b))


def nor(a, b):
    """
    Logical NOR (NOT OR) operation.
    
    Returns True only if both operands are falsy.
    
    Args:
        a: First operand (will be coerced to bool)
        b: Second operand (will be coerced to bool)
        
    Returns:
        bool: NOT (a OR b)
        
    Example:
        >>> nor(False, False)
        True
        >>> nor(True, False)
        False
    """
    return not (coerce(a) or coerce(b))


def implies(a, b):
    """
    Logical implication operation (a → b).
    
    Returns False only when a is true and b is false.
    Equivalent to: NOT a OR b
    
    Args:
        a: Antecedent (will be coerced to bool)
        b: Consequent (will be coerced to bool)
        
    Returns:
        bool: True unless a is true and b is false
        
    Example:
        >>> implies(True, True)
        True
        >>> implies(True, False)
        False
        >>> implies(False, False)
        True
    """
    return not coerce(a) or coerce(b)


def all_true(*args):
    """
    Check if all arguments are truthy.
    
    Args:
        *args: Variable number of arguments
        
    Returns:
        bool: True if all arguments are truthy
        
    Example:
        >>> all_true(1, "yes", [1])
        True
        >>> all_true(1, 0, "yes")
        False
    """
    return all(coerce(x) for x in args)


def any_true(*args):
    """
    Check if any argument is truthy.
    
    Args:
        *args: Variable number of arguments
        
    Returns:
        bool: True if at least one argument is truthy
        
    Example:
        >>> any_true(0, "", 1)
        True
        >>> any_true(0, "", [])
        False
    """
    return any(coerce(x) for x in args)


# Sona-facing aliases (can't use `def and(...)` / `def not(...)` in Python)
globals().setdefault('and', and_)
globals().setdefault('or', or_)
globals().setdefault('not', not_)
