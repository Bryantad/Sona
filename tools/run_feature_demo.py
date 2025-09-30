#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/tools/run_feature_demo.py
# Sona v0.5.0 Feature Demo Runner

"""
This script runs the v0.5.0 feature demonstration program

Usage:
    python tools/run_feature_demo.py
"""

import subprocess
import sys
from pathlib import Path


def run_demo():
    """Run the feature demonstration"""
    print("Running Sona v0.5.0 Feature Demonstration")
    print("========================================")
    
    # Get path to the demo file
    demo_file = Path("examples/v0.5.0_feature_demo.sona").absolute()
    
    if not demo_file.exists():
        print(f"Error: Demo file not found at {demo_file}")
        return False
    
    # Run demo using the Sona interpreter
    cmd = [sys.executable, "-m", "sona.sona_cli", str(demo_file)]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\nFeature demonstration completed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("\nError running feature demonstration")
        return False

if __name__ == "__main__":
    run_demo()
