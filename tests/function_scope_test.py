#!/usr/bin/env python3
"""
Direct fix for the function parameter scope issue in Sona v0.5.0
"""

from sona.interpreter import run_code

# Define minimal test case with just a simple function
test_code = """
func square(x) {
    return x * x
}

print("5 squared = " + square(5))
"""

# Run the test
print("Running function parameter test...")
run_code(test_code, debug_enabled=True)
