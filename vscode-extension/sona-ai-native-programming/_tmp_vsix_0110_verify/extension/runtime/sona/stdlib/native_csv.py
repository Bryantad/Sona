"""Native glue exposing :mod:`sona.stdlib.csv` helpers to Sona."""

from __future__ import annotations

from typing import Any, Dict, List, Callable

from . import csv as _csv


def _normalize_options(options: Any) -> Dict[str, Any]:
    """Convert various option formats to dict."""
    if options is None:
        return {}
    if isinstance(options, dict):
        return options
    if hasattr(options, "items"):
        return dict(options.items())
    return {}


def csv_parse(csv_data: Any, options: Any = None) -> Dict[str, Any]:
    """Parse CSV string into records."""
    try:
        normalized_options = _normalize_options(options)
        result = _csv.parse(str(csv_data), normalized_options)
        
        return {
            "records": result.records,
            "headers": result.headers,
            "row_count": result.row_count,
            "field_count": result.field_count,
            "success": result.success,
        }
    except _csv.CSVError as exc:
        return {
            "type": "error",
            "message": str(exc),
            "error_type": type(exc).__name__,
        }


def csv_parse_file(file_path: Any, options: Any = None) -> Dict[str, Any]:
    """Parse CSV file into records."""
    try:
        normalized_options = _normalize_options(options)
        result = _csv.parse_file(str(file_path), normalized_options)
        
        return {
            "records": result.records,
            "headers": result.headers,
            "row_count": result.row_count,
            "field_count": result.field_count,
            "success": result.success,
        }
    except _csv.CSVError as exc:
        return {
            "type": "error",
            "message": str(exc),
            "error_type": type(exc).__name__,
        }


def csv_stringify(records: Any, options: Any = None) -> Dict[str, Any]:
    """Convert records to CSV string."""
    try:
        if not isinstance(records, list):
            return {
                "type": "error",
                "message": "Records must be a list",
            }
        
        normalized_options = _normalize_options(options)
        csv_data = _csv.stringify(records, normalized_options)
        
        return {
            "csv_data": csv_data,
            "success": True,
        }
    except _csv.CSVError as exc:
        return {
            "type": "error",
            "message": str(exc),
            "error_type": type(exc).__name__,
        }


def csv_write_file(file_path: Any, records: Any, options: Any = None) -> Dict[str, Any]:
    """Write records to CSV file."""
    try:
        if not isinstance(records, list):
            return {
                "type": "error",
                "message": "Records must be a list",
            }
        
        normalized_options = _normalize_options(options)
        success = _csv.write_file(str(file_path), records, normalized_options)
        
        return {
            "success": success,
            "file_path": str(file_path),
        }
    except _csv.CSVError as exc:
        return {
            "type": "error",
            "message": str(exc),
            "error_type": type(exc).__name__,
        }


def csv_validate(csv_data: Any, options: Any = None) -> Dict[str, Any]:
    """Validate CSV structure and return results."""
    try:
        normalized_options = _normalize_options(options)
        result = _csv.validate(str(csv_data), normalized_options)
        
        return {
            "valid": result.valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "row_count": result.row_count,
            "field_count": result.field_count,
        }
    except _csv.CSVError as exc:
        return {
            "type": "error",
            "message": str(exc),
            "error_type": type(exc).__name__,
        }


def csv_stream(file_path: Any, callback: Any, options: Any = None) -> Dict[str, Any]:
    """Stream CSV file for processing large files."""
    try:
        if not callable(callback):
            return {
                "type": "error", 
                "message": "Callback must be callable",
            }
        
        normalized_options = _normalize_options(options)
        processed_count = _csv.stream(str(file_path), callback, normalized_options)
        
        return {
            "processed_count": processed_count,
            "success": True,
        }
    except _csv.CSVError as exc:
        return {
            "type": "error",
            "message": str(exc),
            "error_type": type(exc).__name__,
        }


def csv_extract_fields(records: Any, field_names: Any) -> Dict[str, Any]:
    """Extract specific fields from records."""
    try:
        if not isinstance(records, list):
            return {
                "type": "error",
                "message": "Records must be a list",
            }
        
        if not isinstance(field_names, list):
            # Convert single field name to list
            if isinstance(field_names, str):
                field_names = [field_names]
            else:
                return {
                    "type": "error",
                    "message": "Field names must be a list or string",
                }
        
        extracted = _csv.extract_fields(records, field_names)
        
        return {
            "records": extracted,
            "success": True,
        }
    except _csv.CSVError as exc:
        return {
            "type": "error",
            "message": str(exc),
            "error_type": type(exc).__name__,
        }


def csv_transform(records: Any, transformer: Any, options: Any = None) -> Dict[str, Any]:
    """Transform records using a mapping function."""
    try:
        if not isinstance(records, list):
            return {
                "type": "error",
                "message": "Records must be a list",
            }
        
        if not callable(transformer):
            return {
                "type": "error",
                "message": "Transformer must be callable",
            }
        
        normalized_options = _normalize_options(options)
        transformed = _csv.transform(records, transformer, normalized_options)
        
        return {
            "records": transformed,
            "success": True,
        }
    except _csv.CSVError as exc:
        return {
            "type": "error",
            "message": str(exc),
            "error_type": type(exc).__name__,
        }


__all__ = [
    "csv_parse",
    "csv_parse_file",
    "csv_stringify",
    "csv_write_file", 
    "csv_validate",
    "csv_stream",
    "csv_extract_fields",
    "csv_transform",
]