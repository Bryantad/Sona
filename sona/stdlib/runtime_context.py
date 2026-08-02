"""Interpreter-bound capabilities for standard-library effects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .errors import StdlibError


_SECRET_NAMES = {
    ".env",
    ".npmrc",
    ".pypirc",
    "credentials",
    "credentials.json",
    "id_rsa",
    "id_ed25519",
}


def _is_secret_name(value: str) -> bool:
    name = value.lower()
    return name in _SECRET_NAMES or name.startswith(".env.")


@dataclass(frozen=True)
class RuntimeCapabilities:
    filesystem_read: bool = True
    filesystem_write: bool = True
    network: bool = True
    console_input: bool = True
    console_output: bool = True


class StdlibRuntimeContext:
    def __init__(self, interpreter=None) -> None:
        self.interpreter = interpreter
        self.project_root = Path(
            getattr(interpreter, "project_root", Path.cwd())
        ).resolve()
        self.safe_mode = bool(getattr(interpreter, "safe_mode", False))
        configured = getattr(interpreter, "stdlib_capabilities", None)
        self.capabilities = configured or RuntimeCapabilities(
            filesystem_read=True,
            filesystem_write=not self.safe_mode,
            network=not self.safe_mode,
            console_input=True,
            console_output=True,
        )

    def require(self, capability: str, operation: str, target: object = "") -> None:
        if bool(getattr(self.capabilities, capability, False)):
            return
        family = "SONA-HTTP-005" if capability == "network" else "SONA-FS-005"
        if capability.startswith("console"):
            family = "SONA-IO-003"
        raise StdlibError(
            family,
            f"runtime capability '{capability}' is disabled",
            operation=operation,
            target=target,
            suggestion="Run without safe mode or grant the explicit runtime capability.",
            is_url=capability == "network",
        )

    def resolve_path(self, value: object, *, write: bool, operation: str) -> Path:
        capability = "filesystem_write" if write else "filesystem_read"
        self.require(capability, operation, value)
        if not isinstance(value, (str, Path)) or "\x00" in str(value):
            raise StdlibError(
                "SONA-FS-001",
                "filesystem path is invalid",
                operation=operation,
                target=value,
                suggestion="Pass a non-empty path without null characters.",
            )
        candidate = Path(value)
        if not self.safe_mode:
            return candidate
        resolved = (
            candidate.resolve()
            if candidate.is_absolute()
            else (self.project_root / candidate).resolve()
        )
        try:
            resolved.relative_to(self.project_root)
        except ValueError as error:
            raise StdlibError(
                "SONA-FS-005",
                "safe-mode path escapes the project root",
                operation=operation,
                target=value,
                suggestion="Use a path inside the current project root.",
                cause=error,
            ) from error
        if not write and any(_is_secret_name(part) for part in resolved.parts):
            raise StdlibError(
                "SONA-FS-005",
                "safe mode denies secret-file reads",
                operation=operation,
                target=value,
                suggestion="Read non-secret project data or run through an approved secret store.",
            )
        return resolved
