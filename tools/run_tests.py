#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/tools/run_tests.py
# Comprehensive test runner for Sona v0.5.0

"""
This script runs a series of tests to verify that all Sona v0.5.0 features
are working correctly:
- Function parameter scoping
- Import aliasing (with 'as' keyword)
- Multi-line string literals
- Improved error reporting

Usage:
    python tools/run_tests.py [test_name]
    
    If no test_name is provided, all tests will be run.
    Available test names: 'comprehensive', 'minimal_param', 'patch_test'
"""

import subprocess
import sys
from pathlib import Path


# Test files
TESTS = {
    'comprehensive': 'tests/fixed_comprehensive_v0.5.0_test.sona',
    'minimal_param': 'tests/minimal_param_test.sona',
    'patch_test': 'tests/v050_patch_test.sona',
}

def run_test(test_path):
    """Run a specific test file with the Sona interpreter"""
    print(f"Running test: {test_path}")
    print("-" * 50)
    
    # Get absolute path to the test file
    abs_path = Path(test_path).absolute()
    if not abs_path.exists():
        print(f"Error: Test file {abs_path} does not exist")
        return False
    
    # Run test using the Sona interpreter
    cmd = [sys.executable, "-m", "sona.sona_cli", str(abs_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Print output
    print("Output:")
    print(result.stdout)
    
    # Print any errors
    if result.stderr:
        print("Errors:")
        print(result.stderr)
        return False
    
    print(f"Test {test_path} completed successfully")
    print("-" * 50)
    return True

def run_all_tests():
    """Run all available tests"""
    print("Running all tests for Sona v0.5.0")
    print("=" * 50)
    
    failures = 0
    for test_name, test_path in TESTS.items():
        print(f"\nRunning test suite: {test_name}")
        success = run_test(test_path)
        if not success:
            failures += 1
    
    print("\nTest summary:")
    print(f"- Total tests: {len(TESTS)}")
    print(f"- Passed: {len(TESTS) - failures}")
    print(f"- Failed: {failures}")
    
    return failures == 0

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run a specific test
        test_name = sys.argv[1]
        if test_name in TESTS:
            run_test(TESTS[test_name])
        else:
            print(f"Unknown test: {test_name}")
            print(f"Available tests: {', '.join(TESTS.keys())}")
    else:
        # Run all tests
        run_all_tests()
