"""
Sona Language Type-Aware Interpreter v0.7.1 (EXPERIMENTAL)

This module provides an experimental type-aware interpreter that integrates
basic type inference with the existing interpreter. This is a preview of
advanced type system features planned for v0.8.0.

EXPERIMENTAL FEATURES (v0.7.1):
- Basic type inference for literals and expressions
- Type error reporting with source locations
- Progressive typing (can work with both typed and untyped code)
- Foundation for advanced type system (coming in v0.8.0)

Author: Sona Development Team
Version: 0.7.1 (Experimental)
License: See LICENSE file
"""

from typing import Dict, Any, List, Optional, Tuple
from lark import Tree, Token

from .interpreter import SonaInterpreter
from .type_system import (
    HindleyMilnerInference, TypeEnvironment, TypeScheme,
    TypeInferenceError, TypeVariable, FunctionType,
    INT_TYPE, FLOAT_TYPE, STRING_TYPE, BOOL_TYPE, UNIT_TYPE
)
from .utils.debug import debug, warn


class TypeContext:
    """Context for type checking and inference"""

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode  # Whether to enforce strict typing
        self.type_env = TypeEnvironment()
        self.inference_engine = HindleyMilnerInference()
        self.type_cache = {}  # Cache for inferred types
        # Allow some type errors in non-strict mode
        self.error_tolerance = not strict_mode

    def infer_and_cache(self, expr, location: str = "") -> Optional[Any]:
        """Infer type and cache result"""
        try:
            type_result, substitution = self.inference_engine.infer_type(
                expr, self.type_env)
            self.type_cache[id(expr)] = (type_result, substitution)
            return type_result
        except TypeInferenceError as e:
            if self.strict_mode:
                raise
            else:
                warn(f"Type inference warning at {location}: {e}")
                return None

    def get_cached_type(self, expr):
        """Get cached type for expression"""
        return self.type_cache.get(id(expr))


class TypeAwareSonaInterpreter(SonaInterpreter):
    """Enhanced Sona interpreter with integrated type checking"""

    def __init__(self, strict_typing: bool = False,
                 enable_type_optimizations: bool = True):
        super().__init__()

        self.type_context = TypeContext(strict_mode=strict_typing)
        self.strict_typing = strict_typing
        self.enable_type_optimizations = enable_type_optimizations

        # Type-aware execution statistics
        self.type_stats = {
            'expressions_typed': 0,
            'type_errors_caught': 0,
            'type_optimizations_applied': 0,
            'inference_cache_hits': 0
        }

        # Initialize builtin types in type environment
        self._initialize_builtin_types()

        debug(f"✅ Type-aware Sona Interpreter v0.7.1 (EXPERIMENTAL) "
              f"initialized (strict={strict_typing})")

    def _initialize_builtin_types(self):
        """Initialize built-in types and functions in type environment"""
        # Built-in functions with their type schemes
        print_type = FunctionType([TypeVariable('a')], UNIT_TYPE)
        len_type = FunctionType([TypeVariable('a')], INT_TYPE)
        str_type = FunctionType([TypeVariable('a')], STRING_TYPE)
        int_type = FunctionType([STRING_TYPE], INT_TYPE)
        float_type = FunctionType([STRING_TYPE], FLOAT_TYPE)

        builtin_functions = {
            'print': TypeScheme(['a'], print_type),
            'len': TypeScheme(['a'], len_type),
            'str': TypeScheme(['a'], str_type),
            'int': TypeScheme([], int_type),
            'float': TypeScheme([], float_type),
        }

        for name, scheme in builtin_functions.items():
            self.type_context.type_env.bind(name, scheme)

    def transform(self, tree: Tree) -> Any:
        """Enhanced transform with type checking"""
        try:
            # Perform type inference if enabled
            if not self.strict_typing and self.enable_type_optimizations:
                self._try_type_inference(tree)

            # Standard interpretation
            result = super().transform(tree)

            return result

        except TypeInferenceError as e:
            if self.strict_typing:
                raise RuntimeError(f"Type error: {e}")
            else:
                warn(f"Type warning: {e}")
                return super().transform(tree)

    def _try_type_inference(self, tree: Tree) -> None:
        """Attempt type inference on the AST"""
        try:
            inferred_type = self.type_context.infer_and_cache(tree)
            if inferred_type:
                self.type_stats['expressions_typed'] += 1
                debug(f"Inferred type: {inferred_type} for {tree.data}")
        except Exception as e:
            # Don't let type inference errors break execution in non-strict
            self.type_stats['type_errors_caught'] += 1
            debug(f"Type inference failed: {e}")

    def var_assign(self, items):
        """Type-aware variable assignment"""
        if len(items) == 3:  # typed assignment: type name = value
            type_expr, name_token, value = items

            if self.strict_typing:
                # Perform strict type checking
                expected_type = self._resolve_type_expression(type_expr)
                actual_type = self.type_context.infer_and_cache(
                    value, f"assignment to {name_token}")

                if actual_type and not self._types_compatible(
                        expected_type, actual_type):
                    raise RuntimeError(
                        f"Type mismatch: cannot assign {actual_type} "
                        f"to {expected_type}")

        # Delegate to original implementation
        return super().var_assign(items)

    def _resolve_type_expression(self, type_expr):
        """Resolve a type expression to a Type object"""
        if isinstance(type_expr, Token):
            type_name = str(type_expr).lower()
            if type_name == 'int':
                return INT_TYPE
            elif type_name == 'float':
                return FLOAT_TYPE
            elif type_name == 'string' or type_name == 'str':
                return STRING_TYPE
            elif type_name == 'bool':
                return BOOL_TYPE
            else:
                return TypeVariable(type_name)  # Unknown type becomes type variable

        # For complex type expressions, we'd need more sophisticated parsing
        return TypeVariable("unknown")

    def _types_compatible(self, expected, actual):
        """Check if two types are compatible"""
        try:
            self.type_context.inference_engine.unifier.unify(expected, actual)
            return True
        except:
            return False

    def func_def(self, items):
        """Type-aware function definition"""
        try:
            # Try to infer function type
            if len(items) >= 3:
                func_name = str(items[0])
                params = items[1]
                body = items[2] if len(items) == 3 else items[-1]

                # Infer function type and add to type environment
                self.type_context.infer_and_cache(
                    Tree('func_def', items),
                    f"function {func_name}"
                )
        except Exception as e:
            debug(f"Function type inference failed: {e}")

        # Delegate to original implementation
        return super().func_def(items)

    def add(self, items):
        """Type-aware addition with optimization"""
        left, right = items

        # Check if we can apply type-based optimizations
        if self.enable_type_optimizations:
            left_type = self.type_context.get_cached_type(left)
            right_type = self.type_context.get_cached_type(right)

            if left_type and right_type:
                # Type-guided optimization
                left_is_int = left_type[0] == INT_TYPE
                right_is_int = right_type[0] == INT_TYPE
                both_numeric = (isinstance(left, (int, float)) and
                                isinstance(right, (int, float)))

                if left_is_int and right_is_int and both_numeric:
                    self.type_stats['type_optimizations_applied'] += 1
                    return int(left) + int(right)  # Fast integer path

        # Delegate to original implementation
        return super().add(items)

    def mul(self, items):
        """Type-aware multiplication with optimization"""
        left, right = items

        # Similar optimization as add
        if self.enable_type_optimizations:
            left_type = self.type_context.get_cached_type(left)
            right_type = self.type_context.get_cached_type(right)

            if left_type and right_type:
                left_is_int = left_type[0] == INT_TYPE
                right_is_int = right_type[0] == INT_TYPE
                both_numeric = (isinstance(left, (int, float)) and
                                isinstance(right, (int, float)))

                if left_is_int and right_is_int and both_numeric:
                    self.type_stats['type_optimizations_applied'] += 1
                    return int(left) * int(right)

        return super().mul(items)

    def get_type_statistics(self) -> Dict[str, Any]:
        """Get type system usage statistics"""
        return {
            **self.type_stats,
            'type_environment_size': len(self.type_context.type_env.bindings),
            'type_cache_size': len(self.type_context.type_cache),
            'strict_mode': self.strict_typing,
            'optimizations_enabled': self.enable_type_optimizations
        }

    def validate_program_types(self, ast: Tree) -> List[str]:
        """Validate types for entire program, return list of errors"""
        errors = []

        def check_node(node):
            try:
                if isinstance(node, Tree):
                    self.type_context.infer_and_cache(
                        node, f"node {node.data}")
                    for child in node.children:
                        check_node(child)
            except TypeInferenceError as e:
                errors.append(str(e))
            except Exception as e:
                errors.append(f"Type checking error: {e}")

        check_node(ast)
        return errors


class TypeAwareREPL:
    """Type-aware REPL with enhanced error reporting"""

    def __init__(self, strict_typing: bool = False):
        self.interpreter = TypeAwareSonaInterpreter(
            strict_typing=strict_typing)
        self.strict_typing = strict_typing

    def evaluate_with_types(self, code: str) -> Tuple[Any, List[str],
                                                     Dict[str, Any]]:
        """Evaluate code and return result, type errors, and statistics"""
        try:
            # Import parser locally to avoid module resolution issues
            try:
                from lark import Lark
                # Create a simple parser - in real implementation,
                # this would use the actual Sona grammar
                parser = Lark("start: expr", start='start')
                ast = parser.parse(code)
            except Exception:
                # Fallback: create a simple AST structure
                from lark import Tree
                ast = Tree('start', [code])

            # Pre-validate types if in strict mode
            type_errors = []
            if self.strict_typing:
                type_errors = self.interpreter.validate_program_types(ast)
                if type_errors:
                    return (None, type_errors,
                            self.interpreter.get_type_statistics())

            # Execute
            result = self.interpreter.transform(ast)
            stats = self.interpreter.get_type_statistics()

            return result, type_errors, stats

        except Exception as e:
            return (None, [str(e)],
                    self.interpreter.get_type_statistics())


# Factory functions for different modes
def create_type_aware_interpreter(strict: bool = False,
                                  optimizations: bool = True):
    """Create a type-aware interpreter with specified settings"""
    return TypeAwareSonaInterpreter(
        strict_typing=strict,
        enable_type_optimizations=optimizations
    )


def create_strict_interpreter():
    """Create a strictly typed interpreter"""
    return create_type_aware_interpreter(strict=True, optimizations=True)


def create_gradual_interpreter():
    """Create a gradually typed interpreter (warnings only)"""
    return create_type_aware_interpreter(strict=False, optimizations=True)


# Export public interface
__all__ = [
    'TypeAwareSonaInterpreter',
    'TypeAwareREPL',
    'TypeContext',
    'create_type_aware_interpreter',
    'create_strict_interpreter',
    'create_gradual_interpreter'
]
