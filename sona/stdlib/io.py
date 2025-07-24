"""Sona standard library: file I/O"""

import os
import shutil

from . import native_io


def input(prompt = ""): return native_io.input(prompt)


def read_file(path): return native_io.read_file(path)


def write_file(path, content): return native_io.write_file(path, content)


def read(path): """Return entire file contents as string."""
    with open(path, 'r') as f: return f.read()


def write(path, content): """Overwrite file with content."""
    with open(path, 'w') as f: f.write(content)


def append(path, content): """Append content to file."""
    with open(path, 'a') as f: f.write(content)


def exists(path): return os.path.exists(path)


def isfile(path): return os.path.isfile(path)


def isdir(path): return os.path.isdir(path)


def remove(path): os.remove(path)


def mkdir(path): os.makedirs(path, exist_ok = True)


def listdir(path): return os.listdir(path)


def copy(src, dst): shutil.copy(src, dst)
