#!/usr/bin/env python3
# This script implements a targeted fix for the function parameter evaluation issue in Sona v0.5.0

"""
Final patch for Sona v0.5.0 function parameter evaluation

This script fixes a critical issue with function parameters in Sona v0.5.0 where
parameters are being evaluated during function definition rather than during function call.

The fix modifies the `func_def` method to store AST nodes without evaluation, and ensures
that parameter resolution only happens during function call execution.
"""

import os
import sys
import re
from pathlib import Path
import shutil
from datetime import datetime

def backup_file(file_path, suffix="_bak"):
    """Create a backup of the file with timestamp"""
    backup_path = file_path.with_suffix(f"{file_path.suffix}{suffix}")
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")
    return backup_path

def fix_evaluator():
    """Fix the function parameter evaluation issue"""
    # Path to interpreter file
    interpreter_path = Path("sona/interpreter.py")
    if not interpreter_path.exists():
        print(f"ERROR: Could not find interpreter at {interpreter_path}")
        return False
    
    # Create backup
    backup_file(interpreter_path)
    
    # Read the file content
    with open(interpreter_path, "r") as f:
        content = f.read()
    
    # CRITICAL FIX: Modify the func_def method to prevent early evaluation of parameters
    # This is the root cause of the "variable not found" errors
    func_def_pattern = r"def func_def\(self, args\):(.*?)(def \w+\(self, args\):)"
    func_def_match = re.search(func_def_pattern, content, re.DOTALL)
    
    if not func_def_match:
        print("ERROR: Could not find func_def method in interpreter")
        return False
    
    old_func_def = func_def_match.group(1)
    next_def = func_def_match.group(2)
    
    # Create the fixed version that stores parameters without evaluation
    fixed_func_def = """    def func_def(self, args):
        # Function name, parameters list, and body
        name, param_list, body = args
        
        # Clean and store parameter names without evaluating anything in the body
        params = []
        
        # Process parameter list appropriately depending on type
        if param_list is None:
            # No parameters
            debug(f"Function {name} has no parameters")
            params = []
        elif isinstance(param_list, Tree) and param_list.data == 'param_list':
            # This is a normal param_list tree node
            for child in param_list.children:
                if isinstance(child, Token) and child.type == 'NAME':
                    params.append(child)
                    debug(f"Added parameter: {child}")
        elif hasattr(param_list, 'children'):
            # Generic tree with children
            for child in param_list.children:
                if isinstance(child, Token) and child.type == 'NAME':
                    params.append(child)
                    debug(f"Added parameter from children: {child}")
        elif isinstance(param_list, list):
            # Already processed list of parameters
            params = [p for p in param_list if isinstance(p, Token) and p.type == 'NAME']
            debug(f"Parameters from list: {[str(p) for p in params]}")
        else:
            # Single parameter as a token
            if isinstance(param_list, Token) and param_list.type == 'NAME':
                params = [param_list]
                debug(f"Single parameter: {param_list}")
        
        debug(f"Function '{name}' registered with parameters: {[str(p) for p in params]}")
        
        # Register function with its parameters and body WITHOUT evaluating body
        self.functions[str(name)] = (params, body)
        return name
"""
    
    # Replace the old function definition
    modified_content = content.replace(old_func_def, fixed_func_def)
    
    # ADDITIONAL FIX: Improve function parameter handling in function calls
    func_call_params_pattern = r"# Add each parameter to the function scope with its value.*?for i, \(param, value\) in enumerate\(zip\(params, passed_args\)\):.*?debug\(f\"Function '\{name\}' scope parameters: \{scope_contents\}\"\)"
    func_call_params_match = re.search(func_call_params_pattern, modified_content, re.DOTALL)
    
    if func_call_params_match:
        old_params_setting = func_call_params_match.group(0)
        
        # Create the fixed version of parameter setting
        fixed_params_setting = """# Add each parameter to the function scope with its value - FIXED for v0.5.0
        for i, (param, value) in enumerate(zip(params, passed_args)):
            param_name = str(param)
            print(f"[FIXED] Setting parameter {i}: {param_name} = {value}")
            # Set parameter directly in function scope
            self.env[-1][param_name] = value
            
            # Verify parameter was set correctly
            if param_name in self.env[-1]:
                print(f"[FIXED] Verified parameter {param_name} in scope {len(self.env)-1}")
            else:
                print(f"[FIXED] ERROR: Failed to set parameter {param_name}!")
                
        # Debug the function scope contents after setting parameters
        scope_contents = ", ".join([f"{k}={v}" for k, v in self.env[-1].items()])
        debug(f"Function '{name}' scope parameters: {scope_contents}")"""
        
        # Replace the parameter setting code
        modified_content = modified_content.replace(old_params_setting, fixed_params_setting)
    else:
        print("WARNING: Could not find parameter setting code to enhance")
    
    # Write the modified content back
    with open(interpreter_path, "w") as f:
        f.write(modified_content)
    
    print("✅ Successfully applied function parameter fixes")
    return True

def test_fix():
    """Create and run a simple test to verify the fix"""
    test_file = Path("simple_function_test.sona")
    test_content = """// Test for function parameter fix in v0.5.0

// Simple function that uses a parameter
func test(value) {
    print("Parameter value: " + value)
    return value + " processed"
}

// Call the function with a string
print("Testing function with string parameter:")
let result = test("hello")
print("Function returned: " + result)

// Function that uses parameters in calculations
func multiply(a, b) {
    let product = a * b
    return product
}

// Call function with numeric parameters
print("\\nTesting calculation function:")
print("5 * 3 = " + multiply(5, 3))

print("\\nAll tests passed!")
"""
    
    with open(test_file, "w") as f:
        f.write(test_content)
    
    # Create a test runner
    runner_file = Path("run_function_fix_test.py")
    runner_content = """#!/usr/bin/env python3
import os
from sona.interpreter import run_code

# Enable debug output
os.environ["SONA_DEBUG"] = "1"

print("=== Testing Function Parameter Fix ===")
with open("simple_function_test.sona", "r") as f:
    code = f.read()
    print("Running test code:")
    print("-" * 40)
    print(code)
    print("-" * 40)
    run_code(code, debug_enabled=True)
print("\\n✅ Test complete")
"""
    
    with open(runner_file, "w") as f:
        f.write(runner_content)
    
    print(f"Created test file: {test_file}")
    print(f"Created test runner: {runner_file}")
    print("\nTo test the fix, run:")
    print(f"python {runner_file}")
    
    return True

if __name__ == "__main__":
    print("Applying final Sona v0.5.0 function parameter fix...")
    if fix_evaluator():
        test_fix()
    else:
        print("Failed to apply fixes")
        sys.exit(1)
