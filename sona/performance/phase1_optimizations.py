"""
Sona Performance Optimization Framework - Phase 1 Implementation
Performance interventions to achieve 2-5x immediate speedup before VM implementation
"""

import hashlib
import time
from collections import OrderedDict
from functools import wraps
from typing import Dict, Any, Optional, Tuple
import weakref

class LRUCache:
    """Least Recently Used cache implementation for function results"""
    
    def __init__(self, max_size: int = 1024):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache, moving to end if found"""
        if key in self.cache:
            # Move to end (most recently used)
            value = self.cache.pop(key)
            self.cache[key] = value
            self.stats['hits'] += 1
            return value
        
        self.stats['misses'] += 1
        return None
    
    def put(self, key: str, value: Any):
        """Add value to cache, evicting oldest if necessary"""
        if key in self.cache:
            # Update existing entry
            self.cache.pop(key)
        elif len(self.cache) >= self.max_size:
            # Evict oldest entry
            self.cache.popitem(last=False)
            self.stats['evictions'] += 1
        
        self.cache[key] = value
    
    def clear(self):
        """Clear all cached entries"""
        self.cache.clear()
        self.stats = {'hits': 0, 'misses': 0, 'evictions': 0}
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache performance statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 2),
            'cache_size': len(self.cache)
        }

class FunctionCallCache:
    """Implement memoization for frequently called functions"""
    
    def __init__(self, max_size: int = 1024):
        self.cache = LRUCache(max_size)
        self.call_frequency = {}
        self.max_size = max_size
        self.performance_monitor = PerformanceMonitor()
        
        # Cache thresholds
        self.MIN_CALLS_TO_CACHE = 10
        self.MIN_EXECUTION_TIME_MS = 1.0  # Only cache functions taking >1ms
    
    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate a unique cache key for function call"""
        # Create deterministic hash of arguments
        args_str = str(args) + str(sorted(kwargs.items()))
        args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
        return f"{func_name}:{args_hash}"
    
    def get_cached_result(self, func_name: str, args: tuple, kwargs: dict) -> Optional[Any]:
        """Get cached result if available"""
        cache_key = self._generate_cache_key(func_name, args, kwargs)
        return self.cache.get(cache_key)
    
    def cache_result(self, func_name: str, args: tuple, kwargs: dict, result: Any):
        """Cache function result if caching is beneficial"""
        if self.should_cache_function(func_name):
            cache_key = self._generate_cache_key(func_name, args, kwargs)
            self.cache.put(cache_key, result)
    
    def should_cache_function(self, func_name: str) -> bool:
        """Determine if function should be cached based on heuristics"""
        frequency = self.call_frequency.get(func_name, 0)
        avg_time = self.performance_monitor.get_average_time(func_name)
        
        # Cache if called frequently OR takes significant time
        return (frequency >= self.MIN_CALLS_TO_CACHE or 
                avg_time >= self.MIN_EXECUTION_TIME_MS)
    
    def record_function_call(self, func_name: str, execution_time_ms: float):
        """Record function call for caching decisions"""
        self.call_frequency[func_name] = self.call_frequency.get(func_name, 0) + 1
        self.performance_monitor.record_execution(func_name, execution_time_ms)
    
    def get_cache_stats(self) -> dict:
        """Get comprehensive caching statistics"""
        return {
            'cache_stats': self.cache.get_stats(),
            'function_frequencies': dict(sorted(
                self.call_frequency.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]),  # Top 10 most called functions
            'performance_stats': self.performance_monitor.get_top_functions(10)
        }

class PerformanceMonitor:
    """Monitor function execution times for optimization decisions"""
    
    def __init__(self):
        self.execution_times = {}  # func_name -> list of execution times
        self.total_calls = {}
        self.total_time = {}
    
    def record_execution(self, func_name: str, execution_time_ms: float):
        """Record execution time for a function"""
        if func_name not in self.execution_times:
            self.execution_times[func_name] = []
            self.total_calls[func_name] = 0
            self.total_time[func_name] = 0.0
        
        # Keep only last 100 measurements to prevent memory bloat
        if len(self.execution_times[func_name]) >= 100:
            self.execution_times[func_name].pop(0)
        
        self.execution_times[func_name].append(execution_time_ms)
        self.total_calls[func_name] += 1
        self.total_time[func_name] += execution_time_ms
    
    def get_average_time(self, func_name: str) -> float:
        """Get average execution time for a function"""
        if func_name not in self.execution_times:
            return 0.0
        
        times = self.execution_times[func_name]
        return sum(times) / len(times) if times else 0.0
    
    def get_top_functions(self, limit: int = 10) -> list:
        """Get top functions by total execution time"""
        function_stats = []
        
        for func_name in self.total_time:
            avg_time = self.get_average_time(func_name)
            function_stats.append({
                'function': func_name,
                'total_time_ms': round(self.total_time[func_name], 2),
                'avg_time_ms': round(avg_time, 2),
                'call_count': self.total_calls[func_name]
            })
        
        return sorted(function_stats, key=lambda x: x['total_time_ms'], reverse=True)[:limit]

class ScopeAwareVariableCache:
    """Optimize variable lookups with scope-aware caching"""
    
    def __init__(self):
        self.scope_cache = {}  # scope_id -> {var_name -> value}
        self.variable_access_frequency = {}  # var_name -> access_count
        self.scope_hierarchy = {}  # scope_id -> parent_scope_id
        
        # Use weak references to prevent memory leaks
        self.scope_objects = weakref.WeakValueDictionary()
    
    def register_scope(self, scope_id: str, scope_obj: dict, parent_scope_id: Optional[str] = None):
        """Register a new scope for caching"""
        self.scope_cache[scope_id] = {}
        self.scope_hierarchy[scope_id] = parent_scope_id
        self.scope_objects[scope_id] = scope_obj
    
    def get_variable(self, scope_id: str, var_name: str) -> Tuple[Optional[Any], bool]:
        """
        Get variable value with caching
        Returns: (value, found)
        """
        # Record access frequency
        self.variable_access_frequency[var_name] = self.variable_access_frequency.get(var_name, 0) + 1
        
        # Check cache first
        if scope_id in self.scope_cache and var_name in self.scope_cache[scope_id]:
            return self.scope_cache[scope_id][var_name], True
        
        # Look up in scope hierarchy
        current_scope_id = scope_id
        while current_scope_id is not None:
            scope_obj = self.scope_objects.get(current_scope_id)
            if scope_obj and var_name in scope_obj:
                value = scope_obj[var_name]
                
                # Cache frequently accessed variables
                if self.variable_access_frequency[var_name] >= 5:
                    if scope_id not in self.scope_cache:
                        self.scope_cache[scope_id] = {}
                    self.scope_cache[scope_id][var_name] = value
                
                return value, True
            
            current_scope_id = self.scope_hierarchy.get(current_scope_id)
        
        return None, False
    
    def invalidate_variable(self, var_name: str):
        """Invalidate cached variable across all scopes"""
        for scope_cache in self.scope_cache.values():
            scope_cache.pop(var_name, None)
    
    def cleanup_scope(self, scope_id: str):
        """Clean up scope when it's no longer needed"""
        self.scope_cache.pop(scope_id, None)
        self.scope_hierarchy.pop(scope_id, None)
        # WeakValueDictionary will automatically clean up scope_objects

class ConstantFolder:
    """Implement constant folding optimization at parse time"""
    
    FOLDABLE_OPERATIONS = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: a / b if b != 0 else None,
        '%': lambda a, b: a % b if b != 0 else None,
        '**': lambda a, b: a ** b,
        '==': lambda a, b: a == b,
        '!=': lambda a, b: a != b,
        '<': lambda a, b: a < b,
        '>': lambda a, b: a > b,
        '<=': lambda a, b: a <= b,
        '>=': lambda a, b: a >= b,
        '&&': lambda a, b: a and b,
        '||': lambda a, b: a or b,
    }
    
    def __init__(self):
        self.folded_expressions = 0
        self.optimization_savings = 0.0  # Estimated time saved in ms
    
    def can_fold_expression(self, operation: str, left_value: Any, right_value: Any) -> bool:
        """Check if expression can be folded at compile time"""
        if operation not in self.FOLDABLE_OPERATIONS:
            return False
        
        # Only fold if both operands are constants (numbers, strings, booleans)
        if not self._is_constant(left_value) or not self._is_constant(right_value):
            return False
        
        # Special checks for division by zero
        if operation in ['/', '%'] and right_value == 0:
            return False
        
        return True
    
    def fold_expression(self, operation: str, left_value: Any, right_value: Any) -> Any:
        """Fold constant expression into a single value"""
        if not self.can_fold_expression(operation, left_value, right_value):
            return None
        
        try:
            folder_func = self.FOLDABLE_OPERATIONS[operation]
            result = folder_func(left_value, right_value)
            
            self.folded_expressions += 1
            self.optimization_savings += 0.1  # Estimated 0.1ms saved per folded expression
            
            return result
        except Exception:
            # If folding fails, return None to indicate no optimization
            return None
    
    def _is_constant(self, value: Any) -> bool:
        """Check if value is a compile-time constant"""
        return isinstance(value, (int, float, str, bool))
    
    def get_optimization_stats(self) -> dict:
        """Get constant folding statistics"""
        return {
            'expressions_folded': self.folded_expressions,
            'estimated_time_saved_ms': round(self.optimization_savings, 2)
        }

class StringInterningPool:
    """Implement string interning for frequently used literals"""
    
    def __init__(self, max_pool_size: int = 10000):
        self.string_pool = {}
        self.access_frequency = {}
        self.max_pool_size = max_pool_size
        
        # Intern frequency threshold
        self.INTERN_THRESHOLD = 3
    
    def intern_string(self, string_value: str) -> str:
        """Intern string if it's used frequently enough"""
        # Track usage frequency
        self.access_frequency[string_value] = self.access_frequency.get(string_value, 0) + 1
        
        # Return interned string if already in pool
        if string_value in self.string_pool:
            return self.string_pool[string_value]
        
        # Intern if used frequently and pool has space
        if (self.access_frequency[string_value] >= self.INTERN_THRESHOLD and 
            len(self.string_pool) < self.max_pool_size):
            self.string_pool[string_value] = string_value
            return self.string_pool[string_value]
        
        return string_value
    
    def get_interning_stats(self) -> dict:
        """Get string interning statistics"""
        total_accesses = sum(self.access_frequency.values())
        interned_accesses = sum(
            freq for string, freq in self.access_frequency.items() 
            if string in self.string_pool
        )
        
        intern_rate = (interned_accesses / total_accesses * 100) if total_accesses > 0 else 0
        
        return {
            'pool_size': len(self.string_pool),
            'total_unique_strings': len(self.access_frequency),
            'total_string_accesses': total_accesses,
            'interned_access_rate_percent': round(intern_rate, 2),
            'memory_saved_estimate': len(self.string_pool) * 50  # Rough estimate
        }

class PerformanceOptimizer:
    """Main coordinator for all performance optimizations"""
    
    def __init__(self):
        self.function_cache = FunctionCallCache()
        self.variable_cache = ScopeAwareVariableCache()
        self.constant_folder = ConstantFolder()
        self.string_pool = StringInterningPool()
        
        self.optimization_enabled = True
        self.start_time = time.time()
    
    def wrap_function_call(self, func_name: str, original_func):
        """Wrap function with caching and performance monitoring"""
        @wraps(original_func)
        def optimized_function(*args, **kwargs):
            if not self.optimization_enabled:
                return original_func(*args, **kwargs)
            
            # Check cache first
            cached_result = self.function_cache.get_cached_result(func_name, args, kwargs)
            if cached_result is not None:
                return cached_result
            
            # Execute function with timing
            start_time = time.perf_counter()
            result = original_func(*args, **kwargs)
            execution_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
            
            # Record performance and cache if beneficial
            self.function_cache.record_function_call(func_name, execution_time)
            self.function_cache.cache_result(func_name, args, kwargs, result)
            
            return result
        
        return optimized_function
    
    def optimize_variable_access(self, scope_id: str, var_name: str, fallback_lookup):
        """Optimize variable access with caching"""
        if not self.optimization_enabled:
            return fallback_lookup()
        
        value, found = self.variable_cache.get_variable(scope_id, var_name)
        if found:
            return value
        
        # Fallback to original lookup
        return fallback_lookup()
    
    def optimize_string_literal(self, string_value: str) -> str:
        """Optimize string literal with interning"""
        if not self.optimization_enabled:
            return string_value
        
        return self.string_pool.intern_string(string_value)
    
    def optimize_constant_expression(self, operation: str, left: Any, right: Any):
        """Optimize constant expression with folding"""
        if not self.optimization_enabled:
            return None
        
        return self.constant_folder.fold_expression(operation, left, right)
    
    def get_comprehensive_stats(self) -> dict:
        """Get comprehensive optimization statistics"""
        runtime_seconds = time.time() - self.start_time
        
        return {
            'runtime_seconds': round(runtime_seconds, 2),
            'optimization_enabled': self.optimization_enabled,
            'function_caching': self.function_cache.get_cache_stats(),
            'constant_folding': self.constant_folder.get_optimization_stats(),
            'string_interning': self.string_pool.get_interning_stats(),
            'variable_cache_size': len(self.variable_cache.scope_cache)
        }
    
    def enable_optimizations(self):
        """Enable all optimizations"""
        self.optimization_enabled = True
    
    def disable_optimizations(self):
        """Disable all optimizations (for debugging)"""
        self.optimization_enabled = False
    
    def clear_all_caches(self):
        """Clear all caches (useful for testing)"""
        self.function_cache.cache.clear()
        self.variable_cache.scope_cache.clear()
        self.string_pool.string_pool.clear()

# Global optimizer instance
performance_optimizer = PerformanceOptimizer()

def get_optimizer() -> PerformanceOptimizer:
    """Get the global performance optimizer instance"""
    return performance_optimizer

def benchmark_optimization(func, *args, iterations=1000, **kwargs):
    """Benchmark function with and without optimizations"""
    optimizer = get_optimizer()
    
    # Benchmark without optimizations
    optimizer.disable_optimizations()
    start_time = time.perf_counter()
    for _ in range(iterations):
        func(*args, **kwargs)
    unoptimized_time = time.perf_counter() - start_time
    
    # Benchmark with optimizations
    optimizer.enable_optimizations()
    start_time = time.perf_counter()
    for _ in range(iterations):
        func(*args, **kwargs)
    optimized_time = time.perf_counter() - start_time
    
    speedup = unoptimized_time / optimized_time if optimized_time > 0 else float('inf')
    
    return {
        'unoptimized_time_ms': round(unoptimized_time * 1000, 2),
        'optimized_time_ms': round(optimized_time * 1000, 2),
        'speedup_factor': round(speedup, 2),
        'improvement_percent': round((1 - optimized_time / unoptimized_time) * 100, 2)
    }
