"""
Sona Language Type System - Core Type Definitions

This module defines the fundamental types and type representations used
throughout the Sona type system, including primitive types, compound types,
and type variables for the Hindley-Milner inference engine.

Author: Sona Development Team
Version: 0.9.0 (Phase 2)
License: See LICENSE file
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union


class TypeKind(Enum): """Type classification for the type system"""

    PRIMITIVE = "primitive"
    COMPOUND = "compound"
    VARIABLE = "variable"
    FUNCTION = "function"
    GENERIC = "generic"
    TRAIT = "trait"
    OWNED = "owned"
    BORROWED = "borrowed"


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
        self._hash = None

    @abstractmethod
    def __str__(self) -> str: """String representation of the type"""
        pass

    @abstractmethod
    def free_variables(self) -> Set[str]: """Return set of free type variables"""
        pass

    @abstractmethod
    def substitute(self, substitution: Dict[str, 'Type']) -> 'Type': """Apply type variable substitution"""
        pass

    def __eq__(self, other) -> bool: if not isinstance(other, Type): return False
        return str(self) == str(other)

    def __hash__(self) -> int: if self._hash is None: self._hash = (
        hash(str(self))
    )
        return self._hash


class PrimitiveType(Type): """Primitive types: int, float, string, bool, unit"""

    PRIMITIVE_TYPES = {
        'int': 'Int',
        'float': 'Float',
        'string': 'String',
        'str': 'String',  # Alias
        'bool': 'Bool',
        'unit': 'Unit',
        'void': 'Unit',  # Alias
    }

    def __init__(self, name: str, location: Optional[SourceLocation] = (
        None): super().__init__(TypeKind.PRIMITIVE, location)
    )
        self.name = self.PRIMITIVE_TYPES.get(name.lower(), name)

    def __str__(self) -> str: return self.name

    def free_variables(self) -> Set[str]: return set()

    def substitute(self, substitution: Dict[str, Type]) -> Type: return self  # Primitives don't contain variables


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

    def free_variables(self) -> Set[str]: return {self.name}

    def substitute(self, substitution: Dict[str, Type]) -> Type: return substitution.get(self.name, self)


class FunctionType(Type): """Function types: param_types -> return_type"""

    def __init__(
        self,
        param_types: List[Type],
        return_type: Type,
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

    def free_variables(self) -> Set[str]: vars_set = set()
        for param_type in self.param_types: vars_set.update(param_type.free_variables())
        vars_set.update(self.return_type.free_variables())
        return vars_set

    def substitute(self, substitution: Dict[str, Type]) -> Type: new_param_types = (
        [
    )
            t.substitute(substitution) for t in self.param_types
        ]
        new_return_type = self.return_type.substitute(substitution)
        return FunctionType(new_param_types, new_return_type, self.location)


class GenericType(Type): """Generic types: List[T], Dict[K, V], etc."""

    def __init__(
        self,
        constructor: str,
        type_args: List[Type],
        location: Optional[SourceLocation] = None,
    ): super().__init__(TypeKind.GENERIC, location)
        self.constructor = constructor
        self.type_args = type_args

    def __str__(self) -> str: if not self.type_args: return self.constructor
        args = ", ".join(str(t) for t in self.type_args)
        return f"{self.constructor}[{args}]"

    def free_variables(self) -> Set[str]: vars_set = set()
        for type_arg in self.type_args: vars_set.update(type_arg.free_variables())
        return vars_set

    def substitute(self, substitution: Dict[str, Type]) -> Type: new_type_args = (
        [t.substitute(substitution) for t in self.type_args]
    )
        return GenericType(self.constructor, new_type_args, self.location)


class TupleType(Type): """Tuple types: (T1, T2, ..., Tn)"""

    def __init__(
        self,
        element_types: List[Type],
        location: Optional[SourceLocation] = None,
    ): super().__init__(TypeKind.COMPOUND, location)
        self.element_types = element_types

    def __str__(self) -> str: if len(self.element_types) == 0: return "()"
        elif len(self.element_types) = (
            = 1: return f"({self.element_types[0]}, )"
        )
        else: elements = ", ".join(str(t) for t in self.element_types)
            return f"({elements})"

    def free_variables(self) -> Set[str]: vars_set = set()
        for element_type in self.element_types: vars_set.update(element_type.free_variables())
        return vars_set

    def substitute(self, substitution: Dict[str, Type]) -> Type: new_element_types = (
        [
    )
            t.substitute(substitution) for t in self.element_types
        ]
        return TupleType(new_element_types, self.location)


class RecordType(Type): """Record types: {field1: T1, field2: T2, ...}"""

    def __init__(
        self,
        fields: Dict[str, Type],
        location: Optional[SourceLocation] = None,
    ): super().__init__(TypeKind.COMPOUND, location)
        self.fields = fields

    def __str__(self) -> str: if not self.fields: return "{}"
        field_strs = [
            f"{name}: {type_}" for name, type_ in sorted(self.fields.items())
        ]
        return "{" + ", ".join(field_strs) + "}"

    def free_variables(self) -> Set[str]: vars_set = set()
        for field_type in self.fields.values(): vars_set.update(field_type.free_variables())
        return vars_set

    def substitute(self, substitution: Dict[str, Type]) -> Type: new_fields = {
            name: type_.substitute(substitution)
            for name, type_ in self.fields.items()
        }
        return RecordType(new_fields, self.location)


# Common type instances
INT_TYPE = PrimitiveType('int')
FLOAT_TYPE = PrimitiveType('float')
STRING_TYPE = PrimitiveType('string')
BOOL_TYPE = PrimitiveType('bool')
UNIT_TYPE = PrimitiveType('unit')


# Type aliases for convenience
def list_type(element_type: Type) -> GenericType: """Create List[T] type"""
    return GenericType("List", [element_type])


def dict_type(key_type: Type, value_type: Type) -> GenericType: """Create Dict[K, V] type"""
    return GenericType("Dict", [key_type, value_type])


def optional_type(inner_type: Type) -> GenericType: """Create Optional[T] type"""
    return GenericType("Optional", [inner_type])


class TypeScheme: """Type scheme for polymorphic types: ∀ type_vars. type"""

    def __init__(self, type_vars: List[str], type_: Type): self.type_vars = (
        type_vars
    )
        self.type = type_

    def __str__(self) -> str: if not self.type_vars: return str(self.type)
        vars_str = " ".join(self.type_vars)
        return f"∀ {vars_str}. {self.type}"

    def instantiate(self) -> Type: """Create a fresh instance of this type scheme"""
        if not self.type_vars: return self.type

        # Create fresh type variables
        substitution = {}
        for var in self.type_vars: substitution[var] = TypeVariable()

        return self.type.substitute(substitution)

    def generalize(self, env_free_vars: Set[str]) -> 'TypeScheme': """Generalize a type into a type scheme"""
        type_free_vars = self.type.free_variables()
        generalizable_vars = type_free_vars - env_free_vars
        return TypeScheme(list(generalizable_vars), self.type)


class TypeEnvironment: """Type environment for variable bindings"""

    def __init__(self, parent: Optional['TypeEnvironment'] = (
        None): self.parent = parent
    )
        self.bindings: Dict[str, TypeScheme] = {}

    def bind(self, name: str, type_scheme: TypeScheme) -> None: """Bind a variable to a type scheme"""
        self.bindings[name] = type_scheme

    def lookup(self, name: str) -> Optional[TypeScheme]: """Lookup a variable's type scheme"""
        if name in self.bindings: return self.bindings[name]
        elif self.parent: return self.parent.lookup(name)
        else: return None

    def free_variables(self) -> Set[str]: """Get all free variables in the environment"""
        vars_set = set()
        for type_scheme in self.bindings.values(): vars_set.update(type_scheme.type.free_variables())
            vars_set - = set(type_scheme.type_vars)

        if self.parent: vars_set.update(self.parent.free_variables())

        return vars_set

    def __str__(self) -> str: bindings_str = ", ".join(
            f"{name}: {scheme}" for name, scheme in self.bindings.items()
        )
        return f"TypeEnv({bindings_str})"


# Export main classes and functions
__all__ = [
    'Type',
    'TypeKind',
    'SourceLocation',
    'PrimitiveType',
    'TypeVariable',
    'FunctionType',
    'GenericType',
    'TupleType',
    'RecordType',
    'TypeScheme',
    'TypeEnvironment',
    'INT_TYPE',
    'FLOAT_TYPE',
    'STRING_TYPE',
    'BOOL_TYPE',
    'UNIT_TYPE',
    'list_type',
    'dict_type',
    'optional_type',
]
