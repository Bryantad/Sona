#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/fix_func_eval.py

"""
This script fixes the key function parameter evaluation issue in Sona v0.5.0.
The issue is that function parameters are being evaluated too early during function definition,
before the actual values have been passed during the function call.
"""

import os
from pathlib import Path
import shutil

# Path to the interpreter file
INTERPRETER_PATH = Path("sona/interpreter.py")

def backup_interpreter():
    """Create a backup of the interpreter file"""
    backup_path = INTERPRETER_PATH.with_suffix(".py.func_eval_bak")
    shutil.copy2(INTERPRETER_PATH, backup_path)
    print(f"Created backup at {backup_path}")

def fix_func_def():
    """Fix the func_def method in the interpreter to avoid early parameter evaluation"""
    if not INTERPRETER_PATH.exists():
        print(f"Error: Interpreter file not found at {INTERPRETER_PATH}")
        return False
        
    # Backup the file first
    backup_interpreter()
    
    # Read the current file content
    with open(INTERPRETER_PATH, "r") as f:
        content = f.readlines()
        
    # Find the func_def method
    func_def_start = None
    func_def_end = None
    for i, line in enumerate(content):
        if line.strip() == "def func_def(self, args):":
            func_def_start = i
            break
    
    if func_def_start is None:
        print("Error: Could not find func_def method in interpreter")
        return False
    
    # Find the end of the method (next method definition)
    for i in range(func_def_start + 1, len(content)):
        if content[i].strip().startswith("def "):
            func_def_end = i
            break
    
    if func_def_end is None:
        print("Error: Could not determine end of func_def method")
        return False
        
    # Extract the func_def method
    func_def_lines = content[func_def_start:func_def_end]
    
    # Create the fixed version that doesn't evaluate parameters early
    fixed_func_def = [
        "    def func_def(self, args):\n",
        "        # Function name, parameters list, and body\n",
        "        name, param_list, body = args\n",
        "        \n",
        "        # Clean and store parameter names without evaluating\n",
        "        params = []\n",
        "        \n",
        "        # Process parameter list appropriately depending on type\n",
        "        if param_list is None:\n",
        "            # No parameters\n",
        "            debug(f\"Function {name} has no parameters\")\n",
        "            params = []\n",
        "        elif isinstance(param_list, Tree) and param_list.data == 'param_list':\n",
        "            # This is a normal param_list tree node\n",
        "            for child in param_list.children:\n",
        "                if isinstance(child, Token) and child.type == 'NAME':\n",
        "                    params.append(child)\n",
        "                    debug(f\"Added parameter: {child}\")\n",
        "        elif hasattr(param_list, 'children'):\n",
        "            # Generic tree with children\n",
        "            for child in param_list.children:\n",
        "                if isinstance(child, Token) and child.type == 'NAME':\n",
        "                    params.append(child)\n",
        "                    debug(f\"Added parameter from children: {child}\")\n",
        "        elif isinstance(param_list, list):\n",
        "            # Already processed list of parameters\n",
        "            params = [p for p in param_list if isinstance(p, Token) and p.type == 'NAME']\n",
        "            debug(f\"Parameters from list: {[str(p) for p in params]}\")\n",
        "        else:\n",
        "            # Single parameter as a token\n",
        "            if isinstance(param_list, Token) and param_list.type == 'NAME':\n",
        "                params = [param_list]\n",
        "                debug(f\"Single parameter: {param_list}\")\n",
        "        \n",
        "        debug(f\"Function '{name}' registered with parameters: {[str(p) for p in params]}\")\n",
        "        \n",
        "        # Register function with its parameters and body\n",
        "        # Do not evaluate the body during function definition\n",
        "        self.functions[str(name)] = (params, body)\n",
        "        return name\n",
    ]
    
    # Replace the old method with the new one
    new_content = content[:func_def_start] + fixed_func_def + content[func_def_end:]
    
    # Write the updated content back
    with open(INTERPRETER_PATH, "w") as f:
        f.writelines(new_content)
    
    print("✅ Successfully updated func_def method to avoid early parameter evaluation")
    return True

def main():
    """Main entry point"""
    print("Fixing function parameter evaluation in Sona v0.5.0...")
    if fix_func_def():
        print("\nTo test the fix, run one of the test scripts:")
        print("  python run_minimal_param_test.py")
        print("  python run_v050_patch_test.py")
    else:
        print("\nFailed to apply fix")

if __name__ == "__main__":
    main()
