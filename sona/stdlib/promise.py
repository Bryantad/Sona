"""
promise - Promise/Future pattern for Sona stdlib

Provides async promise handling:
- Promise: Promise class
- all: Wait for all promises
- race: Race multiple promises
"""

from concurrent.futures import ThreadPoolExecutor, Future
import threading


class Promise:
    """Promise for async operations."""
    
    def __init__(self, executor_func=None):
        """
        Initialize promise.
        
        Args:
            executor_func: Function(resolve, reject) to execute
        
        Example:
            def executor(resolve, reject):
                result = do_work()
                resolve(result)
            
            p = Promise(executor)
        """
        self._future = Future()
        self._then_callbacks = []
        self._catch_callbacks = []
        
        if executor_func:
            def run():
                try:
                    executor_func(self._resolve, self._reject)
                except Exception as e:
                    self._reject(e)
            
            thread = threading.Thread(target=run)
            thread.start()
    
    def _resolve(self, value):
        """Resolve promise with value."""
        self._future.set_result(value)
        for callback in self._then_callbacks:
            callback(value)
    
    def _reject(self, error):
        """Reject promise with error."""
        self._future.set_exception(error)
        for callback in self._catch_callbacks:
            callback(error)
    
    def then(self, callback):
        """
        Add success callback.
        
        Args:
            callback: Function to call on success
        
        Returns:
            Self for chaining
        
        Example:
            promise.then(lambda result: print(result))
        """
        self._then_callbacks.append(callback)
        
        # If already resolved, call immediately
        if self._future.done() and not self._future.exception():
            try:
                callback(self._future.result())
            except Exception:
                pass
        
        return self
    
    def catch(self, callback):
        """
        Add error callback.
        
        Args:
            callback: Function to call on error
        
        Returns:
            Self for chaining
        
        Example:
            promise.catch(lambda err: print(f"Error: {err}"))
        """
        self._catch_callbacks.append(callback)
        
        # If already rejected, call immediately
        if self._future.done() and self._future.exception():
            try:
                callback(self._future.exception())
            except Exception:
                pass
        
        return self
    
    def wait(self, timeout=None):
        """
        Wait for promise to complete.
        
        Args:
            timeout: Wait timeout in seconds
        
        Returns:
            Promise result
        
        Raises:
            Exception if promise rejected
        
        Example:
            result = promise.wait()
        """
        return self._future.result(timeout=timeout)


def all(promises):
    """
    Wait for all promises to resolve.
    
    Args:
        promises: List of Promise objects
    
    Returns:
        List of results
    
    Example:
        results = promise.all([p1, p2, p3])
    """
    return [p.wait() for p in promises]


def race(promises):
    """
    Race multiple promises (return first to complete).
    
    Args:
        promises: List of Promise objects
    
    Returns:
        First completed result
    
    Example:
        result = promise.race([p1, p2, p3])
    """
    from concurrent.futures import wait, FIRST_COMPLETED
    
    futures = [p._future for p in promises]
    done, pending = wait(futures, return_when=FIRST_COMPLETED)
    
    first = list(done)[0]
    return first.result()


def resolve(value):
    """
    Create resolved promise.
    
    Args:
        value: Value to resolve with
    
    Returns:
        Resolved Promise
    
    Example:
        p = promise.resolve(42)
    """
    p = Promise()
    p._resolve(value)
    return p


def reject(error):
    """
    Create rejected promise.
    
    Args:
        error: Error to reject with
    
    Returns:
        Rejected Promise
    
    Example:
        p = promise.reject(Exception("Failed"))
    """
    p = Promise()
    p._reject(error)
    return p


def any(promises):
    """
    Return first promise to resolve successfully.
    
    Args:
        promises: List of Promise objects
    
    Returns:
        First successful result
    
    Example:
        result = promise.any([p1, p2, p3])
    """
    from concurrent.futures import wait, FIRST_COMPLETED
    
    futures = [p._future for p in promises]
    remaining = set(futures)
    
    while remaining:
        done, remaining = wait(remaining, return_when=FIRST_COMPLETED)
        for future in done:
            if not future.exception():
                return future.result()
    
    raise Exception("All promises rejected")


def allSettled(promises):
    """
    Wait for all promises to settle (resolve or reject).
    
    Args:
        promises: List of Promise objects
    
    Returns:
        List of dicts with status and value/reason
    
    Example:
        results = promise.allSettled([p1, p2, p3])
        # [{'status': 'fulfilled', 'value': 42}, ...]
    """
    results = []
    
    for p in promises:
        try:
            value = p.wait()
            results.append({'status': 'fulfilled', 'value': value})
        except Exception as e:
            results.append({'status': 'rejected', 'reason': e})
    
    return results


def delay(seconds, value=None):
    """
    Create promise that resolves after delay.
    
    Args:
        seconds: Delay in seconds
        value: Value to resolve with
    
    Returns:
        Promise
    
    Example:
        p = promise.delay(2.0, "done")
        result = p.wait()
    """
    import time
    
    def executor(resolve, reject):
        time.sleep(seconds)
        resolve(value)
    
    return Promise(executor)


def timeout(promise_obj, seconds):
    """
    Add timeout to promise.
    
    Args:
        promise_obj: Promise to add timeout to
        seconds: Timeout in seconds
    
    Returns:
        Promise that rejects on timeout
    
    Example:
        p = promise.timeout(my_promise, 5.0)
    """
    def executor(resolve, reject):
        try:
            result = promise_obj.wait(timeout=seconds)
            resolve(result)
        except Exception as e:
            reject(e)
    
    return Promise(executor)


def retry(func, attempts=3, delay_secs=1.0):
    """
    Retry function with promise.
    
    Args:
        func: Function returning Promise
        attempts: Number of attempts
        delay_secs: Delay between attempts
    
    Returns:
        Promise
    
    Example:
        p = promise.retry(lambda: fetch_data(), attempts=3)
    """
    import time
    
    def executor(resolve, reject):
        last_error = None
        
        for i in range(attempts):
            try:
                result = func().wait()
                resolve(result)
                return
            except Exception as e:
                last_error = e
                if i < attempts - 1:
                    time.sleep(delay_secs)
        
        reject(last_error)
    
    return Promise(executor)


def wrap(func, *args, **kwargs):
    """
    Wrap function call in promise.
    
    Args:
        func: Function to wrap
        args: Function arguments
        kwargs: Function keyword arguments
    
    Returns:
        Promise
    
    Example:
        p = promise.wrap(expensive_function, arg1, arg2)
    """
    def executor(resolve, reject):
        try:
            result = func(*args, **kwargs)
            resolve(result)
        except Exception as e:
            reject(e)
    
    return Promise(executor)


__all__ = [
    'Promise', 'all', 'race', 'resolve', 'reject',
    'any', 'allSettled', 'delay', 'timeout', 'retry', 'wrap'
]
