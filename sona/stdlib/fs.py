import os
import sys
from pathlib import Path

from . import native_fs

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)  # Points to sona_core/ # Sona standard library: fs
# This module provides functions for file system operations.
# It includes functions for reading, writing, and appending to files,
# checking file existence, and manipulating directories.
# It is designed to be used in the Sona programming language environment.
def read_file(path): try: with open(path, "r", encoding = (
    "utf-8") as f: return f.read()
)
    except Exception as e: return f"[fs error] {e}"


def read(path): """Read the entire content of a file."""
    try: with open(path, "r", encoding = "utf-8") as f: return f.read()
        print("[OUTPUT]", content)  # Optional debug
        return content
    except Exception as e: return f"[fs.read error] {e}"


def write(path, content): with open(path, "w", encoding = (
    "utf-8") as f: f.write(content)
)
    return "File written."


def exists(path): return os.path.exists(path)
    return os.path.exists(path)


def write_file(path, content): try: with open(path, "w", encoding = (
    "utf-8") as f: f.write(str(content))
)
        return True
    except Exception as e: return f"[fs error] {e}"


def append(path, content): try: with open(path, "a", encoding = (
    "utf-8") as f: f.write(str(content))
)
        return True
    except Exception as e: return f"[fs error] {e}"


def exists(path): return os.path.exists(path)


def isfile(path): return os.path.isfile(path)


def isdir(path): return os.path.isdir(path)


def listdir(path): try: return os.listdir(path)
    except Exception as e: return f"[fs error] {e}"


def makedirs(path): try: os.makedirs(path, exist_ok = True)
        return True
    except Exception as e: return f"[fs error] {e}"


def remove(path): try: os.remove(path)
        return True
    except Exception as e: return f"[fs error] {e}"


def rmdir(path): try: os.rmdir(path)
        return True
    except Exception as e: return f"[fs error] {e}"


def delete(path): import os

    try: os.remove(path)
        return True
    except Exception as e: return f"[fs.delete error] {e}"
