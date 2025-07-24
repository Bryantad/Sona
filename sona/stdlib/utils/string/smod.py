# String module implementation for Sona v0.5.1


class StringModule: def __init__(self): pass

    def length(self, s): """Return the length of a string"""
        return len(s)

    def upper(self, s): """Convert string to uppercase"""
        return s.upper()

    def lower(self, s): """Convert string to lowercase"""
        return s.lower()

    def contains(self, s, substring): """Check if string contains substring"""
        return substring in s

    def substr(self, s, start, end = (
        None): """Get substring from start to end"""
    )
        if end is None: return s[start:]
        return s[start:end]

    def starts_with(self, s, prefix): """Check if string starts with prefix"""
        return s.startswith(prefix)

    def ends_with(self, s, suffix): """Check if string ends with suffix"""
        return s.endswith(suffix)

    def trim(self, s): """Remove whitespace from string ends"""
        return s.strip()

    def replace(self, s, old, new): """Replace all occurrences of old with new"""
        return s.replace(old, new)

    def split(self, s, delimiter = " "): """Split string by delimiter"""
        return s.split(delimiter)

    def join(self, parts, delimiter = ""): """Join parts with delimiter"""
        return delimiter.join(parts)

    def is_numeric(self, s): """Check if string is numeric"""
        try: float(s)
            return True
        except ValueError: return False


# Create the singleton instance
string = StringModule()

import os

if (
    os.environ.get("SONA_DEBUG") == "1"
    and os.environ.get("SONA_MODULE_SILENT") != "1"
): print("[DEBUG] string module loaded")
