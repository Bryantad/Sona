"""
collection.list - Sequence operations for Sona stdlib

Provides utilities for working with lists and sequences:
- chunk: split sequence into fixed-size chunks
- flatten: flatten nested sequences
- unique: deduplicate while preserving order
- window: sliding window view over sequence
"""


def chunk(seq, n):
    """
    Split sequence into chunks of size n.
    
    Args:
        seq: Input sequence (list, tuple, string, etc.)
        n: Chunk size (must be > 0)
    
    Returns:
        List of chunks (last chunk may be smaller if len(seq) % n != 0)
    
    Example:
        chunk([1,2,3,4,5], 2) → [[1,2], [3,4], [5]]
        chunk("hello", 2) → ["he", "ll", "o"]
    """
    if n <= 0:
        raise ValueError("chunk size must be positive")
    
    result = []
    for i in range(0, len(seq), n):
        result.append(seq[i:i+n])
    return result


def flatten(nested):
    """
    Flatten one level of nesting.
    
    Args:
        nested: Sequence of sequences
    
    Returns:
        Single flattened list
    
    Example:
        flatten([[1,2], [3,4]]) → [1,2,3,4]
        flatten([["a"], ["b","c"]]) → ["a","b","c"]
    """
    result = []
    for item in nested:
        if isinstance(item, (list, tuple)):
            result.extend(item)
        else:
            result.append(item)
    return result


def unique(seq):
    """
    Remove duplicates while preserving order.
    
    Args:
        seq: Input sequence
    
    Returns:
        List with duplicates removed (first occurrence kept)
    
    Example:
        unique([1,2,1,3,2]) → [1,2,3]
        unique("hello") → ["h","e","l","o"]
    """
    seen = set()
    result = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def window(seq, k, step=1):
    """
    Sliding window view over sequence.
    
    Args:
        seq: Input sequence
        k: Window size
        step: Step size between windows (default 1)
    
    Returns:
        List of windows (each window is a slice of the sequence)
    
    Example:
        window([1,2,3,4,5], 3) → [[1,2,3], [2,3,4], [3,4,5]]
        window([1,2,3,4,5], 2, step=2) → [[1,2], [3,4]]
    """
    if k <= 0:
        raise ValueError("window size must be positive")
    if step <= 0:
        raise ValueError("step must be positive")
    
    result = []
    for i in range(0, len(seq) - k + 1, step):
        result.append(seq[i:i+k])
    return result
