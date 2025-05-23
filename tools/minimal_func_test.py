import os
from sona.interpreter import SonaInterpreter, run_code
from lark import Lark

test_code = """
// Simple function with parameters
func test(x, y) {
    let z = x + y
    return z
}

// Call the function
test(2, 3)
"""

def main():
    """Run a minimal test for function parameters"""
    print("=== Running Minimal Function Parameter Test ===")
    
    # Parse and execute the test code
    try:
        os.environ["SONA_DEBUG"] = "1"  # Enable debug logging
        result = run_code(test_code, debug_enabled=True)
        print(f"Result: {result}")
        print("Test passed!")
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
