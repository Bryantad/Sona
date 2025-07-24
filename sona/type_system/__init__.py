"""
Sona Language Type System (EXPERIMENTAL v0.7.1)

This package implements an experimental type system for the Sona programming
language. This is a preview of advanced features planned for v0.8.0.

EXPERIMENTAL Components (v0.7.1):
- types.py: Core type definitions and type representations
- inference.py: Basic Hindley-Milner type inference (experimental)
- simple.py: Simplified type system for initial implementation

Author: Sona Development Team
Version: 0.7.1 (Experimental)
License: See LICENSE file
"""

# Import inference engine
from .inference import (
    Constraint,
    HindleyMilnerInference,
    Substitution,
    TypeInferenceError,
    UnificationEngine,
    UnificationError,
)

# Import simple type checker for fallback
from .simple import SimpleTypeChecker, check_type

# Import core types
from .types import (
    BOOL_TYPE,
    FLOAT_TYPE,
    INT_TYPE,
    STRING_TYPE,
    UNIT_TYPE,
    FunctionType,
    GenericType,
    PrimitiveType,
    RecordType,
    SourceLocation,
    TupleType,
    Type,
    TypeEnvironment,
    TypeKind,
    TypeScheme,
    TypeVariable,
)

__version__ = "0.8.1"
__all__ = [
    # Core types
    "Type",
    "TypeKind",
    "SourceLocation",
    "PrimitiveType",
    "TypeVariable",
    "FunctionType",
    "GenericType",
    "TupleType",
    "RecordType",
    "TypeScheme",
    "TypeEnvironment",
    # Type constants
    "INT_TYPE",
    "FLOAT_TYPE",
    "STRING_TYPE",
    "BOOL_TYPE",
    "UNIT_TYPE",
    # Inference engine
    "TypeInferenceError",
    "UnificationError",
    "Constraint",
    "Substitution",
    "UnificationEngine",
    "HindleyMilnerInference",
    # Simple type checking
    "SimpleTypeChecker",
    "check_type",
]
