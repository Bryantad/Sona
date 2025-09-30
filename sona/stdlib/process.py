"""Process execution helpers backing the Sona stdlib ``process`` module."""

from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


class ProcessError(Exception):
    """Base error for process operations."""


class ProcessTimeoutError(ProcessError, TimeoutError):
    """Raised when a process operation times out."""


class ProcessNotFoundError(ProcessError, FileNotFoundError):
    """Raised when the command cannot be found."""


@dataclass(slots=True)
class ProcessHandle:
    """Handle for managing a spawned process."""
    pid: int
    process: subprocess.Popen
    command: str
    args: List[str]
    start_time: float


@dataclass(slots=True)
class ProcessResult:
    """Result of a completed process execution."""
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    success: bool


def run(
    command: str,
    args: List[str] | None = None,
    options: Dict[str, Any] | None = None,
) -> ProcessResult:
    """Execute a command synchronously and return the result."""
    args = args or []
    options = options or {}
    
    timeout_ms = options.get("timeout_ms")
    timeout = None if timeout_ms is None else timeout_ms / 1000.0
    cwd = options.get("cwd")
    env = _prepare_env(options.get("env"))
    capture_output = options.get("capture_output", True)
    
    start_time = time.monotonic()
    
    try:
        result = subprocess.run(
            [command] + args,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
            check=False,
        )
        execution_time = time.monotonic() - start_time
        
        return ProcessResult(
            exit_code=result.returncode,
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            execution_time=execution_time,
            success=result.returncode == 0,
        )
        
    except subprocess.TimeoutExpired as exc:
        execution_time = time.monotonic() - start_time
        raise ProcessTimeoutError(
            f"Process '{command}' timed out after {timeout}s"
        ) from exc
    except FileNotFoundError as exc:
        raise ProcessNotFoundError(f"Command '{command}' not found") from exc


def spawn(
    command: str,
    args: List[str] | None = None,
    options: Dict[str, Any] | None = None,
) -> ProcessHandle:
    """Spawn a process in the background and return a handle."""
    args = args or []
    options = options or {}
    
    cwd = options.get("cwd")
    env = _prepare_env(options.get("env"))
    capture_output = options.get("capture_output", True)
    
    try:
        process = subprocess.Popen(
            [command] + args,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            text=True,
            cwd=cwd,
            env=env,
        )
        
        return ProcessHandle(
            pid=process.pid,
            process=process,
            command=command,
            args=args,
            start_time=time.monotonic(),
        )
        
    except FileNotFoundError as exc:
        raise ProcessNotFoundError(f"Command '{command}' not found") from exc


def wait(
    handle: ProcessHandle,
    timeout_ms: int | None = None,
) -> ProcessResult:
    """Wait for a spawned process to complete."""
    timeout = None if timeout_ms is None else timeout_ms / 1000.0
    
    try:
        stdout, stderr = handle.process.communicate(timeout=timeout)
        execution_time = time.monotonic() - handle.start_time
        
        return ProcessResult(
            exit_code=handle.process.returncode,
            stdout=stdout or "",
            stderr=stderr or "",
            execution_time=execution_time,
            success=handle.process.returncode == 0,
        )
        
    except subprocess.TimeoutExpired as exc:
        raise ProcessTimeoutError(
            f"Process {handle.pid} timed out after {timeout}s"
        ) from exc


def terminate(handle: ProcessHandle, signal_type: str = "TERM") -> bool:
    """Send a termination signal to the process."""
    if handle.process.poll() is not None:
        return False  # Process already terminated
    
    try:
        if os.name == "nt":  # Windows
            if signal_type == "KILL":
                handle.process.kill()
            else:
                handle.process.terminate()
        else:  # Unix-like
            sig = getattr(signal, f"SIG{signal_type}", signal.SIGTERM)
            os.kill(handle.pid, sig)
        return True
    except (OSError, ProcessLookupError):
        return False


def kill(handle: ProcessHandle) -> bool:
    """Force kill the process immediately."""
    return terminate(handle, "KILL")


def status(handle: ProcessHandle) -> Dict[str, Any]:
    """Get the current status of a process."""
    poll_result = handle.process.poll()
    is_running = poll_result is None
    
    return {
        "pid": handle.pid,
        "command": handle.command,
        "args": handle.args,
        "is_running": is_running,
        "exit_code": poll_result,
        "runtime": time.monotonic() - handle.start_time,
        "success": poll_result == 0 if poll_result is not None else None,
    }


def capture(
    command: str,
    args: List[str] | None = None,
    options: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Run a command and capture stdout/stderr separately."""
    result = run(command, args, options)
    
    return {
        "exit_code": result.exit_code,
        "success": result.success,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "execution_time": result.execution_time,
    }


def _prepare_env(env_override: Dict[str, str] | None) -> Dict[str, str] | None:
    """Prepare environment variables for subprocess."""
    if env_override is None:
        return None
    
    # Start with current environment and apply overrides
    env = os.environ.copy()
    env.update(env_override)
    return env


def _timeout_with_cleanup(
    func,
    timeout_seconds: float,
    cleanup_func=None,
):
    """Execute a function with timeout and optional cleanup."""
    result = None
    exception = None
    
    def target():
        nonlocal result, exception
        try:
            result = func()
        except Exception as e:
            exception = e
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout_seconds)
    
    if thread.is_alive():
        if cleanup_func:
            cleanup_func()
        raise ProcessTimeoutError(f"Operation timed out after {timeout_seconds}s")
    
    if exception:
        raise exception
    
    return result


__all__ = [
    "ProcessError",
    "ProcessTimeoutError", 
    "ProcessNotFoundError",
    "ProcessHandle",
    "ProcessResult",
    "run",
    "spawn",
    "wait",
    "terminate",
    "kill",
    "status",
    "capture",
]