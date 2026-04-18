"""
collection.tuple - Tuple operations for Sona stdlib

Provides utilities for working with tuples and zipping:
- zipn: zip multiple sequences into tuples
- unzip: unzip sequence of tuples into separate sequences
- head_tail: split tuple into head and tail
"""


def zipn(*seqs):
    """
    Zip multiple sequences into list of tuples.
    
    Args:
        *seqs: Variable number of sequences to zip
    
    Returns:
        List of tuples (stops at shortest sequence length)
    
    Example:
        zipn([1,2,3], ["a","b","c"]) → [(1,"a"), (2,"b"), (3,"c")]
        zipn([1,2], [10,20,30]) → [(1,10), (2,20)]
    """
    if not seqs:
        return []
    
    min_len = min(len(s) for s in seqs)
    result = []
    for i in range(min_len):
        result.append(tuple(s[i] for s in seqs))
    return result


def unzip(seq_of_tuples):
    """
    Unzip sequence of tuples into separate lists.
    
    Args:
        seq_of_tuples: Sequence of tuples (all must have same length)
    
    Returns:
        List of lists (one per tuple position)
    
    Example:
        unzip([(1,"a"), (2,"b")]) → [[1,2], ["a","b"]]
        unzip([(1,2,3), (4,5,6)]) → [[1,4], [2,5], [3,6]]
    """
    if not seq_of_tuples:
        return []
    
    # Validate all tuples have same length
    first_len = len(seq_of_tuples[0])
    for t in seq_of_tuples:
        if len(t) != first_len:
            raise ValueError("all tuples must have same length")
    
    result = [[] for _ in range(first_len)]
    for t in seq_of_tuples:
        for i, val in enumerate(t):
            result[i].append(val)
    return result


def head_tail(t):
    """
    Split tuple into head (first element) and tail (rest).
    
    Args:
        t: Tuple or sequence
    
    Returns:
        Tuple of (head, tail) where tail is a list
    
    Example:
        head_tail((1,2,3)) → (1, [2,3])
        head_tail([1]) → (1, [])
    """
    if not t:
        raise ValueError("cannot split empty tuple")
    
    return (t[0], list(t[1:]))
