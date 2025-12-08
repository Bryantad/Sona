"""
http - HTTP client operations for Sona stdlib

Provides utilities for making HTTP requests:
- get: HTTP GET request with retry policy
- post: HTTP POST request with retry policy
"""

import urllib.request
import urllib.error
import urllib.parse
import json as _json
import time


def get(url, timeout=10, headers=None, max_retries=3, retry_delay=1):
    """
    Make an HTTP GET request with retry policy.
    
    Args:
        url: URL to request
        timeout: Request timeout in seconds (default 10)
        headers: Optional dictionary of HTTP headers
        max_retries: Maximum number of retry attempts (default 3)
        retry_delay: Delay between retries in seconds (default 1)
    
    Returns:
        Dictionary with:
            - status: HTTP status code
            - body: Response body as string
            - headers: Response headers as dict
    
    Raises:
        RuntimeError: If all retry attempts fail
    
    Example:
        result = http.get("https://api.example.com/data")
        print(result["body"])
    """
    if headers is None:
        headers = {}
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=headers, method='GET')
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return {
                    'status': response.status,
                    'body': response.read().decode('utf-8'),
                    'headers': dict(response.headers)
                }
        
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            continue
    
    # All retries failed
    raise RuntimeError(f"HTTP GET failed after {max_retries} attempts: {last_error}")


def post(url, data=None, json=None, timeout=10, headers=None, max_retries=3, retry_delay=1):
    """
    Make an HTTP POST request with retry policy.
    
    Args:
        url: URL to request
        data: Optional form data as dictionary or bytes
        json: Optional JSON data (will be serialized automatically)
        timeout: Request timeout in seconds (default 10)
        headers: Optional dictionary of HTTP headers
        max_retries: Maximum number of retry attempts (default 3)
        retry_delay: Delay between retries in seconds (default 1)
    
    Returns:
        Dictionary with:
            - status: HTTP status code
            - body: Response body as string
            - headers: Response headers as dict
    
    Raises:
        RuntimeError: If all retry attempts fail
        ValueError: If both data and json are provided
    
    Example:
        result = http.post("https://api.example.com/users", 
                          json={"name": "Alice", "age": 30})
        print(result["status"])
    """
    if data is not None and json is not None:
        raise ValueError("Cannot specify both 'data' and 'json' parameters")
    
    if headers is None:
        headers = {}
    
    # Prepare request body
    body = None
    if json is not None:
        body = _json.dumps(json).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    elif data is not None:
        if isinstance(data, dict):
            body = urllib.parse.urlencode(data).encode('utf-8')
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        elif isinstance(data, bytes):
            body = data
        else:
            body = str(data).encode('utf-8')
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method='POST')
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return {
                    'status': response.status,
                    'body': response.read().decode('utf-8'),
                    'headers': dict(response.headers)
                }
        
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            continue
    
    # All retries failed
    raise RuntimeError(f"HTTP POST failed after {max_retries} attempts: {last_error}")


def put(url, data=None, json=None, timeout=10, headers=None):
    """Make an HTTP PUT request."""
    if headers is None:
        headers = {}
    
    body = None
    if json is not None:
        body = _json.dumps(json).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    elif data is not None:
        if isinstance(data, dict):
            body = urllib.parse.urlencode(data).encode('utf-8')
        elif isinstance(data, bytes):
            body = data
        else:
            body = str(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=body, headers=headers, method='PUT')
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return {
            'status': response.status,
            'body': response.read().decode('utf-8'),
            'headers': dict(response.headers)
        }


def delete(url, timeout=10, headers=None):
    """Make an HTTP DELETE request."""
    if headers is None:
        headers = {}
    
    req = urllib.request.Request(url, headers=headers, method='DELETE')
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return {
            'status': response.status,
            'body': response.read().decode('utf-8'),
            'headers': dict(response.headers)
        }


def patch(url, data=None, json=None, timeout=10, headers=None):
    """Make an HTTP PATCH request."""
    if headers is None:
        headers = {}
    
    body = None
    if json is not None:
        body = _json.dumps(json).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    elif data is not None:
        if isinstance(data, dict):
            body = urllib.parse.urlencode(data).encode('utf-8')
        elif isinstance(data, bytes):
            body = data
        else:
            body = str(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=body, headers=headers, method='PATCH')
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return {
            'status': response.status,
            'body': response.read().decode('utf-8'),
            'headers': dict(response.headers)
        }


def head(url, timeout=10, headers=None):
    """Make an HTTP HEAD request (headers only)."""
    if headers is None:
        headers = {}
    
    req = urllib.request.Request(url, headers=headers, method='HEAD')
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return {
            'status': response.status,
            'headers': dict(response.headers)
        }


def request(method, url, data=None, json=None, timeout=10, headers=None):
    """Make a generic HTTP request with custom method."""
    if headers is None:
        headers = {}
    
    body = None
    if json is not None:
        body = _json.dumps(json).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    elif data is not None:
        if isinstance(data, dict):
            body = urllib.parse.urlencode(data).encode('utf-8')
        elif isinstance(data, bytes):
            body = data
        else:
            body = str(data).encode('utf-8')
    
    req = urllib.request.Request(
        url, data=body, headers=headers, method=method.upper()
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return {
            'status': response.status,
            'body': response.read().decode('utf-8'),
            'headers': dict(response.headers)
        }


def get_json(url, timeout=10, headers=None):
    """Make GET request and parse JSON response."""
    response = get(url, timeout=timeout, headers=headers, max_retries=1)
    return _json.loads(response['body'])


def post_json(url, json=None, timeout=10, headers=None):
    """Make POST request with JSON data and parse JSON response."""
    response = post(url, json=json, timeout=timeout, headers=headers, max_retries=1)
    return _json.loads(response['body'])


def download(url, filename, timeout=30, chunk_size=8192):
    """Download file from URL."""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        with open(filename, 'wb') as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
    return filename


def upload(url, filename, timeout=30, headers=None):
    """Upload file to URL using POST."""
    if headers is None:
        headers = {}
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return {
            'status': response.status,
            'body': response.read().decode('utf-8'),
            'headers': dict(response.headers)
        }


__all__ = [
    'get',
    'post',
    'put',
    'delete',
    'patch',
    'head',
    'request',
    'get_json',
    'post_json',
    'download',
    'upload',
]
