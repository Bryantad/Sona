"""
Sona v0.10.1 - Deterministic Error System
=========================================

Unified error formatting with:
- Stable error codes (E####)
- file:line:col location format
- Source code snippets with carets
- Structured diagnostic objects
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ErrorSeverity(Enum):
    """Severity levels for diagnostics."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class ErrorCode(Enum):
    """
    Stable error codes for Sona diagnostics.
    
    Ranges:
    - E0001-E0099: Syntax/parse errors
    - E0100-E0199: Import/module errors
    - E0200-E0299: Type errors
    - E0300-E0399: Runtime errors
    - E0400-E0499: Name/scope errors
    - E0500-E0599: Value errors
    - E0600-E0699: IO errors
    - W0001-W0099: Warnings
    """
    # Syntax errors (E0001-E0099)
    SYNTAX_ERROR = "E0001"
    UNEXPECTED_TOKEN = "E0002"
    UNCLOSED_STRING = "E0003"
    UNCLOSED_BRACKET = "E0004"
    INVALID_ESCAPE = "E0005"
    MISSING_SEMICOLON = "E0006"
    INVALID_EXPRESSION = "E0007"
    MALFORMED_NUMBER = "E0008"
    RESERVED_WORD = "E0009"
    
    # Import/module errors (E0100-E0199)
    MODULE_NOT_FOUND = "E0100"
    IMPORT_ERROR = "E0101"
    CIRCULAR_IMPORT = "E0102"
    INVALID_MODULE_PATH = "E0103"
    EXPORT_ERROR = "E0104"
    MODULE_LOAD_ERROR = "E0105"
    
    # Type errors (E0200-E0299)
    TYPE_ERROR = "E0200"
    TYPE_MISMATCH = "E0201"
    INVALID_OPERAND = "E0202"
    NOT_CALLABLE = "E0203"
    NOT_ITERABLE = "E0204"
    NOT_SUBSCRIPTABLE = "E0205"
    
    # Runtime errors (E0300-E0399)
    RUNTIME_ERROR = "E0300"
    DIVISION_BY_ZERO = "E0301"
    INDEX_OUT_OF_BOUNDS = "E0302"
    KEY_ERROR = "E0303"
    ASSERTION_FAILED = "E0304"
    RECURSION_LIMIT = "E0305"
    TIMEOUT_ERROR = "E0306"
    
    # Name/scope errors (E0400-E0499)
    NAME_ERROR = "E0400"
    UNDEFINED_VARIABLE = "E0401"
    UNDEFINED_FUNCTION = "E0402"
    ALREADY_DEFINED = "E0403"
    SCOPE_ERROR = "E0404"
    
    # Value errors (E0500-E0599)
    VALUE_ERROR = "E0500"
    INVALID_ARGUMENT = "E0501"
    OUT_OF_RANGE = "E0502"
    EMPTY_SEQUENCE = "E0503"
    
    # IO errors (E0600-E0699)
    IO_ERROR = "E0600"
    FILE_NOT_FOUND = "E0601"
    PERMISSION_DENIED = "E0602"
    ENCODING_ERROR = "E0603"
    
    # Warnings (W0001-W0099)
    UNUSED_VARIABLE = "W0001"
    UNUSED_IMPORT = "W0002"
    DEPRECATED = "W0003"
    SHADOWED_NAME = "W0004"


@dataclass(frozen=True)
class SourceLocation:
    """Precise source location for diagnostics."""
    file: str
    line: int
    column: int
    end_line: int | None = None
    end_column: int | None = None
    
    def __str__(self) -> str:
        """Format as file:line:col."""
        return f"{self.file}:{self.line}:{self.column}"
    
    @classmethod
    def from_node(cls, node: Any, file: str = "<unknown>") -> "SourceLocation":
        """Create location from AST node with line/column attrs."""
        line = getattr(node, "line", 1) or 1
        col = getattr(node, "column", 1) or 1
        end_line = getattr(node, "end_line", None)
        end_col = getattr(node, "end_column", None)
        return cls(file=file, line=line, column=col, end_line=end_line, end_column=end_col)
    
    @classmethod
    def unknown(cls) -> "SourceLocation":
        """Create unknown location placeholder."""
        return cls(file="<unknown>", line=1, column=1)


@dataclass
class Diagnostic:
    """
    Structured diagnostic with all context needed for display.
    
    Attributes:
        code: Stable error code (e.g., E0401)
        severity: error/warning/info/hint
        message: Human-readable message
        location: Source location
        source_line: The actual source line text
        suggestion: Optional fix suggestion
        related: Related diagnostics (e.g., "defined here")
    """
    code: ErrorCode
    severity: ErrorSeverity
    message: str
    location: SourceLocation
    source_line: str = ""
    suggestion: str = ""
    related: list["Diagnostic"] = field(default_factory=list)
    
    def format(self, color: bool = False) -> str:
        """
        Format diagnostic for terminal output.
        
        Example output:
            error[E0401]: undefined variable 'foo'
              --> test.sona:10:5
               |
            10 |     let x = foo + 1;
               |             ^^^ not found in this scope
               |
            help: did you mean 'for'?
        """
        lines: list[str] = []
        
        # Header: severity[code]: message
        sev = self.severity.value
        code = self.code.value
        if color:
            header = f"\033[1;31m{sev}[{code}]\033[0m: {self.message}"
        else:
            header = f"{sev}[{code}]: {self.message}"
        lines.append(header)
        
        # Location pointer
        lines.append(f"  --> {self.location}")
        
        # Source snippet with caret
        if self.source_line:
            line_num = str(self.location.line)
            padding = " " * len(line_num)
            lines.append(f"{padding} |")
            lines.append(f"{line_num} | {self.source_line}")
            
            # Caret line
            caret_padding = " " * (self.location.column - 1)
            caret_width = 1
            if self.location.end_column and self.location.end_column > self.location.column:
                caret_width = self.location.end_column - self.location.column
            carets = "^" * caret_width
            lines.append(f"{padding} | {caret_padding}{carets}")
        
        # Related diagnostics
        for related in self.related:
            lines.append(f"note: {related.message}")
            lines.append(f"  --> {related.location}")
        
        # Suggestion
        if self.suggestion:
            lines.append(f"help: {self.suggestion}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "code": self.code.value,
            "severity": self.severity.value,
            "message": self.message,
            "location": {
                "file": self.location.file,
                "line": self.location.line,
                "column": self.location.column,
                "end_line": self.location.end_line,
                "end_column": self.location.end_column,
            },
            "source_line": self.source_line,
            "suggestion": self.suggestion,
            "related": [r.to_dict() for r in self.related],
        }


class SonaError(Exception):
    """
    Base exception class for all Sona errors with diagnostic support.
    
    All Sona errors carry a Diagnostic for structured reporting.
    """
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.RUNTIME_ERROR,
        location: SourceLocation | None = None,
        source_line: str = "",
        suggestion: str = "",
    ):
        self.diagnostic = Diagnostic(
            code=code,
            severity=ErrorSeverity.ERROR,
            message=message,
            location=location or SourceLocation.unknown(),
            source_line=source_line,
            suggestion=suggestion,
        )
        super().__init__(self.diagnostic.format())
    
    @property
    def code(self) -> str:
        return self.diagnostic.code.value
    
    @property
    def location(self) -> SourceLocation:
        return self.diagnostic.location
    
    def format(self, color: bool = False) -> str:
        return self.diagnostic.format(color=color)


class SonaSyntaxError(SonaError):
    """Syntax/parse error with location."""
    
    def __init__(
        self,
        message: str,
        location: SourceLocation | None = None,
        source_line: str = "",
        suggestion: str = "",
        code: ErrorCode = ErrorCode.SYNTAX_ERROR,
    ):
        super().__init__(message, code, location, source_line, suggestion)


class SonaImportError(SonaError):
    """Import/module error."""
    
    def __init__(
        self,
        message: str,
        module_name: str = "",
        location: SourceLocation | None = None,
        source_line: str = "",
        suggestion: str = "",
    ):
        if not suggestion and module_name:
            suggestion = f"check that module '{module_name}' exists in stdlib or .sona_modules/"
        super().__init__(
            message,
            ErrorCode.MODULE_NOT_FOUND,
            location,
            source_line,
            suggestion,
        )
        self.module_name = module_name


class SonaNameError(SonaError):
    """Undefined name error."""
    
    def __init__(
        self,
        name: str,
        location: SourceLocation | None = None,
        source_line: str = "",
        did_you_mean: str = "",
    ):
        suggestion = f"did you mean '{did_you_mean}'?" if did_you_mean else ""
        super().__init__(
            f"undefined variable '{name}'",
            ErrorCode.UNDEFINED_VARIABLE,
            location,
            source_line,
            suggestion,
        )
        self.name = name


class SonaTypeError(SonaError):
    """Type mismatch error."""
    
    def __init__(
        self,
        message: str,
        expected: str = "",
        got: str = "",
        location: SourceLocation | None = None,
        source_line: str = "",
    ):
        if expected and got:
            message = f"{message}: expected {expected}, got {got}"
        super().__init__(
            message,
            ErrorCode.TYPE_ERROR,
            location,
            source_line,
        )
        self.expected = expected
        self.got = got


class SonaValueError(SonaError):
    """Invalid value error."""
    
    def __init__(
        self,
        message: str,
        location: SourceLocation | None = None,
        source_line: str = "",
        suggestion: str = "",
    ):
        super().__init__(message, ErrorCode.VALUE_ERROR, location, source_line, suggestion)


class SonaIndexError(SonaError):
    """Index out of bounds."""
    
    def __init__(
        self,
        index: int,
        length: int,
        location: SourceLocation | None = None,
        source_line: str = "",
    ):
        super().__init__(
            f"index {index} out of bounds for sequence of length {length}",
            ErrorCode.INDEX_OUT_OF_BOUNDS,
            location,
            source_line,
        )
        self.index = index
        self.length = length


class SonaKeyError(SonaError):
    """Key not found in dict."""
    
    def __init__(
        self,
        key: str,
        location: SourceLocation | None = None,
        source_line: str = "",
        available_keys: list[str] | None = None,
    ):
        suggestion = ""
        if available_keys:
            # Simple similarity check for suggestions
            for k in available_keys:
                if k.startswith(key[:2]) or key in k:
                    suggestion = f"did you mean '{k}'?"
                    break
        super().__init__(
            f"key '{key}' not found",
            ErrorCode.KEY_ERROR,
            location,
            source_line,
            suggestion,
        )
        self.key = key


class SonaDivisionError(SonaError):
    """Division by zero."""
    
    def __init__(
        self,
        location: SourceLocation | None = None,
        source_line: str = "",
    ):
        super().__init__(
            "division by zero",
            ErrorCode.DIVISION_BY_ZERO,
            location,
            source_line,
        )


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def get_source_line(file_path: str | Path, line_num: int) -> str:
    """Read a specific line from a source file."""
    try:
        path = Path(file_path)
        if not path.exists():
            return ""
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        if 1 <= line_num <= len(lines):
            return lines[line_num - 1]
    except Exception:
        pass
    return ""


def format_error_simple(
    message: str,
    file: str = "<unknown>",
    line: int = 1,
    column: int = 1,
    code: str = "E0300",
) -> str:
    """
    Simple one-line error format: file:line:col: error[CODE]: message
    
    Compatible with editors that parse compiler output.
    """
    return f"{file}:{line}:{column}: error[{code}]: {message}"


__all__ = [
    # Enums
    "ErrorSeverity",
    "ErrorCode",
    # Data classes
    "SourceLocation",
    "Diagnostic",
    # Exception classes
    "SonaError",
    "SonaSyntaxError",
    "SonaImportError",
    "SonaNameError",
    "SonaTypeError",
    "SonaValueError",
    "SonaIndexError",
    "SonaKeyError",
    "SonaDivisionError",
    # Utilities
    "get_source_line",
    "format_error_simple",
]
