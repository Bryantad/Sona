"""
decorator - Decorator utilities for Sona stdlib

Provides common decorators:
- memoize: Cache function results
- retry: Retry on failure
- timeout: Function timeout
"""

import time
import functools


def memoize(func):
    """
    Memoization decorator - cache function results.
    
    Args:
        func: Function to memoize
    
    Returns:
        Memoized function
    
    Example:
        @decorator.memoize
        def fibonacci(n):
            if n < 2:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
    """
    cache = {}
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    
    return wrapper


def retry(max_attempts=3, delay=1):
    """
    Retry decorator - retry function on failure.
    
    Args:
        max_attempts: Maximum retry attempts
        delay: Delay between retries (seconds)
    
    Returns:
        Decorator function
    
    Example:
        @decorator.retry(max_attempts=3, delay=2)
        def fetch_data():
            # May fail occasionally
            return requests.get(url)
    """
    def decorator_retry(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator_retry


def timing(func):
    """
    Timing decorator - measure execution time.
    
    Args:
        func: Function to time
    
    Returns:
        Wrapped function
    
    Example:
        @decorator.timing
        def slow_operation():
            time.sleep(2)
        
        slow_operation()  # Prints: slow_operation took 2.00s
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end-start:.2f}s")
        return result
    return wrapper


def deprecated(message="This function is deprecated"):
    """
    Deprecation decorator - warn when function is used.
    
    Args:
        message: Deprecation message
    
    Returns:
        Decorator function
    
    Example:
        @decorator.deprecated("Use new_function() instead")
        def old_function():
            pass
    """
    def decorator_deprecated(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"WARNING: {func.__name__} - {message}")
            return func(*args, **kwargs)
        return wrapper
    return decorator_deprecated


def validate(*validators):
    """
    Validation decorator - validate function arguments.
    
    Args:
        validators: Validation functions
    
    Returns:
        Decorator function
    
    Example:
        def is_positive(x):
            return x > 0
        
        @decorator.validate(is_positive)
        def process(number):
            return number * 2
    """
    def decorator_validate(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for i, (arg, validator) in enumerate(zip(args, validators)):
                if not validator(arg):
                    raise ValueError(f"Argument {i} failed validation")
            return func(*args, **kwargs)
        return wrapper
    return decorator_validate


def singleton(cls):
    """
    Singleton decorator - ensure only one instance of class.
    
    Args:
        cls: Class to make singleton
    
    Returns:
        Singleton class
    
    Example:
        @decorator.singleton
        class Config:
            pass
    """
    instances = {}
    
    @functools.wraps(cls)
    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return wrapper


def rate_limit(calls_per_second):
    """
    Rate limiting decorator.
    
    Args:
        calls_per_second: Maximum calls per second
    
    Returns:
        Decorator function
    
    Example:
        @decorator.rate_limit(2)
        def api_call():
            pass
    """
    min_interval = 1.0 / calls_per_second
    last_call = [0]
    
    def decorator_rate_limit(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_call[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            
            last_call[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator_rate_limit


def cache_with_ttl(ttl_seconds):
    """
    Cache with time-to-live decorator.
    
    Args:
        ttl_seconds: Cache TTL in seconds
    
    Returns:
        Decorator function
    
    Example:
        @decorator.cache_with_ttl(60)
        def get_data():
            return expensive_operation()
    """
    def decorator_cache(func):
        cache = {}
        timestamps = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = time.time()
            
            if key in cache and (now - timestamps[key]) < ttl_seconds:
                return cache[key]
            
            result = func(*args, **kwargs)
            cache[key] = result
            timestamps[key] = now
            return result
        
        return wrapper
    return decorator_cache


def synchronized(func):
    """
    Thread synchronization decorator.
    
    Args:
        func: Function to synchronize
    
    Returns:
        Synchronized function
    
    Example:
        @decorator.synchronized
        def update_counter():
            global counter
            counter += 1
    """
    import threading
    lock = threading.Lock()
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with lock:
            return func(*args, **kwargs)
    return wrapper


def log_calls(func):
    """
    Log function calls decorator.
    
    Args:
        func: Function to log
    
    Returns:
        Wrapped function
    
    Example:
        @decorator.log_calls
        def process(x, y):
            return x + y
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} returned {result}")
        return result
    return wrapper


def once(func):
    """
    Execute function only once decorator.
    
    Args:
        func: Function to execute once
    
    Returns:
        Wrapped function
    
    Example:
        @decorator.once
        def initialize():
            print("Setup")
    """
    called = [False]
    result = [None]
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not called[0]:
            result[0] = func(*args, **kwargs)
            called[0] = True
        return result[0]
    return wrapper


def count_calls(func):
    """
    Count function calls decorator.
    
    Args:
        func: Function to count
    
    Returns:
        Wrapped function with call_count attribute
    
    Example:
        @decorator.count_calls
        def process():
            pass
        
        process()
        print(process.call_count)  # 1
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.call_count += 1
        return func(*args, **kwargs)
    
    wrapper.call_count = 0
    return wrapper


def debug(func):
    """
    Debug decorator with detailed output.
    
    Args:
        func: Function to debug
    
    Returns:
        Wrapped function
    
    Example:
        @decorator.debug
        def calculate(x, y):
            return x + y
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        args_str = ', '.join(repr(a) for a in args)
        kwargs_str = ', '.join(f"{k}={v!r}" for k, v in kwargs.items())
        all_args = ', '.join(filter(None, [args_str, kwargs_str]))
        
        print(f"[DEBUG] {func.__name__}({all_args})")
        result = func(*args, **kwargs)
        print(f"[DEBUG] {func.__name__} -> {result!r}")
        
        return result
    return wrapper


__all__ = [
    'memoize', 'retry', 'timing', 'deprecated', 'validate', 'singleton',
    'rate_limit', 'cache_with_ttl', 'synchronized', 'log_calls',
    'once', 'count_calls', 'debug'
]
