"""
Sona Language Type System - Hindley-Milner Type Inference Engine

This module implements the core Hindley-Milner type inference algorithm
with constraint generation, unification, and type scheme generalization.
It provides principal type inference for the Sona language.

Author: Sona Development Team
Version: 0.8.0 (Phase 2)
License: See LICENSE file
"""

from typing import Dict, List, Set, Optional, Tuple, Union
from dataclasses import dataclass
import copy

from .types import (
    Type, TypeVariable, PrimitiveType, FunctionType, GenericType,
    TupleType, RecordType, TypeScheme, TypeEnvironment, SourceLocation,
    INT_TYPE, FLOAT_TYPE, STRING_TYPE, BOOL_TYPE, UNIT_TYPE
)


class TypeInferenceError(Exception):
    """Exception raised during type inference"""

    def __init__(self, message: str, location: Optional[SourceLocation] = None):
        self.message = message
        self.location = location
        super().__init__(message)

    def __str__(self) -> str:
        if self.location:
            return f"Type error at {self.location}: {self.message}"
        return f"Type error: {self.message}"


class UnificationError(TypeInferenceError):
    """Exception raised when types cannot be unified"""

    def __init__(self, type1: Type, type2: Type,
                 location: Optional[SourceLocation] = None):
        self.type1 = type1
        self.type2 = type2
        message = f"Cannot unify types '{type1}' and '{type2}'"
        super().__init__(message, location)


@dataclass
class Constraint:
    """Type constraint for constraint-based inference"""
    left: Type
    right: Type
    location: Optional[SourceLocation] = None

    def __str__(self) -> str:
        return f"{self.left} ~ {self.right}"


class Substitution:
    """Type variable substitution mapping"""

    def __init__(self, mapping: Optional[Dict[str, Type]] = None):
        self.mapping = mapping or {}

    def __getitem__(self, var_name: str) -> Type:
        return self.mapping.get(var_name, TypeVariable(var_name))

    def __setitem__(self, var_name: str, type_: Type) -> None:
        self.mapping[var_name] = type_

    def __contains__(self, var_name: str) -> bool:
        return var_name in self.mapping

    def apply(self, type_: Type) -> Type:
        """Apply substitution to a type"""
        return type_.substitute(self.mapping)

    def apply_scheme(self, scheme: TypeScheme) -> TypeScheme:
        """Apply substitution to a type scheme"""
        # Don't substitute bound variables
        filtered_mapping = {k: v for k, v in self.mapping.items()
                           if k not in scheme.type_vars}
        new_type = scheme.type.substitute(filtered_mapping)
        return TypeScheme(scheme.type_vars, new_type)

    def apply_env(self, env: TypeEnvironment) -> TypeEnvironment:
        """Apply substitution to a type environment"""
        new_env = TypeEnvironment(env.parent)
        for name, scheme in env.bindings.items():
            new_env.bind(name, self.apply_scheme(scheme))
        return new_env

    def compose(self, other: 'Substitution') -> 'Substitution':
        """Compose two substitutions"""
        new_mapping = {}

        # Apply other to self's mapping
        for var, type_ in self.mapping.items():
            new_mapping[var] = other.apply(type_)

        # Add other's mappings that aren't in self
        for var, type_ in other.mapping.items():
            if var not in new_mapping:
                new_mapping[var] = type_

        return Substitution(new_mapping)

    def __str__(self) -> str:
        if not self.mapping:
            return "[]"
        items = [f"{k} := {v}" for k, v in self.mapping.items()]
        return "[" + ", ".join(items) + "]"


class UnificationEngine:
    """Type unification engine with occurs check"""

    def unify(self, type1: Type, type2: Type) -> Substitution:
        """Unify two types, returning a substitution"""
        return self._unify_impl(type1, type2)

    def _unify_impl(self, type1: Type, type2: Type) -> Substitution:
        """Internal unification implementation"""
        # Same type
        if type1 == type2:
            return Substitution()

        # Type variable cases
        if isinstance(type1, TypeVariable):
            return self._unify_variable(type1, type2)
        elif isinstance(type2, TypeVariable):
            return self._unify_variable(type2, type1)

        # Function types
        elif isinstance(type1, FunctionType) and isinstance(type2, FunctionType):
            return self._unify_function_types(type1, type2)

        # Generic types
        elif isinstance(type1, GenericType) and isinstance(type2, GenericType):
            return self._unify_generic_types(type1, type2)

        # Tuple types
        elif isinstance(type1, TupleType) and isinstance(type2, TupleType):
            return self._unify_tuple_types(type1, type2)

        # Record types
        elif isinstance(type1, RecordType) and isinstance(type2, RecordType):
            return self._unify_record_types(type1, type2)

        # Cannot unify
        else:
            raise UnificationError(type1, type2)

    def _unify_variable(self, var: TypeVariable, type_: Type) -> Substitution:
        """Unify a type variable with another type"""
        if var == type_:
            return Substitution()

        # Occurs check
        if var.name in type_.free_variables():
            raise UnificationError(var, type_)

        return Substitution({var.name: type_})

    def _unify_function_types(self, func1: FunctionType,
                             func2: FunctionType) -> Substitution:
        """Unify two function types"""
        if len(func1.param_types) != len(func2.param_types):
            raise UnificationError(func1, func2)

        # Unify parameter types and return type
        subst = Substitution()

        # Unify parameter types
        for p1, p2 in zip(func1.param_types, func2.param_types):
            param_subst = self._unify_impl(subst.apply(p1), subst.apply(p2))
            subst = subst.compose(param_subst)

        # Unify return types
        return_subst = self._unify_impl(
            subst.apply(func1.return_type),
            subst.apply(func2.return_type)
        )
        return subst.compose(return_subst)

    def _unify_generic_types(self, gen1: GenericType,
                            gen2: GenericType) -> Substitution:
        """Unify two generic types"""
        if (gen1.constructor != gen2.constructor or
            len(gen1.type_args) != len(gen2.type_args)):
            raise UnificationError(gen1, gen2)

        subst = Substitution()
        for arg1, arg2 in zip(gen1.type_args, gen2.type_args):
            arg_subst = self._unify_impl(subst.apply(arg1), subst.apply(arg2))
            subst = subst.compose(arg_subst)

        return subst

    def _unify_tuple_types(self, tuple1: TupleType,
                          tuple2: TupleType) -> Substitution:
        """Unify two tuple types"""
        if len(tuple1.element_types) != len(tuple2.element_types):
            raise UnificationError(tuple1, tuple2)

        subst = Substitution()
        for elem1, elem2 in zip(tuple1.element_types, tuple2.element_types):
            elem_subst = self._unify_impl(subst.apply(elem1), subst.apply(elem2))
            subst = subst.compose(elem_subst)

        return subst

    def _unify_record_types(self, rec1: RecordType,
                           rec2: RecordType) -> Substitution:
        """Unify two record types"""
        if set(rec1.fields.keys()) != set(rec2.fields.keys()):
            raise UnificationError(rec1, rec2)

        subst = Substitution()
        for field_name in rec1.fields:
            field_subst = self._unify_impl(
                subst.apply(rec1.fields[field_name]),
                subst.apply(rec2.fields[field_name])
            )
            subst = subst.compose(field_subst)

        return subst


class HindleyMilnerInference:
    """Main Hindley-Milner type inference engine"""

    def __init__(self):
        self.unifier = UnificationEngine()
        self._type_var_counter = 0

    def fresh_var(self) -> TypeVariable:
        """Generate a fresh type variable"""
        self._type_var_counter += 1
        return TypeVariable(f"t{self._type_var_counter}")

    def infer_type(self, expr, env: TypeEnvironment) -> Tuple[Type, Substitution]:
        """Infer the type of an expression"""
        try:
            from lark import Tree, Token
        except ImportError:
            # Fallback for testing without lark
            Tree = type('Tree', (), {})
            Token = type('Token', (), {})

        if isinstance(expr, Token) or (hasattr(expr, 'type') and hasattr(expr, 'value')):
            return self._infer_token(expr, env)
        elif isinstance(expr, Tree) or (hasattr(expr, 'data') and hasattr(expr, 'children')):
            return self._infer_tree(expr, env)
        else:
            # Literal values
            return self._infer_literal(expr, env)

    def _infer_token(self, token,
                    env: TypeEnvironment) -> Tuple[Type, Substitution]:
        """Infer type of a token"""
        if token.type == 'NUMBER':
            if '.' in token.value:
                return FLOAT_TYPE, Substitution()
            else:
                return INT_TYPE, Substitution()
        elif token.type == 'STRING':
            return STRING_TYPE, Substitution()
        elif token.type == 'NAME':
            # Variable lookup
            scheme = env.lookup(token.value)
            if scheme is None:
                raise TypeInferenceError(f"Undefined variable: {token.value}")
            return scheme.instantiate(), Substitution()
        else:
            raise TypeInferenceError(f"Unknown token type: {token.type}")

    def _infer_literal(self, value,
                      env: TypeEnvironment) -> Tuple[Type, Substitution]:
        """Infer type of literal values"""
        if isinstance(value, int):
            return INT_TYPE, Substitution()
        elif isinstance(value, float):
            return FLOAT_TYPE, Substitution()
        elif isinstance(value, str):
            return STRING_TYPE, Substitution()
        elif isinstance(value, bool):
            return BOOL_TYPE, Substitution()
        else:
            raise TypeInferenceError(f"Unknown literal type: {type(value)}")

    def _infer_tree(self, tree, env: TypeEnvironment) -> Tuple[Type, Substitution]:
        """Infer type of a tree node"""
        if tree.data == 'add':
            return self._infer_arithmetic(tree, env, '+')
        elif tree.data == 'sub':
            return self._infer_arithmetic(tree, env, '-')
        elif tree.data == 'mul':
            return self._infer_arithmetic(tree, env, '*')
        elif tree.data == 'div':
            return self._infer_arithmetic(tree, env, '/')
        elif tree.data == 'var_assign':
            return self._infer_assignment(tree, env)
        elif tree.data == 'func_def':
            return self._infer_function_def(tree, env)
        elif tree.data == 'func_call':
            return self._infer_function_call(tree, env)
        elif tree.data == 'if_stmt':
            return self._infer_if(tree, env)
        else:
            raise TypeInferenceError(f"Unknown tree node: {tree.data}")

    def _infer_arithmetic(self, tree, env: TypeEnvironment, op: str) -> Tuple[Type, Substitution]:
        """Infer type of arithmetic expressions"""
        left_expr, right_expr = tree.children

        # Infer operand types
        left_type, left_subst = self.infer_type(left_expr, env)
        right_type, right_subst = self.infer_type(right_expr,
                                                 left_subst.apply_env(env))

        # Compose substitutions
        subst = left_subst.compose(right_subst)

        # Apply substitution to operand types
        left_type = subst.apply(left_type)
        right_type = subst.apply(right_type)

        # For arithmetic ops, operands should be numeric
        if op in ['+', '-', '*', '/']:
            # Try to unify with numeric types
            numeric_unify = self._unify_numeric_types(left_type, right_type)
            if numeric_unify:
                result_type, unify_subst = numeric_unify
                return result_type, subst.compose(unify_subst)

        # String concatenation for +
        if op == '+':
            try:
                str_subst = self.unifier.unify(left_type, STRING_TYPE)
                str_subst2 = self.unifier.unify(right_type, STRING_TYPE)
                combined_subst = subst.compose(str_subst).compose(str_subst2)
                return STRING_TYPE, combined_subst
            except UnificationError:
                pass

        raise TypeInferenceError(f"Type mismatch in {op} operation: "
                               f"{left_type} {op} {right_type}")

    def _unify_numeric_types(self, left: Type,
                           right: Type) -> Optional[Tuple[Type, Substitution]]:
        """Try to unify types as numeric, returning result type"""
        try:
            # Try int + int = int
            int_subst1 = self.unifier.unify(left, INT_TYPE)
            int_subst2 = self.unifier.unify(right, INT_TYPE)
            combined_subst = int_subst1.compose(int_subst2)
            return INT_TYPE, combined_subst
        except UnificationError:
            pass

        try:
            # Try float + float = float (or mixed numeric = float)
            float_subst1 = self.unifier.unify(left, FLOAT_TYPE)
            float_subst2 = self.unifier.unify(right, FLOAT_TYPE)
            combined_subst = float_subst1.compose(float_subst2)
            return FLOAT_TYPE, combined_subst
        except UnificationError:
            pass

        # Mixed int/float = float
        try:
            if ((left == INT_TYPE and right == FLOAT_TYPE) or
                (left == FLOAT_TYPE and right == INT_TYPE)):
                return FLOAT_TYPE, Substitution()
        except:
            pass

        return None

    def _infer_assignment(self, tree,
                         env: TypeEnvironment) -> Tuple[Type, Substitution]:
        """Infer type of variable assignment"""
        if len(tree.children) == 3:
            _, var_name, value_expr = tree.children
        else:
            var_name, value_expr = tree.children

        # Infer value type
        value_type, subst = self.infer_type(value_expr, env)

        # Generalize and bind to environment
        generalized = self._generalize(value_type, subst.apply_env(env))
        env.bind(str(var_name), generalized)

        return value_type, subst

    def _generalize(self, type_: Type, env: TypeEnvironment) -> TypeScheme:
        """Generalize a type into a type scheme"""
        env_free_vars = env.free_variables()
        type_free_vars = type_.free_variables()
        generalizable_vars = type_free_vars - env_free_vars
        return TypeScheme(list(generalizable_vars), type_)

    def _infer_function_def(self, tree,
                           env: TypeEnvironment) -> Tuple[Type, Substitution]:
        """Infer type of function definition"""
        # This is a simplified version - full implementation would be more complex
        func_name, params, body = tree.children

        # Create parameter types
        param_types = [self.fresh_var() for _ in params.children]

        # Create new environment with parameters
        new_env = TypeEnvironment(env)
        for param_name, param_type in zip(params.children, param_types):
            scheme = TypeScheme([], param_type)
            new_env.bind(str(param_name), scheme)

        # Infer body type
        body_type, body_subst = self.infer_type(body, new_env)

        # Create function type
        func_type = FunctionType(param_types, body_type)

        # Generalize and bind function
        generalized = self._generalize(func_type, body_subst.apply_env(env))
        env.bind(str(func_name), generalized)

        return func_type, body_subst

    def _infer_function_call(self, tree,
                           env: TypeEnvironment) -> Tuple[Type, Substitution]:
        """Infer type of function call"""
        func_expr, *arg_exprs = tree.children

        # Infer function type
        func_type, func_subst = self.infer_type(func_expr, env)

        # Infer argument types
        arg_types = []
        subst = func_subst
        current_env = env

        for arg_expr in arg_exprs:
            arg_type, arg_subst = self.infer_type(arg_expr,
                                                 subst.apply_env(current_env))
            arg_types.append(arg_type)
            subst = subst.compose(arg_subst)

        # Create expected function type
        return_type = self.fresh_var()
        expected_func_type = FunctionType(arg_types, return_type)

        # Unify with actual function type
        unify_subst = self.unifier.unify(subst.apply(func_type),
                                        expected_func_type)
        final_subst = subst.compose(unify_subst)

        return final_subst.apply(return_type), final_subst

    def _infer_if(self, tree,
                 env: TypeEnvironment) -> Tuple[Type, Substitution]:
        """Infer type of if expression"""
        condition, then_branch, else_branch = tree.children

        # Infer condition type (should be bool)
        cond_type, cond_subst = self.infer_type(condition, env)
        bool_subst = self.unifier.unify(cond_type, BOOL_TYPE)
        subst = cond_subst.compose(bool_subst)

        # Infer branch types
        then_type, then_subst = self.infer_type(then_branch,
                                               subst.apply_env(env))
        else_type, else_subst = self.infer_type(else_branch,
                                               then_subst.apply_env(subst.apply_env(env)))

        # Unify branch types
        branch_subst = self.unifier.unify(then_subst.apply(then_type),
                                         else_type)

        final_subst = subst.compose(then_subst).compose(else_subst).compose(branch_subst)
        return final_subst.apply(then_type), final_subst


# Export main classes
__all__ = [
    'TypeInferenceError', 'UnificationError', 'Constraint', 'Substitution',
    'UnificationEngine', 'HindleyMilnerInference'
]
