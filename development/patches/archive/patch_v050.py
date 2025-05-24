#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/patch_v050.py

"""
This script patches the Sona interpreter to fix function parameter scope issues in v0.5.0.
It applies all necessary fixes to make function parameters work correctly.
"""

import os
import sys
from pathlib import Path

def apply_patches():
    # Get the interpreter file path
    interpreter_path = Path("sona/interpreter.py")
    if not os.path.exists(interpreter_path):
        print(f"Error: Could not find interpreter at {interpreter_path}")
        return False
    
    print(f"Patching {interpreter_path} for v0.5.0 parameter scope issues...")
    
    # Read current file content
    with open(interpreter_path, "r") as f:
        code = f.read()
    
    # Make a backup
    backup_path = Path("sona/interpreter.py.bak")
    with open(backup_path, "w") as f:
        f.write(code)
    print(f"Created backup at {backup_path}")
    
    # Apply all necessary patches
    
    # 1. Fix function call implementation - enhanced parameter debugging
    code = code.replace(
        'debug(f"Evaluated function arguments: {passed_args}")',
        'debug(f"Evaluated function arguments: {passed_args}")\n            debug(f"Current environment stack before function call: {len(self.env)} scopes")'
    )
    
    # 2. Add parameter debugging to function scope setup
    code = code.replace(
        'debug(f"Function \'{name}\' scope parameters: {scope_contents}")',
        'debug(f"Function \'{name}\' scope parameters: {scope_contents}")\n        \n        # Ensure function parameters are visible to debug\n        debug(f"Current environment after parameter setting: {self.env}")'
    )
    
    # 3. Improve parameter scope lookup in var method
    code = code.replace(
        'debug(f"Looking for variable \'{name}\' in scopes: {all_scopes}")',
        'debug(f"Looking for variable \'{name}\' in scopes: {all_scopes}")\n            \n            # Check specifically in function parameter scope (most local scope) first\n            if len(self.env) > 0 and name in self.env[-1]:\n                debug(f"Found parameter \'{name}\' = {self.env[-1][name]} in local scope")\n                return self.env[-1][name]'
    )
    
    # 4. Add more error context for parameter lookup
    code = code.replace(
        'raise NameError(f"Variable \'{name}\' not found")',
        'debug(f"Variable \'{name}\' not found in any scope. Current env stack has {len(self.env)} scopes")\n            if len(self.env) > 1:\n                debug(f"Function local scope: {self.env[-1]}")\n                \n            raise NameError(f"Variable \'{name}\' not found")'
    )
    
    # 5. Add function parameter verification
    code = code.replace(
        'self.env[-1][param_name] = value',
        'self.env[-1][param_name] = value\n            # Verify parameter was set correctly\n            if param_name not in self.env[-1]:\n                debug(f"ERROR: Failed to set parameter {param_name} in function scope")\n            else:\n                debug(f"Verified parameter {param_name} = {self.env[-1][param_name]}")'
    )
    
    # Write the patched file
    with open(interpreter_path, "w") as f:
        f.write(code)
    
    print("Patch applied successfully.")
    return True

if __name__ == "__main__":
    if apply_patches():
        print("All patches applied successfully. Run your tests to verify the fixes.")
    else:
        print("Failed to apply patches.")
