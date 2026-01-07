#!/usr/bin/env python3
"""
Sona - Direct Program Runner
Executes .sona files without requiring installation
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Version assertion - fail fast if version drifted
try:
    # Add current dir to path first
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from sona import __version__ as SONA_VERSION
    assert SONA_VERSION.startswith(("0.10.",)), f"Expected 0.10.x, got {SONA_VERSION}"
except ImportError:
    print("Warning: Could not verify Sona version (module not in path)")
except AssertionError as e:
    print(f"Version mismatch: {e}")
    sys.exit(1)

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Suppress parser initialization messages by temporarily redirecting stdout
_original_stdout = sys.stdout
_original_stderr = sys.stderr

# Redirect to null during imports
import io as _io
sys.stdout = _io.StringIO()
sys.stderr = _io.StringIO()

from sona.parser_v090 import SonaParserv090
from sona.interpreter import SonaUnifiedInterpreter

# Restore output
sys.stdout = _original_stdout
sys.stderr = _original_stderr


def _read_source(filename):
    if not os.path.exists(filename):
        print(f"Error: File not found: {filename}")
        return None
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:  # utf-8-sig strips BOM
            return f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None


def run_sona_file(filename, interpreter=None, debug=False):
    """Run a Sona program file."""
    source = _read_source(filename)
    if source is None:
        return 1, None, None

    # Execute the entire file as a Sona program
    try:
        interpreter = interpreter or SonaUnifiedInterpreter()
        if debug and hasattr(interpreter, 'enable_debug'):
            interpreter.enable_debug()

        # Check if source contains Sona-specific keywords
        sona_keywords = [
            'let', 'const', 'func', 'import', '//', 'true', 'false',
            'while', 'for', 'if', 'repeat', 'break', 'continue',
            'match', 'case', 'try', 'catch', 'finally'
        ]
        has_sona_syntax = (
            any(keyword in source for keyword in sona_keywords) or
            '{' in source  # C-style braces indicate Sona syntax
        )

        if has_sona_syntax:
            # Parse as complete Sona program
            interpreter.interpret(source, filename=filename)
        else:
            # Fall back to line-by-line Python-like execution
            lines = source.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                interpreter.interpret(line)

    except Exception as e:
        message = None
        if interpreter and hasattr(interpreter, "_explain_exception"):
            try:
                message = interpreter._explain_exception(e, code=source, filename=filename)
            except Exception:
                message = None
        if not message:
            try:
                from sona.utils.error_explainer import explain_error
                message = explain_error(e, filename=filename, source=source)
            except Exception:
                message = str(e)

        print("Runtime error:")
        print(message)
        if debug:
            import traceback
            traceback.print_exc()
        return 1, source, e

    return 0, source, None


def _resolve_cognitive_report(interpreter):
    """Try known report methods on the interpreter, then fall back to monitor."""
    method_candidates = [
        'export_cognitive_report',
        'get_cognitive_report',
        'cognitive_report',
        'build_cognitive_report',
    ]
    for name in method_candidates:
        method = getattr(interpreter, name, None)
        if callable(method):
            return method()

    try:
        builtin = interpreter.memory.get_variable('cognitive_report')
        if callable(builtin):
            return builtin()
    except Exception:
        pass

    monitor = getattr(interpreter, 'cognitive_monitor', None)
    if monitor and hasattr(monitor, 'report'):
        return monitor.report()
    return None


def _build_report_payload(filename, report_data, error):
    meta = {
        "status": "ok" if error is None else "error",
        "filename": filename,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "error": str(error) if error else None,
    }
    if report_data is None:
        report_data = {
            "message": "No cognitive report available",
            "notes": "Interpreter did not expose a report method",
        }
    if not isinstance(report_data, dict):
        report_data = {"value": report_data}
    return {"meta": meta, "report": report_data}


def _render_report_md(payload):
    lines = [
        "# Sona Cognitive Report",
        "",
        f"- File: {payload['meta'].get('filename')}",
        f"- Generated: {payload['meta'].get('generated_at')}",
        f"- Status: {payload['meta'].get('status')}",
    ]
    if payload['meta'].get('error'):
        lines.append(f"- Error: {payload['meta'].get('error')}")
    lines.append("")
    lines.append("## Payload")
    lines.append("")
    json_payload = json.dumps(payload.get('report', {}), indent=2, ensure_ascii=True)
    lines.append("```json")
    lines.append(json_payload)
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def _write_report(out_path, payload, fmt):
    output_dir = os.path.dirname(out_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    if fmt == "md":
        content = _render_report_md(payload)
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(content)
    else:
        with open(out_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=True)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Sona direct runner with cognitive report export"
    )
    parser.add_argument("command_or_file", nargs="?", help="run | report | <file.sona>")
    parser.add_argument("file", nargs="?", help="Sona file path")
    parser.add_argument("--format", choices=["md", "json"], default="json",
                        help="Report output format (report mode only)")
    parser.add_argument("--out", dest="out_path", help="Report output path (report mode only)")
    parser.add_argument(
        "--receipt",
        dest="receipt_path",
        help="Write an execution receipt JSON to this path (run/report modes)",
    )
    parser.add_argument(
        "--receipt-env",
        action="append",
        default=[],
        help="Environment variable key to include in receipt (repeatable)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable interpreter debug mode")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output (reserved)")
    args = parser.parse_args(argv)

    command = args.command_or_file
    filename = args.file

    if command in ("run", "report"):
        return command, filename, args

    if command:
        # Legacy: python run_sona.py file.sona
        return "run", command, args

    return None, None, args


def main(argv):
    command, filename, args = _parse_args(argv)

    if not command or not filename:
        print("Usage:")
        print("  python run_sona.py <file.sona>")
        print("  python run_sona.py run <file.sona>")
        print("  python run_sona.py report <file.sona> --format md|json --out <path>")
        return 1

    start = time.perf_counter()
    interpreter = SonaUnifiedInterpreter(project_root=os.path.dirname(os.path.abspath(filename)) or None)
    exit_code, source, error = run_sona_file(filename, interpreter=interpreter, debug=args.debug)
    duration_ms = int((time.perf_counter() - start) * 1000)

    if getattr(args, "receipt_path", None):
        try:
            from sona.receipts import ReceiptConfig, build_receipt, write_receipt_json

            entry_file = Path(filename)
            project_root = entry_file.resolve().parent
            error_text = None if exit_code == 0 else (str(error) if error is not None else "unknown error")
            cfg = ReceiptConfig(env_allowlist=tuple(getattr(args, "receipt_env", []) or ()))
            receipt = build_receipt(
                sona_version=SONA_VERSION if isinstance(SONA_VERSION, str) else str(SONA_VERSION),
                entry_file=entry_file,
                project_root=project_root,
                argv=list(argv),
                exit_code=exit_code,
                duration_ms=duration_ms,
                error_text=error_text,
                config=cfg,
            )
            write_receipt_json(receipt, Path(args.receipt_path))
        except Exception as exc:
            print(f"[WARN] Failed to write receipt: {exc}", file=sys.stderr)

    if source is None:
        return exit_code

    if command == "report":
        report_data = None
        if interpreter:
            try:
                report_data = _resolve_cognitive_report(interpreter)
            except Exception as exc:
                report_data = None
                error = error or exc

        payload = _build_report_payload(filename, report_data, error)
        out_path = args.out_path
        if not out_path:
            base, _ = os.path.splitext(filename)
            out_path = f"{base}.cognitive_report.{args.format}"

        try:
            _write_report(out_path, payload, args.format)
            print(f"Cognitive report written: {out_path}")
        except Exception as exc:
            print(f"Error writing report: {exc}")
            return 1
        return 0

    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
