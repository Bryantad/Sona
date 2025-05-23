#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/fix_function_params.py

"""
This script applies a targeted fix to the function parameter handling in Sona v0.5.0.
"""

from pathlib import Path

def apply_fix():
    # Path to the interpreter file
    interpreter_path = Path('sona/interpreter.py')
    if not interpreter_path.exists():
        print(f"Error: Could not find interpreter at {interpreter_path}")
        return False
    
    # Create backup
    backup_path = Path('sona/interpreter.py.bak_param_fix')
    with open(interpreter_path, 'r') as src:
        content = src.read()
        with open(backup_path, 'w') as dst:
            dst.write(content)
    print(f"Created backup at {backup_path}")
    
    # Split content into lines for easier modification
    lines = content.split('\n')
    
    # Find the 'var' method and modify it
    var_start = -1
    for i, line in enumerate(lines):
        if line.strip() == 'def var(self, args):':
            var_start = i
            break
    
    if var_start >= 0:
        # Find the parameter checking code
        param_check_start = -1
        for i in range(var_start, len(lines)):
            if '# First check if the variable exists in' in lines[i]:
                param_check_start = i
                break
        
        if param_check_start >= 0:
            # Replace the parameter checking code
            new_param_check = [
                '            # First check if the variable exists in the current (function) scope',
                '            if len(self.env) > 0 and name in self.env[-1]:',
                '                debug(f"Found parameter \'{name}\' = {self.env[-1][name]} in current scope")',
                '                return self.env[-1][name]',
                '',
                '            # Then check in other scopes'
            ]
            
            # Find the end of the param checking section
            param_check_end = -1
            for i in range(param_check_start + 1, len(lines)):
                if 'for scope in reversed(self.env):' in lines[i]:
                    param_check_end = i
                    break
            
            if param_check_end >= 0:
                # Replace the section
                new_lines = lines[:param_check_start] + new_param_check + lines[param_check_end:]
                
                # Write the modified content
                with open(interpreter_path, 'w') as f:
                    f.write('\n'.join(new_lines))
                print("Applied fix to parameter scope handling in the 'var' method")
                return True
            else:
                print("Could not find parameter checking loop")
        else:
            print("Could not find parameter checking section")
    else:
        print("Could not find 'var' method")
    
    return False

if __name__ == "__main__":
    if apply_fix():
        print("\nFunction parameter scope fix applied successfully.")
        print("Run a test with 'python run_simple_func.py' to verify the changes.")
    else:
        print("\nFailed to apply parameter scope fix.")
