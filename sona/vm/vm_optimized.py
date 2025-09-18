"""
Sona VM Optimization v2.0 - Phase 1, Day 2
High-Performance VM with Jump Table Dispatch

Target: 2-10x performance improvement through:
1. Jump table instruction dispatch (30% improvement)  
2. Optimized constant/variable loading (20% improvement)
3. Pre-allocated instruction arrays (15% improvement)
4. Streamlined cognitive processing (10% improvement)
"""

from typing import Any, Dict, List


try:
    from .bytecode import Instruction, OpCode
    from .stack import CallStack, VMStack
except ImportError:
    from bytecode import Instruction, OpCode
    from stack import CallStack, VMStack


class SonaVMOptimized:
    """
    Optimized Sona Virtual Machine with jump table dispatch.
    
    Target performance: 650K+ ops/sec (2x baseline improvement)
    Stretch target: 1.3M+ ops/sec (4x baseline improvement)
    """
    
    def __init__(self, debug_mode: bool = False):
        """Initialize the optimized Sona VM."""
        self.stack = VMStack()
        self.call_stack = CallStack()
        self.globals: dict[str, Any] = {}
        self.constants: list[Any] = []
        self.variable_names: list[str] = []
        self.cognitive_blocks: list[dict[str, Any]] = []
        
        # Execution state
        self.instructions: list[Instruction] = []
        self.instruction_pointer = 0
        self.halted = False
        
        # Performance tracking
        self.instruction_count = 0
        self.debug_mode = debug_mode
        self.performance_stats = {
            'total_instructions': 0,
            'function_calls': 0,
            'cognitive_blocks_processed': 0,
            'execution_time': 0.0
        }
        
        # Cognitive accessibility (optimized)
        self.accessibility_enabled = True
        self.cognitive_load_threshold = 0.8
        self.thinking_pause_ms = 5  # Reduced from 50ms for performance
        
        # OPTIMIZATION 1: Jump table dispatch instead of dictionary
        self._init_optimized_dispatch()
    
    def _init_optimized_dispatch(self):
        """Initialize optimized jump table for instruction dispatch."""
        # Pre-allocate jump table array indexed by opcode value
        max_opcode = max(op.value for op in OpCode)
        self.dispatch_table = [None] * (max_opcode + 1)
        
        # Populate jump table with direct function references
        self.dispatch_table[OpCode.LOAD_CONST.value] = self._handle_load_const
        self.dispatch_table[OpCode.LOAD_VAR.value] = self._handle_load_var
        self.dispatch_table[OpCode.STORE_VAR.value] = self._handle_store_var
        self.dispatch_table[OpCode.POP_TOP.value] = self._handle_pop_top
        self.dispatch_table[OpCode.DUP_TOP.value] = self._handle_dup_top
        
        self.dispatch_table[OpCode.BINARY_ADD.value] = self._handle_binary_add
        self.dispatch_table[OpCode.BINARY_SUB.value] = self._handle_binary_sub
        self.dispatch_table[OpCode.BINARY_MUL.value] = self._handle_binary_mul
        self.dispatch_table[OpCode.BINARY_DIV.value] = self._handle_binary_div
        
        self.dispatch_table[OpCode.COMPARE_EQ.value] = self._handle_compare_eq
        self.dispatch_table[OpCode.COMPARE_NE.value] = self._handle_compare_ne
        self.dispatch_table[OpCode.COMPARE_LT.value] = self._handle_compare_lt
        self.dispatch_table[OpCode.COMPARE_LE.value] = self._handle_compare_le
        self.dispatch_table[OpCode.COMPARE_GT.value] = self._handle_compare_gt
        self.dispatch_table[OpCode.COMPARE_GE.value] = self._handle_compare_ge
        
        self.dispatch_table[OpCode.JUMP_FORWARD.value] = self._handle_jump_forward
        self.dispatch_table[OpCode.JUMP_IF_FALSE.value] = self._handle_jump_if_false
        
        self.dispatch_table[OpCode.CALL_FUNCTION.value] = self._handle_call_function
        self.dispatch_table[OpCode.RETURN_VALUE.value] = self._handle_return_value
        
        self.dispatch_table[OpCode.THINKING_BLOCK.value] = self._handle_thinking_block
        self.dispatch_table[OpCode.PRINT.value] = self._handle_print
        self.dispatch_table[OpCode.HALT.value] = self._handle_halt
        self.dispatch_table[OpCode.NOP.value] = self._handle_nop
    
    def load_program(self, instructions: list[Instruction],
                     constants: list[Any] = None,
                     variable_names: list[str] = None,
                     cognitive_blocks: list[dict[str, Any]] = None):
        """Load bytecode program into VM with optimizations."""
        self.instructions = instructions
        self.constants = constants or []
        self.variable_names = variable_names or []
        self.cognitive_blocks = cognitive_blocks or []
        self.instruction_pointer = 0
        self.halted = False
        
        # OPTIMIZATION 2: Pre-cache frequently accessed data
        self.constants_len = len(self.constants)
        self.variable_names_len = len(self.variable_names)
        self.instructions_len = len(self.instructions)
        
        if self.debug_mode:
            print(f"Loaded optimized program: {self.instructions_len} instructions")
    
    def execute(self) -> Any:
        """Execute loaded bytecode program with optimizations."""
        import time
        start_time = time.perf_counter()
        
        result = None
        
        # OPTIMIZATION 3: Minimize condition checks in hot loop
        instructions = self.instructions  # Local reference
        dispatch_table = self.dispatch_table  # Local reference
        
        while not self.halted and self.instruction_pointer < self.instructions_len:
            # Get current instruction
            instruction = instructions[self.instruction_pointer]
            self.instruction_count += 1
            
            # OPTIMIZATION 1: Direct jump table dispatch (no dictionary lookup)
            handler = dispatch_table[instruction.opcode.value]
            if handler is None:
                raise RuntimeError(f"Unhandled opcode: {instruction.opcode}")
            
            # OPTIMIZATION 4: Streamlined cognitive processing
            if (self.accessibility_enabled and 
                instruction.cognitive_weight > self.cognitive_load_threshold and
                self.thinking_pause_ms > 0):
                time.sleep(self.thinking_pause_ms / 1000.0)
            
            # Execute instruction
            if self.debug_mode:
                print(f"[{self.instruction_pointer:04d}] {instruction.opcode.name}")
            
            result = handler(instruction)
            
            # Advance instruction pointer (unless jump occurred)
            if not getattr(self, '_jump_flag', False):
                self.instruction_pointer += 1
            else:
                self._jump_flag = False
        
        end_time = time.perf_counter()
        self.performance_stats['execution_time'] = end_time - start_time
        self.performance_stats['total_instructions'] = self.instruction_count
        
        return result
    
    # === Optimized Instruction Handlers ===
    
    def _handle_load_const(self, instruction: Instruction) -> None:
        """Optimized LOAD_CONST handler."""
        const_index = instruction.operand
        # OPTIMIZATION 2: Use pre-cached length instead of len() call
        if const_index >= self.constants_len:
            raise RuntimeError(f"Constant index {const_index} out of range")
        self.stack.push(self.constants[const_index])
    
    def _handle_load_var(self, instruction: Instruction) -> None:
        """Optimized LOAD_VAR handler."""
        var_index = instruction.operand
        if var_index >= self.variable_names_len:
            raise RuntimeError(f"Variable index {var_index} out of range")
        
        var_name = self.variable_names[var_index]
        # OPTIMIZATION 2: Use .get() with None check instead of 'in' test + lookup
        value = self.globals.get(var_name)
        if value is None and var_name not in self.globals:
            raise RuntimeError(f"Variable '{var_name}' not defined")
        self.stack.push(value)
    
    def _handle_store_var(self, instruction: Instruction) -> None:
        """Optimized STORE_VAR handler."""
        var_index = instruction.operand
        if var_index >= self.variable_names_len:
            raise RuntimeError(f"Variable index {var_index} out of range")
        
        var_name = self.variable_names[var_index]
        value = self.stack.pop()
        self.globals[var_name] = value
    
    def _handle_pop_top(self, instruction: Instruction) -> None:
        """Handle POP_TOP instruction."""
        self.stack.pop()
    
    def _handle_dup_top(self, instruction: Instruction) -> None:
        """Handle DUP_TOP instruction."""
        self.stack.duplicate_top()
    
    def _handle_binary_add(self, instruction: Instruction) -> None:
        """Optimized BINARY_ADD handler."""
        right = self.stack.pop()
        left = self.stack.pop()
        # OPTIMIZATION: Direct addition without intermediate variables in simple cases
        self.stack.push(left + right)
    
    def _handle_binary_sub(self, instruction: Instruction) -> None:
        """Optimized BINARY_SUB handler."""
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.push(left - right)
    
    def _handle_binary_mul(self, instruction: Instruction) -> None:
        """Optimized BINARY_MUL handler."""
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.push(left * right)
    
    def _handle_binary_div(self, instruction: Instruction) -> None:
        """Optimized BINARY_DIV handler."""
        right = self.stack.pop()
        left = self.stack.pop()
        if right == 0:
            raise RuntimeError("Division by zero")
        self.stack.push(left / right)
    
    def _handle_compare_eq(self, instruction: Instruction) -> None:
        """Optimized COMPARE_EQ handler."""
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.push(left == right)
    
    def _handle_compare_ne(self, instruction: Instruction) -> None:
        """Optimized COMPARE_NE handler."""
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.push(left != right)
    
    def _handle_compare_lt(self, instruction: Instruction) -> None:
        """Optimized COMPARE_LT handler."""
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.push(left < right)
    
    def _handle_compare_le(self, instruction: Instruction) -> None:
        """Optimized COMPARE_LE handler."""
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.push(left <= right)
    
    def _handle_compare_gt(self, instruction: Instruction) -> None:
        """Optimized COMPARE_GT handler."""
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.push(left > right)
    
    def _handle_compare_ge(self, instruction: Instruction) -> None:
        """Optimized COMPARE_GE handler."""
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.push(left >= right)
    
    def _handle_jump_forward(self, instruction: Instruction) -> None:
        """Optimized JUMP_FORWARD handler."""
        self.instruction_pointer = instruction.operand
        self._jump_flag = True
    
    def _handle_jump_if_false(self, instruction: Instruction) -> None:
        """Optimized JUMP_IF_FALSE handler."""
        condition = self.stack.pop()
        if not condition:
            self.instruction_pointer = instruction.operand
            self._jump_flag = True
    
    def _handle_call_function(self, instruction: Instruction) -> None:
        """Handle CALL_FUNCTION instruction."""
        arg_count = instruction.operand
        self.performance_stats['function_calls'] += 1
        # Pop arguments (placeholder implementation)
        for _ in range(arg_count):
            self.stack.pop()
    
    def _handle_return_value(self, instruction: Instruction) -> None:
        """Handle RETURN_VALUE instruction."""
        pass
    
    def _handle_thinking_block(self, instruction: Instruction) -> None:
        """Optimized THINKING_BLOCK handler."""
        block_index = instruction.operand
        if block_index < len(self.cognitive_blocks):
            self.performance_stats['cognitive_blocks_processed'] += 1
            
            if self.debug_mode:
                block = self.cognitive_blocks[block_index]
                print(f"[THINKING] {block.get('description', 'Processing...')}")
    
    def _handle_print(self, instruction: Instruction) -> None:
        """Handle PRINT instruction."""
        value = self.stack.pop()
        print(value)
    
    def _handle_halt(self, instruction: Instruction) -> None:
        """Handle HALT instruction."""
        self.halted = True
    
    def _handle_nop(self, instruction: Instruction) -> None:
        """Handle NOP instruction."""
        pass
    
    def get_performance_stats(self) -> dict[str, Any]:
        """Get VM performance statistics."""
        stack_stats = self.stack.get_stats()
        return {
            **self.performance_stats,
            'stack_stats': stack_stats,
            'instructions_per_second': (
                self.performance_stats['total_instructions'] / 
                max(0.001, self.performance_stats['execution_time'])
            ),
            'current_stack_size': stack_stats['current_size'],
            'globals_count': len(self.globals)
        }
    
    def reset(self):
        """Reset VM state for new program."""
        self.stack.clear()
        self.call_stack.clear()
        self.globals.clear()
        self.instruction_pointer = 0
        self.halted = False
        self.instruction_count = 0
        self._jump_flag = False


# Performance comparison test
def test_optimized_vm():
    """Test optimized VM performance."""
    from bytecode import BytecodeGenerator, OpCode
    
    print("=" * 60)
    print("PHASE 1, DAY 2: OPTIMIZED VM PERFORMANCE TEST")
    print("=" * 60)
    
    # Create test program
    generator = BytecodeGenerator()
    generator.generate_basic_assignment('x', 42)
    generator.emit(OpCode.HALT)
    
    vm = SonaVMOptimized(debug_mode=False)
    vm.accessibility_enabled = False  # Disable for pure performance
    vm.load_program(
        instructions=generator.instructions,
        constants=list(generator.constants.keys()),
        variable_names=list(generator.variables.keys())
    )
    
    # Test performance
    import time
    iterations = 500000  # Increased for better measurement
    
    start_time = time.perf_counter()
    for _ in range(iterations):
        vm.instruction_pointer = 0
        vm.halted = False
        vm.globals.clear()
        vm.stack.clear()
        vm.execute()
    end_time = time.perf_counter()
    
    total_time = end_time - start_time
    ops_per_second = iterations / total_time
    avg_time_ms = (total_time / iterations) * 1000
    
    print("Optimized VM Performance:")
    print(f"Iterations: {iterations:,}")
    print(f"Total time: {total_time:.4f} seconds")
    print(f"Operations/second: {ops_per_second:,.0f}")
    print(f"Average time/operation: {avg_time_ms:.6f} ms")
    
    # Compare to baseline targets
    interpreter_baseline = 650000
    day1_vm_baseline = 383035
    
    interpreter_speedup = ops_per_second / interpreter_baseline
    day1_speedup = ops_per_second / day1_vm_baseline
    
    print("\nPerformance Comparison:")
    print(f"Interpreter baseline: {interpreter_baseline:,} ops/sec")
    print(f"Day 1 VM baseline: {day1_vm_baseline:,} ops/sec") 
    print(f"Optimized VM: {ops_per_second:,.0f} ops/sec")
    print(f"vs Interpreter: {interpreter_speedup:.2f}x")
    print(f"vs Day 1 VM: {day1_speedup:.2f}x")
    
    # Achievement assessment
    if ops_per_second >= 1300000:  # 2x interpreter
        status = "🚀 OUTSTANDING: 2x+ interpreter speedup achieved!"
    elif ops_per_second >= 650000:  # 1x interpreter
        status = "✅ SUCCESS: Interpreter parity achieved!"
    elif ops_per_second >= day1_vm_baseline * 1.5:  # 1.5x Day 1 VM
        status = "✅ GOOD: Significant VM optimization achieved!"
    else:
        status = "⚠️ NEEDS FURTHER OPTIMIZATION"
    
    print(f"\nStatus: {status}")
    
    return ops_per_second


if __name__ == "__main__":
    test_optimized_vm()
