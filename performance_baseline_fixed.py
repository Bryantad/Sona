#!/usr/bin/env python3
"""
Sona Language Performance Baseline Suite (Fixed)
Establishes quantitative performance metrics for the current interpreter
"""

import time
import sys

# Add the Sona module to path
sys.path.append('.')


def run_performance_test(test_name, code, iterations=1000):
    """Run a performance test with timing"""
    try:
        from sona.interpreter import run_code_fast

        print(f"\n{'='*50}")
        print(f"Performance Test: {test_name}")
        print(f"Iterations: {iterations:,}")
        print(f"{'='*50}")

        # Warm-up run
        run_code_fast(code, debug_enabled=False)

        # Timed runs
        start_time = time.perf_counter()

        for i in range(iterations):
            run_code_fast(code, debug_enabled=False)

        end_time = time.perf_counter()

        total_time = end_time - start_time
        ops_per_second = iterations / total_time
        avg_time_ms = (total_time / iterations) * 1000

        print(f"Total time: {total_time:.4f} seconds")
        print(f"Operations/second: {ops_per_second:,.0f}")
        print(f"Average time per operation: {avg_time_ms:.4f} ms")

        return {
            'test_name': test_name,
            'total_time': total_time,
            'ops_per_second': ops_per_second,
            'avg_time_ms': avg_time_ms,
            'iterations': iterations
        }

    except Exception as e:
        print(f"Error in test {test_name}: {e}")
        return None


def main():
    print("Sona Language Performance Baseline Suite (Fixed)")
    print("=================================================")
    print()

    results = []

    # Test 1: Integer Arithmetic
    arithmetic_code = "let x = 10 + 5 * 2 - 3"
    result = run_performance_test("Integer Arithmetic", arithmetic_code, 5000)
    if result:
        results.append(result)

    # Test 2: String Operations
    string_code = 'let greeting = "Hello, " + "World!"'
    result = run_performance_test("String Operations", string_code, 3000)
    if result:
        results.append(result)

    # Test 3: Function Calls
    function_code = """
func add(a, b) {
    return a + b
}
let result = add(10, 20)
"""
    result = run_performance_test("Function Calls", function_code, 1000)
    if result:
        results.append(result)

    # Test 4: Variable Assignment
    assignment_code = """
let a = 10
let b = a + 5
let c = b * 2
"""
    result = run_performance_test("Variable Assignment", assignment_code, 4000)
    if result:
        results.append(result)

    # Test 5: Control Flow
    control_flow_code = """
let sum = 0
for i in range(0, 5) {
    if i > 2 {
        sum = sum + i
    }
}
"""
    result = run_performance_test("Control Flow (Loops)", control_flow_code, 500)
    if result:
        results.append(result)

    # Test 6: Simple Expressions
    expr_code = "10 + 20 * 3"
    result = run_performance_test("Simple Expressions", expr_code, 8000)
    if result:
        results.append(result)

    # Print summary
    print(f"\n{'='*70}")
    print("SONA LANGUAGE PERFORMANCE BASELINE SUMMARY")
    print(f"{'='*70}")

    for result in results:
        print(f"{result['test_name']:<25} {result['ops_per_second']:>10,.0f} ops/sec")

    print(f"\n{'='*70}")
    print("CURRENT INTERPRETER ANALYSIS")
    print(f"{'='*70}")

    if results:
        avg_performance = sum(r['ops_per_second'] for r in results) / len(results)
        best_performance = max(r['ops_per_second'] for r in results)
        worst_performance = min(r['ops_per_second'] for r in results)

        print(f"Average performance: {avg_performance:,.0f} ops/sec")
        print(f"Best performance: {best_performance:,.0f} ops/sec")
        print(f"Worst performance: {worst_performance:,.0f} ops/sec")
        print(f"Performance class: Research/Prototype level")
        print(f"Target improvement: 10-100x for production use")

    print(f"\n{'='*70}")
    print("PHASE 2 PERFORMANCE TARGETS")
    print(f"{'='*70}")
    print("Target improvements with type system and optimization:")
    print("- Integer arithmetic: 100x improvement (>500K ops/sec)")
    print("- String operations: 50x improvement (>150K ops/sec)")
    print("- Function calls: 30x improvement (>30K ops/sec)")
    print("- Control flow: 20x improvement (>10K ops/sec)")
    print("- Overall system: 10-50x improvement baseline")

    print(f"\n{'='*70}")
    print("NEXT STEPS FOR PERFORMANCE OPTIMIZATION")
    print(f"{'='*70}")
    print("1. Implement bytecode compilation pipeline")
    print("2. Add type inference for eliminating runtime checks")
    print("3. Optimize environment lookup (O(1) hash table)")
    print("4. Add JIT compilation with LLVM backend")
    print("5. Implement garbage collection and memory pooling")
    print("6. Add concurrent execution for parallelizable operations")


if __name__ == "__main__":
    main()
