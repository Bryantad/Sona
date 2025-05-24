#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/fix_param_call.py

"""
This script directly modifies the function_call method to properly handle parameters
in the Sona v0.5.0 interpreter.
"""

from pathlib import Path

# Path to the interpreter file
interpreter_path = Path("sona/interpreter.py")

# Read the content
with open(interpreter_path, "r") as f:
    lines = f.readlines()

# Find the function call implementation
func_call_start = -1
func_call_end = -1

for i, line in enumerate(lines):
    if line.strip() == "def func_call(self, args):":
        func_call_start = i
        break

if func_call_start >= 0:
    for i in range(func_call_start + 1, len(lines)):
        if line.strip().startswith("def "):
            func_call_end = i
            break

    if func_call_end > 0:
        # Find the part where parameters are added to the function scope
        param_setting_start = -1
        param_setting_end = -1
        
        for i in range(func_call_start, func_call_end):
            if "# Add each parameter to the function scope with its value" in lines[i]:
                param_setting_start = i
                break
        
        if param_setting_start > 0:
            # Find where the parameter setting block ends
            for i in range(param_setting_start + 1, func_call_end):
                if "try:" in lines[i].strip():
                    param_setting_end = i
                    break
            
            if param_setting_end > 0:
                # Insert enhanced parameter handling
                enhanced_param_code = [
                    "        # Add each parameter to the function scope with its value - enhanced for v0.5.0\n",
                    "        for i, (param, value) in enumerate(zip(params, passed_args)):\n",
                    "            param_name = str(param)\n",
                    "            debug(f\"Setting function parameter {i}: {param_name} = {value}\")\n",
                    "            # Ensure the parameter is properly set in the function's local scope\n",
                    "            self.env[-1][param_name] = value\n",
                    "            debug(f\"Parameter {param_name} added to scope {len(self.env)-1}\")\n",
                    "        \n",
                    "        # Debug the function scope contents after setting parameters\n",
                    "        scope_contents = \", \".join([f\"{k}={v}\" for k, v in self.env[-1].items()])\n",
                    "        debug(f\"Function '{name}' scope parameters: {scope_contents}\")\n",
                    "        debug(f\"Current environment structure: {[list(scope.keys()) for scope in self.env]}\")\n",
                    "        \n"
                ]
                
                # Replace the parameter setting code
                new_lines = lines[:param_setting_start] + enhanced_param_code + lines[param_setting_end:]
                
                # Write the modified file
                with open(interpreter_path, "w") as f:
                    f.writelines(new_lines)
                
                print("Enhanced function parameter handling applied")
            else:
                print("Could not find parameter setting end")
        else:
            print("Could not find parameter setting section")
    else:
        print("Could not find function_call end")
else:
    print("Could not find function_call method")
