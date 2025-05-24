#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/simple_v050_test.py

import os
import sys
from pathlib import Path
import importlib  # For dynamically loading modules

test_file = Path("v0.5.0_final_test.sona").resolve()
if not test_file.exists():
    print(f"Error: Test file {test_file} does not exist")
    sys.exit(1)

# Dynamically load the interpreter
try:
    sona_path = Path(__file__).parent / "sona"
    sys.path.insert(0, str(Path(__file__).parent))
    from sona.interpreter import run_code
    
    # Enable debugging
    os.environ["SONA_DEBUG"] = "1"
    
    print(f"Reading test file: {test_file}")
    with open(test_file, "r") as f:
        code = f.read()
        print("Test file content:")
        print("=" * 40)
        print(code[:200] + "..." if len(code) > 200 else code)
        print("=" * 40)
        
    print("Running test...")
    run_code(code, debug_enabled=True)
    print("✅ Test completed successfully!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
