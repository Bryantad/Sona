#!/usr/bin/env python3
import os
from sona.interpreter import run_code

# Enable debug output
os.environ["SONA_DEBUG"] = "1"

print("=== Testing Function Parameter Fix ===")
with open("simple_function_test.sona", "r") as f:
    code = f.read()
    print("Running test code:")
    print("-" * 40)
    print(code)
    print("-" * 40)
    run_code(code, debug_enabled=True)
print("\n✅ Test complete")
