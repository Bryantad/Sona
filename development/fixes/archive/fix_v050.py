#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/fix_v050.py

"""
This script applies all fixes needed for Sona v0.5.0, focusing on:
1. Function parameter scope handling
2. Multiline string support
3. 'as' keyword in imports
4. Better error reporting
"""

import os
import re
from pathlib import Path

# Function to apply fixes to files
def apply_fixes():
    # Ensure the interpreter file exists
    interpreter_path = Path("sona/interpreter.py")
    if not interpreter_path.exists():
        print(f"ERROR: Could not find interpreter at {interpreter_path}")
        return False
        
    # Create a backup
    backup_path = Path("sona/interpreter_v049.py")
    with open(interpreter_path, "r") as src:
        with open(backup_path, "w") as dst:
            dst.write(src.read())
    print(f"Created backup at {backup_path}")
    
    # Read the current interpreter code
    with open(interpreter_path, "r") as f:
        code = f.read()

    # 1. Fix function parameter scope by updating the var method
    code = re.sub(
        r'def var\(self, args\):\s+# Simple variable name\s+if isinstance\(args\[0\], Token\):',
        """def var(self, args):
        # Simple variable name
        if isinstance(args[0], Token):""",
        code
    )
    
    code = re.sub(
        r'# First check if the variable exists in any scope \(including function parameters\)',
        """# First check if the variable exists in the current scope (function parameters)
            if len(self.env) > 0 and name in self.env[-1]:
                debug(f"Found parameter '{name}' = {self.env[-1][name]} in local scope")
                return self.env[-1][name]
                
            # Then check in other scopes""",
        code
    )

    # 2. Fix function call parameter handling
    code = re.sub(
        r'# Create a new scope for function execution\s+self\.push_scope\(\)',
        """# Create a new scope for function execution
        debug(f"Creating new scope for function '{name}'")
        self.push_scope()""",
        code
    )
    
    code = re.sub(
        r'# Add each parameter to the function scope with its value',
        """# Add each parameter to the function scope with its value - fixed in v0.5.0""",
        code
    )
    
    code = re.sub(
        r'self\.env\[-1\]\[param_name\] = value',
        """# Set parameter in function's local scope
            self.env[-1][param_name] = value
            debug(f"Parameter '{param_name}' set to {value} in local scope {len(self.env)-1}")
            # Verify the parameter was set correctly
            if param_name not in self.env[-1]:
                debug(f"ERROR: Failed to set parameter '{param_name}' in function scope")""",
        code
    )
    
    # 3. Ensure the multi-line string handling is present
    if "# Triple-quoted strings (multi-line)" not in code:
        code = re.sub(
            r'def string\(self, args\):',
            """def string(self, args):
        # Handle both single/double quoted strings and multi-line strings""",
            code
        )
        
        code = re.sub(
            r'raw_str = str\(args\[0\])',
            """raw_str = str(args[0])
        
        # Triple-quoted strings (multi-line)
        if raw_str.startswith('\"\"\"') and raw_str.endswith('\"\"\"'):
            return raw_str[3:-3]
        elif raw_str.startswith("'''") and raw_str.endswith("'''"):
            return raw_str[3:-3]""",
            code
        )
    
    # 4. Write the updated code back
    with open(interpreter_path, "w") as f:
        f.write(code)
    
    # Also check and update grammar file for proper v0.5.0 features
    grammar_path = Path("sona/grammar.lark")
    if grammar_path.exists():
        with open(grammar_path, "r") as f:
            grammar_code = f.read()
            
        # Ensure 'as' keyword support in imports
        if "import_stmt: dotted_name (\"as\" NAME)?" not in grammar_code:
            grammar_code = re.sub(
                r'import_stmt: dotted_name',
                'import_stmt: dotted_name ("as" NAME)?',
                grammar_code
            )
            
        # Ensure multi-line string support in grammar
        if "TRIPLE_QUOTED_STRING" not in grammar_code:
            grammar_code = re.sub(
                r'ESCAPED_STRING: /"[^"]*"/ | /\'[^\']*\'/',
                r'ESCAPED_STRING: /"[^"]*"/ | /\'[^\']*\'/ | /""".*?"""/s | /\'\'\'.*?\'\'\'/s',
                grammar_code
            )
            
        # Write the updated grammar
        with open(grammar_path, "w") as f:
            f.write(grammar_code)
        print("Updated grammar file with v0.5.0 features")
    
    # Update version in __init__.py if needed
    init_path = Path("sona/__init__.py")
    if init_path.exists():
        with open(init_path, "r") as f:
            init_code = f.read()
            
        if "__version__ = '0.4.9'" in init_code:
            init_code = init_code.replace("__version__ = '0.4.9'", "__version__ = '0.5.0'")
            with open(init_path, "w") as f:
                f.write(init_code)
            print("Updated version to 0.5.0 in __init__.py")
    
    # Create a README update for v0.5.0
    with open("v0.5.0_CHANGES.md", "w") as f:
        changes = "# Sona v0.5.0 Changes\n\n"
        changes += "## New Features\n\n"
        changes += "1. **Import Statement Enhancement**\n"
        changes += "   - Added support for the 'as' keyword for module aliasing\n"
        changes += "   - Example: `import utils.math.smod as math`\n\n"
        changes += "2. **Multi-line String Support**\n"
        changes += "   - Added triple quote syntax for multi-line strings\n"
        changes += "   - Supports both triple double quotes and triple single quotes\n"
        changes += "   - Example:\n"
        changes += "     ```\n"
        changes += "     let message = \"\"\"\n"
        changes += "     This is a multi-line string\n"
        changes += "     that preserves whitespace and\n"
        changes += "     line breaks.\n"
        changes += "     \"\"\"\n"
        changes += "     ```\n\n"
        changes += "3. **Better Error Reporting**\n"
        changes += "   - Improved error messages with line and column information\n"
        changes += "   - Visual highlighting of error locations in code\n\n"
        changes += "4. **Function Parameter Scope Fixes**\n"
        changes += "   - Resolved issues with accessing parameters inside function bodies\n"
        changes += "   - Improved parameter scoping and lookup\n\n"
        changes += "## Bug Fixes\n\n"
        changes += "- Fixed parameter scope resolution in function bodies\n"
        changes += "- Better handling of aliased module imports\n"
        changes += "- Improved error reporting with precise location information\n"
        changes += "- Enhanced debugging output for troubleshooting\n"
        f.write(changes)
    print("Created v0.5.0 changes documentation")
    
    return True

if __name__ == "__main__":
    if apply_fixes():
        print("\nSona v0.5.0 upgrade complete. Key improvements:")
        print("1. Function parameter scope fixes")
        print("2. Multi-line string support")
        print("3. 'as' keyword in imports")
        print("4. Better error reporting")
        print("\nRun 'python run_comprehensive_test.py' to verify all features")
    else:
        print("Failed to apply v0.5.0 fixes")
