"""
Sona v0.15.6 Command Line Interface with AI Integration

Enhanced CLI with profile, benchmark, suggest, and explain commands
powered by GPT-2 and cognitive assistance features.
"""

import argparse
import difflib
import os
import shutil
import subprocess
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from .native_launcher import NativeProofLaunchError, probe_native_version

# Import type configuration
from .type_config import configure_types, get_type_config, get_type_logger

# Win UTF-8 guard - safer version that doesn't interfere with I/O operations
if sys.platform == "win32":  # pragma: no cover - platform specific
    try:
        import ctypes  # type: ignore
        # Set console code page and reconfigure stdout/stderr to UTF-8.
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        # Ensure Python stdout/stderr can emit UTF-8 safely.
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Import Sona core components
# Lazy imports: avoid importing heavy interpreter (and lark)
# unless actually executing Sona code
default_interpreter = None  # type: ignore


@dataclass
class ExecutionStats:
    result: object | None = None
    statements: int = 0
    python_blocks: int = 0
    python_invocations: int = 0
    duration_ms: float = 0.0
    interpreter_name: str = ""
    interpreter_variant: str = "core"
    fallback_reason: str | None = None
    interpreter_hint: str | None = None
    safe_mode: bool = False
    file_path: str | None = None


INTERPRETER_STATUS = {
    "variant": "core",
    "fallback_reason": None,
    "hint": None,
    "message": None,
}
_INTERPRETER_NOTICE_SENT = False


DEMO_PROGRAMS = {
    "showcase": """let banner = ">>> Welcome to the Sona CLI demo";
print(banner);

let highlights = ["restore points", "micro-chunks", "local AI"];
print("Highlights list:");
print(highlights);

let metrics = {"chunks": 3, "fallback": "core-safe"};
print("Runtime metrics:");
print(metrics);

let totals = [1, 2, 3, 4];
print("Totals:");
print(totals);
let total_count = len(totals);
print("Total count:");
print(total_count);

import math;
import time;
print("sqrt(49) = ");
print(math.math_sqrt(49));
print("Clock tick:");
print(time.time_now());

print("Demo complete!");
""",
    "insights": """let pipeline = ["plan", "build", "ship"];
print("Pipeline steps:");
print(pipeline);

let stats = {"executions": len(pipeline), "success": true};
print("Stats summary:");
print(stats);

import string;
print("Upper: " + string.string_upper("sona"));
print("Lower: " + string.string_lower("SONA"));

import time;
print("Now:");
print(time.time_now());

print("Insights demo complete.");
""",
}

KNOWN_COMMANDS = {
    'run',
    'profile',
    'benchmark',
    'suggest',
    'explain',
    'info',
    'ai-plan',
    'ai-review',
    'probe',
    'doctor',
    'build-info',
    'help',
    'version',
    'repl',
    'check',
    'format',
    'transpile',
    'keys',
    'lock',
    'verify',
    'demo',
    'ai-model',
    'ai-mode',
    'setup',
    'perf-log',
    'ai',
    'model',
    'govern',
    'guardian',
    'guide',
    'proof',
    'why',
    'fix',
    'focus',
}


_NATIVE_PROOF_BINARY_ENV = "SONA_NATIVE_BINARY"
_NATIVE_PROOF_DELEGATION_GUARD = "_SONA_NATIVE_PROOF_DELEGATED"
_PYTHON_PROOF_ACTIONS = {"verify", "inspect"}


def _resolve_native_proof_binary(environment: dict[str, str] | None = None) -> Path:
    """Resolve only an explicitly configured or PATH-installed Native Core."""

    environment = os.environ if environment is None else environment
    configured = environment.get(_NATIVE_PROOF_BINARY_ENV)
    if configured is not None:
        expanded = os.path.expandvars(os.path.expanduser(configured.strip()))
        if not expanded:
            raise NativeProofLaunchError(
                "The configured Native Core executable is unavailable.",
                f"Set {_NATIVE_PROOF_BINARY_ENV} to the Native Core executable "
                "or remove it to use sona-native from PATH.",
            )
        try:
            candidate = Path(expanded).resolve(strict=True)
        except (OSError, ValueError, RuntimeError) as exc:
            raise NativeProofLaunchError(
                "The configured Native Core executable is unavailable.",
                f"Set {_NATIVE_PROOF_BINARY_ENV} to a regular Native Core "
                "executable file.",
            ) from exc
        if not candidate.is_file():
            raise NativeProofLaunchError(
                "The configured Native Core executable is unavailable.",
                f"Set {_NATIVE_PROOF_BINARY_ENV} to a regular Native Core "
                "executable file.",
            )
    else:
        resolved = shutil.which("sona-native", path=environment.get("PATH", ""))
        if resolved is None:
            raise NativeProofLaunchError(
                "Native Core is required to create a Proof Mode receipt.",
                "Install sona-native on PATH or set "
                f"{_NATIVE_PROOF_BINARY_ENV} to the extracted Native Core executable.",
            )
        try:
            candidate = Path(resolved).resolve(strict=True)
        except (OSError, ValueError, RuntimeError) as exc:
            raise NativeProofLaunchError(
                "The PATH-selected Native Core executable is unavailable.",
                "Check sona-native on PATH or set SONA_NATIVE_BINARY.",
            ) from exc

    launcher = Path(sys.argv[0])
    try:
        if launcher.is_file() and os.path.samefile(candidate, launcher):
            raise NativeProofLaunchError(
                "The resolved Native Core executable points back to the "
                "Python Sona launcher.",
                "Install sona-native on PATH or set "
                f"{_NATIVE_PROOF_BINARY_ENV} to the standalone Native Core executable.",
            )
    except OSError:
        pass
    return candidate


def _proof_generation_arguments(argv: list[str]) -> list[str] | None:
    """Return Native Proof arguments while reserving Python receipt actions."""

    if len(argv) < 3 or argv[1] != "proof":
        return None
    first = argv[2]
    if first in _PYTHON_PROOF_ACTIONS or first in {"-h", "--help"}:
        return None
    return argv[2:]


def _delegate_native_proof(
    arguments: list[str],
    environment: dict[str, str] | None = None,
) -> int:
    """Run the sole Native Proof producer with inherited process streams."""

    environment = dict(os.environ if environment is None else environment)
    if environment.get(_NATIVE_PROOF_DELEGATION_GUARD) == "1":
        safe_error(
            "SonaProofLaunchError [SONA-NATIVE-LAUNCH-005]: "
            "Native Proof delegation returned to the Python CLI."
        )
        safe_error(
            f"  hint: Set {_NATIVE_PROOF_BINARY_ENV} to the standalone "
            "Native Core executable."
        )
        return 1
    try:
        binary = _resolve_native_proof_binary(environment)
        probe_native_version(binary, SONA_VERSION, environment)
    except NativeProofLaunchError as exc:
        safe_error(f"SonaProofLaunchError [{exc.diagnostic_id}]: {exc.message}")
        safe_error(f"  hint: {exc.hint}")
        return 1

    environment[_NATIVE_PROOF_DELEGATION_GUARD] = "1"
    try:
        process = subprocess.run(
            [str(binary), "proof", *arguments],
            env=environment,
            check=False,
            shell=False,
        )
    except OSError:
        safe_error(
            "SonaProofLaunchError [SONA-NATIVE-LAUNCH-001]: "
            "Native Core could not be started safely."
        )
        safe_error(
            "  hint: Check the sona-native installation or "
            f"{_NATIVE_PROOF_BINARY_ENV} configuration."
        )
        return 1
    return int(process.returncode)


def _load_default_interpreter(project_root: str | Path | None = None):
    """Instantiate the preferred interpreter with graceful fallback."""
    try:
        from sona.interpreter import SonaInterpreter
        _update_interpreter_status("cognitive", message=None, fallback_reason=None, hint=None)
        return SonaInterpreter(project_root=project_root)
    except Exception as core_error:  # pragma: no cover - defensive
        fallback_reason = _summarize_interpreter_error(core_error)
        raise RuntimeError(
            f"Interpreter unavailable: {fallback_reason}"
        ) from core_error


def _to_str_safe(x):
    """Force any value to clean string - final safety net for AI results."""
    try:
        if x is None:
            return ""
        if isinstance(x, str):
            return x
        # Dataclass or SDK object? Try to unwrap known shapes
        if hasattr(x, "content"):
            return str(x.content)
        if isinstance(x, dict):
            return str(x.get("content") or x)
        return str(x)
    except Exception as e:
        return f"[format-error] {e}"


def safe_print(*args, **kwargs):
    """Print function that handles Unicode gracefully on Windows cp1252."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: encode to ASCII with replacement for unsupported chars
        text = " ".join(str(a) for a in args)
        # Replace common emoji with ASCII equivalents
        replacements = {
            '\U0001f680': '[ROCKET]',  # rocket
            '\u2705': '[OK]',          # check mark
            '\u274c': '[ERROR]',       # cross mark
            '\U0001f916': '[AI]',      # robot
            '\U0001f4d6': '[INFO]',    # open book
            '\U0001f50d': '[DEBUG]',   # magnifying glass
            '\U0001f504': '[INFO]',    # refresh
            '\u26a0\ufe0f': '[WARN]',  # warning
            '\u26a0': '[WARN]',        # warning
            '\U0001f44b': '[BYE]',     # wave
            '\U0001f3e5': '[INFO]',    # hospital
            '\U0001f4ca': '[INFO]',    # chart
            '\u2139\ufe0f': '[INFO]',  # info
            '\u2139': '[INFO]',        # info
        }
        for emoji, replacement in replacements.items():
            text = text.replace(emoji, replacement)
        # Final fallback: replace any remaining non-ASCII
        text = text.encode('ascii', 'replace').decode('ascii')
        print(text, **kwargs)


def safe_error(*args, **kwargs):
    """Print a user-facing error message to stderr."""
    kwargs.setdefault("file", sys.stderr)
    safe_print(*args, **kwargs)


def _update_interpreter_status(
    variant: str,
    *,
    fallback_reason: str | None = None,
    hint: str | None = None,
    message: str | None = None,
    announce: bool = False,
):
    INTERPRETER_STATUS.update(
        {
            "variant": variant,
            "fallback_reason": fallback_reason,
            "hint": hint,
            "message": message,
        }
    )
    if announce and message:
        _announce_interpreter_once()


def _announce_interpreter_once():
    global _INTERPRETER_NOTICE_SENT
    if _INTERPRETER_NOTICE_SENT:
        return
    note = INTERPRETER_STATUS.get("message")
    if not note:
        return
    safe_print(note)
    hint = INTERPRETER_STATUS.get("hint")
    if hint:
        safe_print(f"        {hint}")
    _INTERPRETER_NOTICE_SENT = True


def _summarize_interpreter_error(error: Exception) -> str:
    text = str(error).strip()
    if "No module named" in text:
        missing = text.split("No module named", 1)[1].strip(" :'.\"")
        return f"missing module {missing}"
    if text:
        return text.split('\n', 1)[0]
    return error.__class__.__name__


def _snapshot_interpreter_status() -> dict:
    return dict(INTERPRETER_STATUS)


def _format_duration(ms: float) -> str:
    if ms >= 1000:
        return f"{ms / 1000:.2f}s"
    return f"{ms:.1f}ms"


def _preview_value(value: object, limit: int = 80) -> str:
    text = _to_str_safe(value).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


def _build_capability_banner() -> str | None:
    entries = []
    flags = None
    try:
        from .flags import get_flags  # type: ignore

        flags = get_flags()
    except Exception:
        flags = None

    for label, attr, env_var in [
        ("cache", "enable_cache", "SONA_ENABLE_CACHE"),
        ("batch", "enable_batching", "SONA_ENABLE_BATCH"),
        ("breaker", "enable_breaker", "SONA_ENABLE_BREAKER"),
        ("ai", "enable_capabilities", "SONA_ENABLE_CAPABILITIES"),
        ("perf", "perf_logs", "SONA_PERF_LOGS"),
    ]:
        state = None
        if flags and hasattr(flags, attr):
            value = getattr(flags, attr)
            if isinstance(value, bool):
                state = 'on' if value else 'off'
            elif value not in (None, ""):
                state = value
        if state is None:
            env_value = os.getenv(env_var)
            if env_value is None:
                state = 'off'
            else:
                normalized = env_value.strip().lower()
                if normalized in {'1', 'true', 'on', 'yes'}:
                    state = 'on'
                elif normalized in {'0', 'false', 'off', 'no'}:
                    state = 'off'
                else:
                    state = env_value
        entries.append(f"{label}:{state}")

    if not entries:
        return None
    return "capabilities " + " | ".join(entries)


def _print_structured_summary(
    stats: ExecutionStats,
    file_label: str,
    type_mode: str | None,
    type_stats: dict,
    *,
    header: str = '[Run Summary]'
):
    if not stats:
        return

    type_mode = type_mode or 'off'
    safe_print(f"\n{header}")
    lines = [
        f"file: {file_label}",
        f"interpreter: {stats.interpreter_variant} ({stats.interpreter_name or 'unknown'})",
        f"safe mode: {'on' if stats.safe_mode else 'off'}",
        f"duration: {_format_duration(stats.duration_ms)}",
        f"statements: {stats.statements} (python blocks: {stats.python_blocks}, python exports: {stats.python_invocations})",
    ]

    if stats.fallback_reason:
        lines.append(f"fallback: {stats.fallback_reason}")
    if stats.interpreter_hint and stats.fallback_reason:
        lines.append(f"hint: {stats.interpreter_hint}")

    errors = type_stats.get('errors', 0)
    warnings = type_stats.get('warnings', 0)
    lines.append(f"types: {type_mode} (errors={errors}, warnings={warnings})")

    cap_line = _build_capability_banner()
    if cap_line:
        lines.append(cap_line)

    if stats.result is not None:
        lines.append(f"last result: {_preview_value(stats.result)}")

    for entry in lines:
        safe_print(f"  {entry}")


def _emit_type_logger_summary(logger, args) -> dict:
    stats = {'errors': 0, 'warnings': 0}
    if not logger or not hasattr(args, 'types') or getattr(args, 'types', None) in (None, 'off'):
        return stats

    stats.update(getattr(logger, '_stats', {}))
    types_log = getattr(args, 'types_log', 'all')

    should_show = types_log == 'all'
    if types_log == 'errors':
        should_show = (stats.get('errors', 0) > 0) or (stats.get('warnings', 0) > 0)

    if should_show:
        summary = logger.get_summary()
        print(summary, file=sys.stderr)

    return stats


ERROR_MODES = {'explain', 'trace', 'both'}
KNOWN_STDLIB_MODULES = (
    "crypto",
    "csv",
    "date",
    "env",
    "fs",
    "graph",
    "hashing",
    "io",
    "json",
    "jwt",
    "math",
    "matrix",
    "memory",
    "password",
    "path",
    "permissions",
    "queue",
    "random",
    "search",
    "secrets",
    "sort",
    "stack",
    "statistics",
    "string",
    "time",
    "uuid",
)


def _resolve_error_mode(args) -> str:
    mode = getattr(args, 'errors', None)
    if mode in ERROR_MODES:
        return mode
    return 'explain'


def _select_trace_exception(exc: Exception) -> Exception:
    try:
        from .interpreter import SonaRuntimeError
    except Exception:
        SonaRuntimeError = None  # type: ignore

    if SonaRuntimeError and isinstance(exc, SonaRuntimeError):
        return exc.__cause__ or exc
    return exc


def _render_execution_error(
    exc: Exception,
    *,
    mode: str,
    debug: bool,
    filename: str | None = None,
    source: str | None = None,
) -> None:
    if mode == 'trace':
        trace_exc = _select_trace_exception(exc)
        traceback.print_exception(type(trace_exc), trace_exc, trace_exc.__traceback__)
        return

    _render_user_diagnostic(exc, filename=filename, source=source)

    if mode == 'both' or debug:
        trace_exc = _select_trace_exception(exc)
        traceback.print_exception(type(trace_exc), trace_exc, trace_exc.__traceback__)


def _render_user_diagnostic(
    exc: Exception,
    *,
    filename: str | None = None,
    source: str | None = None,
) -> None:
    """Render compact, stable CLI diagnostics without changing interpreter behavior."""
    diagnostic = getattr(exc, "diagnostic", None)
    if diagnostic is not None:
        diagnostic_id = getattr(diagnostic, "diagnostic_id", None)
        code = getattr(getattr(diagnostic, "code", None), "value", None)
        prefix = f"{diagnostic_id}: " if diagnostic_id else ""
        code_text = f"error[{code}]" if code else "error"
        safe_error(f"{type(exc).__name__}: {prefix}{code_text}: {diagnostic.message}")
        location = getattr(diagnostic, "location", None)
        if location is not None:
            safe_error(f"  at {location}")
        if getattr(diagnostic, "suggestion", ""):
            safe_error(f"  hint: {diagnostic.suggestion}")
        return

    cause = _select_trace_exception(exc)
    message = str(cause) or str(exc) or "Unexpected error"
    header, hint = _classify_user_error(cause, message)
    summary = _diagnostic_summary(header, message)
    safe_error(f"{header}: {summary}")

    location = _extract_cli_location(cause, message, filename, source)
    if location:
        safe_error(f"  at {location}")

    if hint:
        safe_error(f"  hint: {hint}")


def _first_nonempty_line(value: str) -> str:
    for line in value.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _diagnostic_summary(header: str, message: str) -> str:
    if header == "SonaImportError":
        module_name = _extract_module_name(message)
        if module_name:
            return f"module '{module_name}' not found"
    return _first_nonempty_line(message) or "Unexpected error"


def _classify_user_error(exc: Exception, message: str) -> tuple[str, str | None]:
    text = message.lower()
    if isinstance(exc, ImportError) or "module file not found" in text or "module not found" in text or "no module named" in text:
        return "SonaImportError", _module_hint(message)
    if isinstance(exc, FileNotFoundError) or "file not found" in text:
        return "SonaFileError", "check the path and run the command again."
    if isinstance(exc, SyntaxError) or "syntax error" in text or "unexpected token" in text:
        return "SonaSyntaxError", "check punctuation, quotes, and balanced brackets."
    if isinstance(exc, NameError) or "is not defined" in text or "used before it was defined" in text:
        return "SonaNameError", "declare it with let before using it."
    if isinstance(exc, TypeError) or "not callable" in text or "expected" in text:
        return "SonaTypeError", "check the value and arguments used in this call."
    return "SonaRuntimeError", None


def _module_hint(message: str) -> str:
    module_name = _extract_module_name(message)
    if module_name:
        matches = difflib.get_close_matches(module_name, KNOWN_STDLIB_MODULES, n=1, cutoff=0.72)
        if matches:
            return f"did you mean '{matches[0]}'?"
    return "check the module name and that it is available."


def _extract_module_name(message: str) -> str | None:
    import re

    patterns = [
        r"Module file not found:\s*(.+?)(?:\n|$)",
        r"module ['\"]([^'\"]+)['\"] not found",
        r"No module named ['\"]([^'\"]+)['\"]",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if not match:
            continue
        value = match.group(1).strip()
        if "\\" in value or "/" in value:
            value = Path(value).stem
        if value:
            return value
    return None


def _extract_cli_location(
    exc: Exception,
    message: str,
    filename: str | None,
    source: str | None,
) -> str | None:
    line = getattr(exc, "lineno", None)
    column = getattr(exc, "offset", None)
    if line is None:
        import re

        match = re.search(r"line\s+(\d+)(?:,\s*column\s+(\d+))?", message, re.IGNORECASE)
        if match:
            try:
                line = int(match.group(1))
            except ValueError:
                line = None
            if match.group(2):
                try:
                    column = int(match.group(2))
                except ValueError:
                    column = None
    if line is None:
        return None

    location = filename if filename else "<unknown>"
    location = f"{location}:{line}"
    if column:
        location = f"{location}:{column}"
    if source:
        lines = source.splitlines()
        if 0 < line <= len(lines):
            location = f"{location}: {lines[line - 1].strip()}"
    return location


def read_text_safe(path: str) -> str:
    """Robust text loader with multi-encoding fallback.

    Tries common encodings; last resort returns replacement-decoded UTF-8.
    """
    p = Path(path)
    for enc in ("utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            return p.read_text(encoding=enc)
        except UnicodeError:
            continue
        except FileNotFoundError:
            raise
        except Exception:
            continue
    return p.read_text(encoding="utf-8", errors="replace")


def _run_python_script(path: Path, args: list[str], *, debug: bool = False) -> int:
    """Execute a Python script using the current interpreter."""
    import runpy

    original_argv = sys.argv[:]
    sys.argv = [str(path)] + list(args)
    try:
        runpy.run_path(str(path), run_name="__main__")
        return 0
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        safe_error(code)
        return 1
    except Exception as exc:
        safe_error(f"SonaRuntimeError: Python execution error: {exc}")
        if debug:
            import traceback

            traceback.print_exc()
        return 2
    finally:
        sys.argv = original_argv


def _handle_direct_file_invocation(argv: list[str]) -> int | None:
    """Handle 'sona <file>' before argparse so direct file usage works."""
    if len(argv) < 2:
        return None
    candidate = argv[1]
    if candidate.startswith('-'):
        return None
    if candidate in KNOWN_COMMANDS:
        return None
    path = Path(candidate)
    if not path.exists():
        if path.suffix.lower() in {'.sona', '.smod'}:
            safe_error(f"SonaFileError: file not found: {candidate}")
            safe_error("  hint: check the path and run the command again.")
            return 1
        return None

    if path.suffix.lower() == '.py':
        return _run_python_script(path, argv[2:])

    if len(argv) > 2:
        safe_error("SonaUsageError: extra arguments for direct file execution.")
        safe_error("  hint: use 'sona run <file.sona>' for flags/options.")
        return 1

    class DirectArgs:
        file = str(path)
        safe = False
        debug = False
        types = None
        types_log = 'all'
        summary = False
        compatibility = 'auto'

    return handle_run_command(DirectArgs())


def execute_sona(
    code: str,
    safe_mode: bool = False,
    file_path: str | None = None,
    debug: bool = False,
    compatibility_mode: str = "auto",
) -> any:
    """Execute Sona code using the default interpreter."""
    # Each file execution receives isolated state. The REPL owns its persistent
    # interpreter separately.
    project_root = Path(file_path).resolve().parent if file_path else Path.cwd()
    interpreter = _load_default_interpreter(project_root=project_root)
    interpreter.compatibility_mode = compatibility_mode
    interpreter.safe_mode = bool(safe_mode)
    if safe_mode:
        interpreter.maximum_call_depth = 128
        interpreter.maximum_loop_iterations = 100_000
        interpreter.maximum_execution_time_ms = 30_000
        interpreter.maximum_output_bytes = 1_048_576
    stats = ExecutionStats(safe_mode=safe_mode, file_path=file_path)

    # Support embedded Python functions with @check_types decorator.
    from sona.type_system.runtime_checker import TypeCheckAbort, check_types

    python_blocks, remaining_lines = _extract_python_blocks(code)
    stats.python_blocks = len(python_blocks)

    exec_globals = {'check_types': check_types}

    # Track current file for exclusion logic
    try:
        get_type_config().set_current_file(file_path)
    except Exception:
        pass

    # Toggle interpreter debug mode if supported.
    try:
        if debug:
            interpreter.enable_debug()
        else:
            interpreter.disable_debug()
    except Exception:
        pass

    for python_block in python_blocks:
        try:
            compiled = compile(python_block, file_path or '<embedded>', 'exec')
            exec(compiled, exec_globals, exec_globals)
        except TypeCheckAbort:
            raise
        except Exception as e:
            raise RuntimeError(f"Python block execution error: {e}") from e

    python_exports = _register_python_exports(exec_globals, interpreter)

    remaining_code = '\n'.join(remaining_lines)
    executed_statements = sum(
        1
        for line in remaining_lines
        if line.strip() and not line.strip().startswith('#')
    )
    result = None
    start_time = perf_counter()

    if remaining_code.strip():
        try:
            result = interpreter.interpret(
                remaining_code,
                filename=file_path or '<string>',
            )
            if result is not None:
                result = _to_str_safe(result)
        except TypeCheckAbort:
            raise
        except Exception as e:
            try:
                from .errors import SonaError
            except Exception:
                SonaError = None  # type: ignore
            if SonaError and isinstance(e, SonaError):
                raise
            raise RuntimeError(f"Interpretation error: {e}") from e

    end_time = perf_counter()
    stats.result = result
    stats.statements = executed_statements
    stats.python_invocations = python_exports
    stats.duration_ms = max(0.0, (end_time - start_time) * 1000)
    stats.interpreter_name = interpreter.__class__.__name__
    snapshot = _snapshot_interpreter_status()
    stats.interpreter_variant = snapshot.get('variant') or stats.interpreter_name
    stats.fallback_reason = snapshot.get('fallback_reason')
    stats.interpreter_hint = snapshot.get('hint')

    return stats


def _extract_python_blocks(code: str):
    """Enhanced Python block extraction with multi-decorator support."""
    lines = code.split('\n')
    python_blocks = []
    remaining_lines = []
    i = 0

    while i < len(lines):
        line = lines[i].rstrip('\n')
        stripped = line.strip()

        # Look for @check_types decorator
        if stripped.startswith('@check_types'):
            # Start collecting a function block
            block_lines = []
            decorators_end = i

            # Collect all decorators (including @check_types)
            while decorators_end < len(lines):
                dec_line = lines[decorators_end].strip()
                if dec_line.startswith('@'):
                    block_lines.append(lines[decorators_end])
                    decorators_end += 1
                elif dec_line == '':
                    # Empty line between decorators and function
                    block_lines.append(lines[decorators_end])
                    decorators_end += 1
                else:
                    break

            # Find the function definition
            func_start = decorators_end
            if (func_start < len(lines) and
                    lines[func_start].strip().startswith('def ')):
                block_lines.append(lines[func_start])

                # Collect function body with proper indentation detection
                func_line = lines[func_start]
                func_indent = len(func_line) - len(func_line.lstrip())
                body_end = func_start + 1

                # Find end of function body
                while body_end < len(lines):
                    body_line = lines[body_end]
                    body_stripped = body_line.strip()

                    if body_stripped == '':
                        # Empty line - include and continue
                        block_lines.append(body_line)
                        body_end += 1
                        continue

                    body_indent = len(body_line) - len(body_line.lstrip())

                    # If indented more than function def, it's function body
                    if body_indent > func_indent:
                        block_lines.append(body_line)
                        body_end += 1
                        continue

                    # If same or less indentation, function body is complete
                    # Unless it's another @check_types (multi-function block)
                    if body_stripped.startswith('@check_types'):
                        # Continue with next decorated function in same block
                        break
                    else:
                        # End of Python block
                        break

                python_blocks.append('\n'.join(block_lines))
                # Preserve line numbers by keeping blank placeholders.
                remaining_lines.extend([''] * (body_end - i))
                i = body_end
                continue

        # Not a Python block line - add to remaining
        remaining_lines.append(line)
        i += 1

    return python_blocks, remaining_lines


def _register_python_exports(exec_globals: dict, interpreter) -> int:
    """Expose Python symbols from embedded blocks to the Sona interpreter."""
    exported = 0
    for name, value in exec_globals.items():
        if name.startswith('__'):
            continue
        if name in {'check_types'}:
            continue
        try:
            if hasattr(interpreter, 'has_variable') and interpreter.has_variable(name):
                continue
        except Exception:
            pass
        try:
            if hasattr(interpreter, 'set_variable'):
                interpreter.set_variable(name, value, global_scope=True)
                exported += 1
            elif hasattr(interpreter, 'memory'):
                interpreter.memory.set_variable(name, value, global_scope=True)
                exported += 1
        except Exception:
            continue
    return exported


ENHANCED_COMMANDS = None  # lazy-loaded mapping


# Version information
SONA_VERSION = "0.15.6"
AI_FEATURES_VERSION = "1.0.0"
DEFAULT_OFFLINE_MODEL = "qwen2.5-coder:7b"


class SonaArgumentParser(argparse.ArgumentParser):
    """Argument parser that keeps CLI usage failures in Sona's error shape."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        safe_error(f"SonaUsageError: {message}")
        safe_error("  hint: use 'sona --help' for available commands.")
        raise SystemExit(2)


def _ai_disabled_msg(cmd: str) -> int:
    """Standard graceful degrade message for AI capability commands."""
    print(
        f"AI features for '{cmd}' are disabled. "
        "Enable flag SONA_ENABLE_CAPABILITIES=1 or install extras: "
        "pip install 'sona-lang[ai]'."
    )
    return 0


def create_argument_parser() -> argparse.ArgumentParser:
    """Create the main argument parser for Sona CLI"""
    parser = SonaArgumentParser(
        prog='sona',
        description=(
            'Sona v0.15.6 - simple programs with optional execution evidence'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Start with an ordinary run (no Proof Mode receipt):\n"
            "  sona run hello.sona\n"
            "  sona hello.sona\n\n"
            "Create and verify Native execution evidence:\n"
            "  sona proof hello.sona --receipt hello.sproof --engine native\n"
            "  sona proof verify hello.sproof\n"
            "  sona proof inspect hello.sproof\n\n"
            "Add project-local policy and a trusted baseline:\n"
            "  sona guardian init --project-root .\n"
            "  sona guardian check --project-root .\n"
            "  sona guardian explain --project-root .\n\n"
            "Guide: https://github.com/Bryantad/Sona/tree/main/docs/getting-started"
        )
    )

    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'Sona {SONA_VERSION}'
    )

    parser.add_argument(
        '--types-status',
        action='store_true',
        help='Show effective type checking configuration and exit',
    )

    # Main command subparsers
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
    )

    from .guide.models import DENSITIES, MODES, STYLES
    from .guide.profile import FAMILIARITY_VALUES
    from .learning_cli import add_learning_parsers

    add_learning_parsers(subparsers)

    why_parser = subparsers.add_parser(
        'why', help='Explain a diagnostic using the offline Sona Guide catalog',
    )
    why_parser.add_argument('diagnostic_id', help='Exact identifier printed by Sona')
    why_parser.add_argument('--mode', choices=MODES, default=None, help='Override the project guidance mode')
    why_parser.add_argument('--style', choices=STYLES, default=None, help='Override the project explanation style')
    why_parser.add_argument(
        '--project-root',
        default='.',
        help='Project root used to read .sona/learning.json',
    )
    why_parser.add_argument(
        '--no-profile',
        action='store_true',
        help='Ignore the project-local Sona Guide learning profile',
    )
    why_parser.add_argument('--json', action='store_true', help='Emit the Guide schema-1 response')

    fix_parser = subparsers.add_parser(
        'fix',
        help='Preview or apply deterministic Sona Guide source edits',
    )
    fix_parser.add_argument('file', help='Sona source file to inspect')
    fix_parser.add_argument(
        '--rule',
        choices=['auto', 'undefined-name', 'stdlib-api-migration'],
        default='auto',
        help='Fix rule to run; auto uses every safe rule with available context',
    )
    fix_parser.add_argument('--diagnostic-json', help='Path to a canonical diagnostic JSON file, or - for stdin')
    fix_parser.add_argument('--diagnostic-id', help='Canonical diagnostic identifier for source-backed fixes')
    fix_parser.add_argument('--name', help='Undefined name reported by the diagnostic')
    fix_parser.add_argument('--message', help='Canonical diagnostic message')
    fix_parser.add_argument('--line', type=int, help='One-based diagnostic start line')
    fix_parser.add_argument('--column', type=int, help='One-based diagnostic start column')
    fix_parser.add_argument('--end-line', type=int, help='One-based diagnostic end line')
    fix_parser.add_argument('--end-column', type=int, help='One-based diagnostic end column')
    fix_parser.add_argument('--legacy-code', help='Legacy E#### code, when available')
    fix_parser.add_argument('--apply', action='store_true', help='Write the previewed edits if stale checks pass')
    fix_parser.add_argument(
        '--project-root',
        default='.',
        help='Project root used for successful fix learning updates',
    )
    fix_parser.add_argument(
        '--no-profile-update',
        action='store_true',
        help='Do not update .sona/learning.json after a successful deterministic fix',
    )
    fix_parser.add_argument('--json', action='store_true', help='Emit the Guide fix schema-1 response')

    focus_parser = subparsers.add_parser(
        'focus',
        help='Group canonical diagnostics with deterministic Focus Mode rules',
    )
    focus_parser.add_argument('file', nargs='?', help='Sona source file to check')
    focus_parser.add_argument(
        '--density',
        choices=DENSITIES,
        default=None,
        help='Diagnostic density for presentation',
    )
    focus_parser.add_argument(
        '--diagnostics-json',
        help='Path to canonical diagnostic JSON, or - for stdin',
    )
    focus_parser.add_argument(
        '--project-root',
        default='.',
        help='Project root used to read .sona/learning.json',
    )
    focus_parser.add_argument(
        '--no-profile',
        action='store_true',
        help='Ignore the project-local Sona Guide learning profile',
    )
    focus_parser.add_argument('--json', action='store_true', help='Emit the Focus schema-1 response')
    focus_quiet = focus_parser.add_mutually_exclusive_group()
    focus_quiet.add_argument('--quiet', action='store_true', default=None)
    focus_quiet.add_argument('--no-quiet', action='store_false', dest='quiet')

    guide_parser = subparsers.add_parser(
        'guide',
        help='Manage deterministic Sona Guide preferences and learning state',
    )
    guide_sub = guide_parser.add_subparsers(
        dest='guide_cmd',
        help='Sona Guide commands',
    )
    guide_request_parser = guide_sub.add_parser(
        'request', help='Read an offline Guide schema-1 JSON request from stdin',
    )
    guide_request_parser.add_argument('--json', action='store_true', help='Emit shared editor/CLI JSON')
    guide_request_parser.add_argument('--project-root', default='.')
    guide_request_parser.add_argument('--no-profile', action='store_true')
    for fact_kind in ('proof', 'guardian'):
        fact_parser = guide_sub.add_parser(fact_kind, help='Explain checked facts without changing evidence or project state')
        if fact_kind == 'proof':
            fact_parser.add_argument('receipt')
        fact_parser.add_argument('--project-root', default='.')
        fact_parser.add_argument('--no-profile', action='store_true')
        fact_parser.add_argument('--mode', choices=MODES, default=None)
        fact_parser.add_argument('--style', choices=STYLES, default=None)
        fact_parser.add_argument('--json', action='store_true')
    guide_profile_common = argparse.ArgumentParser(add_help=False)
    guide_profile_common.add_argument(
        '--project-root',
        default='.',
        help='Project root containing .sona/learning.json',
    )
    guide_profile_common.add_argument(
        '--json',
        action='store_true',
        help='Emit the Guide profile schema-1 response',
    )
    guide_profile_parser = guide_sub.add_parser(
        'profile',
        parents=[guide_profile_common],
        help='Show or update the project-local Sona Guide profile',
    )
    guide_profile_sub = guide_profile_parser.add_subparsers(
        dest='profile_cmd',
        help='Profile actions',
    )
    guide_profile_sub.add_parser(
        'show',
        parents=[guide_profile_common],
        help='Show the effective Sona Guide profile',
    )
    guide_profile_set = guide_profile_sub.add_parser(
        'set',
        parents=[guide_profile_common],
        help='Set explicit guidance preferences',
    )
    guide_profile_set.add_argument('--mode', choices=MODES, dest='guidance_mode')
    guide_profile_set.add_argument('--density', choices=DENSITIES, dest='diagnostic_density')
    guide_profile_set.add_argument('--style', choices=STYLES, dest='explanation_style')
    quiet_group = guide_profile_set.add_mutually_exclusive_group()
    quiet_group.add_argument('--quiet', action='store_true', default=None, dest='quiet')
    quiet_group.add_argument('--no-quiet', action='store_false', dest='quiet')
    guide_profile_sub.add_parser(
        'reset',
        parents=[guide_profile_common],
        help='Reset the Sona Guide profile to documented defaults',
    )
    guide_profile_learn = guide_profile_sub.add_parser(
        'learn',
        parents=[guide_profile_common],
        help='Record explicit concept familiarity',
    )
    guide_profile_learn.add_argument('concept', help='Lowercase concept identifier, such as variables')
    guide_profile_learn.add_argument(
        '--familiarity',
        choices=FAMILIARITY_VALUES,
        default='learning',
        help='Concept familiarity to record',
    )

    # Run command (default)
    run_parser = subparsers.add_parser(
        'run',
        help='Execute a Sona file without creating a Proof Mode receipt',
    )
    run_parser.add_argument('file', help='Sona file to execute')
    run_parser.add_argument('--json', action='store_true', help='Return execution streams and structured diagnostics as JSON')
    run_parser.add_argument(
        '--safe',
        action='store_true',
        help='Enable safe mode',
    )
    run_parser.add_argument(
        '--compatibility', choices=['auto', 'sona', 'python'], default='auto',
        help='Frontend compatibility mode; auto preserves legacy fallback behavior',
    )
    run_parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output',
    )
    run_parser.add_argument(
        '--errors',
        choices=['explain', 'trace', 'both'],
        default='explain',
        help='Error output mode (explain|trace|both)',
    )
    run_parser.add_argument(
        '--types',
        choices=['off', 'warn', 'on'],
        help='Type checking mode (off|warn|on). Overrides SONA_TYPES env var',
    )
    run_parser.add_argument(
        '--types-log',
        choices=['all', 'errors', 'silent'],
        default='all',
        help='Control type checking log verbosity (all|errors|silent)',
    )
    run_parser.add_argument(
        '--summary',
        action='store_true',
        help='Print a structured execution summary after completion',
    )
    run_parser.add_argument(
        '--receipt',
        dest='receipt_path',
        help='Write an execution receipt JSON to this path',
    )
    run_parser.add_argument(
        '--receipt-env',
        action='append',
        default=[],
        help='Environment variable key to include in receipt (repeatable)',
    )

    demo_parser = subparsers.add_parser(
        'demo',
        help='Run a built-in feature showcase program'
    )
    demo_parser.add_argument(
        '--scenario',
        choices=sorted(DEMO_PROGRAMS.keys()),
        default='showcase',
        help='Choose which curated scenario to run',
    )
    demo_parser.add_argument(
        '--summary',
        action='store_true',
        help='Print a structured summary when the demo finishes',
    )
    demo_parser.add_argument(
        '--types',
        choices=['off', 'warn', 'on'],
        help='Optional type checking mode for demo execution',
    )
    demo_parser.add_argument(
        '--types-log',
        choices=['all', 'errors', 'silent'],
        default='errors',
        help='Control type logging verbosity for demos',
    )

    # Profile command
    profile_parser = subparsers.add_parser(
        'profile',
        help='Profile Sona code execution'
    )
    profile_parser.add_argument('file', help='Sona file to profile')
    profile_parser.add_argument(
        '--ai-insights',
        action='store_true',
        help='Generate AI-powered insights',
    )

    # Benchmark command
    benchmark_parser = subparsers.add_parser(
        'benchmark',
        help='Benchmark Sona performance',
    )
    benchmark_parser.add_argument('file', help='Sona file to benchmark')
    benchmark_parser.add_argument(
        '--compare-versions',
        action='store_true',
        help='Compare with previous versions',
    )
    benchmark_parser.add_argument(
        '--ai-recommendations',
        action='store_true',
        help='Get AI performance recommendations',
    )

    # Suggest command
    suggest_parser = subparsers.add_parser(
        'suggest',
        help='Get AI code suggestions',
    )
    suggest_parser.add_argument('file', help='Sona file to analyze')
    suggest_parser.add_argument(
        '--cognitive',
        action='store_true',
        help='Focus on cognitive programming suggestions',
    )
    suggest_parser.add_argument(
        '--performance',
        action='store_true',
        help='Focus on performance suggestions',
    )
    suggest_parser.add_argument(
        '--accessibility',
        action='store_true',
        help='Focus on accessibility suggestions',
    )
    suggest_parser.add_argument(
        '--ai',
        action='store_true',
        help='Use the configured AI backend; default is fast local analysis',
    )
    suggest_parser.add_argument('--format', choices=['text', 'json'], default='text')
    suggest_parser.add_argument('--json', action='store_true', help=argparse.SUPPRESS)
    suggest_parser.add_argument('--provider', default=None)
    suggest_parser.add_argument('--model', default=None)

    # Explain command
    explain_parser = subparsers.add_parser(
        'explain',
        help='Get AI code explanations',
    )
    explain_parser.add_argument('file', help='Sona file to explain')
    explain_parser.add_argument(
        '--style',
        choices=['simple', 'detailed', 'cognitive'],
        default='simple',
        help='Explanation style',
    )
    explain_parser.add_argument('--format', choices=['text', 'json'], default='text')
    explain_parser.add_argument('--json', action='store_true', help=argparse.SUPPRESS)
    explain_parser.add_argument('--provider', default=None)
    explain_parser.add_argument('--model', default=None)
    explain_parser.add_argument(
        '--ai',
        action='store_true',
        help='Use the configured AI backend; default is fast local analysis',
    )

    # Info command
    info_parser = subparsers.add_parser('info', help='Show system information')

    # Check command
    check_parser = subparsers.add_parser('check', help='Check Sona syntax')
    check_parser.add_argument('file', help='Sona file to check')
    check_parser.add_argument('--format', choices=['text', 'json'], default='text')
    check_parser.add_argument('--json', action='store_true', help=argparse.SUPPRESS)
    # Setup command
    setup_parser = subparsers.add_parser(
        'setup',
        help='One-time setup commands',
    )
    setup_sub = setup_parser.add_subparsers(
        dest='setup_cmd',
        help='Setup targets',
    )
    # Setup -> Azure
    setup_azure_parser = setup_sub.add_parser(
        'azure',
        help='Configure Azure OpenAI for Sona',
    )
    setup_azure_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Do not write any files',
    )
    setup_azure_parser.add_argument(
        '--workspace',
        help='Workspace directory to update .env',
        default=None,
    )
    setup_azure_parser.add_argument(
        '--manual',
        action='store_true',
        help='Manual setup without Azure CLI',
    )
    setup_azure_parser.add_argument(
        '--write-env-secret', action='store_true',
        help='Explicitly permit writing the provider key to workspace .env',
    )
    # Setup -> Manual
    setup_manual_parser = setup_sub.add_parser(
        'manual',
        help='Manual Azure OpenAI setup (no Azure CLI)',
    )
    setup_manual_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Do not write any files',
    )
    setup_manual_parser.add_argument(
        '--workspace',
        help='Workspace directory to update .env',
        default=None,
    )
    setup_manual_parser.add_argument(
        '--write-env-secret', action='store_true',
        help='Explicitly permit writing the provider key to workspace .env',
    )

    # Package command (v0.10 platform bridge)
    pkg_parser = subparsers.add_parser(
        'pkg',
        help='Package/project helpers (manifest + local modules)',
    )
    pkg_sub = pkg_parser.add_subparsers(
        dest='pkg_cmd',
        help='Package commands',
    )
    pkg_init = pkg_sub.add_parser(
        'init',
        help='Create sona.json manifest in current directory',
    )
    pkg_init.add_argument(
        '--name',
        default=None,
        help='Project name (defaults to folder name)',
    )
    pkg_init.add_argument(
        '--version',
        default=SONA_VERSION,
        help='Project version (defaults to Sona version)',
    )

    # Format command
    format_parser = subparsers.add_parser('format', help='Format Sona code')
    format_parser.add_argument('file', help='Sona file to format')

    # Transpile command
    transpile_parser = subparsers.add_parser(
        'transpile',
        help='Transpile Sona to Python',
    )
    transpile_parser.add_argument('file', help='Sona file to transpile')
    transpile_parser.add_argument('--output', help='Output file path')
    transpile_parser.add_argument(
        '--core-only',
        action='store_true',
        help='Emit core syntax only (skip cognitive/AI helpers)',
    )

    # REPL command
    repl_parser = subparsers.add_parser(
        'repl',
        help='Start interactive REPL',
    )
    repl_parser.add_argument(
        '--ai',
        action='store_true',
        help='Enable AI assistance',
    )
    info_parser.add_argument(
        '--ai-status',
        action='store_true',
        help='Show AI feature status',
    )

    # Lock command (deterministic builds)
    lock_parser = subparsers.add_parser(
        'lock',
        help='Generate sona.lock.json for deterministic builds'
    )
    lock_parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify existing lockfile instead of generating new one'
    )

    # Verify command (lockfile validation)
    verify_parser = subparsers.add_parser(
        'verify',
        help='Verify sona.lock.json integrity and workspace state'
    )

    # Keys management command group
    keys_parser = subparsers.add_parser(
        'keys',
        help='Manage API credentials (secure storage)'
    )
    keys_sub = keys_parser.add_subparsers(
        dest='keys_cmd',
        help='Key operations'
    )

    # keys set <service> --api-key ... [--endpoint ...]
    keys_set = keys_sub.add_parser('set', help='Set credentials for a service')
    keys_set.add_argument(
        'service',
        choices=['openai', 'azure', 'anthropic', 'google'],
        help='Service name'
    )
    keys_set.add_argument(
        '--api-key', dest='api_key',
        help='API key or secret token'
    )
    keys_set.add_argument('--endpoint', help='Custom API endpoint / base URL')

    # keys get <service>
    keys_get = keys_sub.add_parser(
        'get',
        help='Get masked credentials for a service'
    )
    keys_get.add_argument(
        'service',
        choices=['openai', 'azure', 'anthropic', 'google'],
        help='Service name'
    )

    # keys list
    keys_sub.add_parser('list', help='List stored services and masked keys')

    # keys migrate (one-time)
    keys_sub.add_parser(
        'migrate',
        help='Migrate plaintext .env / legacy credentials to secure storage'
    )

    # keys rotate <service> [--key api_key]
    keys_rotate = keys_sub.add_parser(
        'rotate',
        help='Rotate (generate new) secret for a service key'
    )
    keys_rotate.add_argument(
        'service',
        choices=['openai', 'azure', 'anthropic', 'google'],
        help='Service name'
    )
    keys_rotate.add_argument(
        '--key', default='api_key',
        help='Key name to rotate (default: api_key)'
    )

    # ai-plan command (capabilities)
    plan_parser = subparsers.add_parser(
        'ai-plan',
        help='Generate deterministic plan JSON (capabilities feature)'
    )
    plan_parser.add_argument('goal', help='Goal / objective text')
    plan_parser.add_argument(
        '--context', default='', help='Optional context text'
    )

    # ai-review command (capabilities)
    review_parser = subparsers.add_parser(
        'ai-review',
        help='Review artifact text against criteria'
    )
    review_parser.add_argument('file', help='Artifact file to review')
    review_parser.add_argument(
        '--criteria', default='quality,clarity', help='Comma list'
    )

    # AI model management command
    ai_model_parser = subparsers.add_parser(
        'ai-model', help='Manage local Ollama models for offline AI'
    )
    ai_model_sub = ai_model_parser.add_subparsers(
        dest='ai_model_cmd',
        help='AI model operations',
    )
    ai_status_parser = ai_model_sub.add_parser(
        'status', help='Check whether the required model is installed'
    )
    ai_status_parser.add_argument(
        '--model',
        default=DEFAULT_OFFLINE_MODEL,
        help=f"Model name to inspect (default: {DEFAULT_OFFLINE_MODEL})",
    )
    ai_pull_parser = ai_model_sub.add_parser(
        'pull', help='Download the required model via Ollama'
    )
    ai_pull_parser.add_argument(
        '--model',
        default=DEFAULT_OFFLINE_MODEL,
        help=f"Model name to download (default: {DEFAULT_OFFLINE_MODEL})",
    )

    # Canonical developer-intelligence task API.
    ai_parser = subparsers.add_parser('ai', help='Experimental structured developer-intelligence tasks')
    ai_sub = ai_parser.add_subparsers(dest='ai_cmd')
    ai_task = ai_sub.add_parser('task', help='Run a preview-first developer task')
    ai_task.add_argument('--type', dest='task_type', choices=[
        'complete', 'explain', 'diagnose', 'suggest', 'refactor', 'edit',
        'generate_tests', 'review', 'fix', 'document',
    ])
    ai_task.add_argument('--instruction', default='')
    ai_task.add_argument('--file', dest='files', action='append', default=[])
    ai_task.add_argument('--provider', default=None)
    ai_task.add_argument('--model', default=None)
    ai_task.add_argument('--request', default=None, help="Read a schema-1 request from a path or '-' for stdin")
    ai_task.add_argument('--format', choices=['text', 'json'], default='json')
    ai_task.add_argument('--no-receipt', action='store_true')

    model_parser = subparsers.add_parser('model', help='Inspect and register developer-intelligence models')
    model_sub = model_parser.add_subparsers(dest='model_cmd')
    model_sub.add_parser('list', help='List registered models')
    model_inspect = model_sub.add_parser('inspect', help='Inspect a model descriptor')
    model_inspect.add_argument('model_id')
    model_register = model_sub.add_parser('register', help='Register a schema-1 model manifest')
    model_register.add_argument('manifest')
    model_register.add_argument('--scope', choices=['workspace', 'user'], default='workspace')
    model_test = model_sub.add_parser('test', help='Validate model configuration')
    model_test.add_argument('model_id')
    model_health = model_sub.add_parser('health', help='Show model registry health')
    model_health.add_argument('--format', choices=['text', 'json'], default='json')

    govern_parser = subparsers.add_parser('govern', help='Validate and explain governance policy')
    govern_sub = govern_parser.add_subparsers(dest='govern_cmd')
    govern_validate = govern_sub.add_parser('validate')
    govern_validate.add_argument('--policy', default=None)
    for govern_name in ('check', 'explain'):
        govern_action = govern_sub.add_parser(govern_name)
        govern_action.add_argument('--task', required=True)
        govern_action.add_argument('--provider', default=None)
        govern_action.add_argument('--model', default=None)
        govern_action.add_argument('--capability', default=None)
        govern_action.add_argument('--format', choices=['text', 'json'], default='json')
    govern_audit = govern_sub.add_parser('audit')
    govern_audit.add_argument('--last', type=int, default=20)
    govern_sub.add_parser('policy')

    proof_parser = subparsers.add_parser(
        'proof',
        help='Generate, inspect, and verify Proof Mode receipts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        usage=(
            'sona proof <program.sona|program.sbc> --receipt <new-receipt> '
            '[Native Proof options]\n'
            '       sona proof verify <receipt> [--json]\n'
            '       sona proof inspect <receipt> [--json]'
        ),
        description=(
            'Generate a receipt with Native Core using privacy-conscious '
            'execution evidence, or verify and inspect an existing receipt. '
            'Generation never falls back to Python.'
        ),
        epilog=(
            'Generation:\n'
            '  sona proof app.sona --receipt new.sproof --engine native\n'
            '  --allow-fs-read       Grant filesystem reads\n'
            '  --allow-fs-write      Grant filesystem writes\n'
            '  --allow-network       Grant network policy\n'
            '  --guardian-root PATH  Bind to an initialized Guardian project\n'
            '  --summary             Print a human-readable save summary\n\n'
            'Receipts are never overwritten. The schema-1 self-hash checks '\
            'integrity and consistency; it does not authenticate an author, '\
            'runtime host, or signer.'
        ),
    )
    proof_sub = proof_parser.add_subparsers(dest='proof_cmd')
    proof_help = {
        'verify': 'Validate receipt structure, canonical bytes, and self-hash',
        'inspect': 'Verify first, then show recorded runtime and effect facts',
    }
    for name in ('verify', 'inspect'):
        sub = proof_sub.add_parser(name, help=proof_help[name])
        sub.add_argument('receipt', help='Path to a Proof Mode receipt')
        sub.add_argument(
            '--json', action='store_true', help='Print machine-readable JSON'
        )

    # Canonical Guardian name; the existing `guard` family remains compatible.
    guardian_parser = subparsers.add_parser(
        'guardian',
        help='Apply project-local policy and baseline checks around trusted workflows',
        description=(
            'Guardian manages local capability policy and a reviewed project '
            'baseline. Start with init, then use check and explain before '
            'running a Guardian-bound Proof Mode workflow.'
        ),
        epilog=(
            'Beginner path:\n'
            '  sona guardian init --project-root .\n'
            '  sona guardian check --project-root .\n'
            '  sona guardian explain --project-root .\n\n'
            'check and explain are read-only. Commands that change project '\
            'state require their documented apply and approval controls.'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    guardian_sub = guardian_parser.add_subparsers(dest='guard_cmd')
    guardian_help = {
        'init': 'Create policy, trusted baseline, snapshot, and local audit state',
        'status': 'Show initialization and circuit-breaker state',
        'verify': 'Compare current project state with the trusted baseline',
        'check': 'Read-only readiness check for policy, baseline, drift, and Proof Mode',
        'explain': 'Explain capability decisions, warnings, and the next safe action',
        'diff': 'Show the compact difference from the trusted baseline',
        'doctor': 'Diagnose Guardian configuration and readiness',
        'graph': 'Build the project relationship graph',
        'audit': 'Read recent Guardian audit records',
    }
    for name in ('init', 'status', 'verify', 'check', 'explain', 'diff', 'doctor', 'graph', 'audit'):
        sub = guardian_sub.add_parser(name, help=guardian_help[name])
        sub.add_argument('--project-root', default=None)
        if name in {'init', 'check', 'explain'}:
            sub.add_argument(
                '--format', choices=['auto', 'text', 'json'], default='auto',
                help='Output format; auto uses text on a terminal and JSON when redirected',
            )
        if name == 'verify':
            sub.add_argument('--run-validation', action='store_true')
        if name == 'audit':
            sub.add_argument('--limit', type=int, default=50)
    guardian_heal = guardian_sub.add_parser(
        'heal', help='Preview or apply governed quarantine and recovery'
    )
    guardian_heal.add_argument('--project-root', default=None)
    guardian_heal.add_argument('--apply', action='store_true')
    guardian_heal.add_argument('--approve', action='store_true')
    guardian_repair = guardian_sub.add_parser(
        'repair', help='Compatibility name for the governed healing workflow'
    )
    guardian_repair.add_argument('--project-root', default=None)
    guardian_repair.add_argument('--apply', action='store_true')
    guardian_repair.add_argument('--approve', action='store_true')
    guardian_rollback = guardian_sub.add_parser(
        'rollback', help='Preview or restore a selected trusted snapshot'
    )
    guardian_rollback.add_argument('--project-root', default=None)
    guardian_rollback.add_argument('--snapshot-id', default=None)
    guardian_rollback.add_argument('--dry-run', action='store_true')
    guardian_rollback.add_argument('--apply', action='store_true')
    guardian_rollback.add_argument('--approve', action='store_true')
    guardian_history = guardian_sub.add_parser(
        'history', help='Read recent Guardian audit history'
    )
    guardian_history.add_argument('--project-root', default=None)
    guardian_history.add_argument('--limit', type=int, default=50)
    guardian_snapshot = guardian_sub.add_parser(
        'snapshot', help='Create a new project snapshot'
    )
    guardian_snapshot.add_argument('--project-root', default=None)
    guardian_snapshot.add_argument('--name', default=None)
    guardian_quarantine = guardian_sub.add_parser(
        'quarantine', help='Copy selected suspect files into local quarantine'
    )
    guardian_quarantine.add_argument('--project-root', default=None)
    guardian_quarantine.add_argument('paths', nargs='*')
    guardian_quarantine.add_argument('--reason', default='manual')
    guardian_report = guardian_sub.add_parser(
        'report', help='Print a Guardian project report'
    )
    guardian_report.add_argument('--project-root', default=None)
    guardian_report.add_argument('--json', action='store_true')
    guardian_proof = guardian_sub.add_parser('proof', help='Verify, attest, and review Proof Mode receipts')
    guardian_proof_sub = guardian_proof.add_subparsers(dest='guardian_proof_cmd')
    for name in ('verify', 'attest'):
        sub = guardian_proof_sub.add_parser(name)
        sub.add_argument('--project-root', default=None)
        sub.add_argument('--receipt', required=True)
    guardian_proof_review = guardian_proof_sub.add_parser('review')
    guardian_proof_review.add_argument('--project-root', default=None)
    guardian_proof_review.add_argument('--receipt', required=True)
    guardian_proof_review.add_argument('--provider', default=None)
    guardian_proof_review.add_argument('--model', default=None)
    guardian_proof_review.add_argument('--allow-network', action='store_true')
    guardian_proof_history = guardian_proof_sub.add_parser('history')
    guardian_proof_history.add_argument('--project-root', default=None)
    guardian_proof_history.add_argument('--limit', type=int, default=50)

    # AI mode convenience command
    ai_mode_parser = subparsers.add_parser(
        'ai-mode', help='Enable or inspect local AI mode features'
    )
    ai_mode_parser.add_argument(
        'action',
        choices=['status', 'enable', 'disable'],
        help='Inspect, enable, or disable cache/breaker helpers',
    )
    ai_mode_parser.add_argument(
        '--model',
        default=DEFAULT_OFFLINE_MODEL,
        help=f"Model to verify when enabling (default: {DEFAULT_OFFLINE_MODEL})",
    )
    ai_mode_parser.add_argument(
        '--persist',
        action='store_true',
        help='Store cache/breaker preference under ~/.sona/ai-mode.json',
    )

    # security probe command
    probe_parser = subparsers.add_parser(
        'probe', help='Run lightweight security / policy probe or stdlib inspection'
    )
    probe_parser.add_argument(
        'probe_target',
        nargs='?',
        choices=['stdlib', 'accessibility', 'guardian'],
        help='Probe target (stdlib, accessibility, or guardian)'
    )
    probe_parser.add_argument(
        '--category',
        choices=['utility', 'accessibility', 'resilience', 'testing', 'developer-experience', 'security', 'internal'],
        help='Filter stdlib probe output by manifest category',
    )
    probe_parser.add_argument(
        '--stability',
        choices=['stable', 'experimental', 'internal'],
        help='Filter stdlib probe output by stability group',
    )
    probe_parser.add_argument(
        '--profile',
        choices=['adhd', 'dyslexia', 'autism', 'cross-profile'],
        help='Filter accessibility probe output by profile',
    )
    probe_parser.add_argument(
        '--text', help='Optional inline text to scan', default=''
    )

    guard_parser = subparsers.add_parser(
        'guard',
        help='Guardian project resilience commands',
    )
    guard_sub = guard_parser.add_subparsers(
        dest='guard_cmd',
        help='Guardian operations',
    )

    def add_guard_root(command_parser):
        command_parser.add_argument(
            '--project-root',
            default=None,
            help='Project root to guard (defaults to current directory)',
        )

    for name, help_text in [
        ('init', 'Initialize Guardian for a project root'),
        ('status', 'Show Guardian status'),
        ('verify', 'Detect drift against the trusted baseline'),
        ('check', 'Compatibility alias for read-only Guardian verification'),
        ('explain', 'Explain Guardian workflow state and next step'),
        ('doctor', 'Show Guardian readiness and policy state'),
        ('diff', 'Show concise drift details'),
        ('graph', 'Show Guardian PARG dependency graph'),
        ('audit', 'Show local Guardian audit history'),
    ]:
        sub = guard_sub.add_parser(name, help=help_text)
        add_guard_root(sub)

    guard_sub.choices['verify'].add_argument(
        '--run-validation',
        action='store_true',
        help='Run trusted validation commands recorded during init',
    )
    guard_sub.choices['audit'].add_argument(
        '--limit',
        type=int,
        default=50,
        help='Maximum audit records to print',
    )

    snapshot_parser = guard_sub.add_parser('snapshot', help='Create a Guardian snapshot')
    add_guard_root(snapshot_parser)
    snapshot_parser.add_argument('--name', default=None, help='Optional snapshot label')

    quarantine_parser = guard_sub.add_parser('quarantine', help='Copy suspect files into local quarantine')
    add_guard_root(quarantine_parser)
    quarantine_parser.add_argument('paths', nargs='*', help='Optional relative paths to quarantine')
    quarantine_parser.add_argument('--reason', default='manual', help='Quarantine reason')

    rollback_parser = guard_sub.add_parser('rollback', help='Restore the last known-good snapshot')
    add_guard_root(rollback_parser)
    rollback_parser.add_argument('--snapshot-id', default=None, help='Snapshot id to restore')
    rollback_parser.add_argument('--dry-run', action='store_true', help='Preview rollback (default)')
    rollback_parser.add_argument('--apply', action='store_true', help='Apply the approved rollback plan')
    rollback_parser.add_argument('--approve', action='store_true', help='Grant approval for this rollback')

    heal_parser = guard_sub.add_parser('heal', help='Recommend or apply Guardian recovery')
    add_guard_root(heal_parser)
    heal_parser.add_argument(
        '--apply',
        action='store_true',
        help='Quarantine suspect state and restore the last known-good snapshot',
    )
    heal_parser.add_argument('--approve', action='store_true', help='Grant approval for this repair')

    repair_parser = guard_sub.add_parser('repair', help='Compatibility name for Guardian healing')
    add_guard_root(repair_parser)
    repair_parser.add_argument('--apply', action='store_true', help='Apply the approved repair plan')
    repair_parser.add_argument('--approve', action='store_true', help='Grant approval for this repair')

    report_parser = guard_sub.add_parser('report', help='Print a Guardian report')
    add_guard_root(report_parser)
    report_parser.add_argument('--json', action='store_true', help='Print JSON report')

    proof_parser = guard_sub.add_parser('proof', help='Verify, attest, and review Proof Mode receipts')
    proof_sub = proof_parser.add_subparsers(dest='guardian_proof_cmd', help='Proof Mode operations')
    for name, help_text in [
        ('verify', 'Verify a Guardian-bound Proof Mode receipt'),
        ('attest', 'Record a successful Guardian-bound Proof Mode receipt'),
    ]:
        sub = proof_sub.add_parser(name, help=help_text)
        add_guard_root(sub)
        sub.add_argument('--receipt', required=True, help='Path to a Proof Mode receipt')
    proof_review_parser = proof_sub.add_parser('review', help='Run governed advisory analysis over verified Proof facts')
    add_guard_root(proof_review_parser)
    proof_review_parser.add_argument('--receipt', required=True, help='Path to a Proof Mode receipt')
    proof_review_parser.add_argument('--provider', default=None, help='Governed provider id, such as ollama or deterministic')
    proof_review_parser.add_argument('--model', default=None, help='Optional registered model id')
    proof_review_parser.add_argument('--allow-network', action='store_true', help='Explicitly permit a configured remote provider; local Ollama does not require this')
    proof_history_parser = proof_sub.add_parser('history', help='Show Proof Mode attestations')
    add_guard_root(proof_history_parser)
    proof_history_parser.add_argument('--limit', type=int, default=50, help='Maximum attestations to print')

    # doctor command
    _doctor_parser = subparsers.add_parser(  # noqa: F841
        'doctor', help='Diagnose environment & feature readiness'
    )

    # build-info command
    _build_info_parser = subparsers.add_parser(  # noqa: F841
        'build-info', help='Show feature flag & subsystem status'
    )

    # perf-log command (emit a single perf event)
    _perf_log_parser = subparsers.add_parser(  # noqa: F841
        'perf-log', help='Emit a perf event (requires SONA_PERF_LOGS=1)'
    )
    _perf_log_parser.add_argument('event', help='Event name')
    _perf_log_parser.add_argument(
        '--ms', type=float, default=0.0,
        help='Optional duration in ms'
    )
    _perf_log_parser.add_argument(
        '--field', action='append', default=[],
        help='Extra key=value field (repeatable)'
    )

    return parser


def handle_run_command(args) -> int:
    """Handle the run command with centralized exit code logic"""

    if getattr(args, 'json', False):
        from .run_result import run_json
        return run_json(args, handle_run_command)

    # Import here to avoid circular imports
    from sona.type_system.runtime_checker import TypeCheckAbort

    file_path = Path(args.file)
    if not file_path.exists():
        safe_error(f"SonaFileError: file not found: {args.file}")
        safe_error("  hint: check the path and run the command again.")
        return 1

    if file_path.suffix.lower() == '.py':
        return _run_python_script(file_path, [], debug=getattr(args, 'debug', False))

    exit_code = 0
    error_text = None
    start = None
    logger = None
    execution = None
    type_stats = {'errors': 0, 'warnings': 0}

    try:
        import time as _time
        start = _time.perf_counter()

        # Configure type checking based on CLI argument
        if hasattr(args, 'types'):
            configure_types(cli_mode=args.types)
            logger = get_type_logger()

        code = read_text_safe(args.file)
        if hasattr(args, '_run_packet'):
            from hashlib import sha256
            args._run_packet['source_sha256'] = 'sha256:' + sha256(code.encode('utf-8')).hexdigest()
            args._run_packet['source_mapping'] = 'transformed' if _extract_python_blocks(code)[0] else 'original'

        if args.debug:
            safe_print(f"[DEBUG] Executing: {args.file}")
            safe_print(f"Safe mode: {'enabled' if args.safe else 'disabled'}")
            if hasattr(args, 'types'):
                safe_print(f"Type checking: {args.types}")
            safe_print("=" * 50)

        # Execute the code
        execution = execute_sona(
            code,
            safe_mode=args.safe,
            file_path=args.file,
            debug=args.debug,
            compatibility_mode=getattr(args, 'compatibility', 'auto'),
        )

        if args.debug:
            safe_print("=" * 50)
            safe_print(f"[OK] Execution completed. Result: {execution.result}")

    except TypeCheckAbort:
        # Type checking failure in ON mode - exit code handled below
        error_text = 'TypeCheckAbort'
        pass
    except Exception as e:
        if hasattr(args, '_run_packet'):
            runtime_diagnostic = getattr(e, 'diagnostic', None)
            if runtime_diagnostic is not None:
                args._run_packet['diagnostics'].append(runtime_diagnostic.to_dict())
        mode = _resolve_error_mode(args)
        _render_execution_error(
            e,
            mode=mode,
            debug=getattr(args, 'debug', False),
            filename=args.file,
            source=code if 'code' in locals() else None,
        )
        error_text = f"{type(e).__name__}: {e}"
        exit_code = 1
    finally:
        type_stats = _emit_type_logger_summary(logger, args)
        if (
            logger
            and hasattr(args, 'types')
            and getattr(args, 'types', None) not in (None, 'off')
            and logger.should_exit_with_error()
        ):
            exit_code = 2

        duration_ms = None
        if start is not None:
            try:
                import time as _time
                duration_ms = int((_time.perf_counter() - start) * 1000)
            except Exception:
                duration_ms = None

        receipt_path = getattr(args, 'receipt_path', None)
        if receipt_path and duration_ms is not None:
            try:
                import sys
                from sona import __version__ as _sona_version
                from sona.receipts import ReceiptConfig, build_receipt, write_receipt_json

                cfg = ReceiptConfig(env_allowlist=tuple(getattr(args, 'receipt_env', []) or ()))
                receipt = build_receipt(
                    sona_version=str(_sona_version),
                    entry_file=file_path,
                    project_root=file_path.resolve().parent,
                    argv=list(getattr(sys, 'argv', []) or []),
                    exit_code=exit_code,
                    duration_ms=duration_ms,
                    error_text=error_text,
                    config=cfg,
                )
                write_receipt_json(receipt, Path(receipt_path))
            except Exception as exc:
                safe_print(f"[WARN] Failed to write receipt: {exc}")

    type_mode = 'off'
    if logger:
        try:
            type_mode = get_type_config().get_effective_mode().value
        except Exception:
            type_mode = 'off'

    type_issues = bool(type_stats.get('errors') or type_stats.get('warnings'))
    fallback_flag = bool(execution and execution.fallback_reason)
    summary_requested = bool(getattr(args, 'summary', False))
    debug_summary = bool(getattr(args, 'debug', False))
    if (summary_requested or type_issues or fallback_flag or debug_summary) and execution:
        _print_structured_summary(
            execution,
            args.file,
            type_mode,
            type_stats,
            header='[Run Summary]'
        )

    return exit_code


def handle_demo_command(args) -> int:
    """Execute curated demo programs with optional summary output."""

    scenario = getattr(args, 'scenario', 'showcase')
    code = DEMO_PROGRAMS.get(scenario)
    if code is None:
        safe_print(f"[ERROR] Unknown demo scenario '{scenario}'")
        return 1

    logger = None
    execution = None
    exit_code = 0
    type_stats = {'errors': 0, 'warnings': 0}

    try:
        if hasattr(args, 'types'):
            configure_types(cli_mode=args.types)
            logger = get_type_logger()

        safe_print(f"[DEMO] Running built-in scenario '{scenario}'")
        execution = execute_sona(
            code,
            safe_mode=False,
            file_path=f"<demo:{scenario}>",
            debug=False,
        )
    except Exception as exc:
        safe_print(f"[ERROR] Demo execution failed: {exc}")
        exit_code = 1
    finally:
        type_stats = _emit_type_logger_summary(logger, args)
        if (
            logger
            and hasattr(args, 'types')
            and getattr(args, 'types', None) not in (None, 'off')
            and logger.should_exit_with_error()
        ):
            exit_code = max(exit_code, 2)

    type_mode = 'off'
    if logger:
        try:
            type_mode = get_type_config().get_effective_mode().value
        except Exception:
            type_mode = 'off'

    should_show_summary = bool(getattr(args, 'summary', False))
    if execution and (should_show_summary or execution.fallback_reason):
        _print_structured_summary(
            execution,
            f"demo::{scenario}",
            type_mode,
            type_stats,
            header='[Demo Summary]'
        )

    return exit_code


def handle_ai_model_command(args) -> int:
    """Manage local Ollama models for offline AI features."""

    try:
        from .ai.local_models import ensure_local_model
    except Exception as exc:
        safe_print(f"[ERROR] Local AI helpers unavailable: {exc}")
        return 1

    model = getattr(args, 'model', None) or DEFAULT_OFFLINE_MODEL
    cmd = getattr(args, 'ai_model_cmd', None) or 'status'
    pull_flag = cmd == 'pull'

    status = ensure_local_model(
        model,
        pull_if_missing=pull_flag,
        quiet=not pull_flag,
    )

    host = status.get('ollama_host', 'unknown')
    safe_print(f"[AI] Ollama host: {host}")

    if not status.get('ollama_running'):
        safe_print("[WARN] Ollama is not running. Install/start it from https://ollama.com/download.")
        if status.get('error'):
            safe_print(f"       {status['error']}")
        return 1

    if status.get('installed'):
        safe_print(f"[OK] Model '{model}' is ready for offline mode.")
        return 0

    if pull_flag and status.get('pulled'):
        safe_print(f"[OK] Model '{model}' downloaded successfully.")
        return 0

    if status.get('error'):
        safe_print(f"[ERROR] {status['error']}")
    else:
        safe_print(f"[WARN] Model '{model}' is missing. Run 'sona ai-model pull --model {model}' to download (~4GB).")
    return 1


def handle_ai_mode_command(args) -> int:
    """High-level helper to enable cache/breaker and verify the local model."""

    action = getattr(args, 'action', 'status')
    model = getattr(args, 'model', DEFAULT_OFFLINE_MODEL)
    persist_requested = bool(getattr(args, 'persist', False))

    from .flags import refresh_flags, get_flags
    from .persisted_env import (
        get_ai_mode_config_path,
        load_ai_mode_preferences,
        save_ai_mode_preferences,
        clear_ai_mode_preferences,
    )
    try:
        from .ai.local_models import ensure_local_model
    except Exception as exc:
        safe_print(f"[ERROR] Local AI helpers unavailable: {exc}")
        return 1

    def _print_persisted_status(prefs: dict) -> None:
        config_path = get_ai_mode_config_path()
        if not prefs:
            safe_print("[AI] Persisted defaults: not set (run with --persist to store.)")
            safe_print(f"      Target file: {config_path}")
            return
        cache_txt = 'on' if prefs.get('enable_cache') else 'off'
        breaker_txt = 'on' if prefs.get('enable_breaker') else 'off'
        safe_print(f"[AI] Persisted defaults ({config_path}): cache={cache_txt}, breaker={breaker_txt}")

    status = {"status": "skipped"}
    if action != 'disable':
        status = ensure_local_model(
            model,
            pull_if_missing=(action == 'enable'),
            quiet=(action != 'enable')
        )
        safe_print(f"[AI] Model status: {status.get('status')}")
        if status.get('error'):
            safe_print(f"      {status['error']}")
            if action == 'enable':
                safe_print("      Resolve the issue above, then rerun 'sona ai-mode enable'.")
            return 1
    else:
        safe_print("[AI] Model status: skipped (disable does not require local model checks)")

    prefs = load_ai_mode_preferences()

    if action == 'status':
        if persist_requested:
            safe_print("[WARN] --persist is ignored for 'status'.")
        flags = get_flags()
        safe_print(f"[AI] Cache enabled: {flags.enable_cache}")
        safe_print(f"[AI] Breaker enabled: {flags.enable_breaker}")
        _print_persisted_status(prefs)
        return 0

    if action == 'disable':
        removed_keys = []
        for key in ("SONA_ENABLE_CACHE", "SONA_ENABLE_BREAKER"):
            if os.environ.pop(key, None) is not None:
                removed_keys.append(key)
        if removed_keys:
            safe_print(f"[AI] Cleared {', '.join(removed_keys)} for this process.")
        else:
            safe_print("[AI] No session environment overrides were active.")

        if persist_requested:
            try:
                path = save_ai_mode_preferences(False, False)
                safe_print(f"[OK] Stored persistent defaults at {path} (cache/breaker off).")
            except Exception as exc:
                safe_print(f"[WARN] Failed to persist defaults: {exc}")
        else:
            cleared_path = clear_ai_mode_preferences()
            if cleared_path is not None:
                safe_print(f"[OK] Removed persisted defaults at {cleared_path}.")
            else:
                safe_print("[AI] No persisted defaults were set.")

        refresh_flags()
        flags = get_flags()
        prefs = load_ai_mode_preferences()
        safe_print(f"[AI] Cache enabled: {flags.enable_cache}")
        safe_print(f"[AI] Breaker enabled: {flags.enable_breaker}")
        _print_persisted_status(prefs)

        if os.name == 'nt':
            safe_print("[HINT] Remove the variables from your current shell with:")
            safe_print("  Remove-Item Env:SONA_ENABLE_CACHE")
            safe_print("  Remove-Item Env:SONA_ENABLE_BREAKER")
            safe_print("  setx SONA_ENABLE_CACHE \"\" # clears persisted user value")
            safe_print("  setx SONA_ENABLE_BREAKER \"\"")
        else:
            safe_print("[HINT] Remove environment variables with:")
            safe_print("  unset SONA_ENABLE_CACHE")
            safe_print("  unset SONA_ENABLE_BREAKER")

        safe_print("[OK] Local AI mode defaults reverted. Restart your shell/editor if needed.")
        return 0

    # Enable cache + breaker via environment suggestion
    if os.name == 'nt':
        safe_print("[HINT] Run these commands in PowerShell to enable cache + breaker permanently:")
        safe_print("  $env:SONA_ENABLE_CACHE=1")
        safe_print("  $env:SONA_ENABLE_BREAKER=1")
    else:
        safe_print("[HINT] Run these commands in your shell to enable cache + breaker:")
        safe_print("  export SONA_ENABLE_CACHE=1")
        safe_print("  export SONA_ENABLE_BREAKER=1")

    stored_path = None
    persist_error = None
    if persist_requested:
        try:
            stored_path = save_ai_mode_preferences(True, True)
        except Exception as exc:
            persist_error = exc

    refresh_flags()
    flags = get_flags()
    prefs = load_ai_mode_preferences()
    safe_print(f"[AI] Cache enabled: {flags.enable_cache}")
    safe_print(f"[AI] Breaker enabled: {flags.enable_breaker}")
    if stored_path:
        safe_print(f"[OK] Stored persistent defaults at {stored_path}.")
    elif persist_error:
        safe_print(f"[WARN] Failed to persist defaults: {persist_error}")
    _print_persisted_status(prefs)
    safe_print("[OK] Local AI mode dependencies verified. Restart your shell/editor if needed.")
    return 0


def handle_types_status(args) -> int:
    """Handle --types-status command with proper exit code semantics"""
    try:
        from .type_config import get_type_config

        # Configure with CLI argument if provided
        if hasattr(args, 'types') and args.types:
            configure_types(cli_mode=args.types)
        else:
            configure_types()

        config = get_type_config()
        effective_mode = config.get_effective_mode()

        print("=== Sona Type Checking Configuration ===")
        print(f"Effective mode: {effective_mode.value}")

        # Determine source of configuration
        if hasattr(config, 'cli_mode') and config.cli_mode is not None:
            cli_val = config.cli_mode.value
            print(f"Source: CLI argument (--types={cli_val})")
        elif hasattr(config, 'env_mode') and config.env_mode is not None:
            env_val = config.env_mode.value
            print(f"Source: Environment variable (SONA_TYPES={env_val})")
        elif hasattr(config, 'config_mode') and config.config_mode is not None:
            cfg_val = config.config_mode.value
            print(f"Source: Configuration file (mode={cfg_val})")
        else:
            print("Source: Default (OFF)")

        # Show available settings
        print(f"Type checking enabled: {config.should_check_types()}")
        if hasattr(config, 'should_exit_with_error'):
            print(f"Exit on errors: {config.should_exit_with_error()}")

        # Show log level
        if hasattr(config, 'log_level'):
            print(f"Log level: {config.log_level}")

        # Show log sink
        print("Log sink: stderr (JSONL)")

        # Exit code semantics as per directive:
        # ON -> 2, WARN -> 0, OFF -> 0 (implied), exceptions -> 1
        if effective_mode.value.lower() == 'on':
            return 2
        else:  # warn or off
            return 0

    except Exception as e:
        print(f"[ERROR] Error checking type configuration: {e}")
        return 1


def handle_info_command(args) -> int:
    """Handle the info command"""
    safe_print("[SONA] Sona Programming Language")
    safe_print(f"   Version: {SONA_VERSION}")
    safe_print(f"   AI Features: {AI_FEATURES_VERSION}")
    safe_print(f"   Python: {sys.version.split()[0]}")

    if args.ai_status:
        safe_print("\n[AI] AI Feature Status:")
        try:
            from sona.ai.ai_backend import get_ai_backend
            backend = get_ai_backend()
            safe_print(f"   [OK] AI Backend: {backend.__class__.__name__}")
            safe_print("   [OK] Code Completion: Available")
            safe_print("   [OK] Cognitive Assistant: Available")
            safe_print("   [OK] Natural Language Processing: Available")
        except ImportError:
            safe_print("   [ERROR] AI Features: Not available (missing dependencies)")
        except Exception as e:
            safe_print(f"   [WARN] AI Features: Error ({e})")

    safe_print("\n[HELP] Commands:")
    commands = [
        ("run", "Execute a Sona file"),
        ("demo", "Run built-in demo"),
        ("profile", "Profile code execution"),
        ("benchmark", "Benchmark performance"),
        ("suggest", "AI code suggestions"),
        ("explain", "AI code explanations"),
        ("why", "Explain a diagnostic with Sona Guide"),
        ("fix", "Preview deterministic Sona Guide fixes"),
        ("focus", "Group diagnostics with Focus Mode"),
        ("check", "Validate syntax"),
        ("format", "Format Sona code"),
        ("transpile", "Transpile Sona to Python"),
        ("repl", "Start interactive REPL"),
        ("lock", "Generate sona.lock.json"),
        ("verify", "Verify sona.lock.json"),
        ("setup", "Configure AI providers"),
        ("keys", "Manage API credentials"),
        ("ai-plan", "Generate deterministic plan JSON"),
        ("ai-review", "Review artifact text"),
        ("ai-model", "Manage offline AI models"),
        ("ai-mode", "Enable cache/breaker for local AI"),
        ("probe", "Run policy probe / stdlib inspection"),
        ("doctor", "Diagnose environment readiness"),
        ("build-info", "Show build and feature info"),
        ("perf-log", "Emit a perf event"),
        ("info", "System information"),
    ]
    for name, desc in commands:
        safe_print(f"   {name:<10} - {desc}")

    return 0


def handle_check_command(args) -> int:
    """Handle the check command"""
    output_format = 'json' if getattr(args, 'json', False) else getattr(args, 'format', 'text')
    target = Path(args.file)
    if not target.exists():
        if output_format == 'json':
            import json
            print(json.dumps({"schema_version": 1, "command": "check", "status": "failed", "diagnostics": [{"diagnostic_id": "SONA-MODULE-001", "category": "module", "severity": "error", "message": f"File not found: {args.file}", "file": args.file, "start_line": 1, "start_column": 1}]}))
            return 1
        safe_error(f"SonaFileError: file not found: {args.file}")
        safe_error("  hint: check the path and run the command again.")
        return 1
    if not target.is_file():
        if output_format == 'json':
            import json
            print(json.dumps({"schema_version": 1, "command": "check", "status": "failed", "diagnostics": [{"diagnostic_id": "SONA-MODULE-003", "category": "module", "severity": "error", "message": "The check target is not a regular file.", "file": str(args.file), "start_line": 1, "start_column": 1, "hint": "Pass a .sona or .smod file path."}]}))
            return 1
        safe_error(f"SonaFileError: not a regular file: {args.file}")
        safe_error("  hint: pass a .sona or .smod file path.")
        return 1

    try:
        code = read_text_safe(args.file)
        from .parser_v090 import create_parser
    except (OSError, UnicodeError, ImportError):
        if output_format == 'json':
            import json
            print(json.dumps({"schema_version": 1, "command": "check", "status": "failed", "diagnostics": [{"diagnostic_id": "SONA-PARSE-099", "category": "internal", "severity": "error", "message": "The source or canonical parser could not be loaded.", "file": str(args.file), "start_line": 1, "start_column": 1, "hint": "Verify file permissions and the Sona installation."}]}))
            return 1
        safe_error("[ERROR] The source or canonical parser could not be loaded.")
        return 1

    try:
        parser = create_parser()
        result = parser.validate_syntax(code)
    except Exception:
        if output_format == 'json':
            import json
            print(json.dumps({"schema_version": 1, "command": "check", "status": "failed", "diagnostics": [{"diagnostic_id": "SONA-PARSE-099", "category": "internal", "severity": "error", "message": "The syntax check encountered an internal failure.", "file": str(args.file), "start_line": 1, "start_column": 1, "hint": "Source was not executed; report this failure."}]}))
            return 1
        safe_error("[ERROR] The syntax check encountered an internal failure.")
        return 1

    errors = result.get('errors', []) if isinstance(result, dict) else []
    warnings = result.get('warnings', []) if isinstance(result, dict) else []
    suggestions = result.get('suggestions', []) if isinstance(result, dict) else []

    if output_format == 'json':
        import json
        from sona.developer_intelligence.frontend import analyze_frontend
        structured = [item.to_dict() for item in analyze_frontend(code, file=str(args.file))]
        print(json.dumps({
            "schema_version": 1, "command": "check",
            "status": "failed" if any(item.get("severity") == "error" for item in structured) else "ok", "file": str(args.file),
            "diagnostics": structured,
        }, ensure_ascii=False, sort_keys=True))
        return 1 if errors else 0

    if errors:
        safe_print(f"[ERROR] Syntax check failed for {args.file}")
        for err in errors:
            safe_print(f"  - {err}")
        if suggestions:
            safe_print("[HINT] Suggestions:")
            for hint in suggestions:
                safe_print(f"  - {hint}")
        return 1

    safe_print(f"[OK] Syntax check passed for {args.file}")
    if warnings:
        safe_print("[WARN] Warnings:")
        for warn in warnings:
            safe_print(f"  - {warn}")
    if suggestions:
        safe_print("[HINT] Suggestions:")
        for hint in suggestions:
            safe_print(f"  - {hint}")
    return 0


def handle_format_command(args) -> int:
    """Handle the format command"""
    if not Path(args.file).exists():
        safe_print(f"[ERROR] File '{args.file}' not found.")
        return 1

    try:
        code = read_text_safe(args.file)

        # Basic formatting - preserve whitespace and adjust simple assignments.
        lines = code.splitlines(keepends=True)
        formatted_lines: list[str] = []

        for line in lines:
            line_ending = ""
            content = line
            if line.endswith("\r\n"):
                line_ending = "\r\n"
                content = line[:-2]
            elif line.endswith("\n") or line.endswith("\r"):
                line_ending = line[-1]
                content = line[:-1]

            stripped = content.lstrip()
            if not stripped or stripped.startswith('#'):
                formatted_lines.append(content + line_ending)
                continue

            # Keep inline comments untouched to avoid breaking them.
            if '//' in stripped or '#' in stripped:
                formatted_lines.append(content + line_ending)
                continue

            if stripped.startswith(('let ', 'const ')) and '=' in stripped:
                left, right = stripped.split('=', 1)
                normalized = f"{left.rstrip()} = {right.lstrip()}"
                content = content[: len(content) - len(stripped)] + normalized

            formatted_lines.append(content + line_ending)

        formatted_text = ''.join(formatted_lines)
        if formatted_text == code:
            safe_print(f"[OK] Already formatted: {args.file}")
            return 0

        with open(args.file, 'w', encoding='utf-8') as f:
            f.write(formatted_text)

        safe_print(f"[OK] Formatted {args.file}")
        return 0

    except Exception as e:
        safe_print(f"[ERROR] Format error: {e}")
        return 1


def handle_transpile_command(args) -> int:
    """Handle the transpile command"""
    if not Path(args.file).exists():
        safe_print(f"[ERROR] File '{args.file}' not found.")
        return 1

    try:
        from .sona_transpiler import SonaTranspiler, TranspileOptions

        transpiler = SonaTranspiler(
            TranspileOptions(include_cognitive_blocks=not args.core_only)
        )
        result = transpiler.transpile_file(args.file)
        if not result.ok:
            safe_print("[ERROR] Transpilation failed:")
            for err in result.errors:
                safe_print(f"  - {err}")
            return 1

        if result.warnings:
            safe_print("[WARN] Transpilation warnings:")
            for warn in result.warnings:
                safe_print(f"  - {warn}")

        # Determine output file
        src_path = Path(args.file)
        output_file = Path(args.output) if args.output else src_path.with_suffix('.py')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.code)

        safe_print(f"[OK] Transpiled {args.file} to {output_file}")
        return 0

    except Exception as e:
        safe_print(f"[ERROR] Transpile error: {e}")
        return 1


def _repl_source_complete(source: str) -> bool:
    """Return whether a REPL buffer has balanced strings and delimiters."""
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []
    quote: str | None = None
    escaped = False
    comment = False
    for character in source:
        if comment:
            if character == "\n":
                comment = False
            continue
        if quote is not None:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            continue
        if character in {'"', "'"}:
            quote = character
        elif character == "#":
            comment = True
        elif character in "([{":
            stack.append(character)
        elif character in pairs:
            if not stack or stack[-1] != pairs[character]:
                return True  # Let the parser report the extra delimiter now.
            stack.pop()
    return quote is None and not stack


def handle_repl_command(args) -> int:
    """Handle the repl command"""
    safe_print("[INFO] Starting Sona REPL...")

    try:
        from sona.interpreter import SonaInterpreter
        interpreter = SonaInterpreter()

        safe_print("Sona REPL v0.15.6 - Type 'exit' to quit; ':reset' clears state")
        if args.ai:
            try:
                interpreter.enable_ai()
                safe_print("[AI] AI assistance enabled")
            except Exception as e:
                safe_print(f"[WARN] Failed to enable AI assistance: {e}")

        buffer: list[str] = []
        while True:
            try:
                user_input = input("...> " if buffer else "sona> ")
                command = user_input.strip().lower()
                if not buffer and command in ['exit', 'quit']:
                    break
                if not buffer and command == ':reset':
                    interpreter.reset()
                    safe_print("[OK] REPL state reset")
                    continue

                if user_input.strip() or buffer:
                    buffer.append(user_input)
                    source = "\n".join(buffer)
                    if not _repl_source_complete(source):
                        continue
                    try:
                        result = interpreter.interpret(source, filename="<repl>")
                        if result is not None:
                            safe_print(f"=> {result}")
                    except Exception as e:
                        diagnostic_id = getattr(
                            getattr(e, "diagnostic", None), "diagnostic_id", None
                        )
                        prefix = f"{diagnostic_id}: " if diagnostic_id else ""
                        safe_print(f"[ERROR] {prefix}{e}")
                    finally:
                        buffer.clear()

            except KeyboardInterrupt:
                safe_print("\n[BYE] Goodbye!")
                break
            except EOFError:
                break

        interpreter.close()
        return 0

    except Exception as e:
        safe_print(f"[ERROR] REPL error: {e}")
        return 1


def _ensure_enhanced_loaded():
    global ENHANCED_COMMANDS
    if ENHANCED_COMMANDS is None:
        from sona.ai.enhanced_cli import (
            ENHANCED_COMMANDS as CMDS,  # type: ignore
        )
        ENHANCED_COMMANDS = CMDS


def handle_enhanced_command(command: str, args) -> int:
    """Handle enhanced AI commands (lazy import of heavy deps)."""
    try:
        output_format = 'json' if getattr(args, 'json', False) else getattr(args, 'format', 'text')
        if command in {'explain', 'suggest'}:
            from sona.developer_intelligence import (
                ContextEnvelope,
                DeveloperIntelligenceService,
                TaskConstraints,
                TaskRequest,
                TaskType,
            )
            from sona.developer_intelligence.config import resolve_config
            task_type = TaskType.EXPLAIN if command == 'explain' else TaskType.SUGGEST
            provider_id = getattr(args, 'provider', None)
            model_id = getattr(args, 'model', None)
            if getattr(args, 'ai', False) and not provider_id and not model_id:
                configured = resolve_config(Path.cwd()).get('providers', {})
                provider_id = configured.get('selected') or configured.get('backend')
            source = read_text_safe(args.file)
            request = TaskRequest(
                task_type=task_type,
                instruction=f"{command} the target file for a developer",
                target_files=(str(args.file),),
                provider_id=provider_id,
                model_id=model_id,
                context=ContextEnvelope(active_file=str(args.file), target_files=(str(args.file),), selected_text=source, origin='cli'),
                constraints=TaskConstraints(allow_network=bool(provider_id or model_id)),
                governance_metadata={'style': getattr(args, 'style', 'simple')},
            )
            result = DeveloperIntelligenceService(Path.cwd()).execute(request, write_task_receipt=False)
            if output_format == 'json':
                print(result.to_json(canonical=True))
            else:
                safe_print(result.summary)
            return 0 if result.status.value in {'ok', 'proposed'} else 1
        _ensure_enhanced_loaded()
        cmds = ENHANCED_COMMANDS or {}
        if command not in cmds:  # type: ignore
            safe_print(f"[ERROR] Unknown command: {command}")
            return 1

        arg_list = [args.file]

        if command == 'profile' and getattr(args, 'ai_insights', False):
            arg_list.append('--ai-insights')
        elif command == 'benchmark':
            if getattr(args, 'compare_versions', False):
                arg_list.append('--compare-versions')
            if getattr(args, 'ai_recommendations', False):
                arg_list.append('--ai-recommendations')
        elif command == 'suggest':
            if getattr(args, 'cognitive', False):
                arg_list.append('--cognitive')
            if getattr(args, 'performance', False):
                arg_list.append('--performance')
            if getattr(args, 'accessibility', False):
                arg_list.append('--accessibility')
            if getattr(args, 'ai', False):
                arg_list.append('--ai')
        elif command == 'explain' and hasattr(args, 'style'):
            arg_list.extend(['--style', args.style])
            if getattr(args, 'ai', False):
                arg_list.append('--ai')

        result = cmds[command](arg_list)  # type: ignore[index]
        return result if isinstance(result, int) else 0
    except Exception as e:  # pragma: no cover - defensive
        safe_print(f"[ERROR] Command failed: {e}")
        return 1


def handle_ai_task_command(args) -> int:
    import json
    from sona.developer_intelligence import DeveloperIntelligenceService, TaskRequest, TaskType

    try:
        if getattr(args, 'request', None):
            raw = sys.stdin.read() if args.request == '-' else Path(args.request).read_text(encoding='utf-8')
            request = TaskRequest.from_dict(json.loads(raw))
        else:
            if not getattr(args, 'task_type', None):
                raise ValueError("--type is required when --request is not used")
            request = TaskRequest(
                task_type=TaskType(args.task_type), instruction=str(args.instruction or ''),
                target_files=tuple(args.files or ()), provider_id=args.provider, model_id=args.model,
            )
        result = DeveloperIntelligenceService(Path.cwd()).execute(
            request, write_task_receipt=not getattr(args, 'no_receipt', False)
        )
        if getattr(args, 'format', 'json') == 'json':
            print(result.to_json(canonical=True))
        else:
            safe_print(f"[{result.status.value}] {result.summary}")
            if result.receipt_path:
                safe_print(f"Receipt: {result.receipt_path}")
        return 0 if result.status.value in {'ok', 'proposed'} else 1
    except Exception as exc:
        payload = {"schema_version": 1, "status": "failed", "diagnostics": [{"diagnostic_id": "SONA-AI-001", "category": "provider", "severity": "error", "message": str(exc)}]}
        if getattr(args, 'format', 'json') == 'json':
            print(json.dumps(payload, sort_keys=True))
        else:
            safe_error(f"[ERROR] {exc}")
        return 1


def _registry_for_workspace():
    from sona.developer_intelligence import ModelRegistry
    registry = ModelRegistry()
    sona_home = Path(os.getenv('SONA_HOME', Path.home() / '.sona'))
    registry.load_directory(sona_home / 'models', override=True)
    registry.load_directory(Path.cwd() / '.sona' / 'models', override=True)
    return registry


def handle_model_command(args) -> int:
    import json
    import shutil
    from sona.developer_intelligence.models import descriptor_from_manifest
    from sona.developer_intelligence.redaction import redact
    try:
        registry = _registry_for_workspace()
        command = getattr(args, 'model_cmd', None)
        if command == 'list':
            print(json.dumps(redact({"schema_version": 1, "models": [item.to_dict() for item in registry.list()]}), indent=2, default=str))
            return 0
        if command == 'inspect':
            item = registry.get(args.model_id)
            if item is None:
                raise ValueError(f"unknown model: {args.model_id}")
            print(json.dumps(redact(item.to_dict()), indent=2, default=str))
            return 0
        if command == 'register':
            source = Path(args.manifest).resolve()
            payload = json.loads(source.read_text(encoding='utf-8'))
            descriptor = descriptor_from_manifest(payload)
            destination_root = (Path.cwd() / '.sona' / 'models') if args.scope == 'workspace' else Path(os.getenv('SONA_HOME', Path.home() / '.sona')) / 'models'
            destination_root.mkdir(parents=True, exist_ok=True)
            destination = destination_root / (descriptor.model_id.replace(':', '__') + '.json')
            destination.write_text(json.dumps(payload, sort_keys=True, indent=2) + '\n', encoding='utf-8')
            safe_print(str(destination))
            return 0
        if command in {'test', 'health'}:
            if command == 'test' and registry.get(args.model_id) is None:
                raise ValueError(f"unknown model: {args.model_id}")
            selected = [registry.get(args.model_id)] if command == 'test' else registry.list()
            records = []
            for item in selected:
                if item is None:
                    continue
                if item.provider_id in {'claude', 'codex'}:
                    state, detail = 'unavailable', 'Provider is intentionally unavailable in 0.15.6.'
                elif not item.enabled:
                    state, detail = 'disabled', 'Descriptor is disabled.'
                elif item.provider_id == 'deterministic':
                    state, detail = 'available', 'Local deterministic provider is ready.'
                elif item.provider_id == 'ollama':
                    from sona.ai.local_models import ensure_local_model
                    status = ensure_local_model(item.provider_model_name, quiet=True, timeout=0.25)
                    ready = bool(status.get('ollama_running') and status.get('installed'))
                    state, detail = ('available', 'Ollama is running and the model is installed.') if ready else ('unavailable', 'Ollama is stopped or the model is not installed; pulling remains explicit.')
                elif item.provider_id == 'huggingface' and item.locality == 'local':
                    ready = Path(str(item.configuration.get('local_path') or '')).exists()
                    state, detail = ('available', 'Configured local path exists.') if ready else ('unavailable', 'Configured local path does not exist.')
                else:
                    ready = bool(item.configuration.get('endpoint'))
                    state, detail = ('configured', 'Endpoint configuration is present; no request was sent.') if ready else ('unavailable', 'Required endpoint configuration is missing.')
                records.append({'model_id': item.model_id, 'provider_id': item.provider_id, 'status': state, 'detail': detail})
            payload = {'schema_version': 1, 'status': 'ok', 'registered': len(registry.list()), 'models': records}
            if getattr(args, 'format', 'json') == 'text':
                for record in records:
                    safe_print(f"{record['model_id']}: {record['status']} - {record['detail']}")
            else:
                print(json.dumps(payload, sort_keys=True))
            return 0 if command == 'health' or all(item['status'] in {'available', 'configured'} for item in records) else 1
        raise ValueError("missing model command")
    except Exception as exc:
        safe_error(f"[ERROR] model command failed: {exc}")
        return 1


def handle_govern_command(args) -> int:
    import json
    from sona.developer_intelligence.governance import append_audit, evaluate, load_policy, policy_hash, validate_policy
    try:
        command = getattr(args, 'govern_cmd', None)
        if command == 'validate' and getattr(args, 'policy', None):
            policy = json.loads(Path(args.policy).read_text(encoding='utf-8'))
            source = str(Path(args.policy).resolve())
            validate_policy(policy)
        else:
            policy, source = load_policy(Path.cwd())
            validate_policy(policy)
        if command == 'validate':
            print(json.dumps({"schema_version": 1, "status": "ok", "source": source, "policy_hash": policy_hash(policy)}, sort_keys=True))
            return 0
        if command in {'check', 'explain'}:
            result = evaluate(policy, source=source, task_type=args.task, provider=args.provider, model=args.model, capability=args.capability)
            append_audit(Path.cwd(), result)
            print(json.dumps({"schema_version": 1, "decision": result.to_dict()}, sort_keys=True))
            return 1 if result.blocked else 0
        if command == 'policy':
            print(json.dumps({"schema_version": 1, "source": source, "policy_hash": policy_hash(policy), "policy": policy}, indent=2, sort_keys=True))
            return 0
        if command == 'audit':
            path = Path.cwd() / '.sona' / 'governance' / 'audit.jsonl'
            lines = path.read_text(encoding='utf-8').splitlines() if path.exists() else []
            print(json.dumps({"schema_version": 1, "records": [json.loads(line) for line in lines[-args.last:]]}, indent=2, sort_keys=True))
            return 0
        raise ValueError("missing govern command")
    except Exception as exc:
        safe_error(f"[ERROR] governance command failed: {exc}")
        return 1


def handle_keys_command(args) -> int:
    """Handle the keys command group (secure credential storage).

    Subcommands:
      set <service> [--api-key KEY] [--endpoint URL]
      get <service>
      list
      migrate
      rotate <service> [--key api_key]
    """
    try:
        # Import inside function to avoid hard dependency
        # if user never touches keys
        from secure_storage import (
            get_secret,
            list_service_keys,
            rotate_secret,
            set_secret,
        )
    except Exception as e:
        safe_print(f"[ERROR] Secure storage unavailable: {e}")
        return 1

    def _mask(value: str | None) -> str:
        if not value:
            return "<empty>"
        if len(value) <= 8:
            return "****"
        return value[:4] + "****" + value[-4:]

    cmd = args.keys_cmd
    if cmd == 'set':
        service = args.service
        api_key = getattr(args, 'api_key', None)
        endpoint = getattr(args, 'endpoint', None)
        if not api_key:
            try:
                import getpass
                api_key = getpass.getpass(f"Enter API key for {service}: ")
            except Exception:
                api_key = input(f"Enter API key for {service}: ")
        try:
            set_secret(service, 'api_key', api_key)
            if endpoint:
                set_secret(service, 'endpoint', endpoint)
            safe_print(f"[OK] Stored credentials for {service}. Key={_mask(api_key)}")
            if endpoint:
                safe_print(f"   Endpoint: {endpoint}")
            return 0
        except Exception as e:
            safe_print(f"[ERROR] Failed to store secret: {e}")
            return 1
    elif cmd == 'get':
        service = args.service
        try:
            value = get_secret(service, 'api_key')
            endpoint = get_secret(service, 'endpoint')
            if value is None and endpoint is None:
                safe_print(f"[INFO] No stored credentials for {service}")
                return 0
            safe_print(f"Service: {service}")
            safe_print(f"  api_key: {_mask(value)}")
            if endpoint:
                safe_print(f"  endpoint: {endpoint}")
            return 0
        except Exception as e:
            safe_print(f"[ERROR] Failed to retrieve secret: {e}")
            return 1
    elif cmd == 'list':
        try:
            from secure_storage import list_all_services  # local import
            services = list_all_services()
            if not services:
                safe_print("[INFO] No credentials stored yet")
                return 0
            safe_print("Stored services:")
            for service in sorted(services.keys()):
                keys = list_service_keys(service).keys()
                api_val = get_secret(service, 'api_key')
                mask = _mask(api_val) if api_val else "(no api_key)"
                extra = [k for k in keys if k != 'api_key']
                extras = f" +{len(extra)} other keys" if extra else ""
                safe_print(f"  - {service}: {mask}{extras}")
            return 0
        except Exception as e:
            safe_print(f"[ERROR] Failed to list keys: {e}")
            return 1
    elif cmd == 'migrate':
        try:
            from key_migration import migrate as migrate_keys
        except Exception as e:
            safe_print(f"[ERROR] Migration module unavailable: {e}")
            return 1
        try:
            result = migrate_keys()
            moved = result.get('migrated', 0)
            skipped = result.get('skipped', 0)
            errors = result.get('errors', 0)
            safe_print(
                "[OK] Migration complete. "
                f"Migrated={moved} Skipped={skipped} Errors={errors}"
            )
            if errors:
                safe_print("   See migration logs for details.")
            return 0 if errors == 0 else 1
        except Exception as e:
            safe_print(f"[ERROR] Migration failed: {e}")
            return 1
    elif cmd == 'rotate':
        service = args.service
        key_name = getattr(args, 'key', 'api_key')
        try:
            new_val = rotate_secret(service, key_name)
            safe_print(f"[ROTATE] Rotated {service}.{key_name}: {_mask(new_val)}")
            return 0
        except Exception as e:
            safe_print(f"[ERROR] Rotation failed: {e}")
            return 1
    else:
        safe_print(
            "[ERROR] Missing or unknown keys subcommand. "
            "Try one of: set, get, list, migrate, rotate"
        )
        return 1


# --- New feature command handlers (0.9.3) -------------------------------
def handle_ai_plan_command(args) -> int:
    try:
        from .flags import get_flags
        flags = get_flags()
        if not flags.enable_capabilities:
            return _ai_disabled_msg('ai-plan')
        try:
            from .ai.capability import ai_plan  # noqa: WPS433
        except Exception:
            return _ai_disabled_msg('ai-plan')
        plan = ai_plan(args.goal, args.context)
        import json
        print(json.dumps(plan, indent=2))
        return 0
    except Exception as e:  # pragma: no cover - defensive
        safe_print(f"[ERROR] ai-plan error: {e}")
        return 1


def handle_ai_review_command(args) -> int:
    try:
        from .flags import get_flags
        flags = get_flags()
        if not flags.enable_capabilities:
            return _ai_disabled_msg('ai-review')
        try:
            from .ai.capability import ai_review  # noqa: WPS433
        except Exception:
            return _ai_disabled_msg('ai-review')
        if not Path(args.file).exists():
            safe_print(f"[ERROR] File not found: {args.file}")
            return 1
        text = read_text_safe(args.file)
        review = ai_review(text, args.criteria)
        import json
        print(json.dumps(review, indent=2))
        return 0
    except Exception as e:  # pragma: no cover
        safe_print(f"[ERROR] ai-review error: {e}")
        return 1


def handle_probe_command(args) -> int:
    # Check if this is a stdlib probe request
    if hasattr(args, 'probe_target') and args.probe_target == 'stdlib':
        try:
            from .stdlib_cli_commands import stdlib_probe
            return stdlib_probe(
                category=getattr(args, 'category', None),
                stability=getattr(args, 'stability', None),
            )
        except Exception as e:
            safe_print(f"[ERROR] stdlib probe error: {e}")
            return 1

    if hasattr(args, 'probe_target') and args.probe_target == 'accessibility':
        try:
            from .stdlib_cli_commands import accessibility_probe
            return accessibility_probe(profile=getattr(args, 'profile', None))
        except Exception as e:
            safe_print(f"[ERROR] accessibility probe error: {e}")
            return 1

    if hasattr(args, 'probe_target') and args.probe_target == 'guardian':
        try:
            from .stdlib_cli_commands import guardian_probe
            return guardian_probe()
        except Exception as e:
            safe_print(f"[ERROR] guardian probe error: {e}")
            return 1

    # Lightweight scan using policy deny patterns (original functionality)
    try:
        from .policy import deny_text, policy_snapshot
        sample = args.text or ""
        pattern = deny_text(sample) if sample else None
        snap = policy_snapshot()
        result = {
            "type": "probe",
            "version": 1,
            "input_scanned": bool(sample),
            "denied_pattern": pattern,
            "policy": snap,
        }
        import json
        print(json.dumps(result, indent=2))
        return 0
    except Exception as e:  # pragma: no cover
        safe_print(f"[ERROR] probe error: {e}")
        return 1


def handle_why_command(args) -> int:
    import json

    from .guide import GuideError, GuideRequest, explain, mode_for_concepts, render_text
    from .guide.catalog import CATALOG

    try:
        profile_state = _guide_profile_for_args(args)
        entry = CATALOG.get(args.diagnostic_id)
        concepts = entry.concepts if entry is not None else ()
        mode = mode_for_concepts(
            profile_state.profile,
            concepts,
            explicit_mode=args.mode,
        )
        style = args.style or profile_state.profile.explanation_style
        response = explain(GuideRequest(args.diagnostic_id, mode=mode, style=style))
    except GuideError as exc:
        if args.json:
            safe_print(json.dumps({
                "schema_version": 1, "status": "unavailable", "diagnostic": exc.to_dict(),
            }, sort_keys=True))
        else:
            safe_error(f"{exc.diagnostic_id}: {exc.message}")
            safe_error(f"  hint: {exc.hint}")
        return 1
    safe_print(json.dumps(response.to_dict(), sort_keys=True) if args.json else render_text(response))
    return 0


def _guide_profile_for_args(args):
    from .guide import ProfileState, default_profile, load_profile_state

    if getattr(args, "no_profile", False):
        return ProfileState(default_profile(), persisted=False)
    return load_profile_state(getattr(args, "project_root", "."))


def _read_guide_source(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            with path.open("r", encoding=encoding, newline="") as source:
                return source.read()
        except UnicodeError:
            continue
    with path.open("r", encoding="utf-8", errors="replace", newline="") as source:
        return source.read()


def _guide_diagnostic_from_payload(payload: dict, default_file: str):
    from .guide.adapters import diagnostic_from_payload

    return diagnostic_from_payload(payload, default_file)


def _guide_diagnostics_from_payload(payload, default_file: str):
    from .guide import GuideError

    if isinstance(payload, dict):
        if isinstance(payload.get("diagnostics"), list):
            payload = payload["diagnostics"]
        elif isinstance(payload.get("visible_diagnostics"), list):
            payload = payload["visible_diagnostics"]
        else:
            payload = [payload]
    if not isinstance(payload, list):
        raise GuideError(
            "SONA-GUIDE-002",
            "The diagnostic JSON must be an object or array.",
            "Pass canonical diagnostic JSON from Sona.",
        )
    return tuple(_guide_diagnostic_from_payload(item, default_file) for item in payload)


def _guide_diagnostics_from_json_argument(value: str, default_file: str):
    import json

    from .guide import GuideError

    raw = sys.stdin.read() if value == "-" else Path(value).read_text(encoding="utf-8")
    try:
        return _guide_diagnostics_from_payload(json.loads(raw), default_file)
    except json.JSONDecodeError as exc:
        raise GuideError(
            "SONA-GUIDE-002",
            "The diagnostic JSON could not be parsed.",
            "Pass a JSON object or array from Sona's canonical diagnostic output.",
        ) from exc


def _guide_diagnostic_from_args(args, default_file: str):
    import json

    from .developer_intelligence.diagnostics import SourceSpan, diagnostic
    from .guide import GuideError

    if getattr(args, "diagnostic_json", None):
        if args.diagnostic_json == "-":
            raw = sys.stdin.read()
        else:
            raw = Path(args.diagnostic_json).read_text(encoding="utf-8")
        try:
            return _guide_diagnostic_from_payload(json.loads(raw), default_file)
        except json.JSONDecodeError as exc:
            raise GuideError(
                "SONA-GUIDE-002",
                "The diagnostic JSON could not be parsed.",
                "Pass a JSON object from Sona's canonical diagnostic output.",
            ) from exc

    if not getattr(args, "diagnostic_id", None):
        return None
    if getattr(args, "line", None) is None or getattr(args, "column", None) is None:
        raise GuideError(
            "SONA-GUIDE-002",
            "The source-backed diagnostic is missing a location.",
            "Pass --line and --column from the canonical diagnostic.",
        )
    name = getattr(args, "name", None)
    message = getattr(args, "message", None)
    if message is None:
        if name:
            message = f"Name '{name}' is not defined."
        else:
            message = "Diagnostic reported by Sona."
    return diagnostic(
        args.diagnostic_id,
        "runtime",
        message,
        hint="",
        span=SourceSpan(
            file=default_file,
            start_line=args.line,
            start_column=args.column,
            end_line=args.end_line or args.line,
            end_column=args.end_column or (args.column + len(name) if name else args.column + 1),
        ),
        source="sona",
        metadata={"name": name} if name else {},
        legacy_code=getattr(args, "legacy_code", None),
    )


def _guide_fix_payload(
    path: Path,
    status: str,
    fixes,
    diagnostic=None,
    learning_profile: dict | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "command": "fix",
        "status": status,
        "file": str(path),
        "diagnostic": diagnostic.to_dict() if diagnostic is not None else None,
        "fixes": [fix.to_dict() for fix in fixes],
        "learning_profile": learning_profile or {
            "updated": False,
            "profile_path": ".sona/learning.json",
            "concepts": [],
        },
    }


def _render_guide_fix_payload(payload: dict, *, apply_requested: bool) -> str:
    header = "Sona Guide Fix" if payload["status"] == "applied" else "Sona Guide Fix Preview"
    lines = [
        header,
        "",
        f"Status       {payload['status'].upper()}",
        f"File         {payload['file']}",
        f"Fixes        {len(payload['fixes'])}",
    ]
    for index, fix in enumerate(payload["fixes"], start=1):
        lines.extend((
            "",
            f"[{index}] {fix['title']}",
            f"Rule         {fix['rule_id']}",
            f"Confidence   {fix['confidence']}",
            f"Reason       {fix['rationale']}",
        ))
        for edit in fix["edits"]:
            span = edit["range"]
            lines.extend((
                f"Edit         {span['start_line']}:{span['start_column']}-{span['end_line']}:{span['end_column']}",
                f"Expected     {edit['expected']!r}",
                f"Replacement  {edit['replacement']!r}",
            ))
    if payload["status"] == "preview" and not apply_requested:
        lines.extend(("", "No files changed. Re-run with --apply to write these edits."))
    profile = payload.get("learning_profile") or {}
    concepts = ", ".join(profile.get("concepts") or [])
    if profile.get("updated"):
        lines.extend(("", f"Learning     updated {concepts or 'profile'}"))
    elif profile.get("diagnostic"):
        diagnostic = profile["diagnostic"]
        lines.extend((
            "",
            f"Learning     skipped ({diagnostic['diagnostic_id']})",
            f"             {diagnostic['message']}",
        ))
    elif profile.get("reason") == "disabled":
        lines.extend(("", "Learning     skipped (--no-profile-update)"))
    return "\n".join(lines)


def handle_fix_command(args) -> int:
    import json

    from .guide import (
        GuideError,
        GuideRequest,
        apply_fixes,
        concepts_for_fixes,
        preview_diagnostic_fixes,
        preview_stdlib_api_migration,
        update_concepts,
    )

    target = Path(args.file)
    try:
        source = _read_guide_source(target)
        diagnostic = _guide_diagnostic_from_args(args, str(target))
        fixes = []
        if args.rule in {"auto", "undefined-name"}:
            if diagnostic is not None:
                fixes.extend(preview_diagnostic_fixes(
                    GuideRequest(diagnostic.diagnostic_id, diagnostic),
                    source,
                    document=str(target),
                ))
            elif args.rule == "undefined-name":
                raise GuideError(
                    "SONA-GUIDE-002",
                    "The undefined-name rule needs a diagnostic.",
                    "Pass --diagnostic-json or --diagnostic-id with --line and --column.",
                )
        if args.rule in {"auto", "stdlib-api-migration"}:
            fixes.extend(preview_stdlib_api_migration(source, document=str(target)))
        if not fixes:
            raise GuideError(
                "SONA-GUIDE-004",
                "Sona Guide found no deterministic fix for this input.",
                "Use an exact diagnostic location or review the source manually.",
            )
        status = "preview"
        if args.apply:
            updated = apply_fixes(source, fixes)
            target.write_text(updated, encoding="utf-8", newline="")
            status = "applied"
        concepts = concepts_for_fixes(fixes)
        learning_profile = {
            "updated": False,
            "profile_path": ".sona/learning.json",
            "concepts": list(concepts),
            "reason": "preview",
        }
        if status == "applied":
            if args.no_profile_update:
                learning_profile["reason"] = "disabled"
            elif concepts:
                try:
                    state = update_concepts(args.project_root, concepts, familiarity="learning")
                    learning_profile = {
                        "updated": True,
                        "profile_path": ".sona/learning.json",
                        "concepts": list(concepts),
                        "profile": state.profile.to_dict(),
                    }
                except GuideError as exc:
                    learning_profile = {
                        "updated": False,
                        "profile_path": ".sona/learning.json",
                        "concepts": list(concepts),
                        "diagnostic": exc.to_dict(),
                    }
            else:
                learning_profile["reason"] = "no-concepts"
        payload = _guide_fix_payload(
            target,
            status,
            fixes,
            diagnostic,
            learning_profile=learning_profile,
        )
    except GuideError as exc:
        payload = {
            "schema_version": 1,
            "command": "fix",
            "status": "unavailable",
            "file": str(target),
            "diagnostic": exc.to_dict(),
            "fixes": [],
        }
        if args.json:
            safe_print(json.dumps(payload, sort_keys=True))
        else:
            safe_error(f"{exc.diagnostic_id}: {exc.message}")
            safe_error(f"  hint: {exc.hint}")
        return 1
    except OSError:
        payload = {
            "schema_version": 1,
            "command": "fix",
            "status": "unavailable",
            "file": str(target),
            "diagnostic": {
                "diagnostic_id": "SONA-MODULE-001",
                "category": "module",
                "severity": "error",
                "message": "The source file could not be read or written.",
                "hint": "Check that the file exists and is accessible.",
            },
            "fixes": [],
        }
        if args.json:
            safe_print(json.dumps(payload, sort_keys=True))
        else:
            safe_error("SONA-MODULE-001: The source file could not be read or written.")
            safe_error("  hint: Check that the file exists and is accessible.")
        return 1

    safe_print(json.dumps(payload, sort_keys=True) if args.json else _render_guide_fix_payload(
        payload,
        apply_requested=args.apply,
    ))
    return 0


def handle_focus_command(args) -> int:
    import json

    from .guide import GuideError, focus_diagnostics, render_focus_text

    target = Path(args.file) if getattr(args, "file", None) else None
    try:
        profile_state = _guide_profile_for_args(args)
        density = args.density or profile_state.profile.diagnostic_density
        if getattr(args, "diagnostics_json", None):
            diagnostics = _guide_diagnostics_from_json_argument(
                args.diagnostics_json,
                str(target or "<diagnostics>"),
            )
        else:
            if target is None:
                raise GuideError(
                    "SONA-GUIDE-002",
                    "Focus Mode needs a source file or diagnostic JSON.",
                    "Pass a .sona file or --diagnostics-json.",
                )
            source = _read_guide_source(target)
            from .developer_intelligence.frontend import analyze_frontend

            diagnostics = analyze_frontend(source, file=str(target))
        quiet = profile_state.profile.quiet if args.quiet is None else args.quiet
        result = focus_diagnostics(diagnostics, density=density, quiet=quiet)
    except GuideError as exc:
        payload = {
            "schema_version": 1,
            "command": "focus",
            "status": "unavailable",
            "diagnostic": exc.to_dict(),
        }
        if args.json:
            safe_print(json.dumps(payload, sort_keys=True))
        else:
            safe_error(f"{exc.diagnostic_id}: {exc.message}")
            safe_error(f"  hint: {exc.hint}")
        return 1
    except OSError:
        payload = {
            "schema_version": 1,
            "command": "focus",
            "status": "unavailable",
            "diagnostic": {
                "diagnostic_id": "SONA-MODULE-001",
                "category": "module",
                "severity": "error",
                "message": "The source file could not be read.",
                "hint": "Check that the file exists and is accessible.",
            },
        }
        if args.json:
            safe_print(json.dumps(payload, sort_keys=True))
        else:
            safe_error("SONA-MODULE-001: The source file could not be read.")
            safe_error("  hint: Check that the file exists and is accessible.")
        return 1

    safe_print(json.dumps(result.to_dict(), sort_keys=True) if args.json else render_focus_text(result))
    return 0


def handle_guide_command(args) -> int:
    if getattr(args, "guide_cmd", None) in {"proof", "guardian"}:
        from .fact_service import handle_fact_command
        return handle_fact_command(args)
    import json

    from .guide import (
        GuideError,
        load_profile_state,
        render_profile_text,
        reset_profile,
        set_preferences,
        update_concepts,
    )

    if getattr(args, "guide_cmd", None) == "request":
        from .guide.service import MAX_REQUEST_BYTES, request_json, unavailable
        try:
            profile = _guide_profile_for_args(args).profile
            raw = sys.stdin.read(MAX_REQUEST_BYTES + 1)
            payload = request_json(raw, profile=profile)
        except GuideError as exc:
            payload = unavailable(exc)
        if args.json:
            safe_print(json.dumps(payload, sort_keys=True))
        elif payload["status"] == "unavailable":
            safe_error(payload["diagnostic"]["diagnostic_id"] + ": " + payload["diagnostic"]["message"])
        else:
            safe_print(payload["text"])
        return 1 if payload["status"] == "unavailable" else 0

    if getattr(args, "guide_cmd", None) != "profile":
        safe_error("SONA-GUIDE-002: Missing Sona Guide command.")
        safe_error("  hint: Try `sona guide profile --help`.")
        return 1

    action = getattr(args, "profile_cmd", None) or "show"
    try:
        if action == "show":
            state = load_profile_state(args.project_root)
        elif action == "set":
            if (
                args.guidance_mode is None
                and args.diagnostic_density is None
                and args.explanation_style is None
                and args.quiet is None
            ):
                raise GuideError(
                    "SONA-GUIDE-002",
                    "No Sona Guide preference was selected.",
                    "Pass --mode, --density, --style, --quiet, or --no-quiet.",
                )
            state = set_preferences(
                args.project_root,
                guidance_mode=args.guidance_mode,
                diagnostic_density=args.diagnostic_density,
                explanation_style=args.explanation_style,
                quiet=args.quiet,
            )
        elif action == "reset":
            state = reset_profile(args.project_root)
        elif action == "learn":
            state = update_concepts(
                args.project_root,
                (args.concept,),
                familiarity=args.familiarity,
            )
        else:
            raise GuideError(
                "SONA-GUIDE-002",
                "The Sona Guide profile action is unknown.",
                "Use show, set, reset, or learn.",
            )
    except GuideError as exc:
        payload = {
            "schema_version": 1,
            "command": "guide profile",
            "action": action,
            "status": "unavailable",
            "diagnostic": exc.to_dict(),
        }
        if getattr(args, "json", False):
            safe_print(json.dumps(payload, sort_keys=True))
        else:
            safe_error(f"{exc.diagnostic_id}: {exc.message}")
            safe_error(f"  hint: {exc.hint}")
        return 1

    payload = state.to_dict()
    payload["command"] = "guide profile"
    payload["action"] = action
    safe_print(json.dumps(payload, sort_keys=True) if args.json else render_profile_text(state))
    return 0


def handle_proof_command(args) -> int:
    from .proof import ProofDiagnostic

    try:
        import json
        from .proof import (
            inspect_receipt,
            render_inspection,
            render_verification,
            verify_receipt,
        )

        command = getattr(args, 'proof_cmd', None)
        receipt = getattr(args, 'receipt', None)
        if command == 'verify':
            result = verify_receipt(receipt)
            if getattr(args, 'json', False):
                print(json.dumps(result, indent=2, sort_keys=True))
            else:
                safe_print(render_verification(result))
            return 0
        if command == 'inspect':
            result = inspect_receipt(receipt)
            if getattr(args, 'json', False):
                print(json.dumps(result, indent=2, sort_keys=True))
            else:
                safe_print(render_inspection(result))
            return 0 if result.get('status') == 'valid' else 1
        safe_print("[ERROR] Missing Proof command. Try: sona proof --help")
        return 1
    except ProofDiagnostic as diagnostic:
        if getattr(args, 'json', False):
            print(json.dumps({"status": "invalid", "diagnostic": diagnostic.to_dict()}, indent=2, sort_keys=True))
        else:
            safe_print(str(diagnostic))
        return 1
    except Exception as e:  # pragma: no cover
        safe_print(f"[ERROR] proof command error: {e}")
        return 1


def _render_guardian_workflow(command: str, result: dict) -> str:
    """Render the canonical Guardian workflow without changing JSON contracts."""
    lines = ["Sona Guardian", ""]
    status = str(result.get('status', 'unknown'))
    if command == 'init':
        label = 'READY' if status in {'initialized', 'already-initialized'} else status.upper()
        lines.append(f"State          {label}")
        lines.append(f"Baseline       {result.get('snapshot_id') or 'not available'}")
    elif command == 'explain':
        lines.append(f"State          {str(result.get('guardian_status', status)).upper()}")
    else:
        lines.append(f"State          {status.upper()}")
        proof = result.get('proof_mode', {})
        lines.append(f"Proof Mode     {'READY' if proof.get('ready') else 'NOT READY'}")
    policy_hash = result.get('policy_sha256') or result.get('policy', {}).get('policy_sha256')
    if policy_hash:
        lines.append(f"Policy         {policy_hash}")
    decisions = result.get('capability_decisions', [])
    if decisions:
        lines.extend(["", "Capabilities"])
        for decision in decisions:
            lines.append(
                f"- {decision.get('capability', 'unknown'):<14} "
                f"{str(decision.get('decision', 'unknown')).upper()}"
            )
    message = result.get('message')
    if message:
        lines.extend(["", str(message)])
    warnings = result.get('warnings', [])
    if warnings:
        lines.extend(["", "Warnings"])
        lines.extend(f"- {warning}" for warning in warnings)
    next_step = result.get('next_step') or result.get('hint')
    if next_step:
        lines.extend(["", f"Next: {next_step}"])
    return "\n".join(lines)


def handle_guard_command(args) -> int:
    try:
        import json
        from .stdlib import native_guardian as guardian
        from sona.developer_intelligence.redaction import redact

        command = getattr(args, 'guard_cmd', None)
        project_root = getattr(args, 'project_root', None)
        if not command:
            safe_print("[ERROR] Missing Guardian command. Try: sona guard --help")
            return 1

        authorization = None
        if command in {'rollback', 'heal', 'repair'} and bool(getattr(args, 'apply', False)):
            from sona.developer_intelligence.governance import append_audit, authorize_mutation, load_policy
            authorization_root = Path(project_root or '.').resolve()
            policy, source = load_policy(authorization_root)
            authorization = authorize_mutation(
                policy, source=source, task_type=f'guardian_{command}',
                capabilities=('write_workspace', 'execute_code'),
                approval_granted=bool(getattr(args, 'approve', False)),
                approval_scope=f'guardian:{command}:{authorization_root}',
            )
            append_audit(authorization_root, authorization)

        if command == 'init':
            result = guardian.guardian_init(project_root)
        elif command == 'status':
            result = guardian.guardian_status(project_root)
        elif command == 'verify':
            result = guardian.guardian_verify(
                project_root,
                run_validation=getattr(args, 'run_validation', False),
            )
        elif command == 'check':
            result = guardian.guardian_check(project_root)
        elif command == 'explain':
            result = guardian.guardian_explain(project_root)
        elif command == 'doctor':
            result = guardian.guardian_doctor(project_root)
        elif command == 'snapshot':
            result = guardian.guardian_snapshot(project_root, getattr(args, 'name', None))
        elif command == 'diff':
            result = guardian.guardian_diff(project_root)
        elif command == 'quarantine':
            result = guardian.guardian_quarantine(
                project_root,
                list(getattr(args, 'paths', []) or []),
                getattr(args, 'reason', 'manual'),
            )
        elif command == 'rollback':
            apply = bool(getattr(args, 'apply', False))
            result = guardian.guardian_rollback(
                project_root, getattr(args, 'snapshot_id', None),
                dry_run=not apply, approved=bool(getattr(args, 'approve', False)),
                authorization=authorization,
            )
        elif command in {'heal', 'repair'}:
            result = guardian.guardian_heal(
                project_root, apply=getattr(args, 'apply', False),
                approved=bool(getattr(args, 'approve', False)),
                authorization=authorization,
            )
        elif command == 'graph':
            result = guardian.guardian_graph(project_root)
        elif command in {'audit', 'history'}:
            result = guardian.guardian_audit_history(project_root, getattr(args, 'limit', 50))
        elif command == 'proof':
            proof_command = getattr(args, 'guardian_proof_cmd', None)
            if proof_command == 'verify':
                result = guardian.guardian_proof_verify(project_root, getattr(args, 'receipt', None))
            elif proof_command == 'attest':
                result = guardian.guardian_proof_attest(project_root, getattr(args, 'receipt', None))
            elif proof_command == 'review':
                result = guardian.guardian_proof_review(
                    project_root,
                    getattr(args, 'receipt', None),
                    getattr(args, 'provider', None),
                    getattr(args, 'model', None),
                    getattr(args, 'allow_network', False),
                )
            elif proof_command == 'history':
                result = guardian.guardian_proof_history(project_root, getattr(args, 'limit', 50))
            else:
                safe_print("[ERROR] Missing Guardian Proof command. Try: sona guardian proof --help")
                return 1
        elif command == 'report':
            if getattr(args, 'json', False):
                result = guardian.guardian_report_json(project_root)
            else:
                safe_print(guardian.guardian_report_plain(project_root))
                return 0
        else:
            safe_print(f"[ERROR] Unknown Guardian command: {command}")
            return 1

        clean_result = redact(result)
        output_format = getattr(args, 'format', 'json')
        if output_format == 'auto':
            output_format = 'text' if sys.stdout.isatty() else 'json'
        if output_format == 'text' and isinstance(clean_result, dict) and command in {'init', 'check', 'explain'}:
            print(_render_guardian_workflow(command, clean_result))
        else:
            print(json.dumps(clean_result, indent=2, sort_keys=True))
        status = result.get('status') if isinstance(result, dict) else None
        failed_statuses = {
            'denied', 'failed', 'blocked', 'approval-required', 'rejected',
            'review-unavailable', 'invalid-project-root', 'invalid-config',
            'invalid-state', 'state-write-denied',
        }
        if command == 'check' and status in {'drift', 'uninitialized'}:
            return 1
        if command == 'explain' and result.get('guardian_status') in {'drift', 'uninitialized'}:
            return 1
        return 1 if status in failed_statuses else 0
    except Exception as error:  # pragma: no cover
        failure = (
            error.as_result()
            if callable(getattr(error, 'as_result', None))
            else {
                "schema_version": 1,
                "status": "failed",
                "diagnostic_id": "SONA-GUARD-900",
                "message": "Guardian command failed safely.",
                "hint": "Run `sona guardian check` and review project-local Guardian configuration and state.",
            }
        )
        safe_print(json.dumps(failure, indent=2, sort_keys=True))
        return 1


def handle_doctor_command(_args) -> int:
    # Summarize subsystem readiness
    try:
        import json
        from .flags import get_flags
        from .persisted_env import (
            get_ai_mode_config_path,
            load_ai_mode_preferences,
        )
        try:
            from .policy import policy_snapshot as _policy_snapshot
        except Exception as policy_error:
            error_msg = str(policy_error)

            def _policy_snapshot() -> dict:
                return {"status": "unavailable", "error": error_msg}
        policy_snapshot = _policy_snapshot

        flags = get_flags()
        prefs = load_ai_mode_preferences()
        config_path = get_ai_mode_config_path()
        diag = {
            "type": "doctor",
            "version": 1,
            "flags": flags.__dict__,
            "policy": policy_snapshot(),
            "ai_mode": {
                "persisted": prefs,
                "config_path": str(config_path),
                "session_env": {
                    "SONA_ENABLE_CACHE": os.getenv("SONA_ENABLE_CACHE"),
                    "SONA_ENABLE_BREAKER": os.getenv("SONA_ENABLE_BREAKER"),
                },
            },
        }

        try:
            from .ai.local_models import ensure_local_model
            diag["local_ai"] = ensure_local_model(quiet=True)
        except Exception as ai_error:
            diag["local_ai"] = {
                "status": "error",
                "error": str(ai_error),
            }

        # Optional subsystems
        try:
            from .ai.cache import get_cache  # noqa: WPS433
            cache = get_cache()
            diag["cache"] = cache.stats() if cache else {"enabled": False}
        except ImportError:
            diag["cache"] = {"enabled": False, "error": "Import failed"}

        try:
            from .ai.retry import get_breaker  # noqa: WPS433
            breaker = get_breaker()
            diag["breaker"] = (
                breaker.snapshot() if breaker else {"enabled": False}
            )
        except ImportError:
            diag["breaker"] = {"enabled": False, "error": "Import failed"}

        # Add stdlib health check
        safe_print("\n[DOCTOR] Sona Doctor - System Health Check")
        safe_print("=" * 50)
        try:
            from .stdlib_cli_commands import stdlib_doctor_check
            stdlib_doctor_check()
        except Exception as stdlib_err:
            safe_print(f"  [WARN]  Stdlib: Health check unavailable ({stdlib_err})")

        safe_print("\n[INFO] Detailed Diagnostics:")
        ai_diag = diag.get("local_ai", {})
        safe_print("\n[AI] Offline Model Readiness:")
        if ai_diag.get("status") == "ready":
            safe_print(
                f"  Model {ai_diag.get('model')} available on {ai_diag.get('ollama_host')}"
            )
        else:
            safe_print(f"  Status: {ai_diag.get('status', 'unknown')}")
            if ai_diag.get('error'):
                safe_print(f"  Hint: {ai_diag['error']}")
        def _pref_label(value):
            if value is None:
                return "unset"
            return "on" if value else "off"

        safe_print("\n[AI] Runtime Features:")
        safe_print(f"  Cache enabled: {flags.enable_cache}")
        safe_print(f"  Breaker enabled: {flags.enable_breaker}")
        if flags.enable_cache and flags.enable_breaker:
            safe_print("  Hint: Use 'sona ai-mode disable' to revert when needed.")
        else:
            safe_print("  Hint: Run 'sona ai-mode enable --persist' to turn both on once the model is ready.")

        if prefs:
            safe_print(
                "  Persisted defaults ({path}): cache={cache}, breaker={breaker}".format(
                    path=config_path,
                    cache=_pref_label(prefs.get("enable_cache")),
                    breaker=_pref_label(prefs.get("enable_breaker")),
                )
            )
        else:
            safe_print(f"  Persisted defaults: not set (target {config_path})")

        cache_env = os.getenv("SONA_ENABLE_CACHE")
        breaker_env = os.getenv("SONA_ENABLE_BREAKER")
        if cache_env or breaker_env:
            safe_print("  Session overrides:")
            if cache_env:
                safe_print(f"    SONA_ENABLE_CACHE={cache_env}")
            if breaker_env:
                safe_print(f"    SONA_ENABLE_BREAKER={breaker_env}")

        print(json.dumps(diag, indent=2))
        return 0
    except Exception as e:  # pragma: no cover
        safe_print(f"[ERROR] doctor error: {e}")
        return 1


def handle_build_info_command(_args) -> int:
    try:
        import json
        from .flags import get_flags
        from .persisted_env import (
            get_ai_mode_config_path,
            load_ai_mode_preferences,
        )

        flags = get_flags()
        prefs = load_ai_mode_preferences()
        config_path = get_ai_mode_config_path()
        info = {
            "version": SONA_VERSION,
            "features": flags.__dict__,
        }

        info["ai_mode"] = {
            "cache_enabled": flags.enable_cache,
            "breaker_enabled": flags.enable_breaker,
            "persisted_defaults": prefs or {},
            "config_path": str(config_path),
            "session_env": {
                "SONA_ENABLE_CACHE": os.getenv("SONA_ENABLE_CACHE"),
                "SONA_ENABLE_BREAKER": os.getenv("SONA_ENABLE_BREAKER"),
            },
            "hint": (
                "sona ai-mode disable"
                if flags.enable_cache and flags.enable_breaker
                else "sona ai-mode enable --persist"
            ),
        }

        # Try to get cache info
        try:
            from .ai.cache import get_cache
            cache = get_cache()
            info["cache"] = cache.stats() if cache else {"enabled": False}
        except ImportError:
            info["cache"] = {"enabled": False, "error": "Import failed"}

        # Try to get breaker info
        try:
            from .ai.retry import get_breaker
            breaker = get_breaker()
            info["breaker"] = (
                breaker.snapshot() if breaker else {"enabled": False}
            )
        except ImportError:
            info["breaker"] = {"enabled": False, "error": "Import failed"}

        # Add stdlib metadata
        try:
            from .stdlib_cli_commands import stdlib_build_info
            info["stdlib"] = stdlib_build_info()
        except Exception:
            info["stdlib"] = {"status": "unavailable"}

        print(json.dumps(info, indent=2))
        return 0
    except Exception as e:  # pragma: no cover
        safe_print(f"[ERROR] build-info error: {e}")
        return 1


def handle_perf_log_command(args) -> int:
    """Emit a single performance log event then close file.

    Closing ensures the file is flushed so users can inspect immediately.
    """
    try:
        from .flags import refresh_flags
        from .perf.logging import log_perf, close_logs
        flags = refresh_flags()  # pick up any env changes
        if not flags.perf_logs:
            safe_print(
                "[INFO] Perf logging disabled (set SONA_PERF_LOGS=1). "
                "No file written."
            )
            return 0
        extra = {}
        for item in getattr(args, 'field', []) or []:
            if '=' in item:
                k, v = item.split('=', 1)
                extra[k.strip()] = v.strip()
        if args.ms:
            extra['ms'] = args.ms
        log_perf(args.event, **extra)
        close_logs()  # flush/close so file appears immediately
        safe_print(f"[OK] Perf event '{args.event}' logged to {flags.perf_dir or '.'}")
        return 0
    except Exception as e:  # pragma: no cover
        safe_print(f"[ERROR] perf-log error: {e}")
        return 1


def handle_lock_command(args) -> int:
    """Handle 'sona lock' command - generate or verify lockfile"""
    from pathlib import Path

    try:
        # Import lockfile management functions
        from .lockfile_manager import generate_lockfile, verify_lockfile

        # Determine workspace directory (current directory)
        workspace_dir = Path.cwd()

        if getattr(args, 'verify', False):
            # Verify existing lockfile
            print("[LOCK] Verifying sona.lock.json...")
            success = verify_lockfile(workspace_dir)
            if success:
                print("[SUCCESS] Lockfile verification successful - workspace matches")
                return 0
            else:
                print("[FAILED] Lockfile verification failed - workspace differs")
                return 1
        else:
            # Generate new lockfile
            print("[LOCK] Generating sona.lock.json...")
            success = generate_lockfile(workspace_dir)
            if success:
                print("[SUCCESS] Generated sona.lock.json with module checksums")
                return 0
            else:
                print("[FAILED] Failed to generate lockfile")
                return 1

    except Exception as e:
        print(f"[ERROR] Lock command error: {e}")
        return 1


def handle_verify_command(args) -> int:
    """Handle 'sona verify' command - verify lockfile integrity"""
    from pathlib import Path

    try:
        # Import lockfile management functions
        from .lockfile_manager import verify_lockfile

        # Determine workspace directory (current directory)
        workspace_dir = Path.cwd()

        print("[VERIFY] Verifying sona.lock.json...")
        success = verify_lockfile(workspace_dir)
        if success:
            print("[SUCCESS] Lockfile verification successful - workspace matches")
            return 0
        else:
            print("[FAILED] Lockfile verification failed - workspace differs")
            return 1

    except Exception as e:
        print(f"[ERROR] Verify command error: {e}")
        return 1


def main() -> int:
    """Main CLI entry point"""
    proof_arguments = _proof_generation_arguments(sys.argv)
    if proof_arguments is not None:
        return _delegate_native_proof(proof_arguments)

    # Keep package management on one implementation path. The ``spm``
    # console script and ``sona pkg`` both use the hardened local-only parser
    # and transaction engine instead of maintaining two command surfaces.
    if len(sys.argv) > 1 and sys.argv[1] == 'pkg':
        from .spm import main as spm_main

        return spm_main(sys.argv[2:], prog='sona pkg')

    direct_result = _handle_direct_file_invocation(sys.argv)
    if direct_result is not None:
        return direct_result

    parser = create_argument_parser()

    # Handle case where no arguments are provided
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        return 1

    # Parse arguments first to check for global options
    args = parser.parse_args()

    # Handle global --types-status first (before any command processing)
    if hasattr(args, 'types_status') and args.types_status:
        return handle_types_status(args)

    # Handle commands
    if args.command == 'run' or args.command is None:
        return handle_run_command(args)

    elif args.command == 'demo':
        return handle_demo_command(args)

    elif args.command == 'ai-model':
        return handle_ai_model_command(args)

    elif args.command == 'ai':
        if getattr(args, 'ai_cmd', None) == 'task':
            return handle_ai_task_command(args)
        safe_error("[ERROR] Missing AI command. Try: sona ai task --help")
        return 1

    elif args.command == 'model':
        return handle_model_command(args)

    elif args.command == 'govern':
        return handle_govern_command(args)

    elif args.command == 'ai-mode':
        return handle_ai_mode_command(args)
    elif args.command == 'lock':
        return handle_lock_command(args)

    elif args.command == 'verify':
        return handle_verify_command(args)

    elif args.command == 'info':
        return handle_info_command(args)

    elif args.command == 'setup':
        if args.setup_cmd == 'azure':
            try:
                from .setup_azure import setup_azure
            except Exception as e:
                safe_print(f"[ERROR] Failed to load Azure setup: {e}")
                return 1
            # Ensure workspace defaults to CWD when not provided
            workspace_dir = args.workspace or os.getcwd()
            manual_mode = getattr(args, 'manual', False)
            code = setup_azure(
                dry_run=getattr(args, 'dry_run', False),
                workspace_dir=workspace_dir,
                manual_mode=manual_mode,
                write_env_secret=getattr(args, 'write_env_secret', False),
            )
            return code
        elif args.setup_cmd == 'manual':
            try:
                from .setup_azure import setup_azure
            except Exception as e:
                safe_print(f"[ERROR] Failed to load setup: {e}")
                return 1
            workspace_dir = args.workspace or os.getcwd()
            code = setup_azure(
                dry_run=getattr(args, 'dry_run', False),
                workspace_dir=workspace_dir,
                manual_mode=True,
                write_env_secret=getattr(args, 'write_env_secret', False),
            )
            return code
        else:
            safe_print("[ERROR] Missing or unknown setup target. Try:")
            safe_print("   sona setup azure   (with Azure CLI)")
            safe_print("   sona setup manual  (manual entry)")
            return 1

    elif args.command == 'check':
        return handle_check_command(args)

    elif args.command == 'format':
        return handle_format_command(args)

    elif args.command == 'transpile':
        return handle_transpile_command(args)

    elif args.command == 'repl':
        return handle_repl_command(args)

    elif args.command in ('profile', 'benchmark', 'suggest', 'explain'):
        return handle_enhanced_command(args.command, args)

    elif args.command == 'keys':
        return handle_keys_command(args)
    elif args.command == 'ai-plan':
        return handle_ai_plan_command(args)
    elif args.command == 'ai-review':
        return handle_ai_review_command(args)
    elif args.command == 'probe':
        return handle_probe_command(args)
    elif args.command == 'proof':
        return handle_proof_command(args)
    elif args.command == 'why':
        return handle_why_command(args)
    elif args.command == 'fix':
        return handle_fix_command(args)
    elif args.command == 'focus':
        return handle_focus_command(args)
    elif args.command == 'guide':
        return handle_guide_command(args)
    elif args.command in {'examples', 'learn'}:
        from .learning_cli import handle_learning_command
        return handle_learning_command(args)
    elif args.command in {'guard', 'guardian'}:
        return handle_guard_command(args)
    elif args.command == 'doctor':
        return handle_doctor_command(args)
    elif args.command == 'build-info':
        return handle_build_info_command(args)

    elif args.command == 'pkg':
        if getattr(args, 'pkg_cmd', None) == 'init':
            try:
                from .spm import init_project
                from pathlib import Path
            except Exception as e:
                safe_print(f"[ERROR] Package tooling unavailable: {e}")
                return 1

            try:
                path = init_project(Path.cwd(), name=getattr(args, 'name', None), version=getattr(args, 'version', SONA_VERSION))
            except Exception as e:
                safe_print(f"[ERROR] Failed to init manifest: {e}")
                return 1
            safe_print(f"[OK] Initialized {path}")
            return 0

        safe_print("[ERROR] Missing or unknown pkg command. Try: sona pkg init")
        return 1
    elif args.command == 'perf-log':
        return handle_perf_log_command(args)

    elif (
        isinstance(ENHANCED_COMMANDS, dict)
        and args.command in ENHANCED_COMMANDS
    ):
        return handle_enhanced_command(args.command, args)

    else:
        safe_print(f"[ERROR] Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

