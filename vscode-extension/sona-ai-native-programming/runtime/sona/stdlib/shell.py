"""
shell - Shell command execution for Sona stdlib

Provides shell utilities:
- run: Execute shell commands
- capture: Capture command output
- background: Run in background
"""

import subprocess
import shlex
import sys


def run(command, shell=True, check=True, timeout=None):
    """
    Run shell command.
    
    Args:
        command: Command to execute
        shell: Use shell (default True)
        check: Raise error on failure
        timeout: Command timeout in seconds
    
    Returns:
        Exit code
    
    Example:
        code = shell.run("ls -la")
    """
    try:
        result = subprocess.run(
            command,
            shell=shell,
            check=check,
            timeout=timeout
        )
        return result.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Command timed out after {timeout}s")


def capture(command, shell=True, timeout=None):
    """
    Run command and capture output.
    
    Args:
        command: Command to execute
        shell: Use shell (default True)
        timeout: Command timeout in seconds
    
    Returns:
        Dictionary with stdout, stderr, code
    
    Example:
        result = shell.capture("echo 'hello'")
        # {"stdout": "hello\\n", "stderr": "", "code": 0}
    """
    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'code': result.returncode
        }
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Command timed out after {timeout}s")


def background(command, shell=True):
    """
    Run command in background.
    
    Args:
        command: Command to execute
        shell: Use shell (default True)
    
    Returns:
        Process object
    
    Example:
        proc = shell.background("python server.py")
        # Later: proc.terminate()
    """
    return subprocess.Popen(
        command,
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


def which(command):
    """
    Find command in PATH.
    
    Args:
        command: Command name
    
    Returns:
        Full path or None
    
    Example:
        python_path = shell.which("python")
    """
    result = subprocess.run(
        ['which' if sys.platform != 'win32' else 'where', command],
        capture_output=True,
        text=True,
        shell=False
    )
    
    if result.returncode == 0:
        return result.stdout.strip().split('\n')[0]
    return None


def exists(command):
    """
    Check if command exists.
    
    Args:
        command: Command name
    
    Returns:
        True if exists
    
    Example:
        has_git = shell.exists("git")
    """
    return which(command) is not None


def pipe(commands, shell=True, timeout=None):
    """
    Pipe multiple commands together.
    
    Args:
        commands: List of commands
        shell: Use shell (default True)
        timeout: Command timeout in seconds
    
    Returns:
        Dictionary with final stdout, stderr, code
    
    Example:
        result = shell.pipe(["echo hello", "grep ell"])
    """
    processes = []
    
    for i, cmd in enumerate(commands):
        stdin = processes[-1].stdout if processes else None
        proc = subprocess.Popen(
            cmd,
            shell=shell,
            stdin=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes.append(proc)
    
    stdout, stderr = processes[-1].communicate(timeout=timeout)
    
    return {
        'stdout': stdout,
        'stderr': stderr,
        'code': processes[-1].returncode
    }


def env_var(name, default=None):
    """
    Get environment variable.
    
    Args:
        name: Variable name
        default: Default value if not found
    
    Returns:
        Variable value or default
    
    Example:
        path = shell.env_var("PATH")
    """
    import os
    return os.environ.get(name, default)


def set_env(name, value):
    """
    Set environment variable.
    
    Args:
        name: Variable name
        value: Variable value
    
    Example:
        shell.set_env("MY_VAR", "value")
    """
    import os
    os.environ[name] = str(value)


def cwd():
    """
    Get current working directory.
    
    Returns:
        Current directory path
    
    Example:
        current = shell.cwd()
    """
    import os
    return os.getcwd()


def cd(path):
    """
    Change current directory.
    
    Args:
        path: Directory path
    
    Example:
        shell.cd("/tmp")
    """
    import os
    os.chdir(path)


def quote(arg):
    """
    Quote shell argument safely.
    
    Args:
        arg: Argument to quote
    
    Returns:
        Quoted argument
    
    Example:
        safe = shell.quote("file with spaces.txt")
    """
    return shlex.quote(str(arg))


def split(command):
    """
    Split command into arguments.
    
    Args:
        command: Command string
    
    Returns:
        List of arguments
    
    Example:
        args = shell.split('echo "hello world"')
        # ['echo', 'hello world']
    """
    return shlex.split(command)


def execute(command, cwd=None, env=None, timeout=None):
    """
    Execute command with custom environment/directory.
    
    Args:
        command: Command to execute
        cwd: Working directory
        env: Environment variables dict
        timeout: Timeout in seconds
    
    Returns:
        Dictionary with stdout, stderr, code
    
    Example:
        result = shell.execute("ls", cwd="/tmp")
    """
    result = subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    
    return {
        'stdout': result.stdout,
        'stderr': result.stderr,
        'code': result.returncode
    }


def interactive(command):
    """
    Run command with interactive I/O.
    
    Args:
        command: Command to execute
    
    Returns:
        Exit code
    
    Example:
        shell.interactive("python")
    """
    result = subprocess.run(command, shell=True)
    return result.returncode


__all__ = [
    'run', 'capture', 'background', 'which', 'exists',
    'pipe', 'env_var', 'set_env', 'cwd', 'cd', 'quote',
    'split', 'execute', 'interactive'
]
