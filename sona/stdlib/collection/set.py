"""
collection.set - Set operations for Sona stdlib

Provides utilities for working with sets:
- union: combine multiple sets
- intersect: find common elements
- diff: set difference

All operations return deterministic sorted output for reproducibility.
"""


def union(*sets):
    """
    Union of multiple sets (deterministic sorted output).
    
    Args:
        *sets: Variable number of iterables to union
    
    Returns:
        Sorted list of unique elements from all sets
    
    Example:
        union([1,2], [2,3]) → [1,2,3]
        union([1,2], [3,4], [5,6]) → [1,2,3,4,5,6]
    """
    result = set()
    for s in sets:
        result.update(s)
    return sorted(result)


def intersect(*sets):
    """
    Intersection of multiple sets (deterministic sorted output).
    
    Args:
        *sets: Variable number of iterables to intersect
    
    Returns:
        Sorted list of elements common to all sets
    
    Example:
        intersect([1,2,3], [2,3,4]) → [2,3]
        intersect([1,2], [2,3], [2,4]) → [2]
    """
    if not sets:
        return []
    
    result = set(sets[0])
    for s in sets[1:]:
        result.intersection_update(s)
    return sorted(result)


def diff(a, b):
    """
    Set difference: elements in a but not in b (deterministic sorted output).
    
    Args:
        a: First set
        b: Second set
    
    Returns:
        Sorted list of elements in a but not in b
    
    Example:
        diff([1,2,3], [2,3,4]) → [1]
        diff([1,2], [3,4]) → [1,2]
    """
    result = set(a) - set(b)
    return sorted(result)
