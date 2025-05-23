#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/run_minimal_v050.py

import os
from pathlib import Path
from sona.interpreter import run_code

# Set up debug mode
os.environ["SONA_DEBUG"] = "1"

# Run the minimal test
print("=== Running Minimal v0.5.0 Test ===")
test_file = Path("minimal_v050_test.sona")
with open(test_file, "r") as f:
    code = f.read()
    run_code(code, debug_enabled=True)
