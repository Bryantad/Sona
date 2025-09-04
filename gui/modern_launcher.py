#!/usr/bin/env python3
"""
Sona Modern GUI Launcher v0.7.0 - PySide6 Edition

A production-ready, modern application launcher for Sona development.
Built with PySide6 for professional UI/UX and scalable architecture.
"""

import sys
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Any

try:
    from PySide6.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QDockWidget,
        QTreeWidget,
        QTreeWidgetItem,
        QPlainTextEdit,
        QLabel,
        QLineEdit,
        QComboBox,
        QPushButton,
        QStackedWidget,
        QFileDialog,
        QMessageBox,
    )
    from PySide6.QtCore import QObject, Qt, Signal
    from PySide6.QtGui import QFont, QColor, QTextCharFormat
    PYSIDE6_AVAILABLE = True
except ImportError:
    print("="*60)
    print("ERROR: PySide6 not found. Please install it using:")
    print("pip install PySide6")
    print("="*60)
    PYSIDE6_AVAILABLE = False
    
    # Simple Tkinter fallback for showing error
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        def show_error_and_exit():
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "PySide6 Not Found",
                "PySide6 is required but not installed.\n\n"
                "Please install it using:\npip install PySide6\n\n"
                "Then restart the application."
            )
            sys.exit(1)
    except ImportError:
        def show_error_and_exit():
            print("PySide6 is required.")
            print("Please install it using: pip install PySide6")
            sys.exit(1)

# UI / Release constants (studio vs language)
STUDIO_NAME = "Sona Studio 1.0 Beta"
STUDIO_DISPLAY_VERSION = "1.0.0-beta"
LANGUAGE_VERSION = "0.9.1"  # Sona language runtime remains at 0.9.1


class SonaTheme:
    """Modern dark theme configuration"""
    
    # Main color palette
    BACKGROUND_PRIMARY = "#0f1115"
    BACKGROUND_SECONDARY = "#151823"
    BACKGROUND_TERTIARY = "#111318"

    # Accent colors (neon-ish)
    ACCENT_PRIMARY = "#7c3aed"
    ACCENT_SECONDARY = "#22d3ee"
    ACCENT_SUCCESS = "#10b981"
    ACCENT_WARNING = "#f59e0b"
    ACCENT_ERROR = "#ef4444"
    
    # Text colors
    TEXT_PRIMARY = "#cdd6f4"
    TEXT_SECONDARY = "#bac2de"
    TEXT_MUTED = "#6c7086"
    TEXT_OVERLAY = "#9399b2"
    
    # UI element colors
    BORDER_COLOR = "#313244"
    HOVER_COLOR = "#45475a"
    SELECTION_COLOR = "#585b70"
    
    @classmethod
    def get_stylesheet(cls) -> str:
        """Generate complete QSS stylesheet"""
        # Keep stylesheet concise; colors come from the theme constants.
        return f"""
        /* Main Application Styling */
        QMainWindow {{
            background-color: {cls.BACKGROUND_PRIMARY};
            color: {cls.TEXT_PRIMARY};
            font-family: 'Segoe UI', sans-serif;
        }}
        
        /* Top Bar Styling */
        #topBar {{
            background-color: {cls.BACKGROUND_SECONDARY};
            border-bottom: 1px solid {cls.BORDER_COLOR};
            padding: 8px 16px;
            min-height: 50px;
        }}
        
        /* Sidebar Styling */
        QDockWidget {{
            background-color: {cls.BACKGROUND_SECONDARY};
            border: 1px solid {cls.BORDER_COLOR};
            titlebar-close-icon: none;
            titlebar-normal-icon: none;
        }}
        
        QDockWidget::title {{
            background-color: {cls.BACKGROUND_TERTIARY};
            padding: 8px 12px;
            border-bottom: 1px solid {cls.BORDER_COLOR};
        }}
        
        /* Tree Widget (Sidebar Menu) */
        QTreeWidget {{
            background-color: {cls.BACKGROUND_SECONDARY};
            border: none;
            outline: none;
            selection-background-color: {cls.SELECTION_COLOR};
            alternate-background-color: {cls.BACKGROUND_TERTIARY};
        }}
        
        QTreeWidget::item {{
            padding: 8px 12px;
            border: none;
            color: {cls.TEXT_SECONDARY};
        }}
        
        QTreeWidget::item:hover {{
            background-color: {cls.HOVER_COLOR};
        }}
        
        QTreeWidget::item:selected {{
            background-color: {cls.ACCENT_PRIMARY};
            color: {cls.BACKGROUND_PRIMARY};
        }}
        
    /* Default branch icons will be used; custom images removed for brevity */
        
        /* Buttons */
        QPushButton {{
            background-color: {cls.ACCENT_PRIMARY};
            color: {cls.BACKGROUND_PRIMARY};
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
            font-size: 13px;
        }}
        
        QPushButton:hover {{
            background-color: {cls.ACCENT_SECONDARY};
        }}
        
        QPushButton:pressed {{
            background-color: {cls.SELECTION_COLOR};
        }}
        
        QPushButton:disabled {{
            background-color: {cls.HOVER_COLOR};
            color: {cls.TEXT_MUTED};
        }}
        
        /* Special Button Styles */
        QPushButton#runButton {{
            background-color: {cls.ACCENT_SUCCESS};
            min-width: 80px;
        }}
        
        QPushButton#consoleButton {{
            background-color: {cls.BACKGROUND_TERTIARY};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER_COLOR};
        }}
        
        QPushButton#consoleButton:hover {{
            background-color: {cls.HOVER_COLOR};
        }}
        
        QPushButton#consoleButton:checked {{
            background-color: {cls.ACCENT_PRIMARY};
            color: {cls.BACKGROUND_PRIMARY};
        }}
        
        /* ComboBox */
        QComboBox {{
            background-color: {cls.BACKGROUND_TERTIARY};
            border: 1px solid {cls.BORDER_COLOR};
            border-radius: 4px;
            padding: 6px 12px;
            color: {cls.TEXT_PRIMARY};
            min-width: 120px;
        }}
        
        QComboBox:hover {{
            border-color: {cls.ACCENT_PRIMARY};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            width: 0px;
            height: 0px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {cls.BACKGROUND_SECONDARY};
            border: 1px solid {cls.BORDER_COLOR};
            selection-background-color: {cls.ACCENT_PRIMARY};
            color: {cls.TEXT_PRIMARY};
        }}
        
        /* Line Edit (Search) */
        QLineEdit {{
            background-color: {cls.BACKGROUND_TERTIARY};
            border: 1px solid {cls.BORDER_COLOR};
            border-radius: 4px;
            padding: 6px 12px;
            color: {cls.TEXT_PRIMARY};
        }}
        
        QLineEdit:focus {{
            border-color: {cls.ACCENT_PRIMARY};
        }}
        
        /* Splitter */
        QSplitter::handle {{
            background-color: {cls.BORDER_COLOR};
        }}
        
        QSplitter::handle:horizontal {{
            width: 1px;
        }}
        
        QSplitter::handle:vertical {{
            height: 1px;
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {cls.BACKGROUND_SECONDARY};
            border-top: 1px solid {cls.BORDER_COLOR};
            color: {cls.TEXT_MUTED};
            padding: 4px 12px;
        }}
        
        /* Text Areas */
        QTextEdit, QPlainTextEdit {{
            background-color: {cls.BACKGROUND_TERTIARY};
            border: 1px solid {cls.BORDER_COLOR};
            border-radius: 4px;
            color: {cls.TEXT_PRIMARY};
            selection-background-color: {cls.SELECTION_COLOR};
            font-family: 'Fira Code', 'Consolas', monospace;
        }}
        
        /* Scrollbars */
        QScrollBar:vertical {{
            background-color: {cls.BACKGROUND_SECONDARY};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {cls.HOVER_COLOR};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {cls.SELECTION_COLOR};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background-color: {cls.BACKGROUND_SECONDARY};
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {cls.HOVER_COLOR};
            border-radius: 6px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {cls.SELECTION_COLOR};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        
        /* Menu Bar */
        QMenuBar {{
            background-color: {cls.BACKGROUND_SECONDARY};
            color: {cls.TEXT_PRIMARY};
            border-bottom: 1px solid {cls.BORDER_COLOR};
        }}
        
        QMenuBar::item {{
            padding: 8px 12px;
            background-color: transparent;
        }}
        
        QMenuBar::item:selected {{
            background-color: {cls.HOVER_COLOR};
        }}
        
        QMenu {{
            background-color: {cls.BACKGROUND_SECONDARY};
            border: 1px solid {cls.BORDER_COLOR};
            color: {cls.TEXT_PRIMARY};
        }}
        
        QMenu::item {{
            padding: 6px 20px;
        }}
        
        QMenu::item:selected {{
            background-color: {cls.ACCENT_PRIMARY};
            color: {cls.BACKGROUND_PRIMARY};
        }}
        
        /* Labels */
        QLabel {{
            color: {cls.TEXT_PRIMARY};
        }}
        
        QLabel#titleLabel {{
            font-size: 16px;
            font-weight: bold;
            color: {cls.ACCENT_PRIMARY};
        }}
        
        QLabel#subtitleLabel {{
            color: {cls.TEXT_SECONDARY};
            font-size: 11px;
        }}
        """


class ExecutionMode:
    """Execution mode constants"""
    SANDBOX = "Sandbox"
    NATIVE = "Native"
    REMOTE = "Remote"


class AppCategory:
    """Application category data structure"""
    def __init__(self, name: str, icon: str, apps: List[Dict[str, Any]]):
        self.name = name
        self.icon = icon
        self.apps = apps


class ExecutionController(QObject):
    """Central controller for handling execution logic"""
    
    output_ready = Signal(str)
    error_ready = Signal(str)
    execution_started = Signal()
    execution_finished = Signal(int)
    
    def __init__(self):
        super().__init__()
        self.current_mode = ExecutionMode.SANDBOX
        self.sona_dir = Path(__file__).parent.parent
        self.examples_dir = self.sona_dir / "examples"
        
    def set_execution_mode(self, mode: str):
        """Set the current execution mode"""
        self.current_mode = mode
        
    def execute_file(self, file_path: str):
        """Execute a Sona file in a separate thread"""
        def run_process():
            try:
                self.execution_started.emit()
                
                # Prepare execution command based on mode
                if self.current_mode == ExecutionMode.SANDBOX:
                    cmd = [sys.executable, "-m", "sona", file_path]
                elif self.current_mode == ExecutionMode.NATIVE:
                    cmd = [sys.executable, "-m", "sona", "--native", file_path]
                else:  # Remote mode
                    cmd = [sys.executable, "-m", "sona", "--remote", file_path]
                
                # Execute process
                process = subprocess.Popen(
                    cmd,
                    cwd=str(self.sona_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Stream output in real-time
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        self.output_ready.emit(output.strip())
                
                # Get any remaining output
                stdout, stderr = process.communicate()
                if stdout:
                    self.output_ready.emit(stdout)
                if stderr:
                    self.error_ready.emit(stderr)
                
                self.execution_finished.emit(process.returncode)
                
            except Exception as e:
                self.error_ready.emit(f"Execution error: {str(e)}")
                self.execution_finished.emit(-1)
        
        # Run in separate thread
        thread = threading.Thread(target=run_process, daemon=True)
        thread.start()


class ConsoleDock(QDockWidget):
    """Floating/dockable console for output display"""
    
    def __init__(self, parent=None):
        super().__init__("Console Output", parent)
        
        # Configure dock widget
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetMovable | 
                        QDockWidget.DockWidgetClosable |
                        QDockWidget.DockWidgetFloatable)
        
        # Create console widget
        self.console_widget = QWidget()
        self.setWidget(self.console_widget)
        
        # Layout
        layout = QVBoxLayout(self.console_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Console controls
        controls_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_console)
        
        self.copy_button = QPushButton("Copy All")
        self.copy_button.clicked.connect(self.copy_console)
        
        self.pin_button = QPushButton("📌 Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.toggled.connect(self.toggle_pin)
        
        controls_layout.addWidget(self.clear_button)
        controls_layout.addWidget(self.copy_button)
        controls_layout.addWidget(self.pin_button)
        controls_layout.addStretch()
        
        # Console output area
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumBlockCount(1000)  # Limit output for performance
        
        # Configure text formatting
        font = QFont("Fira Code", 10)
        font.setStyleHint(QFont.Monospace)
        self.output_text.setFont(font)
        
        layout.addLayout(controls_layout)
        layout.addWidget(self.output_text)
        
        # Initially hidden
        self.hide()
        
    def append_output(self, text: str):
        """Append text to console output"""
        self.output_text.appendPlainText(text)
        
    def append_error(self, text: str):
        """Append error text to console output"""
        # Format error text in red
        cursor = self.output_text.textCursor()
        cursor.movePosition(cursor.End)
        
        char_format = QTextCharFormat()
        char_format.setForeground(QColor(SonaTheme.ACCENT_ERROR))
        
        cursor.insertText(f"ERROR: {text}\n", char_format)
        self.output_text.setTextCursor(cursor)
        
    def clear_console(self):
        """Clear console output"""
        self.output_text.clear()
        
    def copy_console(self):
        """Copy all console text to clipboard"""
        QApplication.clipboard().setText(self.output_text.toPlainText())
        
    def toggle_pin(self, pinned: bool):
        """Toggle console pinning"""
        if pinned:
            self.pin_button.setText("📌 Pinned")
            self.setFeatures(QDockWidget.DockWidgetMovable)
        else:
            self.pin_button.setText("📌 Pin")
            self.setFeatures(QDockWidget.DockWidgetMovable | 
                           QDockWidget.DockWidgetClosable |
                           QDockWidget.DockWidgetFloatable)


class Sidebar(QDockWidget):
    """Collapsible sidebar with categorized app menu"""
    
    app_selected = Signal(str, str)  # app_name, app_path
    
    def __init__(self, parent=None):
        super().__init__("Applications", parent)
        
        # Configure dock widget
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetMovable)
        
        # Create main widget
        self.sidebar_widget = QWidget()
        self.setWidget(self.sidebar_widget)
        
        # Layout
        layout = QVBoxLayout(self.sidebar_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Search bar
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search applications...")
        self.search_edit.textChanged.connect(self.filter_apps)
        layout.addWidget(self.search_edit)
        
        # Application tree
        self.app_tree = QTreeWidget()
        self.app_tree.setHeaderHidden(True)
        self.app_tree.setAlternatingRowColors(True)
        self.app_tree.itemClicked.connect(self.on_app_selected)
        layout.addWidget(self.app_tree)
        
        # Load applications
        self.load_applications()
        
    def load_applications(self):
        """Load applications into tree structure"""
        # Define application categories
        categories = [
            AppCategory("🎮 Games", "games", [
                {"name": "Tetris", "file": "tetris.sona", "description": "Classic puzzle game"},
                {"name": "Snake", "file": "snake_game.sona", "description": "Classic snake game"},
                {"name": "Ping Pong", "file": "ping_pong.sona", "description": "Table tennis game"},
                {"name": "Space Shooter", "file": "space_shooter.sona", "description": "Arcade shooter"},
                {"name": "Flappy Bird", "file": "flappy_bird.sona", "description": "Flying challenge"},
                {"name": "Invaders", "file": "invaders.sona", "description": "Space invaders clone"},
                {"name": "Doom 2D", "file": "doom_2d.sona", "description": "2D shooter game"},
                {"name": "Bejeweled", "file": "bejeweled.sona", "description": "Match-3 puzzle"},
                {"name": "Solitaire", "file": "solitaire.sona", "description": "Card game"},
                {"name": "Mahjong", "file": "mahjong.sona", "description": "Tile matching"},
                {"name": "Bubble Shooter", "file": "bubble_shooter.sona", "description": "Bubble popping"},
                {"name": "Sudoku", "file": "sudoku.sona", "description": "Number puzzle"},
            ]),
            AppCategory("🛠️ Tools", "tools", [
                {"name": "Calculator", "file": "calculator.sona", "description": "Scientific calculator"},
                {"name": "Text Editor", "file": "text_editor.sona", "description": "Code editor"},
                {"name": "File Organizer", "file": "file_organizer.sona", "description": "File management"},
                {"name": "Media Player", "file": "media_player.sona", "description": "Audio/video player"},
                {"name": "Painter", "file": "painter.sona", "description": "Digital drawing"},
            ]),
            AppCategory("📊 Data Apps", "data", [
                {"name": "Todo Manager", "file": "todo_manager.sona", "description": "Task management"},
                {"name": "Notes Manager", "file": "notes_manager.sona", "description": "Note taking"},
                {"name": "Calendar", "file": "calendar.sona", "description": "Schedule management"},
            ]),
            AppCategory("📚 Tutorials", "tutorials", [
                {"name": "Hello World", "file": "hello_world.sona", "description": "Basic example"},
                {"name": "Basic Syntax", "file": "basic_syntax.sona", "description": "Language syntax"},
                {"name": "Dictionary Operations", "file": "dictionary_operations.sona", "description": "Data structures"},
                {"name": "Module Demo", "file": "module_demo.sona", "description": "Module system"},
                {"name": "Data Processing", "file": "data_processing.sona", "description": "Data handling"},
                {"name": "Error Handling", "file": "error_handling.sona", "description": "Error management"},
            ])
        ]
        
        # Populate tree
        for category in categories:
            category_item = QTreeWidgetItem(self.app_tree)
            category_item.setText(0, category.name)
            category_item.setData(0, Qt.UserRole, {"type": "category", "name": category.name})
            
            # Set category styling
            font = category_item.font(0)
            font.setBold(True)
            category_item.setFont(0, font)
            
            # Add apps
            for app in category.apps:
                app_item = QTreeWidgetItem(category_item)
                app_item.setText(0, app["name"])
                app_item.setData(0, Qt.UserRole, {
                    "type": "app",
                    "name": app["name"],
                    "file": app["file"],
                    "description": app["description"],
                    "category": category.name
                })
                
                # Set tooltip
                app_item.setToolTip(0, app["description"])
        
        # Expand all categories by default
        self.app_tree.expandAll()
        
    def filter_apps(self, text: str):
        """Filter applications based on search text"""
        # Simple filter implementation
        # Hide/show items based on search text
        for i in range(self.app_tree.topLevelItemCount()):
            category_item = self.app_tree.topLevelItem(i)
            category_visible = False
            
            for j in range(category_item.childCount()):
                app_item = category_item.child(j)
                app_data = app_item.data(0, Qt.UserRole)
                
                if not text or text.lower() in app_data["name"].lower():
                    app_item.setHidden(False)
                    category_visible = True
                else:
                    app_item.setHidden(True)
            
            category_item.setHidden(not category_visible)
            
    def on_app_selected(self, item: QTreeWidgetItem, column: int):
        """Handle app selection"""
        data = item.data(0, Qt.UserRole)
        if data and data["type"] == "app":
            # Find the app file
            sona_dir = Path(__file__).parent.parent
            examples_dir = sona_dir / "examples"
            app_path = examples_dir / data["file"]
            
            self.app_selected.emit(data["name"], str(app_path))


class AppDisplay(QStackedWidget):
    """Main display area for apps and code"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Welcome page
        self.welcome_page = self.create_welcome_page()
        self.addWidget(self.welcome_page)
        
        # Code editor page
        self.code_page = self.create_code_page()
        self.addWidget(self.code_page)
        
        # Embedded app page
        self.app_page = self.create_app_page()
        self.addWidget(self.app_page)
        
        # Set initial page
        self.setCurrentWidget(self.welcome_page)
        
    def create_welcome_page(self) -> QWidget:
        """Create welcome/dashboard page"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # Welcome content
        title = QLabel(f"Welcome to {STUDIO_NAME}")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("Professional • Modern • Extensible")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)
        
        description = QLabel("""
        Select an application from the sidebar to get started.
        
        • Browse interactive games and tools
        • View source code with syntax highlighting
        • Run applications in different execution modes
        • Monitor output in real-time console
        """)
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(30)
        layout.addWidget(description)
        
        return widget
        
    def create_code_page(self) -> QWidget:
        """Create code editor page"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # File info
        self.file_info_label = QLabel("No file selected")
        layout.addWidget(self.file_info_label)
        
        # Code editor
        self.code_editor = QPlainTextEdit()
        self.code_editor.setReadOnly(True)
        
        # Set monospace font
        font = QFont("Fira Code", 11)
        font.setStyleHint(QFont.Monospace)
        self.code_editor.setFont(font)
        
        layout.addWidget(self.code_editor)
        
        return widget
        
    def create_app_page(self) -> QWidget:
        """Create embedded app page"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # App container (will be filled by embedded apps)
        self.app_container = QWidget()
        self.app_container.setStyleSheet(f"background-color: {SonaTheme.BACKGROUND_TERTIARY};")
        
        layout.addWidget(self.app_container)
        
        return widget
        
    def show_welcome(self):
        """Show welcome page"""
        self.setCurrentWidget(self.welcome_page)
        
    def show_code(self, file_path: str):
        """Show code for file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.file_info_label.setText(f"File: {Path(file_path).name}")
            self.code_editor.setPlainText(content)
            self.setCurrentWidget(self.code_page)
            
        except Exception as e:
            self.file_info_label.setText(f"Error loading file: {e}")
            self.code_editor.setPlainText("")
            
    def show_embedded_app(self, app_name: str):
        """Show embedded application"""
        # Clear existing content
        layout = self.app_container.layout()
        if layout:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            layout = QVBoxLayout(self.app_container)
            layout.setContentsMargins(0, 0, 0, 0)
        
        # Create app placeholder (would be replaced with actual embedded apps)
        app_label = QLabel(f"🎮 {app_name}")
        app_label.setAlignment(Qt.AlignCenter)
        app_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {SonaTheme.ACCENT_PRIMARY};
            padding: 40px;
        """)
        
        demo_label = QLabel("Interactive app would be embedded here")
        demo_label.setAlignment(Qt.AlignCenter)
        demo_label.setStyleSheet(f"color: {SonaTheme.TEXT_SECONDARY};")
        
        layout.addWidget(app_label)
        layout.addWidget(demo_label)
        layout.addStretch()
        
        self.setCurrentWidget(self.app_page)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        # Initialize components
        self.execution_controller = ExecutionController()
        self.current_file = None

        # Setup UI
        self.setup_ui()
        self.setup_connections()

        # Apply theme
        self.setStyleSheet(SonaTheme.get_stylesheet())

        # Window properties
        self.setWindowTitle(f"{STUDIO_NAME} - Modern Development Platform")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
    def setup_ui(self):
        """Setup the main UI layout"""
        # Central widget (app display)
        self.app_display = AppDisplay()
        self.setCentralWidget(self.app_display)
        
        # Create top bar
        self.create_top_bar()
        
        # Create sidebar
        self.sidebar = Sidebar()
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar)
        
        # Create console dock
        self.console_dock = ConsoleDock()
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console_dock)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.create_status_bar()
        
    def create_top_bar(self):
        """Create the top control bar"""
        # Top bar widget
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(60)

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(12, 6, 12, 6)

        # Left: window control dots + breadcrumbs
        left = QWidget()
        left_layout = QHBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        for color in ("#ff5f57", "#febc2e", "#28c840"):
            dot = QLabel()
            dot.setFixedSize(12, 12)
            dot.setStyleSheet(f"background:{color};border-radius:6px;")
            left_layout.addWidget(dot)

        crumbs = QLabel(f"<b>{STUDIO_NAME}</b> &nbsp; › &nbsp; apps &nbsp; › &nbsp; ide &nbsp; › &nbsp; renderer.tsx")
        crumbs.setStyleSheet(f"color: {SonaTheme.TEXT_SECONDARY};")
        left_layout.addWidget(crumbs)
        left_layout.addStretch()
        layout.addWidget(left, 1)

        # Middle spacer
        layout.addStretch()

        # Right controls: mode, console, run, theme/actions
        mode_label = QLabel("Mode:")
        layout.addWidget(mode_label)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems([ExecutionMode.SANDBOX, ExecutionMode.NATIVE, ExecutionMode.REMOTE])
        self.mode_combo.setCurrentText(ExecutionMode.SANDBOX)
        layout.addWidget(self.mode_combo)

        layout.addSpacing(12)

        self.console_button = QPushButton("</> Console")
        self.console_button.setObjectName("consoleButton")
        self.console_button.setCheckable(True)
        layout.addWidget(self.console_button)

        layout.addSpacing(6)

        self.run_button = QPushButton("🔵 Run")
        self.run_button.setObjectName("runButton")
        self.run_button.setEnabled(False)
        layout.addWidget(self.run_button)

        # Theme/action buttons
        self.toggle_welcome_btn = QPushButton("Welcome Hub")
        self.toggle_welcome_btn.setObjectName("toggleWelcome")
        layout.addWidget(self.toggle_welcome_btn)

        self.theme_base_btn = QPushButton("Glass")
        self.theme_base_btn.setObjectName("themeBase")
        layout.addWidget(self.theme_base_btn)

        self.theme_neon_btn = QPushButton("Neon")
        self.theme_neon_btn.setObjectName("themeNeon")
        layout.addWidget(self.theme_neon_btn)

        self.theme_zen_btn = QPushButton("Zen")
        self.theme_zen_btn.setObjectName("themeZen")
        layout.addWidget(self.theme_zen_btn)

        # Add to main window as toolbar
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.addWidget(top_bar)

        # Create welcome overlay
        self.create_welcome_overlay()
        
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction("Open File...", self.open_file, "Ctrl+O")
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close, "Ctrl+Q")
        
        # View menu
        view_menu = menubar.addMenu("View")
        view_menu.addAction("Toggle Sidebar", self.toggle_sidebar, "Ctrl+1")
        view_menu.addAction("Toggle Console", self.toggle_console, "Ctrl+2")
        view_menu.addSeparator()
        view_menu.addAction("Reset Layout", self.reset_layout)
        
        # Run menu
        run_menu = menubar.addMenu("Run")
        run_menu.addAction("Run Current", self.run_current, "F5")
        run_menu.addAction("Stop Execution", self.stop_execution, "Ctrl+C")
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        help_menu.addAction("About Sona", self.show_about)
        help_menu.addAction("Documentation", self.show_docs)
        
    def create_status_bar(self):
        """Create the status bar"""
        status_bar = self.statusBar()
        
        # Current file
        self.file_status = QLabel("No file selected")
        status_bar.addWidget(self.file_status)
        
        # Spacer
        status_bar.addPermanentWidget(QLabel("  |  "))
        
        # Memory usage (placeholder)
        self.memory_status = QLabel("Memory: 0 MB")
        status_bar.addPermanentWidget(self.memory_status)
        
        # Version info
        status_bar.addPermanentWidget(QLabel(f"  |  Language v{LANGUAGE_VERSION} | {STUDIO_DISPLAY_VERSION}"))
        
    def setup_connections(self):
        """Setup signal/slot connections"""
        # Execution controller connections
        self.execution_controller.output_ready.connect(self.console_dock.append_output)
        self.execution_controller.error_ready.connect(self.console_dock.append_error)
        self.execution_controller.execution_started.connect(self.on_execution_started)
        self.execution_controller.execution_finished.connect(self.on_execution_finished)
        
        # UI connections
        self.sidebar.app_selected.connect(self.on_app_selected)
        self.run_button.clicked.connect(self.run_current)
        self.console_button.toggled.connect(self.toggle_console)
        self.mode_combo.currentTextChanged.connect(self.execution_controller.set_execution_mode)
        # Theme / welcome handlers (connected only if buttons exist)
        if hasattr(self, 'toggle_welcome_btn'):
            self.toggle_welcome_btn.clicked.connect(self.toggle_welcome)
        if hasattr(self, 'theme_base_btn'):
            self.theme_base_btn.clicked.connect(self.apply_theme_base)
        if hasattr(self, 'theme_neon_btn'):
            self.theme_neon_btn.clicked.connect(self.apply_theme_neon)
        if hasattr(self, 'theme_zen_btn'):
            self.theme_zen_btn.clicked.connect(self.apply_theme_zen)
        
    def on_app_selected(self, app_name: str, app_path: str):
        """Handle application selection"""
        self.current_file = app_path
        self.file_status.setText(f"Selected: {Path(app_path).name}")
        self.run_button.setEnabled(True)
        
        # Determine display mode based on app type
        if any(game in app_name.lower() for game in ["tetris", "snake", "pong", "shooter", "flappy", "invaders", "doom", "bejeweled", "solitaire", "mahjong", "bubble", "sudoku"]):
            # Show as embedded app
            self.app_display.show_embedded_app(app_name)
        else:
            # Show as code
            self.app_display.show_code(app_path)
    
    def run_current(self):
        """Run the currently selected file"""
        if self.current_file:
            # Show console if hidden
            if not self.console_dock.isVisible():
                self.console_dock.show()
                self.console_button.setChecked(True)
            
            # Clear previous output
            self.console_dock.clear_console()
            
            # Execute file
            self.execution_controller.execute_file(self.current_file)
    
    def stop_execution(self):
        """Stop current execution (placeholder)"""
        # Would implement process termination
        pass
    
    def on_execution_started(self):
        """Handle execution start"""
        self.run_button.setText("⏸️ Running...")
        self.run_button.setEnabled(False)
        
    def on_execution_finished(self, return_code: int):
        """Handle execution completion"""
        self.run_button.setText("🔵 Run")
        self.run_button.setEnabled(True)
        
        if return_code == 0:
            self.console_dock.append_output("\\n✅ Execution completed successfully")
        else:
            self.console_dock.append_error(f"Execution failed with code {return_code}")
    
    def toggle_sidebar(self):
        """Toggle sidebar visibility"""
        self.sidebar.setVisible(not self.sidebar.isVisible())
    
    def toggle_console(self, show: bool = None):
        """Toggle console visibility"""
        if show is None:
            show = not self.console_dock.isVisible()
        
        self.console_dock.setVisible(show)
        self.console_button.setChecked(show)
    
    def reset_layout(self):
        """Reset dock layout to default"""
        self.sidebar.setVisible(True)
        self.console_dock.setVisible(False)
        self.console_button.setChecked(False)
        
        # Reset dock positions
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console_dock)
    
    def open_file(self):
        """Open file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Sona File",
            str(Path(__file__).parent.parent / "examples"),
            "Sona Files (*.sona);;All Files (*)"
        )
        
        if file_path:
            self.current_file = file_path
            self.file_status.setText(f"Selected: {Path(file_path).name}")
            self.run_button.setEnabled(True)
            self.app_display.show_code(file_path)

    # --- Welcome overlay and theme helpers (UI-only) ---
    def create_welcome_overlay(self):
        """Create a welcome overlay widget that can be toggled"""
        self.welcome_wrap = QWidget(self)
        self.welcome_wrap.setObjectName('welcomeWrap')
        self.welcome_wrap.setStyleSheet('background: transparent;')
        self.welcome_wrap.setVisible(False)

        # Simple centered label/card
        welcome = QLabel("Welcome to " + STUDIO_NAME, self.welcome_wrap)
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setStyleSheet(f"color: {SonaTheme.TEXT_PRIMARY}; background: rgba(12,14,21,.85); padding: 24px; border-radius: 16px; border: 1px solid {SonaTheme.BORDER_COLOR};")
        welcome.setFixedSize(800, 420)
        welcome.move((self.width() - welcome.width())//2, (self.height() - welcome.height())//2)

    def toggle_welcome(self):
        if hasattr(self, 'welcome_wrap'):
            self.welcome_wrap.setVisible(not self.welcome_wrap.isVisible())

    def apply_theme_base(self):
        # keep default theme
        self.setStyleSheet(SonaTheme.get_stylesheet())

    def apply_theme_neon(self):
        # apply neon variant by tweaking palette — simple example
        neon_styles = SonaTheme.get_stylesheet() + "\nQMainWindow { background: linear-gradient(180deg,#07070a,#0f1115); }"
        self.setStyleSheet(neon_styles)

    def apply_theme_zen(self):
        zen_styles = SonaTheme.get_stylesheet() + "\nQMainWindow { background: linear-gradient(180deg,#0b0d10,#0b0d10); }"
        self.setStyleSheet(zen_styles)
    
    def show_about(self):
        """Show about dialog"""
        about_html = (
            f"<h3>{STUDIO_NAME} - Modern Development Platform</h3>"
            f"<p>A professional, modern application launcher built with PySide6.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Interactive application browser</li>"
            "<li>Real-time code execution</li>"
            "<li>Embedded game and tool support</li>"
            "<li>Modern, responsive UI</li>"
            "<li>Multiple execution modes</li>"
            "</ul>"
            f"<p>Built for Sona Language v{LANGUAGE_VERSION}</p>"
        )

        QMessageBox.about(self, "About Sona", about_html)
    
    def show_docs(self):
        """Show documentation (placeholder)"""
        QMessageBox.information(self, "Documentation", 
                               "Documentation would open here or in browser.")


def main():
    """Main application entry point"""
    if not PYSIDE6_AVAILABLE:
        show_error_and_exit()
        return

    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName(STUDIO_NAME)
    app.setApplicationVersion(STUDIO_DISPLAY_VERSION)
    app.setOrganizationName("Sona Platform")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
