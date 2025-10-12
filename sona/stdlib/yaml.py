"""
Sona Standard Library - YAML Module

Provides safe YAML parsing and serialization.
Uses PyYAML with safe_load/safe_dump to prevent code execution.

Stability: stable
Version: 0.9.6
Dependencies: PyYAML >= 6.0
"""

__all__ = ['loads', 'dumps', 'load_safe', 'dump_safe']

try:
    import yaml as _yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    _yaml = None

def loads(yaml_string):
    """
    Parse YAML string to Python object.
    
    Uses safe_load to prevent code execution vulnerabilities.
    
    Args:
        yaml_string: YAML formatted string
        
    Returns:
        Parsed Python object (dict, list, str, int, float, bool, None)
        
    Raises:
        ImportError: If PyYAML is not installed
        yaml.YAMLError: If YAML is malformed
        
    Example:
        >>> data = loads("name: Sona\\nversion: 0.9.6")
        >>> data['name']
        'Sona'
    """
    if not YAML_AVAILABLE:
        raise ImportError(
            "PyYAML is required for YAML support. "
            "Install with: pip install PyYAML>=6.0"
        )
    
    try:
        return _yaml.safe_load(yaml_string)
    except _yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {e}")

def dumps(obj, **kwargs):
    """
    Serialize Python object to YAML string.
    
    Uses safe_dump for security.
    
    Args:
        obj: Python object to serialize
        **kwargs: Additional arguments passed to yaml.safe_dump
        
    Returns:
        str: YAML formatted string
        
    Raises:
        ImportError: If PyYAML is not installed
        
    Example:
        >>> data = {"name": "Sona", "version": 0.96}
        >>> yaml_str = dumps(data)
        >>> "name: Sona" in yaml_str
        True
    """
    if not YAML_AVAILABLE:
        raise ImportError(
            "PyYAML is required for YAML support. "
            "Install with: pip install PyYAML>=6.0"
        )
    
    # Set sensible defaults
    if 'default_flow_style' not in kwargs:
        kwargs['default_flow_style'] = False
    
    return _yaml.safe_dump(obj, **kwargs)

# Aliases for clarity
load_safe = loads
dump_safe = dumps
