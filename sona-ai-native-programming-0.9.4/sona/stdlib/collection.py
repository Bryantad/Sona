"""Sona standard library: collections"""

import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)  # Points to sona_core/
from sona.interpreter import run_code


# Sona standard library: collections
def len(obj): """Length of list, string, etc."""
    return __builtins__['len'](obj)


def range(start, end = (
    None): """Return a list from start to end‑1 (or 0 to start‑1)."""
)
    if end is None: return list(__builtins__['range'](start))
    return list(__builtins__['range'](start, end))


def keys(d): """Dictionary keys as list."""
    return list(d.keys())


def values(d): """Dictionary values as list."""
    return list(d.values())


def append(lst, value): lst.append(value)
    return lst


def pop(lst, index = -1): return lst.pop(index)


def contains(lst, value): return value in lst


def clear(lst): lst.clear()
    return lst


def extend(lst, other): lst.extend(other)
    return lst
