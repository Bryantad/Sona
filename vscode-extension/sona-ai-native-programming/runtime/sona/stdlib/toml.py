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
