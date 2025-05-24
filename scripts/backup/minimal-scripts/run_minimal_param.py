#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/run_minimal_param.py

from sona.interpreter import run_code

with open('param_test.sona', 'r') as f:
    code = f.read()
    print("Running parameter test...")
    run_code(code, debug_enabled=True)
