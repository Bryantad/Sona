#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/run_v050_patch_test.py
# Run test for v0.5.0 features

import os
import sys
from sona.interpreter import run_code

# Enable debug output
os.environ["SONA_DEBUG"] = "1"

print("=== Running Sona v0.5.0 Feature Test ===")
try:
    with open("v050_patch_test.sona", "r") as f:
        code = f.read()
        run_code(code, debug_enabled=True)
    print("\n✅ Test completed successfully!")
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    sys.exit(1)
