"""
Collection utilities namespace for Sona v0.9.7+

This package provides specialized collection helpers under namespaced imports:
- collection.list: sequence operations (chunk, flatten, unique, window)
- collection.dict: dictionary operations (safe_get, merge, remap)
- collection.set: set operations (union, intersect, diff)
- collection.tuple: tuple operations (zipn, unzip, head_tail)

Example:
    import collection.list
    chunks = collection.list.chunk([1,2,3,4,5], 2)
    # → [[1,2], [3,4], [5]]
"""

__all__ = ["list", "dict", "set", "tuple"]
