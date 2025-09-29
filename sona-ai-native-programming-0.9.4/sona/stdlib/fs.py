"""Sona standard library: file system operations"""

import os
from pathlib import Path

def read(file_path):
    """Read content from a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def write(file_path, content):
    """Write content to a file."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

def append(file_path, content):
    """Append content to a file."""
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(content)

def exists(file_path):
    """Check if a file or directory exists."""
    return Path(file_path).exists()

def is_file(path):
    """Check if path is a file."""
    return Path(path).is_file()

def is_dir(path):
    """Check if path is a directory."""
    return Path(path).is_dir()

def list_dir(dir_path):
    """List contents of a directory."""
    return [str(p.name) for p in Path(dir_path).iterdir()]

def mkdir(dir_path):
    """Create a directory."""
    Path(dir_path).mkdir(parents=True, exist_ok=True)

def remove(path):
    """Remove a file or directory."""
    path_obj = Path(path)
    if path_obj.is_file():
        path_obj.unlink()
    elif path_obj.is_dir():
        import shutil
        shutil.rmtree(path)
