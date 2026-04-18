"""Native shims exposing path utilities to the Sona runtime."""

from __future__ import annotations

from . import path as _path


def path_join(*parts):
    if len(parts) == 1 and isinstance(parts[0], (list, tuple)):
        return _path.join(parts[0])
    return _path.join(list(parts))


def path_normalize(path):
    return _path.normalize(path)


def path_basename(path):
    return _path.basename(path)


def path_dirname(path):
    return _path.dirname(path)


def path_split(path):
    return _path.split(path)


def path_extension(path):
    return _path.extension(path)


def path_is_absolute(path):
    return _path.is_absolute(path)


def path_is_relative(path):
    return _path.is_relative(path)


def path_resolve(base, target):
    return _path.resolve(base, target)


def __dir__():
    return [
        "path_join",
        "path_normalize",
        "path_basename",
        "path_dirname",
        "path_split",
        "path_extension",
        "path_is_absolute",
        "path_is_relative",
        "path_resolve",
    ]


__all__ = __dir__()
