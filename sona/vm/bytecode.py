"""
Sona Bytecode Instruction Set and Generator
Phase 1, Day 1: Core VM Foundation

Implements cognitive-aware bytecode compilation with accessibility features.
Target: 10-50x performance improvement over current interpreter baseline.
"""

import struct
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union


class OpCode(Enum):
    """Bytecode operation codes optimized for cognitive accessibility."""
    
    # === Stack Operations ===
    LOAD_CONST = auto()       # Load constant onto stack
    LOAD_VAR = auto()         # Load variable value onto stack
    STORE_VAR = auto()        # Store top of stack to variable
    POP_TOP = auto()          # Pop and discard top of stack
    DUP_TOP = auto()          # Duplicate top of stack
    
    # === Arithmetic Operations ===
    BINARY_ADD = auto()       # Add two values (a + b)
    BINARY_SUB = auto()       # Subtract two values (a - b)
    BINARY_MUL = auto()       # Multiply two values (a * b)
    BINARY_DIV = auto()       # Divide two values (a / b)
    BINARY_MOD = auto()       # Modulo operation (a % b)
    
    # === Comparison Operations ===
    COMPARE_EQ = auto()       # Equal comparison (a == b)
    COMPARE_NE = auto()       # Not equal comparison (a != b)
    COMPARE_LT = auto()       # Less than comparison (a < b)
    COMPARE_LE = auto()       # Less than or equal (a <= b)
    COMPARE_GT = auto()       # Greater than comparison (a > b)
    COMPARE_GE = auto()       # Greater than or equal (a >= b)
    
    # === Control Flow ===
    JUMP_FORWARD = auto()     # Unconditional jump forward
    JUMP_BACKWARD = auto()    # Unconditional jump backward
    JUMP_IF_FALSE = auto()    # Jump if top of stack is false
    JUMP_IF_TRUE = auto()     # Jump if top of stack is true
    
    # === Function Operations ===
    CALL_FUNCTION = auto()    # Call function with N arguments
    RETURN_VALUE = auto()     # Return value from function
    LOAD_FUNCTION = auto()    # Load function object
    
    # === Cognitive Accessibility Features ===
    THINKING_BLOCK = auto()   # Mark thinking block for accessibility
    REMEMBER_VAR = auto()     # Add variable to working memory
    FOCUS_ENTER = auto()      # Enter focused cognitive state
    FOCUS_EXIT = auto()       # Exit focused cognitive state
    
    # === I/O Operations ===
    PRINT = auto()           # Print value from stack
    INPUT = auto()           # Get input from user
    
    # === Program Flow ===
    NOP = auto()             # No operation
    HALT = auto()            # Halt program execution


@dataclass
class Instruction:
    """Single bytecode instruction with operand."""
    opcode: OpCode
    operand: int | str | float | None = None
    line_number: int = 0
    cognitive_weight: float = 1.0  # For cognitive load balancing
    
    def serialize(self) -> bytes:
        """Serialize instruction to bytecode."""
        # Pack opcode as short (2 bytes)
        result = struct.pack('<H', self.opcode.value)
        
        # Pack operand based on type
        if self.operand is None:
            result += struct.pack('<B', 0)  # No operand marker
        elif isinstance(self.operand, int):
            result += struct.pack('<Bi', 1, self.operand)  # Int operand
        elif isinstance(self.operand, float):
            result += struct.pack('<Bf', 2, self.operand)  # Float operand
        elif isinstance(self.operand, str):
            encoded = self.operand.encode('utf-8')
            result += struct.pack('<BH', 3, len(encoded)) + encoded  # String operand
        
        return result
    
    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple['Instruction', int]:
        """Deserialize bytecode to instruction."""
        opcode_val, = struct.unpack_from('<H', data, offset)
        opcode = OpCode(opcode_val)
        offset += 2
        
        operand_type, = struct.unpack_from('<B', data, offset)
        offset += 1
        
        operand = None
        if operand_type == 1:  # Int
            operand, = struct.unpack_from('<i', data, offset)
            offset += 4
        elif operand_type == 2:  # Float
            operand, = struct.unpack_from('<f', data, offset)
            offset += 4
        elif operand_type == 3:  # String
            str_len, = struct.unpack_from('<H', data, offset)
            offset += 2
            operand = data[offset:offset+str_len].decode('utf-8')
            offset += str_len
        
        return cls(opcode, operand), offset


class BytecodeGenerator:
    """Generates optimized bytecode from Sona AST with cognitive features."""
    
    def __init__(self):
        self.instructions: list[Instruction] = []
        self.constants: dict[Any, int] = {}
        self.variables: dict[str, int] = {}
        self.cognitive_blocks: list[dict[str, Any]] = []
        self.current_line = 1
        
    def emit(self, opcode: OpCode, operand: Any = None, cognitive_weight: float = 1.0) -> int:
        """Emit a bytecode instruction."""
        instruction = Instruction(
            opcode=opcode,
            operand=operand,
            line_number=self.current_line,
            cognitive_weight=cognitive_weight
        )
        self.instructions.append(instruction)
        return len(self.instructions) - 1  # Return instruction index
    
    def emit_load_const(self, value: Any) -> int:
        """Emit instruction to load constant."""
        if value not in self.constants:
            self.constants[value] = len(self.constants)
        const_index = self.constants[value]
        return self.emit(OpCode.LOAD_CONST, const_index)
    
    def emit_load_var(self, name: str) -> int:
        """Emit instruction to load variable."""
        if name not in self.variables:
            self.variables[name] = len(self.variables)
        var_index = self.variables[name]
        return self.emit(OpCode.LOAD_VAR, var_index)
    
    def emit_store_var(self, name: str) -> int:
        """Emit instruction to store variable."""
        if name not in self.variables:
            self.variables[name] = len(self.variables)
        var_index = self.variables[name]
        return self.emit(OpCode.STORE_VAR, var_index)
    
    def emit_binary_op(self, operator: str) -> int:
        """Emit binary operation instruction."""
        op_map = {
            '+': OpCode.BINARY_ADD,
            '-': OpCode.BINARY_SUB,
            '*': OpCode.BINARY_MUL,
            '/': OpCode.BINARY_DIV,
            '%': OpCode.BINARY_MOD,
            '==': OpCode.COMPARE_EQ,
            '!=': OpCode.COMPARE_NE,
            '<': OpCode.COMPARE_LT,
            '<=': OpCode.COMPARE_LE,
            '>': OpCode.COMPARE_GT,
            '>=': OpCode.COMPARE_GE,
        }
        opcode = op_map.get(operator)
        if opcode is None:
            raise ValueError(f"Unsupported binary operator: {operator}")
        return self.emit(opcode)
    
    def emit_jump(self, opcode: OpCode, target: int | None = None) -> int:
        """Emit jump instruction."""
        return self.emit(opcode, target)
    
    def emit_call_function(self, arg_count: int) -> int:
        """Emit function call instruction."""
        return self.emit(OpCode.CALL_FUNCTION, arg_count)
    
    def emit_thinking_block(self, description: str, cognitive_load: str = "medium") -> int:
        """Emit cognitive thinking block marker."""
        block_data = {
            'description': description,
            'cognitive_load': cognitive_load,
            'line': self.current_line
        }
        self.cognitive_blocks.append(block_data)
        return self.emit(OpCode.THINKING_BLOCK, len(self.cognitive_blocks) - 1, 
                        cognitive_weight=2.0 if cognitive_load == "high" else 1.0)
    
    def patch_jump(self, instruction_index: int, target: int):
        """Patch jump instruction with target address."""
        self.instructions[instruction_index].operand = target
    
    def get_instruction_count(self) -> int:
        """Get current instruction count."""
        return len(self.instructions)
    
    def generate_basic_assignment(self, var_name: str, value: Any) -> list[int]:
        """Generate bytecode for basic variable assignment."""
        instructions = []
        instructions.append(self.emit_load_const(value))
        instructions.append(self.emit_store_var(var_name))
        return instructions
    
    def generate_print_statement(self, var_name: str | None = None, 
                                value: Any | None = None) -> list[int]:
        """Generate bytecode for print statement."""
        instructions = []
        if var_name:
            instructions.append(self.emit_load_var(var_name))
        elif value is not None:
            instructions.append(self.emit_load_const(value))
        instructions.append(self.emit(OpCode.PRINT))
        return instructions
    
    def serialize_program(self) -> bytes:
        """Serialize complete bytecode program."""
        result = b''
        
        # Serialize constants table
        result += struct.pack('<H', len(self.constants))
        const_values = [None] * len(self.constants)
        for value, index in self.constants.items():
            const_values[index] = value
            
        for value in const_values:
            if isinstance(value, int):
                result += struct.pack('<Bi', 1, value)
            elif isinstance(value, float):
                result += struct.pack('<Bf', 2, value)
            elif isinstance(value, str):
                encoded = value.encode('utf-8')
                result += struct.pack('<BH', 3, len(encoded)) + encoded
            else:
                # Default to string representation
                encoded = str(value).encode('utf-8')
                result += struct.pack('<BH', 3, len(encoded)) + encoded
        
        # Serialize variable names
        result += struct.pack('<H', len(self.variables))
        var_names = [None] * len(self.variables)
        for name, index in self.variables.items():
            var_names[index] = name
            
        for name in var_names:
            encoded = name.encode('utf-8')
            result += struct.pack('<H', len(encoded)) + encoded
        
        # Serialize cognitive blocks
        result += struct.pack('<H', len(self.cognitive_blocks))
        for block in self.cognitive_blocks:
            desc_encoded = block['description'].encode('utf-8')
            load_encoded = block['cognitive_load'].encode('utf-8')
            result += struct.pack('<HHH', len(desc_encoded), len(load_encoded), block['line'])
            result += desc_encoded + load_encoded
        
        # Serialize instructions
        result += struct.pack('<I', len(self.instructions))
        for instruction in self.instructions:
            result += instruction.serialize()
        
        return result
    
    def get_stats(self) -> dict[str, int]:
        """Get bytecode generation statistics."""
        return {
            'instructions': len(self.instructions),
            'constants': len(self.constants),
            'variables': len(self.variables),
            'cognitive_blocks': len(self.cognitive_blocks),
            'estimated_size_bytes': len(self.serialize_program())
        }


# Quick test functions for development
def test_bytecode_generation():
    """Test basic bytecode generation."""
    generator = BytecodeGenerator()
    
    # Test: let x = 42
    generator.generate_basic_assignment('x', 42)
    
    # Test: print(x)
    generator.generate_print_statement(var_name='x')
    
    # Test: thinking block
    generator.emit_thinking_block("Setting up variables", "low")
    
    stats = generator.get_stats()
    print(f"Generated bytecode stats: {stats}")
    
    # Test serialization
    serialized = generator.serialize_program()
    print(f"Serialized program size: {len(serialized)} bytes")
    
    return generator


if __name__ == "__main__":
    test_bytecode_generation()
