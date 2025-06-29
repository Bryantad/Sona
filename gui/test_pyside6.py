#!/usr/bin/env python3
"""
PySide6 Installation Test
Simple test to verify PySide6 is working correctly
"""

import sys
from pathlib import Path

def test_pyside6_import():
    """Test if PySide6 can be imported"""
    print("Testing PySide6 installation...")
    
    try:
        from PySide6 import QtWidgets, QtCore, QtGui
        print("✓ PySide6 core modules imported successfully")
        
        # Test Qt version
        print(f"✓ Qt version: {QtCore.qVersion()}")
        print(f"✓ PySide6 version: {QtCore.__version__}")
        
        return True
    except ImportError as e:
        print(f"✗ Failed to import PySide6: {e}")
        return False

def create_test_window():
    """Create a simple test window"""
    from PySide6 import QtWidgets, QtCore, QtGui
    
    app = QtWidgets.QApplication(sys.argv)
    
    # Create main window
    window = QtWidgets.QMainWindow()
    window.setWindowTitle("PySide6 Test - Sona Engine")
    window.setGeometry(100, 100, 400, 300)
    
    # Create central widget
    central_widget = QtWidgets.QWidget()
    window.setCentralWidget(central_widget)
    
    # Create layout
    layout = QtWidgets.QVBoxLayout(central_widget)
    
    # Add welcome label
    welcome_label = QtWidgets.QLabel("🎉 PySide6 is working correctly!")
    welcome_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    welcome_label.setStyleSheet("""
        QLabel {
            font-size: 18px;
            font-weight: bold;
            color: #2E7D32;
            padding: 20px;
            background-color: #E8F5E8;
            border-radius: 8px;
            margin: 10px;
        }
    """)
    layout.addWidget(welcome_label)
    
    # Add info labels
    info_layout = QtWidgets.QVBoxLayout()
    
    qt_version_label = QtWidgets.QLabel(f"Qt Version: {QtCore.qVersion()}")
    pyside_version_label = QtWidgets.QLabel(f"PySide6 Version: {QtCore.__version__}")
    platform_label = QtWidgets.QLabel(f"Platform: {sys.platform}")
    python_version_label = QtWidgets.QLabel(f"Python Version: {sys.version.split()[0]}")
    
    for label in [qt_version_label, pyside_version_label, platform_label, python_version_label]:
        label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                padding: 5px;
                margin: 2px;
            }
        """)
        info_layout.addWidget(label)
    
    layout.addLayout(info_layout)
    
    # Add test button
    test_button = QtWidgets.QPushButton("Test Features")
    test_button.setStyleSheet("""
        QPushButton {
            background-color: #1976D2;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: bold;
            border-radius: 6px;
        }
        QPushButton:hover {
            background-color: #1565C0;
        }
        QPushButton:pressed {
            background-color: #0D47A1;
        }
    """)
    
    def test_features():
        QtWidgets.QMessageBox.information(
            window, 
            "Feature Test", 
            "✓ Widgets working\n✓ Styling working\n✓ Events working\n\nPySide6 is ready for the Sona launcher!"
        )
    
    test_button.clicked.connect(test_features)
    layout.addWidget(test_button)
    
    # Add close button
    close_button = QtWidgets.QPushButton("Close Test")
    close_button.setStyleSheet("""
        QPushButton {
            background-color: #757575;
            color: white;
            border: none;
            padding: 8px 16px;
            font-size: 12px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #616161;
        }
    """)
    close_button.clicked.connect(window.close)
    layout.addWidget(close_button)
    
    # Show window
    window.show()
    
    return app, window

def main():
    """Main test function"""
    print("=" * 50)
    print("PySide6 Installation Test for Sona Engine")
    print("=" * 50)
    
    if test_pyside6_import():
        print("\n✓ Import test passed! Creating test window...")
        
        try:
            app, window = create_test_window()
            print("✓ Test window created successfully")
            print("✓ PySide6 is ready for use!")
            print("\nClose the test window to continue...")
            
            # Run the application
            sys.exit(app.exec())
            
        except Exception as e:
            print(f"✗ Error creating test window: {e}")
            return False
    else:
        print("\n✗ PySide6 import test failed")
        print("Please ensure PySide6 is properly installed")
        return False

if __name__ == "__main__":
    main()
