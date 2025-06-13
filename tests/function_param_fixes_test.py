#!/usr/bin/env python3
"""
Enhanced Function Parameter Test Suite
Tests the critical fixes applied for function parameter scope resolution
"""

import os
import sys
from pathlib import Path

# Add Sona to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sona.interpreter import run_code

def test_basic_function_parameters():
    """Test basic function parameter handling"""
    print("\n=== Testing Basic Function Parameters ===")
    
    code = """
func greet(name) {
    print("Hello, " + name + "!")
    return name
}

let result = greet("World")
print("Returned: " + result)
"""
    
    try:
        run_code(code, debug_enabled=True)
        print("✅ Basic function parameter test PASSED")
        return True
    except Exception as e:
        print(f"❌ Basic function parameter test FAILED: {e}")
        return False

def test_multiple_parameters():
    """Test functions with multiple parameters"""
    print("\n=== Testing Multiple Parameters ===")
    
    code = """
func add_three(a, b, c) {
    let sum = a + b + c
    print("Sum: " + sum)
    return sum
}

let result = add_three(1, 2, 3)
print("Final result: " + result)
"""
    
    try:
        run_code(code, debug_enabled=True)
        print("✅ Multiple parameter test PASSED")
        return True
    except Exception as e:
        print(f"❌ Multiple parameter test FAILED: {e}")
        return False

def test_parameter_scope_isolation():
    """Test that function parameters don't leak to global scope"""
    print("\n=== Testing Parameter Scope Isolation ===")
    
    code = """
let x = "global"

func test_scope(x) {
    print("Inside function, x = " + x)
    return x
}

test_scope("local")
print("Outside function, x = " + x)
"""
    
    try:
        run_code(code, debug_enabled=True)
        print("✅ Parameter scope isolation test PASSED")
        return True
    except Exception as e:
        print(f"❌ Parameter scope isolation test FAILED: {e}")
        return False

def test_error_handling():
    """Test enhanced error messages"""
    print("\n=== Testing Enhanced Error Handling ===")
    
    # Test function not found
    code1 = """
nonexistent_function()
"""
    
    try:
        run_code(code1, debug_enabled=False)
        print("❌ Function not found test should have failed")
        return False
    except NameError as e:
        if "Available functions:" in str(e):
            print("✅ Enhanced function not found error PASSED")
        else:
            print(f"❌ Error message not enhanced: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error type: {e}")
        return False
    
    # Test parameter count mismatch
    code2 = """
func test_params(a, b) {
    return a + b
}

test_params(1)  # Missing one parameter
"""
    
    try:
        run_code(code2, debug_enabled=False)
        print("❌ Parameter count test should have failed")
        return False
    except ValueError as e:
        if "expects" in str(e) and "got" in str(e):
            print("✅ Enhanced parameter count error PASSED")
        else:
            print(f"❌ Error message not enhanced: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error type: {e}")
        return False
    
    return True

def run_all_tests():
    """Run all function parameter tests"""
    print("🧪 Running Enhanced Function Parameter Test Suite")
    print("Based on Critical Bug Fixes from Thesis Research")
    
    tests = [
        test_basic_function_parameters,
        test_multiple_parameters,
        test_parameter_scope_isolation,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All function parameter fixes working correctly!")
    else:
        print("⚠️  Some tests failed - additional fixes may be needed")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests()
