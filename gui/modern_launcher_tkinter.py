#!/usr/bin/env python3
"""
Sona Modern GUI Launcher v0.7.0 - Enhanced Tkinter Edition

A modern, production-ready application launcher for Sona development.
Enhanced Tkinter version with modern design patterns and UI/UX improvements.

This version provides the modern architecture and visual design while
maintaining compatibility with Tkinter. For the full PySide6 experience,
see modern_launcher.py (requires: pip install PySide6)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import sys
import os
import subprocess
import threading
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import time


class ModernTheme:
    """Modern dark theme configuration for Tkinter"""
    
    # Color palette matching the PySide6 version
    BACKGROUND_PRIMARY = "#1e1e2e"
    BACKGROUND_SECONDARY = "#181825" 
    BACKGROUND_TERTIARY = "#11111b"
    
    ACCENT_PRIMARY = "#89b4fa"
    ACCENT_SECONDARY = "#74c7ec"
    ACCENT_SUCCESS = "#a6e3a1"
    ACCENT_WARNING = "#f9e2af"
    ACCENT_ERROR = "#f38ba8"
    
    TEXT_PRIMARY = "#cdd6f4"
    TEXT_SECONDARY = "#bac2de"
    TEXT_MUTED = "#6c7086"
    
    BORDER_COLOR = "#313244"
    HOVER_COLOR = "#45475a"
    SELECTION_COLOR = "#585b70"


class ExecutionMode:
    """Execution mode constants"""
    SANDBOX = "Sandbox"
    NATIVE = "Native" 
    REMOTE = "Remote"


class ExecutionController:
    """Central controller for handling execution logic"""
    
    def __init__(self, output_callback=None, error_callback=None, 
                 start_callback=None, finish_callback=None):
        self.current_mode = ExecutionMode.SANDBOX
        self.sona_dir = Path(__file__).parent.parent
        self.examples_dir = self.sona_dir / "examples"
        self.is_running = False
        
        # Callbacks
        self.output_callback = output_callback
        self.error_callback = error_callback
        self.start_callback = start_callback
        self.finish_callback = finish_callback
        
    def set_execution_mode(self, mode: str):
        """Set the current execution mode"""
        self.current_mode = mode
        
    def execute_file(self, file_path: str):
        """Execute a Sona file in a separate thread"""
        if self.is_running:
            return
            
        def run_process():
            try:
                self.is_running = True
                if self.start_callback:
                    self.start_callback()
                
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
                    text=True
                )
                
                # Get output
                stdout, stderr = process.communicate()
                
                if stdout and self.output_callback:
                    self.output_callback(stdout)
                if stderr and self.error_callback:
                    self.error_callback(stderr)
                
                if self.finish_callback:
                    self.finish_callback(process.returncode)
                
            except Exception as e:
                if self.error_callback:
                    self.error_callback(f"Execution error: {str(e)}")
                if self.finish_callback:
                    self.finish_callback(-1)
            finally:
                self.is_running = False
        
        # Run in separate thread
        thread = threading.Thread(target=run_process, daemon=True)
        thread.start()
        
    def stop_execution(self):
        """Stop current execution"""
        # Placeholder - would implement process termination
        self.is_running = False


class ModernConsole:
    """Modern console widget with enhanced functionality"""
    
    def __init__(self, parent):
        self.parent = parent
        self.is_visible = False
        self.is_pinned = False
        
        # Create console window (initially hidden)
        self.window = tk.Toplevel(parent)
        self.window.title("Console Output")
        self.window.geometry("800x300")
        self.window.configure(bg=ModernTheme.BACKGROUND_SECONDARY)
        
        # Hide initially
        self.window.withdraw()
        
        # Setup console UI
        self.setup_ui()
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.hide_console)
        
    def setup_ui(self):
        """Setup console UI"""
        # Main frame
        main_frame = tk.Frame(self.window, bg=ModernTheme.BACKGROUND_SECONDARY)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Controls frame
        controls_frame = tk.Frame(main_frame, bg=ModernTheme.BACKGROUND_SECONDARY)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Control buttons
        self.clear_button = tk.Button(
            controls_frame,
            text="Clear",
            bg=ModernTheme.ACCENT_ERROR,
            fg=ModernTheme.BACKGROUND_PRIMARY,
            activebackground=ModernTheme.ACCENT_WARNING,
            border=0,
            padx=15,
            pady=5,
            font=('Segoe UI', 10, 'bold'),
            command=self.clear_console
        )
        self.clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.copy_button = tk.Button(
            controls_frame,
            text="Copy All",
            bg=ModernTheme.ACCENT_PRIMARY,
            fg=ModernTheme.BACKGROUND_PRIMARY,
            activebackground=ModernTheme.ACCENT_SECONDARY,
            border=0,
            padx=15,
            pady=5,
            font=('Segoe UI', 10, 'bold'),
            command=self.copy_console
        )
        self.copy_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.pin_button = tk.Button(
            controls_frame,
            text="📌 Pin",
            bg=ModernTheme.BACKGROUND_TERTIARY,
            fg=ModernTheme.TEXT_PRIMARY,
            activebackground=ModernTheme.HOVER_COLOR,
            border=0,
            padx=15,
            pady=5,
            font=('Segoe UI', 10),
            command=self.toggle_pin
        )
        self.pin_button.pack(side=tk.LEFT)
        
        # Status label
        self.status_label = tk.Label(
            controls_frame,
            text="● Ready",
            bg=ModernTheme.BACKGROUND_SECONDARY,
            fg=ModernTheme.ACCENT_SUCCESS,
            font=('Segoe UI', 10, 'bold')
        )
        self.status_label.pack(side=tk.RIGHT)
        
        # Console output
        self.output_text = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            bg=ModernTheme.BACKGROUND_TERTIARY,
            fg=ModernTheme.TEXT_PRIMARY,
            insertbackground=ModernTheme.ACCENT_PRIMARY,
            selectbackground=ModernTheme.SELECTION_COLOR,
            font=('Fira Code', 10),
            border=0,
            relief='flat'
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags
        self.output_text.tag_configure("error", foreground=ModernTheme.ACCENT_ERROR)
        self.output_text.tag_configure("success", foreground=ModernTheme.ACCENT_SUCCESS)
        self.output_text.tag_configure("warning", foreground=ModernTheme.ACCENT_WARNING)
        
    def show_console(self):
        """Show the console"""
        if not self.is_visible:
            self.window.deiconify()
            self.window.lift()
            self.is_visible = True
            
    def hide_console(self):
        """Hide the console"""
        if not self.is_pinned:
            self.window.withdraw()
            self.is_visible = False
            
    def toggle_console(self):
        """Toggle console visibility"""
        if self.is_visible:
            self.hide_console()
        else:
            self.show_console()
            
    def append_output(self, text: str):
        """Append text to console"""
        self.output_text.insert(tk.END, text + "\\n")
        self.output_text.see(tk.END)
        
    def append_error(self, text: str):
        """Append error text to console"""
        self.output_text.insert(tk.END, f"ERROR: {text}\\n", "error")
        self.output_text.see(tk.END)
        
    def clear_console(self):
        """Clear console output"""
        self.output_text.delete(1.0, tk.END)
        
    def copy_console(self):
        """Copy console text to clipboard"""
        text = self.output_text.get(1.0, tk.END)
        self.window.clipboard_clear()
        self.window.clipboard_append(text)
        
    def toggle_pin(self):
        """Toggle console pinning"""
        self.is_pinned = not self.is_pinned
        if self.is_pinned:
            self.pin_button.config(text="📌 Pinned", bg=ModernTheme.ACCENT_PRIMARY)
        else:
            self.pin_button.config(text="📌 Pin", bg=ModernTheme.BACKGROUND_TERTIARY)
            
    def set_status(self, status: str, color: str = None):
        """Set console status"""
        if color is None:
            color = ModernTheme.TEXT_PRIMARY
        self.status_label.config(text=status, fg=color)


class ModernSidebar:
    """Modern collapsible sidebar with app categories"""
    
    def __init__(self, parent, selection_callback=None):
        self.parent = parent
        self.selection_callback = selection_callback
        self.is_visible = True
        
        # Create sidebar frame
        self.frame = tk.Frame(parent, bg=ModernTheme.BACKGROUND_SECONDARY, width=280)
        self.frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 1))
        self.frame.pack_propagate(False)
        
        # Setup UI
        self.setup_ui()
        
        # Load applications
        self.load_applications()
        
    def setup_ui(self):
        """Setup sidebar UI"""
        # Title
        title_frame = tk.Frame(self.frame, bg=ModernTheme.BACKGROUND_SECONDARY)
        title_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        title_label = tk.Label(
            title_frame,
            text="Applications",
            bg=ModernTheme.BACKGROUND_SECONDARY,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 14, 'bold')
        )
        title_label.pack(side=tk.LEFT)
        
        # Search frame
        search_frame = tk.Frame(self.frame, bg=ModernTheme.BACKGROUND_SECONDARY)
        search_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Search icon
        search_icon = tk.Label(
            search_frame,
            text="🔍",
            bg=ModernTheme.BACKGROUND_SECONDARY,
            fg=ModernTheme.TEXT_MUTED,
            font=('Segoe UI', 12)
        )
        search_icon.pack(side=tk.LEFT, padx=(0, 5))
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            bg=ModernTheme.BACKGROUND_TERTIARY,
            fg=ModernTheme.TEXT_PRIMARY,
            insertbackground=ModernTheme.ACCENT_PRIMARY,
            border=0,
            font=('Segoe UI', 10),
            relief='flat'
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, ipadx=10)
        self.search_entry.bind('<KeyRelease>', self.filter_apps)
        
        # App tree frame
        tree_frame = tk.Frame(self.frame, bg=ModernTheme.BACKGROUND_SECONDARY)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Create tree (using Treeview for better hierarchy support)
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure Treeview style
        style.configure("Modern.Treeview",
                       background=ModernTheme.BACKGROUND_SECONDARY,
                       foreground=ModernTheme.TEXT_PRIMARY,
                       fieldbackground=ModernTheme.BACKGROUND_SECONDARY,
                       borderwidth=0,
                       relief='flat')
        
        style.configure("Modern.Treeview.Heading",
                       background=ModernTheme.BACKGROUND_TERTIARY,
                       foreground=ModernTheme.TEXT_PRIMARY,
                       borderwidth=0)
        
        self.app_tree = ttk.Treeview(tree_frame, style="Modern.Treeview", show='tree')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.app_tree.yview)
        self.app_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.app_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection
        self.app_tree.bind('<<TreeviewSelect>>', self.on_app_selected)
        
    def load_applications(self):
        """Load applications from configuration"""
        # Define application categories (same as PySide6 version)
        categories = [
            {
                "name": "🎮 Games",
                "apps": [
                    {"name": "Tetris", "file": "tetris.sona", "type": "game"},
                    {"name": "Snake Game", "file": "snake_game.sona", "type": "game"},
                    {"name": "Ping Pong", "file": "ping_pong.sona", "type": "game"},
                    {"name": "Space Shooter", "file": "space_shooter.sona", "type": "game"},
                    {"name": "Flappy Bird", "file": "flappy_bird.sona", "type": "game"},
                    {"name": "Space Invaders", "file": "invaders.sona", "type": "game"},
                    {"name": "Doom 2D", "file": "doom_2d.sona", "type": "game"},
                    {"name": "Bejeweled", "file": "bejeweled.sona", "type": "game"},
                    {"name": "Solitaire", "file": "solitaire.sona", "type": "game"},
                    {"name": "Sudoku", "file": "sudoku.sona", "type": "game"},
                ]
            },
            {
                "name": "🛠️ Tools",
                "apps": [
                    {"name": "Calculator", "file": "calculator.sona", "type": "tool"},
                    {"name": "Text Editor", "file": "text_editor.sona", "type": "tool"},
                    {"name": "File Organizer", "file": "file_organizer.sona", "type": "tool"},
                    {"name": "Media Player", "file": "media_player.sona", "type": "tool"},
                    {"name": "Digital Painter", "file": "painter.sona", "type": "tool"},
                ]
            },
            {
                "name": "📊 Data Apps",
                "apps": [
                    {"name": "Todo Manager", "file": "todo_manager.sona", "type": "data"},
                    {"name": "Notes Manager", "file": "notes_manager.sona", "type": "data"},
                    {"name": "Calendar", "file": "calendar.sona", "type": "data"},
                ]
            },
            {
                "name": "📚 Tutorials",
                "apps": [
                    {"name": "Hello World", "file": "hello_world.sona", "type": "tutorial"},
                    {"name": "Basic Syntax", "file": "basic_syntax.sona", "type": "tutorial"},
                    {"name": "Dictionary Operations", "file": "dictionary_operations.sona", "type": "tutorial"},
                    {"name": "Module Demo", "file": "module_demo.sona", "type": "tutorial"},
                    {"name": "Data Processing", "file": "data_processing.sona", "type": "tutorial"},
                    {"name": "Error Handling", "file": "error_handling.sona", "type": "tutorial"},
                ]
            }
        ]
        
        # Populate tree
        for category in categories:
            category_id = self.app_tree.insert('', 'end', text=category["name"], open=True)
            
            for app in category["apps"]:
                app_id = self.app_tree.insert(category_id, 'end', text=app["name"])
                self.app_tree.set(app_id, "file", app["file"])
                self.app_tree.set(app_id, "type", app["type"])
                
    def filter_apps(self, event=None):
        """Filter applications based on search"""
        query = self.search_var.get().lower()
        # Simple filter - would be enhanced for better UX
        # For now, just highlight matching items
        
    def on_app_selected(self, event=None):
        """Handle app selection"""
        selection = self.app_tree.selection()
        if selection and self.selection_callback:
            item = selection[0]
            text = self.app_tree.item(item, "text")
            
            # Check if it's an app (not category)
            if self.app_tree.parent(item):  # Has parent = is an app
                file_name = self.app_tree.set(item, "file") if self.app_tree.set(item, "file") else f"{text.lower().replace(' ', '_')}.sona"
                app_type = self.app_tree.set(item, "type") if self.app_tree.set(item, "type") else "tutorial"
                
                # Find file path
                sona_dir = Path(__file__).parent.parent
                examples_dir = sona_dir / "examples"
                app_path = examples_dir / file_name
                
                self.selection_callback(text, str(app_path), app_type)
                
    def toggle_visibility(self):
        """Toggle sidebar visibility"""
        if self.is_visible:
            self.frame.pack_forget()
            self.is_visible = False
        else:
            self.frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 1))
            self.is_visible = True


class ModernAppDisplay:
    """Modern app display area with multiple view modes"""
    
    def __init__(self, parent):
        self.parent = parent
        self.current_mode = "welcome"
        
        # Main frame
        self.frame = tk.Frame(parent, bg=ModernTheme.BACKGROUND_PRIMARY)
        self.frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create different view modes
        self.create_welcome_view()
        self.create_code_view()
        self.create_app_view()
        
        # Show welcome initially
        self.show_welcome()
        
    def create_welcome_view(self):
        """Create welcome view"""
        self.welcome_frame = tk.Frame(self.frame, bg=ModernTheme.BACKGROUND_PRIMARY)
        
        # Center content
        center_frame = tk.Frame(self.welcome_frame, bg=ModernTheme.BACKGROUND_PRIMARY)
        center_frame.pack(expand=True, fill=tk.BOTH)
        
        content_frame = tk.Frame(center_frame, bg=ModernTheme.BACKGROUND_PRIMARY)
        content_frame.pack(expand=True)
        
        # Title
        title = tk.Label(
            content_frame,
            text="Welcome to Sona v0.7.0",
            bg=ModernTheme.BACKGROUND_PRIMARY,
            fg=ModernTheme.ACCENT_PRIMARY,
            font=('Segoe UI', 24, 'bold')
        )
        title.pack(pady=(0, 10))
        
        # Subtitle
        subtitle = tk.Label(
            content_frame,
            text="Professional • Modern • Extensible",
            bg=ModernTheme.BACKGROUND_PRIMARY,
            fg=ModernTheme.TEXT_SECONDARY,
            font=('Segoe UI', 12)
        )
        subtitle.pack(pady=(0, 30))
        
        # Description
        desc_text = """Select an application from the sidebar to get started.

• Browse interactive games and tools
• View source code with syntax highlighting
• Run applications in different execution modes
• Monitor output in real-time console"""
        
        description = tk.Label(
            content_frame,
            text=desc_text,
            bg=ModernTheme.BACKGROUND_PRIMARY,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 11),
            justify=tk.CENTER
        )
        description.pack()
        
    def create_code_view(self):
        """Create code view"""
        self.code_frame = tk.Frame(self.frame, bg=ModernTheme.BACKGROUND_PRIMARY)
        
        # File info
        info_frame = tk.Frame(self.code_frame, bg=ModernTheme.BACKGROUND_SECONDARY, height=40)
        info_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        info_frame.pack_propagate(False)
        
        self.file_info_label = tk.Label(
            info_frame,
            text="No file selected",
            bg=ModernTheme.BACKGROUND_SECONDARY,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 11, 'bold')
        )
        self.file_info_label.pack(side=tk.LEFT, padx=15, pady=10)
        
        # Code editor
        editor_frame = tk.Frame(self.code_frame, bg=ModernTheme.BACKGROUND_PRIMARY)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.code_editor = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.NONE,
            bg=ModernTheme.BACKGROUND_TERTIARY,
            fg=ModernTheme.TEXT_PRIMARY,
            insertbackground=ModernTheme.ACCENT_PRIMARY,
            selectbackground=ModernTheme.SELECTION_COLOR,
            font=('Fira Code', 11),
            border=0,
            relief='flat',
            state='disabled'
        )
        self.code_editor.pack(fill=tk.BOTH, expand=True)
        
    def create_app_view(self):
        """Create embedded app view"""
        self.app_frame = tk.Frame(self.frame, bg=ModernTheme.BACKGROUND_TERTIARY)
        
        # App container
        self.app_container = tk.Frame(self.app_frame, bg=ModernTheme.BACKGROUND_TERTIARY)
        self.app_container.pack(fill=tk.BOTH, expand=True)
        
    def show_welcome(self):
        """Show welcome view"""
        self.hide_all_views()
        self.welcome_frame.pack(fill=tk.BOTH, expand=True)
        self.current_mode = "welcome"
        
    def show_code(self, file_path: str):
        """Show code view"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.file_info_label.config(text=f"File: {Path(file_path).name}")
            
            self.code_editor.config(state='normal')
            self.code_editor.delete(1.0, tk.END)
            self.code_editor.insert(1.0, content)
            self.code_editor.config(state='disabled')
            
            self.hide_all_views()
            self.code_frame.pack(fill=tk.BOTH, expand=True)
            self.current_mode = "code"
            
        except Exception as e:
            self.file_info_label.config(text=f"Error loading file: {e}")
            
    def show_embedded_app(self, app_name: str, app_type: str):
        """Show embedded app view"""
        # Clear existing content
        for widget in self.app_container.winfo_children():
            widget.destroy()
            
        # Create app demo
        demo_frame = tk.Frame(self.app_container, bg=ModernTheme.BACKGROUND_TERTIARY)
        demo_frame.pack(expand=True, fill=tk.BOTH)
        
        # App title
        title = tk.Label(
            demo_frame,
            text=f"🎮 {app_name}",
            bg=ModernTheme.BACKGROUND_TERTIARY,
            fg=ModernTheme.ACCENT_PRIMARY,
            font=('Segoe UI', 20, 'bold')
        )
        title.pack(expand=True, pady=(0, 10))
        
        # App description
        desc = tk.Label(
            demo_frame,
            text="Interactive application would be embedded here\\nSwitch to Console mode to run the actual application",
            bg=ModernTheme.BACKGROUND_TERTIARY,
            fg=ModernTheme.TEXT_SECONDARY,
            font=('Segoe UI', 12),
            justify=tk.CENTER
        )
        desc.pack(expand=True)
        
        self.hide_all_views()
        self.app_frame.pack(fill=tk.BOTH, expand=True)
        self.current_mode = "app"
        
    def hide_all_views(self):
        """Hide all views"""
        self.welcome_frame.pack_forget()
        self.code_frame.pack_forget()
        self.app_frame.pack_forget()


class ModernMainWindow:
    """Modern main window with enhanced Tkinter design"""
    
    def __init__(self):
        # Create main window
        self.root = tk.Tk()
        self.root.title("Sona v0.7.0 - Modern Development Platform")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        self.root.configure(bg=ModernTheme.BACKGROUND_PRIMARY)
        
        # State
        self.current_file = None
        self.current_app_name = None
        self.current_app_type = None
        
        # Initialize controllers
        self.execution_controller = ExecutionController(
            output_callback=self.on_output,
            error_callback=self.on_error,
            start_callback=self.on_execution_start,
            finish_callback=self.on_execution_finish
        )
        
        # Setup UI
        self.setup_ui()
        
        # Setup bindings
        self.setup_bindings()
        
    def setup_ui(self):
        """Setup the main UI"""
        # Create top bar
        self.create_top_bar()
        
        # Create main content area
        content_frame = tk.Frame(self.root, bg=ModernTheme.BACKGROUND_PRIMARY)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create sidebar
        self.sidebar = ModernSidebar(content_frame, self.on_app_selected)
        
        # Create app display
        self.app_display = ModernAppDisplay(content_frame)
        
        # Create console
        self.console = ModernConsole(self.root)
        
        # Create status bar
        self.create_status_bar()
        
        # Create menu
        self.create_menu()
        
    def create_top_bar(self):
        """Create modern top bar"""
        top_frame = tk.Frame(self.root, bg=ModernTheme.BACKGROUND_SECONDARY, height=60)
        top_frame.pack(fill=tk.X)
        top_frame.pack_propagate(False)
        
        # Left side - Title
        left_frame = tk.Frame(top_frame, bg=ModernTheme.BACKGROUND_SECONDARY)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=10)
        
        title = tk.Label(
            left_frame,
            text="Sona v0.7.0",
            bg=ModernTheme.BACKGROUND_SECONDARY,
            fg=ModernTheme.ACCENT_PRIMARY,
            font=('Segoe UI', 16, 'bold')
        )
        title.pack(side=tk.LEFT, pady=10)
        
        # Right side - Controls
        right_frame = tk.Frame(top_frame, bg=ModernTheme.BACKGROUND_SECONDARY)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=20, pady=10)
        
        # Execution mode
        mode_label = tk.Label(
            right_frame,
            text="Mode:",
            bg=ModernTheme.BACKGROUND_SECONDARY,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 10)
        )
        mode_label.pack(side=tk.LEFT, padx=(0, 5), pady=10)
        
        self.mode_var = tk.StringVar(value=ExecutionMode.SANDBOX)
        self.mode_combo = ttk.Combobox(
            right_frame,
            textvariable=self.mode_var,
            values=[ExecutionMode.SANDBOX, ExecutionMode.NATIVE, ExecutionMode.REMOTE],
            state='readonly',
            width=12
        )
        self.mode_combo.pack(side=tk.LEFT, padx=(0, 20), pady=10)
        
        # Console button
        self.console_button = tk.Button(
            right_frame,
            text="</> Console",
            bg=ModernTheme.BACKGROUND_TERTIARY,
            fg=ModernTheme.TEXT_PRIMARY,
            activebackground=ModernTheme.HOVER_COLOR,
            border=0,
            padx=15,
            pady=8,
            font=('Segoe UI', 10),
            command=self.toggle_console
        )
        self.console_button.pack(side=tk.LEFT, padx=(0, 10), pady=10)
        
        # Run button
        self.run_button = tk.Button(
            right_frame,
            text="🔵 Run",
            bg=ModernTheme.ACCENT_SUCCESS,
            fg=ModernTheme.BACKGROUND_PRIMARY,
            activebackground=ModernTheme.ACCENT_PRIMARY,
            border=0,
            padx=20,
            pady=8,
            font=('Segoe UI', 10, 'bold'),
            command=self.run_current,
            state='disabled'
        )
        self.run_button.pack(side=tk.LEFT, pady=10)
        
    def create_status_bar(self):
        """Create status bar"""
        status_frame = tk.Frame(self.root, bg=ModernTheme.BACKGROUND_SECONDARY, height=30)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        status_frame.pack_propagate(False)
        
        # Current file
        self.file_status = tk.Label(
            status_frame,
            text="No file selected",
            bg=ModernTheme.BACKGROUND_SECONDARY,
            fg=ModernTheme.TEXT_MUTED,
            font=('Segoe UI', 9)
        )
        self.file_status.pack(side=tk.LEFT, padx=15, pady=5)
        
        # Version info
        version_label = tk.Label(
            status_frame,
            text="Sona Platform v0.7.0 | Enhanced Tkinter Edition",
            bg=ModernTheme.BACKGROUND_SECONDARY,
            fg=ModernTheme.TEXT_MUTED,
            font=('Segoe UI', 9)
        )
        version_label.pack(side=tk.RIGHT, padx=15, pady=5)
        
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root, bg=ModernTheme.BACKGROUND_SECONDARY, fg=ModernTheme.TEXT_PRIMARY)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=ModernTheme.BACKGROUND_SECONDARY, fg=ModernTheme.TEXT_PRIMARY)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open File...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0, bg=ModernTheme.BACKGROUND_SECONDARY, fg=ModernTheme.TEXT_PRIMARY)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Sidebar", command=self.toggle_sidebar, accelerator="Ctrl+1")
        view_menu.add_command(label="Toggle Console", command=self.toggle_console, accelerator="Ctrl+2")
        view_menu.add_separator()
        view_menu.add_command(label="Reset Layout", command=self.reset_layout)
        
        # Run menu
        run_menu = tk.Menu(menubar, tearoff=0, bg=ModernTheme.BACKGROUND_SECONDARY, fg=ModernTheme.TEXT_PRIMARY)
        menubar.add_cascade(label="Run", menu=run_menu)
        run_menu.add_command(label="Run Current", command=self.run_current, accelerator="F5")
        run_menu.add_command(label="Stop Execution", command=self.stop_execution, accelerator="Ctrl+C")
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=ModernTheme.BACKGROUND_SECONDARY, fg=ModernTheme.TEXT_PRIMARY)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About Sona", command=self.show_about)
        help_menu.add_command(label="Documentation", command=self.show_docs)
        help_menu.add_separator()
        help_menu.add_command(label="Upgrade to PySide6", command=self.show_pyside6_info)
        
    def setup_bindings(self):
        """Setup keyboard bindings"""
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<Control-1>', lambda e: self.toggle_sidebar())
        self.root.bind('<Control-2>', lambda e: self.toggle_console())
        self.root.bind('<F5>', lambda e: self.run_current())
        self.root.bind('<Control-c>', lambda e: self.stop_execution())
        
        # Mode change binding
        self.mode_combo.bind('<<ComboboxSelected>>', self.on_mode_change)
        
    def on_app_selected(self, app_name: str, app_path: str, app_type: str):
        """Handle application selection"""
        self.current_file = app_path
        self.current_app_name = app_name
        self.current_app_type = app_type
        
        self.file_status.config(text=f"Selected: {Path(app_path).name}")
        self.run_button.config(state='normal')
        
        # Show appropriate view
        if app_type in ["game", "tool", "data"]:
            self.app_display.show_embedded_app(app_name, app_type)
        else:
            self.app_display.show_code(app_path)
            
    def on_mode_change(self, event=None):
        """Handle execution mode change"""
        mode = self.mode_var.get()
        self.execution_controller.set_execution_mode(mode)
        
    def run_current(self):
        """Run current file"""
        if self.current_file and not self.execution_controller.is_running:
            # Show console
            self.console.show_console()
            self.console.clear_console()
            
            # Execute
            self.execution_controller.execute_file(self.current_file)
            
    def stop_execution(self):
        """Stop execution"""
        self.execution_controller.stop_execution()
        
    def on_output(self, text: str):
        """Handle output from execution"""
        self.root.after(0, lambda: self.console.append_output(text))
        
    def on_error(self, text: str):
        """Handle error from execution"""
        self.root.after(0, lambda: self.console.append_error(text))
        
    def on_execution_start(self):
        """Handle execution start"""
        self.root.after(0, lambda: self.run_button.config(
            text="⏸️ Running...", 
            state='disabled',
            bg=ModernTheme.ACCENT_WARNING
        ))
        self.root.after(0, lambda: self.console.set_status("● Running...", ModernTheme.ACCENT_WARNING))
        
    def on_execution_finish(self, return_code: int):
        """Handle execution finish"""
        self.root.after(0, lambda: self.run_button.config(
            text="🔵 Run", 
            state='normal',
            bg=ModernTheme.ACCENT_SUCCESS
        ))
        
        if return_code == 0:
            self.root.after(0, lambda: self.console.set_status("● Completed", ModernTheme.ACCENT_SUCCESS))
        else:
            self.root.after(0, lambda: self.console.set_status("● Error", ModernTheme.ACCENT_ERROR))
            
    def toggle_sidebar(self):
        """Toggle sidebar"""
        self.sidebar.toggle_visibility()
        
    def toggle_console(self):
        """Toggle console"""
        self.console.toggle_console()
        
    def reset_layout(self):
        """Reset layout"""
        self.sidebar.is_visible = True
        self.sidebar.frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 1))
        self.console.hide_console()
        
    def open_file(self):
        """Open file dialog"""
        file_path = filedialog.askopenfilename(
            title="Open Sona File",
            filetypes=[("Sona files", "*.sona"), ("All files", "*.*")],
            initialdir=str(Path(__file__).parent.parent / "examples")
        )
        
        if file_path:
            self.current_file = file_path
            self.current_app_name = Path(file_path).stem
            self.current_app_type = "tutorial"
            
            self.file_status.config(text=f"Selected: {Path(file_path).name}")
            self.run_button.config(state='normal')
            self.app_display.show_code(file_path)
            
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About Sona", """Sona v0.7.0 - Modern Development Platform

Enhanced Tkinter Edition

A professional, modern application launcher built with enhanced Tkinter design patterns.

Features:
• Interactive application browser
• Real-time code execution
• Modern dark theme
• Multiple execution modes
• Floating console with advanced controls
• Responsive layout

Built for the Sona Programming Language

For the ultimate experience with native Qt styling,
consider upgrading to the PySide6 edition.""")
        
    def show_docs(self):
        """Show documentation"""
        messagebox.showinfo("Documentation", 
                           "Sona documentation and tutorials are available in the sidebar under 'Tutorials'.")
        
    def show_pyside6_info(self):
        """Show PySide6 upgrade information"""
        messagebox.showinfo("Upgrade to PySide6", """Upgrade to PySide6 for Enhanced Experience

The PySide6 edition offers:
• Native Qt styling and animations
• Better performance and responsiveness  
• Advanced docking and layout system
• Professional desktop application feel
• Enhanced graphics and rendering

To upgrade:
1. Install PySide6: pip install PySide6
2. Run: python gui/modern_launcher.py

The PySide6 version provides the complete modern experience
with professional-grade UI components and native OS integration.""")
        
    def run(self):
        """Run the application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    app = ModernMainWindow()
    app.run()


if __name__ == "__main__":
    main()
