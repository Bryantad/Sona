#!/usr/bin/env python3
"""
Sona Modern Launcher - Minimal Version

A simplified PySide6-based launcher for Sona examples
with graceful fallback to native UI if PySide6 is unavailable.
"""

import sys
import os
import subprocess
import threading
from pathlib import Path
import importlib.util
import tempfile
import webbrowser

# Check if PySide6 is available
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None

if PYSIDE6_AVAILABLE:
    try:
        from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                      QHBoxLayout, QSplitter, QLabel, QPushButton, 
                                      QListWidget, QTextEdit, QTabWidget, QLineEdit, 
                                      QFileDialog, QMessageBox, QFrame, QStatusBar,
                                      QDialog, QMenu)
        from PySide6.QtCore import Qt, Signal, Slot, QSize, QProcess, QTimer, QObject
        from PySide6.QtGui import QFont, QColor, QAction, QIcon, QTextCursor
    except ImportError:
        PYSIDE6_AVAILABLE = False


# Colors - Used in both UI versions
COLORS = {
    'bg_primary': '#1a1a2e',      # Dark navy background
    'bg_secondary': '#16213e',     # Darker secondary
    'bg_tertiary': '#0f3460',      # Blue accent
    'accent_primary': '#533483',   # Purple accent
    'accent_secondary': '#7209b7', # Bright purple
    'text_primary': '#ffffff',     # White text
    'text_secondary': '#b8b8b8',   # Light gray text
    'text_accent': '#64ffda',      # Cyan accent text
    'success': '#4caf50',          # Green
    'warning': '#ff9800',          # Orange
    'error': '#f44336',            # Red
    'button_hover': '#2a2a5a',     # Button hover
}


# PySide6 Version
if PYSIDE6_AVAILABLE:
    
    class SyntaxHighlighter:
        """Simple syntax highlighter for Sona code"""
        
        def highlight_code(self, text_edit):
            """Apply syntax highlighting to code in text edit widget"""
            document = text_edit.document()
            cursor = QTextCursor(document)
            
            # Clear existing formatting
            cursor.select(QTextCursor.Document)
            char_format = cursor.charFormat()
            char_format.setForeground(QColor(COLORS['text_primary']))
            cursor.setCharFormat(char_format)
            cursor.clearSelection()
            
            # Highlight keywords
            keywords = ['let', 'import', 'print', 'if', 'else', 'func']
            keyword_format = cursor.charFormat()
            keyword_format.setForeground(QColor('#569CD6'))  # Blue for keywords
            keyword_format.setFontWeight(QFont.Bold)
            
            for keyword in keywords:
                cursor = QTextCursor(document)
                while not cursor.isNull() and not cursor.atEnd():
                    cursor = document.find(keyword, cursor)
                    if not cursor.isNull():
                        cursor.mergeCharFormat(keyword_format)
            
            # Highlight comments
            comment_format = cursor.charFormat()
            comment_format.setForeground(QColor('#6A9955'))  # Green for comments
            
            cursor = QTextCursor(document)
            while not cursor.isNull() and not cursor.atEnd():
                cursor = document.find("//", cursor)
                if not cursor.isNull():
                    line_end = cursor.block().position() + cursor.block().length() - 1
                    cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
                    cursor.mergeCharFormat(comment_format)
            
            # Highlight strings
            string_format = cursor.charFormat()
            string_format.setForeground(QColor('#CE9178'))  # Orange for strings
            
            cursor = QTextCursor(document)
            while not cursor.isNull() and not cursor.atEnd():
                cursor = document.find('"', cursor)
                if not cursor.isNull():
                    start = cursor.position()
                    cursor.movePosition(QTextCursor.Right)
                    cursor = document.find('"', cursor)
                    if not cursor.isNull():
                        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 
                                          start - cursor.position())
                        cursor.mergeCharFormat(string_format)

    
    class ConsoleWidget(QWidget):
        """Output console widget"""
        
        def __init__(self, parent=None):
            super().__init__(parent)
            
            self.layout = QVBoxLayout(self)
            self.layout.setContentsMargins(0, 0, 0, 0)
            
            # Console output
            self.output = QTextEdit()
            self.output.setReadOnly(True)
            self.output.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {COLORS['bg_secondary']};
                    color: {COLORS['text_primary']};
                    font-family: 'Consolas', monospace;
                    border: none;
                    padding: 5px;
                }}
            """)
            self.layout.addWidget(self.output)
            
            # Controls
            controls_layout = QHBoxLayout()
            
            self.clear_btn = QPushButton("Clear")
            self.clear_btn.clicked.connect(self.clear_output)
            controls_layout.addWidget(self.clear_btn)
            
            controls_layout.addStretch()
            
            self.status_label = QLabel("Ready")
            self.status_label.setStyleSheet(f"color: {COLORS['success']};")
            controls_layout.addWidget(self.status_label)
            
            self.layout.addLayout(controls_layout)
        
        def append_text(self, text, color=None):
            """Add text to the console with optional color"""
            cursor = self.output.textCursor()
            cursor.movePosition(QTextCursor.End)
            
            if color:
                format_text = f"<span style='color:{color};'>{text}</span>"
                self.output.insertHtml(format_text)
            else:
                self.output.insertPlainText(text)
            
            cursor.movePosition(QTextCursor.End)
            self.output.setTextCursor(cursor)
        
        def append_line(self, text, color=None):
            """Add a line of text with a newline"""
            self.append_text(text + "\n", color)
        
        def clear_output(self):
            """Clear the console output"""
            self.output.clear()
            
        def set_status(self, text, color=None):
            """Set the status text"""
            self.status_label.setText(text)
            if color:
                self.status_label.setStyleSheet(f"color: {color};")
            else:
                self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")


    class SonaExampleBrowser(QWidget):
        """Example browser widget"""
        
        example_selected = Signal(str)
        
        def __init__(self, parent=None):
            super().__init__(parent)
            
            self.examples_dir = Path(__file__).parent.parent.parent / "examples"
            self.working_examples = [
                "basic_syntax.sona",
                "dict_simple.sona",
                "dictionary_operations.sona",
                "modules_working.sona",
                "module_demo.sona",
                "data_processing.sona",
                "error_handling.sona"
            ]
            
            self.layout = QVBoxLayout(self)
            
            # Search box
            search_layout = QHBoxLayout()
            search_label = QLabel("🔍")
            search_layout.addWidget(search_label)
            
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Search examples...")
            self.search_input.textChanged.connect(self.filter_examples)
            search_layout.addWidget(self.search_input)
            
            self.layout.addLayout(search_layout)
            
            # Example list
            self.example_list = QListWidget()
            self.example_list.itemClicked.connect(self.on_example_selected)
            self.layout.addWidget(self.example_list)
            
            # Action buttons
            self.run_btn = QPushButton("▶ Run Example")
            self.run_btn.setEnabled(False)
            self.layout.addWidget(self.run_btn)
            
            self.view_btn = QPushButton("👁 View Code")
            self.view_btn.setEnabled(False)
            self.layout.addWidget(self.view_btn)
            
            self.refresh_btn = QPushButton("🔄 Refresh")
            self.refresh_btn.clicked.connect(self.load_examples)
            self.layout.addWidget(self.refresh_btn)
            
            # Load examples
            self.load_examples()
        
        def load_examples(self):
            """Load example files into the list"""
            self.example_list.clear()
            
            if not self.examples_dir.exists():
                print(f"Examples directory not found: {self.examples_dir}")
                return
            
            # Add working examples first with checkmark
            for example in self.working_examples:
                if (self.examples_dir / example).exists():
                    self.example_list.addItem(f"✓ {example}")
            
            # Add other .sona files
            try:
                for file_path in self.examples_dir.glob("*.sona"):
                    if file_path.name not in self.working_examples:
                        self.example_list.addItem(f"? {file_path.name}")
            except Exception as e:
                print(f"Error loading examples: {e}")
        
        def filter_examples(self):
            """Filter examples based on search text"""
            search_text = self.search_input.text().lower()
            
            for i in range(self.example_list.count()):
                item = self.example_list.item(i)
                item_text = item.text()[2:].lower()  # Remove prefix (✓ or ?)
                item.setHidden(search_text and search_text not in item_text)
        
        def on_example_selected(self, item):
            """Handle example selection"""
            example_text = item.text()
            # Remove the status prefix (✓ or ?)
            example_name = example_text[2:] if len(example_text) > 2 else example_text
            
            self.run_btn.setEnabled(True)
            self.view_btn.setEnabled(True)
            self.example_selected.emit(example_name)
        
        def get_selected_example(self):
            """Get the currently selected example filename"""
            selected_items = self.example_list.selectedItems()
            if not selected_items:
                return None
                
            item_text = selected_items[0].text()
            # Remove the status prefix (✓ or ?)
            return item_text[2:] if len(item_text) > 2 else item_text


    class SonaExecutor(QObject):
        """Executor for running Sona examples"""
        
        output_ready = Signal(str)
        error_ready = Signal(str)
        execution_started = Signal()
        execution_finished = Signal(int)
        
        def __init__(self, parent=None):
            super().__init__(parent)
            
            self.sona_dir = Path(__file__).parent.parent.parent
            self.process = QProcess()
            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            self.process.readyReadStandardError.connect(self.handle_stderr)
            self.process.finished.connect(self.process_finished)
        
        def run_example(self, example_name):
            """Run a Sona example"""
            self.execution_started.emit()
            
            # Prepare command
            cmd = sys.executable
            args = ["-m", "sona", str(self.sona_dir / "examples" / example_name)]
            
            # Start process
            self.process.setWorkingDirectory(str(self.sona_dir))
            self.process.start(cmd, args)
        
        def handle_stdout(self):
            """Handle standard output from the process"""
            data = self.process.readAllStandardOutput()
            text = data.data().decode('utf-8', errors='replace')
            self.output_ready.emit(text)
        
        def handle_stderr(self):
            """Handle standard error from the process"""
            data = self.process.readAllStandardError()
            text = data.data().decode('utf-8', errors='replace')
            self.error_ready.emit(text)
        
        def process_finished(self, exit_code, exit_status):
            """Handle process completion"""
            self.execution_finished.emit(exit_code)
            
            if exit_code != 0:
                self.error_ready.emit(f"\nProcess exited with code {exit_code}\n")


    class MainWindow(QMainWindow):
        """Main window for Sona Modern Launcher"""
        
        def __init__(self):
            super().__init__()
            
            self.setWindowTitle("Sona Modern Launcher v0.7.0")
            self.setMinimumSize(1200, 800)
            self.setStyleSheet(f"""
                QMainWindow, QWidget {{
                    background-color: {COLORS['bg_primary']};
                    color: {COLORS['text_primary']};
                }}
                
                QPushButton {{
                    background-color: {COLORS['accent_primary']};
                    color: {COLORS['text_primary']};
                    border: none;
                    padding: 8px;
                    border-radius: 2px;
                }}
                
                QPushButton:hover {{
                    background-color: {COLORS['accent_secondary']};
                }}
                
                QPushButton:disabled {{
                    background-color: {COLORS['bg_secondary']};
                    color: {COLORS['text_secondary']};
                }}
                
                QListWidget, QTextEdit, QLineEdit {{
                    background-color: {COLORS['bg_secondary']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['bg_tertiary']};
                    border-radius: 2px;
                }}
                
                QListWidget::item:selected {{
                    background-color: {COLORS['accent_primary']};
                    color: {COLORS['text_primary']};
                }}
                
                QTabWidget::pane {{
                    border: 1px solid {COLORS['bg_tertiary']};
                }}
                
                QTabBar::tab {{
                    background-color: {COLORS['bg_secondary']};
                    color: {COLORS['text_secondary']};
                    padding: 8px 16px;
                }}
                
                QTabBar::tab:selected {{
                    background-color: {COLORS['accent_primary']};
                    color: {COLORS['text_primary']};
                }}
            """)
            
            # Central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Main layout
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(10, 10, 10, 10)
            
            # Title bar
            title_layout = QHBoxLayout()
            title_label = QLabel("Sona v0.7.0 - Modern Development Platform")
            title_label.setStyleSheet(f"""
                font-size: 18px;
                font-weight: bold;
                color: {COLORS['text_primary']};
            """)
            title_layout.addWidget(title_label)
            
            subtitle_label = QLabel("Professional • Modern • Extensible")
            subtitle_label.setStyleSheet(f"color: {COLORS['text_accent']};")
            title_layout.addWidget(subtitle_label)
            title_layout.addStretch()
            
            main_layout.addLayout(title_layout)
            
            # Splitter for main content
            splitter = QSplitter(Qt.Horizontal)
            
            # Example browser (left side)
            self.example_browser = SonaExampleBrowser()
            splitter.addWidget(self.example_browser)
            
            # Content area (middle)
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(0, 0, 0, 0)
            
            # Content tabs
            self.tabs = QTabWidget()
            
            # Code tab
            self.code_widget = QWidget()
            code_layout = QVBoxLayout(self.code_widget)
            self.code_edit = QTextEdit()
            self.code_edit.setReadOnly(True)
            code_layout.addWidget(self.code_edit)
            
            # Create syntax highlighter
            self.highlighter = SyntaxHighlighter()
            
            self.tabs.addTab(self.code_widget, "📝 Source Code")
            
            content_layout.addWidget(self.tabs)
            splitter.addWidget(content_widget)
            
            # Console (right side)
            self.console = ConsoleWidget()
            splitter.addWidget(self.console)
            
            # Set initial splitter sizes (1:3:2 ratio)
            splitter.setSizes([200, 600, 400])
            
            main_layout.addWidget(splitter)
            
            # Status bar
            self.statusBar().showMessage("Ready")
            
            # Create executor
            self.executor = SonaExecutor()
            self.executor.output_ready.connect(lambda text: self.console.append_text(text))
            self.executor.error_ready.connect(lambda text: self.console.append_text(text, COLORS['error']))
            self.executor.execution_started.connect(lambda: self.console.set_status("Running...", COLORS['warning']))
            self.executor.execution_finished.connect(lambda code: self.console.set_status(
                "Ready" if code == 0 else "Error", 
                COLORS['success'] if code == 0 else COLORS['error']
            ))
            
            # Connect signals
            self.example_browser.example_selected.connect(self.view_example)
            self.example_browser.run_btn.clicked.connect(self.run_example)
            self.example_browser.view_btn.clicked.connect(self.view_example)
            
            # Create menu
            self.create_menu()
            
            # Show initial message
            self.console.append_line("Sona Modern Launcher started. Select an example to begin.", COLORS['text_accent'])
        
        def create_menu(self):
            """Create application menu"""
            menubar = self.menuBar()
            
            # File menu
            file_menu = menubar.addMenu("&File")
            
            open_action = QAction("&Open Example...", self)
            open_action.triggered.connect(self.open_file)
            file_menu.addAction(open_action)
            
            file_menu.addSeparator()
            
            exit_action = QAction("E&xit", self)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
            
            # Examples menu
            examples_menu = menubar.addMenu("&Examples")
            
            refresh_action = QAction("&Refresh Examples", self)
            refresh_action.triggered.connect(self.example_browser.load_examples)
            examples_menu.addAction(refresh_action)
            
            open_folder_action = QAction("Open Examples &Folder", self)
            open_folder_action.triggered.connect(self.open_examples_folder)
            examples_menu.addAction(open_folder_action)
            
            # Help menu
            help_menu = menubar.addMenu("&Help")
            
            about_action = QAction("&About", self)
            about_action.triggered.connect(self.show_about)
            help_menu.addAction(about_action)
        
        def view_example(self, example_name=None):
            """View the selected example's source code"""
            if not example_name:
                example_name = self.example_browser.get_selected_example()
            
            if not example_name:
                return
            
            example_path = Path(__file__).parent.parent.parent / "examples" / example_name
            
            try:
                with open(example_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.code_edit.setPlainText(content)
                self.highlighter.highlight_code(self.code_edit)
                self.tabs.setCurrentIndex(0)  # Switch to code tab
                
                self.statusBar().showMessage(f"Loaded {example_name}")
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to read {example_name}: {e}")
        
        def run_example(self):
            """Run the selected example"""
            example_name = self.example_browser.get_selected_example()
            
            if not example_name:
                QMessageBox.warning(self, "Warning", "Please select an example to run")
                return
            
            self.console.clear_output()
            self.console.append_line(f"=== Running {example_name} ===\n", COLORS['text_accent'])
            self.executor.run_example(example_name)
        
        def open_file(self):
            """Open a custom .sona file"""
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Open Sona File",
                str(Path(__file__).parent.parent.parent / "examples"),
                "Sona files (*.sona);;All files (*.*)"
            )
            
            if file_path:
                example_name = Path(file_path).name
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    self.code_edit.setPlainText(content)
                    self.highlighter.highlight_code(self.code_edit)
                    self.tabs.setCurrentIndex(0)  # Switch to code tab
                    
                    self.statusBar().showMessage(f"Loaded {example_name}")
                    
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to read {file_path}: {e}")
        
        def open_examples_folder(self):
            """Open the examples folder in file explorer"""
            examples_dir = Path(__file__).parent.parent.parent / "examples"
            
            if sys.platform == 'win32':
                os.startfile(examples_dir)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', examples_dir])
            else:  # Linux
                subprocess.run(['xdg-open', examples_dir])
        
        def show_about(self):
            """Show about dialog"""
            QMessageBox.about(self, "About Sona", 
                """<h3>Sona v0.7.0 - Modern Development Platform</h3>
                <p>A professional, modern application launcher built with PySide6.</p>
                <p><b>Features:</b></p>
                <ul>
                <li>Interactive application browser</li>
                <li>Real-time code execution</li>
                <li>Modern, responsive UI</li>
                <li>Syntax highlighting</li>
                </ul>
                <p>Built for the Sona Programming Language</p>""")


# Create a direct access class for importing 
class SonaModernLauncher(MainWindow):
    """Direct access class for the Sona Modern Launcher"""
    def __init__(self):
        super().__init__()
        

# Fallback to native UI if PySide6 is not available
class FallbackUI:
    """Fallback UI using native dialog when PySide6 is not available"""
    
    def __init__(self):
        import tkinter as tk
        from tkinter import messagebox
        
        # Create a hidden root window
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Show an error message
        messagebox.showinfo(
            "PySide6 Not Available",
            "The modern launcher requires PySide6, which is not installed.\n\n"
            "Please install PySide6 with:\npip install PySide6\n\n"
            "Launching the classic launcher instead..."
        )
        
        # Launch the classic launcher
        self.launch_classic()
    
    def launch_classic(self):
        """Launch the classic Tkinter-based launcher"""
        import runpy
        import importlib.util
        
        # Check if the classic launcher exists
        classic_launcher = Path(__file__).parent.parent / "gui_launcher.py"
        
        if classic_launcher.exists():
            # If it exists, run it
            try:
                # Exit this application's root
                if hasattr(self, 'root') and self.root:
                    self.root.destroy()
                
                # Run the classic launcher
                runpy.run_path(str(classic_launcher), run_name="__main__")
                return True
            except Exception as e:
                print(f"Error launching classic launcher: {e}")
                return False
        else:
            # If not, show an error
            if hasattr(self, 'root') and self.root:
                import tkinter.messagebox as mb
                mb.showerror(
                    "Launcher Error",
                    f"Could not find classic launcher at {classic_launcher}\n\n"
                    "Please reinstall the Sona platform."
                )
            return False


def main():
    """Main application entry point"""
    if PYSIDE6_AVAILABLE:
        app = QApplication(sys.argv)
        
        # Set application properties
        app.setApplicationName("Sona Modern Launcher")
        app.setApplicationVersion("0.7.0")
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Run application
        sys.exit(app.exec())
    else:
        # Use fallback UI
        FallbackUI()


if __name__ == "__main__":
    main()
