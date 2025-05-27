import os
from pathlib import Path

# Native bindings for Sona's fs.smod

def fs_exists(path):
    return Path(path).exists()

def fs_delete(path):
    p = Path(path)
    if p.is_file():
        p.unlink()
        return True
    elif p.is_dir():
        os.rmdir(p)
        return True
    return False

def fs_rename(old_path, new_path):
    Path(old_path).rename(new_path)
    return True

def fs_mkdir(path):
    Path(path).mkdir(parents=True, exist_ok=True)
    return True

def fs_list_dir(path):
    return os.listdir(path)

def fs_read_file(path):
    """Read content from a file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"[Error reading file: {e}]"

def fs_write_file(path, content):
    """Write content to a file."""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        return f"[Error writing file: {e}]"

def fs_append_file(path, content):
    """Append content to a file."""
    try:
        with open(path, 'a', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        return f"[Error appending to file: {e}]"
