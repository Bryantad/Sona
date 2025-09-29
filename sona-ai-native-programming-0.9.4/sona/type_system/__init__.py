"""
Sona Language Type System (v0.9.4)

This package implements the type system for the Sona programming language.

v0.9.4 Components:
- runtime_checker.py: Runtime type validation for function parameters/returns
- types.py: Core type definitions and type representations
- inference.py: Hindley-Milner type inference (experimental)
- simple.py: Simplified type system for initial implementation
- checker.py: Integration with Sona interpreter

Author: Sona Development Team
Version: 0.9.4
License: See LICENSE file
"""

# Import runtime type checking (NEW in v0.9.4)
from .runtime_checker import (
    TypeValidationError,
    ReturnTypeValidationError,
    TypeChecker,
    check_types,
    typed_function,
    TypeCheckingConfig,
    optimized_check_types
)

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

# Export all public APIs
__all__ = [
    # Runtime type checking (v0.9.4)
    'TypeValidationError',
    'ReturnTypeValidationError',
    'TypeChecker',
    'check_types',
    'typed_function',
    'TypeCheckingConfig',
    'optimized_check_types',
    
    # Type inference
    'Constraint',
    'HindleyMilnerInference',
    'Substitution',
    'TypeInferenceError',
    'UnificationEngine',
    'UnificationError',
    
    # Simple type checker
    'SimpleTypeChecker',
    'check_type',
    
    # Core types
    'BOOL_TYPE',
    'FLOAT_TYPE',
    'INT_TYPE',
    'STRING_TYPE',
    'UNIT_TYPE',
    'FunctionType',
    'GenericType',
    'PrimitiveType',
    'RecordType',
    'SourceLocation',
    'TupleType',
    'Type',
    'TypeEnvironment',
    'TypeKind',
    'TypeScheme',
    'TypeVariable',
]


__version__ = "0.9.2"
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
