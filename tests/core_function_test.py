#!/usr/bin/env python3
"""
Simple Function Parameter Test
Tests that the critical function parameter scope fixes are working
"""

import os
import sys
from pathlib import Path

# Add Sona to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sona.interpreter import run_code

def test_simple_function():
    """Test that basic function parameters work"""
    print("\n=== Simple Function Parameter Test ===")
    
    code = '''
func double(x) {
    return x * 2
}

print(double(5))
'''
    
    try:
        run_code(code, debug_enabled=False)
        print("✅ Simple function test PASSED")
        return True
    except Exception as e:
        print(f"❌ Simple function test FAILED: {e}")
        return False

def test_function_with_multiple_params():
    """Test function with multiple parameters"""
    print("\n=== Multiple Parameters Test ===")
    
    code = '''
func multiply(a, b) {
    return a * b
}

print(multiply(3, 4))
'''
    
    try:
        run_code(code, debug_enabled=False)
        print("✅ Multiple parameters test PASSED")
        return True
    except Exception as e:
        print(f"❌ Multiple parameters test FAILED: {e}")
        return False

def test_enhanced_error_messages():
    """Test that enhanced error messages work"""
    print("\n=== Enhanced Error Messages Test ===")
    
    # Test function not found
    code = '''
missing_func()
'''
    
    try:
        run_code(code, debug_enabled=False)
        print("❌ Should have failed")
        return False
    except Exception as e:
        error_msg = str(e)
        if "not defined" in error_msg and "line" in error_msg:
            print("✅ Enhanced error message test PASSED")
            print(f"   Error: {error_msg}")
            return True
        else:
            print(f"❌ Error message not enhanced enough: {error_msg}")
            return False

def main():
    """Run simplified tests for core functionality"""
    print("🔧 Testing Core Function Parameter Fixes")
    print("=" * 50)
    
    tests = [
        test_simple_function,
        test_function_with_multiple_params,
        test_enhanced_error_messages
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{len(tests)} core tests passed")
    
    if passed == len(tests):
        print("🎉 Core function parameter fixes are working!")
    else:
        print("⚠️  Some core functionality needs additional work")

if __name__ == "__main__":
    main()
