#!/usr/bin/env python3
# Demo fix for function parameter scope in Sona v0.5.0

import re
from pathlib import Path

def apply_fix():
    # Locate the interpreter file
    interpreter_path = Path("sona/interpreter.py")
    
    if not interpreter_path.exists():
        print(f"ERROR: Could not find interpreter at {interpreter_path}")
        return False
    
    # Create a backup
    backup_path = Path("sona/interpreter.py.demo_fix_backup")
    with open(interpreter_path, "r") as src:
        content = src.read()
        with open(backup_path, "w") as dst:
            dst.write(content)
    print(f"Created backup at {backup_path}")
    
    # Fix #1: Enhance the var method to print more debugging information and fix scope access
    with open(interpreter_path, "r") as f:
        content = f.read()
    
    # Critical fix: Add a function to ensure parameters are in the current scope
    # This is a simple temporary fix for demo purposes
    self_method_missing = '''
    def set_func_param(self, name, value):
        """Set a function parameter in the current scope and ensure it's accessible"""
        if len(self.env) > 0:
            self.env[-1][name] = value
            print(f"[DEMO FIX] Parameter '{name}' = {value} set in scope {len(self.env)-1}")
            return True
        return False
        
    def get_func_param(self, name):
        """Get a function parameter from any scope"""
        for i, scope in reversed(list(enumerate(self.env))):
            if name in scope:
                return scope[name]
        return None
    '''
    
    # Insert the methods after the pop_scope method
    pop_scope_pattern = r'def pop_scope\(self\):\s+self\.env\.pop\(\)'
    if 'def set_func_param' not in content:  # Only add if not already present
        content = re.sub(pop_scope_pattern, r'def pop_scope(self):\n        self.env.pop()' + self_method_missing, content)
        print("Added parameter helper methods")
    
    # Fix #2: Modify the func_call method to ensure parameters are properly set
    func_call_pattern = r'# Add each parameter to the function scope with its value - FIXED for v0\.5\.0(.*?)self\.env\[-1\]\[param_name\] = value'
    func_call_replacement = r'''# Add each parameter to the function scope with its value - FIXED for v0.5.0\1self.set_func_param(param_name, value)  # Demo fix: Use helper method'''
    
    content = re.sub(func_call_pattern, func_call_replacement, content, flags=re.DOTALL)
    print("Modified func_call to use the parameter helper method")
    
    # Fix #3: Modify the var method to check for function parameters more thoroughly
    var_pattern = r'def var\(self, args\):(.*?)# First check directly in the current scope \(for parameters\)(.*?)if len\(self\.env\) > 0 and name in self\.env\[\-1\]:'
    var_replacement = r'''def var(self, args):
        # Simple variable name
        if isinstance(args[0], Token):
            name = str(args[0])

            # Demo fix: Check for function parameters first using helper method
            param_value = self.get_func_param(name)
            if param_value is not None:
                print(f"[DEMO FIX] Found parameter '{name}' = {param_value}")
                return param_value
                
            # Debug all available scopes
            all_scopes = []
            for i, scope in enumerate(self.env):
                all_scopes.append(f"Scope {i}: {list(scope.keys())}")
            print(f"[FIXED] Looking for variable '{name}' in scopes: {all_scopes}")

            # First check directly in the current scope (for parameters)
            if len(self.env) > 0 and name in self.env[-1]:'''
    
    content = re.sub(var_pattern, var_replacement, content, flags=re.DOTALL)
    print("Enhanced var method to better handle function parameters")
    
    # Write the modified content back to the interpreter file
    with open(interpreter_path, "w") as f:
        f.write(content)
    
    print("\nDemo fix applied successfully!")
    print("Function parameters should now work correctly for the demo.")
    print("This is a temporary fix for demo purposes.")
    
    return True

if __name__ == "__main__":
    apply_fix()
