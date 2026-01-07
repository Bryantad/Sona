"""
process - Process management for Sona stdlib

Provides process utilities:
- spawn: Spawn new process
- kill: Terminate process
- list: List running processes
"""

import subprocess
import os
import signal as sig
import sys


def spawn(command, args=None, env=None, cwd=None):
    """
    Spawn new process.
    
    Args:
        command: Command to execute
        args: List of arguments
        env: Environment variables
        cwd: Working directory
    
    Returns:
        Process object with pid
    
    Example:
        proc = process.spawn("python", ["script.py"], cwd="/path")
        print(proc.pid)
    """
    args = args or []
    cmd = [command] + args
    
    proc = subprocess.Popen(
        cmd,
        env=env,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    return {
        'pid': proc.pid,
        'process': proc
    }


def kill(pid, force=False):
    """
    Kill process by PID.
    
    Args:
        pid: Process ID
        force: Force kill (SIGKILL vs SIGTERM)
    
    Returns:
        True if successful
    
    Example:
        process.kill(1234)
    """
    try:
        if sys.platform == 'win32':
            import ctypes
            handle = ctypes.windll.kernel32.OpenProcess(1, False, pid)
            ctypes.windll.kernel32.TerminateProcess(handle, 0)
            return True
        else:
            signal = sig.SIGKILL if force else sig.SIGTERM
            os.kill(pid, signal)
            return True
    except Exception:
        return False


def exists(pid):
    """
    Check if process exists.
    
    Args:
        pid: Process ID
    
    Returns:
        True if exists
    
    Example:
        if process.exists(1234):
            print("Running")
    """
    try:
        if sys.platform == 'win32':
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}'],
                capture_output=True,
                text=True
            )
            return str(pid) in result.stdout
        else:
            os.kill(pid, 0)
            return True
    except (OSError, ProcessLookupError):
        return False


def current_pid():
    """
    Get current process ID.
    
    Returns:
        Process ID
    
    Example:
        pid = process.current_pid()
    """
    return os.getpid()


def parent_pid():
    """
    Get parent process ID.
    
    Returns:
        Parent process ID
    
    Example:
        ppid = process.parent_pid()
    """
    return os.getppid()


def wait(pid, timeout=None):
    """
    Wait for process to complete.
    
    Args:
        pid: Process ID
        timeout: Timeout in seconds
    
    Returns:
        Exit code
    
    Example:
        code = process.wait(1234, timeout=10)
    """
    import time
    start = time.time()
    
    while exists(pid):
        if timeout and (time.time() - start) > timeout:
            raise TimeoutError(f"Process {pid} did not exit within {timeout}s")
        time.sleep(0.1)
    
    return 0


def run_with_timeout(command, timeout, args=None):
    """
    Run process with timeout.
    
    Args:
        command: Command to execute
        timeout: Timeout in seconds
        args: Command arguments
    
    Returns:
        Dictionary with output and code
    
    Example:
        result = process.run_with_timeout("sleep", 2, ["10"])
    """
    args = args or []
    cmd = [command] + args
    
    try:
        result = subprocess.run(
            cmd,
            timeout=timeout,
            capture_output=True,
            text=True
        )
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'code': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'stdout': '',
            'stderr': f'Timeout after {timeout}s',
            'code': -1
        }


def get_children(pid):
    """
    Get child processes of a process.
    
    Args:
        pid: Parent process ID
    
    Returns:
        List of child PIDs
    
    Example:
        children = process.get_children(1234)
    """
    if sys.platform == 'win32':
        result = subprocess.run(
            ['wmic', 'process', 'where', f'ParentProcessId={pid}', 'get', 'ProcessId'],
            capture_output=True,
            text=True
        )
        lines = result.stdout.strip().split('\n')[1:]
        return [int(line.strip()) for line in lines if line.strip().isdigit()]
    else:
        result = subprocess.run(
            ['pgrep', '-P', str(pid)],
            capture_output=True,
            text=True
        )
        return [int(p) for p in result.stdout.strip().split('\n') if p]


def terminate(proc):
    """
    Gracefully terminate process object.
    
    Args:
        proc: Process object from spawn()
    
    Example:
        proc = process.spawn("python", ["server.py"])
        process.terminate(proc['process'])
    """
    if hasattr(proc, 'terminate'):
        proc.terminate()
        proc.wait()


def get_info(pid):
    """
    Get process information.
    
    Args:
        pid: Process ID
    
    Returns:
        Dictionary with process info
    
    Example:
        info = process.get_info(1234)
    """
    if not exists(pid):
        return None
    
    info = {'pid': pid}
    
    if sys.platform == 'win32':
        result = subprocess.run(
            ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
            capture_output=True,
            text=True
        )
        if result.stdout:
            parts = result.stdout.strip().split(',')
            if len(parts) >= 2:
                info['name'] = parts[0].strip('"')
    else:
        result = subprocess.run(
            ['ps', '-p', str(pid), '-o', 'comm='],
            capture_output=True,
            text=True
        )
        if result.stdout:
            info['name'] = result.stdout.strip()
    
    return info


def is_running(pid):
    """
    Check if process is running (alias for exists).
    
    Args:
        pid: Process ID
    
    Returns:
        True if running
    
    Example:
        if process.is_running(1234):
            print("Active")
    """
    return exists(pid)


def exit_code(pid):
    """
    Get exit code of completed process.
    
    Args:
        pid: Process ID
    
    Returns:
        Exit code or None if still running
    
    Example:
        code = process.exit_code(1234)
    """
    if exists(pid):
        return None
    return 0


__all__ = [
    'spawn', 'kill', 'exists', 'current_pid', 'parent_pid',
    'wait', 'run_with_timeout', 'get_children', 'terminate',
    'get_info', 'is_running', 'exit_code'
]
