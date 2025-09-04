"""
Sona Language Type System - Type Checker Integration

This module integrates the type system with the Sona interpreter,
providing type checking for Sona language constructs.

Author: Sona Development Team
Version: 0.9.0 (Phase 2)
License: See LICENSE file
"""

from typing import Any, Dict, List, Optional, Tuple

from .inference import HindleyMilnerInference, TypeInferenceError
from .types import (
    BOOL_TYPE,
    FLOAT_TYPE,
    INT_TYPE,
    STRING_TYPE,
    UNIT_TYPE,
    FunctionType,
    PrimitiveType,
    SourceLocation,
    Type,
    TypeEnvironment,
    TypeScheme,
    TypeVariable,
)


class SonaTypeChecker: """Main type checker for Sona language"""

    def __init__(self): self.inference_engine = HindleyMilnerInference()
        self.global_env = self._create_global_env()

    def _create_global_env(self) -> TypeEnvironment: """Create global type environment with built-ins"""
        env = TypeEnvironment()

        # Built-in functions
        env.bind(
            "print",
            TypeScheme(["a"], FunctionType([TypeVariable("a")], UNIT_TYPE)),
        )
        env.bind(
            "len",
            TypeScheme(["a"], FunctionType([TypeVariable("a")], INT_TYPE)),
        )
        env.bind(
            "str",
            TypeScheme(["a"], FunctionType([TypeVariable("a")], STRING_TYPE)),
        )
        env.bind("int", TypeScheme([], FunctionType([STRING_TYPE], INT_TYPE)))
        env.bind(
            "float", TypeScheme([], FunctionType([STRING_TYPE], FLOAT_TYPE))
        )

        return env

    def check_expression(
        self, expr: Any, env: Optional[TypeEnvironment] = None
    ) -> Type: """Type check an expression and return its type"""
        if env is None: env = self.global_env

        try: inferred_type, _ = self.inference_engine.infer_type(expr, env)
            return inferred_type
        except TypeInferenceError as e: # Re-raise with more context
            raise TypeInferenceError(
                f"Type checking failed: {e.message}", e.location
            )

    def check_program(self, statements: List[Any]) -> Dict[str, Type]: """Type check a program and return variable types"""
        env = TypeEnvironment(self.global_env)
        variable_types = {}

        for stmt in statements: try: stmt_type = (
            self.check_expression(stmt, env)
        )
                # If it's a variable assignment, record the type
                if hasattr(stmt, 'data') and stmt.data = (
                    = 'var_assign': if len(stmt.children) >= 2: var_name = str(stmt.children[-2])
                )
                        variable_types[var_name] = stmt_type
            except TypeInferenceError as e: print(f"Type error in statement: {e}")
                # Continue checking other statements

        return variable_types

    def get_type_info(self, expr: Any) -> Dict[str, Any]: """Get detailed type information for an expression"""
        try: inferred_type = self.check_expression(expr)
            return {
                "type": str(inferred_type),
                "kind": inferred_type.kind.value,
                "free_variables": list(inferred_type.free_variables()),
                "success": True,
                "error": None,
            }
        except TypeInferenceError as e: return {
                "type": None,
                "kind": None,
                "free_variables": [],
                "success": False,
                "error": str(e),
            }


# Convenience function for quick type checking
def check_type(expr: Any) -> str: """Quick type check that returns type as string"""
    checker = SonaTypeChecker()
    try: result_type = checker.check_expression(expr)
        return str(result_type)
    except TypeInferenceError as e: return f"Type Error: {e.message}"


# Export main classes
__all__ = ['SonaTypeChecker', 'TypeInferenceError', 'check_type']
