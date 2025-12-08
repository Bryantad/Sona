"""
crypto - Cryptographic operations for Sona stdlib

Provides common cryptographic functions:
- hash: Cryptographic hashing (SHA256, MD5, etc.)
- hmac: HMAC generation
- random_bytes: Secure random generation
"""

import hashlib
import hmac as _hmac
import os
import base64


def hash(data, algorithm='sha256'):
    """
    Generate cryptographic hash.

    Args:
        data: Data to hash (str or bytes)
        algorithm: Hash algorithm ('sha256', 'sha512', 'md5', 'sha1')

    Returns:
        Hex digest string

    Example:
        digest = crypto.hash("hello world")
        # "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

    Note:
        MD5 and SHA1 are deprecated for security purposes.
        Use SHA256 or SHA512 for new applications.
    """
    if isinstance(data, str):
        data = data.encode('utf-8')

    if algorithm == 'sha256':
        h = hashlib.sha256()
    elif algorithm == 'sha512':
        h = hashlib.sha512()
    elif algorithm == 'sha1':
        h = hashlib.sha1(usedforsecurity=False)
    elif algorithm == 'md5':
        h = hashlib.md5(usedforsecurity=False)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    h.update(data)
    return h.hexdigest()


def hmac(key, message, algorithm='sha256'):
    """
    Generate HMAC (Hash-based Message Authentication Code).

    Args:
        key: Secret key (str or bytes)
        message: Message to authenticate (str or bytes)
        algorithm: Hash algorithm (default 'sha256')

    Returns:
        Hex digest string

    Example:
        signature = crypto.hmac("secret", "message")
    """
    if isinstance(key, str):
        key = key.encode('utf-8')
    if isinstance(message, str):
        message = message.encode('utf-8')

    if algorithm == 'sha256':
        h = _hmac.new(key, message, hashlib.sha256)
    elif algorithm == 'sha512':
        h = _hmac.new(key, message, hashlib.sha512)
    elif algorithm == 'sha1':
        h = _hmac.new(key, message, hashlib.sha1)
    elif algorithm == 'md5':
        h = _hmac.new(key, message, hashlib.md5)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    return h.hexdigest()


def random_bytes(length=32):
    """
    Generate secure random bytes.

    Args:
        length: Number of bytes (default 32)

    Returns:
        Random bytes

    Example:
        token = crypto.random_bytes(16)
    """
    return os.urandom(length)


def random_token(length=32):
    """
    Generate secure random token (hex string).

    Args:
        length: Number of bytes (default 32)

    Returns:
        Hex string (2x length)

    Example:
        token = crypto.random_token(16)
        # 32-character hex string
    """
    return random_bytes(length).hex()


def random_string(length=32):
    """
    Generate URL-safe random string.

    Args:
        length: Approximate string length

    Returns:
        URL-safe base64 string

    Example:
        token = crypto.random_string(24)
    """
    num_bytes = (length * 3) // 4  # Adjust for base64 encoding
    random_data = random_bytes(num_bytes)
    return base64.urlsafe_b64encode(random_data).decode('utf-8')[:length]


def compare_digest(a, b):
    """
    Timing-safe string comparison.

    Args:
        a: First string
        b: Second string

    Returns:
        True if equal, False otherwise

    Example:
        is_valid = crypto.compare_digest(provided_token, expected_token)
    """
    if isinstance(a, str):
        a = a.encode('utf-8')
    if isinstance(b, str):
        b = b.encode('utf-8')

    return _hmac.compare_digest(a, b)


def encrypt_simple(data, key):
    """Simple XOR-based encryption (not secure for production)."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    if isinstance(key, str):
        key = key.encode('utf-8')

    key_bytes = hashlib.sha256(key).digest()
    encrypted = bytearray()
    for i, byte in enumerate(data):
        encrypted.append(byte ^ key_bytes[i % len(key_bytes)])

    return base64.b64encode(bytes(encrypted)).decode('utf-8')


def decrypt_simple(encrypted, key):
    """Decrypt simple XOR-based encryption."""
    if isinstance(key, str):
        key = key.encode('utf-8')

    data = base64.b64decode(encrypted)
    key_bytes = hashlib.sha256(key).digest()
    decrypted = bytearray()
    for i, byte in enumerate(data):
        decrypted.append(byte ^ key_bytes[i % len(key_bytes)])

    return bytes(decrypted).decode('utf-8')


def derive_key(password, salt, iterations=100000, length=32):
    """Derive key from password using PBKDF2."""
    if isinstance(password, str):
        password = password.encode('utf-8')
    if isinstance(salt, str):
        salt = salt.encode('utf-8')

    return hashlib.pbkdf2_hmac('sha256', password, salt, iterations, length)


def hash_file(file_path, algorithm='sha256'):
    """Hash entire file contents."""
    if algorithm == 'sha256':
        h = hashlib.sha256()
    elif algorithm == 'sha512':
        h = hashlib.sha512()
    elif algorithm == 'md5':
        h = hashlib.md5()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)

    return h.hexdigest()


def generate_salt(length=16):
    """Generate random salt for key derivation."""
    return base64.b64encode(random_bytes(length)).decode('utf-8')


__all__ = [
    'hash',
    'hmac',
    'random_bytes',
    'random_token',
    'random_string',
    'compare_digest',
    'encrypt_simple',
    'decrypt_simple',
    'derive_key',
    'hash_file',
    'generate_salt',
]
