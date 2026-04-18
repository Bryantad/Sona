"""
ftp - FTP client for Sona stdlib

Provides FTP operations:
- connect: Connect to FTP server
- upload/download: File transfer
- list: List directory contents
"""

from ftplib import FTP, FTP_TLS
import os


class FTPClient:
    """FTP client wrapper."""
    
    def __init__(self, host, port=21, user='', passwd='', tls=False):
        """Initialize and connect to FTP server."""
        if tls:
            self.ftp = FTP_TLS()
        else:
            self.ftp = FTP()
        
        self.ftp.connect(host, port)
        self.ftp.login(user, passwd)
        
        if tls:
            self.ftp.prot_p()
    
    def list(self, path='.'):
        """List directory contents."""
        return self.ftp.nlst(path)
    
    def upload(self, local_path, remote_path):
        """Upload file."""
        with open(local_path, 'rb') as f:
            self.ftp.storbinary(f'STOR {remote_path}', f)
    
    def download(self, remote_path, local_path):
        """Download file."""
        with open(local_path, 'wb') as f:
            self.ftp.retrbinary(f'RETR {remote_path}', f.write)
    
    def delete(self, remote_path):
        """Delete file."""
        self.ftp.delete(remote_path)
    
    def mkdir(self, dirname):
        """Create directory."""
        self.ftp.mkd(dirname)
    
    def rmdir(self, dirname):
        """Remove directory."""
        self.ftp.rmd(dirname)
    
    def cwd(self, path):
        """Change working directory."""
        self.ftp.cwd(path)
    
    def pwd(self):
        """Get current directory."""
        return self.ftp.pwd()
    
    def close(self):
        """Close connection."""
        self.ftp.quit()


def connect(host, port=21, user='anonymous', passwd='', tls=False):
    """
    Connect to FTP server.
    
    Args:
        host: FTP server host
        port: FTP port (default 21)
        user: Username
        passwd: Password
        tls: Use FTP over TLS
    
    Returns:
        FTPClient object
    
    Example:
        client = ftp.connect("ftp.example.com", user="user", passwd="pass")
        files = client.list()
        client.download("file.txt", "/local/path/file.txt")
        client.close()
    """
    return FTPClient(host, port, user, passwd, tls)


def download_file(host, remote_path, local_path, user='anonymous', passwd=''):
    """Quick download file from FTP server."""
    client = connect(host, user=user, passwd=passwd)
    client.download(remote_path, local_path)
    client.close()
    return local_path


def upload_file(host, local_path, remote_path, user='anonymous', passwd=''):
    """Quick upload file to FTP server."""
    client = connect(host, user=user, passwd=passwd)
    client.upload(local_path, remote_path)
    client.close()
    return remote_path


def list_files(host, path='.', user='anonymous', passwd=''):
    """Quick list files on FTP server."""
    client = connect(host, user=user, passwd=passwd)
    files = client.list(path)
    client.close()
    return files


__all__ = [
    'FTPClient',
    'connect',
    'download_file',
    'upload_file',
    'list_files',
]
