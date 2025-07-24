# sona/stdlib/env.py

import os

"""
Sona Standard Library: env
--------------------------
Environment variable access for Sona programs.

Functions:
- get(key) = > returns environment variable or empty string
- set(key, value) = > sets environment variable in process
"""


def get(key): """Get an environment variable."""
    return os.environ.get(key, "")


def set(key, value): """Set an environment variable (only for current process)."""
    os.environ[str(key)] = str(value)
    return True
