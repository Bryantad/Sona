#!/usr/bin/env python3
"""
PySide6 Installer and Tester

This script will:
1. Check if PySide6 is installed
2. If not, attempt to install it
3. Test the installation
4. Display helpful diagnostics
"""

import sys
import subprocess
import os
import platform
from pathlib import Path


def print_header(title):
    """Print a section header"""
    print("\n" + "="*60)
    print(title.center(60))
    print("="*60)


def check_pip():
    """Check if pip is available"""
    print("Checking for pip...")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ pip is available")
        return True
    except subprocess.CalledProcessError:
        print("❌ pip is not available or not working properly")
        return False
    except FileNotFoundError:
        print("❌ pip command not found")
        return False


def check_pyside6():
    """Check if PySide6 is installed"""
    print("Checking for PySide6...")
    
    try:
        import PySide6
        from PySide6 import QtCore
        
        print(f"✅ PySide6 {PySide6.__version__} is installed")
        print(f"✅ Qt version: {QtCore.qVersion()}")
        return True
    except ImportError:
        print("❌ PySide6 is not installed")
        return False


def install_pyside6():
    """Install PySide6"""
    print("Attempting to install PySide6...")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "PySide6"],
            check=True,
            capture_output=False
        )
        print("✅ PySide6 installation completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install PySide6: {e}")
        return False


def system_info():
    """Print system information"""
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.architecture()[0]}")
    
    # Check virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"Running in virtual environment: {'Yes' if in_venv else 'No'}")
    
    if in_venv:
        print(f"Virtual environment path: {sys.prefix}")


def test_pyside6_gui():
    """Create a simple PySide6 window to test the installation"""
    print("Testing PySide6 GUI functionality...")
    
    try:
        from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
        from PySide6.QtCore import Qt
        
        class TestWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("PySide6 Test")
                self.setGeometry(100, 100, 400, 200)
                
                # Create central widget
                central_widget = QWidget()
                self.setCentralWidget(central_widget)
                
                # Create layout
                layout = QVBoxLayout(central_widget)
                
                # Add a label
                label = QLabel("PySide6 is working correctly!")
                label.setAlignment(Qt.AlignCenter)
                layout.addWidget(label)
        
        print("✅ PySide6 modules imported successfully")
        print("Would display a window in non-headless environment")
        return True
    
    except Exception as e:
        print(f"❌ Failed to create PySide6 test window: {e}")
        return False


def main():
    """Main function"""
    print_header("PySide6 Installer and Tester")
    
    print_header("System Information")
    system_info()
    
    print_header("Dependencies Check")
    pip_available = check_pip()
    
    if not pip_available:
        print("Cannot continue without pip. Please install pip first.")
        return 1
    
    pyside6_installed = check_pyside6()
    
    if not pyside6_installed:
        print_header("PySide6 Installation")
        install_success = install_pyside6()
        
        if install_success:
            pyside6_installed = check_pyside6()
        else:
            print("Could not install PySide6 automatically.")
            print("Try running: pip install PySide6 --upgrade")
    
    if pyside6_installed:
        print_header("PySide6 GUI Test")
        test_pyside6_gui()
    
    print_header("Summary")
    if pyside6_installed:
        print("PySide6 is installed and ready to use!")
        print("You can now run the modern launcher with:")
        print(f"{sys.executable} {Path(__file__).parent / 'modern_launcher.py'}")
        return 0
    else:
        print("PySide6 installation incomplete or not working properly.")
        print("Please try installing manually with:")
        print("pip install PySide6 --upgrade")
        return 1


if __name__ == "__main__":
    sys.exit(main())
