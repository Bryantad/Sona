"""
async - Async/await utilities for Sona stdlib

Provides async programming helpers:
- run: Run async function synchronously
- gather: Run multiple async functions concurrently
- timeout: Run with timeout
"""

import asyncio
import time


def run(coro):
    """
    Run async function synchronously.
    
    Args:
        coro: Async function to run
    
    Returns:
        Function result
    
    Example:
        result = async.run(async_function())
    """
    return asyncio.run(coro)


def gather(*coros):
    """
    Run multiple async functions concurrently.
    
    Args:
        coros: Async functions to run
    
    Returns:
        List of results
    
    Example:
        results = async.gather(func1(), func2(), func3())
    """
    async def _gather():
        return await asyncio.gather(*coros)
    
    return asyncio.run(_gather())


def timeout(coro, seconds):
    """
    Run async function with timeout.
    
    Args:
        coro: Async function to run
        seconds: Timeout in seconds
    
    Returns:
        Function result or None if timeout
    
    Example:
        result = async.timeout(slow_function(), 5)
    """
    async def _timeout():
        try:
            return await asyncio.wait_for(coro, timeout=seconds)
        except asyncio.TimeoutError:
            return None
    
    return asyncio.run(_timeout())


def sleep(seconds):
    """
    Async sleep (for use in async functions).
    
    Args:
        seconds: Sleep duration
    
    Example:
        await async.sleep(1)
    """
    return asyncio.sleep(seconds)


def create_task(coro):
    """
    Create async task.
    
    Args:
        coro: Async function to run as task
    
    Returns:
        Task object
    
    Example:
        task = async.create_task(background_job())
    """
    return asyncio.create_task(coro)


def wait_for(tasks, timeout=None):
    """
    Wait for multiple tasks to complete.
    
    Args:
        tasks: List of tasks
        timeout: Optional timeout in seconds
    
    Returns:
        (done, pending) sets of tasks
    
    Example:
        done, pending = async.wait_for([task1, task2], timeout=10)
    """
    async def _wait():
        return await asyncio.wait(tasks, timeout=timeout)
    
    return asyncio.run(_wait())


def run_in_executor(func, *args, executor=None):
    """
    Run blocking function in executor (thread pool).
    
    Args:
        func: Blocking function to run
        args: Function arguments
        executor: Optional executor (default: ThreadPoolExecutor)
    
    Returns:
        Coroutine that runs function in executor
    
    Example:
        result = await async.run_in_executor(blocking_io_operation)
    """
    async def _run():
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, func, *args)
    
    return _run()


def as_completed(coros):
    """
    Return async functions as they complete.
    
    Args:
        coros: List of coroutines
    
    Returns:
        Iterator of completed results
    
    Example:
        for coro in async.as_completed([f1(), f2(), f3()]):
            result = async.run(coro)
            print(result)
    """
    return asyncio.as_completed(coros)


def shield(coro):
    """
    Protect coroutine from cancellation.
    
    Args:
        coro: Coroutine to protect
    
    Returns:
        Shielded coroutine
    
    Example:
        result = await async.shield(important_operation())
    """
    return asyncio.shield(coro)


def to_thread(func, *args, **kwargs):
    """
    Run synchronous function in separate thread (async wrapper).
    
    Args:
        func: Sync function
        args: Positional arguments
        kwargs: Keyword arguments
    
    Returns:
        Coroutine
    
    Example:
        result = await async.to_thread(blocking_function, arg1, arg2)
    """
    return asyncio.to_thread(func, *args, **kwargs)


def race(*coros):
    """
    Run coroutines and return first completed result.
    
    Args:
        coros: Coroutines to race
    
    Returns:
        First completed result
    
    Example:
        result = async.race(slow_api(), cache_lookup())
    """
    async def _race():
        done, pending = await asyncio.wait(
            coros, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        return done.pop().result()
    
    return asyncio.run(_race())


__all__ = [
    'run',
    'gather',
    'timeout',
    'sleep',
    'create_task',
    'wait_for',
    'run_in_executor',
    'as_completed',
    'shield',
    'to_thread',
    'race'
]
