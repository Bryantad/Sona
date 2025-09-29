"""
Quick VM Performance Test - Phase 1 Day 1
Simple test to validate VM performance improvement
"""
import os
import sys
import time


# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from bytecode import BytecodeGenerator, OpCode

from vm import SonaVM


def simple_vm_test():
    """Test basic VM performance."""
    print("=" * 50)
    print("PHASE 1 DAY 1: VM PERFORMANCE TEST")
    print("=" * 50)
    
    # Create bytecode program: let x = 42
    generator = BytecodeGenerator()
    generator.generate_basic_assignment('x', 42)
    generator.emit(OpCode.HALT)
    
    print(f"Generated {len(generator.instructions)} instructions")
    
    # Test single execution
    vm = SonaVM(debug_mode=False)
    vm.load_program(
        instructions=generator.instructions,
        constants=list(generator.constants.keys()),
        variable_names=list(generator.variables.keys())
    )
    
    start_time = time.perf_counter()
    result = vm.execute()
    end_time = time.perf_counter()
    
    single_execution_time = (end_time - start_time) * 1000  # ms
    
    print(f"Single execution: {single_execution_time:.4f} ms")
    print(f"Result: {result}")
    print(f"VM Stats: {vm.get_performance_stats()}")
    
    # Test multiple executions (optimized)
    iterations = 10000
    print(f"\nRunning {iterations:,} iterations (optimized)...")
    
    # Pre-create VM and load program once
    vm = SonaVM()
    vm.accessibility_enabled = False  # Disable for performance testing
    vm.load_program(
        instructions=generator.instructions,
        constants=list(generator.constants.keys()),
        variable_names=list(generator.variables.keys())
    )
    
    start_time = time.perf_counter()
    for _ in range(iterations):
        vm.reset()  # Reset VM state but keep loaded program
        vm.load_program(  # Reload is still needed for now
            instructions=generator.instructions,
            constants=list(generator.constants.keys()),
            variable_names=list(generator.variables.keys())
        )
        vm.execute()
    end_time = time.perf_counter()
    
    # Also test with pure execution (no reloading)
    print("\nTesting pure execution performance...")
    vm.reset()
    vm.load_program(
        instructions=generator.instructions,
        constants=list(generator.constants.keys()),
        variable_names=list(generator.variables.keys())
    )
    
    pure_iterations = 100000
    start_time = time.perf_counter()
    for _ in range(pure_iterations):
        # Reset VM state but keep program loaded
        vm.instruction_pointer = 0
        vm.halted = False
        vm.globals.clear()
        vm.stack.clear()
        vm.execute()
    end_time = time.perf_counter()
    
    pure_time = end_time - start_time
    pure_ops_per_second = pure_iterations / pure_time
    pure_avg_time_ms = (pure_time / pure_iterations) * 1000
    
    total_time = end_time - start_time
    ops_per_second = iterations / total_time
    avg_time_ms = (total_time / iterations) * 1000
    
    print("\nBulk Performance Results:")
    print(f"Total time: {total_time:.4f} seconds")
    print(f"Operations/second: {ops_per_second:,.0f}")
    print(f"Average time/operation: {avg_time_ms:.4f} ms")
    
    print("\nPure Execution Performance:")
    print(f"Pure iterations: {pure_iterations:,}")
    print(f"Pure time: {pure_time:.4f} seconds") 
    print(f"Pure ops/second: {pure_ops_per_second:,.0f}")
    print(f"Pure avg time: {pure_avg_time_ms:.4f} ms")
    
    # Compare with baseline target (650K ops/sec from interpreter)
    interpreter_baseline = 650000  # ops/sec from baseline test
    speedup = ops_per_second / interpreter_baseline
    pure_speedup = pure_ops_per_second / interpreter_baseline
    
    print("\nComparison to Interpreter Baseline:")
    print(f"Interpreter baseline: {interpreter_baseline:,} ops/sec")
    print(f"VM performance: {ops_per_second:,.0f} ops/sec")
    print(f"Speedup factor: {speedup:.2f}x")
    print(f"Pure VM performance: {pure_ops_per_second:,.0f} ops/sec") 
    print(f"Pure speedup factor: {pure_speedup:.2f}x")
    
    if pure_speedup >= 1.0:
        status = "✅ IMPROVEMENT ACHIEVED (Pure Execution)"
    elif speedup >= 1.0:
        status = "✅ IMPROVEMENT ACHIEVED"
    else:
        status = "⚠️ NEEDS OPTIMIZATION"
    
    print(f"\nStatus: {status}")
    
    return {
        'vm_ops_per_second': ops_per_second,
        'pure_vm_ops_per_second': pure_ops_per_second,
        'speedup': speedup,
        'pure_speedup': pure_speedup,
        'avg_time_ms': avg_time_ms
    }

if __name__ == "__main__":
    simple_vm_test()
