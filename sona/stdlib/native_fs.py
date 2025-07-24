import os
from pathlib import Path

# Native bindings for Sona's fs.smod


def fs_exists(path): return Path(path).exists()


def fs_delete(path): p = Path(path)
    if p.is_file(): p.unlink()
        return True
    elif p.is_dir(): os.rmdir(p)
        return True
    return False


def fs_rename(old_path, new_path): Path(old_path).rename(new_path)
    return True


def fs_mkdir(path): Path(path).mkdir(parents = True, exist_ok = True)
    return True


def fs_list_dir(path): return os.listdir(path)
