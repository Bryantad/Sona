#!/usr/bin/env python3
"""
Sona CLI - minimal command entrypoint for user-managed AI keys

Commands:
  sona setup --provider azure    # Guides user to enter their Azure credentials and saves to user config
  sona run <file.sona>           # Run a Sona file using interpreter (requires user keys for AI features)
  sona info                      # Show current AI provider status and config path

Notes:
- This CLI intentionally requires users to provide their own Azure keys.
- User config is stored in ~/.sona/config.json (Windows: %USERPROFILE%/.sona/config.json)
"""

import sys
import argparse
from pathlib import Path
import json
import os

# Local imports
from azure_ai_provider import USER_CONFIG_PATH, USER_CONFIG, _save_user_config, AzureAIProvider
from sona.interpreter import SonaUnifiedInterpreter


def cmd_setup_azure(args):
    print("🛡️  Sona Setup: Azure OpenAI Provider")
    print("Enter your Azure OpenAI credentials. These will be saved to your user profile directory and not the repo.")
    api_key = input("AZURE_OPENAI_API_KEY: ").strip()
    endpoint = input("AZURE_OPENAI_ENDPOINT: ").strip()
    deployment = input("AZURE_OPENAI_DEPLOYMENT_NAME (default gpt-4): ").strip() or "gpt-4"

    cfg = dict(USER_CONFIG) if isinstance(USER_CONFIG, dict) else {}
    cfg['AZURE_OPENAI_API_KEY'] = api_key
    cfg['AZURE_OPENAI_ENDPOINT'] = endpoint
    cfg['AZURE_OPENAI_DEPLOYMENT_NAME'] = deployment

    _save_user_config(cfg)
    print(f"✅ Saved user config to: {USER_CONFIG_PATH}")
    print("You can now run Sona with your Azure credentials configured.")


def cmd_info(args):
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
    file = Path(args.file)
    if not file.exists():
        print(f"❌ File not found: {file}")
        return

    # Initialize interpreter with user-configured AI
    from test_advanced_cognitive_functions import AdvancedSonaInterpreter
    interp = AdvancedSonaInterpreter()

    # Read file content with fallback encoding
    try:
        content = file.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        # Fallback to latin-1 which can read any byte sequence
        content = file.read_text(encoding='latin-1')
    try:
        result = interp.interpret(content, filename=str(file))
        print("✅ Execution completed")
        if result is not None:
            print(result)
    except Exception as e:
        print(f"❌ Error executing file: {e}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog='sona')
    sub = parser.add_subparsers(dest='command')

    # setup
    p_setup = sub.add_parser('setup', help='Configure AI provider')
    p_setup.add_argument('--provider', choices=['azure'], default='azure')

    p_info = sub.add_parser('info', help='Show AI provider info')

    p_run = sub.add_parser('run', help='Run a Sona file')
    p_run.add_argument('file', help='Sona source file to run')

    # install: add repo to user PATH and optionally install PowerShell profile function
    p_install = sub.add_parser('install', help='Install shell integration so `sona` works globally')
    p_install.add_argument('--add-profile', action='store_true', help='Also add PowerShell profile function for sona')

    args = parser.parse_args(argv)

    if args.command == 'setup':
        cmd_setup_azure(args)
    elif args.command == 'info':
        cmd_info(args)
    elif args.command == 'run':
        cmd_run(args)
    elif args.command == 'install':
        cmd_install(args)
    else:
        parser.print_help()


def cmd_install(args):
    """Install shell integration: add repo folder to user PATH and optionally add PS profile function."""
    import subprocess
    from pathlib import Path
    repo_dir = Path(__file__).parent.resolve()

    # Add to user PATH if not present
    user_path = os.environ.get('PATH', '')
    if str(repo_dir) in user_path.split(os.pathsep):
        print(f"✅ {repo_dir} already in PATH")
    else:
        # Build new PATH value for setx (user-level)
        new_path = user_path + os.pathsep + str(repo_dir)
        try:
            # Use setx to persist user PATH
            subprocess.check_call(['setx', 'PATH', new_path])
            print(f"✅ Added {repo_dir} to user PATH. Restart your shell to use 'sona'.")
        except Exception as e:
            print(f"❌ Failed to add to PATH: {e}")
            print("You can manually add the directory to your PATH environment variable.")

    # Optionally add PowerShell profile function
    if getattr(args, 'add_profile', False):
        try:
            documents = Path.home() / 'Documents'
            ps_dir = documents / 'WindowsPowerShell'
            ps_dir.mkdir(parents=True, exist_ok=True)
            profile = ps_dir / 'Microsoft.PowerShell_profile.ps1'
            # Function content - properly escaped PowerShell function
            func = f"function sona {{ & '{repo_dir}\\sona.bat' @args }}\n"
            content = profile.read_text(encoding='utf-8') if profile.exists() else ''
            if 'function sona' in content:
                print("✅ PowerShell profile already contains 'sona' function")
            else:
                with open(profile, 'a', encoding='utf-8') as f:
                    f.write('\n' + func)
                print(f"✅ Added 'sona' function to PowerShell profile: {profile}")
                print("Restart PowerShell or run: . $PROFILE to load the function")
        except Exception as e:
            print(f"❌ Failed to modify PowerShell profile: {e}")

    return


if __name__ == '__main__':
    main()
