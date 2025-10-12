"""
Sona v0.9.4 Runtime Type Checking

This module implements runtime type validation for function parameters
and return values. Focus on simple types: int, str, bool with clear
error messages.

Author: GitHub Copilot (Release Engineer)
Version: 0.9.4
"""

import functools
import inspect
from typing import Any, Callable

# Import the new configuration system
from ..type_config import (
    get_type_config,
    get_type_logger,
    TypeCheckMode,
    create_fix_tip
)


# Compatibility layer for old TypeCheckingConfig
class TypeCheckingConfig:
    """Legacy configuration for runtime type checking - now uses type_config"""
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Check if type checking is enabled via new configuration system"""
        config = get_type_config()
        return config.should_check_types()
    
    @classmethod
    def enable(cls):
        """Explicitly enable type checking"""
        # For tests, we can override the global config
        config = get_type_config()
        config.set_cli_mode("on")
    
    @classmethod
    def disable(cls):
        """Explicitly disable type checking"""
        config = get_type_config()
        config.set_cli_mode("off")
    
    @classmethod
    def reset(cls):
        """Reset to environment variable detection"""
        config = get_type_config()
        config.set_cli_mode(None)


class TypeCheckAbort(Exception):
    """Sentinel exception for type checking failures in ON mode"""
    pass


class TypeValidationError(Exception):
    """Raised when runtime type validation fails"""
    
    def __init__(self, param_name: str, expected_type: str,
                 actual_type: str, value: Any, function_name: str = None,
                 error_code: str = "S-1001", fix_suggestion: str = None):
        self.param_name = param_name
        self.expected_type = expected_type
        self.actual_type = actual_type
        self.value = value
        self.function_name = function_name
        self.error_code = error_code
        self.fix_suggestion = fix_suggestion
        
        # Build enhanced error message
        func_context = f" at {function_name}()" if function_name else ""
        message = f"TypeError[{error_code}]{func_context}: expected {expected_type} for '{param_name}', got {actual_type}"
        
        # Add value details for better debugging
        if actual_type in ['list', 'dict', 'set', 'tuple'] and hasattr(value, '__len__'):
            message += f" (length: {len(value)})"
        elif len(str(value)) < 50:
            message += f" (value: {repr(value)})"
        
        # Add fix suggestion if provided
        if fix_suggestion:
            message += f"\nFix: {fix_suggestion}"
        else:
            # Generate default fix suggestions
            default_fix = self._generate_fix_suggestion()
            if default_fix:
                message += f"\nFix: {default_fix}"
                
        super().__init__(message)
    
    def _generate_fix_suggestion(self) -> str:
        """Generate helpful fix suggestions based on the error"""
        expected = self.expected_type.lower()
        actual = self.actual_type.lower()
        
        # Common type conversion suggestions
        if expected == "str" and actual in ["int", "float", "bool"]:
            return f"Convert to string: str({self.param_name})"
        elif expected == "int" and actual == "str":
            return f"Convert to integer: int({self.param_name}) (ensure it's a valid number)"
        elif expected == "list" and actual in ["tuple", "set"]:
            return f"Convert to list: list({self.param_name})"
        elif expected == "bool" and actual in ["int", "str"]:
            return f"Convert to boolean: bool({self.param_name})"
        elif "list[" in expected and actual == "list":
            return f"Check list elements - they should all be {expected.split('[')[1].split(']')[0]} type"
        elif "dict[" in expected and actual == "dict":
            return f"Check dict keys/values - they should match {expected} pattern"
        elif "|" in expected:  # Union type
            valid_types = expected.split("|")
            return f"Use one of: {', '.join(valid_types)}"
        elif expected.startswith("union["):  # Union[...] syntax
            # Extract types from Union[type1, type2, ...]
            inner = expected[6:-1]  # Remove "union[" and "]"
            valid_types = [t.strip() for t in inner.split(",")]
            return f"Use one of: {', '.join(valid_types)}"
        elif expected.startswith("optional["):
            inner_type = expected[9:-1]  # Remove "optional[" and "]"
            return f"Use {inner_type} or None"
        
        return f"Ensure {self.param_name} is of type {expected}"


class ReturnTypeValidationError(Exception):
    """Raised when return type validation fails"""
    
    def __init__(self, expected_type: str, actual_type: str, value: Any,
                 function_name: str = None, error_code: str = "S-1002",
                 fix_suggestion: str = None):
        self.expected_type = expected_type
        self.actual_type = actual_type
        self.value = value
        self.function_name = function_name
        self.error_code = error_code
        self.fix_suggestion = fix_suggestion
        
        # Build enhanced error message
        func_context = f" in {function_name}()" if function_name else ""
        message = f"TypeError[{error_code}]{func_context}: expected return type {expected_type}, got {actual_type}"
        
        # Add value details for better debugging
        if actual_type in ['list', 'dict', 'set', 'tuple'] and hasattr(value, '__len__'):
            message += f" (returned {actual_type} of length: {len(value)})"
        elif len(str(value)) < 50:
            message += f" (returned: {repr(value)})"
        
        # Add fix suggestion if provided
        if fix_suggestion:
            message += f"\nFix: {fix_suggestion}"
        else:
            # Generate default fix suggestions
            default_fix = self._generate_fix_suggestion()
            if default_fix:
                message += f"\nFix: {default_fix}"
                
        super().__init__(message)
    
    def _generate_fix_suggestion(self) -> str:
        """Generate helpful fix suggestions for return type errors"""
        expected = self.expected_type.lower()
        actual = self.actual_type.lower()
        
        if expected == "bool" and actual in ["int", "str", "none"]:
            return "Return True or False instead of other types"
        elif expected == "str" and actual in ["int", "float", "bool"]:
            return "Convert return value to string: return str(value)"
        elif expected == "int" and actual in ["str", "float", "bool"]:
            return "Convert return value to integer: return int(value)"
        elif expected == "list" and actual in ["tuple", "set"]:
            return "Convert return value to list: return list(value)"
        elif "|" in expected:  # Union type
            valid_types = expected.split("|")
            return f"Return one of: {', '.join(valid_types)}"
        elif expected.startswith("optional["):
            inner_type = expected[9:-1]  # Remove "optional[" and "]"
            return f"Return {inner_type} or None"
        
        return f"Ensure function returns {expected} type"


class CollectionTypeValidationError(TypeValidationError):
    """Raised when collection element validation fails"""
    
    def __init__(self, param_name: str, expected_type: str, actual_type: str,
                 value: Any, element_index: int = None, element_key: str = None,
                 function_name: str = None):
        self.element_index = element_index
        self.element_key = element_key
        
        # Build more specific error message for collections
        if element_index is not None:
            detail = f" (index {element_index} is {actual_type})"
            error_code = "S-1003"
            fix_suggestion = f"Check element at index {element_index} - it should be {expected_type.split('[')[1].split(']')[0] if '[' in expected_type else expected_type}"
        elif element_key is not None:
            detail = f" (key '{element_key}' has {actual_type})"
            error_code = "S-1004"
            fix_suggestion = f"Check value for key '{element_key}' - it should be the correct type"
        else:
            detail = ""
            error_code = "S-1003"
            fix_suggestion = f"Check all collection elements are {expected_type}"
            
        super().__init__(
            param_name=param_name,
            expected_type=expected_type,
            actual_type=actual_type + detail,
            value=value,
            function_name=function_name,
            error_code=error_code,
            fix_suggestion=fix_suggestion
        )


class CallableTypeValidationError(Exception):
    """Raised when Callable type validation fails"""
    
    def __init__(self, param_name: str, expected_spec: str, actual_type: str,
                 value: Any, function_name: str = None,
                 error_code: str = "S-2100", fix_suggestion: str = None):
        self.param_name = param_name
        self.expected_spec = expected_spec
        self.actual_type = actual_type
        self.value = value
        self.function_name = function_name
        self.error_code = error_code
        self.fix_suggestion = fix_suggestion or self._generate_fix_suggestion()
        
        # Build enhanced error message
        func_context = f" at {function_name}()" if function_name else ""
        message = (f"TypeError[{error_code}]{func_context}: "
                   f"expected {expected_spec} for '{param_name}', "
                   f"got {actual_type}")
        
        # Add value context for debugging
        if hasattr(value, '__name__'):
            value_context = f" (function: {value.__name__})"
        elif callable(value):
            value_context = f" (callable: {type(value).__name__})"
        else:
            value_repr = repr(value)[:50]
            if len(repr(value)) > 50:
                value_repr += "..."
            value_context = f" (value: {value_repr})"
        message += value_context
        
        # Add fix suggestion
        message += f"\nFix: {self.fix_suggestion}"
        
        super().__init__(message)
    
    def _generate_fix_suggestion(self) -> str:
        """Generate helpful fix suggestion based on error type"""
        if self.error_code == "S-2100":  # NonCallable
            return f"Ensure {self.param_name} is a function or callable object"
        elif self.error_code == "S-2101":  # ArityMismatch
            return (f"Adjust function signature to match "
                    f"{self.expected_spec} parameter count")
        elif self.error_code == "S-2102":  # VariadicMismatch
            return ("Use Callable[..., ReturnType] spec for functions "
                    "with *args/**kwargs")
        elif self.error_code == "S-2103":  # ReturnTypeMismatch
            return ("Change return type or update spec to match "
                    "actual return type")
        else:
            return f"Ensure {self.param_name} matches {self.expected_spec}"


class TypeChecker:
    """Runtime type checker for Sona functions"""
    
    # Map Sona type names to Python types
    TYPE_MAP = {
        # Primitive types
        'int': int,
        'str': str,
        'bool': bool,
        'float': float,
        'complex': complex,
        'bytes': bytes,
        'bytearray': bytearray,
        
        # Collection types
        'list': list,
        'dict': dict,
        'set': set,
        'frozenset': frozenset,
        'tuple': tuple,
        
        # Capitalized versions for typing module compatibility
        'List': list,
        'Dict': dict,
        'Set': set,
        'FrozenSet': frozenset,
        'Tuple': tuple,
        
        # Optional and Union (special handling)
        'Optional': object,  # Special handling in validate_collection_type
        'Union': object,     # Special handling in validate_single_type
        
        # Standard library types from typing module
        'Any': object,       # Any type accepts anything
        'Sequence': (list, tuple, str, bytes, bytearray),
        'Iterable': (list, tuple, str, dict, set, frozenset, bytes, bytearray),
        'Mapping': dict,
        'MutableMapping': dict,
        'Collection': (list, tuple, set, frozenset, dict),
        'Container': (list, tuple, str, dict, set, frozenset, bytes),
        
        # IO types
        'TextIO': object,    # For file-like objects
        'BinaryIO': object,  # For binary file-like objects
        
        # Callable is handled specially in validate_single_type
        'Callable': object,
        
        # Pattern type for match statements
        'Pattern': object,
        
        # Type aliases
        'Number': (int, float, complex),
        'Text': str,
    }
    
    # Type alias registry for custom type aliases
    TYPE_ALIASES = {}
    
    # Performance caches
    _PARSE_CACHE = {}  # Cache for parse_generic_type results
    _VALIDATION_CACHE = {}  # Cache for validation results
    _SIGNATURE_CACHE = {}  # Cache for function signature inspection
    _CACHE_STATS = {
        'parse_hits': 0, 'parse_misses': 0,
        'validation_hits': 0, 'validation_misses': 0,
        'signature_hits': 0, 'signature_misses': 0
    }
    
    @classmethod
    def register_type_alias(cls, alias_name: str, actual_type: str):
        """Register a custom type alias
        
        Args:
            alias_name: The alias name (e.g., "UserId")
            actual_type: The actual type (e.g., "int", "Dict[str, int]")
        
        Example:
            TypeChecker.register_type_alias("UserId", "int")
            TypeChecker.register_type_alias("UserData", "Dict[str, int]")
        """
        cls.TYPE_ALIASES[alias_name] = actual_type
    
    @classmethod
    def unregister_type_alias(cls, alias_name: str):
        """Remove a type alias"""
        if alias_name in cls.TYPE_ALIASES:
            del cls.TYPE_ALIASES[alias_name]
    
    @classmethod
    def clear_type_aliases(cls):
        """Clear all type aliases"""
        cls.TYPE_ALIASES.clear()
    
    @classmethod
    def get_type_aliases(cls) -> dict:
        """Get all registered type aliases"""
        return cls.TYPE_ALIASES.copy()
    
    @classmethod
    def clear_caches(cls):
        """Clear all performance caches"""
        cls._PARSE_CACHE.clear()
        cls._VALIDATION_CACHE.clear()
        cls._SIGNATURE_CACHE.clear()
        cls._CACHE_STATS = {
            'parse_hits': 0, 'parse_misses': 0,
            'validation_hits': 0, 'validation_misses': 0,
            'signature_hits': 0, 'signature_misses': 0
        }
    
    @classmethod
    def get_cache_stats(cls) -> dict:
        """Get performance cache statistics"""
        stats = cls._CACHE_STATS.copy()
        # Calculate hit rates
        for prefix in ['parse', 'validation', 'signature']:
            hits = stats[f'{prefix}_hits']
            misses = stats[f'{prefix}_misses']
            total = hits + misses
            stats[f'{prefix}_hit_rate'] = hits / total if total > 0 else 0.0
        return stats
    
    @classmethod
    def get_cache_sizes(cls) -> dict:
        """Get current cache sizes"""
        return {
            'parse_cache': len(cls._PARSE_CACHE),
            'validation_cache': len(cls._VALIDATION_CACHE),
            'signature_cache': len(cls._SIGNATURE_CACHE)
        }
    
    @classmethod
    def _is_cacheable_value(cls, value: Any) -> bool:
        """Check if a value is safe to use for caching (immutable)"""
        return isinstance(value, (str, int, float, bool, tuple, type(None)))
    
    @classmethod
    def resolve_type_alias(cls, type_str: str) -> str:
        """Resolve a type alias to its actual type
        
        Args:
            type_str: Type string that might be an alias
            
        Returns:
            The resolved actual type string
        """
        # Check if it's a simple alias
        if type_str in cls.TYPE_ALIASES:
            # Recursively resolve in case alias points to another alias
            return cls.resolve_type_alias(cls.TYPE_ALIASES[type_str])
        
        # Check if it's a generic type with aliases (e.g., "List[UserId]")
        # But skip special cases like "[]" which represents empty argument list
        if '[' in type_str and ']' in type_str and type_str != "[]":
            base_type, type_params = cls.parse_generic_type(type_str)
            
            # Resolve base type alias
            resolved_base = cls.resolve_type_alias(base_type)
            
            # Resolve parameter aliases recursively
            resolved_params = []
            for param in type_params:
                resolved_params.append(cls.resolve_type_alias(param))
            
            # Reconstruct the type string
            if resolved_params:
                return f"{resolved_base}[{', '.join(resolved_params)}]"
            else:
                return resolved_base
        
        # Not an alias, return as-is
        return type_str
    
    @classmethod
    def get_type_name(cls, value: Any) -> str:
        """Get human-readable type name for a value"""
        if value is None:
            return "null"
        return type(value).__name__
    
    @classmethod
    def parse_union_type(cls, type_annotation: str) -> list:
        """Parse union types like 'int|str|bool' into list of types"""
        if '|' not in type_annotation:
            return [type_annotation.strip()]
        
        # Split on '|' and clean up whitespace
        return [t.strip() for t in type_annotation.split('|')]
    
    @classmethod
    def parse_generic_type(cls, type_annotation: str) -> tuple:
        """Parse generic types like 'List[int]' or 'Dict[str, int]' w/ cache"""
        # Check cache first
        if type_annotation in cls._PARSE_CACHE:
            cls._CACHE_STATS['parse_hits'] += 1
            return cls._PARSE_CACHE[type_annotation]
        
        cls._CACHE_STATS['parse_misses'] += 1
        
        if '[' not in type_annotation or ']' not in type_annotation:
            result = (type_annotation, [])
        else:
            # Extract base type and type parameters
            bracket_start = type_annotation.index('[')
            bracket_end = type_annotation.rindex(']')
            
            base_type = type_annotation[:bracket_start].strip()
            type_params_str = type_annotation[bracket_start + 1:bracket_end]
            
            # Split type parameters by comma, respecting nested brackets
            if not type_params_str.strip():
                result = (base_type, [])
            else:
                type_params = cls._split_type_params(type_params_str)
                result = (base_type, type_params)
        
        # Cache result (limit cache size to prevent memory issues)
        if len(cls._PARSE_CACHE) < 1000:
            cls._PARSE_CACHE[type_annotation] = result
            
        return result
    
    @classmethod
    def _split_type_params(cls, params_str: str) -> list:
        """Split type parameters by comma, respecting nested brackets"""
        params = []
        current_param = ""
        bracket_depth = 0
        
        for char in params_str:
            if char == '[':
                bracket_depth += 1
                current_param += char
            elif char == ']':
                bracket_depth -= 1
                current_param += char
            elif char == ',' and bracket_depth == 0:
                params.append(current_param.strip())
                current_param = ""
            else:
                current_param += char
        
        # Add the last parameter
        if current_param.strip():
            params.append(current_param.strip())
            
        return params
    
    @classmethod
    def validate_collection_type(cls, value: Any, base_type: str,
                                 type_params: list) -> bool:
        """Validate collection types with generic parameters"""
        # Normalize base type to lowercase for comparison
        base_type_lower = base_type.lower()
        
        # First check if the value is the right collection type
        if not cls.validate_single_type(value, base_type_lower):
            return False
        
        # If no type parameters, just check the base type
        if not type_params:
            return True
        
        # Handle Optional types (Optional[T] is equivalent to T|None)
        if base_type_lower == 'optional':
            if len(type_params) != 1:
                return True  # Skip validation for wrong param count
            if value is None:
                return True  # None is always valid for Optional
            # Validate against the inner type
            return cls.validate_type(value, type_params[0])
        
        # Validate type parameters based on collection type
        if base_type_lower == 'list':
            if len(type_params) != 1:
                return True  # Skip validation for wrong param count
            element_type = type_params[0]
            return all(cls.validate_type(item, element_type) for item in value)
        
        elif base_type_lower == 'dict':
            if len(type_params) != 2:
                return True  # Skip validation for wrong param count
            key_type, value_type = type_params
            keys_valid = all(cls.validate_type(k, key_type)
                             for k in value.keys())
            values_valid = all(cls.validate_type(v, value_type)
                               for v in value.values())
            return keys_valid and values_valid
        
        elif base_type_lower == 'set':
            if len(type_params) != 1:
                return True  # Skip validation for wrong param count
            element_type = type_params[0]
            return all(cls.validate_type(item, element_type) for item in value)
        
        elif base_type_lower == 'tuple':
            # For tuples, each position can have a different type
            if len(value) != len(type_params):
                return False
            return all(cls.validate_type(value[i], type_params[i])
                       for i in range(len(type_params)))
        
        elif base_type_lower in ('frozenset', 'set'):
            if len(type_params) != 1:
                return True  # Skip validation for wrong param count
            element_type = type_params[0]
            return all(cls.validate_type(item, element_type) for item in value)
        
        elif base_type_lower in ('sequence', 'iterable', 'collection',
                                 'container'):
            # These are abstract base classes that accept multiple types
            if len(type_params) == 1:
                element_type = type_params[0]
                # For sequences and iterables, validate each element
                if hasattr(value, '__iter__'):
                    return all(cls.validate_type(item, element_type)
                               for item in value)
            return True  # Basic type check already passed
        
        elif base_type_lower in ('mapping', 'mutablemapping'):
            # Dictionary-like types
            if len(type_params) == 2:
                key_type, value_type = type_params
                if hasattr(value, 'keys') and hasattr(value, 'values'):
                    keys_valid = all(cls.validate_type(k, key_type)
                                     for k in value.keys())
                    values_valid = all(cls.validate_type(v, value_type)
                                       for v in value.values())
                    return keys_valid and values_valid
            return True  # Basic type check already passed
        
        elif base_type_lower == 'callable':
            # For Callable[[arg_types], return_type] or
            # Callable[[], return_type]
            if not callable(value):
                return False
            
            # If no type parameters, just check if it's callable
            if not type_params:
                return True
            
            # Parse Callable type parameters: [[arg_types], return_type]
            if len(type_params) != 2:
                return True  # Skip validation for wrong param count
                
            arg_types_str, return_type = type_params
            
            # Extract argument types from [arg_types] format
            if not (arg_types_str.startswith('[') and
                    arg_types_str.endswith(']')):
                return True  # Skip validation for malformed arg types
                
            arg_types_inner = arg_types_str[1:-1].strip()
            if not arg_types_inner:
                expected_arg_count = 0
                arg_types = []
            else:
                arg_types = [t.strip() for t in arg_types_inner.split(',')]
                expected_arg_count = len(arg_types)
            
            # Try to inspect function signature if possible
            try:
                sig = inspect.signature(value)
                actual_arg_count = len([
                    p for p in sig.parameters.values()
                    if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                ])
                
                # Check argument count matches
                if actual_arg_count != expected_arg_count:
                    return False
                    
                # Note: We can't validate argument types or return type
                # without actually calling the function, so we just check
                # the signature structure
                return True
                
            except (ValueError, TypeError):
                # Can't inspect signature (e.g., built-in function)
                # Just validate it's callable
                return True
        
        # Unknown collection type - skip validation
        return True
    
    @classmethod
    def validate_type(cls, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type (supports union types)"""
        # Create cache key from value type and expected type for performance
        value_type = type(value).__name__
        cache_key = f"{value_type}:{expected_type}"
        
        # For immutable values, we can cache validation results
        if cls._is_cacheable_value(value):
            if cache_key in cls._VALIDATION_CACHE:
                cls._CACHE_STATS['validation_hits'] += 1
                return cls._VALIDATION_CACHE[cache_key]
            cls._CACHE_STATS['validation_misses'] += 1
        
        # Resolve type aliases first
        expected_type = cls.resolve_type_alias(expected_type)
        
        # Handle union types (e.g., "int|str|bool")
        if '|' in expected_type:
            union_types = cls.parse_union_type(expected_type)
            result = any(cls.validate_single_type(value, t)
                         for t in union_types)
        # Handle Union[...] syntax (e.g., "Union[int, str]")
        elif (expected_type.startswith('Union[') and
              expected_type.endswith(']')):
            base_type, type_params = cls.parse_generic_type(expected_type)
            # Validate against any of the union parameters
            result = any(cls.validate_single_type(value, t)
                         for t in type_params)
        else:
            result = cls.validate_single_type(value, expected_type)
        
        # Cache result for cacheable values (limit cache size)
        if (cls._is_cacheable_value(value) and
                len(cls._VALIDATION_CACHE) < 1000):
            cls._VALIDATION_CACHE[cache_key] = result
            
        return result
    
    @classmethod
    def validate_single_type(cls, value: Any, expected_type: str) -> bool:
        """Check if value matches a single expected type"""
        # Resolve type aliases first (for cases where union already resolved)
        expected_type = cls.resolve_type_alias(expected_type)
        
        # Handle generic types (e.g., "List[int]", "Dict[str, int]")
        if '[' in expected_type and ']' in expected_type:
            base_type, type_params = cls.parse_generic_type(expected_type)
            return cls.validate_collection_type(value, base_type, type_params)
        
        # Special handling for basic Callable type
        if expected_type.lower() == 'callable':
            return callable(value)
        
        # Special handling for Any type (accepts anything)
        if expected_type == 'Any':
            return True
        
        if expected_type not in cls.TYPE_MAP:
            # Unknown type - skip validation for now
            return True
            
        expected_python_type = cls.TYPE_MAP[expected_type]
        
        # Special handling for bool vs int (bool is subclass of int in Python)
        if expected_type == 'int' and isinstance(value, bool):
            return False  # bool should not match int type specifically
        elif expected_type == 'bool':
            return isinstance(value, bool)
        
        # Special handling for Number alias (int, float, complex)
        elif expected_type == 'Number':
            return (isinstance(value, (int, float, complex)) and
                    not isinstance(value, bool))
        
        # Special handling for Text alias (just str)
        elif expected_type == 'Text':
            return isinstance(value, str)
        
        # Handle tuple types for abstract base classes
        elif isinstance(expected_python_type, tuple):
            return isinstance(value, expected_python_type)
            
        return isinstance(value, expected_python_type)
    
    @classmethod
    def check_parameter(cls, param_name: str, value: Any, expected_type: str,
                        function_name: str = None):
        """Validate a function parameter"""
        # Resolve type alias for validation
        resolved_type = cls.resolve_type_alias(expected_type)
        
        if not cls.validate_type(value, expected_type):
            actual_type = cls.get_type_name(value)
            
            # Get configuration to determine behavior
            config = get_type_config()
            
            # Log the error
            logger = get_type_logger()
            logger.log_type_error(
                code="S-2000",
                fn_name=function_name or "unknown",
                param_name=param_name,
                spec=resolved_type,
                value_type=actual_type,
                mode=config.get_effective_mode().value,
                fix_tip=create_fix_tip("S-2000", resolved_type, actual_type)
            )
            
            # Only raise exception in ON mode
            if config.should_fail_on_error():
                raise TypeCheckAbort()  # Sentinel for CLI to handle
    
    @classmethod
    def check_return_value(cls, value: Any, expected_type: str,
                           function_name: str = None):
        """Validate a function return value"""
        # Resolve type alias for validation
        resolved_type = cls.resolve_type_alias(expected_type)
        
        if not cls.validate_type(value, expected_type):
            actual_type = cls.get_type_name(value)
            
            # Get configuration to determine behavior
            config = get_type_config()
            
            # Log the error
            logger = get_type_logger()
            logger.log_type_error(
                code="S-2001",
                fn_name=function_name or "unknown",
                param_name="return",
                spec=resolved_type,
                value_type=actual_type,
                mode=config.get_effective_mode().value,
                fix_tip=create_fix_tip("S-2001", resolved_type, actual_type)
            )
            
            # Only raise exception in ON mode
            if config.should_fail_on_error():
                raise TypeCheckAbort()  # Sentinel for CLI to handle


def check_types(func: Callable) -> Callable:
    """
    Decorator to add runtime type checking to Sona functions.
    
    Extracts type annotations and validates parameters and return values.
    Supports union types like 'int|str|bool'.
    """
    
    def _extract_type_string(type_annotation) -> str:
        """Extract type string from annotation (handles str/type objects)"""
        if isinstance(type_annotation, str):
            return type_annotation
        elif hasattr(type_annotation, '__name__'):
            return type_annotation.__name__
        elif hasattr(type_annotation, '__str__'):
            # Handle Union types and other complex annotations
            type_str = str(type_annotation)
            # Convert typing.Union[int, str] to int|str format
            if 'Union[' in type_str:
                # Extract types from Union[type1, type2, ...]
                import re
                union_match = re.search(r'Union\[(.*?)\]', type_str)
                if union_match:
                    types_str = union_match.group(1)
                    # Split on comma and extract type names
                    types = []
                    for t in types_str.split(','):
                        t = t.strip()
                        if '.' in t:  # Handle module.Type format
                            t = t.split('.')[-1]
                        types.append(t)
                    return '|'.join(types)
            return type_str
        return None
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Skip type checking if disabled globally
        if not TypeCheckingConfig.is_enabled():
            return func(*args, **kwargs)
        
        # Get function signature and annotations
        sig = inspect.signature(func)
        annotations = func.__annotations__
        
        # Bind arguments to parameters
        try:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
        except TypeError as e:
            # Re-raise parameter binding errors as-is
            raise e
        
        # Check parameter types
        for param_name, value in bound.arguments.items():
            if param_name in annotations:
                expected_type = annotations[param_name]
                type_str = _extract_type_string(expected_type)
                if type_str:
                    TypeChecker.check_parameter(param_name, value, type_str,
                                                func.__name__)
        
        # Call the original function
        result = func(*args, **kwargs)
        
        # Check return type
        return_annotation = annotations.get('return')
        if return_annotation:
            type_str = _extract_type_string(return_annotation)
            if type_str:
                TypeChecker.check_return_value(result, type_str, func.__name__)
        
        return result
    
    return wrapper


def typed_function(func: Callable) -> Callable:
    """Alias for check_types decorator - more Sona-like naming"""
    return check_types(func)


def optimized_check_types(func: Callable) -> Callable:
    """
    Performance-optimized type checker that respects global config.
    
    Skips type checking entirely when disabled globally.
    """
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not TypeCheckingConfig.is_enabled():
            # Skip all type checking when disabled
            return func(*args, **kwargs)
        
        return check_types(func)(*args, **kwargs)
    
    return wrapper


def enforce_callable(value: Any, spec: str, param_name: str = "func",
                     function_name: str = None) -> Any:
    """
    Enforce Callable type specification on a value with return type validation.
    
    This function validates a callable value against a Callable spec and
    returns a wrapper that validates return types at call time.
    
    Args:
        value: The value to validate (should be callable)
        spec: Callable specification (e.g., "Callable[[int, str], bool]")
        param_name: Name of the parameter for error messages
        function_name: Name of the calling function for error context
        
    Returns:
        The original callable (if spec is Callable[..., Any]) or a wrapped
        callable that validates return types
        
    Raises:
        CallableTypeValidationError: If validation fails
    """
    # Parse the Callable specification
    if not spec.startswith('Callable'):
        # Not a Callable spec, use regular validation
        if not TypeChecker.validate_type(value, spec):
            actual_type = TypeChecker.get_type_name(value)
            raise CallableTypeValidationError(
                param_name, spec, actual_type, value, function_name, "S-2100"
            )
        return value
    
    # Check if value is callable
    if not callable(value):
        actual_type = TypeChecker.get_type_name(value)
        raise CallableTypeValidationError(
            param_name, spec, actual_type, value, function_name, "S-2100"
        )
    
    # Handle basic Callable without parameters
    if spec == "Callable":
        return value
    
    # Parse Callable[...] specification
    try:
        base_type, type_params = TypeChecker.parse_generic_type(spec)
        if len(type_params) != 2:
            # Malformed spec, just check callability
            return value
            
        arg_spec, return_spec = type_params
        
        # Handle Callable[..., Any] - fast path with no validation
        if arg_spec == "..." and return_spec.lower() == "any":
            return value
            
        # Validate function signature against spec
        _validate_callable_signature(value, arg_spec, spec, param_name,
                                     function_name)
        
        # If return type is Any, no wrapping needed
        if return_spec.lower() == "any":
            return value
            
        # Wrap function to validate return type
        return _create_return_type_wrapper(value, return_spec, spec,
                                           param_name, function_name)
        
    except (ValueError, TypeError, AttributeError):
        # If parsing fails, just validate basic callability
        return value


def _validate_callable_signature(func: Any, arg_spec: str, full_spec: str,
                                 param_name: str, function_name: str):
    """Validate function signature against Callable argument specification"""
    # Create cache key for signature inspection
    func_id = id(func)
    cache_key = f"{func_id}:{arg_spec}"
    
    # Check signature cache
    if cache_key in TypeChecker._SIGNATURE_CACHE:
        TypeChecker._CACHE_STATS['signature_hits'] += 1
        cached_result = TypeChecker._SIGNATURE_CACHE[cache_key]
        if cached_result['error']:
            raise CallableTypeValidationError(
                param_name, full_spec, cached_result['actual'],
                func, function_name, cached_result['code']
            )
        return
    
    TypeChecker._CACHE_STATS['signature_misses'] += 1
    
    try:
        import inspect
        sig = inspect.signature(func)
        
        # Count positional parameters
        positional_params = [
            p for p in sig.parameters.values()
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        ]
        actual_arg_count = len(positional_params)
        
        # Check for variadic parameters
        has_varargs = any(p.kind == p.VAR_POSITIONAL
                          for p in sig.parameters.values())
        has_kwargs = any(p.kind == p.VAR_KEYWORD
                         for p in sig.parameters.values())
        
        if arg_spec == "...":
            # Spec allows any arguments - no validation needed
            # Cache success
            if len(TypeChecker._SIGNATURE_CACHE) < 1000:
                TypeChecker._SIGNATURE_CACHE[cache_key] = {'error': False}
            return
            
        # Parse expected argument count from [arg1, arg2, ...] format
        if not (arg_spec.startswith('[') and arg_spec.endswith(']')):
            # Cache success for malformed spec (skip validation)
            if len(TypeChecker._SIGNATURE_CACHE) < 1000:
                TypeChecker._SIGNATURE_CACHE[cache_key] = {'error': False}
            return  # Malformed spec
            
        arg_types_inner = arg_spec[1:-1].strip()
        if not arg_types_inner:
            expected_arg_count = 0
        else:
            expected_arg_count = len([t.strip() for t in
                                      arg_types_inner.split(',')])
        
        # Check argument count match
        if actual_arg_count != expected_arg_count:
            # Allow functions with *args/**kwargs if they can accept the count
            if not (has_varargs and actual_arg_count <= expected_arg_count):
                # Cache error
                error_data = {
                    'error': True,
                    'actual': f"function[{actual_arg_count} args]",
                    'code': "S-2101"
                }
                if len(TypeChecker._SIGNATURE_CACHE) < 1000:
                    TypeChecker._SIGNATURE_CACHE[cache_key] = error_data
                raise CallableTypeValidationError(
                    param_name, full_spec,
                    f"function[{actual_arg_count} args]",
                    func, function_name, "S-2101"
                )
        
        # Check for spec mismatch with variadic functions
        if (has_varargs or has_kwargs) and expected_arg_count > 0:
            # Function has variadics but spec expects fixed args
            # This is allowed if the function can handle the expected count
            pass
        
        # Cache success
        if len(TypeChecker._SIGNATURE_CACHE) < 1000:
            TypeChecker._SIGNATURE_CACHE[cache_key] = {'error': False}
            
    except (ValueError, TypeError):
        # Can't inspect signature - cache success (skip validation)
        if len(TypeChecker._SIGNATURE_CACHE) < 1000:
            TypeChecker._SIGNATURE_CACHE[cache_key] = {'error': False}


def _create_return_type_wrapper(func: Any, return_spec: str, full_spec: str,
                                param_name: str, function_name: str):
    """Create a wrapper that validates return type"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Call original function
        result = func(*args, **kwargs)
        
        # Validate return type
        if not TypeChecker.validate_type(result, return_spec):
            actual_return_type = TypeChecker.get_type_name(result)
            raise CallableTypeValidationError(
                param_name, full_spec,
                f"function returning {actual_return_type}",
                func, function_name, "S-2103"
            )
        
        return result
    
    return wrapper


__all__ = [
    'TypeValidationError',
    'ReturnTypeValidationError',
    'CallableTypeValidationError',
    'TypeChecker',
    'TypeCheckingConfig',
    'check_types',
    'typed_function',
    'optimized_check_types',
    'enforce_callable',
]
