"""Debug utilities for suppressing debug output"""
import os
import sys
from contextlib import contextmanager
import io

@contextmanager
def suppress_debug_output():
    """Context manager to temporarily suppress stdout"""
    if os.environ.get("SONA_DEBUG") != "1":
        original_stdout = sys.stdout
        sys.stdout = io.StringIO()  # Redirect stdout to string buffer
        try:
            yield
        finally:
            sys.stdout = original_stdout  # Restore original stdout
    else:
        yield  # Do nothing in debug mode
