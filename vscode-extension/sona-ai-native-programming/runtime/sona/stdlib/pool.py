"""
pool - Thread/process pooling for Sona stdlib

Provides concurrent execution:
- ThreadPool: Thread-based pool
- ProcessPool: Process-based pool
- map: Parallel map operation
"""

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing


class ThreadPool:
    """Thread pool for parallel execution."""
    
    def __init__(self, max_workers=None):
        """Initialize pool."""
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
    
    def map(self, func, items):
        """
        Map function over items in parallel.
        
        Args:
            func: Function to apply
            items: Items to process
        
        Returns:
            List of results
        
        Example:
            pool = pool.ThreadPool(4)
            results = pool.map(process_item, items)
        """
        return list(self.executor.map(func, items))
    
    def submit(self, func, *args, **kwargs):
        """
        Submit task to pool.
        
        Args:
            func: Function to execute
            args: Function arguments
            kwargs: Function keyword arguments
        
        Returns:
            Future object
        
        Example:
            future = pool.submit(task, arg1, arg2)
            result = future.result()
        """
        return self.executor.submit(func, *args, **kwargs)
    
    def shutdown(self, wait=True):
        """Shutdown pool."""
        self.executor.shutdown(wait=wait)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


class ProcessPool:
    """Process pool for parallel execution."""
    
    def __init__(self, max_workers=None):
        """Initialize pool."""
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
    
    def map(self, func, items):
        """
        Map function over items in parallel processes.
        
        Args:
            func: Function to apply
            items: Items to process
        
        Returns:
            List of results
        
        Example:
            pool = pool.ProcessPool(4)
            results = pool.map(cpu_intensive_task, items)
        """
        return list(self.executor.map(func, items))
    
    def submit(self, func, *args, **kwargs):
        """
        Submit task to pool.
        
        Args:
            func: Function to execute
            args: Function arguments
            kwargs: Function keyword arguments
        
        Returns:
            Future object
        """
        return self.executor.submit(func, *args, **kwargs)
    
    def shutdown(self, wait=True):
        """Shutdown pool."""
        self.executor.shutdown(wait=wait)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


def thread_pool(max_workers=None):
    """
    Create thread pool.
    
    Args:
        max_workers: Maximum threads
    
    Returns:
        ThreadPool object
    
    Example:
        with pool.thread_pool(4) as p:
            results = p.map(func, items)
    """
    return ThreadPool(max_workers)


def process_pool(max_workers=None):
    """
    Create process pool.
    
    Args:
        max_workers: Maximum processes
    
    Returns:
        ProcessPool object
    
    Example:
        with pool.process_pool(4) as p:
            results = p.map(func, items)
    """
    return ProcessPool(max_workers)


def map_parallel(func, items, workers=None, use_processes=False):
    """
    Parallel map with automatic pool management.
    
    Args:
        func: Function to apply
        items: Items to process
        workers: Number of workers
        use_processes: Use processes instead of threads
    
    Returns:
        List of results
    
    Example:
        results = pool.map_parallel(process_item, items, workers=4)
    """
    pool_cls = ProcessPool if use_processes else ThreadPool
    with pool_cls(workers) as p:
        return p.map(func, items)


def cpu_count():
    """
    Get CPU count.
    
    Returns:
        Number of CPUs
    
    Example:
        cores = pool.cpu_count()
    """
    return multiprocessing.cpu_count()


def apply_async(pool_obj, func, args=(), kwargs=None):
    """
    Apply function asynchronously.
    
    Args:
        pool_obj: Pool object
        func: Function to execute
        args: Function arguments
        kwargs: Function keyword arguments
    
    Returns:
        Future object
    
    Example:
        future = pool.apply_async(my_pool, task, (arg1,))
    """
    kwargs = kwargs or {}
    return pool_obj.submit(func, *args, **kwargs)


def starmap(pool_obj, func, arg_tuples):
    """
    Map function with multiple arguments per item.
    
    Args:
        pool_obj: Pool object
        func: Function to apply
        arg_tuples: List of argument tuples
    
    Returns:
        List of results
    
    Example:
        results = pool.starmap(my_pool, add, [(1,2), (3,4)])
    """
    futures = [pool_obj.submit(func, *args) for args in arg_tuples]
    return [f.result() for f in futures]


def wait_all(futures, timeout=None):
    """
    Wait for all futures to complete.
    
    Args:
        futures: List of Future objects
        timeout: Timeout in seconds
    
    Returns:
        List of results
    
    Example:
        futures = [pool.submit(task, i) for i in range(10)]
        results = pool.wait_all(futures)
    """
    from concurrent.futures import wait
    done, pending = wait(futures, timeout=timeout)
    return [f.result() for f in done]


def as_completed(futures):
    """
    Yield futures as they complete.
    
    Args:
        futures: List of Future objects
    
    Yields:
        Completed futures
    
    Example:
        for future in pool.as_completed(futures):
            print(future.result())
    """
    from concurrent.futures import as_completed as _as_completed
    return _as_completed(futures)


def batch_process(func, items, batch_size=100, workers=None):
    """
    Process items in batches.
    
    Args:
        func: Function to apply to each batch
        items: Items to process
        batch_size: Size of each batch
        workers: Number of workers
    
    Returns:
        List of results from all batches
    
    Example:
        results = pool.batch_process(process_batch, data, batch_size=50)
    """
    batches = [items[i:i+batch_size] for i in range(0, len(items), batch_size)]
    return map_parallel(func, batches, workers=workers)


__all__ = [
    'ThreadPool', 'ProcessPool', 'thread_pool', 'process_pool',
    'map_parallel', 'cpu_count', 'apply_async', 'starmap',
    'wait_all', 'as_completed', 'batch_process'
]
