"""
Sona Language Type System - Basic Type Definitions (Simplified)

This module provides a simplified type system for initial Phase 2 implementation.

Author: Sona Development Team
Version: 0.9.0 (Phase 2)
License: See LICENSE file
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Set


class TypeKind(Enum): """Type classification for the type system"""

    PRIMITIVE = "primitive"
    COMPOUND = "compound"
    VARIABLE = "variable"
    FUNCTION = "function"
    GENERIC = "generic"


@dataclass(frozen = True)
class SourceLocation: """Source code location for error reporting"""

    file: str
    line: int
    column: int
    length: int = 1

    def __str__(self) -> str: return f"{self.file}:{self.line}:{self.column}"


class Type(ABC): """Abstract base class for all types in the Sona type system"""

    def __init__(
        self, kind: TypeKind, location: Optional[SourceLocation] = None
    ): self.kind = kind
        self.location = location

    @abstractmethod
    def __str__(self) -> str: """String representation of the type"""
        pass

    def __eq__(self, other) -> bool: if not isinstance(other, Type): return False
        return str(self) == str(other)

    def __hash__(self) -> int: return hash(str(self))


class PrimitiveType(Type): """Primitive types: int, float, string, bool, unit"""

    def __init__(self, name: str, location: Optional[SourceLocation] = (
        None): super().__init__(TypeKind.PRIMITIVE, location)
    )
        self.name = name

    def __str__(self) -> str: return self.name


class TypeVariable(Type): """Type variables for polymorphic types"""

    _counter = 0

    def __init__(
        self,
        name: Optional[str] = None,
        location: Optional[SourceLocation] = None,
    ): super().__init__(TypeKind.VARIABLE, location)
        if name is None: TypeVariable._counter + = 1
            self.name = f"t{TypeVariable._counter}"
        else: self.name = name

    def __str__(self) -> str: return f"'{self.name}"


class FunctionType(Type): """Function types: param_types -> return_type"""

    def __init__(
        self,
        param_types,
        return_type,
        location: Optional[SourceLocation] = None,
    ): super().__init__(TypeKind.FUNCTION, location)
        self.param_types = param_types
        self.return_type = return_type

    def __str__(self) -> str: if len(self.param_types) = (
        = 0: return f"() -> {self.return_type}"
    )
        elif len(self.param_types) = (
            = 1: return f"{self.param_types[0]} -> {self.return_type}"
        )
        else: params = ", ".join(str(t) for t in self.param_types)
            return f"({params}) -> {self.return_type}"


class TypeInferenceError(Exception): """Exception raised during type inference"""

    def __init__(
        self, message: str, location: Optional[SourceLocation] = None
    ): self.message = message
        self.location = location
        super().__init__(message)

    def __str__(self) -> str: if self.location: return f"Type error at {self.location}: {self.message}"
        return f"Type error: {self.message}"


class SimpleTypeChecker: """Simplified type checker for basic Sona expressions"""

    def __init__(self): self.env = {}

    def check_type(self, expr) -> str: """Check the type of an expression and return as string"""
        try: if isinstance(expr, int): return "Int"
            elif isinstance(expr, float): return "Float"
            elif isinstance(expr, str): return "String"
            elif isinstance(expr, bool): return "Bool"
            else: return "Unknown"
        except Exception as e: return f"Type Error: {e}"


# Common type instances
INT_TYPE = PrimitiveType('Int')
FLOAT_TYPE = PrimitiveType('Float')
STRING_TYPE = PrimitiveType('String')
BOOL_TYPE = PrimitiveType('Bool')
UNIT_TYPE = PrimitiveType('Unit')


def check_type(expr) -> str: """Quick type check that returns type as string"""
    checker = SimpleTypeChecker()
    return checker.check_type(expr)


# Export main classes and functions
__all__ = [
    'Type',
    'TypeKind',
    'SourceLocation',
    'PrimitiveType',
    'TypeVariable',
    'FunctionType',
    'TypeInferenceError',
    'SimpleTypeChecker',
    'INT_TYPE',
    'FLOAT_TYPE',
    'STRING_TYPE',
    'BOOL_TYPE',
    'UNIT_TYPE',
    'check_type',
]
