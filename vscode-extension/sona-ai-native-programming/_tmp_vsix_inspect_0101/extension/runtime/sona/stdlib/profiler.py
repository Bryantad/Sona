"""
profiler - Code profiling for Sona stdlib

Provides profiling tools:
- profile: Profile function execution
- memory: Profile memory usage
- timeit: Time function execution
- compare: Compare performance of functions
- trace: Line-by-line tracing
- measure_time: Measure execution time
- measure_memory: Measure memory usage
- benchmark: Benchmark with iterations
"""

import cProfile
import pstats
import io
import sys

__all__ = [
    'profile', 'memory', 'create', 'timeit', 'compare', 'trace',
    'get_stats', 'print_stats', 'measure_time', 'measure_memory', 'benchmark',
    'Profiler'
]


def profile(func, sort_by='cumulative', limit=20):
    """
    Profile function execution.
    
    Args:
        func: Function to profile
        sort_by: Sort order ('cumulative', 'time', 'calls')
        limit: Number of results to show
    
    Returns:
        Dictionary with profile stats
    
    Example:
        stats = profiler.profile(my_function)
        print(stats['output'])
    """
    profiler = cProfile.Profile()
    
    # Run profiling
    profiler.enable()
    result = func()
    profiler.disable()
    
    # Capture stats
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats(sort_by)
    stats.print_stats(limit)
    
    return {
        'result': result,
        'output': stream.getvalue()
    }


def memory(func):
    """
    Profile memory usage.
    
    Args:
        func: Function to profile
    
    Returns:
        Dictionary with memory info
    
    Example:
        mem_info = profiler.memory(my_function)
    """
    import tracemalloc
    
    # Start tracing
    tracemalloc.start()
    
    # Run function
    result = func()
    
    # Get stats
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return {
        'result': result,
        'current_mb': current / (1024 * 1024),
        'peak_mb': peak / (1024 * 1024)
    }


class Profiler:
    """Context manager for profiling code blocks."""
    
    def __init__(self, sort_by='cumulative', limit=20):
        """Initialize profiler."""
        self.sort_by = sort_by
        self.limit = limit
        self.profiler = cProfile.Profile()
        self.stats = None
    
    def __enter__(self):
        """Start profiling."""
        self.profiler.enable()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop profiling."""
        self.profiler.disable()
        
        stream = io.StringIO()
        self.stats = pstats.Stats(self.profiler, stream=stream)
        self.stats.strip_dirs()
        self.stats.sort_stats(self.sort_by)
        self.stats.print_stats(self.limit)
        
        self.output = stream.getvalue()
    
    def print(self):
        """Print profiling results."""
        print(self.output)


def create(sort_by='cumulative', limit=20):
    """
    Create profiler context manager.
    
    Args:
        sort_by: Sort order
        limit: Number of results
    
    Returns:
        Profiler object
    
    Example:
        with profiler.create() as p:
            expensive_operation()
        p.print()
    """
    return Profiler(sort_by, limit)


def timeit(func, repeat=5):
    """
    Time function execution.
    
    Args:
        func: Function to time
        repeat: Number of times to run
    
    Returns:
        Dictionary with timing stats
    
    Example:
        stats = profiler.timeit(my_function, repeat=10)
        print(stats['average'])
    """
    import time
    
    times = []
    for _ in range(repeat):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append(end - start)
    
    return {
        'times': times,
        'average': sum(times) / len(times),
        'min': min(times),
        'max': max(times),
        'total': sum(times)
    }


def compare(funcs, repeat=5):
    """
    Compare performance of multiple functions.
    
    Args:
        funcs: Dictionary of function name -> function
        repeat: Number of times to run each
    
    Returns:
        Dictionary of function name -> stats
    
    Example:
        results = profiler.compare({
            'method1': func1,
            'method2': func2
        })
    """
    results = {}
    for name, func in funcs.items():
        results[name] = timeit(func, repeat)
    
    return results


def trace(func):
    """
    Trace function execution with line-by-line profiling.
    
    Args:
        func: Function to trace
    
    Returns:
        Dictionary with trace info
    
    Example:
        trace_info = profiler.trace(my_function)
    """
    import sys
    
    trace_lines = []
    
    def tracer(frame, event, arg):
        if event == 'line':
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno
            trace_lines.append(f"{filename}:{lineno}")
        return tracer
    
    sys.settrace(tracer)
    result = func()
    sys.settrace(None)
    
    return {
        'result': result,
        'trace': trace_lines
    }


def get_stats(profiler_obj):
    """
    Get statistics from profiler object.
    
    Args:
        profiler_obj: Profiler object
    
    Returns:
        Statistics string
    
    Example:
        stats = profiler.get_stats(p)
    """
    return profiler_obj.output if hasattr(profiler_obj, 'output') else ''


def print_stats(profiler_obj):
    """
    Print profiler statistics.
    
    Args:
        profiler_obj: Profiler object
    
    Example:
        profiler.print_stats(p)
    """
    if hasattr(profiler_obj, 'print'):
        profiler_obj.print()
    elif hasattr(profiler_obj, 'output'):
        print(profiler_obj.output)


def measure_time(func, *args, **kwargs):
    """
    Measure execution time of a function call.
    
    Args:
        func: Function to measure
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Tuple of (result, elapsed_time)
    
    Example:
        result, time = profiler.measure_time(my_func, arg1, arg2)
    """
    import time
    
    start = time.perf_counter()
    result = func(*args, **kwargs)
    end = time.perf_counter()
    
    return result, end - start


def measure_memory(func, *args, **kwargs):
    """
    Measure memory usage of a function call.
    
    Args:
        func: Function to measure
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Tuple of (result, memory_mb)
    
    Example:
        result, mem = profiler.measure_memory(my_func, arg1)
    """
    import tracemalloc
    
    tracemalloc.start()
    result = func(*args, **kwargs)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return result, peak / (1024 * 1024)


def benchmark(func, iterations=1000):
    """
    Benchmark function with many iterations.
    
    Args:
        func: Function to benchmark
        iterations: Number of iterations
    
    Returns:
        Dictionary with benchmark results
    
    Example:
        results = profiler.benchmark(my_function, 10000)
    """
    import time
    
    start = time.perf_counter()
    
    for _ in range(iterations):
        func()
    
    end = time.perf_counter()
    total_time = end - start
    
    return {
        'iterations': iterations,
        'total_time': total_time,
        'avg_time': total_time / iterations,
        'ops_per_second': iterations / total_time
    }
