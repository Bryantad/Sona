"""Hash helpers wrapping hashlib for deterministic usage."""
from __future__ import annotations

import hashlib
from typing import Union

BytesLike = Union[str, bytes, bytearray]


def _coerce(data: BytesLike) -> bytes:
    if isinstance(data, bytes):
        return data
    if isinstance(data, bytearray):
        return bytes(data)
    return data.encode("utf-8")


def md5(data: BytesLike) -> str:
    """Compute MD5 hash (deprecated, use for legacy compat only)."""
    return hashlib.md5(_coerce(data), usedforsecurity=False).hexdigest()


def sha1(data: BytesLike) -> str:
    """Compute SHA-1 hash (deprecated, use for legacy compat only)."""
    return hashlib.sha1(_coerce(data), usedforsecurity=False).hexdigest()


def sha256(data: BytesLike) -> str:
    """Compute SHA-256 hash (recommended for most use cases)."""
    return hashlib.sha256(_coerce(data)).hexdigest()


def sha512(data: BytesLike) -> str:
    """Compute SHA-512 hash (strongest SHA-2 variant)."""
    return hashlib.sha512(_coerce(data)).hexdigest()


def blake2b(data: BytesLike, digest_size: int = 64) -> str:
    """
    Compute BLAKE2b hash (modern, fast, cryptographically secure).

    Args:
        data: Data to hash
        digest_size: Output size in bytes (1-64, default 64)

    Returns:
        Hex-encoded hash string
    """
    return hashlib.blake2b(_coerce(data), digest_size=digest_size).hexdigest()


def checksum(data: BytesLike, algorithm: str = "sha256") -> str:
    """Compute hash using specified algorithm."""
    algorithm = algorithm.lower()
    if algorithm == "md5":
        return md5(data)
    if algorithm == "sha1":
        return sha1(data)
    if algorithm == "sha256":
        return sha256(data)
    if algorithm == "sha512":
        return sha512(data)
    if algorithm == "blake2b":
        return blake2b(data)
    raise ValueError(f"unsupported algorithm: {algorithm}")


def sha3_256(data: BytesLike) -> str:
    """Compute SHA3-256 hash (modern SHA-3 variant)."""
    return hashlib.sha3_256(_coerce(data)).hexdigest()


def sha3_512(data: BytesLike) -> str:
    """Compute SHA3-512 hash (strongest SHA-3 variant)."""
    return hashlib.sha3_512(_coerce(data)).hexdigest()


def hash_file(file_path: str, algorithm: str = "sha256") -> str:
    """Hash entire file contents."""
    algorithm = algorithm.lower()
    if algorithm == "md5":
        h = hashlib.md5(usedforsecurity=False)
    elif algorithm == "sha1":
        h = hashlib.sha1(usedforsecurity=False)
    elif algorithm == "sha256":
        h = hashlib.sha256()
    elif algorithm == "sha512":
        h = hashlib.sha512()
    elif algorithm == "blake2b":
        h = hashlib.blake2b()
    else:
        raise ValueError(f"unsupported algorithm: {algorithm}")

    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)

    return h.hexdigest()


def hmac_sha256(key: BytesLike, message: BytesLike) -> str:
    """Compute HMAC-SHA256."""
    import hmac
    return hmac.new(_coerce(key), _coerce(message), hashlib.sha256).hexdigest()


__all__ = [
    "md5",
    "sha1",
    "sha256",
    "sha512",
    "blake2b",
    "checksum",
    "sha3_256",
    "sha3_512",
    "hash_file",
    "hmac_sha256",
]
