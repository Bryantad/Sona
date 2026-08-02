"""Structured standard-library failures shared by public adapters."""

from __future__ import annotations

from pathlib import Path
from typing import NoReturn
from urllib.parse import urlsplit, urlunsplit

from sona.errors import ErrorCode, SonaError, SourceLocation


_ERROR_CODES = {
    "SONA-FS-001": ErrorCode.INVALID_ARGUMENT,
    "SONA-FS-002": ErrorCode.FILE_NOT_FOUND,
    "SONA-FS-003": ErrorCode.IO_ERROR,
    "SONA-FS-004": ErrorCode.PERMISSION_DENIED,
    "SONA-FS-005": ErrorCode.IO_ERROR,
    "SONA-FS-006": ErrorCode.ENCODING_ERROR,
    "SONA-HTTP-001": ErrorCode.INVALID_ARGUMENT,
    "SONA-HTTP-002": ErrorCode.TIMEOUT_ERROR,
    "SONA-HTTP-003": ErrorCode.IO_ERROR,
    "SONA-HTTP-004": ErrorCode.OUT_OF_RANGE,
    "SONA-HTTP-005": ErrorCode.IO_ERROR,
    "SONA-JSON-001": ErrorCode.INVALID_ARGUMENT,
    "SONA-JSON-002": ErrorCode.TYPE_ERROR,
    "SONA-JSON-003": ErrorCode.INVALID_ARGUMENT,
    "SONA-IO-001": ErrorCode.IO_ERROR,
    "SONA-IO-002": ErrorCode.IO_ERROR,
    "SONA-IO-003": ErrorCode.IO_ERROR,
    "SONA-TIME-001": ErrorCode.INVALID_ARGUMENT,
    "SONA-TIME-002": ErrorCode.INVALID_ARGUMENT,
    "SONA-TIME-003": ErrorCode.OUT_OF_RANGE,
    "SONA-STDLIB-001": ErrorCode.EXPORT_ERROR,
    "SONA-STDLIB-002": ErrorCode.TYPE_ERROR,
    "SONA-STDLIB-003": ErrorCode.INVALID_MODULE_PATH,
}


def sanitize_target(value: object, *, is_url: bool = False) -> str:
    """Render an operation target without credentials, queries, or content."""

    text = str(value or "")
    if not text:
        return "<unspecified>"
    if is_url:
        try:
            parts = urlsplit(text)
            host = parts.hostname or ""
            if parts.port:
                host = f"{host}:{parts.port}"
            return urlunsplit((parts.scheme, host, parts.path, "", ""))
        except (TypeError, ValueError):
            return "<invalid-url>"
    try:
        return Path(text).as_posix()
    except (TypeError, ValueError):
        return "<invalid-path>"


class StdlibError(SonaError):
    """A Sona diagnostic produced at a standard-library boundary."""

    def __init__(
        self,
        diagnostic_id: str,
        message: str,
        *,
        operation: str,
        target: object = "",
        suggestion: str,
        location: SourceLocation | None = None,
        is_url: bool = False,
        cause: BaseException | None = None,
    ) -> None:
        safe_target = sanitize_target(target, is_url=is_url)
        rendered = f"{message} (operation={operation}, target={safe_target})"
        super().__init__(
            rendered,
            code=_ERROR_CODES.get(diagnostic_id, ErrorCode.RUNTIME_ERROR),
            location=location,
            suggestion=suggestion,
            diagnostic_id=diagnostic_id,
        )
        self.operation = operation
        self.target = safe_target
        self.cause_type = type(cause).__name__ if cause is not None else None


def raise_fs_error(operation: str, target: object, error: BaseException) -> NoReturn:
    if isinstance(error, FileNotFoundError):
        diagnostic_id = "SONA-FS-002"
        message = "filesystem path was not found"
        suggestion = "Verify the path and run the operation again."
    elif isinstance(error, PermissionError):
        diagnostic_id = "SONA-FS-004"
        message = "filesystem permission was denied"
        suggestion = "Verify that the current process has the required access."
    elif isinstance(error, (UnicodeError, LookupError)):
        diagnostic_id = "SONA-FS-006"
        message = "filesystem text encoding failed"
        suggestion = "Use UTF-8 text or a supported compatibility encoding."
    elif isinstance(error, (TypeError, ValueError)):
        diagnostic_id = "SONA-FS-001"
        message = "filesystem argument is invalid"
        suggestion = "Pass a valid path and arguments for this operation."
    else:
        diagnostic_id = "SONA-FS-003"
        message = "filesystem operation failed"
        suggestion = "Check the path, available space, and operating-system error."
    raise StdlibError(
        diagnostic_id,
        message,
        operation=operation,
        target=target,
        suggestion=suggestion,
        cause=error,
    ) from error
