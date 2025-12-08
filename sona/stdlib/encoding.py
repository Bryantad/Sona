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


def urlsafe_b64encode(value: BytesLike) -> str:
    """
    URL-safe base64 encoding.
    
    Args:
        value: Data to encode
    
    Returns:
        URL-safe base64 string
    
    Example:
        encoded = encoding.urlsafe_b64encode(b"data+with/special=chars")
    """
    return base64.urlsafe_b64encode(_ensure_bytes(value)).decode("ascii")


def urlsafe_b64decode(value: str) -> bytes:
    """
    URL-safe base64 decoding.
    
    Args:
        value: URL-safe base64 string
    
    Returns:
        Decoded bytes
    
    Example:
        data = encoding.urlsafe_b64decode(encoded_string)
    """
    return base64.urlsafe_b64decode(value.encode("ascii"))


def b32encode(value: BytesLike) -> str:
    """
    Base32 encoding.
    
    Args:
        value: Data to encode
    
    Returns:
        Base32 string
    
    Example:
        encoded = encoding.b32encode(b"hello")
    """
    return base64.b32encode(_ensure_bytes(value)).decode("ascii")


def b32decode(value: str) -> bytes:
    """
    Base32 decoding.
    
    Args:
        value: Base32 string
    
    Returns:
        Decoded bytes
    
    Example:
        data = encoding.b32decode("NBSWY3DP")
    """
    return base64.b32decode(value.encode("ascii"))


def hex_encode(value: BytesLike) -> str:
    """
    Hexadecimal encoding.
    
    Args:
        value: Data to encode
    
    Returns:
        Hex string
    
    Example:
        hex_str = encoding.hex_encode(b"\\x01\\x02\\x03")
    """
    return _ensure_bytes(value).hex()


def hex_decode(value: str) -> bytes:
    """
    Hexadecimal decoding.
    
    Args:
        value: Hex string
    
    Returns:
        Decoded bytes
    
    Example:
        data = encoding.hex_decode("010203")
    """
    return bytes.fromhex(value)


def url_encode(value: str) -> str:
    """
    URL percent encoding.
    
    Args:
        value: String to encode
    
    Returns:
        URL-encoded string
    
    Example:
        encoded = encoding.url_encode("hello world")
    """
    from urllib.parse import quote
    return quote(value)


def url_decode(value: str) -> str:
    """
    URL percent decoding.
    
    Args:
        value: URL-encoded string
    
    Returns:
        Decoded string
    
    Example:
        decoded = encoding.url_decode("hello%20world")
    """
    from urllib.parse import unquote
    return unquote(value)


def rot13(value: str) -> str:
    """
    ROT13 encoding/decoding.
    
    Args:
        value: String to encode/decode
    
    Returns:
        ROT13 string
    
    Example:
        encoded = encoding.rot13("hello")  # "uryyb"
        decoded = encoding.rot13(encoded)  # "hello"
    """
    import codecs
    return codecs.encode(value, 'rot_13')


__all__ = [
    "b64encode", "b64decode",
    "urlsafe_b64encode", "urlsafe_b64decode",
    "b32encode", "b32decode",
    "hex_encode", "hex_decode",
    "url_encode", "url_decode",
    "rot13"
]
