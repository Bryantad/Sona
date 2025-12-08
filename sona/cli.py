"""
Sona v0.9.6 Command Line Interface with AI Integration

Enhanced CLI with profile, benchmark, suggest, and explain commands
powered by GPT-2 and cognitive assistance features.
"""

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

# Import type configuration
from .type_config import configure_types, get_type_logger, get_type_config


# Win UTF-8 guard - safer version that doesn't interfere with I/O operations
if sys.platform == "win32":  # pragma: no cover - platform specific
    try:
        import ctypes  # type: ignore
        # Just set the console code page, don't rewrap stdout/stderr
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
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


def _load_default_interpreter():
    """Instantiate the preferred interpreter with graceful fallback."""
    # Try advanced interpreter first for richer cognitive features
    try:
        from test_advanced_cognitive_functions import (
            AdvancedSonaInterpreter,
        )
        _update_interpreter_status("advanced", message=None, fallback_reason=None, hint=None)
        safe_print("[INFO] Advanced Sona interpreter enabled")
        return AdvancedSonaInterpreter()
    except Exception as advanced_error:
        fallback_reason = _summarize_interpreter_error(advanced_error)
        _update_interpreter_status(
            "core",
            fallback_reason=fallback_reason,
            hint='Install optional extras via: python -m pip install "sona-lang[advanced]"',
            message=(
                "[INFO] Core runtime active. Advanced interpreter is optional "
                "and can be enabled when the cognitive bundle is installed."
            ),
            announce=True,
        )
        try:
            from sona.interpreter import SonaInterpreter
            return SonaInterpreter()
        except Exception as core_error:  # pragma: no cover - defensive
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
            '\U0001f680': '[ROCKET]',  # 🚀
            '\u2705': '[OK]',          # ✅
            '\u274c': '[ERROR]',       # ❌
            '\U0001f916': '[AI]',      # 🤖
            '\U0001f4d6': '[INFO]',    # 📖
            '\U0001f50d': '[DEBUG]',   # 🔍
            '\U0001f504': '[INFO]',    # 🔄
            '\u26a0\ufe0f': '[WARN]',  # ⚠️
            '\u26a0': '[WARN]',        # ⚠
            '\U0001f44b': '[BYE]',     # 👋
            '\U0001f3e5': '[INFO]',    # 🏥
            '\U0001f4ca': '[INFO]',    # 📊
            '\u2139\ufe0f': '[INFO]',  # ℹ️
            '\u2139': '[INFO]',        # ℹ
        }
        for emoji, replacement in replacements.items():
            text = text.replace(emoji, replacement)
        # Final fallback: replace any remaining non-ASCII
        text = text.encode('ascii', 'replace').decode('ascii')
        print(text, **kwargs)


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
        f"statements: {stats.statements} (python blocks: {stats.python_blocks}, inline python: {stats.python_invocations})",
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


def read_text_safe(path: str) -> str:
    """Robust text loader with multi-encoding fallback.

    Tries common encodings; last resort returns replacement-decoded UTF-8.
    """
    p = Path(path)
    for enc in ("utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            return p.read_text(encoding=enc)
        except UnicodeError:
            continue
        except FileNotFoundError:
            raise
        except Exception:
            continue
    return p.read_text(encoding="utf-8", errors="replace")


def execute_sona(
    code: str,
    safe_mode: bool = False,
    file_path: str | None = None,
) -> any:
    """Execute Sona code using the default interpreter"""
    global default_interpreter
    if default_interpreter is None:
        default_interpreter = _load_default_interpreter()
    interpreter = default_interpreter
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

    for python_block in python_blocks:
        try:
            compiled = compile(python_block, file_path or '<embedded>', 'exec')
            exec(compiled, exec_globals, exec_globals)
        except Exception as e:
            safe_print(f"[ERROR] Python block execution error: {e}")

    # Now execute remaining (Sona) lines
    lines = '\n'.join(remaining_lines).strip().split('\n') if remaining_lines else []
    result = None
    executed_statements = 0
    python_invocations = 0
    start_time = perf_counter()

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue

        # Simple detection: contains '(' and a known function name
        is_python = False
        for name, obj in exec_globals.items():
            if callable(obj) and name in line and '(' in line:
                is_python = True
                break

        if is_python:
            try:
                exec(line, exec_globals, exec_globals)
            except TypeCheckAbort:
                raise
            except Exception as e:
                safe_print(f"[ERROR] Python exec error: {e}")
            executed_statements += 1
            python_invocations += 1
            continue

        try:
            result = interpreter.interpret(line)
            if result is not None:
                result = _to_str_safe(result)
        except Exception as e:
            safe_print(f"[ERROR] Interpretation error: {e}")
        executed_statements += 1

    end_time = perf_counter()
    stats.result = result
    stats.statements = executed_statements
    stats.python_invocations = python_invocations
    stats.duration_ms = max(0.0, (end_time - start_time) * 1000)
    stats.interpreter_name = interpreter.__class__.__name__
    snapshot = _snapshot_interpreter_status()
    stats.interpreter_variant = snapshot.get('variant') or stats.interpreter_name
    stats.fallback_reason = snapshot.get('fallback_reason')
    stats.interpreter_hint = snapshot.get('hint')

    return stats


def _extract_python_blocks(code: str):
    """Enhanced Python block extraction with multi-decorator support"""
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
                i = body_end
                continue

        # Not a Python block line - add to remaining
        remaining_lines.append(line)
        i += 1

    return python_blocks, remaining_lines


ENHANCED_COMMANDS = None  # lazy-loaded mapping


# Version information
SONA_VERSION = "0.9.8"
AI_FEATURES_VERSION = "1.0.0"
DEFAULT_OFFLINE_MODEL = "qwen2.5-coder:7b"


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
    parser = argparse.ArgumentParser(
        prog='sona',
        description='Sona Cognitive Programming Language v0.9.8',
        epilog='For more information, visit: https://github.com/Bryantad/Sona'
    )

    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'Sona {SONA_VERSION} (AI Features {AI_FEATURES_VERSION})'
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

    # Run command (default)
    run_parser = subparsers.add_parser('run', help='Execute a Sona file')
    run_parser.add_argument('file', help='Sona file to execute')
    run_parser.add_argument(
        '--safe',
        action='store_true',
        help='Enable safe mode',
    )
    run_parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output',
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

    # Info command
    info_parser = subparsers.add_parser('info', help='Show system information')

    # Check command
    check_parser = subparsers.add_parser('check', help='Check Sona syntax')
    check_parser.add_argument('file', help='Sona file to check')
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
        choices=['stdlib'],
        help='Probe target (stdlib for standard library inspection)'
    )
    probe_parser.add_argument(
        '--text', help='Optional inline text to scan', default=''
    )

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

    # Import here to avoid circular imports
    from sona.type_system.runtime_checker import TypeCheckAbort

    if not Path(args.file).exists():
        safe_print(f"[ERROR] File '{args.file}' not found.")
        return 1

    exit_code = 0
    logger = None
    execution = None
    type_stats = {'errors': 0, 'warnings': 0}

    try:
        # Configure type checking based on CLI argument
        if hasattr(args, 'types'):
            configure_types(cli_mode=args.types)
            logger = get_type_logger()

        code = read_text_safe(args.file)

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
        )

        if args.debug:
            safe_print("=" * 50)
            safe_print(f"[OK] Execution completed. Result: {execution.result}")

    except TypeCheckAbort:
        # Type checking failure in ON mode - exit code handled below
        pass
    except Exception as e:
        safe_print(f"[ERROR] Execution error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
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
            from sona.ai.gpt2_integration import get_gpt2_instance
            get_gpt2_instance()
            safe_print("   [OK] GPT-2 Integration: Available")
            safe_print("   [OK] Code Completion: Available")
            safe_print("   [OK] Cognitive Assistant: Available")
            safe_print("   [OK] Natural Language Processing: Available")
        except ImportError:
            safe_print("   [ERROR] AI Features: Not available (missing dependencies)")
        except Exception as e:
            safe_print(f"   [WARN] AI Features: Error ({e})")

    safe_print("\n[HELP] Commands:")
    safe_print("   run       - Execute Sona code")
    safe_print("   profile   - Profile code execution")
    safe_print("   benchmark - Performance benchmarking")
    safe_print("   suggest   - AI code suggestions")
    safe_print("   explain   - AI code explanations")
    safe_print("   info      - System information")

    return 0


def handle_check_command(args) -> int:
    """Handle the check command"""
    if not Path(args.file).exists():
        safe_print(f"[ERROR] File '{args.file}' not found.")
        return 1

    try:
        code = read_text_safe(args.file)

        # Basic syntax checking - try to parse each line
        lines = code.strip().split('\n')
        errors = 0

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                # Basic syntax checks
                if '=' in line and not line.startswith('let '):
                    safe_print(f"[ERROR] Line {i}: Assignment should use 'let' keyword")
                    errors += 1

        if errors == 0:
            safe_print(f"[OK] Syntax check passed for {args.file}")
            return 0
        else:
            safe_print(f"[ERROR] Found {errors} syntax errors")
            return 1

    except Exception as e:
        safe_print(f"[ERROR] Check error: {e}")
        return 1


def handle_format_command(args) -> int:
    """Handle the format command"""
    if not Path(args.file).exists():
        safe_print(f"[ERROR] File '{args.file}' not found.")
        return 1

    try:
        code = read_text_safe(args.file)

        # Basic formatting - ensure proper spacing
        lines = code.strip().split('\n')
        formatted_lines = []

        for line in lines:
            line = line.strip()
            if line:
                # Add consistent spacing around operators
                if '=' in line and 'let ' in line:
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        line = f"{parts[0].strip()} = {parts[1].strip()}"
                formatted_lines.append(line)

        # Write back formatted code
        with open(args.file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(formatted_lines) + '\n')

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
        return 1

    try:
        code = read_text_safe(args.file)

        # Basic transpilation to Python
        lines = code.strip().split('\n')
        python_lines = []

        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Convert Sona syntax to Python
                if line.startswith('let '):
                    # let x = 5 -> x = 5
                    python_lines.append(line[4:])
                elif line.startswith('print('):
                    python_lines.append(line)
                else:
                    python_lines.append(f"# {line}")  # Comment unknown syntax

        # Determine output file
        output_file = (
            args.output
            if args.output
            else args.file.replace('.sona', '.py')
        )

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(python_lines) + '\n')

        safe_print(f"[OK] Transpiled {args.file} to {output_file}")
        return 0

    except Exception as e:
        safe_print(f"[ERROR] Transpile error: {e}")
        return 1


def handle_repl_command(args) -> int:
    """Handle the repl command"""
    safe_print("[INFO] Starting Sona REPL...")

    try:
        from test_advanced_cognitive_functions import AdvancedSonaInterpreter
        interpreter = AdvancedSonaInterpreter()

        safe_print("Sona REPL v0.9.8 - Type 'exit' to quit")
        if args.ai:
            safe_print("[AI] AI assistance enabled")

        while True:
            try:
                user_input = input("sona> ")
                if user_input.strip().lower() in ['exit', 'quit']:
                    break

                if user_input.strip():
                    result = interpreter.interpret(user_input)
                    if result is not None:
                        safe_print(f"=> {result}")

            except KeyboardInterrupt:
                safe_print("\n[BYE] Goodbye!")
                break
            except EOFError:
                break

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
        elif command == 'explain' and hasattr(args, 'style'):
            arg_list.extend(['--style', args.style])

        cmds[command](arg_list)  # type: ignore[index]
        return 0
    except Exception as e:  # pragma: no cover - defensive
        safe_print(f"[ERROR] Command failed: {e}")
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
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
            from stdlib_cli_commands import stdlib_probe
            return stdlib_probe()
        except Exception as e:
            safe_print(f"[ERROR] stdlib probe error: {e}")
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
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
            from stdlib_cli_commands import stdlib_doctor_check
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
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
            from stdlib_cli_commands import stdlib_build_info
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
    parser = create_argument_parser()

    # Parse arguments first to check for global options
    args = parser.parse_args()

    # Handle global --types-status first (before any command processing)
    if hasattr(args, 'types_status') and args.types_status:
        return handle_types_status(args)

    # Handle case where no arguments are provided
    if len(sys.argv) == 1:
        safe_print("[SONA] Sona Cognitive Programming Language v0.9.8")
        safe_print("\nUsage: sona <command> [options]")
        safe_print("\nCommands:")
        safe_print("  run <file>       Execute a Sona file")
        safe_print("  profile <file>   Profile code execution")
        safe_print("  benchmark <file> Benchmark performance")
        safe_print("  suggest <file>   Get AI suggestions")
        safe_print("  explain <file>   Get AI explanations")
        safe_print("  lock             Generate sona.lock.json")
        safe_print("  verify           Verify sona.lock.json")
        safe_print("  demo             Run the built-in feature demo")
        safe_print("  ai-model         Manage offline AI models")
        safe_print("  ai-mode          Enable cache/breaker for local AI")
        safe_print("  info             Show system info")
        safe_print("\nUse 'sona <command> --help' for more information.")
        return 0

    # Handle direct file execution (legacy mode)
    if (
        len(sys.argv) == 2
        and not sys.argv[1].startswith('-')
        and sys.argv[1] not in [
            'run', 'profile', 'benchmark', 'suggest', 'explain', 'info',
            'ai-plan', 'ai-review', 'probe', 'doctor', 'build-info',
            'help', 'version', 'repl', 'check', 'format', 'transpile', 'keys',
            'lock', 'verify', 'demo', 'ai-model', 'ai-mode'
        ]
    ):
        # Treat as direct file execution
        class DirectArgs:
            file = sys.argv[1]
            safe = False
            debug = False

        return handle_run_command(DirectArgs())

    # Handle commands
    if args.command == 'run' or args.command is None:
        return handle_run_command(args)

    elif args.command == 'demo':
        return handle_demo_command(args)

    elif args.command == 'ai-model':
        return handle_ai_model_command(args)

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
                manual_mode=manual_mode
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
                manual_mode=True
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

    elif args.command == 'keys':
        return handle_keys_command(args)
    elif args.command == 'ai-plan':
        return handle_ai_plan_command(args)
    elif args.command == 'ai-review':
        return handle_ai_review_command(args)
    elif args.command == 'probe':
        return handle_probe_command(args)
    elif args.command == 'doctor':
        return handle_doctor_command(args)
    elif args.command == 'build-info':
        return handle_build_info_command(args)
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
