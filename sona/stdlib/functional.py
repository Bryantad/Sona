"""
functional - Functional programming utilities for Sona stdlib

Provides functional helpers:
- compose: Function composition
- curry: Function currying
- partial: Partial application
"""

import functools


def compose(*functions):
    """
    Compose functions (right to left).
    
    Args:
        functions: Functions to compose
    
    Returns:
        Composed function
    
    Example:
        add_one = lambda x: x + 1
        double = lambda x: x * 2
        
        f = functional.compose(add_one, double)
        result = f(5)  # 11 (double first: 10, then add_one: 11)
    """
    def composed(x):
        for func in reversed(functions):
            x = func(x)
        return x
    return composed


def pipe(*functions):
    """
    Pipe functions (left to right).
    
    Args:
        functions: Functions to pipe
    
    Returns:
        Piped function
    
    Example:
        add_one = lambda x: x + 1
        double = lambda x: x * 2
        
        f = functional.pipe(add_one, double)
        result = f(5)  # 12 (add_one first: 6, then double: 12)
    """
    def piped(x):
        for func in functions:
            x = func(x)
        return x
    return piped


def curry(func, arity=None):
    """
    Curry function (convert multi-arg to chain of single-arg).
    
    Args:
        func: Function to curry
        arity: Number of arguments (auto-detected if None)
    
    Returns:
        Curried function
    
    Example:
        def add(a, b, c):
            return a + b + c
        
        curried = functional.curry(add)
        result = curried(1)(2)(3)  # 6
    """
    if arity is None:
        arity = func.__code__.co_argcount
    
    def curried(*args):
        if len(args) >= arity:
            return func(*args[:arity])
        return lambda *more: curried(*(args + more))
    
    return curried


def partial(func, *args, **kwargs):
    """
    Partial function application.
    
    Args:
        func: Function to partially apply
        args: Partial positional arguments
        kwargs: Partial keyword arguments
    
    Returns:
        Partially applied function
    
    Example:
        def greet(greeting, name):
            return f"{greeting}, {name}!"
        
        say_hello = functional.partial(greet, "Hello")
        say_hello("John")  # "Hello, John!"
    """
    return functools.partial(func, *args, **kwargs)


def identity(x):
    """
    Identity function (returns input).
    
    Args:
        x: Input value
    
    Returns:
        Same value
    
    Example:
        functional.identity(42)  # 42
    """
    return x


def const(value):
    """
    Create constant function (always returns same value).
    
    Args:
        value: Value to return
    
    Returns:
        Constant function
    
    Example:
        always_five = functional.const(5)
        always_five()  # 5
        always_five(1, 2, 3)  # 5
    """
    return lambda *args, **kwargs: value


def flip(func):
    """
    Flip function argument order.
    
    Args:
        func: Function to flip
    
    Returns:
        Flipped function
    
    Example:
        def divide(a, b):
            return a / b
        
        flipped = functional.flip(divide)
        flipped(2, 10)  # 5.0 (10 / 2)
    """
    return lambda *args: func(*reversed(args))


def memoize_with_limit(maxsize=128):
    """
    Memoize with size limit (LRU cache).
    
    Args:
        maxsize: Maximum cache size
    
    Returns:
        Decorator function
    
    Example:
        @functional.memoize_with_limit(100)
        def fibonacci(n):
            if n < 2:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
    """
    return functools.lru_cache(maxsize=maxsize)


def reduce_func(func, iterable, initial=None):
    """
    Reduce iterable using function.
    
    Args:
        func: Reduction function
        iterable: Items to reduce
        initial: Initial value
    
    Returns:
        Reduced value
    
    Example:
        sum_all = functional.reduce_func(lambda a, b: a + b, [1, 2, 3, 4])
        # 10
    """
    if initial is None:
        items = iter(iterable)
        initial = next(items)
        iterable = items
    
    result = initial
    for item in iterable:
        result = func(result, item)
    return result


def map_func(func, iterable):
    """
    Map function over iterable.
    
    Args:
        func: Function to apply
        iterable: Items to map
    
    Returns:
        List of results
    
    Example:
        doubled = functional.map_func(lambda x: x * 2, [1, 2, 3])
    """
    return [func(item) for item in iterable]


def filter_func(predicate, iterable):
    """
    Filter iterable by predicate.
    
    Args:
        predicate: Filter function
        iterable: Items to filter
    
    Returns:
        Filtered list
    
    Example:
        evens = functional.filter_func(lambda x: x % 2 == 0, [1, 2, 3, 4])
    """
    return [item for item in iterable if predicate(item)]


def zip_with(func, *iterables):
    """
    Zip iterables and apply function.
    
    Args:
        func: Function to apply to zipped items
        iterables: Multiple iterables
    
    Returns:
        List of results
    
    Example:
        sums = functional.zip_with(lambda a, b: a + b, [1, 2], [3, 4])
    """
    return [func(*items) for items in zip(*iterables)]


def take(n, iterable):
    """
    Take first n items from iterable.
    
    Args:
        n: Number of items
        iterable: Source iterable
    
    Returns:
        List of first n items
    
    Example:
        first_three = functional.take(3, range(10))
    """
    result = []
    for i, item in enumerate(iterable):
        if i >= n:
            break
        result.append(item)
    return result


def drop(n, iterable):
    """
    Drop first n items from iterable.
    
    Args:
        n: Number to drop
        iterable: Source iterable
    
    Returns:
        List of remaining items
    
    Example:
        remaining = functional.drop(3, range(10))
    """
    result = []
    for i, item in enumerate(iterable):
        if i >= n:
            result.append(item)
    return result


def group_by(key_func, iterable):
    """
    Group items by key function.
    
    Args:
        key_func: Function to extract key
        iterable: Items to group
    
    Returns:
        Dict of key -> list of items
    
    Example:
        groups = functional.group_by(lambda x: x % 2, [1, 2, 3, 4])
    """
    groups = {}
    for item in iterable:
        key = key_func(item)
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    return groups


def partition(predicate, iterable):
    """
    Partition items into two lists by predicate.
    
    Args:
        predicate: Test function
        iterable: Items to partition
    
    Returns:
        Tuple of (true_items, false_items)
    
    Example:
        evens, odds = functional.partition(lambda x: x % 2 == 0, [1, 2, 3, 4])
    """
    true_items = []
    false_items = []
    
    for item in iterable:
        if predicate(item):
            true_items.append(item)
        else:
            false_items.append(item)
    
    return true_items, false_items


def all_func(predicate, iterable):
    """
    Check if all items satisfy predicate.
    
    Args:
        predicate: Test function
        iterable: Items to test
    
    Returns:
        bool: True if all satisfy predicate
    
    Example:
        all_positive = functional.all_func(lambda x: x > 0, [1, 2, 3])
    """
    return all(predicate(item) for item in iterable)


def any_func(predicate, iterable):
    """
    Check if any item satisfies predicate.
    
    Args:
        predicate: Test function
        iterable: Items to test
    
    Returns:
        bool: True if any satisfy predicate
    
    Example:
        has_even = functional.any_func(lambda x: x % 2 == 0, [1, 2, 3])
    """
    return any(predicate(item) for item in iterable)


def flatten(nested_list):
    """
    Flatten nested list.
    
    Args:
        nested_list: Nested list structure
    
    Returns:
        Flattened list
    
    Example:
        flat = functional.flatten([[1, 2], [3, 4], [5]])
    """
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


__all__ = [
    'compose', 'pipe', 'curry', 'partial', 'identity', 'const',
    'flip', 'memoize_with_limit', 'reduce_func', 'map_func', 'filter_func',
    'zip_with', 'take', 'drop', 'group_by', 'partition',
    'all_func', 'any_func', 'flatten'
]
