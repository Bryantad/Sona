#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/debug_function_params.py

"""
This script will debug and examine the function parameter handling in the Sona interpreter.
"""

from sona.interpreter import SonaInterpreter, run_code, debug
import os

# Enable debug output
os.environ["SONA_DEBUG"] = "1"

def print_section(title):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)

def debug_function_case():
    """Test a simple function parameter case with debugging"""
    print_section("DEBUGGING FUNCTION PARAMETERS")
    
    # Create minimal test code
    test_code = """
    func simple_test(param) {
        print("Inside function. Parameter value: " + param)
        return param + " processed"
    }
    
    let result = simple_test("test value")
    print("Function returned: " + result)
    """
    
    # Run the code with debug output
    print("Running test code...")
    try:
        run_code(test_code, debug_enabled=True)
        print("✅ Test executed successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
    
if __name__ == "__main__":
    debug_function_case()
