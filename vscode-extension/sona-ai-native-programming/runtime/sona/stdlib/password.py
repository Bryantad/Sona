"""
password - Password hashing and validation for Sona stdlib

Provides secure password operations:
- hash: Hash password securely
- verify: Verify password against hash
- Uses PBKDF2 with SHA256
"""

import hashlib
import os
import base64


def hash(password, iterations=100000):
    """
    Hash password securely using PBKDF2.
    
    Args:
        password: Plain text password
        iterations: Number of iterations (default 100000)
    
    Returns:
        Hashed password string (includes salt)
    
    Example:
        hashed = password.hash("mypassword123")
        # Store hashed in database
    """
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    # Generate random salt
    salt = os.urandom(32)
    
    # Hash password
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password,
        salt,
        iterations
    )
    
    # Encode as base64 for storage
    salt_b64 = base64.b64encode(salt).decode('utf-8')
    key_b64 = base64.b64encode(key).decode('utf-8')
    
    return f"pbkdf2:sha256:{iterations}${salt_b64}${key_b64}"


def verify(password, hashed):
    """
    Verify password against hash.
    
    Args:
        password: Plain text password
        hashed: Hashed password from hash()
    
    Returns:
        True if password matches, False otherwise
    
    Example:
        is_valid = password.verify("mypassword123", stored_hash)
    """
    try:
        # Parse hash components
        parts = hashed.split('$')
        if len(parts) != 3:
            return False
        
        algorithm_info, salt_b64, key_b64 = parts
        
        # Extract algorithm and iterations
        alg_parts = algorithm_info.split(':')
        if len(alg_parts) != 3 or alg_parts[0] != 'pbkdf2':
            return False
        
        iterations = int(alg_parts[2])
        
        # Decode salt and key
        salt = base64.b64decode(salt_b64)
        expected_key = base64.b64decode(key_b64)
        
        # Hash provided password
        if isinstance(password, str):
            password = password.encode('utf-8')
        
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password,
            salt,
            iterations
        )
        
        # Compare keys securely
        return key == expected_key
    
    except Exception:
        return False


def generate(length=16, include_special=True):
    """
    Generate random password.
    
    Args:
        length: Password length (default 16)
        include_special: Include special characters
    
    Returns:
        Random password string
    
    Example:
        pwd = password.generate(20)
    """
    import string
    import secrets
    
    chars = string.ascii_letters + string.digits
    if include_special:
        chars += '!@#$%^&*()_+-=[]{}|'
    
    return ''.join(secrets.choice(chars) for _ in range(length))


def strength(password):
    """
    Check password strength.
    
    Args:
        password: Password to check
    
    Returns:
        Dictionary with strength info
    
    Example:
        info = password.strength("mypassword123")
        # {
        #   "score": 3,  # 1-5
        #   "length": 13,
        #   "has_upper": True,
        #   "has_lower": True,
        #   "has_digit": True,
        #   "has_special": False
        # }
    """
    import string
    
    length = len(password)
    has_upper = any(c in string.ascii_uppercase for c in password)
    has_lower = any(c in string.ascii_lowercase for c in password)
    has_digit = any(c in string.digits for c in password)
    has_special = any(c in '!@#$%^&*()_+-=[]{}|' for c in password)
    
    # Calculate score
    score = 0
    if length >= 8:
        score += 1
    if length >= 12:
        score += 1
    if has_upper and has_lower:
        score += 1
    if has_digit:
        score += 1
    if has_special:
        score += 1
    
    return {
        'score': min(score, 5),
        'length': length,
        'has_upper': has_upper,
        'has_lower': has_lower,
        'has_digit': has_digit,
        'has_special': has_special
    }


def validate_policy(password, min_length=8, require_upper=True, 
                   require_lower=True, require_digit=True, require_special=False):
    """Validate password against policy."""
    import string
    
    if len(password) < min_length:
        return False
    
    if require_upper and not any(c in string.ascii_uppercase for c in password):
        return False
    
    if require_lower and not any(c in string.ascii_lowercase for c in password):
        return False
    
    if require_digit and not any(c in string.digits for c in password):
        return False
    
    if require_special and not any(c in '!@#$%^&*()_+-=[]{}|' for c in password):
        return False
    
    return True


def generate_memorable(num_words=4, separator='-'):
    """Generate memorable password from random words."""
    import secrets
    
    # Simple word list
    words = [
        'alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot',
        'golf', 'hotel', 'india', 'juliet', 'kilo', 'lima',
        'mike', 'november', 'oscar', 'papa', 'quebec', 'romeo',
        'sierra', 'tango', 'uniform', 'victor', 'whiskey', 'xray',
        'yankee', 'zulu'
    ]
    
    selected = [secrets.choice(words) for _ in range(num_words)]
    return separator.join(selected)


def is_weak(password):
    """Check if password is commonly weak."""
    weak_passwords = [
        'password', '123456', '12345678', 'qwerty', 'abc123',
        'monkey', 'letmein', 'trustno1', 'dragon', 'baseball',
        'iloveyou', 'master', 'sunshine', 'ashley', 'bailey'
    ]
    
    return password.lower() in weak_passwords


__all__ = [
    'hash',
    'verify',
    'generate',
    'strength',
    'validate_policy',
    'generate_memorable',
    'is_weak',
]
