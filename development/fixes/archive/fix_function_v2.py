#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/fix_function_v2.py

"""
This script applies targeted fixes to the Sona interpreter to resolve
function parameter scope issues in v0.5.0.
"""

import os
import re
from pathlib import Path

def fix_interpreter():
    # Path to the interpreter file
    interpreter_path = Path("sona/interpreter.py")
    if not interpreter_path.exists():
        print("ERROR: Could not find interpreter file")
        return False
        
    # Create backup
    backup_path = Path("sona/interpreter_v050_bak.py")
    with open(interpreter_path, "r") as src:
        content = src.read()
        with open(backup_path, "w") as dst:
            dst.write(content)
    print(f"Created backup at {backup_path}")
    
    # Read the file content
    with open(interpreter_path, "r") as f:
        content = f.read()
        
    # Counter for applied fixes
    fixes_applied = 0
    
    # 1. Fix the var method to prioritize function parameters
    if "# First check if the variable exists in the current scope (function parameters)" in content:
        print("✓ Parameter priority fix already applied")
    else:
        # Insert the check at the right place
        content = content.replace(
            "debug(f\"Looking for variable '{name}' in scopes: {all_scopes}\")\n", 
            "debug(f\"Looking for variable '{name}' in scopes: {all_scopes}\")\n"
            "            \n"
            "            # First check if the variable exists in the current scope (function parameters)\n"
            "            if len(self.env) > 0 and name in self.env[-1]:\n"
            "                debug(f\"Found parameter '{name}' = {self.env[-1][name]} in current scope\")\n"
            "                return self.env[-1][name]\n"
            "            \n"
        )
        fixes_applied += 1
        print("✓ Added parameter priority check")
    
    # 2. Enhance parameter verification during function calls
    if "# Verify parameter was set correctly" in content:
        print("✓ Parameter verification already added")
    else:
        # Add parameter verification
        content = content.replace(
            "self.env[-1][param_name] = value", 
            "self.env[-1][param_name] = value\n"
            "            # Verify parameter was set correctly\n"
            "            if param_name not in self.env[-1]:\n"
            "                debug(f\"ERROR: Parameter '{param_name}' was not properly set\")\n"
            "            else:\n"
            "                debug(f\"Parameter '{param_name}' verified in scope level {len(self.env)-1}\")"
        )
        fixes_applied += 1
        print("✓ Added parameter verification")
    
    # 3. Add enhanced debugging in return statement processing
    if "Current environment during return:" in content:
        print("✓ Return statement debugging already enhanced")
    else:
        content = content.replace(
            "debug(f\"Processing return statement with expression: {args[0]}\")", 
            "debug(f\"Processing return statement with expression: {args[0]}\")\n"
            "            # Enhanced debugging for return statement evaluation\n"
            "            debug(f\"Current environment during return: {[list(scope.keys()) for scope in self.env]}\")"
        )
        fixes_applied += 1
        print("✓ Enhanced return statement debugging")
    
    # 4. Improve function execution to provide more context
    if "Current environment stack" in content:
        print("✓ Function scope debugging already improved")
    else:
        content = content.replace(
            "debug(f\"Function '{name}' scope parameters: {scope_contents}\")", 
            "debug(f\"Function '{name}' scope parameters: {scope_contents}\")\n"
            "        debug(f\"Current environment stack: {len(self.env)} scopes with keys: {[list(scope.keys()) for scope in self.env]}\")"
        )
        fixes_applied += 1
        print("✓ Improved function scope debugging")
    
    # Save changes
    with open(interpreter_path, "w") as f:
        f.write(content)
    
    return fixes_applied > 0

def create_test():
    """Create a simple function test file to verify the fixes"""
    test_path = Path("function_v2_test.sona")
    
    test_content = """// filepath: function_v2_test.sona
// Simple test for v0.5.0 function parameter scope

// Simple function with parameters
func add(a, b) {
    print("a = " + a)
    print("b = " + b)
    return a + b
}

// String function
func greet(name) {
    print("Hello, " + name + "!")
    return "Greeting complete"
}

// Nested function that uses outer parameter
func process(value) {
    let multiplier = 10
    return value * multiplier
}

// Run tests
print("Testing add function...")
let result = add(5, 7)
print("Result: " + result)

print("\\nTesting greet function...")
greet("World")

print("\\nTesting process function...")
print("Process result: " + process(3))

print("All tests complete!")
"""

    # Create test file
    with open(test_path, "w") as f:
        f.write(test_content)
    
    # Create runner script
    runner_path = Path("run_v2_test.py")
    runner_content = """#!/usr/bin/env python3
# filepath: run_v2_test.py

import os
from sona.interpreter import run_code

# Enable debugging
os.environ["SONA_DEBUG"] = "1"

print("=== Running v0.5.0 function parameter scope test ===")
with open("function_v2_test.sona", "r") as f:
    code = f.read()
    run_code(code, debug_enabled=True)
"""

    with open(runner_path, "w") as f:
        f.write(runner_content)
    
    print(f"Created test files: {test_path} and {runner_path}")
    return True

if __name__ == "__main__":
    print("Applying function parameter scope fixes for Sona v0.5.0...")
    if fix_interpreter():
        print("\nFixed applied successfully!")
        if create_test():
            print("\nTo test the fixes, run: python run_v2_test.py")
    else:
        print("\nFailed to apply fixes. Check the interpreter file manually.")
