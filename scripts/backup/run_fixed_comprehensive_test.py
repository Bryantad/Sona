#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from sona.interpreter import run_code

# Enable debug output
os.environ["SONA_DEBUG"] = "1"

print("=== Running comprehensive v0.5.0 test with fixes ===")
try:
    test_file = Path("fixed_comprehensive_v0.5.0_test.sona").resolve()
    if not test_file.exists():
        print(f"ERROR: Test file not found at {test_file}")
        sys.exit(1)
        
    print(f"Running test file: {test_file}")
    with open(test_file, "r") as f:
        code = f.read()
        run_code(code, debug_enabled=True)
    print("✅ Test completed successfully!")
except Exception as e:
    print(f"❌ Error running test: {e}")
    sys.exit(1)
