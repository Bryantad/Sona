#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/minimal_fix.py

"""
This script provides the minimal fix for function parameter scope issues in Sona v0.5.0.
"""

from pathlib import Path

# New implementation of the transformer class
code_patch = """
class SonaInterpreter(Transformer):
    def __init__(self):
        super().__init__()
        self.env = [{}]  # Stack of scopes (dictionaries)
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

    def push_scope(self):
        self.env.append({})
        debug(f"Pushed new scope, stack size: {len(self.env)}")

    def pop_scope(self):
        debug(f"Popping scope, stack size before: {len(self.env)}")
        self.env.pop()

    def set_var(self, name, value):
        self.env[-1][name] = value
        debug(f"Set variable '{name}' = {value} in current scope")

    def get_var(self, name):
        for scope in reversed(self.env):
            if name in scope:
                debug(f"Found variable '{name}' in scope")
                return scope[name]
        raise NameError(f"Variable '{name}' not found")
        
    def var(self, args):
        # Simple variable name
        if isinstance(args[0], Token):
            name = str(args[0])
            
            # Debug all available scopes
            all_scopes = []
            for i, scope in enumerate(self.env):
                all_scopes.append(f"Scope {i}: {list(scope.keys())}")
            debug(f"Looking for variable '{name}' in scopes: {all_scopes}")
            
            # Check for the variable in all scopes, from innermost to outermost
            for scope in reversed(self.env):
                if name in scope:
                    debug(f"Found variable '{name}' = {scope[name]}")
                    return scope[name]
                    
            # If not found, improve error message with line and column information
            if hasattr(args[0], 'line') and hasattr(args[0], 'column'):
                line, column = args[0].line, args[0].column
                raise NameError(f"Variable '{name}' not found at line {line}, column {column}")
            else:
                raise NameError(f"Variable '{name}' not found")
"""

# Function call fix
func_call_fix = """
    def func_call(self, args):
        # Extract function name and arguments
        name_node = args[0]
        passed_args = []
        if len(args) > 1 and isinstance(args[1], Tree) and args[1].data == "args":
            # Evaluate arguments
            passed_args = [self.eval_arg(a) for a in args[1].children]
            debug(f"Evaluated function arguments: {passed_args}")

        # Handle regular function calls
        name = str(name_node)
        if name in self.functions:
            params, body = self.functions[name]
            
            # Verify argument count
            if len(params) != len(passed_args):
                if hasattr(name_node, 'line') and hasattr(name_node, 'column'):
                    line, column = name_node.line, name_node.column
                    raise ValueError(f"Function '{name}' expects {len(params)} arguments, got {len(passed_args)} at line {line}, column {column}")
                else:
                    raise ValueError(f"Function '{name}' expects {len(params)} arguments, got {len(passed_args)}")

            # Create a new scope for function execution
            debug(f"Setting up function call '{name}' with params: {[str(p) for p in params]}")
            self.push_scope()
            
            # Add parameters to the function scope
            for i, (param, arg) in enumerate(zip(params, passed_args)):
                param_name = str(param)
                debug(f"Setting parameter {i}: {param_name} = {arg}")
                self.set_var(param_name, arg)
            
            # Debug the current environment stack
            debug(f"Current environment after setting parameters: {len(self.env)} scopes")
            debug(f"Function scope contents: {self.env[-1]}")
            
            try:
                # Execute function body
                result = None
                for stmt in body.children:
                    debug(f"Executing statement in function body: {stmt.data if isinstance(stmt, Tree) else stmt}")
                    
                    if isinstance(stmt, Tree) and stmt.data == 'return_stmt':
                        # Return statement
                        result = self.transform(stmt)
                        debug(f"Processed return statement, result: {result}")
                        break
                    else:
                        # Other statements
                        result = self.transform(stmt)
                
                debug(f"Function execution completed with result: {result}")
                self.pop_scope()
                return result
                
            except ReturnSignal as r:
                # Handle explicit return statement
                debug(f"Function '{name}' returned value: {r.value}")
                self.pop_scope()
                return r.value
            except Exception as e:
                # Handle errors
                debug(f"Error in function '{name}': {e}")
                self.pop_scope()
                raise
"""

def apply_minimal_fix():
    # Find the interpreter file
    interpreter_path = Path("sona/interpreter.py")
    if not interpreter_path.exists():
        print(f"Error: Could not find {interpreter_path}")
        return False
    
    # Read the current content
    with open(interpreter_path, "r") as f:
        code = f.read()
    
    # Create a backup
    backup_path = interpreter_path.with_suffix(".py.orig")
    with open(backup_path, "w") as f:
        f.write(code)
    print(f"Created backup at {backup_path}")
    
    # Create a simple replacement of interpreter
    with open("sona/interpreter_simple.py", "w") as f:
        f.write(code)
        f.write("\n\n# Function parameter fix for v0.5.0\n")
        f.write("# Add this to fix function parameter scope issues:\n")
        f.write(func_call_fix)

    print("Created simplified fix in interpreter_simple.py")
    
    return True

if __name__ == "__main__":
    if apply_minimal_fix():
        print("Applied minimal fix - use the simplified interpreter for testing")
    else:
        print("Failed to apply minimal fix")
