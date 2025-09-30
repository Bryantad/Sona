#!/usr/bin/env python3
"""
Sona Language GUI Launcher

A user-friendly graphical interface for exploring and running Sona language examples.
Automatically detects available UI frameworks and provides the best experience.

Usage:
    python launcher.py

Features:
- Modern PySide6 interface (if available)
- Classic Tkinter fallback (always available)
- Browse and run example files
- Interactive REPL
- Code viewer with syntax highlighting
- Real-time output console

Requirements:
- Python 3.8+
- tkinter (included with Python)
- PySide6 (optional, for modern UI)

To install PySide6 for the modern interface:
    pip install PySide6
"""

import importlib.util
import sys
from pathlib import Path


def check_dependencies():
    """Check for available UI frameworks"""
    # tkinter is always available in standard Python installations
    tkinter_available = importlib.util.find_spec("tkinter") is not None
    
    # PySide6 is optional for modern UI
    pyside6_available = importlib.util.find_spec("PySide6") is not None
    
    return tkinter_available, pyside6_available

def print_banner():
    """Print a welcome banner"""
    print("=" * 60)
    print("    Sona Programming Language - GUI Launcher v0.7.0")
    print("=" * 60)
    print("Welcome to the Sona language development environment!")
    print()

def main():
    """Main launcher function"""
    print_banner()
    
    # Set up path to Sona directory
    sona_dir = Path(__file__).parent.absolute()
    if str(sona_dir) not in sys.path:
        sys.path.insert(0, str(sona_dir))
    
    # Check available UI frameworks
    tkinter_available, pyside6_available = check_dependencies()
    
    print(f"Python version: {sys.version.split()[0]}")
    print(f"Tkinter available: {'✓' if tkinter_available else '✗'}")
    print(f"PySide6 available: {'✓' if pyside6_available else '✗'}")
    print()
    
    # Launch appropriate UI
    if pyside6_available:
        try:
            print("🚀 Launching modern PySide6 interface...")
            from gui.modern.launcher import main as modern_main
            return modern_main()
        except ImportError as e:
            print(f"⚠️  Modern UI import failed: {e}")
            print("   Falling back to classic interface...")
            pyside6_available = False
        except Exception as e:
            print(f"⚠️  Modern UI startup failed: {e}")
            print("   Falling back to classic interface...")
            pyside6_available = False
    
    if tkinter_available:
        try:
            print("🎯 Launching classic Tkinter interface...")
            from gui.gui_launcher import main as classic_main
            return classic_main()
        except ImportError as e:
            print(f"❌ Classic UI import failed: {e}")
            print("   Please ensure tkinter is properly installed.")
            return 1
        except Exception as e:
            print(f"❌ Classic UI startup failed: {e}")
            return 1
    else:
        print("❌ No GUI framework available!")
        print("   Please install tkinter (usually included with Python)")
        print("   or PySide6 (pip install PySide6) for the modern interface.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nLauncher interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
