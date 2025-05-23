#!/usr/bin/env python3

"""Apply a direct fix to the function parameter scope issue"""

import os
from pathlib import Path

def fix_function_call():
    interpreter_path = Path("sona/interpreter.py")
    if not interpreter_path.exists():
        print("ERROR: Interpreter file not found")
        return False
        
    # Create backup
    backup_path = Path("sona/interpreter.py.final_backup")
    with open(interpreter_path, "r") as src:
        content = src.read()
        with open(backup_path, "w") as dst:
            dst.write(content)
    print(f"Created backup at {backup_path}")
    
    # Find key sections to modify
    lines = content.split("\n")
    
    # 1. Fix var method
    var_section = []
    in_var_method = False
    var_start = -1
    var_end = -1
    
    for i, line in enumerate(lines):
        if line.strip() == "def var(self, args):":
            in_var_method = True
            var_start = i
        elif in_var_method and line.strip().startswith("def "):
            in_var_method = False
            var_end = i
            break
            
    if var_start >= 0 and var_end >= 0:
        # Replace var method with fixed version
        new_var_method = [
            "    def var(self, args):",
            "        # Simple variable name",
            "        if isinstance(args[0], Token):",
            "            name = str(args[0])",
            "",
            "            # Debug all available scopes",
            "            all_scopes = []",
            "            for i, scope in enumerate(self.env):",
            "                all_scopes.append(f\"Scope {i}: {list(scope.keys())}\")",
            "            print(f\"[FIXED] Looking for variable '{name}' in scopes: {all_scopes}\")",
            "",
            "            # First check directly in the current scope (for parameters)",
            "            if len(self.env) > 0 and name in self.env[-1]:",
            "                print(f\"[FIXED] Found '{name}' = {self.env[-1][name]} in current scope\")",
            "                return self.env[-1][name]",
            "",
            "            # Then check other scopes",
            "            for scope in reversed(self.env):",
            "                if name in scope:",
            "                    print(f\"[FIXED] Found '{name}' = {scope[name]} in scope\")",
            "                    return scope[name]",
            "",
            "            # If not found, improve error message with line and column information",
            "            if hasattr(args[0], 'line') and hasattr(args[0], 'column'):",
            "                line, column = args[0].line, args[0].column",
            "                raise NameError(f\"Variable '{name}' not found at line {line}, column {column}\")",
            "            else:",
            "                raise NameError(f\"Variable '{name}' not found\")"
        ]
        
        # Find where dotted_name starts
        for i in range(var_start, var_end):
            if "# Dotted name (e.g. module.attribute)" in lines[i]:
                var_end = i
                break
                
        # Replace the var method implementation
        lines = lines[:var_start] + new_var_method + lines[var_end:]
        print("✓ Fixed var method for parameter access")
        
    # 2. Fix function call parameter setting
    for i, line in enumerate(lines):
        if "# Create a new scope for function execution" in line:
            # Find parameter setting section
            for j in range(i, len(lines)):
                if "# Add each parameter to the function scope" in lines[j]:
                    param_start = j
                    break
            else:
                print("⚠️ Could not find parameter setting section")
                break
                
            # Replace parameter setting code
            new_param_code = [
                "        # Add each parameter to the function scope with its value - FIXED for v0.5.0",
                "        for i, (param, value) in enumerate(zip(params, passed_args)):",
                "            param_name = str(param)",
                "            print(f\"[FIXED] Setting parameter {i}: {param_name} = {value}\")",
                "            # Set parameter directly in function scope",
                "            self.env[-1][param_name] = value",
                "",
                "            # Verify parameter was set correctly",
                "            if param_name in self.env[-1]:",
                "                print(f\"[FIXED] Verified parameter {param_name} in scope {len(self.env)-1}\")",
                "            else:",
                "                print(f\"[FIXED] ERROR: Failed to set parameter {param_name}!\")"
            ]
            
            # Find the end of parameter setting section
            for j in range(param_start + 1, len(lines)):
                if "# Debug the function scope contents" in lines[j]:
                    param_end = j
                    break
            else:
                param_end = param_start + 10  # Default if not found
                
            # Replace the parameter setting section
            lines = lines[:param_start] + new_param_code + lines[param_end:]
            print("✓ Fixed function parameter setting")
            break
    else:
        print("⚠️ Could not find function scope section")
    
    # Write the modified file
    with open(interpreter_path, "w") as f:
        f.write("\n".join(lines))
    
    return True
    
if __name__ == "__main__":
    if fix_function_call():
        print("\nSuccessfully applied direct parameter scope fix.")
        print("Run 'python run_v2_test.py' to verify.")
    else:
        print("\nFailed to apply direct fix.")
