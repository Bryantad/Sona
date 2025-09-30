"""Native glue exposing :mod:`sona.stdlib.process` helpers to Sona."""

from __future__ import annotations

import platform
from typing import Any, Dict, List

from . import process as _process


def _normalize_args(args: Any) -> List[str]:
    """Convert various argument formats to string list."""
    if args is None:
        return []
    if isinstance(args, str):
        return [args]
    if hasattr(args, "__iter__"):
        return [str(arg) for arg in args]
    return [str(args)]


def _normalize_options(options: Any) -> Dict[str, Any]:
    """Convert various option formats to dict."""
    if options is None:
        return {}
    if isinstance(options, dict):
        return options
    if hasattr(options, "items"):
        return dict(options.items())
    return {}


def _fix_windows_command(command: str, args: List[str]) -> tuple[str, List[str]]:
    """Fix commands for Windows compatibility."""
    if platform.system() == "Windows":
        if command == "echo":
            return "cmd", ["/c", "echo"] + args
        elif command == "sleep" and len(args) > 0:
            # Convert Unix sleep to Windows ping timeout
            try:
                seconds = float(args[0])
                count = max(1, int(seconds))  # At least 1 ping
                return "ping", ["127.0.0.1", "-n", str(count)]
            except:
                pass
    return command, args


def process_run(
    command: Any,
    args: Any = None,
    options: Any = None,
) -> Dict[str, Any]:
    """Run a process synchronously."""
    try:
        normalized_args = _normalize_args(args)
        normalized_options = _normalize_options(options)
        
        # Fix Windows compatibility
        fixed_command, fixed_args = _fix_windows_command(str(command), normalized_args)
        
        result = _process.run(fixed_command, fixed_args, normalized_options)
        return {
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time": result.execution_time,
            "success": result.success,
        }
    except _process.ProcessError as exc:
        return {
            "type": "error",
            "message": str(exc),
            "error_type": type(exc).__name__,
        }


def process_spawn(
    command: Any,
    args: Any = None,
    options: Any = None,
) -> Dict[str, Any]:
    """Spawn a background process."""
    try:
        normalized_args = _normalize_args(args)
        normalized_options = _normalize_options(options)
        
        # Fix Windows compatibility
        fixed_command, fixed_args = _fix_windows_command(str(command), normalized_args)
        
        handle = _process.spawn(fixed_command, fixed_args, normalized_options)
        # Store handle in a registry for later access
        _PROCESS_REGISTRY[handle.pid] = handle
        return {
            "pid": handle.pid,
            "command": handle.command,
            "args": handle.args,
            "success": True,
        }
    except _process.ProcessError as exc:
        return {
            "type": "error",
            "message": str(exc),
            "error_type": type(exc).__name__,
        }


def process_wait(pid: Any, timeout_ms: Any = None) -> Dict[str, Any]:
    """Wait for a spawned process to complete."""
    try:
        handle = _PROCESS_REGISTRY.get(int(pid))
        if handle is None:
            return {"type": "error", "message": f"Process {pid} not found"}
        
        timeout = None if timeout_ms is None else int(timeout_ms)
        result = _process.wait(handle, timeout)
        
        # Clean up registry entry
        _PROCESS_REGISTRY.pop(int(pid), None)
        
        return {
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time": result.execution_time,
            "success": result.success,
        }
    except _process.ProcessError as exc:
        return {
            "type": "error",
            "message": str(exc),
            "error_type": type(exc).__name__,
        }


def process_terminate(pid: Any, signal_type: Any = "TERM") -> Dict[str, Any]:
    """Terminate a process."""
    try:
        handle = _PROCESS_REGISTRY.get(int(pid))
        if handle is None:
            return {"type": "error", "message": f"Process {pid} not found"}
        
        success = _process.terminate(handle, str(signal_type))
        return {"type": "success", "message": f"Process {pid} terminated"}
    except (ValueError, _process.ProcessError) as exc:
        return {"type": "error", "message": str(exc)}


def process_kill(pid: Any) -> Dict[str, Any]:
    """Kill a process."""
    try:
        handle = _PROCESS_REGISTRY.get(int(pid))
        if handle is None:
            return {"type": "error", "message": f"Process {pid} not found"}
        
        success = _process.kill(handle)
        _PROCESS_REGISTRY.pop(int(pid), None)
        return {"type": "success", "message": f"Process {pid} killed"}
    except (ValueError, _process.ProcessError) as exc:
        return {"type": "error", "message": str(exc)}


def process_status(pid: Any) -> Dict[str, Any]:
    """Get process status."""
    try:
        handle = _PROCESS_REGISTRY.get(int(pid))
        if handle is None:
            return {"type": "error", "message": f"Process {pid} not found"}
        
        status = _process.status(handle)
        return status
    except (ValueError, _process.ProcessError) as exc:
        return {"type": "error", "message": str(exc)}


def process_capture(
    command: Any,
    args: Any = None,
    options: Any = None,
) -> Dict[str, Any]:
    """Capture process output."""
    try:
        normalized_args = _normalize_args(args)
        normalized_options = _normalize_options(options)
        
        # Fix Windows compatibility
        fixed_command, fixed_args = _fix_windows_command(str(command), normalized_args)
        
        result = _process.capture(fixed_command, fixed_args, normalized_options)
        
        # Process.capture returns a dictionary, not a ProcessResult
        if isinstance(result, dict):
            return result
        else:
            # If it returns a ProcessResult object (shouldn't happen but handle it)
            return {
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": result.execution_time,
                "success": result.success,
            }
    except _process.ProcessError as exc:
        return {
            "type": "error",
            "message": str(exc),
            "error_type": type(exc).__name__,
        }


# Global registry to track spawned processes
_PROCESS_REGISTRY: Dict[int, _process.ProcessHandle] = {}


__all__ = [
    "process_run",
    "process_spawn", 
    "process_wait",
    "process_terminate",
    "process_kill",
    "process_status",
    "process_capture",
]