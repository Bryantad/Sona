import os
import sys
from sona.interpreter import SonaInterpreter, run_code

# Test code with a simple function that uses parameters
test_code = """
// Simple function parameter test
func add(a, b) {
    let result = a + b
    print("Adding " + a + " + " + b + " = " + result)
    return result
}

// Call the function
let sum = add(5, 7)
print("Sum is: " + sum)
"""

# Run the test
print("=== Testing Function Parameters ===")
os.environ["SONA_DEBUG"] = "1"  # Enable debug mode

try:
    result = run_code(test_code, debug_enabled=True)
    print("\nTest succeeded with result:", result)
    sys.exit(0)
except Exception as e:
    print("\nTest failed with error:", e)
    sys.exit(1)
