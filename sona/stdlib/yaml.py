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


def load(filepath):
    """
    Load YAML from file.
    
    Args:
        filepath: Path to YAML file
    
    Returns:
        Parsed Python object
    
    Example:
        >>> data = yaml.load("config.yaml")
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return loads(f.read())


def dump(obj, filepath, **kwargs):
    """
    Write YAML to file.
    
    Args:
        obj: Python object to serialize
        filepath: Path to output file
        **kwargs: Additional yaml.dump arguments
    
    Example:
        >>> yaml.dump({"key": "value"}, "config.yaml")
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(dumps(obj, **kwargs))


def load_all(yaml_string):
    """
    Load multiple YAML documents from string.
    
    Args:
        yaml_string: YAML string with multiple documents
    
    Returns:
        List of parsed documents
    
    Example:
        >>> docs = yaml.load_all("---\\ndoc1\\n---\\ndoc2")
    """
    if not YAML_AVAILABLE:
        raise ImportError("PyYAML is required")
    
    try:
        return list(_yaml.safe_load_all(yaml_string))
    except _yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {e}")


def dump_all(objects, **kwargs):
    """
    Dump multiple objects as YAML documents.
    
    Args:
        objects: List of objects to serialize
        **kwargs: Additional yaml.dump arguments
    
    Returns:
        YAML string with multiple documents
    
    Example:
        >>> yaml_str = yaml.dump_all([obj1, obj2])
    """
    if not YAML_AVAILABLE:
        raise ImportError("PyYAML is required")
    
    if 'default_flow_style' not in kwargs:
        kwargs['default_flow_style'] = False
    
    return _yaml.safe_dump_all(objects, **kwargs)


def get(data, key, default=None):
    """
    Get value from YAML data with dot notation.
    
    Args:
        data: YAML dict
        key: Key with dot notation
        default: Default value if not found
    
    Returns:
        Value or default
    
    Example:
        >>> yaml.get(data, "database.host", "localhost")
    """
    keys = key.split('.')
    value = data
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value


def merge(base, override):
    """
    Merge two YAML dicts recursively.
    
    Args:
        base: Base dict
        override: Override dict
    
    Returns:
        Merged dict
    
    Example:
        >>> merged = yaml.merge(config1, config2)
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    
    return result


def validate(yaml_string):
    """
    Validate YAML string.
    
    Args:
        yaml_string: YAML string to validate
    
    Returns:
        bool: True if valid
    
    Example:
        >>> yaml.validate("key: value")
        True
    """
    try:
        loads(yaml_string)
        return True
    except Exception:
        return False


def to_dict(yaml_string):
    """
    Parse YAML to dict (alias for loads).
    
    Args:
        yaml_string: YAML string
    
    Returns:
        Parsed data
    
    Example:
        >>> data = yaml.to_dict(yaml_str)
    """
    return loads(yaml_string)


def from_dict(obj, **kwargs):
    """
    Convert dict to YAML (alias for dumps).
    
    Args:
        obj: Python object
        **kwargs: Additional yaml.dump arguments
    
    Returns:
        YAML string
    
    Example:
        >>> yaml_str = yaml.from_dict(data)
    """
    return dumps(obj, **kwargs)


def pretty_print(obj):
    """
    Pretty print object as YAML.
    
    Args:
        obj: Python object
    
    Example:
        >>> yaml.pretty_print({"name": "Sona", "version": "0.9.7"})
    """
    print(dumps(obj))


__all__ = [
    'loads', 'dumps', 'load_safe', 'dump_safe', 'load', 'dump',
    'load_all', 'dump_all', 'get', 'merge', 'validate',
    'to_dict', 'from_dict', 'pretty_print'
]
