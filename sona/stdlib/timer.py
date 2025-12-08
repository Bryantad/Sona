"""Timing helpers for quick measurements."""
from __future__ import annotations

import time
from contextlib import asynccontextmanager, contextmanager
from typing import Callable, Iterator, TypeVar

T = TypeVar("T")


class Timer:
    def __init__(self) -> None:
        self.elapsed: float = 0.0
        self._start: float | None = None

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._start is not None:
            self.elapsed = time.perf_counter() - self._start
            self._start = None

    async def __aenter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._start is not None:
            self.elapsed = time.perf_counter() - self._start
            self._start = None


@contextmanager
def measure() -> Iterator[dict[str, float]]:
    start = time.perf_counter()
    info: dict[str, float] = {"elapsed": 0.0}
    try:
        yield info
    finally:
        info["elapsed"] = time.perf_counter() - start


@asynccontextmanager
async def measure_async() -> Iterator[dict[str, float]]:
    start = time.perf_counter()
    info: dict[str, float] = {"elapsed": 0.0}
    try:
        yield info
    finally:
        info["elapsed"] = time.perf_counter() - start


def time_call(func: Callable[..., T], *args, **kwargs) -> tuple[T, float]:
    start = time.perf_counter()
    result = func(*args, **kwargs)
    return result, time.perf_counter() - start


def benchmark(func: Callable, iterations: int = 1000) -> dict[str, float]:
    """
    Benchmark a function over multiple iterations.

    Args:
        func: Function to benchmark
        iterations: Number of iterations

    Returns:
        Dict with min, max, avg, total times

    Example:
        stats = timer.benchmark(lambda: expensive_operation(), 100)
        print(f"Average: {stats['avg']:.4f}s")
    """
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        times.append(time.perf_counter() - start)

    return {
        'min': min(times),
        'max': max(times),
        'avg': sum(times) / len(times),
        'total': sum(times),
        'iterations': iterations
    }


def timeout_after(seconds: float):
    """
    Context manager to execute code with timeout.

    Args:
        seconds: Timeout in seconds

    Returns:
        Context manager

    Example:
        with timer.timeout_after(5.0):
            # Code that should complete in 5 seconds
            long_operation()

    Note: This is a simple timing check, not a hard timeout.
    """
    @contextmanager
    def _timeout():
        start = time.perf_counter()
        yield
        elapsed = time.perf_counter() - start
        if elapsed > seconds:
            import warnings
            warnings.warn(
                f"Operation took {elapsed:.2f}s, "
                f"exceeding timeout of {seconds}s"
            )
    return _timeout()


def rate_limit(calls_per_second: float):
    """
    Rate limiter to control function call frequency.

    Args:
        calls_per_second: Maximum calls per second

    Returns:
        Decorator function

    Example:
        @timer.rate_limit(10)  # Max 10 calls/second
        def api_call():
            pass
    """
    min_interval = 1.0 / calls_per_second
    last_call = [0.0]

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            now = time.perf_counter()
            elapsed = now - last_call[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            last_call[0] = time.perf_counter()
            return func(*args, **kwargs)
        return wrapper
    return decorator


class Stopwatch:
    """
    Simple stopwatch for manual timing.

    Example:
        sw = timer.Stopwatch()
        sw.start()
        # ... do work ...
        print(f"Elapsed: {sw.stop():.2f}s")
        sw.reset()
    """

    def __init__(self) -> None:
        self._start_time: float | None = None
        self._elapsed: float = 0.0
        self._running: bool = False

    def start(self) -> None:
        """Start the stopwatch."""
        if not self._running:
            self._start_time = time.perf_counter()
            self._running = True

    def stop(self) -> float:
        """Stop and return elapsed time."""
        if self._running and self._start_time is not None:
            self._elapsed = time.perf_counter() - self._start_time
            self._running = False
        return self._elapsed

    def reset(self) -> None:
        """Reset the stopwatch."""
        self._start_time = None
        self._elapsed = 0.0
        self._running = False

    def elapsed(self) -> float:
        """Get current elapsed time without stopping."""
        if self._running and self._start_time is not None:
            return time.perf_counter() - self._start_time
        return self._elapsed


__all__ = [
    "Timer",
    "measure",
    "measure_async",
    "time_call",
    "benchmark",
    "timeout_after",
    "rate_limit",
    "Stopwatch"
]
