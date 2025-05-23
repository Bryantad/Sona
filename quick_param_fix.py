# Quick fix script for function parameter scope issue
# Fix for Sona v0.5.0

import os
import sys
from pathlib import Path
import re

def apply_fix():
    # Locate the interpreter file
    interpreter_path = Path("sona/interpreter.py")
    
    if not interpreter_path.exists():
        print(f"ERROR: Could not find interpreter at {interpreter_path}")
        return False
    
    # Create a backup
    backup_path = Path("sona/interpreter.py.param_fix_backup")
    with open(interpreter_path, "r") as src:
        content = src.read()
        with open(backup_path, "w") as dst:
            dst.write(content)
    print(f"Created backup at {backup_path}")
    
    # Apply fix to variable lookup
    var_method_pattern = r'def var\(self, args\):(.*?)# First check directly in the current scope \(for parameters\)(.*?)if len\(self\.env\) > 0 and name in self\.env\[\-1\]:'
    var_method_replacement = r'''def var(self, args):
        # Simple variable name
        if isinstance(args[0], Token):
            name = str(args[0])
            
            # Debug all available scopes to diagnose any issues
            all_scopes = []
            for i, scope in enumerate(self.env):
                all_scopes.append(f"Scope {i}: {list(scope.keys())}")
            print(f"[DEBUG] Looking for variable '{name}' in all scopes: {all_scopes}")
            
            # BUGFIX: First check directly in the current scope (highest priority for parameters)
            if len(self.env) > 0 and name in self.env[-1]:'''
    
    fixed_content = re.sub(var_method_pattern, var_method_replacement, content, flags=re.DOTALL)
    
    # Apply fix to function call method
    func_call_pattern = r'# Add each parameter to the function scope with its value - FIXED for v0\.5\.0(.*?)for i, \(param, value\) in enumerate\(zip\(params, passed_args\)\):(.*?)# Set parameter directly in function scope'
    func_call_replacement = r'''# Add each parameter to the function scope with its value - FIXED for v0.5.0
        for i, (param, value) in enumerate(zip(params, passed_args)):
            param_name = str(param)
            print(f"[DEBUG] Setting parameter {i}: {param_name} = {value}")
            # BUGFIX: Set parameter directly in function scope'''
    
    fixed_content = re.sub(func_call_pattern, func_call_replacement, fixed_content, flags=re.DOTALL)
    
    # Apply fix to return statement
    return_stmt_pattern = r'def return_stmt\(self, args\):(.*?)if args:'
    return_stmt_replacement = r'''def return_stmt(self, args):
        # BUGFIX: Debug the current environment stack to diagnose scope issues
        print(f"[DEBUG] Return statement - Current environment stack: {len(self.env)} scopes")
        for i, scope in enumerate(self.env):
            print(f"[DEBUG] Scope {i} variables: {list(scope.keys())}")
        
        if args:'''
    
    fixed_content = re.sub(return_stmt_pattern, return_stmt_replacement, fixed_content, flags=re.DOTALL)
    
    # Write the fixed content back to the file
    with open(interpreter_path, "w") as f:
        f.write(fixed_content)
    
    print("Applied fix for function parameter scope issue.")
    print("Please test again with your function examples.")
    return True

if __name__ == "__main__":
    apply_fix()
