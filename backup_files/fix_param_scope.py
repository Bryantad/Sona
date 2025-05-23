#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/fix_param_scope.py

"""
This script fixes the function parameter scope issue in Sona v0.5.0
by adding a specific check in the var() method.
"""

from pathlib import Path
import re

# Path to the interpreter file
interpreter_path = Path("sona/interpreter.py")

# Read the current content
with open(interpreter_path, "r") as f:
    code = f.read()

# Find the var method using regex to be safer
var_method_pattern = r"def var\(self, args\):[^}]*?# Simple variable name[^}]*?for scope in reversed\(self\.env\):[^}]*?if name in scope:[^}]*?return scope\[name\]"

# New implementation with parameter scope fix
var_method_replacement = """def var(self, args):
        # Simple variable name
        if isinstance(args[0], Token):
            name = str(args[0])
            
            # Debug all available scopes to diagnose any issues
            all_scopes = []
            for i, scope in enumerate(self.env):
                all_scopes.append(f"Scope {i}: {list(scope.keys())}")
            debug(f"Looking for variable '{name}' in scopes: {all_scopes}")
            
            # First check the current function scope specifically (optimization for parameters)
            if len(self.env) > 0 and name in self.env[-1]:
                debug(f"Found parameter '{name}' = {self.env[-1][name]} in current scope")
                return self.env[-1][name]
                
            # Then check all scopes from innermost to outermost
            for scope in reversed(self.env):
                if name in scope:
                    debug(f"Found variable '{name}' = {scope[name]}")
                    return scope[name]"""

# Apply the patch
new_code = re.sub(var_method_pattern, var_method_replacement, code, flags=re.DOTALL)

# Write the updated file
with open(interpreter_path, "w") as f:
    f.write(new_code)

print("Parameter scope fix applied to interpreter.py")
