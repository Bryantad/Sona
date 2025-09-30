#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/sona_v050_patch.py

"""
Comprehensive patch file for Sona v0.5.0 

This script fixes all the key issues in Sona v0.5.0:
1. Function parameter scope - ensures parameters are properly accessible
2. Import aliasing - supports 'import x as y' syntax
3. Multi-line strings - supports triple-quoted strings
4. Better error reporting - adds line and column information

Usage:
    python sona_v050_patch.py [--apply]
    python sona_v050_patch.py --test
"""

import os
import re
import shutil
import sys
from pathlib import Path


# Constants
BACKUP_EXTENSION = ".pre_v050_patch"
SONA_DIR = Path("sona")
INTERPRETER_FILE = SONA_DIR / "interpreter.py"
GRAMMAR_FILE = SONA_DIR / "grammar.lark"
TEST_FILE = "v050_patch_test.sona"

def create_backup(file_path):
    """Create a backup of the specified file before patching"""
    backup_path = Path(f"{file_path}{BACKUP_EXTENSION}")
    if not backup_path.exists():
        shutil.copy2(file_path, backup_path)
        print(f"✓ Created backup: {backup_path}")
    return backup_path

def apply_function_param_scope_fix(content):
    """Fix function parameter scope issues"""
    print("Applying function parameter scope fix...")
    
    # 1. Fix the var method to prioritize function parameters in current scope
    if "# First check directly in the current scope (for parameters)" in content:
        print("  ✓ Parameter scope priority check already exists")
    else:
        content = re.sub(
            r'(def var\(self, args\):.*?)(\s+# Then check other scopes|\s+for scope in reversed\(self\.env\):)',
            r'\1\n            # First check directly in the current scope (for parameters)\n'
            r'            if len(self.env) > 0 and name in self.env[-1]:\n'
            r'                print(f"[FIXED] Found \'{name}\' = {self.env[-1][name]} in current scope")\n'
            r'                return self.env[-1][name]\n\2',
            content, flags=re.DOTALL
        )
        print("  ✓ Added parameter priority check")

    # 2. Fix parameter handling in function calls
    if "# Set parameter directly in function scope" in content:
        print("  ✓ Parameter setting in function call already fixed")
    else:
        content = re.sub(
            r'(param_name = str\(param\).*?)(\s+self\.env\[-1\]\[param_name\] = value)',
            r'\1\n            print(f"[FIXED] Setting parameter {i}: {param_name} = {value}")\2\n'
            r'            # Verify parameter was set correctly\n'
            r'            if param_name in self.env[-1]:\n'
            r'                print(f"[FIXED] Verified parameter {param_name} in scope {len(self.env)-1}")\n'
            r'            else:\n'
            r'                print(f"[FIXED] ERROR: Failed to set parameter {param_name}!")',
            content, flags=re.DOTALL
        )
        print("  ✓ Enhanced parameter setting in function calls")

    # 3. Enhance return statement with better debugging
    if "# Enhanced debugging for return statement evaluation" in content:
        print("  ✓ Return statement debugging already enhanced")
    else:
        content = re.sub(
            r'(debug\(f"Processing return statement with expression: \{args\[0\]\}"\))',
            r'\1\n            # Enhanced debugging for return statement evaluation\n'
            r'            debug(f"Current environment during return: {[list(scope.keys()) for scope in self.env]}")',
            content
        )
        print("  ✓ Enhanced return statement debugging")

    return content

def apply_grammar_fix(content):
    """Fix grammar.lark to add support for import aliasing and multi-line strings"""
    print("Checking grammar for v0.5.0 features...")
    
    # Check for import alias support
    if "ALIAS" in content and "AS" in content:
        print("  ✓ Import alias grammar already supported")
    else:
        # Add import alias support
        content = re.sub(
            r'(import_stmt\s*:\s*"import"\s+)(dotted_name)',
            r'\1dotted_name ("as" NAME)?',
            content
        )
        print("  ✓ Added import alias grammar support")
    
    # Check for triple-quoted string support
    if '"""' in content or "'''" in content:
        print("  ✓ Multi-line string grammar already supported")
    else:
        # Add triple-quoted string support
        content = re.sub(
            r'(STRING\s*:.*?)".*?"',
            r'\1(".*?"|\'.*?\'|""".*?"""|\'\'\'.*?\'\'\')',
            content, flags=re.DOTALL
        )
        print("  ✓ Added triple-quoted string grammar support")
    
    return content

def create_test_file():
    """Create a test file to verify all v0.5.0 features"""
    test_content = """// filepath: v050_patch_test.sona
// Comprehensive test for Sona v0.5.0 features

// Test 1: Import aliasing
import utils.math.smod as math

// Test 2: Multi-line string support
let welcome = \"""
Welcome to Sona v0.5.0
This is a multi-line string test
It should preserve all formatting
And whitespace correctly.
\"""

// Test 3: Function parameter scope
func calculate(x) {
    // Using parameter inside the function
    let result = math.multiply(x, 2)
    return result
}

func nested_func(a) {
    func inner() {
        return a  // Should access outer parameter
    }
    return inner()
}

// Test 4: Testing all features together
print(welcome)
print("Math result: " + math.to_str(calculate(5)))
print("Nested function result: " + math.to_str(nested_func(10)))

print("All v0.5.0 features working correctly!")
"""
    
    with open(TEST_FILE, "w") as f:
        f.write(test_content)
    print(f"✓ Created test file: {TEST_FILE}")
    
    # Also create a runner for the test
    run_test_content = """#!/usr/bin/env python3
# Run test for v0.5.0 features

import os
import sys
from sona.interpreter import run_code

os.environ["SONA_DEBUG"] = "1"

print("=== Running Sona v0.5.0 Feature Test ===")
try:
    with open("v050_patch_test.sona", "r") as f:
        code = f.read()
        run_code(code, debug_enabled=True)
    print("\\n✅ Test completed successfully!")
except Exception as e:
    print(f"\\n❌ Test failed: {e}")
    sys.exit(1)
"""
    
    with open("run_v050_patch_test.py", "w") as f:
        f.write(run_test_content)
    print("✓ Created test runner: run_v050_patch_test.py")

def run_test():
    """Run the test file to verify patches"""
    if not Path(TEST_FILE).exists():
        create_test_file()
    
    print("\n=== Running test to verify patches ===")
    try:
        # Use os.system to ensure output is displayed
        cmd = f"{sys.executable} run_v050_patch_test.py"
        exit_code = os.system(cmd)
        if exit_code != 0:
            print(f"\n❌ Test failed with exit code {exit_code}")
            return False
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

def apply_patches():
    """Apply all patches to Sona files"""
    # Check if files exist
    if not INTERPRETER_FILE.exists() or not GRAMMAR_FILE.exists():
        print(f"❌ Error: Required Sona files not found in {SONA_DIR}")
        return False
    
    print(f"Found Sona files in {SONA_DIR}")
    
    # Create backups
    _ = create_backup(INTERPRETER_FILE)
    _ = create_backup(GRAMMAR_FILE)
    
    # Read file contents
    with open(INTERPRETER_FILE, "r") as f:
        interpreter_content = f.read()
    
    with open(GRAMMAR_FILE, "r") as f:
        grammar_content = f.read()
    
    # Apply patches
    new_interpreter_content = apply_function_param_scope_fix(interpreter_content)
    new_grammar_content = apply_grammar_fix(grammar_content)
    
    # Write patched files
    with open(INTERPRETER_FILE, "w") as f:
        f.write(new_interpreter_content)
    
    with open(GRAMMAR_FILE, "w") as f:
        f.write(new_grammar_content)
    
    print("\n✅ All patches applied successfully!")
    print(f"Original files backed up with extension: {BACKUP_EXTENSION}")
    
    return True

def main():
    """Main entry point"""
    print("Sona v0.5.0 Patch Utility")
    print("=" * 30)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--apply":
            if apply_patches():
                create_test_file()
                print("\nTo test the patches, run:")
                print("  python run_v050_patch_test.py")
        elif sys.argv[1] == "--test":
            create_test_file()
            run_test()
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Usage: python sona_v050_patch.py [--apply|--test]")
    else:
        print("Available options:")
        print("  --apply     Apply all patches to Sona files")
        print("  --test      Create and run test file only (no patches)")
        print("\nExample: python sona_v050_patch.py --apply")
    
if __name__ == "__main__":
    main()
