#!/usr/bin/env python3
"""
CSV processing backend for Sona stdlib.
Provides comprehensive CSV parsing, writing, and manipulation capabilities.
"""

import csv
import io
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, Iterator, Callable
import tempfile


# === Exception Classes ===

class CSVError(Exception):
    """Base exception for CSV-related errors."""
    pass


class CSVParseError(CSVError):
    """Exception raised when CSV parsing fails."""
    pass


class CSVWriteError(CSVError):
    """Exception raised when CSV writing fails."""
    pass


class CSVValidationError(CSVError):
    """Exception raised when CSV validation fails."""
    pass


# === Data Classes ===

@dataclass
class CSVParseResult:
    """Result of CSV parsing operation."""
    records: List[Dict[str, Any]]
    headers: Optional[List[str]]
    row_count: int
    field_count: int
    success: bool = True


@dataclass
class CSVValidationResult:
    """Result of CSV validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    row_count: int
    field_count: int


# === Core CSV Functions ===

def parse(
    csv_data: str,
    options: Optional[Dict[str, Any]] = None,
) -> CSVParseResult:
    """Parse CSV string into records."""
    options = options or {}
    
    # Extract parsing options
    delimiter = options.get("delimiter", ",")
    quote_char = options.get("quote_char", '"')
    escape_char = options.get("escape_char", None)
    has_headers = options.get("headers", True)
    skip_blank_lines = options.get("skip_blank_lines", True)
    encoding = options.get("encoding", "utf-8")
    
    try:
        # Create CSV reader
        csv_input = io.StringIO(csv_data)
        reader = csv.reader(
            csv_input,
            delimiter=delimiter,
            quotechar=quote_char,
            escapechar=escape_char,
            skipinitialspace=True,
        )
        
        records = []
        headers = None
        row_count = 0
        field_count = 0
        
        for row_idx, row in enumerate(reader):
            # Skip blank lines if requested
            if skip_blank_lines and not any(cell.strip() for cell in row):
                continue
            
            # Handle headers
            if row_idx == 0 and has_headers:
                headers = [str(cell).strip() for cell in row]
                field_count = len(headers)
                continue
            
            # Process data rows
            if headers:
                # Use headers as keys
                if len(row) != len(headers):
                    # Pad or trim row to match headers
                    if len(row) < len(headers):
                        row.extend([''] * (len(headers) - len(row)))
                    else:
                        row = row[:len(headers)]
                
                record = {headers[i]: str(cell).strip() for i, cell in enumerate(row)}
            else:
                # Use index-based keys
                record = {str(i): str(cell).strip() for i, cell in enumerate(row)}
                if not field_count:
                    field_count = len(record)
            
            records.append(record)
            row_count += 1
        
        return CSVParseResult(
            records=records,
            headers=headers,
            row_count=row_count,
            field_count=field_count,
            success=True,
        )
        
    except Exception as exc:
        raise CSVParseError(f"CSV parsing failed: {exc}") from exc


def parse_file(
    file_path: str,
    options: Optional[Dict[str, Any]] = None,
) -> CSVParseResult:
    """Parse CSV file into records."""
    options = options or {}
    encoding = options.get("encoding", "utf-8")
    
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            csv_data = file.read()
        
        return parse(csv_data, options)
        
    except FileNotFoundError as exc:
        raise CSVError(f"CSV file not found: {file_path}") from exc
    except PermissionError as exc:
        raise CSVError(f"Permission denied reading CSV file: {file_path}") from exc
    except Exception as exc:
        raise CSVParseError(f"Failed to parse CSV file {file_path}: {exc}") from exc


def stringify(
    records: List[Dict[str, Any]],
    options: Optional[Dict[str, Any]] = None,
) -> str:
    """Convert records to CSV string."""
    options = options or {}
    
    if not records:
        return ""
    
    # Extract formatting options
    delimiter = options.get("delimiter", ",")
    quote_char = options.get("quote_char", '"')
    escape_char = options.get("escape_char", None)
    include_headers = options.get("headers", True)
    line_terminator = options.get("line_terminator", "\n")
    
    try:
        # Create CSV writer
        output = io.StringIO()
        
        # Determine field names from first record
        if isinstance(records[0], dict):
            fieldnames = list(records[0].keys())
        else:
            raise CSVError("Records must be dictionaries")
        
        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            delimiter=delimiter,
            quotechar=quote_char,
            escapechar=escape_char,
            lineterminator=line_terminator,
            quoting=csv.QUOTE_MINIMAL,
        )
        
        # Write headers if requested
        if include_headers:
            writer.writeheader()
        
        # Write records
        for record in records:
            # Ensure all values are strings
            cleaned_record = {
                key: str(value) if value is not None else ""
                for key, value in record.items()
            }
            writer.writerow(cleaned_record)
        
        return output.getvalue()
        
    except Exception as exc:
        raise CSVWriteError(f"CSV stringify failed: {exc}") from exc


def write_file(
    file_path: str,
    records: List[Dict[str, Any]],
    options: Optional[Dict[str, Any]] = None,
) -> bool:
    """Write records to CSV file."""
    options = options or {}
    encoding = options.get("encoding", "utf-8")
    
    try:
        csv_data = stringify(records, options)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding=encoding) as file:
            file.write(csv_data)
        
        return True
        
    except Exception as exc:
        raise CSVWriteError(f"Failed to write CSV file {file_path}: {exc}") from exc


def validate(
    csv_data: str,
    options: Optional[Dict[str, Any]] = None,
) -> CSVValidationResult:
    """Validate CSV structure and return detailed results."""
    options = options or {}
    errors = []
    warnings = []
    
    try:
        # Try parsing to detect structural issues
        result = parse(csv_data, options)
        
        # Validate consistency
        if result.records:
            expected_field_count = len(result.records[0])
            
            for i, record in enumerate(result.records):
                if len(record) != expected_field_count:
                    warnings.append(
                        f"Row {i + 1}: Field count mismatch "
                        f"(expected {expected_field_count}, got {len(record)})"
                    )
            
            # Check for empty values
            for i, record in enumerate(result.records):
                empty_fields = [k for k, v in record.items() if not v.strip()]
                if empty_fields:
                    warnings.append(
                        f"Row {i + 1}: Empty fields: {', '.join(empty_fields)}"
                    )
        
        return CSVValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            row_count=result.row_count,
            field_count=result.field_count,
        )
        
    except CSVParseError as exc:
        errors.append(str(exc))
        return CSVValidationResult(
            valid=False,
            errors=errors,
            warnings=warnings,
            row_count=0,
            field_count=0,
        )


def stream(
    file_path: str,
    callback: Callable[[Dict[str, Any], int], Any],
    options: Optional[Dict[str, Any]] = None,
) -> int:
    """Stream CSV file processing for large files."""
    options = options or {}
    encoding = options.get("encoding", "utf-8")
    delimiter = options.get("delimiter", ",")
    quote_char = options.get("quote_char", '"')
    has_headers = options.get("headers", True)
    
    processed_count = 0
    
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            reader = csv.reader(file, delimiter=delimiter, quotechar=quote_char)
            
            headers = None
            if has_headers:
                headers = next(reader, None)
                if not headers:
                    return 0
            
            for row_idx, row in enumerate(reader):
                # Create record
                if headers:
                    record = {
                        headers[i] if i < len(headers) else f"field_{i}": 
                        str(cell).strip() 
                        for i, cell in enumerate(row)
                    }
                else:
                    record = {str(i): str(cell).strip() for i, cell in enumerate(row)}
                
                # Call callback function
                try:
                    callback(record, row_idx + (1 if has_headers else 0))
                    processed_count += 1
                except Exception as callback_exc:
                    raise CSVError(f"Callback failed on row {row_idx}: {callback_exc}")
        
        return processed_count
        
    except Exception as exc:
        raise CSVError(f"CSV streaming failed for {file_path}: {exc}") from exc


def extract_fields(
    records: List[Dict[str, Any]],
    field_names: List[str],
) -> List[Dict[str, Any]]:
    """Extract specific fields from records."""
    if not records:
        return []
    
    extracted = []
    
    for record in records:
        extracted_record = {}
        for field_name in field_names:
            extracted_record[field_name] = record.get(field_name, "")
        extracted.append(extracted_record)
    
    return extracted


def transform(
    records: List[Dict[str, Any]],
    transformer: Callable[[Dict[str, Any]], Dict[str, Any]],
    options: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Transform records using a mapping function."""
    if not records:
        return []
    
    transformed = []
    
    for i, record in enumerate(records):
        try:
            transformed_record = transformer(record)
            if not isinstance(transformed_record, dict):
                raise CSVError(f"Transformer must return a dictionary for record {i}")
            transformed.append(transformed_record)
        except Exception as exc:
            raise CSVError(f"Transform failed on record {i}: {exc}") from exc
    
    return transformed


# === Utility Functions ===

def infer_delimiter(csv_data: str) -> str:
    """Infer the most likely delimiter from CSV data."""
    sample_size = min(1024, len(csv_data))
    sample = csv_data[:sample_size]
    
    # Common delimiters to test
    delimiters = [',', ';', '\t', '|']
    delimiter_counts = {}
    
    for delimiter in delimiters:
        delimiter_counts[delimiter] = sample.count(delimiter)
    
    # Return delimiter with highest count
    best_delimiter = max(delimiter_counts, key=delimiter_counts.get)
    return best_delimiter if delimiter_counts[best_delimiter] > 0 else ','


__all__ = [
    "CSVError",
    "CSVParseError", 
    "CSVWriteError",
    "CSVValidationError",
    "CSVParseResult",
    "CSVValidationResult", 
    "parse",
    "parse_file",
    "stringify",
    "write_file",
    "validate",
    "stream",
    "extract_fields",
    "transform",
    "infer_delimiter",
]