"""
Sona Virtual Machine Core Implementation
Phase 1, Day 1: Bytecode Execution Engine

High-performance VM for executing Sona bytecode with cognitive accessibility
features. Target: 10-50x performance improvement over interpreter.
"""

from typing import Any, Dict, List
from collections.abc import Callable


try:
    from .bytecode import Instruction, OpCode
    from .stack import CallStack, VMStack
except ImportError:
    # For direct testing
    from bytecode import Instruction, OpCode
    from stack import CallStack, VMStack


class SonaVM:
    """
    Sona Virtual Machine for bytecode execution.
    
    Implements cognitive-aware execution with performance optimizations
    and accessibility features for neurodivergent developers.
    """
    
    def __init__(self, debug_mode: bool = False):
        """Initialize the Sona VM."""
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
        
        # Cognitive accessibility
        self.accessibility_enabled = True
        self.cognitive_load_threshold = 0.8
        self.thinking_pause_ms = 50  # Pause for cognitive processing
        
        # Initialize instruction handlers
        self._init_instruction_handlers()
    
    def _init_instruction_handlers(self):
        """Initialize instruction handler dispatch table."""
        self.handlers: dict[OpCode, Callable] = {
            OpCode.LOAD_CONST: self._handle_load_const,
            OpCode.LOAD_VAR: self._handle_load_var,
            OpCode.STORE_VAR: self._handle_store_var,
            OpCode.POP_TOP: self._handle_pop_top,
            OpCode.DUP_TOP: self._handle_dup_top,
            
            OpCode.BINARY_ADD: self._handle_binary_add,
            OpCode.BINARY_SUB: self._handle_binary_sub,
            OpCode.BINARY_MUL: self._handle_binary_mul,
            OpCode.BINARY_DIV: self._handle_binary_div,
            
            OpCode.COMPARE_EQ: self._handle_compare_eq,
            OpCode.COMPARE_NE: self._handle_compare_ne,
            OpCode.COMPARE_LT: self._handle_compare_lt,
            OpCode.COMPARE_LE: self._handle_compare_le,
            OpCode.COMPARE_GT: self._handle_compare_gt,
            OpCode.COMPARE_GE: self._handle_compare_ge,
            
            OpCode.JUMP_FORWARD: self._handle_jump_forward,
            OpCode.JUMP_IF_FALSE: self._handle_jump_if_false,
            
            OpCode.CALL_FUNCTION: self._handle_call_function,
            OpCode.RETURN_VALUE: self._handle_return_value,
            
            OpCode.THINKING_BLOCK: self._handle_thinking_block,
            OpCode.PRINT: self._handle_print,
            OpCode.HALT: self._handle_halt,
            OpCode.NOP: self._handle_nop,
        }
    
    def load_program(self, instructions: list[Instruction], 
                    constants: list[Any] = None,
                    variable_names: list[str] = None,
                    cognitive_blocks: list[dict[str, Any]] = None):
        """Load bytecode program into VM."""
        self.instructions = instructions
        self.constants = constants or []
        self.variable_names = variable_names or []
        self.cognitive_blocks = cognitive_blocks or []
        self.instruction_pointer = 0
        self.halted = False
        
        if self.debug_mode:
            print(f"Loaded program: {len(instructions)} instructions")
    
    def execute(self) -> Any:
        """Execute loaded bytecode program."""
        import time
        start_time = time.perf_counter()
        
        result = None
        while not self.halted and self.instruction_pointer < len(self.instructions):
            result = self._execute_instruction()
        
        end_time = time.perf_counter()
        self.performance_stats['execution_time'] = end_time - start_time
        self.performance_stats['total_instructions'] = self.instruction_count
        
        return result
    
    def _execute_instruction(self) -> Any:
        """Execute single instruction."""
        if self.instruction_pointer >= len(self.instructions):
            self.halted = True
            return None
            
        instruction = self.instructions[self.instruction_pointer]
        self.instruction_count += 1
        
        if self.debug_mode:
            print(f"[{self.instruction_pointer:04d}] {instruction.opcode.name} "
                  f"{instruction.operand if instruction.operand is not None else ''}")
        
        # Handle cognitive accessibility
        if (self.accessibility_enabled and 
            instruction.cognitive_weight > self.cognitive_load_threshold):
            self._handle_cognitive_load(instruction)
        
        # Execute instruction
        handler = self.handlers.get(instruction.opcode)
        if handler is None:
            raise RuntimeError(f"Unhandled opcode: {instruction.opcode}")
        
        result = handler(instruction)
        
        # Advance instruction pointer (unless jump occurred)
        if not self._jump_occurred():
            self.instruction_pointer += 1
            
        return result
    
    def _jump_occurred(self) -> bool:
        """Check if the last instruction was a jump that modified IP."""
        # This is set by jump handlers
        return getattr(self, '_jump_flag', False)
    
    def _handle_cognitive_load(self, instruction: Instruction):
        """Handle high cognitive load instruction with accessibility pause."""
        if self.thinking_pause_ms > 0:
            import time
            time.sleep(self.thinking_pause_ms / 1000.0)
    
    # === Instruction Handlers ===
    
    def _handle_load_const(self, instruction: Instruction) -> None:
        """Handle LOAD_CONST instruction."""
        const_index = instruction.operand
        if const_index >= len(self.constants):
            raise RuntimeError(f"Constant index {const_index} out of range")
        value = self.constants[const_index]
        self.stack.push(value)
    
    def _handle_load_var(self, instruction: Instruction) -> None:
        """Handle LOAD_VAR instruction."""
        var_index = instruction.operand
        if var_index >= len(self.variable_names):
            raise RuntimeError(f"Variable index {var_index} out of range")
        
        var_name = self.variable_names[var_index]
        if var_name not in self.globals:
            raise RuntimeError(f"Variable '{var_name}' not defined")
        
        value = self.globals[var_name]
        self.stack.push(value)
    
    def _handle_store_var(self, instruction: Instruction) -> None:
        """Handle STORE_VAR instruction."""
        var_index = instruction.operand
        if var_index >= len(self.variable_names):
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
        """Handle BINARY_ADD instruction."""
        right = self.stack.pop()
        left = self.stack.pop()
        result = left + right
        self.stack.push(result)
    
    def _handle_binary_sub(self, instruction: Instruction) -> None:
        """Handle BINARY_SUB instruction."""
        right = self.stack.pop()
        left = self.stack.pop()
        result = left - right
        self.stack.push(result)
    
    def _handle_binary_mul(self, instruction: Instruction) -> None:
        """Handle BINARY_MUL instruction."""
        right = self.stack.pop()
        left = self.stack.pop()
        result = left * right
        self.stack.push(result)
    
    def _handle_binary_div(self, instruction: Instruction) -> None:
        """Handle BINARY_DIV instruction."""
        right = self.stack.pop()
        left = self.stack.pop()
        if right == 0:
            raise RuntimeError("Division by zero")
        result = left / right
        self.stack.push(result)
    
    def _handle_compare_eq(self, instruction: Instruction) -> None:
        """Handle COMPARE_EQ instruction."""
        right = self.stack.pop()
        left = self.stack.pop()
        result = left == right
        self.stack.push(result)
    
    def _handle_compare_ne(self, instruction: Instruction) -> None:
        """Handle COMPARE_NE instruction."""
        right = self.stack.pop()
        left = self.stack.pop()
        result = left != right
        self.stack.push(result)
    
    def _handle_compare_lt(self, instruction: Instruction) -> None:
        """Handle COMPARE_LT instruction."""
        right = self.stack.pop()
        left = self.stack.pop()
        result = left < right
        self.stack.push(result)
    
    def _handle_compare_le(self, instruction: Instruction) -> None:
        """Handle COMPARE_LE instruction."""
        right = self.stack.pop()
        left = self.stack.pop()
        result = left <= right
        self.stack.push(result)
    
    def _handle_compare_gt(self, instruction: Instruction) -> None:
        """Handle COMPARE_GT instruction."""
        right = self.stack.pop()
        left = self.stack.pop()
        result = left > right
        self.stack.push(result)
    
    def _handle_compare_ge(self, instruction: Instruction) -> None:
        """Handle COMPARE_GE instruction."""
        right = self.stack.pop()
        left = self.stack.pop()
        result = left >= right
        self.stack.push(result)
    
    def _handle_jump_forward(self, instruction: Instruction) -> None:
        """Handle JUMP_FORWARD instruction."""
        target = instruction.operand
        self.instruction_pointer = target
        self._jump_flag = True
    
    def _handle_jump_if_false(self, instruction: Instruction) -> None:
        """Handle JUMP_IF_FALSE instruction."""
        condition = self.stack.pop()
        if not condition:
            target = instruction.operand
            self.instruction_pointer = target
            self._jump_flag = True
        else:
            self._jump_flag = False
    
    def _handle_call_function(self, instruction: Instruction) -> None:
        """Handle CALL_FUNCTION instruction."""
        arg_count = instruction.operand
        self.performance_stats['function_calls'] += 1
        # Function call implementation would go here
        # For now, just pop arguments
        for _ in range(arg_count):
            self.stack.pop()
    
    def _handle_return_value(self, instruction: Instruction) -> None:
        """Handle RETURN_VALUE instruction."""
        # Return value implementation
        pass
    
    def _handle_thinking_block(self, instruction: Instruction) -> None:
        """Handle THINKING_BLOCK instruction for cognitive accessibility."""
        block_index = instruction.operand
        if block_index < len(self.cognitive_blocks):
            block = self.cognitive_blocks[block_index]
            self.performance_stats['cognitive_blocks_processed'] += 1
            
            if self.debug_mode:
                print(f"[THINKING] {block.get('description', 'Processing...')}")
    
    def _handle_print(self, instruction: Instruction) -> None:
        """Handle PRINT instruction."""
        value = self.stack.pop()
        print(value)
    
    def _handle_halt(self, instruction: Instruction) -> None:
        """Handle HALT instruction."""
        self.halted = True
    
    def _handle_nop(self, instruction: Instruction) -> None:
        """Handle NOP (no operation) instruction."""
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


# Test VM execution
def test_vm_execution():
    """Test basic VM execution with bytecode."""
    from bytecode import BytecodeGenerator, OpCode
    
    # Create test program: let x = 42; print(x)
    generator = BytecodeGenerator()
    generator.generate_basic_assignment('x', 42)
    generator.generate_print_statement(var_name='x')
    generator.emit(OpCode.HALT)
    
    # Create and run VM
    vm = SonaVM(debug_mode=True)
    vm.load_program(
        instructions=generator.instructions,
        constants=list(generator.constants.keys()),
        variable_names=list(generator.variables.keys()),
        cognitive_blocks=generator.cognitive_blocks
    )
    
    print("Executing VM program:")
    result = vm.execute()
    
    print(f"\nExecution complete. Result: {result}")
    print(f"Performance stats: {vm.get_performance_stats()}")
    
    return vm


if __name__ == "__main__":
    test_vm_execution()
