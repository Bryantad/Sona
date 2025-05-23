#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/run_simple_func.py

from sona.interpreter import run_code

# Run the simple function test
if __name__ == "__main__":
    with open('minimal_func.sona', 'r') as f:
        code = f.read()
        print("Running simple function test...")
        run_code(code, debug_enabled=True)
