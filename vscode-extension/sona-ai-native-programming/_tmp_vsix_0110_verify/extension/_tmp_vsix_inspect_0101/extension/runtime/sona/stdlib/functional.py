"""
functional - Functional programming utilities for Sona stdlib (v0.10.1)

Provides functional helpers:
- compose/pipe: Function composition
- curry/partial: Currying and partial application
- juxt/complement/tap: Higher-order utilities
- thread_first/thread_last: Threading macros
- memoize/once/trampoline: Execution control
"""

import functools
import threading
import time
from typing import Any, Callable, TypeVar

T = TypeVar("T")
R = TypeVar("R")


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
    'all_func', 'any_func', 'flatten',
    # v0.10.1 additions
    'juxt', 'complement', 'negate', 'tap', 'once', 'after', 'before',
    'memoize', 'always', 'thread_first', 'thread_last', 'trampoline',
    'debounce', 'throttle', 'is_function', 'is_nil', 'converge',
]


# ---------------------------------------------------------------------------
# v0.10.1 ADDITIONS - Higher-order utilities
# ---------------------------------------------------------------------------


def juxt(*functions):
    """
    Apply multiple functions to the same arguments, return tuple of results.
    
    Args:
        functions: Functions to apply
    
    Returns:
        Function that applies all functions and returns tuple
    
    Example:
        stats = functional.juxt(min, max, sum)
        stats([1, 2, 3, 4, 5])  # (1, 5, 15)
    """
    def juxtaposed(*args, **kwargs):
        return tuple(f(*args, **kwargs) for f in functions)
    return juxtaposed


def complement(predicate):
    """
    Return negation of a predicate function.
    
    Args:
        predicate: Function returning bool
    
    Returns:
        Negated predicate
    
    Example:
        is_even = lambda x: x % 2 == 0
        is_odd = functional.complement(is_even)
        is_odd(3)  # True
    """
    def complemented(*args, **kwargs):
        return not predicate(*args, **kwargs)
    return complemented


# Alias for complement
negate = complement


def tap(func):
    """
    Execute a side-effect function, return original value.
    
    Useful for debugging in pipelines.
    
    Args:
        func: Side-effect function
    
    Returns:
        Function that calls func then returns input
    
    Example:
        pipeline = functional.pipe(
            lambda x: x + 1,
            functional.tap(print),  # prints intermediate value
            lambda x: x * 2
        )
        pipeline(5)  # prints 6, returns 12
    """
    def tapped(value):
        func(value)
        return value
    return tapped


def once(func):
    """
    Create function that only executes once.
    
    Subsequent calls return the first result.
    
    Args:
        func: Function to wrap
    
    Returns:
        Function that runs only once
    
    Example:
        init = functional.once(lambda: print("Initialized!"))
        init()  # prints "Initialized!"
        init()  # does nothing, returns same result
    """
    result = []
    called = [False]
    lock = threading.Lock()
    
    def once_wrapper(*args, **kwargs):
        with lock:
            if not called[0]:
                result.append(func(*args, **kwargs))
                called[0] = True
        return result[0] if result else None
    
    return once_wrapper


def after(n: int, func):
    """
    Create function that only executes after n calls.
    
    Args:
        n: Number of calls before execution
        func: Function to wrap
    
    Returns:
        Function that ignores first n-1 calls
    
    Example:
        log = functional.after(3, lambda: print("Ready!"))
        log()  # nothing
        log()  # nothing
        log()  # prints "Ready!"
    """
    count = [0]
    
    def after_wrapper(*args, **kwargs):
        count[0] += 1
        if count[0] >= n:
            return func(*args, **kwargs)
        return None
    
    return after_wrapper


def before(n: int, func):
    """
    Create function that only executes for first n calls.
    
    Args:
        n: Maximum number of executions
        func: Function to wrap
    
    Returns:
        Function that stops executing after n calls
    
    Example:
        warn = functional.before(3, lambda msg: print(f"Warning: {msg}"))
        warn("first")   # prints
        warn("second")  # prints
        warn("third")   # prints
        warn("fourth")  # nothing
    """
    count = [0]
    last_result = [None]
    
    def before_wrapper(*args, **kwargs):
        if count[0] < n:
            count[0] += 1
            last_result[0] = func(*args, **kwargs)
        return last_result[0]
    
    return before_wrapper


def memoize(func=None, *, maxsize: int = 128, typed: bool = False):
    """
    Memoize function with configurable cache.
    
    Can be used as decorator with or without arguments.
    
    Args:
        func: Function to memoize
        maxsize: Maximum cache size (None for unlimited)
        typed: Whether to cache by argument types
    
    Returns:
        Memoized function
    
    Example:
        @functional.memoize
        def fib(n):
            if n < 2: return n
            return fib(n-1) + fib(n-2)
        
        @functional.memoize(maxsize=256)
        def expensive(x, y):
            return x ** y
    """
    def decorator(fn):
        return functools.lru_cache(maxsize=maxsize, typed=typed)(fn)
    
    if func is not None:
        return decorator(func)
    return decorator


def always(value):
    """
    Create function that always returns the same value.
    
    Clearer alias for const().
    
    Args:
        value: Value to always return
    
    Returns:
        Constant function
    
    Example:
        get_default = functional.always(42)
        get_default()        # 42
        get_default(1, 2, 3) # 42
    """
    return lambda *args, **kwargs: value


def thread_first(value, *forms):
    """
    Thread value through functions as first argument.
    
    Args:
        value: Initial value
        forms: Functions or (func, *args) tuples
    
    Returns:
        Final result
    
    Example:
        result = functional.thread_first(
            5,
            lambda x: x + 1,        # 6
            (lambda x, y: x * y, 2) # 12
        )
    """
    result = value
    for form in forms:
        if callable(form):
            result = form(result)
        elif isinstance(form, (list, tuple)) and len(form) >= 1:
            fn, *args = form
            result = fn(result, *args)
        else:
            raise TypeError(f"Expected callable or (callable, *args), got {type(form)}")
    return result


def thread_last(value, *forms):
    """
    Thread value through functions as last argument.
    
    Args:
        value: Initial value
        forms: Functions or (func, *args) tuples
    
    Returns:
        Final result
    
    Example:
        result = functional.thread_last(
            [1, 2, 3],
            (map, lambda x: x * 2),  # map(fn, [1,2,3])
            list
        )
    """
    result = value
    for form in forms:
        if callable(form):
            result = form(result)
        elif isinstance(form, (list, tuple)) and len(form) >= 1:
            fn, *args = form
            result = fn(*args, result)
        else:
            raise TypeError(f"Expected callable or (callable, *args), got {type(form)}")
    return result


def trampoline(func):
    """
    Trampoline for tail-call optimization.
    
    Wrap recursive function to avoid stack overflow.
    Return a lambda to continue, or value to stop.
    
    Args:
        func: Function that returns lambdas for recursion
    
    Returns:
        Trampolined function
    
    Example:
        def factorial(n, acc=1):
            if n <= 1:
                return acc
            return lambda: factorial(n - 1, n * acc)
        
        fact = functional.trampoline(factorial)
        fact(10000)  # Works without stack overflow
    """
    def trampolined(*args, **kwargs):
        result = func(*args, **kwargs)
        while callable(result):
            result = result()
        return result
    return trampolined


def debounce(wait: float):
    """
    Debounce decorator - delay execution until quiet period.
    
    Args:
        wait: Seconds to wait before execution
    
    Returns:
        Decorator function
    
    Example:
        @functional.debounce(0.5)
        def save_draft(content):
            print(f"Saving: {content}")
        
        save_draft("a")
        save_draft("ab")
        save_draft("abc")  # Only this one executes after 0.5s
    """
    def decorator(func):
        timer = [None]
        lock = threading.Lock()
        
        def debounced(*args, **kwargs):
            def call_func():
                func(*args, **kwargs)
            
            with lock:
                if timer[0] is not None:
                    timer[0].cancel()
                timer[0] = threading.Timer(wait, call_func)
                timer[0].start()
        
        return debounced
    return decorator


def throttle(wait: float):
    """
    Throttle decorator - limit execution rate.
    
    Args:
        wait: Minimum seconds between executions
    
    Returns:
        Decorator function
    
    Example:
        @functional.throttle(1.0)
        def log_event(msg):
            print(msg)
        
        for i in range(100):
            log_event(f"Event {i}")  # Only ~1 per second executes
    """
    def decorator(func):
        last_called = [0.0]
        lock = threading.Lock()
        
        def throttled(*args, **kwargs):
            with lock:
                now = time.time()
                if now - last_called[0] >= wait:
                    last_called[0] = now
                    return func(*args, **kwargs)
            return None
        
        return throttled
    return decorator


def is_function(value) -> bool:
    """
    Check if value is callable/function.
    
    Args:
        value: Value to check
    
    Returns:
        True if callable
    
    Example:
        functional.is_function(print)       # True
        functional.is_function(lambda: 1)   # True
        functional.is_function(42)          # False
    """
    return callable(value)


def is_nil(value) -> bool:
    """
    Check if value is None/nil.
    
    Args:
        value: Value to check
    
    Returns:
        True if None
    
    Example:
        functional.is_nil(None)  # True
        functional.is_nil(0)     # False
        functional.is_nil("")    # False
    """
    return value is None


def converge(converger, branches):
    """
    Apply multiple functions to input, then converge results.
    
    Args:
        converger: Function to combine branch results
        branches: List of functions to apply to input
    
    Returns:
        Function that applies branches then converges
    
    Example:
        avg = functional.converge(
            lambda s, c: s / c,
            [sum, len]
        )
        avg([1, 2, 3, 4, 5])  # 3.0
    """
    def converged(*args, **kwargs):
        results = [branch(*args, **kwargs) for branch in branches]
        return converger(*results)
    return converged
