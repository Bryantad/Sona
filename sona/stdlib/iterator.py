"""
iterator - Iterator utilities for Sona stdlib

Provides iterator helpers:
- range: Custom range iterator
- cycle: Cycle through items
- chain: Chain iterators
"""

import itertools


def range_iter(start, stop=None, step=1):
    """
    Create range iterator.
    
    Args:
        start: Start value (or stop if only one arg)
        stop: Stop value
        step: Step size
    
    Returns:
        Iterator
    
    Example:
        for i in iterator.range_iter(5):
            print(i)  # 0, 1, 2, 3, 4
    """
    if stop is None:
        stop = start
        start = 0
    
    current = start
    while (step > 0 and current < stop) or (step < 0 and current > stop):
        yield current
        current += step


def cycle(items):
    """
    Cycle through items infinitely.
    
    Args:
        items: Items to cycle through
    
    Returns:
        Iterator
    
    Example:
        colors = iterator.cycle(['red', 'green', 'blue'])
        next(colors)  # 'red'
        next(colors)  # 'green'
        next(colors)  # 'blue'
        next(colors)  # 'red' (cycles back)
    """
    return itertools.cycle(items)


def chain(*iterables):
    """
    Chain multiple iterables together.
    
    Args:
        iterables: Iterables to chain
    
    Returns:
        Iterator
    
    Example:
        combined = iterator.chain([1, 2], [3, 4], [5, 6])
        list(combined)  # [1, 2, 3, 4, 5, 6]
    """
    return itertools.chain(*iterables)


def zip_iter(*iterables):
    """
    Zip iterables together.
    
    Args:
        iterables: Iterables to zip
    
    Returns:
        Iterator of tuples
    
    Example:
        pairs = iterator.zip_iter([1, 2, 3], ['a', 'b', 'c'])
        list(pairs)  # [(1, 'a'), (2, 'b'), (3, 'c')]
    """
    return zip(*iterables)


def enumerate_iter(iterable, start=0):
    """
    Enumerate iterable with index.
    
    Args:
        iterable: Items to enumerate
        start: Starting index
    
    Returns:
        Iterator of (index, item) tuples
    
    Example:
        for i, val in iterator.enumerate_iter(['a', 'b', 'c']):
            print(f"{i}: {val}")
    """
    return enumerate(iterable, start)


def filter_iter(predicate, iterable):
    """
    Filter iterable by predicate.
    
    Args:
        predicate: Filter function
        iterable: Items to filter
    
    Returns:
        Iterator
    
    Example:
        evens = iterator.filter_iter(lambda x: x % 2 == 0, [1, 2, 3, 4, 5])
        list(evens)  # [2, 4]
    """
    return filter(predicate, iterable)


def map_iter(func, *iterables):
    """
    Map function over iterables.
    
    Args:
        func: Mapping function
        iterables: Input iterables
    
    Returns:
        Iterator
    
    Example:
        doubled = iterator.map_iter(lambda x: x * 2, [1, 2, 3])
        list(doubled)  # [2, 4, 6]
    """
    return map(func, *iterables)


def take(n, iterable):
    """
    Take first n items from iterable.
    
    Args:
        n: Number of items
        iterable: Source iterable
    
    Returns:
        List of items
    
    Example:
        first_three = iterator.take(3, range(10))
        # [0, 1, 2]
    """
    return list(itertools.islice(iterable, n))


def drop(n, iterable):
    """
    Drop first n items, return rest.
    
    Args:
        n: Number of items to drop
        iterable: Source iterable
    
    Returns:
        Iterator
    
    Example:
        remaining = iterator.drop(3, range(10))
        list(remaining)  # [3, 4, 5, 6, 7, 8, 9]
    """
    return itertools.islice(iterable, n, None)


def chunk(iterable, size):
    """
    Split iterable into chunks.
    
    Args:
        iterable: Items to chunk
        size: Chunk size
    
    Returns:
        Iterator of chunks
    
    Example:
        chunks = iterator.chunk(range(10), 3)
        # [[0,1,2], [3,4,5], [6,7,8], [9]]
    """
    items = list(iterable)
    for i in range(0, len(items), size):
        yield items[i:i+size]


def flatten(nested_iterable):
    """
    Flatten nested iterable.
    
    Args:
        nested_iterable: Nested iterable
    
    Returns:
        Iterator of flattened items
    
    Example:
        flat = iterator.flatten([[1, 2], [3, 4]])
    """
    for item in nested_iterable:
        if hasattr(item, '__iter__') and not isinstance(item, (str, bytes)):
            yield from flatten(item)
        else:
            yield item


def repeat(item, times=None):
    """
    Repeat item n times (or infinitely).
    
    Args:
        item: Item to repeat
        times: Number of times (None for infinite)
    
    Returns:
        Iterator
    
    Example:
        zeros = iterator.repeat(0, 5)
    """
    return itertools.repeat(item, times)


def count_from(start=0, step=1):
    """
    Count from start with step.
    
    Args:
        start: Starting value
        step: Step size
    
    Returns:
        Iterator
    
    Example:
        evens = iterator.count_from(0, 2)
    """
    return itertools.count(start, step)


def pairwise(iterable):
    """
    Return successive overlapping pairs.
    
    Args:
        iterable: Source iterable
    
    Returns:
        Iterator of pairs
    
    Example:
        pairs = iterator.pairwise([1, 2, 3, 4])
        # [(1, 2), (2, 3), (3, 4)]
    """
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def sliding_window(iterable, n):
    """
    Sliding window over iterable.
    
    Args:
        iterable: Source iterable
        n: Window size
    
    Returns:
        Iterator of windows
    
    Example:
        windows = iterator.sliding_window([1, 2, 3, 4], 3)
        # [(1, 2, 3), (2, 3, 4)]
    """
    it = iter(iterable)
    window = list(itertools.islice(it, n))
    
    if len(window) == n:
        yield tuple(window)
    
    for item in it:
        window = window[1:] + [item]
        yield tuple(window)


def unique(iterable, key=None):
    """
    Return unique items preserving order.
    
    Args:
        iterable: Source iterable
        key: Key function for uniqueness
    
    Returns:
        Iterator of unique items
    
    Example:
        unique_items = iterator.unique([1, 2, 2, 3, 1])
    """
    seen = set()
    for item in iterable:
        k = key(item) if key else item
        if k not in seen:
            seen.add(k)
            yield item


def interleave(*iterables):
    """
    Interleave multiple iterables.
    
    Args:
        iterables: Iterables to interleave
    
    Returns:
        Iterator
    
    Example:
        mixed = iterator.interleave([1, 2, 3], ['a', 'b', 'c'])
        # [1, 'a', 2, 'b', 3, 'c']
    """
    iters = [iter(it) for it in iterables]
    
    while iters:
        for it in iters[:]:
            try:
                yield next(it)
            except StopIteration:
                iters.remove(it)


def partition_iter(predicate, iterable):
    """
    Partition into true/false iterators.
    
    Args:
        predicate: Test function
        iterable: Source iterable
    
    Returns:
        Tuple of (true_iter, false_iter)
    
    Example:
        evens, odds = iterator.partition_iter(lambda x: x % 2 == 0, range(6))
    """
    t1, t2 = itertools.tee(iterable)
    return filter(predicate, t1), itertools.filterfalse(predicate, t2)


def accumulate(iterable, func=None):
    """
    Accumulate values.
    
    Args:
        iterable: Source iterable
        func: Accumulation function (default: add)
    
    Returns:
        Iterator of accumulated values
    
    Example:
        running_sum = iterator.accumulate([1, 2, 3, 4])
        # [1, 3, 6, 10]
    """
    if func is None:
        return itertools.accumulate(iterable)
    return itertools.accumulate(iterable, func)


__all__ = [
    'range_iter', 'cycle', 'chain', 'zip_iter', 'enumerate_iter',
    'filter_iter', 'map_iter', 'take', 'drop', 'chunk',
    'flatten', 'repeat', 'count_from', 'pairwise', 'sliding_window',
    'unique', 'interleave', 'partition_iter', 'accumulate'
]
