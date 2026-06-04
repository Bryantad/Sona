"""Private host intrinsics for Sona-authored stdlib modules.

This module is intentionally not a user-facing stdlib module. Public APIs live
in ``stdlib/*.smod`` and call only these small primitives where Sona cannot yet
implement the capability itself.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
import uuid
from typing import Any


def _coerce_bytes(value: Any) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, list):
        return bytes(int(item) & 0xFF for item in value)
    if value is None:
        return b""
    return str(value).encode("utf-8")


def intrinsic_random_bytes(length: int = 32) -> list[int]:
    return list(os.urandom(max(0, int(length))))


def intrinsic_sha256(data: Any) -> str:
    return hashlib.sha256(_coerce_bytes(data)).hexdigest()


def intrinsic_sha512(data: Any) -> str:
    return hashlib.sha512(_coerce_bytes(data)).hexdigest()


def intrinsic_hmac_sha256(key: Any, message: Any) -> str:
    return hmac.new(_coerce_bytes(key), _coerce_bytes(message), hashlib.sha256).hexdigest()


def intrinsic_constant_time_eq(a: Any, b: Any) -> bool:
    return hmac.compare_digest(_coerce_bytes(a), _coerce_bytes(b))


def intrinsic_uuid_v4() -> str:
    return str(uuid.uuid4())


def intrinsic_now() -> int:
    return int(time.time())


def intrinsic_base64_encode(data: Any) -> str:
    return base64.urlsafe_b64encode(_coerce_bytes(data)).rstrip(b"=").decode("ascii")


def intrinsic_base64_decode(data: Any) -> str:
    text = str(data)
    padding = "=" * ((4 - len(text) % 4) % 4)
    raw = base64.urlsafe_b64decode((text + padding).encode("ascii"))
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return "".join(chr(byte) for byte in raw)


__all__ = [
    "intrinsic_random_bytes",
    "intrinsic_sha256",
    "intrinsic_sha512",
    "intrinsic_hmac_sha256",
    "intrinsic_constant_time_eq",
    "intrinsic_uuid_v4",
    "intrinsic_now",
    "intrinsic_base64_encode",
    "intrinsic_base64_decode",
]
