import importlib.util
import importlib
import os

try:
    from lark import Lark, Transformer, Tree, Token
except ImportError as e:
    raise ImportError(
        "The 'lark' package is required but not installed. "
        "Please install it using: pip install lark"
    ) from e

from pathlib import Path
from sona.utils.debug import debug, error, warn

# Native module imports
from sona.stdlib import (
    env as env_module,
    time as time_module,
)

from sona.stdlib.native_stdin import native_stdin

# Import native function implementations
from sona.stdlib import (
    native_fs,
    native_http,
)

debug_mode = False

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class BreakSignal(Exception):
    pass

class ContinueSignal(Exception):
    pass

class SonaInterpreter(Transformer):
    def __init__(self):
        super().__init__()
        self.env = [{}]  # Stack of scopes, innermost scope at end
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
        
        # Register __native__ namespace with its modules
        self.modules["__native__"] = {}
        
        # Add file system native functions
        fs_natives = {
            "fs_exists": native_fs.fs_exists,
            "fs_delete": native_fs.fs_delete,
            "fs_rename": native_fs.fs_rename,
            "fs_mkdir": native_fs.fs_mkdir,
            "fs_list_dir": native_fs.fs_list_dir
        }
        
        # Add read/write functions if they exist
        if hasattr(native_fs, "fs_read_file"):
            fs_natives["fs_read_file"] = native_fs.fs_read_file
        if hasattr(native_fs, "fs_write_file"):
            fs_natives["fs_write_file"] = native_fs.fs_write_file
        if hasattr(native_fs, "fs_append_file"):
            fs_natives["fs_append_file"] = native_fs.fs_append_file
        self.modules["__native__"].update(fs_natives)
        
        # Add HTTP native functions
        http_natives = {
            "http": {
                "get": native_http.http_get,
                "post": native_http.http_post
            }
        }
        self.modules["__native__"].update(http_natives)

        # Preload commonly used modules
        try:
            from sona.stdlib.utils.array.smod import array
            self.modules["array"] = array
            debug(f"array module loaded")
        except ImportError:
            debug("Could not preload array module")

        # Add built-in functions
        self.builtin_functions = {
            "range", "isinstance", "len", "str", 
            "int", "float", "type", "max", "min", 
            "sum", "abs", "round", "sorted", "reversed"
        }
        
        # Add built-in types for isinstance
        self.builtin_types = {
            "list": list,
            "dict": dict, 
            "string": str,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool
        }

    def push_scope(self):
        """Push a new scope onto the scope stack"""
        debug(f"Pushing new scope (now at depth {len(self.env)+1})")
        self.env.append({})
        return self.env[-1]

    def pop_scope(self):
        """Pop the innermost scope from the stack"""
        if len(self.env) > 1:  # Always keep global scope
            debug(f"Popping scope (now at depth {len(self.env)-1})")
            return self.env.pop()
        debug("Cannot pop global scope")
        return None

    def get_current_scope(self):
        """Get the current (innermost) scope"""
        return self.env[-1]

    def set_var(self, name, value):
        """Set a variable in the current scope"""
        debug(f"Setting variable {name} = {value} in scope {len(self.env)-1}")
        self.env[-1][name] = value
        return value

    def find_var_scope(self, name):
        """Find which scope contains a variable, or None if not found"""
        # First check modules
        if name in self.modules:
            return self.modules

        # Then check scopes from most local to most global
        for scope in reversed(self.env):
            if name in scope:
                return scope
        return None

    def get_var(self, name):
        """Get a variable's value, checking all scopes"""
        # First check modules
        if name in self.modules:
            debug(f"Found module: {name}")
            return self.modules[name]

        # Then check scopes from most local to most global
        for i, scope in enumerate(reversed(self.env)):
            if name in scope:
                depth = len(self.env) - i - 1
                debug(f"Found variable {name} in scope {depth}")
                return scope[name]

        # Variable not found
        debug(f"Variable {name} not found in any scope")
        raise NameError(f"Variable '{name}' not found")

    def var(self, args):
        """Handle simple variable access"""
        if isinstance(args[0], Token):
            name = str(args[0])
            return self.get_var(name)
        return None

    def var_assign(self, args):
        """Handle let/const variable assignment"""
        if len(args) != 2:
            raise Exception("Invalid assignment")
        name = str(args[0])
        value = self.eval_arg(args[1])
        return self.set_var(name, value)

    def assign(self, args):
        """Handle normal variable assignment (without let/const)"""
        if len(args) != 2:
            raise Exception("Invalid assignment")
        name = str(args[0])
        value = self.eval_arg(args[1])
        scope = self.find_var_scope(name)
        if scope is None:
            raise Exception(f"Cannot assign to undeclared variable '{name}'")
        scope[name] = value
        return value

    def add(self, args): 
        a = self.eval_arg(args[0])
        b = self.eval_arg(args[1])
        
        # Special handling for string concatenation
        if isinstance(a, str) or isinstance(b, str):
            # Convert both to strings for concatenation
            return str(a) + str(b)
            
        # Normal arithmetic addition
        result = a + b
        return int(result) if isinstance(result, float) and result == int(result) else result
        
    def sub(self, args): 
        a = self.eval_arg(args[0])
        b = self.eval_arg(args[1])
        result = a - b
        return int(result) if isinstance(result, float) and result == int(result) else result
        
    def mul(self, args): 
        a = self.eval_arg(args[0])
        b = self.eval_arg(args[1])
        
        # Handle string multiplication (e.g. "a" * 3)
        if isinstance(a, str) and isinstance(b, (int, float)):
            return a * int(b)
        elif isinstance(b, str) and isinstance(a, (int, float)):
            return b * int(a)
            
        # Normal arithmetic multiplication
        result = a * b
        return int(result) if isinstance(result, float) and result == int(result) else result
        
    def div(self, args): 
        a = self.eval_arg(args[0])
        b = self.eval_arg(args[1])
        result = a / b
        return int(result) if isinstance(result, float) and result == int(result) else result

    def eq(self, args):
        return int(self.eval_arg(args[0]) == self.eval_arg(args[1]))
        
    def neq(self, args):
        return int(self.eval_arg(args[0]) != self.eval_arg(args[1]))
        
    def gt(self, args):
        return int(self.eval_arg(args[0]) > self.eval_arg(args[1]))
        
    def lt(self, args):
        return int(self.eval_arg(args[0]) < self.eval_arg(args[1]))
        
    def gte(self, args):
        return int(self.eval_arg(args[0]) >= self.eval_arg(args[1]))
        
    def lte(self, args):
        return int(self.eval_arg(args[0]) <= self.eval_arg(args[1]))
        
    def and_(self, args):
        return int(bool(self.eval_arg(args[0])) and bool(self.eval_arg(args[1])))
        
    def or_(self, args):
        return int(bool(self.eval_arg(args[0])) or bool(self.eval_arg(args[1])))

    def number(self, args):
        """Process a number literal, normalizing integers to int type"""
        value = float(args[0])
        # If the number is an integer (no decimal part), return as int
        if value.is_integer():
            return int(value)
        return value

    def neg(self, args):
        """Handle negative numbers"""
        debug(f"Handling negative number with args: {args}")
        # Evaluate the argument and negate it
        value = self.eval_arg(args[0])
        return -value

    def boolean(self, args):
        """Process a boolean literal"""
        value = str(args[0])
        return value == "true"

    def string(self, args):
        raw_str = str(args[0])
        
        # Handle triple-quoted strings (multi-line)
        if (raw_str.startswith('"""') and raw_str.endswith('"""')) or \
           (raw_str.startswith("'''") and raw_str.endswith("'''")):
            # Extract content between triple quotes
            return raw_str[3:-3]
        
        # Handle regular strings (single-line)
        if (raw_str.startswith('"') and raw_str.endswith('"')) or \
           (raw_str.startswith("'") and raw_str.endswith("'")):
            # Extract content between quotes
            return raw_str[1:-1]
        
        # Invalid string format
        raise Exception(f"Invalid string format: {raw_str}")

    def f_string(self, args):
        """Handle f-string formatting"""
        # args[0] should be "f" and args[1] should be the string
        if len(args) != 2:
            raise Exception("Invalid f-string format")
        
        raw_str = str(args[1])
        
        # Extract the string content
        if (raw_str.startswith('"') and raw_str.endswith('"')) or \
           (raw_str.startswith("'") and raw_str.endswith("'")):
            content = raw_str[1:-1]
        else:
            raise Exception(f"Invalid f-string format: {raw_str}")
        
        # Simple f-string interpolation - find {variable} patterns
        import re
        result = content
        
        # Find all {expression} patterns
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, content)
        
        for match in matches:
            # Evaluate the expression inside the braces
            try:
                # Handle simple variable access
                if '.' in match:
                    # Handle dotted names like obj.property
                    parts = match.split('.')
                    value = self.get_var(parts[0])
                    for part in parts[1:]:
                        if hasattr(value, part):
                            value = getattr(value, part)
                        elif isinstance(value, dict) and part in value:
                            value = value[part]
                        elif part == 'length' and hasattr(value, '__len__'):
                            value = len(value)
                        else:
                            raise Exception(f"Unknown property: {part}")
                else:
                    # Simple variable lookup
                    value = self.get_var(match)
                
                # Replace the {expression} with the evaluated value
                result = result.replace('{' + match + '}', str(value))
            except Exception as e:
                debug(f"Error evaluating f-string expression '{match}': {e}")
                # Keep the original text if evaluation fails
                pass
        
        return result

    def print_stmt(self, args):
        val = self.eval_arg(args[0])
        print(val)
        return val

    def dotted_name(self, args):
        """Handle dotted names like obj.method or obj.property"""
        if len(args) < 2:
            raise Exception("Invalid dotted name")
        
        # Get all parts of the dotted name
        name_parts = [str(t) for t in args]
        obj_name, prop_name = name_parts[0], name_parts[-1]
        
        # Get the object
        obj = None
        if obj_name in self.modules:
            obj = self.modules[obj_name]
        else:
            # Check scopes for the object
            for scope in reversed(self.env):
                if obj_name in scope:
                    obj = scope[obj_name]
                    break
                
        if obj is None:
            raise NameError(f"Object '{obj_name}' not found")
        
        # Handle array properties
        if isinstance(obj, list):
            if prop_name == "length":
                return len(obj)
            else:
                raise AttributeError(f"Array has no property '{prop_name}'")
        
        # Handle other object properties
        if hasattr(obj, prop_name):
            attr = getattr(obj, prop_name)
            return attr
        elif isinstance(obj, dict) and prop_name in obj:
            return obj[prop_name]
        else:
            raise AttributeError(f"'{obj_name}' has no property '{prop_name}'")

    def args(self, args):
        """Handle function arguments list"""
        # Process each argument expression and return a flat list
        processed_args = []
        for arg in args:
            if isinstance(arg, Token):
                # Handle token directly
                if arg.type == 'NAME':
                    processed_args.append(self.get_var(str(arg)))
                elif arg.type == 'NUMBER':
                    processed_args.append(float(arg.value) if '.' in arg.value else int(arg.value))
                elif arg.type in ('STRING', 'ESCAPED_STRING'):
                    processed_args.append(str(arg.value))
                else:
                    processed_args.append(self.transform(arg))
            elif isinstance(arg, Tree):
                processed_args.append(self.transform(arg))
            else:
                processed_args.append(arg)
        debug(f"args handler processed {len(args)} arguments into: {processed_args}")
        return processed_args

    def import_stmt(self, args):
        # Extract module path and check for alias
        alias = None
        module_parts = []
        i = 0

        # Look for 'AS' token to find where module name ends and alias begins
        as_index = None
        for j in range(len(args)):
            if args[j] is not None and (str(args[j]) == "as" or (hasattr(args[j], 'type') and args[j].type == 'AS')):
                as_index = j
                break

        if as_index is not None:
            # We have an alias - everything before 'as' is the module name
            module_parts = [str(args[k]) for k in range(as_index)]
            if as_index + 1 < len(args):
                alias = str(args[as_index + 1])
        else:
            # No alias - all arguments are part of the module name
            module_parts = [str(arg) for arg in args if arg is not None]
        
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
                # Get the proper base name (e.g., gui from gui.smod)
                base_name = module_name.replace(".smod", "")
                    
                # Convert to Python module path
                py_module = "sona.stdlib." + base_name
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
            
            # Determine paths to search based on module structure
            search_paths = []
            
            if module_name.endswith("smod"):
                # For .smod imports, look for the .smod file directly
                search_paths.append(base_path / 'stdlib' / f"{base_name}.smod")
                search_paths.append(stdlib_path / f"{base_name}.smod")
                # Also check for the Python implementation file
                search_paths.append(base_path / 'stdlib' / f"{base_name}.py")
                search_paths.append(stdlib_path / f"{base_name}.py")
            else:
                # Use the proper last module part
                last_module_part = module_parts[-1]
                
                # Standard paths (for regular imports)
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
            if "utils" in module_parts and "smod" in module_parts and not module_name.endswith("smod"):
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

    def if_stmt(self, args):
        condition = self.eval_arg(args[0])
        if condition:
            self.push_scope()
            try:
                if isinstance(args[1], Tree) and hasattr(args[1], 'children'):
                    result = None
                    for stmt in args[1].children:
                        result = self.transform(stmt)
                else:
                    result = self._exec(args[1])
                
                # Test 6 fix: Return the result as is without normalizing to int
                # This ensures floats stay as floats and integers as integers
                return result
            finally:
                self.pop_scope()
        elif len(args) > 2:
            # Handle else or else-if part
            else_result = self.transform(args[2])
            return else_result
        return None
    
    def else_part(self, args):
        # This handles both "else block" and "else if condition block else_part?" forms
        if len(args) == 1:
            # Simple else block
            self.push_scope()
            try:
                if isinstance(args[0], Tree) and hasattr(args[0], 'children'):
                    result = None
                    for stmt in args[0].children:
                        result = self.transform(stmt)
                else:
                    result = self._exec(args[0])
                return result
            finally:
                self.pop_scope()
        else:
            # else if condition block else_part?
            condition = self.eval_arg(args[0])
            if condition:
                self.push_scope()
                try:
                    if isinstance(args[1], Tree) and hasattr(args[1], 'children'):
                        result = None
                        for stmt in args[1].children:
                            result = self.transform(stmt)
                    else:
                        result = self._exec(args[1])
                    return result
                finally:
                    self.pop_scope()
            elif len(args) > 2:
                # Handle nested else_part
                return self.transform(args[2])
        return None

    def while_stmt(self, args):
        condition_expr, body = args
        result = None
        
        # Debug the condition and body structure
        debug(f"While condition type: {type(condition_expr)}")
        if hasattr(condition_expr, 'data'):
            debug(f"While condition data: {condition_expr.data}")
        debug(f"While body type: {type(body)}")
        if hasattr(body, 'data'):
            debug(f"While body data: {body.data}")
        
        # First evaluate the condition - make sure it's properly evaluated
        try:
            while self.eval_arg(condition_expr):
                debug(f"Executing while loop iteration")
                self.push_scope()
                try:
                    # Handle different body types in a consistent manner
                    if isinstance(body, Tree) and hasattr(body, 'data') and body.data == 'block':
                        # Handle block with proper children iteration
                        if hasattr(body, 'children') and body.children:
                            for stmt in body.children:
                                result = self.transform(stmt)
                    elif isinstance(body, Tree):
                        # Any other tree
                        result = self.transform(body)
                    elif isinstance(body, list):
                        # List of statements
                        for stmt in body:
                            result = self.transform(stmt)
                    else:
                        # Single statement that's not a Tree
                        result = self.transform(body)
                except ReturnSignal as r:
                    result = r.value
                    self.pop_scope()
                    raise
                except BreakSignal:
                    self.pop_scope()
                    break
                except ContinueSignal:
                    # Handle continue by skipping to the next iteration
                    debug("Continue signal received, skipping to next iteration")
                    self.pop_scope()
                    continue
                finally:
                    self.pop_scope()
        except Exception as e:
            debug(f"Error in while loop: {e}")
            raise
        
        # Test 7 fix: Return the result as is without normalizing to int
        return result

    def for_stmt(self, args):
        debug("=== FOR_STMT CALLED ===")
        debug(f"for_stmt called with {len(args)} arguments: {args}")
        debug(f"Arguments types: {[type(arg) for arg in args]}")
        for i, arg in enumerate(args):
            debug(f"Arg {i}: {arg} (type: {type(arg)})")
            if hasattr(arg, 'data'):
                debug(f"  - data: {arg.data}")
            if hasattr(arg, 'children'):
                debug(f"  - children: {arg.children}")
        
        result = None
        
        try:
            if len(args) == 4:
                # Range-based for loop: for var in start..end
                var_name_node, start_expr, end_expr, body = args
                var_name = str(var_name_node)  # Extract variable name
                start = self.eval_arg(start_expr)
                end = self.eval_arg(end_expr)
                
                debug(f"Range-based for loop: {var_name} from {start} to {end}")
                
                for i in range(int(start), int(end) + 1):
                    debug(f"For loop iteration {i}, pushing scope")
                    self.push_scope()
                    try:
                        # Set the loop variable in the current scope
                        self.set_var(var_name, i)
                        debug(f"Set loop variable {var_name} = {i}")
                        
                        # Execute the loop body
                        result = self._exec(body.children)
                        debug(f"Loop body executed with result: {result}")
                        
                    except BreakSignal:
                        debug("Break signal received, exiting loop")
                        self.pop_scope()
                        break
                    except ContinueSignal:
                        debug("Continue signal received, continuing to next iteration")
                        self.pop_scope()
                        continue
                    except ReturnSignal as r:
                        debug(f"Return signal received with value: {r.value}")
                        self.pop_scope()
                        raise
                    finally:
                        if len(self.env) > 1:  # Ensure we don't pop global scope
                            self.pop_scope()
            
            elif len(args) == 3:
                # Iterable-based for loop: for var in iterable
                var_name_node, iterable_expr, body = args
                var_name = str(var_name_node)  # Extract variable name
                iterable = self.eval_arg(iterable_expr)
                
                debug(f"Iterable-based for loop: {var_name} in {iterable}")
                
                if isinstance(iterable, list):
                    for item in iterable:
                        debug(f"For loop iteration with item {item}, pushing scope")
                        self.push_scope()
                        try:
                            # Set the loop variable in the current scope
                            self.set_var(var_name, item)
                            debug(f"Set loop variable {var_name} = {item}")
                            
                            # Execute the loop body
                            result = self._exec(body.children)
                            debug(f"Loop body executed with result: {result}")
                            
                        except BreakSignal:
                            debug("Break signal received, exiting loop")
                            self.pop_scope()
                            break
                        except ContinueSignal:
                            debug("Continue signal received, continuing to next iteration")
                            self.pop_scope()
                            continue
                        except ReturnSignal as r:
                            debug(f"Return signal received with value: {r.value}")
                            self.pop_scope()
                            raise
                        finally:
                            if len(self.env) > 1:  # Ensure we don't pop global scope
                                self.pop_scope()
                else:
                    raise TypeError(f"Cannot iterate over {type(iterable)}")
            else:
                raise ValueError(f"Invalid for statement arguments: {len(args)}")
                
        except Exception as e:
            debug(f"Error in for_stmt: {e}")
            raise
        
        debug(f"for_stmt returning: {result}")
        return result

    def param_list(self, args):
        """Process function parameter list"""
        debug(f"Processing parameter list with {len(args)} parameters")
        return args  # Return the parameter tokens directly

    def func_def(self, args):
        """Process function definition without evaluating its body"""
        debug(f"Function definition with {len(args)} arguments")
        
        # Extract function name and body
        name = args[0]
        func_name = str(name)
        
        # Extract parameters list (could be None)
        param_list = None
        if len(args) > 1 and args[1] is not None:
            # We have parameters
            param_list = args[1]
        
        # Extract body (last argument)
        body = args[-1]
        
        # Process parameter tokens
        params = []
        if param_list is not None:
            if isinstance(param_list, list):
                params = param_list
            elif hasattr(param_list, 'children'):
                params = param_list.children
            elif isinstance(param_list, Token) and param_list.type == 'NAME':
                params = [param_list]
        
        # Store function definition without evaluating its body
        param_names = [str(p) for p in params]
        debug(f"Defined function '{func_name}' with parameters: {param_names}")
        self.functions[func_name] = (params, body)
        
        return func_name

    def func_call(self, args):
        # Extract function name and arguments
        debug(f"func_call called with {len(args)} args")
        name_node = args[0]
        debug(f"Function name node: {name_node}, type: {type(name_node)}")
        passed_args = []
        
        if len(args) > 1:
            if isinstance(args[1], Tree) and args[1].data == "args":
                debug(f"Processing function arguments from Tree...")
                # Store the argument values
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
                debug(f"Evaluated function arguments from Tree: {passed_args}")
            elif isinstance(args[1], list):
                debug(f"Using pre-processed arguments from args handler: {args[1]}")
                # Arguments have already been processed by the args handler
                passed_args = args[1]
            else:
                debug(f"Direct args without 'args' wrapper: {args[1:]}")
                # Handle cases where arguments are passed directly
                for arg in args[1:]:
                    passed_args.append(self.eval_arg(arg))
                debug(f"Evaluated direct arguments: {passed_args}")
        
        debug(f"Final passed_args: {passed_args}")

        # Handle dotted calls (module.method)
        if isinstance(name_node, Tree) and name_node.data == "dotted_name":
            name_parts = [str(t.value) if isinstance(t, Token) else str(t) for t in name_node.children]
            obj_name, method_name = name_parts[0], name_parts[-1]
            
            # Specific handling for __native__ functions
            if obj_name == "__native__":
                debug(f"Native function call detected: {name_parts}")
                
                # Start with the __native__ module
                current = self.modules["__native__"]
                
                # Navigate the nested path (e.g., __native__.http.get)
                for part in name_parts[1:-1]:
                    if part in current:
                        current = current[part]
                    else:
                        if hasattr(name_node.children[0], 'line') and hasattr(name_node.children[0], 'column'):
                            line, column = name_node.children[0].line, name_node.children[0].column
                            raise NameError(f"Native module '{part}' not found at line {line}, column {column}")
                        else:
                            raise NameError(f"Native module '{part}' not found")
                
                # Get the final method
                if method_name in current:
                    native_func = current[method_name]
                    if callable(native_func):
                        return native_func(*passed_args)
                    else:
                        raise TypeError(f"Native function '{method_name}' is not callable")
                else:
                    if hasattr(name_node.children[-1], 'line') and hasattr(name_node.children[-1], 'column'):
                        line, column = name_node.children[-1].line, name_node.children[-1].column
                        raise NameError(f"Native function '{method_name}' not found at line {line}, column {column}")
                    else:
                        raise NameError(f"Native function '{method_name}' not found")
            
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
        
        # Check for built-in functions first
        if name in self.builtin_functions:
            if name == "range":
                if len(passed_args) == 1:
                    # range(end)
                    return list(range(int(passed_args[0])))
                elif len(passed_args) == 2:
                    # range(start, end)
                    return list(range(int(passed_args[0]), int(passed_args[1])))
                elif len(passed_args) == 3:
                    # range(start, end, step)
                    return list(range(int(passed_args[0]), int(passed_args[1]), int(passed_args[2])))
                else:
                    raise ValueError(f"range() takes 1-3 arguments, got {len(passed_args)}")
            elif name == "isinstance":
                if len(passed_args) != 2:
                    raise ValueError(f"isinstance() takes 2 arguments, got {len(passed_args)}")
                obj, type_name = passed_args[0], str(passed_args[1])
                if type_name in self.builtin_types:
                    return isinstance(obj, self.builtin_types[type_name])
                else:
                    raise ValueError(f"Unknown type: {type_name}")
            elif name == "len":
                if len(passed_args) != 1:
                    raise ValueError(f"len() takes 1 argument, got {len(passed_args)}")
                obj = passed_args[0]
                if hasattr(obj, '__len__'):
                    return len(obj)
                else:
                    raise TypeError(f"object of type '{type(obj).__name__}' has no len()")
            elif name == "str":
                if len(passed_args) != 1:
                    raise ValueError(f"str() takes 1 argument, got {len(passed_args)}")
                return str(passed_args[0])
            elif name == "int":
                if len(passed_args) != 1:
                    raise ValueError(f"int() takes 1 argument, got {len(passed_args)}")
                try:
                    return int(passed_args[0])
                except (ValueError, TypeError):
                    raise ValueError(f"invalid literal for int(): {passed_args[0]}")
            elif name == "float":
                if len(passed_args) != 1:
                    raise ValueError(f"float() takes 1 argument, got {len(passed_args)}")
                try:
                    return float(passed_args[0])
                except (ValueError, TypeError):
                    raise ValueError(f"invalid literal for float(): {passed_args[0]}")
            elif name == "type":
                if len(passed_args) != 1:
                    raise ValueError(f"type() takes 1 argument, got {len(passed_args)}")
                obj = passed_args[0]
                if isinstance(obj, bool):
                    return "bool"
                elif isinstance(obj, int):
                    return "int" 
                elif isinstance(obj, float):
                    return "float"
                elif isinstance(obj, str):
                    return "str"
                elif isinstance(obj, list):
                    return "list"
                elif isinstance(obj, dict):
                    return "dict"
                else:
                    return type(obj).__name__
            elif name == "max":
                if len(passed_args) == 0:
                    raise ValueError("max expected at least 1 argument, got 0")
                elif len(passed_args) == 1 and hasattr(passed_args[0], '__iter__'):
                    # max(iterable)
                    return max(passed_args[0])
                else:
                    # max(arg1, arg2, ...)
                    return max(passed_args)
            elif name == "min":
                if len(passed_args) == 0:
                    raise ValueError("min expected at least 1 argument, got 0")
                elif len(passed_args) == 1 and hasattr(passed_args[0], '__iter__'):
                    # min(iterable)
                    return min(passed_args[0])
                else:
                    # min(arg1, arg2, ...)
                    return min(passed_args)
            elif name == "sum":
                if len(passed_args) == 0:
                    raise ValueError("sum expected at least 1 argument, got 0")
                elif len(passed_args) == 1:
                    # sum(iterable)
                    return sum(passed_args[0])
                elif len(passed_args) == 2:
                    # sum(iterable, start)
                    return sum(passed_args[0], passed_args[1])
                else:
                    raise ValueError(f"sum expected 1 or 2 arguments, got {len(passed_args)}")
            elif name == "abs":
                if len(passed_args) != 1:
                    raise ValueError(f"abs() takes 1 argument, got {len(passed_args)}")
                return abs(passed_args[0])
            elif name == "round":
                if len(passed_args) == 1:
                    return round(passed_args[0])
                elif len(passed_args) == 2:
                    return round(passed_args[0], passed_args[1])
                else:
                    raise ValueError(f"round() takes 1 or 2 arguments, got {len(passed_args)}")
            elif name == "sorted":
                if len(passed_args) != 1:
                    raise ValueError(f"sorted() takes 1 argument, got {len(passed_args)}")
                try:
                    return sorted(passed_args[0])
                except TypeError:
                    raise TypeError(f"'{type(passed_args[0]).__name__}' object is not iterable")
            elif name == "reversed":
                if len(passed_args) != 1:
                    raise ValueError(f"reversed() takes 1 argument, got {len(passed_args)}")
                try:
                    return list(reversed(passed_args[0]))
                except TypeError:
                    raise TypeError(f"argument to reversed() must be a sequence")
        
        # Check for __native__ function calls
        if name == "__native__" and len(passed_args) >= 1:
            # This is a direct __native__ function call
            native_func_name = str(passed_args[0])
            if native_func_name in self.modules["__native__"]:
                native_func = self.modules["__native__"][native_func_name]
                # Call with remaining arguments
                return native_func(*passed_args[1:])
            else:
                if hasattr(name_node, 'line') and hasattr(name_node, 'column'):
                    line, column = name_node.line, name_node.column
                    raise NameError(f"Native function '{native_func_name}' not found at line {line}, column {column}")
                else:
                    raise NameError(f"Native function '{native_func_name}' not found")
        
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
                raise ValueError(f"Function '{name}' expects {len(params)} arguments, got {len(passed_args)}")

        debug(f"Function call: About to execute '{name}' with params: {[str(p) for p in params]}")
        
        # Create a new scope for function execution
        self.push_scope()
        debug(f"Pushed new scope for function '{name}', now at level {len(self.env)}")
        
        # Add each parameter to the function scope with its value
        for i, (param, value) in enumerate(zip(params, passed_args)):
            param_name = str(param)
            debug(f"Setting function parameter {i}: {param_name} = {value}")
            self.env[-1][param_name] = value
            debug(f"Parameter '{param_name}' set to {value} in scope {len(self.env)-1}")
            
            # Verify parameter was set correctly
            if param_name not in self.env[-1]:
                debug(f"ERROR: Parameter '{param_name}' not set correctly")
        
        # Debug the function scope contents
        scope_contents = ", ".join([f"{k}={v}" for k, v in self.env[-1].items()])
        debug(f"Function '{name}' scope contents: {scope_contents}")
        debug(f"Current env stack: {len(self.env)} scopes, top scope keys: {list(self.env[-1].keys())}")

        try:
            # Execute the function body statements
            result = None
            debug(f"Starting execution of function '{name}' body")
            
            # Process function body statements
            for i, child in enumerate(body.children):
                debug(f"Executing statement {i} in function '{name}'")
                if isinstance(child, Tree) and child.data == 'return_stmt':
                    debug(f"Processing return statement")
                    # Special handling for return statements
                    try:
                        return_expr = child.children[0] if child.children else None
                        if return_expr:
                            debug(f"Evaluating return expression: {return_expr}")
                            result = self.transform(return_expr)
                            debug(f"Return value: {result}")
                        else:
                            result = None
                            debug("Return with no value")
                        break  # Exit the loop on return
                    except Exception as e:
                        debug(f"Error in return statement: {e}")
                        raise
                else:
                    # Execute other statements
                    try:
                        result = self.transform(child)
                        debug(f"Statement result: {result}")
                    except Exception as e:
                        debug(f"Error executing statement: {e}")
                        raise
            
            debug(f"Function '{name}' execution completed with result: {result}")
            self.pop_scope()
            return result
        except ReturnSignal as r:
            debug(f"Function '{name}' returned via signal with value: {r.value}")
            self.pop_scope()
            return r.value
        except Exception as e:
            error_msg = f"Error in function '{name}': {str(e)}"
            debug(error_msg)
            self.pop_scope()
            raise

    def return_stmt(self, args):
        """Handle return statement"""
        debug(f"Processing return statement with {len(args)} args")
        if args:
            debug(f"Evaluating return value")
            value = self.eval_arg(args[0])
            # Normalize numeric results
            if isinstance(value, float) and value.is_integer():
                value = int(value)
            debug(f"Return value: {value}")
            raise ReturnSignal(value)
        
        debug("Return with no value (None)")
        raise ReturnSignal(None)

    def break_stmt(self, args):
        """Handle break statement"""
        debug(f"Processing break statement")
        raise BreakSignal()

    def continue_stmt(self, args):
        """Handle continue statement"""
        debug(f"Processing continue statement")
        raise ContinueSignal()

    def try_stmt(self, args):
        """Handle try-catch statement"""
        debug(f"Processing try-catch statement with {len(args)} blocks")
        try_block = args[0]
        catch_block = args[1]
        
        try:
            # Execute the try block
            result = self.eval_arg(try_block)
            return result
        except Exception as e:
            debug(f"Exception caught in try block: {e}")
            # Execute the catch block
            result = self.eval_arg(catch_block)
            return result

    def block(self, args):
        """Handle a code block, returning the block contents safely"""
        # This helps with function bodies and control structures
        debug(f"Processing block with {len(args)} statements")
        
        # Create a Tree object with children if args is a list
        if isinstance(args, list):
            new_tree = Tree('block', args)
            return new_tree
            
        return args

    def start(self, args):
        result = None
        for stmt in args:
            result = self._exec(stmt)
        return result

    def array(self, args):
        if not args:
            return []
        if isinstance(args[0], list):
            return args[0]
        if hasattr(args[0], 'children'):
            return [self.eval_arg(item) for item in args[0].children]
        return [self.eval_arg(item) for item in args]

    def array_items(self, args):
        return [self.eval_arg(item) for item in args]

    def array_literal(self, args):
        return self.array(args)

    def object(self, args):
        """Handle object literals like {}"""
        if not args or args[0] is None:
            return {}
        if isinstance(args[0], dict):
            return args[0]
        # args[0] should be the result of object_items
        items = self.eval_arg(args[0])
        if isinstance(items, list):
            return dict(items)
        return {}

    def object_items(self, args):
        """Handle object items (key: value pairs)"""
        return [self.eval_arg(item) for item in args]

    def object_item(self, args):
        """Handle individual object item (key: value)"""
        key = self.eval_arg(args[0])
        value = self.eval_arg(args[1])
        
        # Convert key to string if it's a name token
        if isinstance(key, str):
            # Remove quotes if it's a string literal
            if key.startswith('"') and key.endswith('"'):
                key = key[1:-1]
            elif key.startswith("'") and key.endswith("'"):
                key = key[1:-1]
        
        return (key, value)

    def object_literal(self, args):
        """Handle object literal syntax"""
        return self.object(args)

    def chained_access(self, args):
        """Handle chained access like obj.prop, obj[key], obj.method(), etc."""
        if len(args) < 1:
            raise Exception("Invalid chained access")
        
        # Get the base object
        base = args[0]
        if isinstance(base, Token):
            current = self.get_var(str(base))
        else:
            current = self.eval_arg(base)
        
        # Process the access chain
        for chain in args[1:]:
            if hasattr(chain, 'data'):
                if chain.data == "array_access_chain":
                    # Array/object access [expr]
                    index = self.eval_arg(chain.children[0])
                    current = current[index]
                elif chain.data == "property_access_chain":
                    # Property access .property
                    prop_name = str(chain.children[0])
                    if hasattr(current, prop_name):
                        current = getattr(current, prop_name)
                    elif isinstance(current, dict):
                        current = current[prop_name]
                    else:
                        raise AttributeError(f"'{type(current).__name__}' object has no attribute '{prop_name}'")
                elif chain.data == "method_call_chain":
                    # Method call .method(args)
                    method_name = str(chain.children[0])
                    args_list = []
                    if len(chain.children) > 1:
                        args_list = self.eval_arg(chain.children[1])
                    
                    if hasattr(current, method_name):
                        method = getattr(current, method_name)
                        current = method(*args_list)
                    else:
                        raise AttributeError(f"'{type(current).__name__}' object has no method '{method_name}'")
        
        return current

    def property_assign(self, args):
        """Handle property assignment like obj[key] = value or obj.prop = value"""
        chained_access = args[0]  # Don't evaluate this, process it directly
        value = self.eval_arg(args[1])
        
        # Parse the chained access to get the object and property/index
        if len(chained_access.children) < 2:
            raise Exception("Invalid property assignment")
        
        # Get the base object
        base_name = str(chained_access.children[0])
        base_obj = self.get_var(base_name)
        
        # Handle the access chain
        current = base_obj
        
        # Navigate to the parent object (all but the last access)
        for i, chain in enumerate(chained_access.children[1:-1]):
            if chain.data == "array_access_chain":
                # Array/object access [expr]
                index = self.eval_arg(chain.children[0])
                current = current[index]
            elif chain.data == "property_access_chain":
                # Property access .property
                prop_name = str(chain.children[0])
                current = current[prop_name]
        
        # Handle the final assignment
        final_chain = chained_access.children[-1]
        if final_chain.data == "array_access_chain":
            # Array/object access assignment
            index = self.eval_arg(final_chain.children[0])
            if isinstance(current, (list, dict)):
                current[index] = value
            else:
                raise TypeError(f"'{type(current).__name__}' object does not support item assignment")
        elif final_chain.data == "property_access_chain":
            # Property access assignment
            prop_name = str(final_chain.children[0])
            if isinstance(current, dict):
                current[prop_name] = value
            else:
                setattr(current, prop_name, value)
            # Array/object access assignment
            index = self.eval_arg(final_chain.children[0])
            if isinstance(current, (list, dict)):
                current[index] = value
            else:
                raise TypeError(f"Cannot assign to index of {type(current)}")
        elif final_chain.data == "property_access_chain":
            # Property access assignment
            prop_name = str(final_chain.children[0])
            if isinstance(current, dict):
                current[prop_name] = value
            else:
                raise TypeError(f"Cannot assign to property of {type(current)}")
        
        return value

    def in_op(self, args):
        """Handle 'in' operator"""
        left = self.eval_arg(args[0])
        right = self.eval_arg(args[1])
        
        if isinstance(right, (list, str)):
            return left in right
        elif isinstance(right, dict):
            return left in right
        else:
            raise TypeError(f"Cannot use 'in' with {type(right)}")

    def _eval(self, node):
        return self.transform(node)

    def _exec(self, node):
        """Execute a node or list of nodes, robust to both Tree and list bodies"""
        if node is None:
            return None
            
        if isinstance(node, Tree):
            # Return the result directly without normalizing
            return self.transform(node)
            
        elif isinstance(node, list):
            result = None
            for n in node:
                result = self.transform(n)
            return result
            
        # If node is a block with children attribute
        elif hasattr(node, 'children'):
            result = None
            for child in node.children:
                result = self.transform(child)
            return result
            
        # Handle Token case
        elif isinstance(node, Token):
            return self.transform(node)
            
        return node

    def eval_arg(self, arg):
        if isinstance(arg, Token):
            # Handle Token types directly
            if arg.type == 'NAME':
                # This is a variable name, look it up
                return self.get_var(str(arg))
            elif arg.type == 'NUMBER':
                return float(arg.value) if '.' in arg.value else int(arg.value)
            elif arg.type in ('STRING', 'ESCAPED_STRING'):
                return str(arg.value)
            else:
                # Try to transform it
                try:
                    return self.transform(arg)
                except:
                    return arg
        elif isinstance(arg, Tree):
            try:
                return self.transform(arg)
            except Exception as e:
                if hasattr(arg, 'line') and hasattr(arg, 'column'):
                    debug(f"Error evaluating argument at line {arg.line}, column {arg.column}: {e}")
                raise
        return arg

    def transform_tree(self, tree):
        """Custom transform to fix function parameter scoping and body evaluation"""
        if not isinstance(tree, Tree):
            return tree
            
        try:
            debug(f"Looking for handler for tree data type: {tree.data}")
            handler = getattr(self, tree.data)
            debug(f"Found handler for {tree.data}: {handler}")
        except AttributeError:
            debug(f"No handler found for tree data type: {tree.data}")
            return tree
            
        # Special handling for control flow constructs that need custom child processing
        if tree.data == 'for_stmt':
            debug(f"Special handling for for_stmt with {len(tree.children)} children")
            # Pass the raw tree to for_stmt handler without transforming children
            return handler(tree.children)
            
        # Special handling for property assignment: don't evaluate chained_access
        if tree.data == 'property_assign':
            debug(f"Special handling for property_assign with {len(tree.children)} children")
            # Pass the raw tree to property_assign handler without transforming children
            return handler(tree.children)
            
        # Special handling for function definition: don't evaluate body
        if tree.data == 'func_def':
            name = self.transform(tree.children[0])
            params = []
            if len(tree.children) > 2:
                param_list = tree.children[1]
                if hasattr(param_list, 'children'):
                    params = param_list.children
                elif isinstance(param_list, list):
                    params = param_list
            body = tree.children[-1]  # Store body as Tree, do not transform
            self.functions[str(name)] = (params, body)
            return name
            
        # Special handling for function call: set up scope and evaluate body
        if tree.data == 'func_call':
            # Get function name
            name_node = tree.children[0]
            func_name = str(name_node)
            
            # Process arguments with type handling
            args = []
            if len(tree.children) > 1 and hasattr(tree.children[1], 'data') and tree.children[1].data == 'args':
                args = [self.eval_arg(arg) for arg in tree.children[1].children]
                
            # Handle module calls specially
            if isinstance(name_node, Tree) and name_node.data == "dotted_name":
                # This is a module call, delegate to the regular handler
                children = [self.transform(child) for child in tree.children]
                return handler(children)
                
            # Check for built-in functions first
            if func_name in self.builtin_functions:
                # Delegate to the regular func_call handler for built-ins
                children = [self.transform(child) for child in tree.children]
                return handler(children)
                
            # For normal function calls
            if func_name not in self.functions:
                raise NameError(f"Function '{func_name}' not defined")
                
            params, body = self.functions[func_name]
            if len(params) != len(args):
                raise ValueError(f"Function '{func_name}' expects {len(params)} arguments, got {len(args)}")
                
            # Create function scope with parameters
            self.push_scope()
            for param, value in zip(params, args):
                param_name = str(param)
                self.env[-1][param_name] = value
                
            try:
                # Process function body statements
                result = None
                for child in body.children:
                    if isinstance(child, Tree) and child.data == 'return_stmt':
                        # Handle return statement
                        if len(child.children) > 0:
                            return_expr = child.children[0]
                            result = self.transform(return_expr)
                            # Normalize numeric results
                            if isinstance(result, float) and result.is_integer():
                                result = int(result)
                        else:
                            result = None
                        break
                    else:
                        # Execute other statements
                        result = self.transform(child)
                return result
            finally:
                self.pop_scope()
                
        # Default: transform children with improved type handling
        children = []
        for child in tree.children:
            transformed = self.transform(child)
            children.append(transformed)
            
        try:
            debug(f"Calling handler {tree.data} with {len(children)} children")
            return handler(children)
        except Exception as e:
            debug(f"Exception calling handler {tree.data}: {e}")
            debug(f"Children types: {[type(c) for c in children]}")
            debug(f"Children values: {children}")
            raise

    def transform(self, tree):
        if isinstance(tree, Tree):
            return self.transform_tree(tree)
        return super().transform(tree)

def run_code(code, debug_enabled=False):
    global debug_mode
    debug_mode = debug_enabled

    try:
        interpreter = SonaInterpreter()
        grammar_path = os.path.join(os.path.dirname(__file__), 'grammar.lark')
        with open(grammar_path, 'r') as f:
            grammar = f.read()

        parser = Lark(grammar, parser='lalr', propagate_positions=True)
        tree = parser.parse(code)
        return interpreter.transform(tree)
    except Exception as e:
        if hasattr(e, 'line') and hasattr(e, 'column'):
            lines = code.split('\n')
            error_line = lines[e.line-1] if e.line <= len(lines) else ""
            error_msg = f"ERROR at line {e.line}, column {e.column}:\n"
            error_msg += f"{e.line}: {error_line}\n"
            error_msg += " " * (e.column + len(str(e.line)) + 2) + "^\n"
            print(error_msg)
        raise

def capture(interpreter, code):
    """
    Helper function for tests to run code and capture success/failure.
    Returns True if the code executed successfully, False otherwise.
    """
    try:
        grammar_path = os.path.join(os.path.dirname(__file__), 'grammar.lark')
        with open(grammar_path, 'r') as f:
            grammar = f.read()

        parser = Lark(grammar, parser='lalr', propagate_positions=True)
        tree = parser.parse(code)
        interpreter.transform(tree)
        return True
    except Exception:
        return False
