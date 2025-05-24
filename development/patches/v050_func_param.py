#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/v050_func_param.py

"""
Modify the function call implementation for Sona v0.5.0 to properly handle function parameters.
This script replaces the entire func_call method with an updated version.
"""

import os
import re
from pathlib import Path

# The updated function call implementation
NEW_FUNC_CALL = """
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
                        
            debug(f"Evaluated function arguments: {passed_args}")

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
                raise ValueError(f"Function '{name}' expects {len(params)} arguments, got {len(passed_args)}")

        debug(f"Function call stack before pushing new scope: {len(self.env)}")
        
        # Create a new scope for function execution
        self.push_scope()
        debug(f"Pushed new scope for function '{name}', stack: {len(self.env)}")
        
        # Add each parameter to the function scope with its value
        for i, (param, value) in enumerate(zip(params, passed_args)):
            param_name = str(param)
            debug(f"Setting function parameter {i}: {param_name} = {value}")
            self.env[-1][param_name] = value
        
        # Verify all parameters are set in scope
        for param in params:
            param_name = str(param)
            if param_name not in self.env[-1]:
                debug(f"ERROR: Parameter {param_name} not found in local scope")
            else:
                debug(f"Verified parameter {param_name} = {self.env[-1][param_name]} exists in scope")
        
        # Debug the function scope contents after setting parameters
        scope_contents = ", ".join([f"{k}={v}" for k, v in self.env[-1].items()])
        debug(f"Function '{name}' scope parameters: {scope_contents}")

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
                    result = self.transform(child)
                    break
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
            scope_vars = ", ".join(f"{k}" for k in self.env[-1].keys())
            error_msg = f"Error in function '{name}'{line_info}: {str(e)}\\nCurrent scope variables: {scope_vars}"
            debug(error_msg)
            self.pop_scope()
            
            # Wrap the original exception with more context
            raise type(e)(error_msg) from e
"""

# Also update the var method to better handle params
NEW_VAR_METHOD = """
    def var(self, args):
        # Simple variable name
        if isinstance(args[0], Token):
            name = str(args[0])
            
            # Debug all available scopes
            all_scopes = []
            for i, scope in enumerate(self.env):
                all_scopes.append(f"Scope {i}: {list(scope.keys())}")
            debug(f"Looking for variable '{name}' in scopes: {all_scopes}")
            
            # First check in the current function scope (most likely place for params)
            if len(self.env) > 0 and name in self.env[-1]:
                debug(f"Found parameter '{name}' = {self.env[-1][name]} in local scope")
                return self.env[-1][name]
            
            # Then check all other scopes
            for scope in reversed(self.env[:-1]):
                if name in scope:
                    debug(f"Found variable '{name}' = {scope[name]} in outer scope")
                    return scope[name]
            
            # If not found, improve error message with line and column information
            if hasattr(args[0], 'line') and hasattr(args[0], 'column'):
                line, column = args[0].line, args[0].column
                raise NameError(f"Variable '{name}' not found at line {line}, column {column}")
            else:
                raise NameError(f"Variable '{name}' not found")
"""

def main():
    # Get the path to the interpreter file
    interpreter_path = Path("sona/interpreter.py")
    
    if not interpreter_path.exists():
        print(f"Error: Could not find {interpreter_path}")
        return
    
    # Read the interpreter file
    with open(interpreter_path, "r") as f:
        code = f.read()
    
    # Make a backup
    with open(interpreter_path.with_suffix('.py.bak2'), "w") as f:
        f.write(code)
    print(f"Created backup at {interpreter_path.with_suffix('.py.bak2')}")
    
    # Find the func_call method definition
    func_call_pattern = r'def func_call\(self, args\):.*?(?=def |$)'
    var_method_pattern = r'def var\(self, args\):.*?(?=def |$)'
    
    # Replace the methods
    new_code = re.sub(func_call_pattern, NEW_FUNC_CALL.strip(), code, flags=re.DOTALL)
    new_code = re.sub(var_method_pattern, NEW_VAR_METHOD.strip(), new_code, flags=re.DOTALL)
    
    # Write the updated file
    with open(interpreter_path, "w") as f:
        f.write(new_code)
    
    print("Updated function call and var methods with parameter scope fixes")

if __name__ == "__main__":
    main()
