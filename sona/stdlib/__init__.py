#!/usr/bin/env python3
"""
Sona Standard Library

This module provides core functionality for Sona programs including:
- File system operations (fs)
- HTTP client (http)
- JSON parsing (json)
- Environment variables (env)
- Time and date utilities (time, date)
- I/O operations (io)
- Mathematical functions (math)
- String utilities (string)
- Random number generation (random)
- Web utilities (web)
- Documentation helpers (docs)

All modules are automatically imported and available in Sona programs.
"""

# Core modules for IntelliSense and autocomplete - working modules only
try:
    from . import fs
except ImportError:
    fs = None

try:
    from . import path
except ImportError:
    path = None

try:
    from . import env
except ImportError:
    env = None

try:
    from . import time
except ImportError:
    time = None

try:
    from . import date
except ImportError:
    date = None

try:
    from . import json
except ImportError:
    json = None

try:
    from . import string
except ImportError:
    string = None

try:
    from . import math
except ImportError:
    math = None

try:
    from . import regex
except ImportError:
    regex = None

# Skip all other modules for now due to syntax issues
# They can be re-enabled once fixed
# from . import json
# from . import env
# from . import time
# from . import date
# from . import io
# from . import math
# from . import string
# from . import random

# Skip problematic modules for now
# from . import http
# from . import web
# from . import docs
# from . import collection

# Export available modules for autocomplete - only working ones
__all__ = []
if fs is not None:
    __all__.append('fs')
if path is not None:
    __all__.append('path')
if env is not None:
    __all__.append('env')
if time is not None:
    __all__.append('time')
if date is not None:
    __all__.append('date')
if json is not None:
    __all__.append('json')
if string is not None:
    __all__.append('string')
if math is not None:
    __all__.append('math')
if regex is not None:
    __all__.append('regex')
