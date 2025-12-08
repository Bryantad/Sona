"""
thread - Threading utilities for Sona stdlib

Provides thread management:
- create: Create and start thread
- pool: Thread pool for parallel execution
- lock: Thread locking
"""

import threading
from concurrent.futures import ThreadPoolExecutor
import time


def create(func, args=None):
    """
    Create and start thread.
    
    Args:
        func: Function to run in thread
        args: Tuple of arguments (optional)
    
    Returns:
        Thread object
    
    Example:
        t = thread.create(worker_function, ("arg1", "arg2"))
        t.join()  # Wait for completion
    """
    args = args or ()
    t = threading.Thread(target=func, args=args)
    t.start()
    return t


def pool(max_workers=None):
    """
    Create thread pool executor.
    
    Args:
        max_workers: Maximum threads (default: CPU count * 5)
    
    Returns:
        ThreadPoolExecutor
    
    Example:
        with thread.pool(5) as executor:
            results = executor.map(process_item, items)
    """
    return ThreadPoolExecutor(max_workers=max_workers)


def execute(func, items, max_workers=None):
    """
    Execute function on items in parallel.
    
    Args:
        func: Function to apply
        items: List of items to process
        max_workers: Maximum threads
    
    Returns:
        List of results
    
    Example:
        results = thread.execute(process, data_items, max_workers=10)
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(func, items))


class Lock:
    """Thread lock for synchronization."""
    
    def __init__(self):
        self._lock = threading.Lock()
    
    def acquire(self, blocking=True, timeout=-1):
        """Acquire lock."""
        return self._lock.acquire(blocking=blocking, timeout=timeout)
    
    def release(self):
        """Release lock."""
        self._lock.release()
    
    def __enter__(self):
        """Context manager entry."""
        self._lock.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._lock.release()


def lock():
    """
    Create thread lock.
    
    Returns:
        Lock object
    
    Example:
        lock = thread.lock()
        with lock:
            # Critical section
            update_shared_data()
    """
    return Lock()


def sleep(seconds):
    """
    Sleep current thread.
    
    Args:
        seconds: Sleep duration
    
    Example:
        thread.sleep(2)
    """
    time.sleep(seconds)


def current():
    """
    Get current thread info.
    
    Returns:
        Dictionary with thread info
    
    Example:
        info = thread.current()
        # {"id": 123, "name": "Thread-1", "is_alive": True}
    """
    t = threading.current_thread()
    return {
        'id': t.ident,
        'name': t.name,
        'is_alive': t.is_alive()
    }


def active_count():
    """
    Get number of active threads.
    
    Returns:
        Thread count
    
    Example:
        count = thread.active_count()
    """
    return threading.active_count()


def daemon(func, args=None):
    """
    Create and start daemon thread (exits when main program exits).
    
    Args:
        func: Function to run
        args: Arguments tuple
    
    Returns:
        Thread object
    
    Example:
        t = thread.daemon(background_worker)
    """
    args = args or ()
    t = threading.Thread(target=func, args=args, daemon=True)
    t.start()
    return t


def join_all(threads, timeout=None):
    """
    Wait for all threads to complete.
    
    Args:
        threads: List of thread objects
        timeout: Maximum wait time per thread
    
    Returns:
        True if all completed
    
    Example:
        threads = [thread.create(work, (i,)) for i in range(5)]
        thread.join_all(threads)
    """
    for t in threads:
        t.join(timeout=timeout)
    return all(not t.is_alive() for t in threads)


class RWLock:
    """
    Reader-Writer lock for concurrent read access.
    
    Example:
        rwlock = thread.RWLock()
        
        with rwlock.read():
            # Multiple readers allowed
            value = shared_data
        
        with rwlock.write():
            # Exclusive write access
            shared_data = new_value
    """
    
    def __init__(self):
        self._readers = 0
        self._lock = threading.Lock()
        self._write_lock = threading.Lock()
    
    def read(self):
        """Acquire read lock."""
        class ReadContext:
            def __init__(self_ctx):
                self_ctx.rwlock = self
            
            def __enter__(self_ctx):
                with self._lock:
                    self._readers += 1
                    if self._readers == 1:
                        self._write_lock.acquire()
                return self_ctx
            
            def __exit__(self_ctx, *args):
                with self._lock:
                    self._readers -= 1
                    if self._readers == 0:
                        self._write_lock.release()
        
        return ReadContext()
    
    def write(self):
        """Acquire write lock."""
        return self._write_lock


def run_once(func):
    """
    Decorator to ensure function runs only once (thread-safe).
    
    Args:
        func: Function to wrap
    
    Returns:
        Wrapped function
    
    Example:
        @thread.run_once
        def initialize():
            # Only runs once
            pass
    """
    lock_obj = threading.Lock()
    done = [False]
    result = [None]
    
    def wrapper(*args, **kwargs):
        if not done[0]:
            with lock_obj:
                if not done[0]:
                    result[0] = func(*args, **kwargs)
                    done[0] = True
        return result[0]
    
    return wrapper


__all__ = [
    'create',
    'pool',
    'execute',
    'Lock',
    'lock',
    'sleep',
    'current',
    'active_count',
    'daemon',
    'join_all',
    'RWLock',
    'run_once'
]
