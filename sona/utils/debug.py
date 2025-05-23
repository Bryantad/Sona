"""Debug utilities for Sona"""
import os

def debug(msg):
    """Print debug messages when SONA_DEBUG=1"""
    if os.environ.get("SONA_DEBUG") == "1":
        print(f"[DEBUG] {msg}")

def trace(msg):
    """Print trace messages when SONA_DEBUG=1"""
    if os.environ.get("SONA_DEBUG") == "1":
        print(f"[TRACE] {msg}")

def warn(msg):
    """Print warning messages (always shown)"""
    print(f"[WARN] {msg}")

def error(msg):
    """Print error messages (always shown)"""
    print(f"[ERROR] {msg}")
