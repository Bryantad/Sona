"""Input validation helpers."""
from __future__ import annotations

import re
from urllib.parse import urlparse

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def is_email(value: str) -> bool:
    return bool(EMAIL_REGEX.match(value))


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and parsed.netloc)


def ensure_non_empty(value: str, *, field: str = "value") -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field} must not be empty")
    return cleaned


def is_phone(value: str, pattern: str | None = None) -> bool:
    """
    Validate phone number format.
    
    Args:
        value: Phone number string
        pattern: Optional regex pattern (default: simple validation)
    
    Returns:
        True if valid
    
    Example:
        valid = validation.is_phone("+1-555-0100")
    """
    if pattern:
        return bool(re.match(pattern, value))
    # Simple pattern: digits, spaces, dashes, plus, parentheses
    simple_pattern = r"^[\d\s\-\+\(\)]+$"
    return bool(re.match(simple_pattern, value)) and len(re.sub(r'\D', '', value)) >= 10


def is_ip_address(value: str, version: int | None = None) -> bool:
    """
    Validate IP address (v4 or v6).
    
    Args:
        value: IP address string
        version: 4 or 6 (None = either)
    
    Returns:
        True if valid
    
    Example:
        valid = validation.is_ip_address("192.168.1.1", version=4)
    """
    import ipaddress
    try:
        ip = ipaddress.ip_address(value)
        if version == 4:
            return ip.version == 4
        elif version == 6:
            return ip.version == 6
        return True
    except ValueError:
        return False


def is_numeric(value: str) -> bool:
    """
    Check if string is numeric.
    
    Args:
        value: String to check
    
    Returns:
        True if numeric
    
    Example:
        valid = validation.is_numeric("123.45")
    """
    try:
        float(value)
        return True
    except ValueError:
        return False


def is_alpha(value: str) -> bool:
    """
    Check if string contains only letters.
    
    Args:
        value: String to check
    
    Returns:
        True if alphabetic
    
    Example:
        valid = validation.is_alpha("HelloWorld")
    """
    return value.isalpha()


def is_alphanumeric(value: str) -> bool:
    """
    Check if string contains only letters and numbers.
    
    Args:
        value: String to check
    
    Returns:
        True if alphanumeric
    
    Example:
        valid = validation.is_alphanumeric("User123")
    """
    return value.isalnum()


def in_range(value: float, min_val: float, max_val: float) -> bool:
    """
    Check if value is within range.
    
    Args:
        value: Value to check
        min_val: Minimum (inclusive)
        max_val: Maximum (inclusive)
    
    Returns:
        True if in range
    
    Example:
        valid = validation.in_range(50, 0, 100)
    """
    return min_val <= value <= max_val


def min_length(value: str, length: int) -> bool:
    """
    Check if string meets minimum length.
    
    Args:
        value: String to check
        length: Minimum length
    
    Returns:
        True if meets minimum
    
    Example:
        valid = validation.min_length(password, 8)
    """
    return len(value) >= length


def max_length(value: str, length: int) -> bool:
    """
    Check if string is within maximum length.
    
    Args:
        value: String to check
        length: Maximum length
    
    Returns:
        True if within maximum
    
    Example:
        valid = validation.max_length(username, 20)
    """
    return len(value) <= length


def matches_pattern(value: str, pattern: str) -> bool:
    """
    Check if string matches regex pattern.
    
    Args:
        value: String to check
        pattern: Regex pattern
    
    Returns:
        True if matches
    
    Example:
        valid = validation.matches_pattern(code, r"^[A-Z]{3}\d{3}$")
    """
    return bool(re.match(pattern, value))


def is_credit_card(value: str) -> bool:
    """
    Validate credit card number using Luhn algorithm.
    
    Args:
        value: Card number string
    
    Returns:
        True if valid
    
    Example:
        valid = validation.is_credit_card("4532015112830366")
    """
    # Remove spaces and dashes
    digits = re.sub(r'[\s\-]', '', value)
    
    if not digits.isdigit() or len(digits) < 13 or len(digits) > 19:
        return False
    
    # Luhn algorithm
    total = 0
    reverse_digits = digits[::-1]
    
    for i, digit in enumerate(reverse_digits):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    
    return total % 10 == 0


__all__ = [
    "is_email", "is_url", "ensure_non_empty",
    "is_phone", "is_ip_address", "is_numeric", "is_alpha", "is_alphanumeric",
    "in_range", "min_length", "max_length", "matches_pattern", "is_credit_card"
]
