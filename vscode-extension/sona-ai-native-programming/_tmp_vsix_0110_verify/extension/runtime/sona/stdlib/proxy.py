"""
proxy - HTTP proxy utilities for Sona stdlib

Provides proxy handling:
- configure: Configure proxy settings
- request: Make request through proxy
"""

import urllib.request
import urllib.error


def configure(http_proxy=None, https_proxy=None):
    """
    Configure global proxy settings.
    
    Args:
        http_proxy: HTTP proxy URL
        https_proxy: HTTPS proxy URL
    
    Returns:
        Proxy handler
    
    Example:
        proxy.configure(
            http_proxy="http://proxy.example.com:8080",
            https_proxy="https://proxy.example.com:8080"
        )
    """
    proxies = {}
    if http_proxy:
        proxies['http'] = http_proxy
    if https_proxy:
        proxies['https'] = https_proxy
    
    return urllib.request.ProxyHandler(proxies)


def request(url, proxy_url, method='GET', data=None, headers=None, timeout=30):
    """
    Make request through proxy.
    
    Args:
        url: Target URL
        proxy_url: Proxy server URL
        method: HTTP method
        data: Request body
        headers: Request headers
        timeout: Request timeout
    
    Returns:
        Response dictionary
    
    Example:
        response = proxy.request(
            "https://api.example.com/data",
            "http://proxy.example.com:8080"
        )
    """
    # Configure proxy
    proxy_handler = urllib.request.ProxyHandler({
        'http': proxy_url,
        'https': proxy_url
    })
    opener = urllib.request.build_opener(proxy_handler)
    
    # Prepare request
    headers = headers or {}
    if data and isinstance(data, str):
        data = data.encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with opener.open(req, timeout=timeout) as response:
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


def get_system_proxy():
    """
    Get system proxy settings.
    
    Returns:
        Dictionary with proxy URLs
    
    Example:
        proxies = proxy.get_system_proxy()
        # {"http": "...", "https": "..."}
    """
    proxy_handler = urllib.request.getproxies()
    return proxy_handler


def parse_proxy_url(proxy_url):
    """Parse proxy URL into components."""
    from urllib.parse import urlparse
    parsed = urlparse(proxy_url)
    return {
        'scheme': parsed.scheme,
        'host': parsed.hostname,
        'port': parsed.port or 8080,
        'username': parsed.username,
        'password': parsed.password
    }


def build_proxy_url(host, port=8080, username=None, password=None, scheme='http'):
    """Build proxy URL from components."""
    if username and password:
        return f"{scheme}://{username}:{password}@{host}:{port}"
    return f"{scheme}://{host}:{port}"


__all__ = [
    'configure',
    'request',
    'get_system_proxy',
    'parse_proxy_url',
    'build_proxy_url',
]
