#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/run_fixed_test.py

import sys
import os
from pathlib import Path

# Add the correct directory to the path
sys.path.insert(0, os.path.abspath('.'))

# Import the fixed interpreter
from sona.interpreter_fixed import SonaInterpreter, run_code as original_run_code

# Create a modified run_code function that uses the fixed interpreter
def run_code(code, debug_enabled=False):
    """Run Sona code using the fixed interpreter."""
    print("[FIXED] Running with patched interpreter")
    return original_run_code(code, debug_enabled=debug_enabled)

# Run the test
if __name__ == "__main__":
    try:
        # Check if a file was provided
        if len(sys.argv) > 1:
            test_file = sys.argv[1]
            with open(test_file, 'r') as f:
                code = f.read()
                run_code(code, debug_enabled=True)
        else:
            # Default to the simple parameter test
            with open('simple_param_fixed.sona', 'r') as f:
                code = f.read()
                run_code(code, debug_enabled=True)
    except Exception as e:
        print(f"Error: {e}")
