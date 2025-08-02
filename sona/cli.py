"""
Sona v0.8.2 Command Line Interface with AI Integration

Enhanced CLI with profile, benchmark, suggest, and explain commands
powered by GPT-2 and cognitive assistance features.
"""

import sys
import argparse
from pathlib import Path
from typing import List, Optional

# Import Sona core components
from sona.interpreter import create_interpreter, execute_sona
from sona.ai.enhanced_cli import ENHANCED_COMMANDS

# Version information
SONA_VERSION = "0.8.2-dev"
AI_FEATURES_VERSION = "1.0.0"


def create_argument_parser() -> argparse.ArgumentParser:
    """Create the main argument parser for Sona CLI"""
    parser = argparse.ArgumentParser(
        prog='sona',
        description='Sona Cognitive Programming Language v0.8.2',
        epilog='For more information, visit: https://github.com/sona-lang'
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
    info_parser.add_argument('--ai-status', action='store_true',
                            help='Show AI feature status')
    
    return parser


def handle_run_command(args) -> int:
    """Handle the run command"""
    if not Path(args.file).exists():
        print(f"❌ Error: File '{args.file}' not found.")
        return 1
    
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            code = f.read()
        
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
        print("🚀 Sona Cognitive Programming Language v0.8.2")
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
    
    elif args.command in ENHANCED_COMMANDS:
        return handle_enhanced_command(args.command, args)
    
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
