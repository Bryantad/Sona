#!/usr/bin/env python3
"""
Compatibility runner that forwards to run_sona.py.
"""

import sys
from run_sona import main


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
