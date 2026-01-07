"""
Sona Standard Library - TOML Module

Provides TOML parsing and serialization.
Uses Python's built-in tomllib for parsing (Python 3.11+).

Stability: stable
Version: 0.9.6
"""

__all__ = ['loads', 'dumps']

import sys

# Try to import tomllib (Python 3.11+)
try:
    import tomllib as _tomllib
    TOMLLIB_AVAILABLE = True
except ImportError:
    TOMLLIB_AVAILABLE = False
    _tomllib = None

# For dumps, we need a TOML writer
try:
    import tomli_w as _tomli_w
    TOMLI_W_AVAILABLE = True
except ImportError:
    TOMLI_W_AVAILABLE = False
    _tomli_w = None

def loads(toml_string):
    """
    Parse TOML string to Python dict.
    
    Args:
        toml_string: TOML formatted string
        
    Returns:
        dict: Parsed TOML data
        
    Raises:
        ImportError: If tomllib is not available (Python < 3.11)
        ValueError: If TOML is malformed
        
    Example:
        >>> data = loads('title = "Sona"\\nversion = "0.9.6"')
        >>> data['title']
        'Sona'
    """
    if not TOMLLIB_AVAILABLE:
        raise ImportError(
            "tomllib is not available. "
            "Requires Python 3.11+ or install tomli: pip install tomli"
        )
    
    try:
        # tomllib.loads requires bytes in Python 3.11
        if isinstance(toml_string, str):
            toml_string = toml_string.encode('utf-8')
        return _tomllib.loads(toml_string.decode('utf-8'))
    except Exception as e:
        raise ValueError(f"Invalid TOML: {e}")

def dumps(obj, **kwargs):
    """
    Serialize Python dict to TOML string.
    
    Note: Requires tomli_w package for serialization.
    
    Args:
        obj: Python dict to serialize
        **kwargs: Additional arguments (reserved for future use)
        
    Returns:
        str: TOML formatted string
        
    Raises:
        ImportError: If tomli_w is not installed
        TypeError: If obj is not a dict or contains unsupported types
        
    Example:
        >>> data = {"title": "Sona", "version": "0.9.6"}
        >>> toml_str = dumps(data)
        >>> 'title = "Sona"' in toml_str
        True
    """
    if not TOMLI_W_AVAILABLE:
        raise ImportError(
            "tomli_w is required for TOML serialization. "
            "Install with: pip install tomli-w"
        )
    
    try:
        return _tomli_w.dumps(obj, **kwargs)
    except (TypeError, ValueError) as e:
        raise TypeError(f"Cannot serialize to TOML: {e}")


def load(filepath):
    """
    Load TOML from file.
    
    Args:
        filepath: Path to TOML file
    
    Returns:
        dict: Parsed TOML data
    
    Example:
        >>> data = toml.load("config.toml")
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return loads(f.read())


def dump(obj, filepath):
    """
    Write TOML to file.
    
    Args:
        obj: Python dict to serialize
        filepath: Path to output file
    
    Example:
        >>> toml.dump({"key": "value"}, "config.toml")
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(dumps(obj))


def get(data, key, default=None):
    """
    Get value from TOML data with dot notation.
    
    Args:
        data: TOML dict
        key: Key with dot notation (e.g., "section.subsection.key")
        default: Default value if not found
    
    Returns:
        Value or default
    
    Example:
        >>> toml.get(data, "database.host", "localhost")
    """
    keys = key.split('.')
    value = data
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value


def set_value(data, key, value):
    """
    Set value in TOML data with dot notation.
    
    Args:
        data: TOML dict
        key: Key with dot notation
        value: Value to set
    
    Example:
        >>> toml.set_value(data, "database.port", 5432)
    """
    keys = key.split('.')
    current = data
    
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    current[keys[-1]] = value


def has(data, key):
    """
    Check if key exists in TOML data.
    
    Args:
        data: TOML dict
        key: Key with dot notation
    
    Returns:
        bool: True if exists
    
    Example:
        >>> toml.has(data, "database.host")
    """
    keys = key.split('.')
    value = data
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return False
    
    return True


def merge(base, override):
    """
    Merge two TOML dicts.
    
    Args:
        base: Base dict
        override: Override dict
    
    Returns:
        Merged dict
    
    Example:
        >>> merged = toml.merge(config1, config2)
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    
    return result


def validate(toml_string):
    """
    Validate TOML string.
    
    Args:
        toml_string: TOML string to validate
    
    Returns:
        bool: True if valid
    
    Example:
        >>> toml.validate('key = "value"')
        True
    """
    try:
        loads(toml_string)
        return True
    except Exception:
        return False


def to_dict(toml_string):
    """
    Parse TOML to dict (alias for loads).
    
    Args:
        toml_string: TOML string
    
    Returns:
        dict: Parsed data
    
    Example:
        >>> data = toml.to_dict(toml_str)
    """
    return loads(toml_string)


def from_dict(obj):
    """
    Convert dict to TOML (alias for dumps).
    
    Args:
        obj: Python dict
    
    Returns:
        str: TOML string
    
    Example:
        >>> toml_str = toml.from_dict(data)
    """
    return dumps(obj)


__all__ = [
    'loads', 'dumps', 'load', 'dump', 'get', 'set_value',
    'has', 'merge', 'validate', 'to_dict', 'from_dict'
]
