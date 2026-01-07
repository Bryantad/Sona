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
        valid = validation.matches_pattern(code, r"^[A-Z]{3}\\d{3}$")
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


# ============================================================================
# NEW IN v0.10.1: Extended Validators
# ============================================================================

def is_uuid(value: str, version: int | None = None) -> bool:
    """
    Validate UUID format.
    
    Args:
        value: UUID string to validate
        version: Optional specific version (1, 3, 4, or 5)
    
    Returns:
        True if valid UUID
    
    Example:
        valid = validation.is_uuid("550e8400-e29b-41d4-a716-446655440000")
        valid_v4 = validation.is_uuid("550e8400-e29b-41d4-a716-446655440000", version=4)
    """
    import uuid as uuid_module
    try:
        parsed = uuid_module.UUID(value)
        if version is not None:
            return parsed.version == version
        return True
    except ValueError:
        return False


def is_hex(value: str) -> bool:
    """
    Check if string is valid hexadecimal.
    
    Args:
        value: String to check
    
    Returns:
        True if valid hex
    
    Example:
        valid = validation.is_hex("deadbeef")
        valid = validation.is_hex("0xABCDEF")
    """
    # Handle 0x prefix
    check_val = value[2:] if value.lower().startswith('0x') else value
    if not check_val:
        return False
    return bool(re.match(r'^[0-9A-Fa-f]+$', check_val))


def is_base64(value: str) -> bool:
    """
    Check if string is valid Base64.
    
    Args:
        value: String to check
    
    Returns:
        True if valid Base64
    
    Example:
        valid = validation.is_base64("SGVsbG8gV29ybGQ=")
    """
    import base64
    try:
        # Check pattern first
        if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', value):
            return False
        # Try decode
        base64.b64decode(value, validate=True)
        return True
    except Exception:
        return False


def is_isbn(value: str) -> bool:
    """
    Validate ISBN-10 or ISBN-13.
    
    Args:
        value: ISBN string (with or without dashes)
    
    Returns:
        True if valid ISBN
    
    Example:
        valid = validation.is_isbn("978-3-16-148410-0")
        valid = validation.is_isbn("0-306-40615-2")
    """
    # Remove dashes and spaces
    isbn = re.sub(r'[\s\-]', '', value)
    
    if len(isbn) == 10:
        # ISBN-10 validation
        if not re.match(r'^[0-9]{9}[0-9X]$', isbn):
            return False
        total = sum((10 - i) * (10 if c == 'X' else int(c)) 
                    for i, c in enumerate(isbn))
        return total % 11 == 0
    
    elif len(isbn) == 13:
        # ISBN-13 validation
        if not isbn.isdigit():
            return False
        total = sum(int(d) * (1 if i % 2 == 0 else 3) 
                    for i, d in enumerate(isbn))
        return total % 10 == 0
    
    return False


def is_iban(value: str) -> bool:
    """
    Validate IBAN (International Bank Account Number).
    
    Args:
        value: IBAN string
    
    Returns:
        True if valid IBAN
    
    Example:
        valid = validation.is_iban("DE89370400440532013000")
    """
    # Remove spaces and convert to uppercase
    iban = re.sub(r'\s', '', value).upper()
    
    # Check basic format
    if not re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{4,}$', iban):
        return False
    
    # Move first 4 chars to end and convert letters to numbers
    rearranged = iban[4:] + iban[:4]
    numeric = ''
    for char in rearranged:
        if char.isalpha():
            numeric += str(ord(char) - 55)  # A=10, B=11, etc.
        else:
            numeric += char
    
    # Check mod 97
    return int(numeric) % 97 == 1


def is_mac_address(value: str) -> bool:
    """
    Validate MAC address.
    
    Args:
        value: MAC address string
    
    Returns:
        True if valid MAC
    
    Example:
        valid = validation.is_mac_address("00:1A:2B:3C:4D:5E")
        valid = validation.is_mac_address("00-1A-2B-3C-4D-5E")
    """
    patterns = [
        r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$',  # colon-separated
        r'^([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}$',  # dash-separated
        r'^[0-9A-Fa-f]{12}$',                       # no separator
    ]
    return any(re.match(p, value) for p in patterns)


def is_slug(value: str) -> bool:
    """
    Check if string is URL-safe slug format.
    
    Args:
        value: String to check
    
    Returns:
        True if valid slug
    
    Example:
        valid = validation.is_slug("my-awesome-post")
    """
    return bool(re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', value))


def is_semver(value: str) -> bool:
    """
    Validate semantic version string.
    
    Args:
        value: Version string
    
    Returns:
        True if valid semver
    
    Example:
        valid = validation.is_semver("1.2.3")
        valid = validation.is_semver("0.10.1-beta.1+build.123")
    """
    pattern = r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
    return bool(re.match(pattern, value))


def is_json(value: str) -> bool:
    """
    Check if string is valid JSON.
    
    Args:
        value: String to check
    
    Returns:
        True if valid JSON
    
    Example:
        valid = validation.is_json('{"key": "value"}')
    """
    import json as json_module
    try:
        json_module.loads(value)
        return True
    except (json_module.JSONDecodeError, TypeError):
        return False


def is_date(value: str, format: str = "%Y-%m-%d") -> bool:
    """
    Validate date string format.
    
    Args:
        value: Date string
        format: Expected format (default: YYYY-MM-DD)
    
    Returns:
        True if valid date
    
    Example:
        valid = validation.is_date("2024-12-25")
        valid = validation.is_date("25/12/2024", format="%d/%m/%Y")
    """
    from datetime import datetime
    try:
        datetime.strptime(value, format)
        return True
    except ValueError:
        return False


def is_time(value: str, format: str = "%H:%M:%S") -> bool:
    """
    Validate time string format.
    
    Args:
        value: Time string
        format: Expected format (default: HH:MM:SS)
    
    Returns:
        True if valid time
    
    Example:
        valid = validation.is_time("14:30:00")
        valid = validation.is_time("2:30 PM", format="%I:%M %p")
    """
    from datetime import datetime
    try:
        datetime.strptime(value, format)
        return True
    except ValueError:
        return False


def is_datetime(value: str, format: str = "%Y-%m-%dT%H:%M:%S") -> bool:
    """
    Validate datetime string format.
    
    Args:
        value: Datetime string
        format: Expected format (default: ISO 8601)
    
    Returns:
        True if valid datetime
    
    Example:
        valid = validation.is_datetime("2024-12-25T14:30:00")
    """
    from datetime import datetime
    try:
        datetime.strptime(value, format)
        return True
    except ValueError:
        return False


def is_color_hex(value: str) -> bool:
    """
    Validate CSS hex color code.
    
    Args:
        value: Color string
    
    Returns:
        True if valid hex color
    
    Example:
        valid = validation.is_color_hex("#FF5733")
        valid = validation.is_color_hex("#F53")
    """
    return bool(re.match(r'^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$', value))


def is_postal_code(value: str, country: str = "US") -> bool:
    """
    Validate postal/ZIP code by country.
    
    Args:
        value: Postal code string
        country: Country code (US, UK, CA, DE, FR, etc.)
    
    Returns:
        True if valid postal code
    
    Example:
        valid = validation.is_postal_code("12345", country="US")
        valid = validation.is_postal_code("SW1A 1AA", country="UK")
    """
    patterns = {
        "US": r'^\d{5}(-\d{4})?$',
        "UK": r'^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$',
        "CA": r'^[A-Z]\d[A-Z]\s?\d[A-Z]\d$',
        "DE": r'^\d{5}$',
        "FR": r'^\d{5}$',
        "JP": r'^\d{3}-?\d{4}$',
        "AU": r'^\d{4}$',
        "IN": r'^\d{6}$',
    }
    pattern = patterns.get(country.upper())
    if not pattern:
        return False
    return bool(re.match(pattern, value.upper()))


def is_strong_password(
    value: str, 
    min_length: int = 8,
    require_uppercase: bool = True,
    require_lowercase: bool = True,
    require_digit: bool = True,
    require_special: bool = True
) -> bool:
    """
    Validate password strength.
    
    Args:
        value: Password string
        min_length: Minimum length (default: 8)
        require_uppercase: Require uppercase letter
        require_lowercase: Require lowercase letter
        require_digit: Require digit
        require_special: Require special character
    
    Returns:
        True if password meets requirements
    
    Example:
        valid = validation.is_strong_password("MyP@ssw0rd!")
    """
    if len(value) < min_length:
        return False
    if require_uppercase and not re.search(r'[A-Z]', value):
        return False
    if require_lowercase and not re.search(r'[a-z]', value):
        return False
    if require_digit and not re.search(r'\d', value):
        return False
    if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        return False
    return True


def sanitize_html(value: str) -> str:
    """
    Remove HTML tags from string.
    
    Args:
        value: String with potential HTML
    
    Returns:
        Sanitized string
    
    Example:
        clean = validation.sanitize_html("<p>Hello <b>World</b></p>")
        # Returns: "Hello World"
    """
    return re.sub(r'<[^>]+>', '', value)


def sanitize_filename(value: str, replacement: str = "_") -> str:
    """
    Sanitize string for use as filename.
    
    Args:
        value: Original filename
        replacement: Character to replace invalid chars
    
    Returns:
        Sanitized filename
    
    Example:
        safe = validation.sanitize_filename("my:file/name.txt")
        # Returns: "my_file_name.txt"
    """
    # Remove/replace invalid filename characters
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, replacement, value)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    return sanitized if sanitized else 'unnamed'


def is_domain(value: str) -> bool:
    """
    Validate domain name format.
    
    Args:
        value: Domain string
    
    Returns:
        True if valid domain
    
    Example:
        valid = validation.is_domain("example.com")
    """
    pattern = r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*\.[A-Za-z]{2,}$'
    return bool(re.match(pattern, value))


def is_latitude(value: float) -> bool:
    """
    Validate latitude value.
    
    Args:
        value: Latitude as float
    
    Returns:
        True if valid latitude (-90 to 90)
    
    Example:
        valid = validation.is_latitude(40.7128)
    """
    return -90 <= value <= 90


def is_longitude(value: float) -> bool:
    """
    Validate longitude value.
    
    Args:
        value: Longitude as float
    
    Returns:
        True if valid longitude (-180 to 180)
    
    Example:
        valid = validation.is_longitude(-74.0060)
    """
    return -180 <= value <= 180


def is_coordinate(lat: float, lon: float) -> bool:
    """
    Validate geographic coordinate pair.
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        True if valid coordinate
    
    Example:
        valid = validation.is_coordinate(40.7128, -74.0060)
    """
    return is_latitude(lat) and is_longitude(lon)


def is_ascii(value: str) -> bool:
    """
    Check if string contains only ASCII characters.
    
    Args:
        value: String to check
    
    Returns:
        True if ASCII only
    
    Example:
        valid = validation.is_ascii("Hello World")
    """
    return all(ord(c) < 128 for c in value)


def is_empty(value) -> bool:
    """
    Check if value is empty (None, empty string, empty list, etc.).
    
    Args:
        value: Value to check
    
    Returns:
        True if empty
    
    Example:
        empty = validation.is_empty("")
        empty = validation.is_empty([])
    """
    if value is None:
        return True
    if isinstance(value, (str, list, dict, set, tuple)):
        return len(value) == 0
    return False


def is_not_empty(value) -> bool:
    """
    Check if value is not empty.
    
    Args:
        value: Value to check
    
    Returns:
        True if not empty
    
    Example:
        has_value = validation.is_not_empty("Hello")
    """
    return not is_empty(value)


def is_integer(value: str) -> bool:
    """
    Check if string represents an integer.
    
    Args:
        value: String to check
    
    Returns:
        True if integer
    
    Example:
        valid = validation.is_integer("-42")
    """
    try:
        int(value)
        return True
    except ValueError:
        return False


def is_float(value: str) -> bool:
    """
    Check if string represents a float.
    
    Args:
        value: String to check
    
    Returns:
        True if float
    
    Example:
        valid = validation.is_float("3.14159")
    """
    try:
        f = float(value)
        # Return True only if it has decimal part
        return '.' in value or 'e' in value.lower()
    except ValueError:
        return False


def validate_all(value, *validators) -> bool:
    """
    Run multiple validators, return True if all pass.
    
    Args:
        value: Value to validate
        validators: Validator functions
    
    Returns:
        True if all validators pass
    
    Example:
        valid = validation.validate_all(
            "test@example.com",
            validation.is_email,
            lambda x: len(x) < 50
        )
    """
    return all(v(value) for v in validators)


def validate_any(value, *validators) -> bool:
    """
    Run multiple validators, return True if any pass.
    
    Args:
        value: Value to validate
        validators: Validator functions
    
    Returns:
        True if any validator passes
    
    Example:
        valid = validation.validate_any(
            "12345",
            validation.is_integer,
            validation.is_uuid
        )
    """
    return any(v(value) for v in validators)


def validate_schema(data: dict, schema: dict) -> tuple:
    """
    Validate dictionary against schema.
    
    Args:
        data: Dictionary to validate
        schema: Schema with field validators
            {field: {"required": bool, "type": type, "validator": func}}
    
    Returns:
        Tuple of (is_valid, errors)
    
    Example:
        schema = {
            "email": {"required": True, "validator": validation.is_email},
            "age": {"required": True, "type": int}
        }
        valid, errors = validation.validate_schema(user_data, schema)
    """
    errors = []
    
    for field, rules in schema.items():
        required = rules.get("required", False)
        expected_type = rules.get("type")
        validator = rules.get("validator")
        
        value = data.get(field)
        
        if value is None:
            if required:
                errors.append(f"Missing required field: {field}")
            continue
        
        if expected_type and not isinstance(value, expected_type):
            errors.append(f"Invalid type for {field}: expected {expected_type.__name__}")
            continue
        
        if validator and not validator(value):
            errors.append(f"Validation failed for field: {field}")
    
    return (len(errors) == 0, errors)


__all__ = [
    # Original validators
    "is_email", "is_url", "ensure_non_empty",
    "is_phone", "is_ip_address", "is_numeric", "is_alpha", "is_alphanumeric",
    "in_range", "min_length", "max_length", "matches_pattern", "is_credit_card",
    # NEW in v0.10.1
    "is_uuid", "is_hex", "is_base64", "is_isbn", "is_iban", "is_mac_address",
    "is_slug", "is_semver", "is_json", "is_date", "is_time", "is_datetime",
    "is_color_hex", "is_postal_code", "is_strong_password",
    "sanitize_html", "sanitize_filename", "is_domain",
    "is_latitude", "is_longitude", "is_coordinate",
    "is_ascii", "is_empty", "is_not_empty", "is_integer", "is_float",
    "validate_all", "validate_any", "validate_schema"
]
