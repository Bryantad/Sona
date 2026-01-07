"""
cookies - HTTP cookie management for Sona stdlib

Provides utilities for working with HTTP cookies:
- parse: Parse cookie string
- create: Create cookie string
- Cookie: Cookie object with attributes
"""

from http.cookies import SimpleCookie as _SimpleCookie
from datetime import datetime, timedelta


class Cookie:
    """Represents an HTTP cookie."""
    
    def __init__(self, name, value, **attributes):
        """
        Create a cookie.
        
        Args:
            name: Cookie name
            value: Cookie value
            **attributes: Cookie attributes (expires, path, domain, etc.)
        """
        self.name = name
        self.value = value
        self.expires = attributes.get('expires')
        self.max_age = attributes.get('max_age')
        self.path = attributes.get('path', '/')
        self.domain = attributes.get('domain')
        self.secure = attributes.get('secure', False)
        self.httponly = attributes.get('httponly', False)
        self.samesite = attributes.get('samesite')
    
    def to_header(self):
        """Convert cookie to Set-Cookie header value."""
        parts = [f"{self.name}={self.value}"]
        
        if self.expires:
            if isinstance(self.expires, datetime):
                expires_str = self.expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
            else:
                expires_str = self.expires
            parts.append(f"Expires={expires_str}")
        
        if self.max_age:
            parts.append(f"Max-Age={self.max_age}")
        
        if self.path:
            parts.append(f"Path={self.path}")
        
        if self.domain:
            parts.append(f"Domain={self.domain}")
        
        if self.secure:
            parts.append("Secure")
        
        if self.httponly:
            parts.append("HttpOnly")
        
        if self.samesite:
            parts.append(f"SameSite={self.samesite}")
        
        return "; ".join(parts)


def parse(cookie_string):
    """
    Parse cookie string into dictionary.
    
    Args:
        cookie_string: Cookie header value
    
    Returns:
        Dictionary of cookie name-value pairs
    
    Example:
        cookies = cookies.parse("session=abc123; user=john")
        # {"session": "abc123", "user": "john"}
    """
    simple_cookie = _SimpleCookie()
    simple_cookie.load(cookie_string)
    
    result = {}
    for key, morsel in simple_cookie.items():
        result[key] = morsel.value
    
    return result


def create(name, value, expires=None, max_age=None, path='/', 
           domain=None, secure=False, httponly=False, samesite=None):
    """
    Create a cookie header value.
    
    Args:
        name: Cookie name
        value: Cookie value
        expires: Expiration date (datetime or string)
        max_age: Max age in seconds
        path: Cookie path (default '/')
        domain: Cookie domain
        secure: Secure flag
        httponly: HttpOnly flag
        samesite: SameSite attribute ('Strict', 'Lax', 'None')
    
    Returns:
        Set-Cookie header value
    
    Example:
        header = cookies.create("session", "abc123", max_age=3600, httponly=True)
        # "session=abc123; Max-Age=3600; Path=/; HttpOnly"
    """
    cookie = Cookie(name, value, expires=expires, max_age=max_age, path=path,
                   domain=domain, secure=secure, httponly=httponly, samesite=samesite)
    return cookie.to_header()


def create_session(name, value, max_age=86400):
    """
    Create a session cookie with secure defaults.
    
    Args:
        name: Cookie name
        value: Cookie value
        max_age: Session duration in seconds (default 24 hours)
    
    Returns:
        Set-Cookie header value
    
    Example:
        header = cookies.create_session("session_id", "xyz789")
    """
    return create(name, value, max_age=max_age, httponly=True, 
                 secure=True, samesite='Lax')


def delete(name, path='/', domain=None):
    """
    Create a cookie deletion header.
    
    Args:
        name: Cookie name to delete
        path: Cookie path (default '/')
        domain: Cookie domain
    
    Returns:
        Set-Cookie header value that deletes the cookie
    
    Example:
        header = cookies.delete("session")
        # "session=; Max-Age=0; Path=/"
    """
    return create(name, '', max_age=0, path=path, domain=domain)


def parse_set_cookie(header_value):
    """Parse Set-Cookie header into Cookie object."""
    parts = [p.strip() for p in header_value.split(';')]
    if not parts:
        return None
    
    name, value = parts[0].split('=', 1)
    attrs = {}
    
    for part in parts[1:]:
        if '=' in part:
            key, val = part.split('=', 1)
            attrs[key.lower()] = val
        else:
            attrs[part.lower()] = True
    
    return Cookie(name, value, **attrs)


def serialize(cookies_dict):
    """Serialize dictionary to cookie header string."""
    return '; '.join(f"{k}={v}" for k, v in cookies_dict.items())


__all__ = [
    'Cookie',
    'parse',
    'create',
    'create_session',
    'delete',
    'parse_set_cookie',
    'serialize',
]
