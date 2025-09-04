#!/usr/bin/env python3
"""
Sona CLI - Complete command-line interface for the Sona programming language

Commands:
  sona setup --provider azure    # Configure Azure OpenAI credentials
  sona run <file.sona>           # Run a Sona file
  sona repl                      # Interactive REPL with AI features
  sona transpile <file.sona>     # Transpile to other languages
  sona format <file.sona>        # Format Sona code
  sona check <file.sona>         # Check syntax and validate
  sona info                      # Show AI provider status
  sona install                   # Install shell integration

Notes:
- User config is stored in ~/.sona/config.json
- Windows: %USERPROFILE%/.sona/config.json
- Users must provide their own Azure OpenAI credentials for AI features
"""

import sys
import argparse
from pathlib import Path
import os

# Local imports
from azure_ai_provider import USER_CONFIG_PATH, USER_CONFIG, _save_user_config


def cmd_setup_azure(args):
    """Configure Azure OpenAI provider with user credentials"""
    print("🛡️  Sona Setup: Azure OpenAI Provider")
    print("Enter your Azure OpenAI credentials.")
    print("These will be saved to your user profile directory.")
    
    api_key = input("AZURE_OPENAI_API_KEY: ").strip()
    endpoint = input("AZURE_OPENAI_ENDPOINT: ").strip()
    deployment_prompt = "AZURE_OPENAI_DEPLOYMENT_NAME (default gpt-4): "
    deployment = input(deployment_prompt).strip() or "gpt-4"

    cfg = dict(USER_CONFIG) if isinstance(USER_CONFIG, dict) else {}
    cfg['AZURE_OPENAI_API_KEY'] = api_key
    cfg['AZURE_OPENAI_ENDPOINT'] = endpoint
    cfg['AZURE_OPENAI_DEPLOYMENT_NAME'] = deployment

    _save_user_config(cfg)
    print(f"✅ Saved user config to: {USER_CONFIG_PATH}")
    print("You can now run Sona with your Azure credentials configured.")


def cmd_info(args):
    """Show AI provider configuration info"""
    print("🔎 Sona AI Provider Info")
    print(f"User config path: {USER_CONFIG_PATH}")
    cfg = USER_CONFIG
    if not cfg:
        print("No user config found. Run: sona setup --provider azure")
        return
    print("Configured Azure provider: ")
    print(f"  Endpoint: {cfg.get('AZURE_OPENAI_ENDPOINT')}")
    print(f"  Deployment: {cfg.get('AZURE_OPENAI_DEPLOYMENT_NAME')}")
    print("(API key is kept private and not displayed)")


def cmd_run(args):
    """Run a Sona file using the interpreter"""
    file = Path(args.file)
    if not file.exists():
        print(f"❌ File not found: {file}")
        return

    try:
        from test_advanced_cognitive_functions import AdvancedSonaInterpreter
        interp = AdvancedSonaInterpreter()
        
        content = file.read_text(encoding='utf-8')
        print(f"🚀 Executing: {file}")
        result = interp.interpret(content, filename=str(file))
        print("✅ Execution completed")
        if result is not None:
            print(result)
    except Exception as e:
        print(f"❌ Error executing file: {e}")


def cmd_repl(args):
    """Start interactive REPL with cognitive features"""
    try:
        from test_advanced_cognitive_functions import AdvancedSonaInterpreter

        print("🧠 Sona Interactive REPL v1.0.0")
        print("🎯 Cognitive programming with AI assistance")
        print("💡 Try: remember('key', 'value'), focus_mode('task', 25)")
        print("📝 Commands: :help, :info, :exit")
        print()

        interpreter = AdvancedSonaInterpreter()

        while True:
            try:
                user_input = input("sona> ").strip()

                if user_input.lower() in ['exit', 'quit', ':exit', ':q']:
                    print("👋 Goodbye!")
                    break
                elif user_input == ':help':
                    print_repl_help()
                    continue
                elif user_input == ':info':
                    print("🧠 Cognitive State:")
                    mem_slots = len(interpreter.working_memory.memory_slots)
                    print(f"   Memory slots: {mem_slots}")
                    cog_load = interpreter.working_memory.cognitive_load
                    print(f"   Cognitive load: {cog_load:.2f}")
                    focus_sessions = len(interpreter.working_memory.focus_stack)
                    print(f"   Focus sessions: {focus_sessions}")
                    continue

                if user_input:
                    result = interpreter.interpret(user_input)
                    if result is not None and not isinstance(result, dict):
                        print(f"=> {result}")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    except ImportError as e:
        print(f"❌ Failed to import Sona interpreter: {e}")


def print_repl_help():
    """Print REPL help"""
    print("🧠 Sona REPL Commands:")
    print("  Basic:")
    print("    let x = 5                    # Variable assignment")
    print("    print(x)                     # Print values")
    print("  ")
    print("  Cognitive Functions:")
    print("    remember('key', 'value')     # Store in working memory")
    print("    recall('key')                # Retrieve from memory")
    print("    focus_mode('task', 25)       # Start focus session")
    print("    cognitive_load()             # Check cognitive load")
    print("    attention_check()            # Analyze attention")
    print("  ")
    print("  AI Functions:")
    print("    ai_simplify('complex text')  # AI simplification")
    print("    ai_break_down('big task')    # AI task breakdown")
    print("  ")
    print("  REPL Commands:")
    print("    :help                        # Show this help")
    print("    :info                        # Show cognitive state")
    print("    :exit                        # Exit REPL")


def cmd_transpile(args):
    """Transpile Sona code to other languages"""
    file = Path(args.file)
    if not file.exists():
        print(f"❌ File not found: {file}")
        return

    try:
        from sona_transpiler import (SonaTranspiler, TargetLanguage, 
                                    TranspileOptions)
        
        transpiler = SonaTranspiler()
        content = file.read_text(encoding='utf-8')
        
        target = getattr(args, 'target', 'javascript')
        output_file = getattr(args, 'output', None)
        
        print(f"🔄 Transpiling {file} to {target}")
        
        # Convert string to TargetLanguage enum
        target_lang = TargetLanguage(target)
        options = TranspileOptions(target_language=target_lang)
        
        result = transpiler.transpile(content, options)
        
        if output_file:
            Path(output_file).write_text(result.code, encoding='utf-8')
            print(f"✅ Transpiled to: {output_file}")
        else:
            # Generate default output filename
            output_ext = {
                'javascript': '.js',
                'typescript': '.ts', 
                'python': '.py',
                'java': '.java',
                'csharp': '.cs',
                'go': '.go',
                'rust': '.rs'
            }.get(target, '.txt')
            
            output_path = file.with_suffix(output_ext)
            output_path.write_text(result.code, encoding='utf-8')
            print(f"✅ Transpiled to: {output_path}")
            
        # Show any warnings
        if result.warnings:
            print("⚠️  Warnings:")
            for warning in result.warnings:
                print(f"   {warning}")
            
    except ImportError:
        print("❌ Transpiler not available. Check installation.")
    except Exception as e:
        print(f"❌ Transpilation failed: {e}")


def cmd_format(args):
    """Format Sona code files"""
    file = Path(args.file)
    if not file.exists():
        print(f"❌ File not found: {file}")
        return

    try:
        content = file.read_text(encoding='utf-8')
        
        # Simple formatting (can be enhanced later)
        lines = content.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted_lines.append('')
                continue
                
            # Decrease indent for closing braces
            if stripped.startswith('}'):
                indent_level = max(0, indent_level - 1)
            
            # Add formatted line
            formatted_lines.append('    ' * indent_level + stripped)
            
            # Increase indent for opening braces
            if stripped.endswith('{'):
                indent_level += 1
        
        formatted_content = '\n'.join(formatted_lines)
        
        if getattr(args, 'in_place', True):
            file.write_text(formatted_content, encoding='utf-8')
            print(f"✅ Formatted: {file}")
        else:
            print(formatted_content)
            
    except Exception as e:
        print(f"❌ Formatting failed: {e}")


def cmd_check(args):
    """Check Sona file syntax"""
    file = Path(args.file)
    if not file.exists():
        print(f"❌ File not found: {file}")
        return

    try:
        from test_advanced_cognitive_functions import AdvancedSonaInterpreter
        
        interpreter = AdvancedSonaInterpreter()
        content = file.read_text(encoding='utf-8')
        
        print(f"🔍 Checking syntax: {file}")
        
        # Try to parse/interpret to check for errors
        try:
            interpreter.interpret(content, filename=str(file))
            print("✅ Syntax check passed")
        except Exception as e:
            print(f"❌ Syntax error: {e}")
            
    except Exception as e:
        print(f"❌ Check failed: {e}")


def cmd_install(args):
    """Install shell integration"""
    import subprocess
    
    repo_dir = Path(__file__).parent.resolve()

    # Add to user PATH if not present
    user_path = os.environ.get('PATH', '')
    if str(repo_dir) in user_path.split(os.pathsep):
        print(f"✅ {repo_dir} already in PATH")
    else:
        new_path = user_path + os.pathsep + str(repo_dir)
        try:
            subprocess.check_call(['setx', 'PATH', new_path])
            print(f"✅ Added {repo_dir} to user PATH.")
            print("Restart your shell to use 'sona'.")
        except Exception as e:
            print(f"❌ Failed to add to PATH: {e}")

    # Add PowerShell profile function if requested
    if getattr(args, 'add_profile', False):
        try:
            documents = Path.home() / 'Documents'
            ps_dir = documents / 'WindowsPowerShell'
            ps_dir.mkdir(parents=True, exist_ok=True)
            profile = ps_dir / 'Microsoft.PowerShell_profile.ps1'
            func = f"function sona {{ & '{repo_dir / 'sona.bat'}' @args }}\n"
            content = profile.read_text(encoding='utf-8') if profile.exists() else ''
            if 'function sona' in content:
                print("✅ PowerShell profile already contains 'sona' function")
            else:
                with open(profile, 'a', encoding='utf-8') as f:
                    f.write('\n' + func)
                print(f"✅ Added 'sona' function to PowerShell profile")
        except Exception as e:
            print(f"❌ Failed to modify PowerShell profile: {e}")


def main(argv=None):
    # Handle common command variations before argparse
    if argv is None:
        argv = sys.argv[1:]
    
    # Convert common aliases to standard commands
    if len(argv) > 0:
        if argv[0] == 'setup-azure':
            argv = ['setup', '--provider', 'azure']
        elif argv[0] == 'config':
            argv = ['setup', '--provider', 'azure']
    
    parser = argparse.ArgumentParser(
        prog='sona', 
        description='Sona Programming Language CLI'
    )
    sub = parser.add_subparsers(dest='command', help='Available commands')

    # setup
    p_setup = sub.add_parser('setup', help='Configure AI provider')
    p_setup.add_argument('--provider', choices=['azure'], default='azure')

    # info  
    sub.add_parser('info', help='Show AI provider info')

    # run
    p_run = sub.add_parser('run', help='Run a Sona file')
    p_run.add_argument('file', help='Sona source file to run')

    # repl
    sub.add_parser('repl', help='Start interactive REPL with cognitive features')

    # transpile
    p_transpile = sub.add_parser('transpile', 
                                help='Transpile Sona code to other languages')
    p_transpile.add_argument('file', help='Sona source file to transpile')
    p_transpile.add_argument('--target', 
                           choices=['javascript', 'typescript', 'python', 
                                   'java', 'csharp', 'go', 'rust'], 
                           default='javascript')
    p_transpile.add_argument('--output', help='Output file path')

    # format
    p_format = sub.add_parser('format', help='Format Sona code')
    p_format.add_argument('file', help='Sona source file to format')
    p_format.add_argument('--in-place', action='store_true', default=True, 
                         help='Format file in place')

    # check
    p_check = sub.add_parser('check', help='Check Sona file syntax')
    p_check.add_argument('file', help='Sona source file to check')

    # install
    p_install = sub.add_parser('install', help='Install shell integration')
    p_install.add_argument('--add-profile', action='store_true', 
                          help='Also add PowerShell profile function')

    args = parser.parse_args(argv)

    if args.command == 'setup':
        cmd_setup_azure(args)
    elif args.command == 'info':
        cmd_info(args)
    elif args.command == 'run':
        cmd_run(args)
    elif args.command == 'repl':
        cmd_repl(args)
    elif args.command == 'transpile':
        cmd_transpile(args)
    elif args.command == 'format':
        cmd_format(args)
    elif args.command == 'check':
        cmd_check(args)
    elif args.command == 'install':
        cmd_install(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
