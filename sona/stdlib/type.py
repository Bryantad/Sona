"""
Sona Standard Library - Type Inquiry Module

Provides type checking and type inquiry functions with canonical type names.
All operations are safe and never throw exceptions.

Stability: stable
Version: 0.9.6
"""

__all__ = [
    'typeof', 'type_of', 'is_int', 'is_float', 'is_number', 'is_string', 
    'is_bool', 'is_list', 'is_dict', 'is_set', 'is_tuple', 'is_none',
    'is_callable', 'is_iterable', 'is_numeric', 'is_empty',
    'get_type_name', 'cast', 'is_sequence'
]

# Type name mapping: Python type -> Sona canonical name
TYPE_MAP = {
    int: 'int',
    float: 'float',
    str: 'string',
    bool: 'bool',
    list: 'list',
    dict: 'dict',
    set: 'set',
    tuple: 'tuple',
    type(None): 'none',
    bytes: 'bytes',
    bytearray: 'bytearray',
}

def typeof(x):
    """
    Get canonical type name for a value.
    
    Returns Sona canonical type names:
    - 'int', 'float', 'number' (for int or float)
    - 'string', 'bool', 'none'
    - 'list', 'dict', 'set', 'tuple'
    - 'bytes', 'bytearray'
    - 'object' (for unknown types)
    
    Args:
        x: Value to inspect
        
    Returns:
        str: Canonical type name
        
    Example:
        >>> typeof(42)
        'int'
        >>> typeof("hello")
        'string'
        >>> typeof([1, 2, 3])
        'list'
    """
    python_type = type(x)
    return TYPE_MAP.get(python_type, 'object')


def type_of(x):
    return typeof(x)

def is_int(x):
    """
    Check if value is an integer.
    
    Note: Returns False for booleans (even though bool is subclass of int in Python).
    
    Args:
        x: Value to check
        
    Returns:
        bool: True if value is int (and not bool)
        
    Example:
        >>> is_int(42)
        True
        >>> is_int(3.14)
        False
        >>> is_int(True)
        False
    """
    return isinstance(x, int) and not isinstance(x, bool)

def is_float(x):
    """
    Check if value is a float.
    
    Args:
        x: Value to check
        
    Returns:
        bool: True if value is float
        
    Example:
        >>> is_float(3.14)
        True
        >>> is_float(42)
        False
    """
    return isinstance(x, float)

def is_number(x):
    """
    Check if value is a number (int or float).
    
    Args:
        x: Value to check
        
    Returns:
        bool: True if value is int or float
        
    Example:
        >>> is_number(42)
        True
        >>> is_number(3.14)
        True
        >>> is_number("42")
        False
    """
    return is_int(x) or is_float(x)

def is_string(x):
    """
    Check if value is a string.
    
    Args:
        x: Value to check
        
    Returns:
        bool: True if value is str
        
    Example:
        >>> is_string("hello")
        True
        >>> is_string(42)
        False
    """
    return isinstance(x, str)

def is_bool(x):
    """
    Check if value is a boolean.
    
    Args:
        x: Value to check
        
    Returns:
        bool: True if value is bool
        
    Example:
        >>> is_bool(True)
        True
        >>> is_bool(1)
        False
    """
    return isinstance(x, bool)

def is_list(x):
    """
    Check if value is a list.
    
    Args:
        x: Value to check
        
    Returns:
        bool: True if value is list
        
    Example:
        >>> is_list([1, 2, 3])
        True
        >>> is_list((1, 2, 3))
        False
    """
    return isinstance(x, list)

def is_dict(x):
    """
    Check if value is a dictionary.
    
    Args:
        x: Value to check
        
    Returns:
        bool: True if value is dict
        
    Example:
        >>> is_dict({"key": "value"})
        True
        >>> is_dict([])
        False
    """
    return isinstance(x, dict)

def is_set(x):
    """
    Check if value is a set.
    
    Args:
        x: Value to check
        
    Returns:
        bool: True if value is set
        
    Example:
        >>> is_set({1, 2, 3})
        True
        >>> is_set([1, 2, 3])
        False
    """
    return isinstance(x, set)

def is_tuple(x):
    """
    Check if value is a tuple.
    
    Args:
        x: Value to check
        
    Returns:
        bool: True if value is tuple
        
    Example:
        >>> is_tuple((1, 2, 3))
        True
        >>> is_tuple([1, 2, 3])
        False
    """
    return isinstance(x, tuple)

def is_none(x):
    """
    Check if value is None.
    
    Args:
        x: Value to check
        
    Returns:
        bool: True if value is None
        
    Example:
        >>> is_none(None)
        True
        >>> is_none(0)
        False
    """
    return x is None


def is_callable(x):
    """
    Check if value is callable (function, method, class, etc).
    
    Args:
        x: Value to check
        
    Returns:
        bool: True if value is callable
        
    Example:
        >>> is_callable(len)
        True
        >>> is_callable(42)
        False
    """
    return callable(x)


def is_iterable(x):
    """
    Check if value is iterable (can be used in for loops).
    
    Args:
        x: Value to check
        
    Returns:
        bool: True if value is iterable
        
    Example:
        >>> is_iterable([1, 2, 3])
        True
        >>> is_iterable("hello")
        True
        >>> is_iterable(42)
        False
    """
    try:
        iter(x)
        return True
    except TypeError:
        return False


def is_sequence(x):
    """
    Check if value is a sequence (list, tuple, or string).
    
    Args:
        x: Value to check
        
    Returns:
        bool: True if value is list, tuple, or string
        
    Example:
        >>> is_sequence([1, 2, 3])
        True
        >>> is_sequence((1, 2))
        True
        >>> is_sequence("hello")
        True
        >>> is_sequence({1, 2})
        False
    """
    return isinstance(x, (list, tuple, str))


def is_numeric(x):
    """
    Check if value is numeric (int, float, or numeric string).
    
    Args:
        x: Value to check
        
    Returns:
        bool: True if value is or can be converted to number
        
    Example:
        >>> is_numeric(42)
        True
        >>> is_numeric("42")
        True
        >>> is_numeric("hello")
        False
    """
    if is_number(x):
        return True
    
    if isinstance(x, str):
        try:
            float(x)
            return True
        except ValueError:
            return False
    
    return False


def is_empty(x):
    """
    Check if value is empty (empty collection, string, or None).
    
    Args:
        x: Value to check
        
    Returns:
        bool: True if value is empty or None
        
    Example:
        >>> is_empty([])
        True
        >>> is_empty("")
        True
        >>> is_empty(None)
        True
        >>> is_empty([1, 2])
        False
    """
    if x is None:
        return True
    
    if hasattr(x, '__len__'):
        return len(x) == 0
    
    return False


def get_type_name(x):
    """
    Get friendly type name (alias for typeof).
    
    Args:
        x: Value to inspect
        
    Returns:
        str: Human-readable type name
        
    Example:
        >>> get_type_name(42)
        'int'
        >>> get_type_name([1, 2])
        'list'
    """
    return typeof(x)


def cast(value, target_type):
    """
    Safely cast value to target type.
    
    Args:
        value: Value to cast
        target_type: Target type name ('int', 'float', 'string', 'bool')
        
    Returns:
        Casted value or original if cast fails
        
    Example:
        >>> cast("42", "int")
        42
        >>> cast(3.14, "int")
        3
        >>> cast("hello", "int")
        'hello'
    """
    try:
        if target_type == 'int':
            return int(value)
        elif target_type == 'float':
            return float(value)
        elif target_type == 'string' or target_type == 'str':
            return str(value)
        elif target_type == 'bool':
            return bool(value)
        elif target_type == 'list':
            return list(value)
        elif target_type == 'tuple':
            return tuple(value)
        elif target_type == 'set':
            return set(value)
        else:
            return value
    except (ValueError, TypeError):
        return value
