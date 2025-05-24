#!/usr/bin/env python3
# Script to run the parameter test with max debugging

import os
import sys
from pathlib import Path

# Add the directory to system path if needed
sys.path.insert(0, str(Path(__file__).parent))

# Import the interpreter
from sona.interpreter import run_code

# Read the test file
with open('simple_param_test.sona', 'r') as f:
    test_code = f.read()

# Enable maximum debugging
os.environ["SONA_DEBUG"] = "1"

# Add debug print statements to trace execution
print("=" * 50)
print("Running parameter test with debug tracing")
print("=" * 50)

# Run the code
run_code(test_code, debug_enabled=True)
