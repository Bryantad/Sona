#!/usr/bin/env python3
"""
Sona v0.9.6 - Direct Program Runner
Executes .sona files without requiring installation
"""

import sys
import os

# Version assertion - fail fast if version drifted
try:
    # Add current dir to path first
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from sona import __version__ as SONA_VERSION
    assert SONA_VERSION.startswith("0.9.6"), f"Expected 0.9.6, got {SONA_VERSION}"
except ImportError:
    print("⚠️  Warning: Could not verify Sona version (module not in path)")
except AssertionError as e:
    print(f"❌ Version mismatch: {e}")
    sys.exit(1)

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Suppress parser initialization messages by temporarily redirecting stdout
_original_stdout = sys.stdout
_original_stderr = sys.stderr

# Redirect to null during imports
import io as _io
sys.stdout = _io.StringIO()
sys.stderr = _io.StringIO()

from sona.parser_v090 import SonaParserv090
from sona.interpreter import SonaUnifiedInterpreter

# Restore output
sys.stdout = _original_stdout
sys.stderr = _original_stderr


def run_sona_file(filename):
    """Run a Sona program file."""
    if not os.path.exists(filename):
        print(f"Error: File not found: {filename}")
        return 1
    
    # Read source code
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:  # utf-8-sig strips BOM
            source = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return 1
    
    # Execute the entire file as a Sona program
    try:
        interpreter = SonaUnifiedInterpreter()
        
        # Check if source contains Sona-specific keywords
        sona_keywords = ['let', 'const', 'func', 'import', '//', 'true', 'false']
        has_sona_syntax = any(keyword in source for keyword in sona_keywords)
        
        if has_sona_syntax:
            # Parse as complete Sona program
            result = interpreter.interpret(source, filename=filename)
        else:
            # Fall back to line-by-line Python-like execution
            lines = source.strip().split('\n')
            result = None
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                result = interpreter.interpret(line)
                
    except Exception as e:
        print(f"Runtime error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quick_run.py <file.sona>")
        sys.exit(1)
    
    sys.exit(run_sona_file(sys.argv[1]))
