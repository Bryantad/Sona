"""Encoding helpers for base64."""
from __future__ import annotations

import base64
from typing import Union

BytesLike = Union[str, bytes, bytearray]


def _ensure_bytes(value: BytesLike) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    return value.encode("utf-8")


def b64encode(value: BytesLike) -> str:
    return base64.b64encode(_ensure_bytes(value)).decode("ascii")


def b64decode(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))


__all__ = ["b64encode", "b64decode"]
