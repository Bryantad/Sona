"""
jwt - JSON Web Token operations for Sona stdlib

Provides JWT encoding/decoding:
- encode: Create JWT token
- decode: Verify and decode JWT
- Simple HS256 implementation
"""

import json
import hmac
import hashlib
import base64
import time


def _base64_url_encode(data):
    """URL-safe base64 encoding."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def _base64_url_decode(data):
    """URL-safe base64 decoding."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    # Add padding
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += b'=' * padding
    
    return base64.urlsafe_b64decode(data)


def encode(payload, secret, algorithm='HS256', expires_in=None):
    """
    Encode payload as JWT.
    
    Args:
        payload: Dictionary payload
        secret: Secret key for signing
        algorithm: Algorithm (only 'HS256' supported)
        expires_in: Expiration time in seconds
    
    Returns:
        JWT token string
    
    Example:
        token = jwt.encode({"user_id": 123}, "secret", expires_in=3600)
    """
    if algorithm != 'HS256':
        raise ValueError("Only HS256 algorithm is supported")
    
    # Add standard claims
    if expires_in:
        payload = dict(payload)
        payload['exp'] = int(time.time() + expires_in)
        payload['iat'] = int(time.time())
    
    # Create header
    header = {
        'typ': 'JWT',
        'alg': algorithm
    }
    
    # Encode parts
    header_encoded = _base64_url_encode(json.dumps(header))
    payload_encoded = _base64_url_encode(json.dumps(payload))
    
    # Create signature
    message = f"{header_encoded}.{payload_encoded}"
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    signature_encoded = _base64_url_encode(signature)
    
    return f"{header_encoded}.{payload_encoded}.{signature_encoded}"


def decode(token, secret, verify=True):
    """
    Decode and verify JWT.
    
    Args:
        token: JWT token string
        secret: Secret key for verification
        verify: Whether to verify signature (default True)
    
    Returns:
        Decoded payload dictionary
    
    Raises:
        ValueError: If token is invalid or expired
    
    Example:
        payload = jwt.decode(token, "secret")
        print(payload["user_id"])
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")
        
        header_encoded, payload_encoded, signature_encoded = parts
        
        # Verify signature if requested
        if verify:
            message = f"{header_encoded}.{payload_encoded}"
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
            expected_signature_encoded = _base64_url_encode(expected_signature)
            
            if signature_encoded != expected_signature_encoded:
                raise ValueError("Invalid signature")
        
        # Decode payload
        payload_json = _base64_url_decode(payload_encoded)
        payload = json.loads(payload_json)
        
        # Check expiration
        if 'exp' in payload:
            if time.time() > payload['exp']:
                raise ValueError("Token has expired")
        
        return payload
    
    except Exception as e:
        raise ValueError(f"Invalid JWT: {e}")


def create_token(user_id, secret, expires_in=3600):
    """
    Create a simple user token.
    
    Args:
        user_id: User identifier
        secret: Secret key
        expires_in: Expiration in seconds (default 1 hour)
    
    Returns:
        JWT token
    
    Example:
        token = jwt.create_token(123, "secret")
    """
    return encode({'sub': user_id}, secret, expires_in=expires_in)


def verify_token(token, secret):
    """
    Verify token and return user_id.
    
    Args:
        token: JWT token
        secret: Secret key
    
    Returns:
        User ID from token
    
    Raises:
        ValueError: If token is invalid
    
    Example:
        user_id = jwt.verify_token(token, "secret")
    """
    payload = decode(token, secret)
    return payload.get('sub')


def get_payload_unverified(token):
    """Get payload without verifying signature."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid token format")
        
        payload_encoded = parts[1]
        payload_json = _base64_url_decode(payload_encoded)
        return json.loads(payload_json)
    except Exception as e:
        raise ValueError(f"Invalid token: {e}")


def is_expired(token):
    """Check if token is expired without verifying."""
    try:
        payload = get_payload_unverified(token)
        exp = payload.get('exp')
        if exp is None:
            return False
        return int(time.time()) >= exp
    except Exception:
        return True


def refresh_token(old_token, secret, expires_in=3600):
    """Create new token from existing token payload."""
    payload = decode(old_token, secret)
    
    # Remove old timestamps
    payload.pop('exp', None)
    payload.pop('iat', None)
    
    return encode(payload, secret, expires_in=expires_in)


__all__ = [
    'encode',
    'decode',
    'create_token',
    'verify_token',
    'get_payload_unverified',
    'is_expired',
    'refresh_token',
]
