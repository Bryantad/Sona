#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/fix_return_stmt.py

"""
This script fixes the return statement handling in the Sona interpreter.
"""

from pathlib import Path

def apply_fix():
    # Path to the interpreter file
    interpreter_path = Path('sona/interpreter.py')
    if not interpreter_path.exists():
        print(f"Error: Could not find interpreter at {interpreter_path}")
        return False
    
    # Read the current content
    with open(interpreter_path, 'r') as f:
        content = f.read()
    
    # Create backup
    with open('sona/interpreter.py.bak_return_fix', 'w') as f:
        f.write(content)
    print("Created backup at sona/interpreter.py.bak_return_fix")
    
    # Find and replace the return_stmt method
    old_return_stmt = """    def return_stmt(self, args):
        if args:
            # Evaluate the return expression in the current scope
            debug(f"Processing return statement with expression: {args[0]}")
            value = self.eval_arg(args[0])
            debug(f"Return statement with value: {value}")
            raise ReturnSignal(value)
        else:
            debug("Return statement with no value")
            raise ReturnSignal(None)"""
            
    new_return_stmt = """    def return_stmt(self, args):
        if args:
            # Evaluate the return expression in the current scope
            debug(f"Processing return statement with expression: {args[0]}")
            # Enhanced debugging for return statement evaluation
            debug(f"Current environment during return: {[list(scope.keys()) for scope in self.env]}")
            value = self.eval_arg(args[0])
            debug(f"Return statement with value: {value}")
            raise ReturnSignal(value)
        else:
            debug("Return statement with no value")
            raise ReturnSignal(None)"""
    
    # Replace the return_stmt method
    modified_content = content.replace(old_return_stmt, new_return_stmt)
    
    # Write the modified content back
    with open(interpreter_path, 'w') as f:
        f.write(modified_content)
    
    print("Applied fix to return statement handling")
    return True

if __name__ == "__main__":
    if apply_fix():
        print("\nReturn statement fix applied successfully.")
    else:
        print("\nFailed to apply return statement fix.")
