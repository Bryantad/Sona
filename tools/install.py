#!/usr/bin/env python3
# tools/install.py - installation helper for Sona
# Sona v0.5.0 Installation Helper

"""
This script helps set up Sona v0.5.0 by:
1. Installing required dependencies
2. Setting up a virtual environment (optional)
3. Creating command-line aliases for convenient use

Usage:
    python tools/install.py [--venv]
    
    Use --venv to create a virtual environment
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path


def install_dependencies():
    """Install required Python packages"""
    print("Installing required dependencies...")
    
    # Core dependencies
    dependencies = [
        "lark-parser>=0.7.8",
        "colorama",  # For colored console output
    ]
    
    cmd = [sys.executable, "-m", "pip", "install"] + dependencies
    subprocess.run(cmd, check=True)
    print("✓ Dependencies installed successfully")

def create_virtual_env():
    """Create a virtual environment for Sona"""
    print("Setting up virtual environment...")
    
    # Check if venv module is available
    try:
        import venv
    except ImportError:
        print("Error: Python venv module not available.")
        print("Please install it or use Python 3.3+ which includes venv.")
        return False
    
    # Create venv directory
    venv_dir = Path("venv")
    if venv_dir.exists():
        print("Virtual environment already exists at ./venv")
    else:
        print(f"Creating virtual environment at {venv_dir}...")
        venv.create(venv_dir, with_pip=True)
        
        # Install dependencies in virtual environment
        pip_path = venv_dir / "bin" / "pip" if os.name != 'nt' else venv_dir / "Scripts" / "pip"
        cmd = [str(pip_path), "install", "lark-parser>=0.7.8", "colorama"]
        subprocess.run(cmd, check=True)
    
    # Print activation instructions
    if os.name == 'nt':  # Windows
        print("\nTo activate the virtual environment:")
        print("    .\\venv\\Scripts\\activate")
    else:  # macOS/Linux
        print("\nTo activate the virtual environment:")
        print("    source venv/bin/activate")
    
    print("✓ Virtual environment created successfully")
    return True

def setup_cli_alias():
    """Set up a command-line alias for running Sona"""
    print("Setting up command-line alias...")
    
    system = platform.system()
    shell = os.environ.get('SHELL', '')
    
    # Determine shell configuration file
    if 'zsh' in shell:
        config_file = os.path.expanduser('~/.zshrc')
        print("Detected zsh shell")
    elif 'bash' in shell:
        config_file = os.path.expanduser('~/.bashrc')
        print("Detected bash shell")
    else:
        if system == 'Darwin':  # macOS default
            config_file = os.path.expanduser('~/.zshrc')
            print("Using default macOS zsh shell")
        elif system == 'Linux':
            config_file = os.path.expanduser('~/.bashrc')
            print("Using default Linux bash shell")
        else:
            print("Unsupported shell. Please manually add the alias to your shell config.")
            return

    # Command to invoke the Sona CLI.  Use a relative path so the alias works
    # even if the project directory is moved after installation.
    sona_command = "python -m sona.sona_cli"

    # Create alias
    alias_line = f'\n# Sona Programming Language v0.5.0\nalias sona="{sona_command}"\n'
    
    try:
        # Check if alias already exists
        with open(config_file, 'r') as f:
            if 'alias sona=' in f.read():
                print(f"Sona alias already exists in {config_file}")
                return
        
        # Add alias to shell config
        with open(config_file, 'a') as f:
            f.write(alias_line)
        
        print(f"✓ Added Sona alias to {config_file}")
        print("\nTo use the alias immediately, run:")
        print(f"    source {config_file}")
        print("\nAfterwards, you can run Sona with:")
        print("    sona path/to/your/script.sona")
        
    except Exception as e:
        print(f"Error setting up alias: {e}")
        print("\nTo manually set up the alias, add this line to your shell config file:")
        print(f"{alias_line}")

def verify_installation():
    """Verify that Sona has been installed correctly"""
    print("\nVerifying Sona installation...")
    
    # Try to import necessary modules
    try:
        import lark
        print(f"✓ Found lark-parser version {lark.__version__}")
    except ImportError:
        print("✗ lark-parser not found. Please run the install script again.")
        return False
    
    # Check for core Sona files
    sona_dir = Path("sona")
    grammar_file = sona_dir / "grammar.lark"
    interpreter_file = sona_dir / "interpreter.py"
    
    if not sona_dir.exists():
        print("✗ Sona directory not found.")
        return False
    
    if not grammar_file.exists():
        print("✗ Grammar definition not found.")
        return False
    
    if not interpreter_file.exists():
        print("✗ Interpreter not found.")
        return False
    
    print("✓ All required Sona files found")
    
    # Try running a simple Sona program
    try:
        print("\nRunning test program...")
        sample = 'print("Hello from Sona v0.5.0!")'
        cmd = [sys.executable, "-m", "sona.sona_cli", "-c", sample]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and "Hello from Sona v0.5.0!" in result.stdout:
            print("✓ Sona is working correctly!")
        else:
            print("✗ Sona test failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Error testing Sona: {e}")
        return False
    
    return True

def main():
    """Main installation function"""
    parser = argparse.ArgumentParser(description="Sona v0.5.0 Installation Helper")
    parser.add_argument("--venv", action="store_true", help="Create a virtual environment")
    args = parser.parse_args()
    
    print("Sona v0.5.0 Installation")
    print("=======================")
    
    # Install dependencies
    install_dependencies()
    
    # Set up virtual environment if requested
    if args.venv:
        create_virtual_env()
    
    # Set up CLI alias
    setup_cli_alias()
    
    # Verify installation
    if verify_installation():
        print("\n🎉 Sona v0.5.0 is ready to use!")
        print("\nTo get started, try running an example:")
        print("    python -m sona.sona_cli examples/hello_world.sona")
    else:
        print("\n⚠️ Sona installation may not be complete.")
        print("Please check the error messages above and try again.")

if __name__ == "__main__":
    main()
