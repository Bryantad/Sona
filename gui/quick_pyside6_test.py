#!/usr/bin/env python3
"""
Quick PySide6 Test - Minimal version to verify PySide6 is working
"""

import sys
print("Python version:", sys.version)

try:
    from PySide6.QtWidgets import QApplication, QLabel
    from PySide6.QtCore import Qt
    print("PySide6 SUCCESSFULLY imported!")
    print("PySide6 is properly installed and working!")
    
    # Create a minimal app just to verify GUI creation works
    app = QApplication(sys.argv)
    label = QLabel("PySide6 is working correctly!")
    label.setAlignment(Qt.AlignCenter)
    label.resize(400, 100)
    label.show()
    
    print("GUI window created successfully.")
    print("You can close the window to exit.")
    
    sys.exit(app.exec())
except ImportError as e:
    print("ERROR: PySide6 import failed!")
    print(f"Error details: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(1)
