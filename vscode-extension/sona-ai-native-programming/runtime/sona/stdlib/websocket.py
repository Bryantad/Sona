"""
websocket - WebSocket client for Sona stdlib

Provides WebSocket functionality:
- connect: Connect to WebSocket server
- send/receive: Message exchange
- close: Close connection

Note: This is a simplified implementation.
For production use, consider external WebSocket libraries.
"""

import socket
import base64
import hashlib
import struct
import urllib.parse


class WebSocket:
    """WebSocket client connection."""
    
    def __init__(self, sock):
        """Initialize with socket."""
        self.sock = sock
        self.connected = True
    
    def send(self, message):
        """
        Send text message.
        
        Args:
            message: Text message to send
        
        Example:
            ws.send("Hello, server!")
        """
        if not self.connected:
            raise RuntimeError("WebSocket not connected")
        
        if isinstance(message, str):
            message = message.encode('utf-8')
        
        # Frame format: FIN + opcode(1=text) + mask + length + payload
        frame = bytearray()
        frame.append(0x81)  # FIN + text frame
        
        length = len(message)
        if length < 126:
            frame.append(0x80 | length)  # Mask bit + length
        elif length < 65536:
            frame.append(0x80 | 126)
            frame.extend(struct.pack('>H', length))
        else:
            frame.append(0x80 | 127)
            frame.extend(struct.pack('>Q', length))
        
        # Masking key
        mask = bytes([0x12, 0x34, 0x56, 0x78])
        frame.extend(mask)
        
        # Masked payload
        masked = bytearray(message)
        for i in range(len(masked)):
            masked[i] ^= mask[i % 4]
        frame.extend(masked)
        
        self.sock.sendall(bytes(frame))
    
    def receive(self, timeout=30):
        """
        Receive message.
        
        Args:
            timeout: Receive timeout in seconds
        
        Returns:
            Received message string
        
        Example:
            msg = ws.receive()
        """
        if not self.connected:
            raise RuntimeError("WebSocket not connected")
        
        self.sock.settimeout(timeout)
        
        # Read first 2 bytes
        header = self.sock.recv(2)
        if len(header) < 2:
            return None
        
        # Parse frame
        opcode = header[0] & 0x0F
        masked = (header[1] & 0x80) != 0
        length = header[1] & 0x7F
        
        # Extended length
        if length == 126:
            ext_len = self.sock.recv(2)
            length = struct.unpack('>H', ext_len)[0]
        elif length == 127:
            ext_len = self.sock.recv(8)
            length = struct.unpack('>Q', ext_len)[0]
        
        # Masking key (if present)
        if masked:
            mask = self.sock.recv(4)
        
        # Payload
        payload = bytearray()
        while len(payload) < length:
            chunk = self.sock.recv(length - len(payload))
            if not chunk:
                break
            payload.extend(chunk)
        
        # Unmask if needed
        if masked:
            for i in range(len(payload)):
                payload[i] ^= mask[i % 4]
        
        # Handle close frame
        if opcode == 0x08:
            self.connected = False
            return None
        
        return payload.decode('utf-8')
    
    def close(self):
        """
        Close WebSocket connection.
        
        Example:
            ws.close()
        """
        if self.connected:
            # Send close frame
            frame = bytearray([0x88, 0x00])
            try:
                self.sock.sendall(bytes(frame))
            except Exception:
                pass
            
            self.sock.close()
            self.connected = False


def connect(url, timeout=30):
    """
    Connect to WebSocket server.
    
    Args:
        url: WebSocket URL (ws:// or wss://)
        timeout: Connection timeout
    
    Returns:
        WebSocket object
    
    Example:
        ws = websocket.connect("ws://localhost:8080/chat")
        ws.send("Hello")
        msg = ws.receive()
        ws.close()
    """
    # Parse URL
    parsed = urllib.parse.urlparse(url)
    
    if parsed.scheme not in ('ws', 'wss'):
        raise ValueError("URL must start with ws:// or wss://")
    
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == 'wss' else 80)
    path = parsed.path or '/'
    
    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    # Connect
    sock.connect((host, port))
    
    # Generate WebSocket key
    key = base64.b64encode(bytes([i for i in range(16)])).decode('utf-8')
    
    # Send handshake
    handshake = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"\r\n"
    )
    
    sock.sendall(handshake.encode('utf-8'))
    
    # Receive handshake response
    response = b''
    while b'\r\n\r\n' not in response:
        chunk = sock.recv(1024)
        if not chunk:
            raise RuntimeError("Connection closed during handshake")
        response += chunk
    
    # Verify handshake
    if b'HTTP/1.1 101' not in response:
        raise RuntimeError("WebSocket handshake failed")
    
    # Calculate expected accept key
    magic = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    accept_key = base64.b64encode(
        hashlib.sha1((key + magic).encode()).digest()
    ).decode()
    
    if accept_key.encode() not in response:
        raise RuntimeError("Invalid Sec-WebSocket-Accept key")
    
    return WebSocket(sock)


def is_ws_url(url):
    """Check if URL is a valid WebSocket URL."""
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.scheme in ('ws', 'wss')
    except Exception:
        return False


def parse_ws_url(url):
    """Parse WebSocket URL into components."""
    parsed = urllib.parse.urlparse(url)
    return {
        'scheme': parsed.scheme,
        'host': parsed.hostname,
        'port': parsed.port or (443 if parsed.scheme == 'wss' else 80),
        'path': parsed.path or '/',
        'secure': parsed.scheme == 'wss'
    }


def create_ws_url(host, port=80, path='/', secure=False):
    """Create WebSocket URL from components."""
    scheme = 'wss' if secure else 'ws'
    return f"{scheme}://{host}:{port}{path}"


__all__ = [
    'WebSocket',
    'connect',
    'is_ws_url',
    'parse_ws_url',
    'create_ws_url',
]
