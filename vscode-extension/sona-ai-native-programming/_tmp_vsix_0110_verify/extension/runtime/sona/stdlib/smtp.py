"""
smtp - Email sending via SMTP for Sona stdlib

Provides email functionality:
- send: Send email messages
- send_html: Send HTML email
- SMTP connection management
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os


def send(host, port, username, password, to, subject, body, from_addr=None, use_tls=True):
    """
    Send plain text email.
    
    Args:
        host: SMTP server host
        port: SMTP server port
        username: SMTP username
        password: SMTP password
        to: Recipient email (or list)
        subject: Email subject
        body: Email body (plain text)
        from_addr: Sender email (default: username)
        use_tls: Use TLS encryption
    
    Returns:
        True if sent successfully
    
    Example:
        smtp.send(
            "smtp.gmail.com", 587,
            "user@gmail.com", "password",
            "recipient@example.com",
            "Test Subject",
            "Hello, this is a test!"
        )
    """
    from_addr = from_addr or username
    
    # Create message
    msg = MIMEText(body, 'plain')
    msg['From'] = from_addr
    msg['To'] = to if isinstance(to, str) else ', '.join(to)
    msg['Subject'] = subject
    
    # Send email
    try:
        with smtplib.SMTP(host, port) as server:
            if use_tls:
                server.starttls()
            server.login(username, password)
            server.send_message(msg)
        return True
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {e}")


def send_html(host, port, username, password, to, subject, html, from_addr=None, use_tls=True):
    """
    Send HTML email.
    
    Args:
        host: SMTP server host
        port: SMTP server port
        username: SMTP username
        password: SMTP password
        to: Recipient email (or list)
        subject: Email subject
        html: Email body (HTML)
        from_addr: Sender email (default: username)
        use_tls: Use TLS encryption
    
    Returns:
        True if sent successfully
    
    Example:
        smtp.send_html(
            "smtp.gmail.com", 587,
            "user@gmail.com", "password",
            "recipient@example.com",
            "HTML Email",
            "<h1>Hello</h1><p>This is HTML!</p>"
        )
    """
    from_addr = from_addr or username
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['From'] = from_addr
    msg['To'] = to if isinstance(to, str) else ', '.join(to)
    msg['Subject'] = subject
    
    # Attach HTML
    html_part = MIMEText(html, 'html')
    msg.attach(html_part)
    
    # Send email
    try:
        with smtplib.SMTP(host, port) as server:
            if use_tls:
                server.starttls()
            server.login(username, password)
            server.send_message(msg)
        return True
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {e}")


def send_with_attachment(host, port, username, password, to, subject, body, 
                         attachment_path, from_addr=None, use_tls=True):
    """
    Send email with file attachment.
    
    Args:
        host: SMTP server host
        port: SMTP server port
        username: SMTP username
        password: SMTP password
        to: Recipient email (or list)
        subject: Email subject
        body: Email body (plain text)
        attachment_path: Path to file to attach
        from_addr: Sender email (default: username)
        use_tls: Use TLS encryption
    
    Returns:
        True if sent successfully
    
    Example:
        smtp.send_with_attachment(
            "smtp.gmail.com", 587,
            "user@gmail.com", "password",
            "recipient@example.com",
            "File Attached",
            "Please find the file attached.",
            "/path/to/file.pdf"
        )
    """
    from_addr = from_addr or username
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to if isinstance(to, str) else ', '.join(to)
    msg['Subject'] = subject
    
    # Attach body
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach file
    filename = os.path.basename(attachment_path)
    with open(attachment_path, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
    
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename= {filename}')
    msg.attach(part)
    
    # Send email
    try:
        with smtplib.SMTP(host, port) as server:
            if use_tls:
                server.starttls()
            server.login(username, password)
            server.send_message(msg)
        return True
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {e}")


def validate_email(email):
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def send_bulk(host, port, username, password, recipients, subject, body, 
              from_addr=None, use_tls=True):
    """Send email to multiple recipients."""
    from_addr = from_addr or username
    results = []
    
    for recipient in recipients:
        try:
            send(host, port, username, password, recipient, subject, body,
                 from_addr, use_tls)
            results.append({'email': recipient, 'success': True})
        except Exception as e:
            results.append({'email': recipient, 'success': False, 'error': str(e)})
    
    return results


def create_message(to, subject, body, from_addr, html=False):
    """Create email message object."""
    if html:
        msg = MIMEMultipart('alternative')
        msg.attach(MIMEText(body, 'html'))
    else:
        msg = MIMEText(body, 'plain')
    
    msg['From'] = from_addr
    msg['To'] = to if isinstance(to, str) else ', '.join(to)
    msg['Subject'] = subject
    
    return msg


__all__ = [
    'send',
    'send_html',
    'send_with_attachment',
    'validate_email',
    'send_bulk',
    'create_message',
]
