"""
benchmark - Performance benchmarking for Sona stdlib

Provides benchmarking tools:
- time: Time function execution
- compare: Compare multiple functions
- memory: Memory usage benchmarking
- quicktest: Quick duration-based benchmark
- suite: Complete benchmark suite
- percentile: Performance percentiles
- throughput: Operations per second
- regression: Compare implementations
"""

import time as _time
import statistics

__all__ = [
    'time', 'compare', 'timer', 'memory', 'quicktest', 'warmup',
    'suite', 'percentile', 'throughput', 'regression', 'Timer'
]


def time(func, iterations=1000):
    """
    Benchmark function execution time.
    
    Args:
        func: Function to benchmark
        iterations: Number of iterations
    
    Returns:
        Dictionary with timing stats
    
    Example:
        stats = benchmark.time(my_function, 1000)
        # {
        #   "iterations": 1000,
        #   "total": 1.234,
        #   "mean": 0.001234,
        #   "min": 0.001,
        #   "max": 0.002
        # }
    """
    times = []
    
    for _ in range(iterations):
        start = _time.perf_counter()
        func()
        end = _time.perf_counter()
        times.append(end - start)
    
    return {
        'iterations': iterations,
        'total': sum(times),
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'min': min(times),
        'max': max(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0
    }


def compare(functions, iterations=1000):
    """
    Compare performance of multiple functions.
    
    Args:
        functions: Dictionary of name->function
        iterations: Number of iterations
    
    Returns:
        Dictionary of benchmarksresults
    
    Example:
        results = benchmark.compare({
            "method_a": func_a,
            "method_b": func_b
        }, iterations=1000)
    """
    results = {}
    
    for name, func in functions.items():
        results[name] = time(func, iterations)
    
    # Add comparison
    means = {name: res['mean'] for name, res in results.items()}
    fastest = min(means, key=means.get)
    
    for name in results:
        if name != fastest:
            slowdown = means[name] / means[fastest]
            results[name]['vs_fastest'] = f"{slowdown:.2f}x slower"
        else:
            results[name]['vs_fastest'] = "fastest"
    
    return results


class Timer:
    """Context manager for timing code blocks."""
    
    def __init__(self, name="timer"):
        """Initialize timer."""
        self.name = name
        self.start_time = None
        self.elapsed = None
    
    def __enter__(self):
        """Start timer."""
        self.start_time = _time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer."""
        self.elapsed = _time.perf_counter() - self.start_time
    
    def __str__(self):
        """String representation."""
        return f"{self.name}: {self.elapsed:.6f}s"


def timer(name="timer"):
    """
    Create timing context manager.
    
    Args:
        name: Timer name
    
    Returns:
        Timer object
    
    Example:
        with benchmark.timer("database_query") as t:
            query_database()
        print(t.elapsed)
    """
    return Timer(name)


def memory(func, iterations=100):
    """
    Benchmark memory usage.
    
    Args:
        func: Function to benchmark
        iterations: Number of iterations
    
    Returns:
        Dictionary with memory stats
    
    Example:
        stats = benchmark.memory(my_function, 100)
    """
    import tracemalloc
    
    memories = []
    
    for _ in range(iterations):
        tracemalloc.start()
        func()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        memories.append(peak / (1024 * 1024))  # MB
    
    return {
        'iterations': iterations,
        'mean_mb': statistics.mean(memories),
        'median_mb': statistics.median(memories),
        'min_mb': min(memories),
        'max_mb': max(memories),
        'stdev_mb': statistics.stdev(memories) if len(memories) > 1 else 0
    }


def quicktest(func, duration=1.0):
    """
    Quick benchmark running for a specific duration.
    
    Args:
        func: Function to benchmark
        duration: Duration in seconds
    
    Returns:
        Dictionary with stats
    
    Example:
        stats = benchmark.quicktest(my_function, 2.0)
    """
    start = _time.perf_counter()
    iterations = 0
    times = []
    
    while (_time.perf_counter() - start) < duration:
        iter_start = _time.perf_counter()
        func()
        iter_end = _time.perf_counter()
        times.append(iter_end - iter_start)
        iterations += 1
    
    total_time = _time.perf_counter() - start
    
    return {
        'iterations': iterations,
        'duration': total_time,
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'min': min(times),
        'max': max(times),
        'ops_per_second': iterations / total_time
    }


def warmup(func, iterations=10):
    """
    Warm up function before benchmarking.
    
    Args:
        func: Function to warm up
        iterations: Number of warmup iterations
    
    Returns:
        None
    
    Example:
        benchmark.warmup(my_function, 20)
        stats = benchmark.time(my_function, 1000)
    """
    for _ in range(iterations):
        func()


def suite(functions, iterations=1000, warmup_runs=10):
    """
    Run complete benchmark suite with warmup.
    
    Args:
        functions: Dictionary of name->function
        iterations: Number of iterations
        warmup_runs: Number of warmup runs
    
    Returns:
        Dictionary of results
    
    Example:
        results = benchmark.suite({
            'method1': func1,
            'method2': func2
        })
    """
    results = {}
    
    # Warmup
    for name, func in functions.items():
        warmup(func, warmup_runs)
    
    # Benchmark
    results = compare(functions, iterations)
    
    return results


def percentile(func, iterations=1000, percentiles=None):
    """
    Calculate performance percentiles.
    
    Args:
        func: Function to benchmark
        iterations: Number of iterations
        percentiles: List of percentiles (default: [50, 90, 95, 99])
    
    Returns:
        Dictionary with percentile stats
    
    Example:
        stats = benchmark.percentile(my_function, 1000, [50, 90, 99])
    """
    if percentiles is None:
        percentiles = [50, 90, 95, 99]
    
    times = []
    
    for _ in range(iterations):
        start = _time.perf_counter()
        func()
        end = _time.perf_counter()
        times.append(end - start)
    
    times.sort()
    
    results = {
        'iterations': iterations,
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'percentiles': {}
    }
    
    for p in percentiles:
        idx = int((p / 100) * len(times))
        if idx >= len(times):
            idx = len(times) - 1
        results['percentiles'][f'p{p}'] = times[idx]
    
    return results


def throughput(func, iterations=1000):
    """
    Measure throughput (operations per second).
    
    Args:
        func: Function to benchmark
        iterations: Number of iterations
    
    Returns:
        Dictionary with throughput stats
    
    Example:
        stats = benchmark.throughput(my_function, 10000)
    """
    start = _time.perf_counter()
    
    for _ in range(iterations):
        func()
    
    elapsed = _time.perf_counter() - start
    ops_per_sec = iterations / elapsed
    
    return {
        'iterations': iterations,
        'elapsed': elapsed,
        'ops_per_second': ops_per_sec,
        'time_per_op': elapsed / iterations
    }


def regression(func_old, func_new, iterations=1000):
    """
    Compare old vs new implementation for regression testing.
    
    Args:
        func_old: Old function implementation
        func_new: New function implementation
        iterations: Number of iterations
    
    Returns:
        Dictionary with comparison results
    
    Example:
        results = benchmark.regression(old_func, new_func, 1000)
    """
    old_stats = time(func_old, iterations)
    new_stats = time(func_new, iterations)
    
    improvement = ((old_stats['mean'] - new_stats['mean']) / old_stats['mean']) * 100
    
    return {
        'old': old_stats,
        'new': new_stats,
        'improvement_percent': improvement,
        'faster': 'new' if improvement > 0 else 'old'
    }
