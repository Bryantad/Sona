"""
cli - Command-line interface utilities for Sona stdlib

Provides utilities for building CLI applications:
- args: Access command-line arguments
- prompt: Interactive user input with optional masking
- echo: Output text with optional Windows-safe styling
"""

import sys
import getpass
import platform


def args():
    """
    Get command-line arguments.
    
    Returns:
        List of command-line arguments (excluding script name)
    
    Example:
        # Running: sona script.sona arg1 arg2
        cli.args() → ["arg1", "arg2"]
    """
    return sys.argv[1:]


def prompt(label, secret=False):
    """
    Prompt user for input.
    
    Args:
        label: Prompt text to display
        secret: If True, hide input (for passwords)
    
    Returns:
        User input as string
    
    Example:
        name = cli.prompt("Enter your name: ")
        password = cli.prompt("Password: ", secret=True)
    """
    if secret:
        return getpass.getpass(label)
    else:
        return input(label)


def echo(text, style=None):
    """
    Print text to console with optional styling.
    
    Args:
        text: Text to print
        style: Optional style name (Windows-safe):
            - "info": Blue text (informational)
            - "success": Green text (success message)
            - "warning": Yellow text (warning)
            - "error": Red text (error message)
            - "bold": Bold text
            - None: Normal text (default)
    
    Example:
        cli.echo("Hello, World!")
        cli.echo("Success!", style="success")
        cli.echo("Warning: Check input", style="warning")
    """
    # Windows-safe color codes
    # Check if we're in a terminal that supports ANSI codes
    is_windows = platform.system() == 'Windows'
    supports_color = sys.stdout.isatty()
    
    # ANSI color codes (Windows 10+ supports these in modern terminals)
    styles = {
        'info': '\033[94m',      # Blue
        'success': '\033[92m',   # Green
        'warning': '\033[93m',   # Yellow
        'error': '\033[91m',     # Red
        'bold': '\033[1m',       # Bold
    }
    reset = '\033[0m'
    
    # Apply styling if supported and requested
    if style and style in styles and supports_color:
        # On Windows, check if ANSI is enabled
        if is_windows:
            try:
                # Try to enable ANSI escape sequences on Windows
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except Exception:
                # If we can't enable ANSI, just print without color
                print(text)
                return
        
        print(f"{styles[style]}{text}{reset}")
    else:
        print(text)


def error(text):
    """
    Print error message to stderr with styling.
    
    Args:
        text: Error message to print
    
    Example:
        cli.error("Failed to load file!")
    """
    is_windows = platform.system() == 'Windows'
    supports_color = sys.stderr.isatty()
    
    error_style = '\033[91m'  # Red
    reset = '\033[0m'
    
    if supports_color:
        if is_windows:
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-12), 7)
            except Exception:
                print(text, file=sys.stderr)
                return
        
        print(f"{error_style}{text}{reset}", file=sys.stderr)
    else:
        print(text, file=sys.stderr)


def confirm(message, default=False):
    """
    Ask user for yes/no confirmation.
    
    Args:
        message: Confirmation message
        default: Default value if user presses Enter
    
    Returns:
        True if confirmed, False otherwise
    
    Example:
        if cli.confirm("Delete file?"):
            delete_file()
    """
    suffix = " [Y/n]: " if default else " [y/N]: "
    response = input(message + suffix).strip().lower()
    
    if not response:
        return default
    
    return response in ('y', 'yes')


def select(message, options):
    """
    Interactive selection from list of options.
    
    Args:
        message: Prompt message
        options: List of option strings
    
    Returns:
        Selected option string
    
    Example:
        choice = cli.select("Choose:", ["Option A", "Option B"])
    """
    print(message)
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    
    while True:
        try:
            choice = int(input("Enter number: "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
            print(f"Please enter a number between 1 and {len(options)}")
        except ValueError:
            print("Please enter a valid number")


def progress_bar(current, total, width=50, prefix="Progress"):
    """
    Display progress bar.
    
    Args:
        current: Current progress value
        total: Total value
        width: Bar width in characters
        prefix: Prefix text
    
    Example:
        for i in range(100):
            cli.progress_bar(i+1, 100)
    """
    percent = int((current / total) * 100)
    filled = int((current / total) * width)
    bar = '█' * filled + '-' * (width - filled)
    print(f'\r{prefix}: |{bar}| {percent}%', end='', flush=True)
    if current == total:
        print()  # New line when complete


def clear():
    """
    Clear the terminal screen.
    
    Example:
        cli.clear()
    """
    import os
    os.system('cls' if platform.system() == 'Windows' else 'clear')


def get_terminal_size():
    """
    Get terminal dimensions.
    
    Returns:
        Tuple of (columns, rows)
    
    Example:
        width, height = cli.get_terminal_size()
    """
    import shutil
    size = shutil.get_terminal_size()
    return (size.columns, size.lines)


def spinner(text="Loading"):
    """
    Create a simple loading spinner context manager.
    
    Args:
        text: Loading text
    
    Returns:
        Context manager
    
    Example:
        with cli.spinner("Processing"):
            time.sleep(2)
    """
    import time
    import threading
    
    class Spinner:
        def __init__(self, msg):
            self.msg = msg
            self.spinning = False
            self.thread = None
        
        def spin(self):
            chars = '|/-\\'
            idx = 0
            while self.spinning:
                print(f'\r{self.msg} {chars[idx]}', end='', flush=True)
                idx = (idx + 1) % len(chars)
                time.sleep(0.1)
            print('\r' + ' ' * (len(self.msg) + 2) + '\r', end='', flush=True)
        
        def __enter__(self):
            self.spinning = True
            self.thread = threading.Thread(target=self.spin)
            self.thread.start()
            return self
        
        def __exit__(self, *args):
            self.spinning = False
            if self.thread:
                self.thread.join()
    
    return Spinner(text)


__all__ = [
    'args',
    'prompt',
    'echo',
    'error',
    'confirm',
    'select',
    'progress_bar',
    'clear',
    'get_terminal_size',
    'spinner'
]
