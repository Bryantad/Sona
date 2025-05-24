#!/usr/bin/env python3

import os
from sona.interpreter import run_code

# Enable debugging
os.environ["SONA_DEBUG"] = "1"

print("=== Running v0.5.0 function parameter scope test ===")
with open("function_v2_test.sona", "r") as f:
    code = f.read()
    run_code(code, debug_enabled=True)
