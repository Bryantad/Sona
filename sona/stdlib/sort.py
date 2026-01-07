"""Sorting helpers for Sona programs."""
from __future__ import annotations

from typing import Iterable, List, Sequence, TypeVar, Callable, Optional
import heapq

T = TypeVar("T")


def sort(sequence: Iterable[T], order: str = "asc") -> list[T]:
    reverse = str(order).lower() in {"desc", "descending", "reverse"}
    return sorted(sequence, reverse=reverse)


def quicksort(sequence: Iterable[T], *, key: Optional[Callable[[T], T]] = None) -> list[T]:
    """Return a new list containing *sequence* sorted using quicksort.

    A ``key`` function can be provided; it behaves like ``sorted``.
    """

    data = list(sequence)
    if len(data) <= 1:
        return data

    keyfunc = key if key is not None else lambda x: x
    pivot = data[len(data) // 2]
    left = [item for item in data if keyfunc(item) < keyfunc(pivot)]
    middle = [item for item in data if keyfunc(item) == keyfunc(pivot)]
    right = [item for item in data if keyfunc(item) > keyfunc(pivot)]
    return quicksort(left, key=keyfunc) + middle + quicksort(right, key=keyfunc)


def mergesort(sequence: Iterable[T], *, key: Optional[Callable[[T], T]] = None) -> list[T]:
    data = list(sequence)
    if len(data) <= 1:
        return data

    keyfunc = key if key is not None else lambda x: x

    def merge(left: List[T], right: List[T]) -> List[T]:
        result: List[T] = []
        i = j = 0
        while i < len(left) and j < len(right):
            if keyfunc(left[i]) <= keyfunc(right[j]):
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        result.extend(left[i:])
        result.extend(right[j:])
        return result

    mid = len(data) // 2
    left = mergesort(data[:mid], key=keyfunc)
    right = mergesort(data[mid:], key=keyfunc)
    return merge(left, right)


def top_k(sequence: Iterable[T], k: int, *, key: Optional[Callable[[T], T]] = None) -> list[T]:
    """Return the ``k`` largest items from *sequence* preserving order."""

    if k < 0:
        raise ValueError("k must be non-negative")
    keyfunc = key if key is not None else None
    return heapq.nlargest(k, sequence, key=keyfunc)


def bottom_k(sequence: Iterable[T], k: int, *, key: Optional[Callable[[T], T]] = None) -> list[T]:
    """
    Return the k smallest items from sequence.
    
    Args:
        sequence: Input sequence
        k: Number of items to return
        key: Optional key function
    
    Returns:
        List of k smallest items
    
    Example:
        smallest = sort.bottom_k([5, 2, 8, 1, 9], 3)  # [1, 2, 5]
    """
    if k < 0:
        raise ValueError("k must be non-negative")
    keyfunc = key if key is not None else None
    return heapq.nsmallest(k, sequence, key=keyfunc)


def is_sorted(sequence: Sequence[T], reverse: bool = False) -> bool:
    """
    Check if sequence is sorted.
    
    Args:
        sequence: Sequence to check
        reverse: If True, check descending order
    
    Returns:
        True if sorted
    
    Example:
        sorted_asc = sort.is_sorted([1, 2, 3])  # True
    """
    if len(sequence) <= 1:
        return True
    
    if reverse:
        return all(sequence[i] >= sequence[i+1] for i in range(len(sequence)-1))
    else:
        return all(sequence[i] <= sequence[i+1] for i in range(len(sequence)-1))


def sort_by_frequency(sequence: Iterable[T]) -> list[T]:
    """
    Sort elements by frequency (most frequent first).
    
    Args:
        sequence: Input sequence
    
    Returns:
        Sorted list
    
    Example:
        result = sort.sort_by_frequency([1, 2, 2, 3, 3, 3])
        # [3, 3, 3, 2, 2, 1]
    """
    from collections import Counter
    counts = Counter(sequence)
    return sorted(sequence, key=lambda x: (-counts[x], x))


def stable_sort(sequence: Iterable[T], *, key: Optional[Callable[[T], T]] = None) -> list[T]:
    """
    Stable sort (preserves relative order of equal elements).
    
    Args:
        sequence: Input sequence
        key: Optional key function
    
    Returns:
        Sorted list
    
    Example:
        result = sort.stable_sort(items, key=lambda x: x['priority'])
    """
    return sorted(sequence, key=key)


def natural_sort(sequence: Iterable[str]) -> list[str]:
    """
    Natural (human-friendly) sort for strings with numbers.
    
    Args:
        sequence: String sequence
    
    Returns:
        Naturally sorted list
    
    Example:
        result = sort.natural_sort(['file1', 'file10', 'file2'])
        # ['file1', 'file2', 'file10']
    """
    import re
    
    def natural_key(text):
        return [int(c) if c.isdigit() else c.lower() 
                for c in re.split(r'(\d+)', text)]
    
    return sorted(sequence, key=natural_key)


def reverse_sort(sequence: Iterable[T], *, key: Optional[Callable[[T], T]] = None) -> list[T]:
    """
    Sort in descending order.
    
    Args:
        sequence: Input sequence
        key: Optional key function
    
    Returns:
        Reverse sorted list
    
    Example:
        result = sort.reverse_sort([1, 5, 3])  # [5, 3, 1]
    """
    return sorted(sequence, key=key, reverse=True)


def insertion_sort(sequence: Iterable[T]) -> list[T]:
    """
    Sort using insertion sort algorithm.
    
    Args:
        sequence: Input sequence
    
    Returns:
        Sorted list
    
    Example:
        result = sort.insertion_sort([5, 2, 8, 1])
    """
    arr = list(sequence)
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr


__all__ = [
    "sort", "quicksort", "mergesort", "top_k", "bottom_k",
    "is_sorted", "sort_by_frequency", "stable_sort",
    "natural_sort", "reverse_sort", "insertion_sort"
]
