"""
session - HTTP session management for Sona stdlib

Provides session handling:
- Session: HTTP session with cookies and persistence
- Automatic cookie management
- Connection pooling
"""

import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import json


class Session:
    """HTTP session with cookie persistence."""
    
    def __init__(self):
        """Initialize session."""
        self.cookies = http.cookiejar.CookieJar()
        self.headers = {}
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookies)
        )
    
    def set_header(self, name, value):
        """Set default header."""
        self.headers[name] = value
    
    def get(self, url, headers=None, timeout=30):
        """
        Send GET request.
        
        Args:
            url: Target URL
            headers: Additional headers
            timeout: Request timeout
        
        Returns:
            Response dictionary
        """
        all_headers = {**self.headers, **(headers or {})}
        
        req = urllib.request.Request(url, headers=all_headers)
        
        try:
            with self.opener.open(req, timeout=timeout) as response:
                body = response.read().decode('utf-8')
                
                return {
                    'status': response.status,
                    'headers': dict(response.headers),
                    'body': body,
                    'ok': 200 <= response.status < 300
                }
        except urllib.error.HTTPError as e:
            return {
                'status': e.code,
                'headers': dict(e.headers),
                'body': e.read().decode('utf-8'),
                'ok': False
            }
        except urllib.error.URLError as e:
            return {
                'status': 0,
                'headers': {},
                'body': str(e.reason),
                'ok': False
            }
    
    def post(self, url, data=None, json_data=None, headers=None, timeout=30):
        """
        Send POST request.
        
        Args:
            url: Target URL
            data: Form data (dict)
            json_data: JSON data (dict)
            headers: Additional headers
            timeout: Request timeout
        
        Returns:
            Response dictionary
        """
        all_headers = {**self.headers, **(headers or {})}
        
        if json_data is not None:
            body = json.dumps(json_data).encode('utf-8')
            all_headers['Content-Type'] = 'application/json'
        elif data is not None:
            body = urllib.parse.urlencode(data).encode('utf-8')
            all_headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            body = b''
        
        req = urllib.request.Request(url, data=body, headers=all_headers)
        
        try:
            with self.opener.open(req, timeout=timeout) as response:
                resp_body = response.read().decode('utf-8')
                
                return {
                    'status': response.status,
                    'headers': dict(response.headers),
                    'body': resp_body,
                    'ok': 200 <= response.status < 300
                }
        except urllib.error.HTTPError as e:
            return {
                'status': e.code,
                'headers': dict(e.headers),
                'body': e.read().decode('utf-8'),
                'ok': False
            }
        except urllib.error.URLError as e:
            return {
                'status': 0,
                'headers': {},
                'body': str(e.reason),
                'ok': False
            }
    
    def put(self, url, data=None, json_data=None, headers=None, timeout=30):
        """Send PUT request."""
        all_headers = {**self.headers, **(headers or {})}
        
        if json_data is not None:
            body = json.dumps(json_data).encode('utf-8')
            all_headers['Content-Type'] = 'application/json'
        elif data is not None:
            body = urllib.parse.urlencode(data).encode('utf-8')
            all_headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            body = b''
        
        req = urllib.request.Request(
            url,
            data=body,
            headers=all_headers,
            method='PUT'
        )
        
        try:
            with self.opener.open(req, timeout=timeout) as response:
                resp_body = response.read().decode('utf-8')
                
                return {
                    'status': response.status,
                    'headers': dict(response.headers),
                    'body': resp_body,
                    'ok': 200 <= response.status < 300
                }
        except urllib.error.HTTPError as e:
            return {
                'status': e.code,
                'headers': dict(e.headers),
                'body': e.read().decode('utf-8'),
                'ok': False
            }
        except urllib.error.URLError as e:
            return {
                'status': 0,
                'headers': {},
                'body': str(e.reason),
                'ok': False
            }
    
    def delete(self, url, headers=None, timeout=30):
        """Send DELETE request."""
        all_headers = {**self.headers, **(headers or {})}
        
        req = urllib.request.Request(
            url,
            headers=all_headers,
            method='DELETE'
        )
        
        try:
            with self.opener.open(req, timeout=timeout) as response:
                resp_body = response.read().decode('utf-8')
                
                return {
                    'status': response.status,
                    'headers': dict(response.headers),
                    'body': resp_body,
                    'ok': 200 <= response.status < 300
                }
        except urllib.error.HTTPError as e:
            return {
                'status': e.code,
                'headers': dict(e.headers),
                'body': e.read().decode('utf-8'),
                'ok': False
            }
        except urllib.error.URLError as e:
            return {
                'status': 0,
                'headers': {},
                'body': str(e.reason),
                'ok': False
            }
    
    def get_cookies(self):
        """
        Get all session cookies.
        
        Returns:
            Dictionary of cookie name-value pairs
        """
        return {cookie.name: cookie.value for cookie in self.cookies}
    
    def clear_cookies(self):
        """Clear all session cookies."""
        self.cookies.clear()


def create():
    """
    Create new HTTP session.
    
    Returns:
        Session object
    
    Example:
        s = session.create()
        s.set_header("User-Agent", "MyApp/1.0")
        response = s.get("https://api.example.com")
        # Cookies are automatically managed
    """
    return Session()


def create_with_headers(headers):
    """Create session with default headers."""
    s = Session()
    for name, value in headers.items():
        s.set_header(name, value)
    return s


def create_with_auth(username, password):
    """Create session with basic authentication."""
    import base64
    s = Session()
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    s.set_header("Authorization", f"Basic {credentials}")
    return s


__all__ = [
    'Session',
    'create',
    'create_with_headers',
    'create_with_auth',
]
