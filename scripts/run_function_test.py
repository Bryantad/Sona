#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/run_function_test.py

import os
from sona.interpreter import run_code

# Enable debug output
os.environ["SONA_DEBUG"] = "1"

print("=== Running function parameter test for v0.5.0 ===")
with open("function_test.sona", "r") as f:
    code = f.read()
    run_code(code, debug_enabled=True)
