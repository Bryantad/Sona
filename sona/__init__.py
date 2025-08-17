"""
Sona Programming Language
A cognitive programming language with AI assistance
"""

from .interpreter import (
    SonaUnifiedInterpreter,
    default_interpreter,
    SonaFunction,
    SonaMemoryManager,
    SonaRuntimeError,
    SonaInterpreter
)

__version__ = "0.9.0"
__author__ = "Sona Development Team"

# Export main classes
__all__ = [
    'SonaUnifiedInterpreter',
    'SonaFunction',
    'SonaMemoryManager',
    'SonaRuntimeError',
    'default_interpreter',
    'SonaInterpreter'
]
