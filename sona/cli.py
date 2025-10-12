"""
Sona v0.9.6 Command Line Interface with AI Integration

Enhanced CLI with profile, benchmark, suggest, and explain commands
powered by GPT-2 and cognitive assistance features.
"""

import argparse
import os
import sys
from pathlib import Path

# Import type configuration
from .type_config import configure_types, get_type_logger


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
        try:
            from test_advanced_cognitive_functions import (
                AdvancedSonaInterpreter,
            )
            default_interpreter = AdvancedSonaInterpreter()
        except Exception as e:  # pragma: no cover - defensive
            raise RuntimeError(f"Interpreter unavailable: {e}")
    interpreter = default_interpreter
    
    # Support embedded Python functions with @check_types decorator.
    # Enhanced Python block extraction with multi-decorator support
    from sona.type_system.runtime_checker import check_types
    
    python_blocks, remaining_lines = _extract_python_blocks(code)
    
    # Execute collected python blocks if any
    from sona.type_config import get_type_config
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
            print(f"❌ Python block execution error: {e}")

    # Now execute remaining (Sona) lines
    if remaining_lines:
        lines = '\n'.join(remaining_lines).strip().split('\n')
    else:
        lines = []
    result = None
    
    # Detect assignments or calls referencing defined python functions
    from sona.type_system.runtime_checker import TypeCheckAbort
    
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
                # Type error in ON mode - re-raise to CLI handler
                raise
            except Exception as e:
                print(f"❌ Python exec error: {e}")
            continue
            
        # Fallback to Sona interpreter
        try:
            result = interpreter.interpret(line)
            if result is not None:
                result = _to_str_safe(result)
        except Exception as e:
            print(f"❌ Interpretation error: {e}")
            
    return result


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
SONA_VERSION = "0.9.3"
AI_FEATURES_VERSION = "1.0.0"


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
        description='Sona Cognitive Programming Language v0.9.3',
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
        print(f"❌ Error: File '{args.file}' not found.")
        return 1

    exit_code = 0
    logger = None
    
    try:
        # Configure type checking based on CLI argument
        if hasattr(args, 'types'):
            configure_types(cli_mode=args.types)
            logger = get_type_logger()

        code = read_text_safe(args.file)

        if args.debug:
            print(f"🔍 Executing: {args.file}")
            print(f"Safe mode: {'enabled' if args.safe else 'disabled'}")
            if hasattr(args, 'types'):
                print(f"Type checking: {args.types}")
            print("=" * 50)

        # Execute the code
        result = execute_sona(
            code,
            safe_mode=args.safe,
            file_path=args.file,
        )

        if args.debug:
            print("=" * 50)
            print(f"✅ Execution completed. Result: {result}")

    except TypeCheckAbort:
        # Type checking failure in ON mode - exit code handled below
        pass
    except Exception as e:
        print(f"❌ Execution error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        exit_code = 1
    finally:
        # Emit summary and determine exit code based on --types-log
        if logger and hasattr(args, 'types') and args.types != 'off':
            types_log = getattr(args, 'types_log', 'all')
            
            # Determine if we should show output based on verbosity setting
            should_show_summary = True
            if types_log == 'silent':
                should_show_summary = False
            elif types_log == 'errors':
                # Only show if there are actual errors or warnings
                has_errors = logger._stats.get('errors', 0) > 0
                has_warnings = logger._stats.get('warnings', 0) > 0
                should_show_summary = has_errors or has_warnings
            # 'all' mode always shows summary
            
            if should_show_summary:
                summary = logger.get_summary()
                print(summary, file=sys.stderr)
            
            # Override exit code based on type checking results
            if logger.should_exit_with_error():
                exit_code = 2

    return exit_code


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
    print("🚀 Sona Programming Language")
    print(f"   Version: {SONA_VERSION}")
    print(f"   AI Features: {AI_FEATURES_VERSION}")
    print(f"   Python: {sys.version.split()[0]}")

    if args.ai_status:
        print("\n🤖 AI Feature Status:")
        try:
            from sona.ai.gpt2_integration import get_gpt2_instance
            get_gpt2_instance()
            print("   ✅ GPT-2 Integration: Available")
            print("   ✅ Code Completion: Available")
            print("   ✅ Cognitive Assistant: Available")
            print("   ✅ Natural Language Processing: Available")
        except ImportError:
            print("   ❌ AI Features: Not available (missing dependencies)")
        except Exception as e:
            print(f"   ⚠️ AI Features: Error ({e})")

    print("\n📖 Commands:")
    print("   run       - Execute Sona code")
    print("   profile   - Profile code execution")
    print("   benchmark - Performance benchmarking")
    print("   suggest   - AI code suggestions")
    print("   explain   - AI code explanations")
    print("   info      - System information")

    return 0


def handle_check_command(args) -> int:
    """Handle the check command"""
    if not Path(args.file).exists():
        print(f"❌ Error: File '{args.file}' not found.")
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
                    print(f"❌ Line {i}: Assignment should use 'let' keyword")
                    errors += 1

        if errors == 0:
            print(f"✅ Syntax check passed for {args.file}")
            return 0
        else:
            print(f"❌ Found {errors} syntax errors")
            return 1

    except Exception as e:
        print(f"❌ Check error: {e}")
        return 1


def handle_format_command(args) -> int:
    """Handle the format command"""
    if not Path(args.file).exists():
        print(f"❌ Error: File '{args.file}' not found.")
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

        print(f"✅ Formatted {args.file}")
        return 0

    except Exception as e:
        print(f"❌ Format error: {e}")
        return 1


def handle_transpile_command(args) -> int:
    """Handle the transpile command"""
    if not Path(args.file).exists():
        print(f"❌ Error: File '{args.file}' not found.")
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

        print(f"✅ Transpiled {args.file} to {output_file}")
        return 0

    except Exception as e:
        print(f"❌ Transpile error: {e}")
        return 1


def handle_repl_command(args) -> int:
    """Handle the repl command"""
    print("🔄 Starting Sona REPL...")

    try:
        from test_advanced_cognitive_functions import AdvancedSonaInterpreter
        interpreter = AdvancedSonaInterpreter()

        print("Sona REPL v0.9.2 - Type 'exit' to quit")
        if args.ai:
            print("🤖 AI assistance enabled")

        while True:
            try:
                user_input = input("sona> ")
                if user_input.strip().lower() in ['exit', 'quit']:
                    break

                if user_input.strip():
                    result = interpreter.interpret(user_input)
                    if result is not None:
                        print(f"=> {result}")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                break

        return 0

    except Exception as e:
        print(f"❌ REPL error: {e}")
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
            print(f"❌ Unknown command: {command}")
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
        print(f"❌ Command failed: {e}")
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
        print(f"❌ Secure storage unavailable: {e}")
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
            print(f"✅ Stored credentials for {service}. Key={_mask(api_key)}")
            if endpoint:
                print(f"   Endpoint: {endpoint}")
            return 0
        except Exception as e:
            print(f"❌ Failed to store secret: {e}")
            return 1
    elif cmd == 'get':
        service = args.service
        try:
            value = get_secret(service, 'api_key')
            endpoint = get_secret(service, 'endpoint')
            if value is None and endpoint is None:
                print(f"ℹ️ No stored credentials for {service}")
                return 0
            print(f"Service: {service}")
            print(f"  api_key: {_mask(value)}")
            if endpoint:
                print(f"  endpoint: {endpoint}")
            return 0
        except Exception as e:
            print(f"❌ Failed to retrieve secret: {e}")
            return 1
    elif cmd == 'list':
        try:
            from secure_storage import list_all_services  # local import
            services = list_all_services()
            if not services:
                print("ℹ️ No credentials stored yet")
                return 0
            print("Stored services:")
            for service in sorted(services.keys()):
                keys = list_service_keys(service).keys()
                api_val = get_secret(service, 'api_key')
                mask = _mask(api_val) if api_val else "(no api_key)"
                extra = [k for k in keys if k != 'api_key']
                extras = f" +{len(extra)} other keys" if extra else ""
                print(f"  - {service}: {mask}{extras}")
            return 0
        except Exception as e:
            print(f"❌ Failed to list keys: {e}")
            return 1
    elif cmd == 'migrate':
        try:
            from key_migration import migrate as migrate_keys
        except Exception as e:
            print(f"❌ Migration module unavailable: {e}")
            return 1
        try:
            result = migrate_keys()
            moved = result.get('migrated', 0)
            skipped = result.get('skipped', 0)
            errors = result.get('errors', 0)
            print(
                "✅ Migration complete. "
                f"Migrated={moved} Skipped={skipped} Errors={errors}"
            )
            if errors:
                print("   See migration logs for details.")
            return 0 if errors == 0 else 1
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return 1
    elif cmd == 'rotate':
        service = args.service
        key_name = getattr(args, 'key', 'api_key')
        try:
            new_val = rotate_secret(service, key_name)
            print(f"🔄 Rotated {service}.{key_name}: {_mask(new_val)}")
            return 0
        except Exception as e:
            print(f"❌ Rotation failed: {e}")
            return 1
    else:
        print(
            "❌ Missing or unknown keys subcommand. "
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
        print(f"❌ ai-plan error: {e}")
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
            print(f"❌ File not found: {args.file}")
            return 1
        text = read_text_safe(args.file)
        review = ai_review(text, args.criteria)
        import json
        print(json.dumps(review, indent=2))
        return 0
    except Exception as e:  # pragma: no cover
        print(f"❌ ai-review error: {e}")
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
            print(f"❌ stdlib probe error: {e}")
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
        print(f"❌ probe error: {e}")
        return 1


def handle_doctor_command(_args) -> int:
    # Summarize subsystem readiness
    try:
        import json
        from .flags import get_flags
        from .policy import policy_snapshot

        flags = get_flags()
        diag = {
            "type": "doctor",
            "version": 1,
            "flags": flags.__dict__,
            "policy": policy_snapshot(),
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
        print("\n🏥 Sona Doctor - System Health Check")
        print("=" * 50)
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
            from stdlib_cli_commands import stdlib_doctor_check
            stdlib_doctor_check()
        except Exception as stdlib_err:
            print(f"  ⚠️  Stdlib: Health check unavailable ({stdlib_err})")

        print("\n📊 Detailed Diagnostics:")
        print(json.dumps(diag, indent=2))
        return 0
    except Exception as e:  # pragma: no cover
        print(f"❌ doctor error: {e}")
        return 1


def handle_build_info_command(_args) -> int:
    try:
        import json
        from .flags import get_flags

        flags = get_flags()
        info = {
            "version": SONA_VERSION,
            "features": flags.__dict__,
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
        print(f"❌ build-info error: {e}")
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
            print(
                "ℹ️ Perf logging disabled (set SONA_PERF_LOGS=1). "
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
        print(f"✅ Perf event '{args.event}' logged to {flags.perf_dir or '.'}")
        return 0
    except Exception as e:  # pragma: no cover
        print(f"❌ perf-log error: {e}")
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
        print("🚀 Sona Cognitive Programming Language v0.9.4")
        print("\nUsage: sona <command> [options]")
        print("\nCommands:")
        print("  run <file>       Execute a Sona file")
        print("  profile <file>   Profile code execution")
        print("  benchmark <file> Benchmark performance")
        print("  suggest <file>   Get AI suggestions")
        print("  explain <file>   Get AI explanations")
        print("  lock             Generate sona.lock.json")
        print("  verify           Verify sona.lock.json")
        print("  info             Show system info")
        print("\nUse 'sona <command> --help' for more information.")
        return 0

    # Handle direct file execution (legacy mode)
    if (
        len(sys.argv) == 2
        and not sys.argv[1].startswith('-')
        and sys.argv[1] not in [
            'run', 'profile', 'benchmark', 'suggest', 'explain', 'info',
            'ai-plan', 'ai-review', 'probe', 'doctor', 'build-info',
            'help', 'version', 'repl', 'check', 'format', 'transpile', 'keys',
            'lock', 'verify'
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
                print(f"❌ Failed to load Azure setup: {e}")
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
                print(f"❌ Failed to load setup: {e}")
                return 1
            workspace_dir = args.workspace or os.getcwd()
            code = setup_azure(
                dry_run=getattr(args, 'dry_run', False),
                workspace_dir=workspace_dir,
                manual_mode=True
            )
            return code
        else:
            print("❌ Missing or unknown setup target. Try:")
            print("   sona setup azure   (with Azure CLI)")
            print("   sona setup manual  (manual entry)")
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
        print(f"❌ Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
