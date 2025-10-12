"""
Sona Language Type System - Minimal Types Module

This module provides basic type definitions for Sona v0.9.4.
Simplified to support runtime type checking.

Author: Sona Development Team  
Version: 0.9.4
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union


class TypeKind(Enum):
    """Type classification for the type system"""

    PRIMITIVE = "primitive"
    COMPOUND = "compound"
    VARIABLE = "variable"
    FUNCTION = "function"
    GENERIC = "generic"


@dataclass
class SourceLocation:
    """Source code location for error reporting"""
    
    line: int
    column: int
    file: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"


class Type(ABC):
    """Abstract base class for all types in the Sona type system"""

    def __init__(self, location: Optional[SourceLocation] = None):
        self.location = location
        self._hash = None

    @abstractmethod
    def kind(self) -> TypeKind:
        """Return the kind of this type"""
        pass

    @abstractmethod
    def __str__(self) -> str:
        """String representation of the type"""
        pass

    @abstractmethod
    def substitute(self, mapping: Dict[str, 'Type']) -> 'Type':
        """Apply type variable substitution"""
        pass

    def __eq__(self, other) -> bool:
        if not isinstance(other, Type):
            return False
        return str(self) == str(other)

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash(str(self))
        return self._hash


class PrimitiveType(Type):
    """Primitive types: int, float, string, bool, unit"""

    def __init__(self, name: str, location: Optional[SourceLocation] = None):
        super().__init__(location)
        self.name = name

    def kind(self) -> TypeKind:
        return TypeKind.PRIMITIVE

    def __str__(self) -> str:
        return self.name

    def substitute(self, mapping: Dict[str, Type]) -> Type:
        return self  # Primitives don't contain variables


class TypeVariable(Type):
    """Type variable for generic types"""

    def __init__(self, name: str, location: Optional[SourceLocation] = None):
        super().__init__(location)
        self.name = name

    def kind(self) -> TypeKind:
        return TypeKind.VARIABLE

    def __str__(self) -> str:
        return f"'{self.name}"

    def substitute(self, mapping: Dict[str, Type]) -> Type:
        return mapping.get(self.name, self)


class FunctionType(Type):
    """Function type with parameter and return types"""

    def __init__(self, param_types: List[Type], return_type: Type,
                 location: Optional[SourceLocation] = None):
        super().__init__(location)
        self.param_types = param_types
        self.return_type = return_type

    def kind(self) -> TypeKind:
        return TypeKind.FUNCTION

    def __str__(self) -> str:
        if len(self.param_types) == 1:
            params = str(self.param_types[0])
        else:
            params = f"({', '.join(str(t) for t in self.param_types)})"
        return f"{params} -> {self.return_type}"

    def substitute(self, mapping: Dict[str, Type]) -> Type:
        new_params = [t.substitute(mapping) for t in self.param_types]
        new_return = self.return_type.substitute(mapping)
        return FunctionType(new_params, new_return, self.location)


class GenericType(Type):
    """Generic type with type parameters"""

    def __init__(self, name: str, args: List[Type],
                 location: Optional[SourceLocation] = None):
        super().__init__(location)
        self.name = name
        self.args = args

    def kind(self) -> TypeKind:
        return TypeKind.GENERIC

    def __str__(self) -> str:
        if self.args:
            args_str = ", ".join(str(arg) for arg in self.args)
            return f"{self.name}[{args_str}]"
        return self.name

    def substitute(self, mapping: Dict[str, Type]) -> Type:
        new_args = [arg.substitute(mapping) for arg in self.args]
        return GenericType(self.name, new_args, self.location)


class TupleType(Type):
    """Tuple type with element types"""

    def __init__(self, element_types: List[Type],
                 location: Optional[SourceLocation] = None):
        super().__init__(location)
        self.element_types = element_types

    def kind(self) -> TypeKind:
        return TypeKind.COMPOUND

    def __str__(self) -> str:
        elements = ", ".join(str(t) for t in self.element_types)
        return f"({elements})"

    def substitute(self, mapping: Dict[str, Type]) -> Type:
        new_elements = [t.substitute(mapping) for t in self.element_types]
        return TupleType(new_elements, self.location)


class RecordType(Type):
    """Record type with named fields"""

    def __init__(self, fields: Dict[str, Type],
                 location: Optional[SourceLocation] = None):
        super().__init__(location)
        self.fields = fields

    def kind(self) -> TypeKind:
        return TypeKind.COMPOUND

    def __str__(self) -> str:
        field_strs = [f"{name}: {type_}" for name, type_ in self.fields.items()]
        return f"{{{', '.join(field_strs)}}}"

    def substitute(self, mapping: Dict[str, Type]) -> Type:
        new_fields = {name: type_.substitute(mapping)
                      for name, type_ in self.fields.items()}
        return RecordType(new_fields, self.location)


class TypeScheme:
    """Type scheme for polymorphic types"""

    def __init__(self, type_vars: List[str], type_: Type):
        self.type_vars = type_vars
        self.type = type_

    def __str__(self) -> str:
        if self.type_vars:
            vars_str = " ".join(self.type_vars)
            return f"∀ {vars_str}. {self.type}"
        return str(self.type)


class TypeEnvironment:
    """Type environment for variable bindings"""

    def __init__(self, parent: Optional['TypeEnvironment'] = None):
        self.parent = parent
        self.bindings: Dict[str, TypeScheme] = {}

    def bind(self, name: str, scheme: TypeScheme):
        """Bind a variable to a type scheme"""
        self.bindings[name] = scheme

    def lookup(self, name: str) -> Optional[TypeScheme]:
        """Look up a variable's type scheme"""
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.lookup(name)
        return None


# Predefined primitive types
INT_TYPE = PrimitiveType("int")
FLOAT_TYPE = PrimitiveType("float")
STRING_TYPE = PrimitiveType("str")
BOOL_TYPE = PrimitiveType("bool")
UNIT_TYPE = PrimitiveType("unit")
