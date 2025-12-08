"""
url - URL parsing and building for Sona stdlib

Provides utilities for working with URLs:
- parse: Parse URL into components
- build: Build URL from components
- encode/decode: URL encoding utilities
- join: Join URL paths safely
"""

from urllib.parse import (
    urlparse as _urlparse,
    urlunparse as _urlunparse,
    parse_qs as _parse_qs,
    urlencode as _urlencode,
    quote as _quote,
    unquote as _unquote,
    urljoin as _urljoin
)


def parse(url_string):
    """
    Parse URL into components.
    
    Args:
        url_string: URL to parse
    
    Returns:
        Dictionary with: scheme, netloc, path, params, query, fragment
    
    Example:
        url = "https://example.com:8080/path?key=value#section"
        parts = url.parse(url)
        # {
        #   "scheme": "https",
        #   "host": "example.com:8080",
        #   "path": "/path",
        #   "query": {"key": ["value"]},
        #   "fragment": "section"
        # }
    """
    parsed = _urlparse(url_string)
    
    return {
        'scheme': parsed.scheme,
        'host': parsed.netloc,
        'path': parsed.path,
        'params': parsed.params,
        'query': _parse_qs(parsed.query) if parsed.query else {},
        'fragment': parsed.fragment,
    }


def build(scheme='http', host='', path='', query=None, fragment=''):
    """
    Build URL from components.
    
    Args:
        scheme: URL scheme (default 'http')
        host: Hostname with optional port
        path: Path component
        query: Query parameters as dict
        fragment: Fragment identifier
    
    Returns:
        Complete URL string
    
    Example:
        url = url.build(
            scheme="https",
            host="example.com",
            path="/api/users",
            query={"page": "1", "limit": "10"}
        )
        # "https://example.com/api/users?page=1&limit=10"
    """
    if query and isinstance(query, dict):
        query_string = _urlencode(query)
    else:
        query_string = ''
    
    return _urlunparse((
        scheme,
        host,
        path,
        '',  # params (rarely used)
        query_string,
        fragment
    ))


def encode(text):
    """
    URL encode a string.
    
    Args:
        text: Text to encode
    
    Returns:
        URL-encoded string
    
    Example:
        encoded = url.encode("hello world")
        # "hello%20world"
    """
    return _quote(text)


def decode(text):
    """
    URL decode a string.
    
    Args:
        text: Text to decode
    
    Returns:
        Decoded string
    
    Example:
        decoded = url.decode("hello%20world")
        # "hello world"
    """
    return _unquote(text)


def join(base, *paths):
    """
    Join URL paths safely.
    
    Args:
        base: Base URL
        *paths: Path components to join
    
    Returns:
        Joined URL
    
    Example:
        url = url.join("https://example.com/api", "users", "123")
        # "https://example.com/api/users/123"
    """
    result = base
    for path in paths:
        result = _urljoin(result.rstrip('/') + '/', path.lstrip('/'))
    return result


def query_params(url_string):
    """
    Extract query parameters from URL.
    
    Args:
        url_string: URL to parse
    
    Returns:
        Dictionary of query parameters
    
    Example:
        params = url.query_params("http://example.com?a=1&b=2")
        # {"a": ["1"], "b": ["2"]}
    """
    parsed = _urlparse(url_string)
    return _parse_qs(parsed.query) if parsed.query else {}


def add_query(url_string, params):
    """
    Add query parameters to URL.
    
    Args:
        url_string: Base URL
        params: Dictionary of parameters to add
    
    Returns:
        URL with added parameters
    
    Example:
        url = url.add_query("http://example.com", {"page": "2"})
        # "http://example.com?page=2"
    """
    parsed = _urlparse(url_string)
    existing_params = _parse_qs(parsed.query) if parsed.query else {}
    
    # Merge parameters
    for key, value in params.items():
        if isinstance(value, list):
            existing_params[key] = value
        else:
            existing_params[key] = [str(value)]
    
    # Flatten for encoding
    flat_params = {}
    for key, values in existing_params.items():
        if len(values) == 1:
            flat_params[key] = values[0]
        else:
            flat_params[key] = values
    
    query_string = _urlencode(flat_params, doseq=True)
    
    return _urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        query_string,
        parsed.fragment
    ))


def is_valid(url_string):
    """Check if URL is valid."""
    try:
        result = _urlparse(url_string)
        return bool(result.scheme and result.netloc)
    except Exception:
        return False


def get_domain(url_string):
    """Extract domain from URL."""
    parsed = _urlparse(url_string)
    return parsed.netloc.split(':')[0] if parsed.netloc else ''


def get_path(url_string):
    """Extract path from URL."""
    parsed = _urlparse(url_string)
    return parsed.path


def normalize(url_string):
    """Normalize URL by removing default ports and trailing slashes."""
    parsed = _urlparse(url_string)
    
    # Remove default ports
    netloc = parsed.netloc
    if netloc.endswith(':80') and parsed.scheme == 'http':
        netloc = netloc[:-3]
    elif netloc.endswith(':443') and parsed.scheme == 'https':
        netloc = netloc[:-4]
    
    # Remove trailing slash from path
    path = parsed.path.rstrip('/') if parsed.path != '/' else parsed.path
    
    return _urlunparse((
        parsed.scheme,
        netloc,
        path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))


def is_absolute(url_string):
    """Check if URL is absolute (has scheme)."""
    parsed = _urlparse(url_string)
    return bool(parsed.scheme)


def remove_query(url_string):
    """Remove query string from URL."""
    parsed = _urlparse(url_string)
    return _urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        '',
        parsed.fragment
    ))


__all__ = [
    'parse',
    'build',
    'encode',
    'decode',
    'join',
    'query_params',
    'add_query',
    'is_valid',
    'get_domain',
    'get_path',
    'normalize',
    'is_absolute',
    'remove_query',
]
