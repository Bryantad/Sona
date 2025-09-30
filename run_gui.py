#!/usr/bin/env python3
"""
Simple launcher for Sona GUI (Both Modern and Classic)
"""

import importlib.util
import sys
from pathlib import Path


# Set up Python path
sona_dir = Path(__file__).parent
sys.path.insert(0, str(sona_dir))

# Check for PySide6
pyside6_available = importlib.util.find_spec("PySide6") is not None
print(f"PySide6 available: {pyside6_available}")

if pyside6_available:
    try:
        # Try to import PySide6
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication
        
        # Run the Modern GUI
        print("Launching modern PySide6 GUI...")
        import gui.modern.launcher
        sys.exit(0)
    except ImportError as e:
        print(f"Error importing modern launcher: {e}")
        pyside6_available = False
    except Exception as e:
        print(f"Error in modern launcher: {e}")
        pyside6_available = False

# Fall back to Tkinter
if not pyside6_available:
    print("Launching classic Tkinter GUI...")
    try:
        # This will start the Tkinter GUI
        from gui.gui_launcher import main
        main()
    except Exception as e:
        print(f"Error running classic GUI: {e}")
        sys.exit(1)
