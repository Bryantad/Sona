# Direct fix for Sona function parameter scope issue

import os
from pathlib import Path
from lark import Lark

# Get the Sona code path
sona_path = Path("/Volumes/project usb/WayCore Inc/sona_core/sona")
interpreter_path = sona_path / "interpreter.py"

# Read the current interpreter.py content
with open(interpreter_path, "r") as f:
    interpreter_code = f.read()

# Define a patch for the var method to fix parameter scope
var_patch = """
    def var(self, args):
        name = str(args[0])
        # For parameter debug
        if self.env:
            print(f"Looking for var: {name} in scopes: {[list(scope.keys()) for scope in self.env]}")
        try:
            for scope in reversed(self.env):
                if name in scope:
                    return scope[name]
            raise NameError(f"Variable '{name}' not found")
        except NameError as e:
            if hasattr(args[0], 'line') and hasattr(args[0], 'column'):
                line, column = args[0].line, args[0].column
                print(f"Error finding variable '{name}' at line {line}, column {column}")
            raise e
"""

# Find the current var method and replace it
var_method_start = "    def var(self, args):"
var_method_end = "            raise ValueError(f\"Invalid variable reference: {name}\")"

# Apply patch
with open(interpreter_path, "r") as f:
    lines = f.readlines()

# Find the var method
var_start_idx = None
var_end_idx = None
for i, line in enumerate(lines):
    if line.strip() == "def var(self, args):":
        var_start_idx = i
        break

if var_start_idx:
    # Find the end of the method (next method or class)
    for i in range(var_start_idx + 1, len(lines)):
        if lines[i].strip().startswith("def "):
            var_end_idx = i
            break

    if var_end_idx:
        # Create the new file content
        new_lines = lines[:var_start_idx] + [var_patch] + lines[var_end_idx:]
        
        # Save to a new file
        new_path = Path("/Volumes/project usb/WayCore Inc/sona_core/sona/interpreter_fixed.py")
        with open(new_path, "w") as f:
            f.writelines(new_lines)
            
        print(f"Patched interpreter saved to: {new_path}")
