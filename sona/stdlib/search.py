"""Search helpers for Sona programs."""
from __future__ import annotations

from typing import Iterable, Sequence, TypeVar

T = TypeVar("T")


def linear_search(sequence: Iterable[T], target: T) -> int:
    """Return the index of *target* in *sequence* using linear scan.

    Returns ``-1`` when the value is missing.
    """

    for index, value in enumerate(sequence):
        if value == target:
            return index
    return -1


def index_of(sequence: Iterable[T], target: T) -> int:
    return linear_search(sequence, target)


def contains(sequence: Iterable[T], target: T) -> bool:
    return linear_search(sequence, target) != -1


def binary_search(sequence: Sequence[T], target: T) -> int:
    """Return the index of *target* in a sorted *sequence*.

    The sequence **must** be sorted in ascending order. Returns ``-1`` when the
    element is absent.
    """

    lo = 0
    hi = len(sequence) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        value = sequence[mid]
        if value == target:
            return mid
        if value < target:  # type: ignore[operator]
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def find_all(sequence: Iterable[T], target: T) -> list[int]:
    """Return a list of all indices where *target* appears."""

    return [idx for idx, value in enumerate(sequence) if value == target]


def find_first(sequence: Iterable[T], predicate) -> T | None:
    """
    Find first element matching predicate.
    
    Args:
        sequence: Sequence to search
        predicate: Function returning True for match
    
    Returns:
        First matching element or None
    
    Example:
        first = search.find_first([1, 2, 3, 4], lambda x: x > 2)  # 3
    """
    for item in sequence:
        if predicate(item):
            return item
    return None


def find_last(sequence: Sequence[T], predicate) -> T | None:
    """
    Find last element matching predicate.
    
    Args:
        sequence: Sequence to search
        predicate: Function returning True for match
    
    Returns:
        Last matching element or None
    
    Example:
        last = search.find_last([1, 2, 3, 4], lambda x: x > 2)  # 4
    """
    for item in reversed(sequence):
        if predicate(item):
            return item
    return None


def find_min(sequence: Iterable[T], key=None) -> T | None:
    """
    Find minimum element.
    
    Args:
        sequence: Sequence to search
        key: Optional key function
    
    Returns:
        Minimum element or None if empty
    
    Example:
        min_val = search.find_min([5, 2, 8, 1])  # 1
    """
    try:
        return min(sequence, key=key)
    except ValueError:
        return None


def find_max(sequence: Iterable[T], key=None) -> T | None:
    """
    Find maximum element.
    
    Args:
        sequence: Sequence to search
        key: Optional key function
    
    Returns:
        Maximum element or None if empty
    
    Example:
        max_val = search.find_max([5, 2, 8, 1])  # 8
    """
    try:
        return max(sequence, key=key)
    except ValueError:
        return None


def contains_any(sequence: Iterable[T], targets: Iterable[T]) -> bool:
    """
    Check if sequence contains any of the targets.
    
    Args:
        sequence: Sequence to search
        targets: Target values
    
    Returns:
        True if any target found
    
    Example:
        found = search.contains_any([1, 2, 3], [3, 4, 5])  # True
    """
    target_set = set(targets)
    return any(item in target_set for item in sequence)


def contains_all(sequence: Iterable[T], targets: Iterable[T]) -> bool:
    """
    Check if sequence contains all of the targets.
    
    Args:
        sequence: Sequence to search
        targets: Target values
    
    Returns:
        True if all targets found
    
    Example:
        found = search.contains_all([1, 2, 3, 4], [2, 3])  # True
    """
    sequence_set = set(sequence)
    return all(target in sequence_set for target in targets)


def fuzzy_match(text: str, pattern: str) -> bool:
    """
    Fuzzy string matching (pattern chars in order).
    
    Args:
        text: Text to search
        pattern: Pattern to match
    
    Returns:
        True if pattern matches
    
    Example:
        match = search.fuzzy_match("hello world", "hlwrd")  # True
    """
    pattern_idx = 0
    text_lower = text.lower()
    pattern_lower = pattern.lower()
    
    for char in text_lower:
        if pattern_idx < len(pattern_lower) and char == pattern_lower[pattern_idx]:
            pattern_idx += 1
    
    return pattern_idx == len(pattern_lower)


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings.
    
    Args:
        s1: First string
        s2: Second string
    
    Returns:
        Edit distance
    
    Example:
        dist = search.levenshtein_distance("kitten", "sitting")  # 3
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


__all__ = [
    "linear_search", "binary_search", "find_all",
    "find_first", "find_last", "find_min", "find_max",
    "contains_any", "contains_all", "fuzzy_match", "levenshtein_distance"
]
