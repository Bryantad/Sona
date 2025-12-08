"""
dns - DNS resolution utilities for Sona stdlib

Provides DNS lookups:
- resolve: Resolve hostname to IP
- reverse: Reverse DNS lookup
- resolve_all: Get all IPs for hostname
"""

import socket


def resolve(hostname):
    """
    Resolve hostname to IP address.
    
    Args:
        hostname: Domain name to resolve
    
    Returns:
        IP address string
    
    Example:
        ip = dns.resolve("google.com")
        # "142.250.185.46"
    """
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror as e:
        raise RuntimeError(f"DNS resolution failed: {e}")


def resolve_all(hostname):
    """
    Resolve hostname to all IP addresses.
    
    Args:
        hostname: Domain name to resolve
    
    Returns:
        List of IP addresses
    
    Example:
        ips = dns.resolve_all("google.com")
        # ["142.250.185.46", "2607:f8b0:4004:c07::66"]
    """
    try:
        result = socket.getaddrinfo(hostname, None)
        # Extract unique IPs
        ips = list(set(addr[4][0] for addr in result))
        return ips
    except socket.gaierror as e:
        raise RuntimeError(f"DNS resolution failed: {e}")


def reverse(ip_address):
    """
    Perform reverse DNS lookup.
    
    Args:
        ip_address: IP address to lookup
    
    Returns:
        Hostname string
    
    Example:
        hostname = dns.reverse("8.8.8.8")
        # "dns.google"
    """
    try:
        return socket.gethostbyaddr(ip_address)[0]
    except socket.herror as e:
        raise RuntimeError(f"Reverse DNS lookup failed: {e}")


def get_hostname():
    """
    Get local machine hostname.
    
    Returns:
        Hostname string
    
    Example:
        name = dns.get_hostname()
    """
    return socket.gethostname()


def get_fqdn():
    """
    Get fully qualified domain name.
    
    Returns:
        FQDN string
    
    Example:
        fqdn = dns.get_fqdn()
    """
    return socket.getfqdn()
