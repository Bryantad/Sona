#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/direct_param_fix.py
# Direct fix for function parameter scope in Sona v0.5.0

import os
import sys
import re
from pathlib import Path
import shutil

def apply_direct_fix():
    """Apply critical fix for function parameter scope"""
    interpreter_path = Path("sona/interpreter.py")
    if not interpreter_path.exists():
        print(f"❌ Error: Interpreter file not found at {interpreter_path}")
        return False
        
    # Create backup
    backup_path = Path("sona/interpreter.py.param_fix_bak")
    shutil.copy2(interpreter_path, backup_path)
    print(f"Created backup at {backup_path}")
    
    # Read current content
    with open(interpreter_path, "r") as f:
        content = f.read()
    
    # Add debug code to var method
    var_debug_added = False
    if not "# Debug all available scopes" in content:
        # Add scope debugging to var method
        content = re.sub(
            r'(def var\(self, args\):.*?)(# Simple variable name.*?if isinstance\(args\[0\], Token\):.*?name = str\(args\[0\]))',
            r'\1\2\n\n            # Debug all available scopes\n'
            r'            all_scopes = []\n'
            r'            for i, scope in enumerate(self.env):\n'
            r'                all_scopes.append(f"Scope {i}: {list(scope.keys())}")\n'
            r'            print(f"[FIXED] Looking for variable \'{name}\' in scopes: {all_scopes}")',
            content, flags=re.DOTALL
        )
        var_debug_added = True
        
    # Add parameter priority check
    var_fixed = False
    if not "# First check directly in the current scope (for parameters)" in content:
        # Add parameter priority check to var method
        content = re.sub(
            r'(# Debug all available scopes.*?print\(f"\[FIXED\] Looking for variable.*?)(\s+# Then check other scopes|\s+for scope in reversed\(self\.env\):)',
            r'\1\n\n            # First check directly in the current scope (for parameters)\n'
            r'            if len(self.env) > 0 and name in self.env[-1]:\n'
            r'                print(f"[FIXED] Found \'{name}\' = {self.env[-1][name]} in current scope")\n'
            r'                return self.env[-1][name]\2',
            content, flags=re.DOTALL
        )
        var_fixed = True
        
    # Add parameter setting debug
    param_setting_fixed = False
    if not "[FIXED] Setting parameter" in content:
        # Enhance function call parameters
        content = re.sub(
            r'(param_name = str\(param\).*?)(\s+self\.env\[-1\]\[param_name\] = value)',
            r'\1\n            print(f"[FIXED] Setting parameter {i}: {param_name} = {value}")\2\n\n'
            r'            # Verify parameter was set correctly\n'
            r'            if param_name in self.env[-1]:\n'
            r'                print(f"[FIXED] Verified parameter {param_name} in scope {len(self.env)-1}")\n'
            r'            else:\n'
            r'                print(f"[FIXED] ERROR: Failed to set parameter {param_name}!")',
            content, flags=re.DOTALL
        )
        param_setting_fixed = True
        
    # Write updated content
    with open(interpreter_path, "w") as f:
        f.write(content)
    
    if var_debug_added or var_fixed or param_setting_fixed:
        print(f"✅ Successfully applied function parameter scope fixes:")
        if var_debug_added:
            print("  - Added scope debugging")
        if var_fixed:
            print("  - Added parameter priority check")
        if param_setting_fixed:
            print("  - Enhanced parameter setting")
        return True
    else:
        print("⚠️ No changes needed, fixes already applied")
        return True
        
if __name__ == "__main__":
    print("Applying direct function parameter scope fix for Sona v0.5.0...")
    if apply_direct_fix():
        print("\nTo test the fix, run:")
        print("python run_v050_patch_test.py")
    else:
        print("\nFailed to apply fixes")
        sys.exit(1)
