#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/run_final_test.py

import os
from sona.interpreter import run_code

# Enable debug mode
os.environ["SONA_DEBUG"] = "1"

# Run the final function test
if __name__ == "__main__":
    with open('final_function_test.sona', 'r') as f:
        code = f.read()
        print("Running final function parameter scope test...")
        run_code(code, debug_enabled=True)
