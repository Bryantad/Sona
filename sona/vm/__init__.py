"""
Sona Virtual Machine (VM) Implementation
Phase 1: Bytecode Compilation and Execution

This module implements the core VM infrastructure for Sona language
performance optimization, targeting 10-50x improvement over interpreter.
"""

from .bytecode import BytecodeGenerator, Instruction, OpCode
from .stack import VMStack
from .vm import SonaVM


__all__ = [
    'Instruction',
    'OpCode', 
    'BytecodeGenerator',
    'SonaVM',
    'VMStack'
]
