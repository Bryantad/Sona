"""
Sona Standard Library - Comparison Operations Module

Provides safe comparison operations with explicit error handling.
Deterministic behavior with no implicit coercion across incompatible types.

Stability: stable
Version: 0.9.6
"""

__all__ = ['eq', 'neq', 'lt', 'lte', 'gt', 'gte',
           'equals', 'greater_than', 'less_than',
           'cmp', 'deep_equal', 'in_range', 'between', 'closest',
           'compare_with', 'min_by', 'max_by', 'clamp']

def eq(a, b):
    """
    Check equality of two values.
    
    Handles None safely and uses Python's equality semantics.
    
    Args:
        a: First value
        b: Second value
        
    Returns:
        bool: True if values are equal
        
    Example:
        >>> eq(3, 3)
        True
        >>> eq(None, None)
        True
        >>> eq("hello", "world")
        False
    """
    return a == b


def equals(a, b):
    return eq(a, b)

def neq(a, b):
    """
    Check inequality of two values.
    
    Args:
        a: First value
        b: Second value
        
    Returns:
        bool: True if values are not equal
        
    Example:
        >>> neq(3, 4)
        True
        >>> neq(5, 5)
        False
    """
    return a != b

def lt(a, b):
    """
    Check if first value is less than second.
    
    Args:
        a: First value
        b: Second value
        
    Returns:
        bool: True if a < b
        
    Raises:
        TypeError: If values cannot be compared
        
    Example:
        >>> lt(2, 3)
        True
        >>> lt(5, 5)
        False
    """
    try:
        return a < b
    except TypeError as e:
        raise TypeError(f"Cannot compare {type(a).__name__} with {type(b).__name__}: {e}")


def less_than(a, b):
    return lt(a, b)

def lte(a, b):
    """
    Check if first value is less than or equal to second.
    
    Args:
        a: First value
        b: Second value
        
    Returns:
        bool: True if a <= b
        
    Raises:
        TypeError: If values cannot be compared
        
    Example:
        >>> lte(3, 3)
        True
        >>> lte(2, 3)
        True
        >>> lte(4, 3)
        False
    """
    try:
        return a <= b
    except TypeError as e:
        raise TypeError(f"Cannot compare {type(a).__name__} with {type(b).__name__}: {e}")

def gt(a, b):
    """
    Check if first value is greater than second.
    
    Args:
        a: First value
        b: Second value
        
    Returns:
        bool: True if a > b
        
    Raises:
        TypeError: If values cannot be compared
        
    Example:
        >>> gt(5, 3)
        True
        >>> gt(2, 2)
        False
    """
    try:
        return a > b
    except TypeError as e:
        raise TypeError(f"Cannot compare {type(a).__name__} with {type(b).__name__}: {e}")


def greater_than(a, b):
    return gt(a, b)

def gte(a, b):
    """
    Check if first value is greater than or equal to second.
    
    Args:
        a: First value
        b: Second value
        
    Returns:
        bool: True if a >= b
        
    Raises:
        TypeError: If values cannot be compared
        
    Example:
        >>> gte(3, 3)
        True
        >>> gte(5, 3)
        True
        >>> gte(2, 3)
        False
    """
    try:
        return a >= b
    except TypeError as e:
        raise TypeError(f"Cannot compare {type(a).__name__} with {type(b).__name__}: {e}")

def cmp(a, b):
    """
    Three-way comparison returning -1, 0, or 1.
    
    Returns:
        -1 if a < b
         0 if a == b
         1 if a > b
    
    Args:
        a: First value
        b: Second value
        
    Returns:
        int: -1, 0, or 1
        
    Raises:
        TypeError: If values cannot be compared
        
    Example:
        >>> cmp(2, 3)
        -1
        >>> cmp(3, 3)
        0
        >>> cmp(5, 3)
        1
    """
    try:
        if a < b:
            return -1
        elif a > b:
            return 1
        else:
            return 0
    except TypeError as e:
        raise TypeError(
            f"Cannot perform three-way comparison between {type(a).__name__} and {type(b).__name__}. "
            f"Ensure both values are of comparable types (e.g., both numbers or both strings). Error: {e}"
        )

def deep_equal(a, b):
    """
    Deep equality check for nested structures.
    
    Recursively compares lists, dicts, sets, and tuples.
    For other types, uses standard equality.
    
    Args:
        a: First value
        b: Second value
        
    Returns:
        bool: True if structures are deeply equal
        
    Example:
        >>> deep_equal([1, 2, [3, 4]], [1, 2, [3, 4]])
        True
        >>> deep_equal({"a": [1, 2]}, {"a": [1, 2]})
        True
        >>> deep_equal([1, 2], [1, 3])
        False
    """
    # Fast path for identity
    if a is b:
        return True
    
    # Check types match
    if type(a) != type(b):
        return False
    
    # Handle collections recursively
    if isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return False
        return all(deep_equal(x, y) for x, y in zip(a, b))
    
    elif isinstance(a, dict):
        if a.keys() != b.keys():
            return False
        return all(deep_equal(a[k], b[k]) for k in a.keys())
    
    elif isinstance(a, set):
        # Sets use their own equality
        return a == b
    
    # For all other types, use standard equality
    return a == b


def in_range(value, start, end, inclusive=True):
    """
    Check if value is within range.
    
    Args:
        value: Value to check
        start: Range start
        end: Range end
        inclusive: Include boundaries (default: True)
        
    Returns:
        bool: True if value is in range
        
    Example:
        >>> in_range(5, 1, 10)
        True
        >>> in_range(10, 1, 10, inclusive=False)
        False
    """
    if inclusive:
        return start <= value <= end
    else:
        return start < value < end


def between(value, low, high):
    """
    Check if value is between low and high (inclusive).
    
    Args:
        value: Value to check
        low: Lower bound
        high: Upper bound
        
    Returns:
        bool: True if low <= value <= high
        
    Example:
        >>> between(5, 1, 10)
        True
        >>> between(0, 1, 10)
        False
    """
    return low <= value <= high


def closest(value, candidates):
    """
    Find closest value from candidates.
    
    Args:
        value: Target value
        candidates: List of candidate values
        
    Returns:
        Closest value from candidates
        
    Example:
        >>> closest(7, [1, 5, 10, 15])
        5
        >>> closest(12, [1, 5, 10, 15])
        10
    """
    if not candidates:
        raise ValueError("candidates list cannot be empty")
    
    return min(candidates, key=lambda x: abs(x - value))


def compare_with(value, other, comparator):
    """
    Compare using custom comparator function.
    
    Args:
        value: First value
        other: Second value
        comparator: Function that takes (a, b) and returns comparison
        
    Returns:
        Result of comparator(value, other)
        
    Example:
        >>> compare_with(5, 3, lambda a, b: a > b)
        True
        >>> compare_with("abc", "xyz", lambda a, b: len(a) == len(b))
        True
    """
    return comparator(value, other)


def min_by(items, key_func):
    """
    Find minimum item using key function.
    
    Args:
        items: Iterable of items
        key_func: Function to extract comparison key
        
    Returns:
        Item with minimum key value
        
    Example:
        >>> min_by(["a", "bbb", "cc"], len)
        'a'
        >>> min_by([{"age": 30}, {"age": 20}], lambda x: x["age"])
        {'age': 20}
    """
    if not items:
        raise ValueError("items cannot be empty")
    
    return min(items, key=key_func)


def max_by(items, key_func):
    """
    Find maximum item using key function.
    
    Args:
        items: Iterable of items
        key_func: Function to extract comparison key
        
    Returns:
        Item with maximum key value
        
    Example:
        >>> max_by(["a", "bbb", "cc"], len)
        'bbb'
        >>> max_by([{"age": 30}, {"age": 20}], lambda x: x["age"])
        {'age': 30}
    """
    if not items:
        raise ValueError("items cannot be empty")
    
    return max(items, key=key_func)


def clamp(value, min_val, max_val):
    """
    Clamp value to range [min_val, max_val].
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
        
    Example:
        >>> clamp(5, 0, 10)
        5
        >>> clamp(-5, 0, 10)
        0
        >>> clamp(15, 0, 10)
        10
    """
    if value < min_val:
        return min_val
    elif value > max_val:
        return max_val
    else:
        return value
