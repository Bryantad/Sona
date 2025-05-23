#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/run_v050_final_test.py

import os
import sys
from pathlib import Path
from sona.interpreter import run_code

# Enable debug output
os.environ["SONA_DEBUG"] = "1"

print("=== Running Final Sona v0.5.0 Test ===")

test_file = "v0.5.0_final_test.sona"
try:
    with open(test_file, "r") as f:
        code = f.read()
        run_code(code, debug_enabled=True)
    print("\n✅ Test completed successfully!")
except Exception as e:
    print(f"\n❌ Error running test: {e}")
    sys.exit(1)
