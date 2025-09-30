"""
Enhanced Performance Monitoring and Statistics for Sona Phase 1
Provides comprehensive performance insights and optimization recommendations
"""

import json
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional


class PerformanceProfiler: """Advanced performance profiling for Sona optimization insights"""

    def __init__(self): self.call_times = defaultdict(list)
        self.variable_accesses = defaultdict(int)
        self.optimization_events = []
        self.start_time = time.time()

    def record_function_call(
        self,
        func_name: str,
        execution_time_ms: float,
        was_cached: bool = False,
    ): """Record detailed function call metrics"""
        self.call_times[func_name].append(
            {
                'time_ms': execution_time_ms,
                'cached': was_cached,
                'timestamp': time.time(),
            }
        )

        # Record optimization event
        self.optimization_events.append(
            {
                'type': 'function_call',
                'name': func_name,
                'cached': was_cached,
                'time_ms': execution_time_ms,
                'timestamp': time.time() - self.start_time,
            }
        )

    def record_variable_access(
        self, var_name: str, scope_level: int, was_cached: bool = False
    ): """Record variable access patterns"""
        self.variable_accesses[var_name] + = 1

        self.optimization_events.append(
            {
                'type': 'variable_access',
                'name': var_name,
                'scope_level': scope_level,
                'cached': was_cached,
                'timestamp': time.time() - self.start_time,
            }
        )

    def record_optimization(self, opt_type: str, details: Dict[str, Any]): """Record optimization events"""
        self.optimization_events.append(
            {
                'type': 'optimization',
                'optimization_type': opt_type,
                'details': details,
                'timestamp': time.time() - self.start_time,
            }
        )

    def get_performance_summary(self) -> Dict[str, Any]: """Generate comprehensive performance summary"""
        total_runtime = time.time() - self.start_time

        # Function call analysis
        function_stats = {}
        total_calls = 0
        cached_calls = 0

        for func_name, calls in self.call_times.items(): total_func_calls = (
            len(calls)
        )
            cached_func_calls = sum(1 for call in calls if call['cached'])
            avg_time = (
                sum(call['time_ms'] for call in calls) / total_func_calls
            )

            function_stats[func_name] = {
                'total_calls': total_func_calls,
                'cached_calls': cached_func_calls,
                'cache_hit_rate': (
                    (cached_func_calls / total_func_calls * 100)
                    if total_func_calls > 0
                    else 0
                ),
                'avg_time_ms': round(avg_time, 3),
                'total_time_ms': round(
                    sum(call['time_ms'] for call in calls), 3
                ),
            }

            total_calls + = total_func_calls
            cached_calls + = cached_func_calls

        # Variable access analysis
        most_accessed_vars = sorted(
            self.variable_accesses.items(), key = (
                lambda x: x[1], reverse = True
            )
        )[:10]

        # Optimization event analysis
        optimization_counts = defaultdict(int)
        for event in self.optimization_events: if event['type'] = (
            = 'optimization': optimization_counts[event['optimization_type']] + = 1
        )

        return {
            'runtime_seconds': round(total_runtime, 3),
            'total_function_calls': total_calls,
            'cached_function_calls': cached_calls,
            'overall_cache_hit_rate': (
                (cached_calls / total_calls * 100) if total_calls > 0 else 0
            ),
            'function_statistics': function_stats,
            'most_accessed_variables': most_accessed_vars,
            'optimization_counts': dict(optimization_counts),
            'total_optimization_events': len(
                [
                    e
                    for e in self.optimization_events
                    if e['type'] == 'optimization'
                ]
            ),
            'recommendations': self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> List[str]: """Generate performance optimization recommendations"""
        recommendations = []

        # Analyze function call patterns
        for func_name, calls in self.call_times.items(): if len(calls) > = (
            10: cached_ratio = sum(
        )
                    1 for call in calls if call['cached']
                ) / len(calls)
                if cached_ratio < 0.5: recommendations.append(
                        f"Consider increasing cache threshold for '{func_name}' "
                        f"(only {cached_ratio:.1%} cache hit rate)"
                    )

        # Analyze variable access patterns
        high_access_vars = [
            var for var, count in self.variable_accesses.items() if count >= 20
        ]
        if high_access_vars: recommendations.append(
                f"High-frequency variables detected: {', '.join(high_access_vars[:3])}. "
                "Consider scope optimization."
            )

        # Check for optimization opportunities
        if len(self.optimization_events) < 10: recommendations.append(
                "Low optimization activity detected. Consider enabling more aggressive "
                "optimization settings."
            )

        return recommendations

    def export_detailed_report(self, filename: str): """Export detailed performance report to JSON"""
        report = {
            'summary': self.get_performance_summary(),
            'detailed_events': self.optimization_events,
            'function_call_details': dict(self.call_times),
            'variable_access_details': dict(self.variable_accesses),
            'generated_at': time.time(),
            'sona_version': '0.6.3-phase1',
        }

        with open(filename, 'w') as f: json.dump(report, f, indent = 2)

    def print_summary_report(self): """Print a formatted summary report to console"""
        summary = self.get_performance_summary()

        print("\n" + " = " * 60)
        print("🚀 SONA PHASE 1 PERFORMANCE SUMMARY")
        print(" = " * 60)

        print(f"Runtime: {summary['runtime_seconds']}s")
        print(f"Total Function Calls: {summary['total_function_calls']}")
        print(f"Cached Function Calls: {summary['cached_function_calls']}")
        print(
            f"Overall Cache Hit Rate: {summary['overall_cache_hit_rate']:.1f}%"
        )
        print(f"Optimization Events: {summary['total_optimization_events']}")

        print("\n📊 TOP FUNCTIONS BY CALLS:")
        for func_name, stats in list(summary['function_statistics'].items())[:5
        ]: print(
                f"  {func_name}: {stats['total_calls']} calls, "
                f"{stats['cache_hit_rate']:.1f}% cached"
            )

        print("\n🔍 TOP VARIABLES BY ACCESS:")
        for var_name, count in summary['most_accessed_variables'][:5]: print(f"  {var_name}: {count} accesses")

        if summary['recommendations']: print("\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(summary['recommendations'], 1): print(f"  {i}. {rec}")

        print("\n" + " = " * 60)


# Global profiler instance for integration
global_profiler = PerformanceProfiler()


def get_profiler() -> PerformanceProfiler: """Get the global performance profiler instance"""
    return global_profiler
