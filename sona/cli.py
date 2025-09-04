"""
Sona v0.9.2 Command Line Interface with AI Integration

Enhanced CLI with profile, benchmark, suggest, and explain commands
powered by GPT-2 and cognitive assistance features.
"""

import sys
import os
import argparse
from pathlib import Path
from typing import List, Optional

# Fix UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if os.name == "nt":
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except Exception:
        pass

# Ensure UTF-8 output on Windows (fallback)
if sys.platform == "win32":
    try:
        import io
        import codecs
        # Only wrap if not already wrapped
        if not hasattr(sys.stdout, '_original'):
            sys.stdout._original = sys.stdout
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if not hasattr(sys.stderr, '_original'):
            sys.stderr._original = sys.stderr  
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        # If UTF-8 wrapping fails, continue with default encoding
        pass

# Import Sona core components
from sona.interpreter import default_interpreter

def _to_str_safe(x):
    """Force any value to clean string - final safety net for AI results"""
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
    """Read text from file using UTF-8, fall back to UTF-8-sig, then replace errors."""
    p = Path(path)
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return p.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            return p.read_text(encoding="utf-8", errors="replace")

def execute_sona(code: str, safe_mode: bool = False) -> any:
    """Execute Sona code using the default interpreter"""
    # For now, import our working interpreter
    from test_advanced_cognitive_functions import AdvancedSonaInterpreter
    
    interpreter = AdvancedSonaInterpreter()
    
    # Execute line by line
    lines = code.strip().split('\n')
    result = None
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):  # Skip empty lines and comments
            result = interpreter.interpret(line)
            # Ensure AI results are always clean strings
            if result is not None:
                result = _to_str_safe(result)
    
    return result
from sona.ai.enhanced_cli import ENHANCED_COMMANDS

# Version information
SONA_VERSION = "0.9.2"
AI_FEATURES_VERSION = "1.0.0"


def create_argument_parser() -> argparse.ArgumentParser:
    """Create the main argument parser for Sona CLI"""
    parser = argparse.ArgumentParser(
        prog='sona',
        description='Sona Cognitive Programming Language v0.9.2',
        epilog='For more information, visit: https://github.com/Bryantad/Sona'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'Sona {SONA_VERSION} (AI Features {AI_FEATURES_VERSION})'
    )
    
    # Main command subparsers
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command (default)
    run_parser = subparsers.add_parser('run', help='Execute a Sona file')
    run_parser.add_argument('file', help='Sona file to execute')
    run_parser.add_argument('--safe', action='store_true', help='Enable safe mode')
    run_parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    # Profile command
    profile_parser = subparsers.add_parser('profile', help='Profile Sona code execution')
    profile_parser.add_argument('file', help='Sona file to profile')
    profile_parser.add_argument('--ai-insights', action='store_true', 
                               help='Generate AI-powered insights')
    
    # Benchmark command
    benchmark_parser = subparsers.add_parser('benchmark', help='Benchmark Sona performance')
    benchmark_parser.add_argument('file', help='Sona file to benchmark')
    benchmark_parser.add_argument('--compare-versions', action='store_true',
                                 help='Compare with previous versions')
    benchmark_parser.add_argument('--ai-recommendations', action='store_true',
                                 help='Get AI performance recommendations')
    
    # Suggest command
    suggest_parser = subparsers.add_parser('suggest', help='Get AI code suggestions')
    suggest_parser.add_argument('file', help='Sona file to analyze')
    suggest_parser.add_argument('--cognitive', action='store_true',
                               help='Focus on cognitive programming suggestions')
    suggest_parser.add_argument('--performance', action='store_true',
                               help='Focus on performance suggestions')
    suggest_parser.add_argument('--accessibility', action='store_true',
                               help='Focus on accessibility suggestions')
    
    # Explain command
    explain_parser = subparsers.add_parser('explain', help='Get AI code explanations')
    explain_parser.add_argument('file', help='Sona file to explain')
    explain_parser.add_argument('--style', choices=['simple', 'detailed', 'cognitive'],
                               default='simple', help='Explanation style')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show system information')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check Sona syntax')
    check_parser.add_argument('file', help='Sona file to check')
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='One-time setup commands')
    setup_sub = setup_parser.add_subparsers(dest='setup_cmd', help='Setup targets')
    # Setup -> Azure
    setup_azure_parser = setup_sub.add_parser('azure', help='Configure Azure OpenAI for Sona')
    setup_azure_parser.add_argument('--dry-run', action='store_true', help='Do not write any files')
    setup_azure_parser.add_argument('--workspace', help='Workspace directory to update .env', default=None)
    setup_azure_parser.add_argument('--manual', action='store_true', help='Manual setup without Azure CLI')
    # Setup -> Manual
    setup_manual_parser = setup_sub.add_parser('manual', help='Manual Azure OpenAI setup (no Azure CLI)')
    setup_manual_parser.add_argument('--dry-run', action='store_true', help='Do not write any files')
    setup_manual_parser.add_argument('--workspace', help='Workspace directory to update .env', default=None)
    
    # Format command
    format_parser = subparsers.add_parser('format', help='Format Sona code')
    format_parser.add_argument('file', help='Sona file to format')
    
    # Transpile command
    transpile_parser = subparsers.add_parser('transpile', help='Transpile Sona to Python')
    transpile_parser.add_argument('file', help='Sona file to transpile')
    transpile_parser.add_argument('--output', help='Output file path')
    
    # REPL command
    repl_parser = subparsers.add_parser('repl', help='Start interactive REPL')
    repl_parser.add_argument('--ai', action='store_true', help='Enable AI assistance')
    info_parser.add_argument('--ai-status', action='store_true',
                            help='Show AI feature status')
    
    return parser


def handle_run_command(args) -> int:
    """Handle the run command"""
    if not Path(args.file).exists():
        print(f"❌ Error: File '{args.file}' not found.")
        return 1
    
    try:
        code = read_text_safe(args.file)
        
        if args.debug:
            print(f"🔍 Executing: {args.file}")
            print(f"Safe mode: {'enabled' if args.safe else 'disabled'}")
            print("=" * 50)
        
        # Execute the code
        result = execute_sona(code, safe_mode=args.safe)
        
        if args.debug:
            print("=" * 50)
            print(f"✅ Execution completed. Result: {result}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Execution error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


def handle_info_command(args) -> int:
    """Handle the info command"""
    print(f"🚀 Sona Programming Language")
    print(f"   Version: {SONA_VERSION}")
    print(f"   AI Features: {AI_FEATURES_VERSION}")
    print(f"   Python: {sys.version.split()[0]}")
    
    if args.ai_status:
        print(f"\n🤖 AI Feature Status:")
        try:
            from sona.ai.gpt2_integration import get_gpt2_instance
            gpt2 = get_gpt2_instance()
            print("   ✅ GPT-2 Integration: Available")
            print("   ✅ Code Completion: Available")
            print("   ✅ Cognitive Assistant: Available")
            print("   ✅ Natural Language Processing: Available")
        except ImportError:
            print("   ❌ AI Features: Not available (missing dependencies)")
        except Exception as e:
            print(f"   ⚠️ AI Features: Error ({e})")
    
    print(f"\n📖 Commands:")
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
        with open(args.file, 'r', encoding='utf-8') as f:
            code = f.read()
        
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
        with open(args.file, 'r', encoding='utf-8') as f:
            code = f.read()
        
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
        with open(args.file, 'r', encoding='utf-8') as f:
            code = f.read()
        
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
        output_file = args.output if args.output else args.file.replace('.sona', '.py')
        
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


def handle_enhanced_command(command: str, args) -> int:
    """Handle enhanced AI commands"""
    if command not in ENHANCED_COMMANDS:
        print(f"❌ Unknown command: {command}")
        return 1
    
    try:
        # Convert args to list format expected by enhanced commands
        arg_list = [args.file]
        
        # Add flags based on command
        if command == 'profile' and hasattr(args, 'ai_insights') and args.ai_insights:
            arg_list.append('--ai-insights')
        
        elif command == 'benchmark':
            if hasattr(args, 'compare_versions') and args.compare_versions:
                arg_list.append('--compare-versions')
            if hasattr(args, 'ai_recommendations') and args.ai_recommendations:
                arg_list.append('--ai-recommendations')
        
        elif command == 'suggest':
            if hasattr(args, 'cognitive') and args.cognitive:
                arg_list.append('--cognitive')
            if hasattr(args, 'performance') and args.performance:
                arg_list.append('--performance')
            if hasattr(args, 'accessibility') and args.accessibility:
                arg_list.append('--accessibility')
        
        elif command == 'explain':
            if hasattr(args, 'style'):
                arg_list.extend(['--style', args.style])
        
        # Execute the enhanced command
        ENHANCED_COMMANDS[command](arg_list)
        return 0
        
    except Exception as e:
        print(f"❌ Command failed: {e}")
        return 1


def main() -> int:
    """Main CLI entry point"""
    parser = create_argument_parser()
    
    # Handle case where no arguments are provided
    if len(sys.argv) == 1:
        print("🚀 Sona Cognitive Programming Language v0.9.2")
        print("\nUsage: sona <command> [options]")
        print("\nCommands:")
        print("  run <file>       Execute a Sona file")
        print("  profile <file>   Profile code execution")
        print("  benchmark <file> Benchmark performance")
        print("  suggest <file>   Get AI suggestions")
        print("  explain <file>   Get AI explanations")
        print("  info             Show system info")
        print("\nUse 'sona <command> --help' for more information.")
        return 0
    
    # Handle direct file execution (legacy mode)
    if len(sys.argv) == 2 and not sys.argv[1].startswith('-') and sys.argv[1] not in ['run', 'profile', 'benchmark', 'suggest', 'explain', 'info']:
        # Treat as direct file execution
        class DirectArgs:
            file = sys.argv[1]
            safe = False
            debug = False
        
        return handle_run_command(DirectArgs())
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle commands
    if args.command == 'run' or args.command is None:
        return handle_run_command(args)
    
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
    
    elif args.command in ENHANCED_COMMANDS:
        return handle_enhanced_command(args.command, args)
    
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
