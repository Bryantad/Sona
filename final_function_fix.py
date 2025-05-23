#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/final_function_fix.py

"""
This script applies a comprehensive fix for function parameter scope issues in Sona v0.5.0.
Addresses both function parameter access and return statement handling.
"""

import os
import sys
import re
from pathlib import Path

def apply_fix():
    # Locate the interpreter file
    interpreter_path = Path("sona/interpreter.py")
    
    if not interpreter_path.exists():
        print(f"ERROR: Could not find interpreter at {interpreter_path}")
        return False
    
    # Create a backup
    backup_path = Path("sona/interpreter_v050_final.py")
    with open(interpreter_path, "r") as src:
        content = src.read()
        with open(backup_path, "w") as dst:
            dst.write(content)
    print(f"Created backup at {backup_path}")
    
    # Direct modifications to specific parts of the code
    fixes_applied = 0
    
    # Read the file content
    with open(interpreter_path, "r") as f:
        content = f.read()
        
    # 1. Fix the var method to prioritize parameters in the current scope
    var_method_pattern = r'def var\(self, args\):(.*?)# First check if the variable exists(.*?)for scope in reversed\(self\.env\):'
    var_method_replacement = r'''def var(self, args):
        # Simple variable name
        if isinstance(args[0], Token):
            name = str(args[0])
            
            # Debug all available scopes to diagnose any issues
            all_scopes = []
            for i, scope in enumerate(self.env):
                all_scopes.append(f"Scope {i}: {list(scope.keys())}")
            debug(f"Looking for variable '{name}' in scopes: {all_scopes}")
            
            # FIXED: First check current scope directly (highest priority for parameters)
            if len(self.env) > 0 and name in self.env[-1]:
                debug(f"Found parameter '{name}' = {self.env[-1][name]} directly in current scope")
                return self.env[-1][name]
                
            # Then check in all scopes (for completeness)
            for scope in reversed(self.env):'''
            
    # Apply the var method fix
    if re.search(var_method_pattern, content, re.DOTALL):
        content = re.sub(var_method_pattern, var_method_replacement, content, flags=re.DOTALL)
        fixes_applied += 1
        print("✓ Fixed var method for better parameter lookup")
    else:
        print("⚠️ Could not locate var method pattern")
        
    # 2. Fix function parameter setting to verify parameters are correctly set
    param_setting_pattern = r'debug\(f"Setting function parameter {i}: {param_name} = {value}"\)(.*?)self\.env\[-1\]\[param_name\] = value'
    param_setting_replacement = r'''debug(f"Setting function parameter {i}: {param_name} = {value}")
            # Set parameter in current function scope
            self.env[-1][param_name] = value
            # Verify parameter was correctly set
            if param_name not in self.env[-1]:
                debug(f"⚠️ ERROR: Parameter '{param_name}' was not set properly")
            else:
                debug(f"✓ Parameter '{param_name}' = {self.env[-1][param_name]} confirmed in scope {len(self.env)-1}")'''
                
    # Apply the parameter setting fix
    if re.search(param_setting_pattern, content, re.DOTALL):
        content = re.sub(param_setting_pattern, param_setting_replacement, content, flags=re.DOTALL)
        fixes_applied += 1
        print("✓ Fixed parameter setting with verification")
    else:
        print("⚠️ Could not locate parameter setting pattern")
        
    # 3. Fix eval_arg to better handle parameters in expressions
    eval_arg_pattern = r'def eval_arg\(self, arg\):(.*?)debug\(f"Evaluating argument: {type\(arg\)} - {arg}"\)'
    eval_arg_replacement = r'''def eval_arg(self, arg):
        # Enhanced for v0.5.0 to better handle function parameters
        debug(f"Evaluating argument: {type(arg)} - {arg}")
        if isinstance(arg, Tree) and arg.data == 'var':
            debug(f"Evaluating a variable reference in scopes: {[list(scope.keys()) for scope in self.env]}")'''
            
    # Apply the eval_arg fix
    if re.search(eval_arg_pattern, content, re.DOTALL):
        content = re.sub(eval_arg_pattern, eval_arg_replacement, content, flags=re.DOTALL)
        fixes_applied += 1
        print("✓ Enhanced eval_arg method for parameter handling")
    else:
        print("⚠️ Could not locate eval_arg method pattern")
        
    # Read the file content as lines for more precise replacement
    with open(interpreter_path, "r") as f:
        lines = f.readlines()
    
    # Find the func_call method in the file
    func_call_index = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("def func_call(self, args):"):
            func_call_index = i
            break
    
    if func_call_index == -1:
        print("⚠️ Could not locate func_call method")
        # Save the modified content anyway
        with open(interpreter_path, "w") as f:
            f.write(content)
        return fixes_applied > 0
        
    # Save the fixed file with initial regex-based fixes
    with open(interpreter_path, "w") as f:
        f.write(content)
        
    # Define the complete implementation for func_call
    func_call_implementation = """    def func_call(self, args):
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
"""
    
    # Find the proper end of the func_call method to replace the whole method
    end_index = func_call_index + 1
    brace_count = 0
    found_def = False
    
    for i in range(func_call_index + 1, len(lines)):
        line = lines[i].strip()
        if line.startswith("def "):
            end_index = i
            found_def = True
            break
        # Count braces to track method end (backup approach)
        if not found_def:
            brace_count += line.count("{") - line.count("}")
            if brace_count < 0:
                end_index = i
                break
    
    # Replace the function call implementation
    new_lines = lines[:func_call_index] + [func_call_implementation + "\n"] + lines[end_index:]
    
    # Write the updated content
    with open(interpreter_path, "w") as f:
        f.writelines(new_lines)
    
    print("Successfully applied function parameter scope fix")
    return True

# Also create a minimal function test
def create_test():
    test_content = """// filepath: /Volumes/project usb/WayCore Inc/sona_core/function_test.sona
// Simple function parameter scope test for v0.5.0

// Define a function with parameters
func add(a, b) {
    // Access parameters within function body
    print("a = " + a)
    print("b = " + b)
    return a + b
}

func greet(name) {
    return "Hello, " + name + "!"
}

func test_nested(x) {
    func inner(y) {
        return x + y  // Access outer function parameter
    }
    return inner(10)  // Call inner function
}

// Test simple parameter access
print("Testing add(5, 3)...")
let result = add(5, 3)
print("Result: " + result)

// Test string parameter
print(greet("World"))

// Test nested functions (advanced)
print("Nested function result: " + test_nested(5))

print("All function parameter tests complete!")
"""
    
    with open("function_test.sona", "w") as f:
        f.write(test_content)
    
    # Create a runner script
    runner_content = """#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/run_function_test.py

import os
from sona.interpreter import run_code

# Enable debug output
os.environ["SONA_DEBUG"] = "1"

print("=== Running function parameter test for v0.5.0 ===")
with open("function_test.sona", "r") as f:
    code = f.read()
    run_code(code, debug_enabled=True)
"""
    
    with open("run_function_test.py", "w") as f:
        f.write(runner_content)
    
    print("Created function test files")

if __name__ == "__main__":
    if apply_fix():
        create_test()
        print("\nTo test the function parameter fix, run: python run_function_test.py")
    else:
        print("Failed to apply fix")
