"""
secrets - Secure random generation for Sona stdlib

Provides secure random utilities:
- token: Generate secure token
- choice: Secure random choice
- randbelow: Secure random integer
"""

import secrets as _secrets
import string


__all__ = [
    'token',
    'token_hex',
    'token_urlsafe',
    'choice',
    'randbelow',
    'randbits',
    'password',
    'compare',
    'randint',
    'api_key',
    'session_id',
    'shuffle'
]


def token(nbytes=32):
    """
    Generate secure random token (bytes).
    
    Args:
        nbytes: Number of bytes
    
    Returns:
        Random bytes
    
    Example:
        token = secrets.token(16)
    """
    return _secrets.token_bytes(nbytes)


def token_hex(nbytes=32):
    """
    Generate secure random token (hex string).
    
    Args:
        nbytes: Number of bytes
    
    Returns:
        Hex string (2x nbytes length)
    
    Example:
        token = secrets.token_hex(16)
        # 32-character hex string
    """
    return _secrets.token_hex(nbytes)


def token_urlsafe(nbytes=32):
    """
    Generate URL-safe random token.
    
    Args:
        nbytes: Number of bytes
    
    Returns:
        URL-safe base64 string
    
    Example:
        token = secrets.token_urlsafe(16)
    """
    return _secrets.token_urlsafe(nbytes)


def choice(items):
    """
    Secure random choice from sequence.
    
    Args:
        items: Sequence to choose from
    
    Returns:
        Random item
    
    Example:
        winner = secrets.choice(participants)
    """
    return _secrets.choice(items)


def randbelow(n):
    """
    Secure random integer below n.
    
    Args:
        n: Upper bound (exclusive)
    
    Returns:
        Random integer in [0, n)
    
    Example:
        roll = secrets.randbelow(6) + 1  # Dice roll
    """
    return _secrets.randbelow(n)


def randbits(k):
    """
    Generate random integer with k random bits.
    
    Args:
        k: Number of bits
    
    Returns:
        Random integer
    
    Example:
        value = secrets.randbits(128)
    """
    return _secrets.randbits(k)


def password(length=16, include_special=True):
    """
    Generate secure random password.
    
    Args:
        length: Password length
        include_special: Include special characters
    
    Returns:
        Random password string
    
    Example:
        pwd = secrets.password(20)
    """
    chars = string.ascii_letters + string.digits
    if include_special:
        chars += string.punctuation
    
    return ''.join(_secrets.choice(chars) for _ in range(length))


def compare(a, b):
    """
    Timing-safe string comparison.
    
    Args:
        a: First string
        b: Second string
    
    Returns:
        True if equal
    
    Example:
        is_valid = secrets.compare(provided_token, expected_token)
    """
    return _secrets.compare_digest(a, b)


def randint(a, b):
    """
    Generate cryptographically secure random integer in range [a, b].
    
    Args:
        a (int): Minimum value (inclusive)
        b (int): Maximum value (inclusive)
    
    Returns:
        int: Random integer
    
    Example:
        roll = secrets.randint(1, 6)  # Dice roll
    """
    return a + _secrets.randbelow(b - a + 1)


def api_key(length=32):
    """
    Generate secure API key.
    
    Args:
        length (int): Key length in bytes
    
    Returns:
        str: URL-safe API key
    
    Example:
        key = secrets.api_key()
    """
    return _secrets.token_urlsafe(length)


def session_id(length=24):
    """
    Generate secure session identifier.
    
    Args:
        length (int): ID length in bytes
    
    Returns:
        str: Hexadecimal session ID
    
    Example:
        sid = secrets.session_id()
    """
    return _secrets.token_hex(length)


def shuffle(items):
    """
    Securely shuffle a list in-place using cryptographic random.
    
    Args:
        items (list): List to shuffle
    
    Returns:
        list: The same list, shuffled in-place
    
    Example:
        deck = list(range(52))
        secrets.shuffle(deck)
    """
    for i in range(len(items) - 1, 0, -1):
        j = _secrets.randbelow(i + 1)
        items[i], items[j] = items[j], items[i]
    return items
