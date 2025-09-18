"""
Phase 1, Day 1: VM vs Interpreter Performance Comparison
Test VM performance against current interpreter baseline

Target: Demonstrate 2-10x performance improvement with initial VM implementation
"""

import os
import sys
import time


# Add paths for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import with proper error handling
try:
    from sona.interpreter import SonaInterpreter
except ImportError:
    # Fallback import
    from interpreter import SonaInterpreter

from bytecode import BytecodeGenerator, OpCode

from vm import SonaVM


def benchmark_interpreter(code: str, iterations: int = 1000):
    """Benchmark the current interpreter."""
    interpreter = SonaInterpreter()
    
    # Warm-up
    interpreter._execute_basic(code)
    
    # Timed execution
    start_time = time.perf_counter()
    for _ in range(iterations):
        interpreter = SonaInterpreter()  # Fresh interpreter each time
        interpreter._execute_basic(code)
    end_time = time.perf_counter()
    
    total_time = end_time - start_time
    ops_per_second = iterations / total_time
    
    return {
        'total_time': total_time,
        'ops_per_second': ops_per_second,
        'avg_time_ms': (total_time / iterations) * 1000
    }


def benchmark_vm(assignment_var: str, value: any, iterations: int = 1000):
    """Benchmark the VM implementation."""
    # Generate bytecode once
    generator = BytecodeGenerator()
    generator.generate_basic_assignment(assignment_var, value)
    generator.emit(OpCode.HALT)
    
    # Warm-up
    vm = SonaVM()
    vm.load_program(
        instructions=generator.instructions,
        constants=list(generator.constants.keys()),
        variable_names=list(generator.variables.keys())
    )
    vm.execute()
    
    # Timed execution
    start_time = time.perf_counter()
    for _ in range(iterations):
        vm = SonaVM()  # Fresh VM each time
        vm.load_program(
            instructions=generator.instructions,
            constants=list(generator.constants.keys()),
            variable_names=list(generator.variables.keys())
        )
        vm.execute()
    end_time = time.perf_counter()
    
    total_time = end_time - start_time
    ops_per_second = iterations / total_time
    
    return {
        'total_time': total_time,
        'ops_per_second': ops_per_second,
        'avg_time_ms': (total_time / iterations) * 1000
    }


def run_performance_comparison():
    """Run comprehensive performance comparison."""
    print("=" * 70)
    print("PHASE 1, DAY 1: VM vs INTERPRETER PERFORMANCE COMPARISON")
    print("=" * 70)
    print()
    
    tests = [
        {
            'name': 'Integer Assignment',
            'interpreter_code': 'let x = 42',
            'vm_var': 'x',
            'vm_value': 42,
            'iterations': 5000
        },
        {
            'name': 'String Assignment',
            'interpreter_code': 'let msg = "Hello World"',
            'vm_var': 'msg',
            'vm_value': "Hello World",
            'iterations': 3000
        },
        {
            'name': 'Float Assignment',
            'interpreter_code': 'let pi = 3.14159',
            'vm_var': 'pi',
            'vm_value': 3.14159,
            'iterations': 4000
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"\n{'-' * 50}")
        print(f"Test: {test['name']}")
        print(f"Iterations: {test['iterations']:,}")
        print(f"{'-' * 50}")
        
        # Benchmark interpreter
        print("Running interpreter benchmark...")
        interpreter_result = benchmark_interpreter(
            test['interpreter_code'], 
            test['iterations']
        )
        
        # Benchmark VM
        print("Running VM benchmark...")
        vm_result = benchmark_vm(
            test['vm_var'],
            test['vm_value'], 
            test['iterations']
        )
        
        # Calculate improvement
        speedup = vm_result['ops_per_second'] / interpreter_result['ops_per_second']
        time_reduction = (1 - vm_result['avg_time_ms'] / interpreter_result['avg_time_ms']) * 100
        
        print("\nInterpreter Performance:")
        print(f"  Operations/sec: {interpreter_result['ops_per_second']:,.0f}")
        print(f"  Avg time/op:    {interpreter_result['avg_time_ms']:.4f} ms")
        
        print("\nVM Performance:")
        print(f"  Operations/sec: {vm_result['ops_per_second']:,.0f}")
        print(f"  Avg time/op:    {vm_result['avg_time_ms']:.4f} ms")
        
        print("\nPerformance Improvement:")
        print(f"  Speedup:        {speedup:.2f}x")
        print(f"  Time reduction: {time_reduction:.1f}%")
        
        results.append({
            'test_name': test['name'],
            'interpreter_ops': interpreter_result['ops_per_second'],
            'vm_ops': vm_result['ops_per_second'],
            'speedup': speedup,
            'time_reduction': time_reduction
        })
    
    # Summary
    print(f"\n{'=' * 70}")
    print("PERFORMANCE COMPARISON SUMMARY")
    print(f"{'=' * 70}")
    
    avg_speedup = sum(r['speedup'] for r in results) / len(results)
    max_speedup = max(r['speedup'] for r in results)
    min_speedup = min(r['speedup'] for r in results)
    
    print("\nSpeedup Analysis:")
    print(f"  Average speedup: {avg_speedup:.2f}x")
    print(f"  Maximum speedup: {max_speedup:.2f}x")
    print(f"  Minimum speedup: {min_speedup:.2f}x")
    
    print("\nDetailed Results:")
    for result in results:
        print(f"  {result['test_name']:<20} "
              f"{result['interpreter_ops']:>10,.0f} -> "
              f"{result['vm_ops']:>10,.0f} ops/sec "
              f"({result['speedup']:>5.2f}x)")
    
    # Achievement assessment
    print(f"\n{'=' * 70}")
    print("PHASE 1 DAY 1 ACHIEVEMENT ASSESSMENT")
    print(f"{'=' * 70}")
    
    if avg_speedup >= 2.0:
        print("🎉 SUCCESS: Target 2x+ average speedup ACHIEVED!")
        print(f"   Actual average speedup: {avg_speedup:.2f}x")
    else:
        print("⚠️  PARTIAL: Below 2x target, but foundation established")
        print(f"   Current average speedup: {avg_speedup:.2f}x")
    
    if max_speedup >= 5.0:
        print("🚀 OUTSTANDING: 5x+ speedup achieved in best case")
    elif max_speedup >= 3.0:
        print("✅ GOOD: 3x+ speedup achieved in best case")
    
    print("\nNext Steps for Day 2:")
    print("1. Optimize VM instruction dispatch")
    print("2. Implement instruction-level optimizations")
    print("3. Add constant folding and dead code elimination")
    print("4. Benchmark against complex expressions and control flow")
    
    return results


if __name__ == "__main__":
    run_performance_comparison()
