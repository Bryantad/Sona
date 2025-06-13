import importlib.util
import importlib
import os
import math 
from lark import Lark, Transformer, Tree, Token, UnexpectedInput
from pathlib import Path
from sona.utils.debug import debug, warn, error

# Native module imports
from sona.stdlib import (
    env as env_module,
    time as time_module,
)

from sona.stdlib.native_stdin import native_stdin

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class SonaInterpreter(Transformer):
    def __init__(self):
        super().__init__()
        self.env = [{}]
        self.functions = {}
        self.modules = {}

        # Register native modules
        self.modules["native_stdin"] = native_stdin
        self.modules["env"] = {
            "get": env_module.get,
            "set": env_module.set,
        }
        self.modules["time"] = {
            "now": time_module.now,
            "sleep": time_module.sleep,
        }

        # Preload commonly used modules
        try:
            from sona.stdlib.utils.array.smod import array
            self.modules["array"] = array
            debug(f"Preloaded array module: {dir(array)}")
        except ImportError:
            debug("Could not preload array module")

    # IMPORT_SYSTEM_FIXES_APPLIED = True
    
    # TYPE_CONSISTENCY_FIXES_APPLIED = True
    
    # ENHANCED_ERROR_REPORTING_APPLIED = True

    def create_error_context(self, node, error_type, message):
        """Create rich error context with line/column information"""
        error_info = {
            'type': error_type,
            'message': message,
            'line': None,
            'column': None,
            'context': None
        }
        
        # Extract position information if available
        if hasattr(node, 'line'):
            error_info['line'] = node.line
        if hasattr(node, 'column'):
            error_info['column'] = node.column
        
        # Create formatted error message
        if error_info['line'] and error_info['column']:
            formatted_msg = f"{message} at line {error_info['line']}, column {error_info['column']}"
        else:
            formatted_msg = message
        
        return formatted_msg, error_info

    def handle_runtime_error(self, e, node=None, context=None):
        """Handle runtime errors with enhanced reporting"""
        error_type = type(e).__name__
        message = str(e)
        
        if node:
            formatted_msg, error_info = self.create_error_context(node, error_type, message)
        else:
            formatted_msg = f"{error_type}: {message}"
            error_info = {'type': error_type, 'message': message}
        
        # Add context information if available
        if context:
            formatted_msg += f" (Context: {context})"
        
        # Add suggestions based on error type
        suggestions = self.get_error_suggestions(error_type, message)
        if suggestions:
            formatted_msg += f"\nSuggestions: {', '.join(suggestions)}"
        
        debug(f"Enhanced error: {formatted_msg}")
        return formatted_msg

    def get_error_suggestions(self, error_type, message):
        """Get helpful suggestions based on error type"""
        suggestions = []
        
        if error_type == "NameError":
            if "not found" in message:
                suggestions.append("Check variable spelling")
                suggestions.append("Ensure variable is defined before use")
                suggestions.append("Check variable scope")
        elif error_type == "TypeError":
            if "not callable" in message:
                suggestions.append("Check if you meant to call a function")
                suggestions.append("Verify the object has the expected method")
            elif "convert" in message:
                suggestions.append("Check data types in the operation")
                suggestions.append("Consider explicit type conversion")
        elif error_type == "ValueError":
            if "expects" in message and "arguments" in message:
                suggestions.append("Check function parameter count")
                suggestions.append("Verify function signature")
        elif error_type == "ImportError":
            suggestions.append("Check module path")
            suggestions.append("Ensure module is installed")
            suggestions.append("Verify module exists in the expected location")
        
        return suggestions

    def enhanced_exception_handler(self, func):
        """Decorator for enhanced exception handling"""
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Extract node information from args if available
                node = None
                if args and hasattr(args[0], 'line'):
                    node = args[0]
                elif len(args) > 1 and hasattr(args[1], 'line'):
                    node = args[1]
                
                enhanced_msg = self.handle_runtime_error(e, node, func.__name__)
                raise type(e)(enhanced_msg) from e
        return wrapper

    def ensure_numeric_type(self, value):
        """Ensure a value is a proper numeric type with consistent rules"""
        if isinstance(value, (int, float)):
            return value
        elif isinstance(value, str):
            # Try to convert string to number
            try:
                # Check if it looks like an integer
                if '.' not in value and 'e' not in value.lower():
                    return int(value)
                else:
                    return float(value)
            except ValueError:
                raise TypeError(f"Cannot convert string '{value}' to number")
        elif isinstance(value, bool):
            # Convert boolean to integer (True -> 1, False -> 0)
            return int(value)
        else:
            raise TypeError(f"Cannot convert {type(value).__name__} to number")
    
    def perform_numeric_operation(self, op, left, right):
        """Perform numeric operation with consistent type handling"""
        debug(f"Numeric operation: {left} {op} {right}")
        
        # Ensure both operands are numeric
        try:
            left_num = self.ensure_numeric_type(left)
            right_num = self.ensure_numeric_type(right)
        except TypeError as e:
            raise TypeError(f"Type error in {op} operation: {str(e)}")
        
        # Perform the operation
        if op == '+':
            result = left_num + right_num
        elif op == '-':
            result = left_num - right_num
        elif op == '*':
            result = left_num * right_num
        elif op == '/':
            if right_num == 0:
                raise ZeroDivisionError("Division by zero")
            result = left_num / right_num
        elif op == '%':
            if right_num == 0:
                raise ZeroDivisionError("Modulo by zero")
            result = left_num % right_num
        elif op == '**' or op == '^':
            result = left_num ** right_num
        else:
            raise ValueError(f"Unknown numeric operation: {op}")
        
        debug(f"Numeric operation result: {result} (type: {type(result).__name__})")
        return result

    def perform_comparison_operation(self, op, left, right):
        """Perform comparison operation with consistent type handling"""
        debug(f"Comparison operation: {left} {op} {right}")
        
        # Handle numeric comparisons
        if isinstance(left, (int, float, str)) and isinstance(right, (int, float, str)):
            try:
                left_num = self.ensure_numeric_type(left)
                right_num = self.ensure_numeric_type(right)
                
                if op == '<':
                    return left_num < right_num
                elif op == '<=':
                    return left_num <= right_num
                elif op == '>':
                    return left_num > right_num
                elif op == '>=':
                    return left_num >= right_num
                elif op == '==' or op == '=':
                    return left_num == right_num
                elif op == '!=' or op == '<>':
                    return left_num != right_num
                else:
                    raise ValueError(f"Unknown comparison operation: {op}")
                    
            except TypeError:
                # Fall back to string comparison if numeric conversion fails
                if op == '==' or op == '=':
                    return str(left) == str(right)
                elif op == '!=' or op == '<>':
                    return str(left) != str(right)
                else:
                    return str(left) < str(right) if op == '<' else str(left) > str(right)
        
        # Direct comparison for same types
        if op == '==' or op == '=':
            return left == right
        elif op == '!=' or op == '<>':
            return left != right
        else:
            # For other comparisons, try direct comparison
            try:
                if op == '<':
                    return left < right
                elif op == '<=':
                    return left <= right
                elif op == '>':
                    return left > right
                elif op == '>=':
                    return left >= right
            except TypeError:
                raise TypeError(f"Cannot compare {type(left).__name__} and {type(right).__name__}")

    def enhanced_import_module(self, module_path, alias=None):
        """Enhanced module import with better error handling and path resolution"""
        debug(f"Enhanced import: {module_path} (alias: {alias})")
        
        # Handle cross-platform path resolution
        if os.name == 'nt':  # Windows
            module_path = module_path.replace('/', '\\')
        else:  # Unix-like systems
            module_path = module_path.replace('\\', '/')
        
        # Resolve absolute vs relative paths
        if module_path.startswith('.'):
            # Relative import - resolve from current directory
            current_dir = Path.cwd()
            resolved_path = current_dir / module_path.lstrip('.')
        else:
            # Absolute import - resolve from stdlib or current directory
            stdlib_path = Path(__file__).parent / 'stdlib' / module_path
            if stdlib_path.exists():
                resolved_path = stdlib_path
            else:
                resolved_path = Path(module_path)
        
        # Module caching with reload capability
        cache_key = str(resolved_path)
        if cache_key in self.modules and not os.environ.get('SONA_RELOAD_MODULES'):
            debug(f"Using cached module: {cache_key}")
            return self.modules[cache_key]
        
        # Load module with comprehensive error handling
        try:
            module = self._load_module_safe(resolved_path)
            
            # Store in cache
            self.modules[cache_key] = module
            
            # Handle aliasing with proper scope isolation
            if alias:
                # Prevent scope pollution by using proper scoping
                if alias in self.env[-1]:
                    warn(f"Module alias '{alias}' shadows existing variable")
                self.env[-1][alias] = module
                debug(f"Module '{module_path}' imported as '{alias}'")
            else:
                # Use the module name as the identifier
                module_name = Path(module_path).stem
                self.env[-1][module_name] = module
                debug(f"Module '{module_path}' imported as '{module_name}'")
            
            return module
            
        except Exception as e:
            error_msg = f"Failed to import module '{module_path}': {str(e)}"
            debug(error_msg)
            raise ImportError(error_msg)
    
    def _load_module_safe(self, module_path):
        """Safely load a module with comprehensive error handling"""
        try:
            # Try Python module loading first
            spec = importlib.util.spec_from_file_location("sona_module", module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
            else:
                raise ImportError(f"Could not load module spec for {module_path}")
                
        except Exception as py_error:
            debug(f"Python module loading failed: {py_error}")
            
            # Try Sona module loading
            try:
                if module_path.suffix == '.sona':
                    return self._load_sona_module(module_path)
                else:
                    raise ImportError(f"Unsupported module type: {module_path}")
            except Exception as sona_error:
                debug(f"Sona module loading failed: {sona_error}")
                raise ImportError(f"All module loading attempts failed: Python({py_error}), Sona({sona_error})")
    
    def _load_sona_module(self, module_path):
        """Load a .sona module file"""
        debug(f"Loading Sona module: {module_path}")
        
        # Read the module file
        with open(module_path, 'r', encoding='utf-8') as f:
            module_code = f.read()
        
        # Create a separate interpreter instance for the module
        module_interpreter = SonaInterpreter()
        
        # Parse and execute the module
        grammar_path = Path(__file__).parent / 'grammar.lark'
        with open(grammar_path, 'r') as f:
            grammar = f.read()
        
        from lark import Lark
        parser = Lark(grammar, parser='lalr', propagate_positions=True)
        tree = parser.parse(module_code)
        
        # Execute module in its own environment
        module_interpreter.transform(tree)
        
        # Return the module's global environment as the module object
        return module_interpreter.env[0]

    def push_scope(self):
        self.env.append({})

    def pop_scope(self):
        self.env.pop()

    def set_var(self, name, value):
        self.env[-1][name] = value

    def get_var(self, name):
        for scope in reversed(self.env):
            if name in scope:
                return scope[name]
        raise NameError(f"Variable '{name}' not found")

    def var(self, args):
        # Simple variable name
        if isinstance(args[0], Token):
            name = str(args[0])
            
            # [BUG FIX] First prioritize current scope for function parameters
            # This ensures function parameters are found before outer scope variables
            if len(self.env) > 1 and name in self.env[-1]:
                debug(f"[FIXED] Found parameter '{name}' = {self.env[-1][name]} in function scope")
                return self.env[-1][name]
            
            # Debug all available scopes to diagnose any issues
            all_scopes = []
            for i, scope in enumerate(self.env):
                all_scopes.append(f"Scope {i}: {list(scope.keys())}")
            debug(f"Looking for variable '{name}' in scopes: {all_scopes}")
            
            # Then check other scopes in reverse order (inner to outer)
            for scope in reversed(self.env):
                if name in scope:
                    debug(f"Found variable '{name}' = {scope[name]}")
                    return scope[name]
            
            # Extra debug for function parameters
            debug(f"Variable '{name}' not found in any scope. Current env stack has {len(self.env)} scopes")
            if len(self.env) > 1:
                debug(f"Function local scope: {self.env[-1]}")
            
            # If not found, improve error message with line and column information
            if hasattr(args[0], 'line') and hasattr(args[0], 'column'):
                line, column = args[0].line, args[0].column
                raise NameError(f"Variable '{name}' not found at line {line}, column {column}")
            else:
                raise NameError(f"Variable '{name}' not found")
        
        # [FINAL FIX] Enhanced function parameter resolution
        # Check current function scope first (most local scope)
        if len(self.env) > 1:  # We're in a function
            current_scope = self.env[-1]
            if name in current_scope:
                debug(f"[PARAM FIX] Found '{name}' = {current_scope[name]} in function scope")
                return current_scope[name]
        
        # Dotted name (e.g. module.attribute)
        elif isinstance(args[0], Tree) and args[0].data == "dotted_name":
            name_parts = [str(t) for t in args[0].children]
            
            # First part must be a variable or module
            obj_name = name_parts[0]
            
            # Try to resolve the object (variable or module)
            try:
                obj = self.get_var(obj_name)
            except NameError:
                # Check if it's a function parameter in current scope
                if len(self.env) > 1 and obj_name in self.env[-1]:
                    obj = self.env[-1][obj_name]
                else:
                    # Improve error message with line and column information if possible
                    if hasattr(args[0].children[0], 'line') and hasattr(args[0].children[0], 'column'):
                        line, column = args[0].children[0].line, args[0].children[0].column
                        raise NameError(f"Variable '{obj_name}' not found at line {line}, column {column}")
                    else:
                        raise NameError(f"Variable '{obj_name}' not found")
            
            # Access nested attributes
            for attr in name_parts[1:]:
                if hasattr(obj, attr):
                    obj = getattr(obj, attr)
                elif isinstance(obj, dict) and attr in obj:
                    obj = obj[attr]
                else:
                    # Improve error message with line and column information
                    attr_idx = name_parts.index(attr)
                    if attr_idx < len(args[0].children) and hasattr(args[0].children[attr_idx], 'line'):
                        line, column = args[0].children[attr_idx].line, args[0].children[attr_idx].column
                        raise AttributeError(f"'{obj_name}' has no attribute '{attr}' at line {line}, column {column}")
                    else:
                        raise AttributeError(f"'{obj_name}' has no attribute '{attr}'")
            
            return obj
        else:
            # Handle unexpected input
            name = str(args[0])
            raise ValueError(f"Invalid variable reference: {name}")

    def eval_arg(self, arg):
        # For debugging
        debug(f"Evaluating argument: {type(arg)} - {arg}")
        
        if isinstance(arg, (Tree, Token)):
            try:
                result = self.transform(arg)
                debug(f"Evaluated argument result: {result}")
                return result
            except Exception as e:
                # Add context about the argument being evaluated
                if hasattr(arg, 'line') and hasattr(arg, 'column'):
                    debug(f"Error evaluating argument at line {arg.line}, column {arg.column}: {e}")
                raise
        else:
            return arg

    def array(self, args):
        """Handle array literals like [1, 2, 3]"""
        if not args:
            return []
        if isinstance(args[0], list):
            # Already evaluated list, return as is
            return args[0]
        if hasattr(args[0], 'children'):
            # Parse array items from AST
            return [self.eval_arg(item) for item in args[0].children]
        return [self.eval_arg(item) for item in args]
    
    def array_literal(self, args):
        """Handle array literal syntax by creating a flat list"""
        return self.array(args)
    
    def array_items(self, args):
        """Process array items into a flat list"""
        return [self.eval_arg(item) for item in args]

    def neg(self, args):
        return -self.eval_arg(args[0])

    def pos(self, args):
        return +self.eval_arg(args[0])

    def not_op(self, args):
        return not self.eval_arg(args[0])

    def _eval(self, node):
        return self.transform(node)

    def _exec(self, node):
        if isinstance(node, Tree):
            return self.transform(node)
        elif isinstance(node, list):
            result = None
            for n in node:
                result = self._exec(n)
            return result
        else:
            return node

    def import_stmt(self, args):
        # Extract module path and check for alias
        alias = None
        module_parts = []
        i = 0

        # First pass: Identify if there is an 'as' keyword and extract the alias
        for j in range(len(args)):
            if args[j] is not None and str(args[j]) == "as" and j + 1 < len(args):
                alias = str(args[j + 1])
                break

        # Second pass: Extract module parts (stopping at 'as' if present)
        while i < len(args):
            if args[i] is None:
                i += 1
                continue
                
            current = str(args[i])
            if current == "as":
                # Stop collecting module parts when we hit 'as'
                break
            else:
                module_parts.append(current)
            i += 1
        
        module_name = ".".join(module_parts)
        debug(f"Importing module: {module_name}")
        if alias:
            debug(f"Using alias: {alias}")

        try:
            # Normalize module path parts
            module_parts = module_name.split(".")
            base_name = ""
            
            # For .smod file imports
            if module_name.endswith("smod"):
                # Get the proper base name (e.g., array from utils.array.smod)
                if len(module_parts) > 1:
                    base_name = module_parts[-2]
                else:
                    base_name = module_parts[0].replace(".smod", "")
                    
                # Convert to Python module path
                py_module = "sona.stdlib." + module_name
            else:
                # For regular imports
                py_module = "sona.stdlib." + module_name
                base_name = module_parts[-1]
            
            # Store original name for module lookup
            original_name = base_name
            # Use alias for registration if provided
            register_name = alias if alias else base_name
            
            debug(f"Loading module from {py_module}")
            debug(f"Original name: {original_name}, Register name: {register_name}")
            debug(f"Python module path: {py_module}")
            
            # Ensure the module exists using platform-independent paths
            base_path = Path(__file__).parent  # sona directory
            stdlib_path = Path(base_path).parent / 'stdlib'  # top-level stdlib directory
            
            # Special handling for utils.math.smod pattern
            if "utils" in module_parts and "smod" in module_parts:
                # Recalculate the Python module path for utils.math.smod pattern
                utils_index = module_name.find("utils")
                smod_index = module_name.find("smod")
                
                if utils_index >= 0 and smod_index > utils_index:
                    # Get the module between utils and smod (e.g., "math" in utils.math.smod)
                    module_between = module_name[utils_index+6:smod_index-1]  # -1 to remove the dot
                    if module_between:
                        debug(f"Special case: utils.{module_between}.smod pattern detected")
                        py_module = f"sona.stdlib.utils.{module_between}.smod"
                        # Update base name to use the module between utils and smod
                        base_name = module_between
                        original_name = base_name
                        if not alias:
                            register_name = base_name
            
            # Try finding module in both standard locations
            found_module = False
            module_path = None
            
            # Use the proper last module part
            last_module_part = module_parts[-1]
            
            # Determine paths to search based on module structure
            search_paths = []
            
            # Standard paths (for all imports)
            # Path 1: Inside sona/stdlib/...
            search_paths.append(base_path / 'stdlib' / Path(*module_parts[:-1]) / f"{last_module_part}.py")
            search_paths.append(base_path / 'stdlib' / Path(*module_parts[:-1]) / f"{last_module_part}.smod")
            
            # Path 2: In top-level stdlib/...
            search_paths.append(stdlib_path / Path(*module_parts[:-1]) / f"{last_module_part}.py")
            search_paths.append(stdlib_path / Path(*module_parts[:-1]) / f"{last_module_part}.smod")
            
            # Path 3: Direct access in top-level stdlib
            search_paths.append(stdlib_path / f"{module_name}.py")
            search_paths.append(stdlib_path / f"{module_name}.smod")
            
            # Path 4: Check for special case of utils.*.smod modules
            if "utils" in module_parts and "smod" in module_parts:
                utils_index = module_parts.index("utils")
                smod_index = module_parts.index("smod")
                
                if smod_index > utils_index:
                    # Handle the case where we have a path like utils.math.smod
                    # by creating utils/math/smod.py search path
                    search_paths.append(base_path / 'stdlib' / 'utils' / 
                                       Path(*module_parts[utils_index+1:smod_index]) / "smod.py")
                    search_paths.append(stdlib_path / 'utils' / 
                                       Path(*module_parts[utils_index+1:smod_index]) / "smod.py")
            
            for path in search_paths:
                debug(f"Checking path: {path}")
                if path.is_file():
                    module_path = path
                    found_module = True
                    debug(f"Found module at: {module_path}")
                    break
                    
            if not found_module:
                raise ImportError(f"Module file not found. Checked paths: {', '.join(str(p) for p in search_paths)}")
            
            mod = importlib.import_module(py_module)
            
            # Try to find the module instance
            instance = None
            
            # First check if module exports the instance directly
            if hasattr(mod, original_name):
                instance = getattr(mod, original_name)
                debug(f"Found instance directly: {type(instance)}")
            # Then check __all__ and look for any attributes mentioned there
            elif hasattr(mod, "__all__"):
                all_attrs = getattr(mod, "__all__")
                debug(f"Module __all__ attributes: {all_attrs}")
                # Check each attribute in __all__
                for attr_name in all_attrs:
                    if hasattr(mod, attr_name):
                        instance = getattr(mod, attr_name)
                        debug(f"Found instance via __all__ -> {attr_name}: {type(instance)}")
                        break
            # Try matching by any case
            elif hasattr(mod, original_name.lower()):
                instance = getattr(mod, original_name.lower())
                debug(f"Found instance by lowercase: {type(instance)}")
            # Check if 'math' is specifically available (common case)
            elif hasattr(mod, "math"):
                instance = getattr(mod, "math")
                debug(f"Found instance via 'math' attribute: {type(instance)}")
            # Finally check the smod.py file directly
            else:
                smod_module = f"{py_module}.smod"
                debug(f"Trying smod module: {smod_module}")
                try:
                    smod = importlib.import_module(smod_module)
                    if hasattr(smod, original_name):
                        instance = getattr(smod, original_name)
                        debug(f"Found instance in smod.py: {type(instance)}")
                except ImportError:
                    pass
                    
            if instance is not None:
                debug(f"Registering instance as '{register_name}'")
                debug(f"Available methods: {dir(instance)}")
                
                # Register under the alias name if provided, otherwise use original name
                self.modules[register_name] = instance
                self.set_var(register_name, instance)
                debug(f"Module registered successfully as '{register_name}'")
            else:
                debug(f"No instance found, using module: {mod}")
                self.modules[register_name] = mod
                self.set_var(register_name, mod)
                
            return True
        except ImportError as e:
            raise ImportError(f"Failed to import module '{module_name}': {str(e)}")
        except Exception as e:
            raise ImportError(f"Unexpected error importing '{module_name}': {str(e)}")
    
    def add(self, args):
        left = self.eval_arg(args[0])
        right = self.eval_arg(args[1])
        if hasattr(self, 'perform_numeric_operation'):
            return self.perform_numeric_operation('+', left, right)
        return left + right

    def sub(self, args): 
        left = self.eval_arg(args[0])
        right = self.eval_arg(args[1])
        if hasattr(self, 'perform_numeric_operation'):
            return self.perform_numeric_operation('-', left, right)
        return left - right

    def mul(self, args): 
        left = self.eval_arg(args[0])
        right = self.eval_arg(args[1])
        if hasattr(self, 'perform_numeric_operation'):
            return self.perform_numeric_operation('*', left, right)
        return left * right

    def div(self, args): 
        left = self.eval_arg(args[0])
        right = self.eval_arg(args[1])
        if hasattr(self, 'perform_numeric_operation'):
            return self.perform_numeric_operation('/', left, right)
        return left / right

    def number(self, args): 
        return float(args[0])
        
    def string(self, args):
        # Handle both single/double quoted strings and multi-line strings
        raw_str = str(args[0])
        
        # Triple-quoted strings (multi-line)
        if raw_str.startswith('"""') and raw_str.endswith('"""'):
            return raw_str[3:-3]
        elif raw_str.startswith("'''") and raw_str.endswith("'''"):
            return raw_str[3:-3]
        # Regular single/double quoted strings
        elif raw_str.startswith('"') and raw_str.endswith('"'):
            return raw_str[1:-1]
        elif raw_str.startswith("'") and raw_str.endswith("'"):
            return raw_str[1:-1]
        
        # Fallback
        return raw_str

    def assignment(self, args):
        name_token, value_expr = args
        value = self.eval_arg(value_expr)
        self.set_var(str(name_token), value)
        return value

    def print_stmt(self, args):
        val = self.eval_arg(args[0])
        # print() without [OUTPUT] prefix for cleaner output
        print(val)
        return val

    def func_call(self, args):
        # Extract function name and arguments
        name_node = args[0]
        passed_args = []
        if len(args) > 1 and isinstance(args[1], Tree) and args[1].data == "args":
            # Store the argument values
            passed_args = []
            for a in args[1].children:
                try:
                    val = self.eval_arg(a)
                    passed_args.append(val)
                except Exception as e:
                    if hasattr(a, 'line') and hasattr(a, 'column'):
                        line, column = a.line, a.column
                        raise type(e)(f"{str(e)} at line {line}, column {column}")
                    else:
                        raise
            
            # Enhanced debugging for function arguments            
            debug(f"Evaluated function arguments: {passed_args}")
            debug(f"Current environment stack before function call: {len(self.env)} scopes")

        # Handle dotted calls (module.method)
        if isinstance(name_node, Tree) and name_node.data == "dotted_name":
            name_parts = [str(t.value) if isinstance(t, Token) else str(t) for t in name_node.children]
            obj_name, method_name = name_parts[0], name_parts[-1]
            
            # Resolve the object (could be a module or a variable)
            if obj_name in self.modules:
                obj = self.modules[obj_name]
            else:
                # Try to find it in variables
                try:
                    obj = self.get_var(obj_name)
                except NameError:
                    # Add line and column information if available
                    if hasattr(name_node.children[0], 'line') and hasattr(name_node.children[0], 'column'):
                        line, column = name_node.children[0].line, name_node.children[0].column
                        raise NameError(f"Module or variable '{obj_name}' not found at line {line}, column {column}")
                    else:
                        raise NameError(f"Module or variable '{obj_name}' not found")

            # For nested paths (e.g., pkg.submodule.func), traverse the path
            current = obj
            for part in name_parts[1:-1]:  # Skip first and last parts
                if hasattr(current, part):
                    current = getattr(current, part)
                elif isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    raise AttributeError(f"Cannot access '{part}' in '{obj_name}'")
            
            # Now try to get the actual method
            if hasattr(current, method_name):
                method = getattr(current, method_name)
                if callable(method):
                    return method(*passed_args)
                else:
                    raise TypeError(f"'{method_name}' is not callable")
            elif isinstance(current, dict) and method_name in current:
                method = current[method_name]
                if callable(method):
                    return method(*passed_args)
                else:
                    raise TypeError(f"'{method_name}' is not callable")
            else:
                # Add line and column information if available
                method_token_index = len(name_parts) - 1
                if method_token_index < len(name_node.children) and hasattr(name_node.children[method_token_index], 'line'):
                    line, column = name_node.children[method_token_index].line, name_node.children[method_token_index].column
                    raise AttributeError(f"'{obj_name}' has no method '{method_name}' at line {line}, column {column}")
                else:
                    raise AttributeError(f"'{obj_name}' has no method '{method_name}'")

        # Handle regular function calls
        name = str(name_node)
        if name not in self.functions:
            # Add line and column information if available
            if hasattr(name_node, 'line') and hasattr(name_node, 'column'):
                line, column = name_node.line, name_node.column
                raise NameError(f"Function '{name}' not defined at line {line}, column {column}")
            else:
                raise NameError(f"Function '{name}' not defined")

        params, body = self.functions[name]
        if len(params) != len(passed_args):
            # Add line and column information if available
            if hasattr(name_node, 'line') and hasattr(name_node, 'column'):
                line, column = name_node.line, name_node.column
                raise ValueError(f"Function '{name}' expects {len(params)} arguments, got {len(passed_args)} at line {line}, column {column}")
            else:
                # [BUG FIX] More informative parameter mismatch errors
                param_names = [str(p) for p in params]
                error_msg = f"Function '{name}' expects {len(params)} arguments {param_names}, got {len(passed_args)}: {passed_args}"
                raise ValueError(error_msg)

        # Create a new scope for function execution
        self.push_scope()
        
        # Add each parameter to the function scope with its value
        for i, (param, value) in enumerate(zip(params, passed_args)):
            param_name = str(param)
            debug(f"Setting function parameter {i}: {param_name} = {value}")
            # [BUG FIX] Enhanced parameter setting with verification
            self.env[-1][param_name] = value
            # Verify parameter was set correctly for debugging
            if param_name in self.env[-1]:
                debug(f"[FIXED] Parameter {param_name} = {value} set in scope {len(self.env)-1}")
            else:
                debug(f"[ERROR] Failed to set parameter {param_name}!")
        
        # Debug the function scope contents after setting parameters
        scope_contents = ", ".join([f"{k}={v}" for k, v in self.env[-1].items()])
        debug(f"Function '{name}' scope parameters: {scope_contents}")
        
        # Ensure function parameters are visible to debug
        debug(f"Current environment after parameter setting: {self.env}")

        try:
            # Execute the function body statements directly
            result = None
            
            # Debug function scope before execution
            param_names = [str(p) for p in params]
            debug(f"Executing function '{name}' with params: {param_names}")
            debug(f"Variables in function scope: {list(self.env[-1].keys())}")
              # Process each statement in the function body
            for child in body.children:
                debug(f"Executing statement: {type(child)} - {child}")
                
                # Special handling for function return statements
                if isinstance(child, Tree) and child.data == 'return_stmt':
                    debug(f"Processing return statement")
                    # Handle return statement directly without going through transform
                    if child.children:
                        result = self.eval_arg(child.children[0])
                        debug(f"Return statement with value: {result}")
                        self.pop_scope()
                        return result
                    else:
                        debug("Return statement with no value")
                        self.pop_scope()
                        return None
                else:
                    # For all other statements
                    result = self.transform(child)
                    debug(f"Statement result: {result}")
            
            debug(f"Function execution completed with result: {result}")
            self.pop_scope()
            return result
        except ReturnSignal as r:
            debug(f"Function '{name}' returned value: {r.value}")
            self.pop_scope()
            return r.value
        except Exception as e:            
            # Get function location information if available
            line_info = ""
            if hasattr(name_node, 'line') and hasattr(name_node, 'column'):
                line_info = f" at line {name_node.line}, column {name_node.column}"
            
            # Create a more informative error message with current scope
            scope_vars = ", ".join(f"{k}" for k in self.env[-1].keys()) if self.env else "no scope"
            error_msg = f"Error in function '{name}'{line_info}: {str(e)}\nCurrent scope variables: {scope_vars}"
            debug(error_msg)
            self.pop_scope()
            # Just raise the original exception to avoid VisitError construction issues
            raise e

    def func_def(self, args):
        """Handle function definition - store function without executing body"""
        name_token = args[0]
        func_name = str(name_token)
        
        # Extract parameters
        params = []
        if len(args) > 1 and args[1] is not None:
            if isinstance(args[1], list):
                params = args[1]  # Already processed by param_list
            elif hasattr(args[1], 'children'):
                for child in args[1].children:
                    if isinstance(child, Token) and child.type == 'NAME':
                        params.append(child)
        
        # Extract body (do NOT execute it)
        body = args[-1]
        
        # Store function definition for later execution
        debug(f"Storing function '{func_name}' with parameters: {[str(p) for p in params]}")
        self.functions[func_name] = (params, body)
        
        return func_name

    def param_list(self, args):
        # Process parameter list by collecting just the variable names
        # Skip commas and other tokens
        params = []
        for arg in args:
            if isinstance(arg, Token) and arg.type == 'NAME':
                params.append(arg)
                debug(f"Added parameter name: {arg}")
        debug(f"Complete param list: {[str(p) for p in params]}")
        return params

    def return_stmt(self, args):
        if args:
            # Evaluate the return expression in the current scope
            debug(f"Processing return statement with expression: {args[0]}")
            value = self.eval_arg(args[0])
            debug(f"Return statement with value: {value}")
            raise ReturnSignal(value)
        else:
            debug("Return statement with no value")
            raise ReturnSignal(None)

    def if_stmt(self, args):
        condition = self.eval_arg(args[0])
        
        if condition:
            # Execute the "then" block
            debug("If condition is true, executing then block")
            self.push_scope()
            result = self._exec(args[1].children)
            self.pop_scope()
            return result
        elif len(args) > 2:  # Has an "else" block
            # Execute the "else" block
            debug("If condition is false, executing else block")
            self.push_scope()
            result = self._exec(args[2].children)
            self.pop_scope()
            return result
            
        return None

    def while_stmt(self, args):
        condition_expr, body = args
        
        while self.eval_arg(condition_expr):
            self.push_scope()
            try:
                self._exec(body.children)
            except ReturnSignal:
                # If a return statement is encountered, propagate it
                self.pop_scope()
                raise
            finally:
                self.pop_scope()
        
        return None

    def for_stmt(self, args):
        var_name, start_expr, end_expr, body = args
        
        start = self.eval_arg(start_expr)
        end = self.eval_arg(end_expr)
        
        for i in range(int(start), int(end) + 1):
            self.push_scope()
            self.set_var(str(var_name), i)
            
            try:
                self._exec(body.children)
            except ReturnSignal:
                # If a return statement is encountered, propagate it
                self.pop_scope()
                raise
            finally:
                self.pop_scope()
                
        return None

    def block(self, args):
        return args

    def start(self, args):
        """Two-pass execution: first extract functions, then execute statements"""
        debug("Starting two-pass execution...")
        
        # Pass 1: Extract all function definitions without executing them
        debug("Pass 1: Extracting function definitions...")
        for stmt in args:
            if isinstance(stmt, Tree) and stmt.data == 'func_def':
                self._extract_function_definition(stmt)
        
        # Pass 2: Execute all non-function statements
        debug("Pass 2: Executing statements...")
        result = None
        for stmt in args:
            if not (isinstance(stmt, Tree) and stmt.data == 'func_def'):
                result = self._exec(stmt)
        
        # Return the result of the last expression/statement
        return result

    def _extract_function_definition(self, func_tree):
        """Extract function definition from raw tree without transforming body"""
        debug(f"Extracting function definition from: {func_tree}")
        
        # Extract function name (first child)
        name_token = func_tree.children[0]
        func_name = str(name_token)
        
        # Extract parameters (second child, if exists)
        params = []
        if len(func_tree.children) > 1 and func_tree.children[1] is not None:
            param_tree = func_tree.children[1]
            if isinstance(param_tree, Tree) and param_tree.data == 'param_list':
                for child in param_tree.children:
                    if isinstance(child, Token) and child.type == 'NAME':
                        params.append(child)
        
        # Extract body (last child) - keep as raw tree for later execution
        body = func_tree.children[-1]
        
        # Store function definition with raw body
        param_names = [str(p) for p in params]
        debug(f"Extracted function '{func_name}' with parameters: {param_names}")
        self.functions[func_name] = (params, body)
        
        return func_name

# Global debug mode function for REPL
def debug_mode(enabled=True):
    """Enable or disable debug mode globally"""
    import os
    if enabled:
        os.environ["SONA_DEBUG"] = "1"
    else:
        os.environ.pop("SONA_DEBUG", None)


def load_smod_module(module_name):
    """Load a .smod module in a platform-independent way"""
    try:
        # Convert module name to path parts
        path_parts = ['sona', 'stdlib'] + module_name.split('.')
        if path_parts[-1].endswith('.smod'):
            # Remove .smod extension and add .py
            path_parts[-1] = path_parts[-1][:-5]
        path_parts[-1] += '.py'
        
        # Create path object
        module_path = Path(*path_parts)
        
        if not module_path.is_file():
            raise ImportError(f"No backend found for module '{module_name}'")
            
        # Create module spec using absolute path
        spec = importlib.util.spec_from_file_location(
            f"sona.stdlib.{module_name}",
            str(module_path.resolve())
        )
        
        if spec is None or spec.loader is None:
            raise ImportError(f"Failed to create module spec for '{module_name}'")
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
        
    except Exception as e:
        raise ImportError(f"Failed to load module '{module_name}': {str(e)}")

def run_code(code, debug_enabled=False):
    """Execute Sona code with proper cross-platform path handling"""
    if debug_enabled:
        os.environ["SONA_DEBUG"] = "1"
        
    debug("run_code() received input:")
    debug(code[:100])
    
    # Get grammar file path in a platform-independent way
    grammar_path = Path(__file__).parent / 'grammar.lark'
    try:
        grammar = grammar_path.read_text(encoding='utf-8')
    except Exception as e:
        error(f"Failed to load grammar: {e}")
        return None

    parser = Lark(grammar, parser="lalr", propagate_positions=True)
    try:
        tree = parser.parse(code)
    except UnexpectedInput as e:
        line_num = e.line
        column = e.column
        # Extract the line with the error and add ^ marker        error_line = code.split('\n')[line_num-1] if line_num <= len(code.split('\n')) else ""
        pointer = ' ' * (column - 1) + '^'
        error(f"PARSER ERROR at line {line_num}, column {column}:\n{error_line}\n{pointer}\n{str(e)}")
        return None
    except Exception as e:
        error(f"PARSER ERROR: {str(e)}")
        return None

    debug("Starting execution...")
    interpreter = SonaInterpreter()
    try:
        if os.environ.get("SONA_DEBUG") == "1":
            print(tree.pretty())
        # Use the two-pass start method instead of direct transform
        result = interpreter.start(tree.children)
        return result
    except NameError as e:
        # Extract line and column info if available from error message
        line_info = ""
        if "at line" in str(e):
            line_info = str(e)
        else:
            line_info = str(e)
        error(f"VARIABLE ERROR: {line_info}")
        return None
    except AttributeError as e:
        error(f"MODULE ERROR: {str(e)}")
        return None
    except TypeError as e:
        error(f"TYPE ERROR: {str(e)}")
        return None
    except ImportError as e:
        # Check if the error has position information
        if hasattr(e, 'line') and hasattr(e, 'column'):
            line_num, column = e.line, e.column
            error_line = code.split('\n')[line_num-1] if line_num <= len(code.split('\n')) else ""
            pointer = ' ' * (column - 1) + '^'
            error(f"IMPORT ERROR at line {line_num}, column {column}:\n{error_line}\n{pointer}\n{str(e)}")
        else:
            error(f"IMPORT ERROR: {str(e)}")
        return None
    except ValueError as e:
        error(f"VALUE ERROR: {str(e)}")
        return None
    except Exception as e:
        # Try to extract line and column info from the exception if possible
        if hasattr(e, 'line') and hasattr(e, 'column'):
            line_num, column = e.line, e.column
            error_line = code.split('\n')[line_num-1] if line_num <= len(code.split('\n')) else ""
            pointer = ' ' * (column - 1) + '^'
            error(f"INTERPRETER ERROR at line {line_num}, column {column}:\n{error_line}\n{pointer}\n{str(e)}")
        else:
            error(f"INTERPRETER ERROR: {str(e)}")
        return None

if __name__ == "__main__":
    test_files = [
        "examples/test_all_modules.sona",
    ]

    for file in test_files:
        try:
            code = Path(file).read_text()
            debug(f"Running: {file}")
            run_code(code)
            if os.environ.get("SONA_DEBUG") == "1":
                print("✅ Success\n")
        except Exception as e:
            error(f"Error in {file}: {e}\n")
        finally:
            if os.environ.get("SONA_DEBUG") == "1":
                print("-" * 40)
