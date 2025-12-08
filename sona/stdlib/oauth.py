"""
oauth - OAuth authentication for Sona stdlib

Provides OAuth utilities:
- OAuth1/OAuth2 helpers
- Token management
"""

import urllib.parse
import urllib.request
import json
import time
import hashlib
import hmac
import base64


__all__ = [
    'oauth2_auth_url',
    'oauth2_exchange_code',
    'oauth2_refresh_token',
    'create_token_store',
    'parse_callback_url',
    'validate_state',
    'build_bearer_header',
    'generate_pkce_pair'
]


def oauth2_auth_url(client_id, redirect_uri, scope=None, state=None, auth_endpoint=''):
    """
    Generate OAuth2 authorization URL.
    
    Args:
        client_id: OAuth client ID
        redirect_uri: Redirect URI
        scope: Permission scopes
        state: State parameter
        auth_endpoint: Authorization endpoint URL
    
    Returns:
        Authorization URL
    
    Example:
        url = oauth.oauth2_auth_url(
            "client_123",
            "https://myapp.com/callback",
            scope="read write",
            auth_endpoint="https://provider.com/oauth/authorize"
        )
    """
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code'
    }
    
    if scope:
        params['scope'] = scope
    if state:
        params['state'] = state
    
    query = urllib.parse.urlencode(params)
    return f"{auth_endpoint}?{query}"


def oauth2_exchange_code(code, client_id, client_secret, redirect_uri, token_endpoint):
    """
    Exchange authorization code for access token.
    
    Args:
        code: Authorization code
        client_id: OAuth client ID
        client_secret: OAuth client secret
        redirect_uri: Redirect URI
        token_endpoint: Token endpoint URL
    
    Returns:
        Token response dictionary
    
    Example:
        tokens = oauth.oauth2_exchange_code(
            code,
            "client_123",
            "secret_456",
            "https://myapp.com/callback",
            "https://provider.com/oauth/token"
        )
    """
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri
    }
    
    body = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(token_endpoint, data=body, method='POST')
    
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))


def oauth2_refresh_token(refresh_token, client_id, client_secret, token_endpoint):
    """
    Refresh access token.
    
    Args:
        refresh_token: Refresh token
        client_id: OAuth client ID
        client_secret: OAuth client secret
        token_endpoint: Token endpoint URL
    
    Returns:
        New token response
    
    Example:
        tokens = oauth.oauth2_refresh_token(
            refresh_token,
            "client_123",
            "secret_456",
            "https://provider.com/oauth/token"
        )
    """
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    body = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(token_endpoint, data=body, method='POST')
    
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))


class TokenStore:
    """Simple token storage."""
    
    def __init__(self):
        """Initialize store."""
        self.tokens = {}
    
    def save(self, key, access_token, refresh_token=None, expires_at=None):
        """Save tokens."""
        self.tokens[key] = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_at': expires_at
        }
    
    def get(self, key):
        """Get tokens."""
        return self.tokens.get(key)
    
    def is_expired(self, key):
        """Check if token is expired."""
        token_data = self.tokens.get(key)
        if not token_data or not token_data['expires_at']:
            return False
        
        return time.time() >= token_data['expires_at']


def create_token_store():
    """
    Create token store.
    
    Returns:
        TokenStore object
    
    Example:
        store = oauth.create_token_store()
        store.save("user123", access_token, refresh_token, expires_at)
        token = store.get("user123")
    """
    return TokenStore()


def parse_callback_url(callback_url):
    """
    Parse OAuth callback URL to extract authorization code and state.
    
    Args:
        callback_url (str): Full callback URL from OAuth provider
    
    Returns:
        dict: Contains 'code', 'state', and 'error' (if any)
    
    Example:
        result = oauth.parse_callback_url("https://app.com/callback?code=abc123&state=xyz")
        print(result['code'])  # "abc123"
    """
    from urllib.parse import urlparse, parse_qs
    
    parsed = urlparse(callback_url)
    params = parse_qs(parsed.query)
    
    return {
        'code': params.get('code', [None])[0],
        'state': params.get('state', [None])[0],
        'error': params.get('error', [None])[0],
        'error_description': params.get('error_description', [None])[0]
    }


def validate_state(received_state, expected_state):
    """
    Validate OAuth state parameter to prevent CSRF attacks.
    
    Args:
        received_state (str): State from callback URL
        expected_state (str): Expected state value
    
    Returns:
        bool: True if states match
    
    Example:
        is_valid = oauth.validate_state(callback_state, session_state)
    """
    if not received_state or not expected_state:
        return False
    return received_state == expected_state


def build_bearer_header(access_token):
    """
    Build Authorization header for OAuth2 Bearer token.
    
    Args:
        access_token (str): Access token
    
    Returns:
        dict: Headers dictionary with Authorization field
    
    Example:
        headers = oauth.build_bearer_header(token)
        # {'Authorization': 'Bearer abc123...'}
    """
    return {
        'Authorization': f'Bearer {access_token}'
    }


def generate_pkce_pair():
    """
    Generate PKCE code verifier and challenge for OAuth2 (RFC 7636).
    
    Returns:
        dict: Contains 'code_verifier' and 'code_challenge'
    
    Example:
        pkce = oauth.generate_pkce_pair()
        # Use pkce['code_challenge'] in auth URL
        # Use pkce['code_verifier'] when exchanging code
    """
    import secrets
    import hashlib
    import base64
    
    # Generate code verifier (43-128 characters)
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    # Generate code challenge (SHA256 hash of verifier)
    challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
    
    return {
        'code_verifier': code_verifier,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
