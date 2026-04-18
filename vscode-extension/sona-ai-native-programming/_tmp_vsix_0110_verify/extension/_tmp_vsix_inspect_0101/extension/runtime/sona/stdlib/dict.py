"""
collection.dict - Dictionary operations for Sona stdlib

Provides utilities for working with dictionaries:
- safe_get: get with default value
- merge: combine dictionaries with conflict resolution
- remap: transform dictionary keys via mapping
"""


def safe_get(d, k, default=None):
    """
    Safely get value from dictionary with default.
    
    Args:
        d: Dictionary to query
        k: Key to look up
        default: Value to return if key not found (default None)
    
    Returns:
        d[k] if k exists, otherwise default
    
    Example:
        safe_get({"a": 1}, "a") → 1
        safe_get({"a": 1}, "b", 0) → 0
    """
    return d.get(k, default)


def merge(a, b, mode="prefer_right"):
    """
    Merge two dictionaries with conflict resolution.
    
    Args:
        a: First dictionary
        b: Second dictionary
        mode: Conflict resolution mode:
            - "prefer_right": b values override a (default)
            - "prefer_left": a values override b
            - "error": raise error on key collision
    
    Returns:
        New merged dictionary
    
    Example:
        merge({"x": 1}, {"y": 2}) → {"x": 1, "y": 2}
        merge({"x": 1}, {"x": 2}, "prefer_right") → {"x": 2}
        merge({"x": 1}, {"x": 2}, "prefer_left") → {"x": 1}
    """
    if mode not in ("prefer_right", "prefer_left", "error"):
        raise ValueError(f"invalid merge mode: {mode}")
    
    result = dict(a)
    
    for k, v in b.items():
        if k in result:
            if mode == "error":
                raise KeyError(f"key collision: {k}")
            elif mode == "prefer_right":
                result[k] = v
            # else prefer_left: keep existing value
        else:
            result[k] = v
    
    return result


def remap(d, mapping):
    """
    Transform dictionary keys via mapping.
    
    Args:
        d: Dictionary to transform
        mapping: Dict mapping old keys to new keys
    
    Returns:
        New dictionary with remapped keys
    
    Example:
        remap({"a": 1, "b": 2}, {"a": "x"}) → {"x": 1, "b": 2}
        remap({"a": 1, "b": 2}, {"a": "x", "b": "x"}) → {"x": 2}  # last wins
    """
    result = {}
    
    for k, v in d.items():
        new_key = mapping.get(k, k)  # use mapping if exists, else keep original
        result[new_key] = v  # last write wins on collision
    
    return result
