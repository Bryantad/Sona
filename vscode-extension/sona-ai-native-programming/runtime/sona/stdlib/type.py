"""
Sona Standard Library - Type Inquiry Module

Provides type checking and type inquiry functions with canonical type names.
All operations are safe and never throw exceptions.

Stability: stable
Version: 0.9.6
"""

__all__ = [
    'typeof', 'is_int', 'is_float', 'is_number', 'is_string', 
    'is_bool', 'is_list', 'is_dict', 'is_set', 'is_tuple', 'is_none'
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
