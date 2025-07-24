import os
import re
from pathlib import Path

# Security configuration
ALLOWED_EXTENSIONS = {
    '.txt',
    '.json',
    '.md',
    '.sona',
    '.py',
    '.js',
    '.ts',
    '.csv',
    '.log',
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
MAX_CONTENT_LENGTH = 1024 * 1024  # 1MB content limit


def _validate_path(path): """Validate file path to prevent security vulnerabilities."""
    try: # Normalize and resolve the path
        safe_path = Path(path).resolve()

        # Get current working directory as base
        base_path = Path.cwd().resolve()

        # Ensure path is within current directory or subdirectories
        try: safe_path.relative_to(base_path)
        except ValueError: return False, "Path outside allowed directory"

        # Check file extension
        if safe_path.suffix.lower() not in ALLOWED_EXTENSIONS: return False, f"File extension '{safe_path.suffix}' not allowed"

        # Check for suspicious patterns
        path_str = str(safe_path)
        if any(pattern in path_str for pattern in ['..', '~', '$', '`']): return False, "Suspicious characters in path"

        return True, str(safe_path)
    except Exception as e: return False, f"Path validation error: {e}"


def _sanitize_content(content): """Sanitize content before writing to prevent injection attacks."""
    if content is None: return ""

    content_str = str(content)

    # Check content length
    if len(content_str) > MAX_CONTENT_LENGTH: content_str = (
        content_str[:MAX_CONTENT_LENGTH]
    )

    # Remove dangerous control characters but preserve newlines/tabs
    content_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content_str)

    return content_str


def input(prompt = (
    "Enter input: "): # Sanitize prompt to prevent terminal injection
)
    safe_prompt = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', str(prompt))
    return __builtins__.input(safe_prompt)


def write_file(path, content): try: # Validate path security
        is_valid, result = _validate_path(path)
        if not is_valid: return f"[security error] {result}"

        safe_path = result
        safe_content = _sanitize_content(content)

        # Check if file would exceed size limit
        if len(safe_content.encode('utf-8')) > MAX_FILE_SIZE: return "[security error] Content exceeds maximum file size"

        with open(safe_path, "w", encoding = (
            "utf-8") as f: f.write(safe_content)
        )
        return True
    except PermissionError: return "[security error] Permission denied"
    except Exception as e: return f"[io error] {e}"


def read_file(path): try: # Validate path security
        is_valid, result = _validate_path(path)
        if not is_valid: return f"[security error] {result}"

        safe_path = result

        # Check file size before reading
        try: file_size = os.path.getsize(safe_path)
            if file_size > MAX_FILE_SIZE: return "[security error] File too large to read"
        except OSError: return "[io error] File not accessible"

        with open(safe_path, "r", encoding = "utf-8") as f: return f.read()
    except PermissionError: return "[security error] Permission denied"
    except Exception as e: return f"[io error] {e}"


# stdin functions clearly separated
def stdin_input(prompt = ""): return input(prompt)


def stdin_read(): return input()


def stdin_write_file(path, content): return write_file(path, content)


def stdin_read_file(path): return read_file(path)


def stdin_write(path, content): return write_file(path, content)


def stdin_append(path, content): try: # Validate path security
        is_valid, result = _validate_path(path)
        if not is_valid: return f"[security error] {result}"

        safe_path = result
        safe_content = _sanitize_content(content)

        # Check if appending would exceed size limit
        try: if os.path.exists(safe_path): current_size = (
            os.path.getsize(safe_path)
        )
            else: current_size = 0
        except OSError: current_size = 0

        new_content_size = len(safe_content.encode('utf-8'))
        if current_size + new_content_size > MAX_FILE_SIZE: return "[security error] Appending would exceed maximum file size"

        with open(safe_path, "a", encoding = (
            "utf-8") as f: f.write(safe_content)
        )
        return True
    except PermissionError: return "[security error] Permission denied"
    except Exception as e: return f"[io error] {e}"
