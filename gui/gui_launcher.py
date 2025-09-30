#!/usr/bin/env python3
"""
Sona GUI Launcher v0.7.0
"""

import calendar
import math
import os
import random
import subprocess
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk


class SonaExampleLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Sona v0.7.0 - Advanced Application Platform")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Modern color scheme - Dark theme with gradient accents
        self.colors = {
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
        
        # Configure root window styling
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Get the Sona project directory
        self.sona_dir = Path(__file__).parent.parent
        self.examples_dir = self.sona_dir / "examples"
        
        # Working examples list
        self.working_examples = [
            "basic_syntax.sona",
            "dict_simple.sona",
            "dictionary_operations.sona",
            "modules_working.sona",
            "module_demo.sona",            "data_processing.sona",
            "error_handling.sona"        ]
        
        # Enhanced initialization for embedded applications
        self.embedded_apps = {}  # Track running embedded applications
        
        self.app_registry = {
            "calculator.sona": CalculatorApp,
            "snake_game.sona": SnakeGameApp,
            "ping_pong.sona": PingPongApp,
            "space_shooter.sona": ArcadeShooterApp,
            "invaders.sona": InvadersApp,
            "flappy_bird.sona": FlappyBirdApp,
            "doom_2d.sona": Doom2DApp,
            "bejeweled.sona": BejeweledApp,
            "painter.sona": PainterApp,
            "solitaire.sona": SolitaireApp,
            "tetris.sona": TetrisApp,
            "mahjong.sona": MahjongApp,
            "bubble_shooter.sona": BubbleShooterApp,
            "sudoku.sona": SudokuApp,
            "todo_manager.sona": TodoApp,
            "notes_manager.sona": NotesManagerApp,
            "calendar.sona": CalendarApp,
            "file_organizer.sona": FileOrganizerApp,
            "media_player.sona": MediaPlayerApp,
            "text_editor.sona": TextEditorApp,
            # Map existing examples to embedded apps where applicable
            "basic_syntax.sona": None,  # Console output only
            "dict_simple.sona": None,   # Console output only
        }
        
        # Application execution mode
        self.execution_mode = AppExecutionMode.CONSOLE_OUTPUT
        
        # Initialize modern UI theme
        self.setup_theme()
        self.setup_ui()
        self.load_examples()
        
        # Start embedded app update loop
        self.update_embedded_apps()
        
    def setup_theme(self):
        """Configure the modern theme and styling"""
        # Configure ttk styles for modern look
        style = ttk.Style()
        
        # Use a modern theme as base
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        
        # Configure frame styles
        style.configure('Modern.TFrame', 
                       background=self.colors['bg_secondary'],
                       borderwidth=1,
                       relief='flat')
        
        style.configure('Card.TFrame',
                       background=self.colors['bg_tertiary'],
                       borderwidth=2,
                       relief='raised')
        
        # Configure label styles
        style.configure('Title.TLabel',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 18, 'bold'))
        
        style.configure('Subtitle.TLabel',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_secondary'],
                       font=('Segoe UI', 11))
        
        style.configure('Accent.TLabel',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_accent'],
                       font=('Segoe UI', 10, 'bold'))
        
        # Configure button styles
        style.configure('Modern.TButton',
                       background=self.colors['accent_primary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10))
        
        style.map('Modern.TButton',
                 background=[('active', self.colors['accent_secondary']),
                            ('pressed', self.colors['button_hover'])])
        
        # Configure notebook styles
        style.configure('Modern.TNotebook',
                       background=self.colors['bg_secondary'],
                       borderwidth=0)
        
        style.configure('Modern.TNotebook.Tab',
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_secondary'],
                       padding=[20, 10],
                       font=('Segoe UI', 10))
        
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', self.colors['accent_primary']),
                            ('active', self.colors['button_hover'])],
                 foreground=[('selected', self.colors['text_primary'])])
        
        # Configure entry styles
        style.configure('Modern.TEntry',
                       fieldbackground=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1,
                       insertcolor=self.colors['text_accent'])        
        # Configure combobox styles
        style.configure('Modern.TCombobox',
                       fieldbackground=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1)
        
    def setup_ui(self):
        """Create the modern user interface"""
        # Main container with modern styling
        main_frame = ttk.Frame(self.root, style='Modern.TFrame', padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for responsive design
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=3)  # Give more space to content
        main_frame.rowconfigure(1, weight=1)
        
        # Modern title header with gradient effect
        self.create_title_header(main_frame)
        
        # Create main content areas
        self.create_sidebar(main_frame)
        self.create_content_area(main_frame)
        self.create_output_panel(main_frame)
        
        # Add REPL tab to content area
        self.create_repl_tab()
        
        # Bottom status bar with modern styling
        self.create_status_bar(main_frame)
        
        # Menu bar
        self.create_menu()
        
    def create_title_header(self, parent):
        """Create modern title header with gradient styling"""
        # Header frame with custom background
        header_frame = tk.Frame(parent, bg=self.colors['bg_primary'], height=80)
        header_frame.grid(row=0, column=0, columnspan=3, sticky='ew', pady=(0, 15))
        header_frame.grid_propagate(False)
        
        # Title with modern typography
        title_label = tk.Label(header_frame, 
                              text="Sona v0.7.0 - Advanced Application Platform",
                              font=('Segoe UI', 20, 'bold'),
                              fg=self.colors['text_primary'],
                              bg=self.colors['bg_primary'])
        title_label.pack(side='left', padx=20, pady=25)
        
        # Subtitle
        subtitle_label = tk.Label(header_frame,
                                 text="Professional • Modern • Extensible",
                                 font=('Segoe UI', 10),
                                 fg=self.colors['text_accent'],
                                 bg=self.colors['bg_primary'])
        subtitle_label.pack(side='left', padx=(5, 0), pady=(35, 15))
        
        # Mode selector on the right
        mode_frame = tk.Frame(header_frame, bg=self.colors['bg_primary'])
        mode_frame.pack(side='right', padx=20, pady=25)
        
        mode_label = tk.Label(mode_frame, text="Execution Mode:",
                             font=('Segoe UI', 11, 'bold'),
                             fg=self.colors['text_secondary'],
                             bg=self.colors['bg_primary'])
        mode_label.pack(side='left', padx=(0, 10))
        
        self.mode_var = tk.StringVar(value="Console")
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var,
                                 values=["Console", "Embedded App", "Separate Window", "Interactive REPL"],
                                 state='readonly', width=18, style='Modern.TCombobox')
        mode_combo.pack(side='left')
        mode_combo.bind('<<ComboboxSelected>>', self.on_mode_change)
        
    def create_sidebar(self, parent):
        """Create modern sidebar for examples"""
        # Sidebar frame with card styling
        sidebar_frame = ttk.Frame(parent, style='Card.TFrame', padding="15")
        sidebar_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Sidebar title
        sidebar_title = tk.Label(sidebar_frame, text="📁 Examples",
                                font=('Segoe UI', 14, 'bold'),
                                fg=self.colors['text_primary'],
                                bg=self.colors['bg_tertiary'])
        sidebar_title.pack(fill='x', pady=(0, 15))
        
        # Search box
        search_frame = tk.Frame(sidebar_frame, bg=self.colors['bg_tertiary'])
        search_frame.pack(fill='x', pady=(0, 10))
        
        search_label = tk.Label(search_frame, text="🔍",
                               font=('Segoe UI', 12),
                               fg=self.colors['text_secondary'],
                               bg=self.colors['bg_tertiary'])
        search_label.pack(side='left', padx=(0, 5))
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var,
                                font=('Segoe UI', 10), style='Modern.TEntry')
        search_entry.pack(side='left', fill='x', expand=True)
        search_entry.bind('<KeyRelease>', self.on_search_change)
        
        # Example listbox with modern styling
        listbox_frame = tk.Frame(sidebar_frame, bg=self.colors['bg_tertiary'])
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Custom listbox with modern colors
        self.example_listbox = tk.Listbox(listbox_frame, 
                                         font=('Segoe UI', 10),
                                         bg=self.colors['bg_secondary'],
                                         fg=self.colors['text_primary'],
                                         selectbackground=self.colors['accent_primary'],
                                         selectforeground=self.colors['text_primary'],
                                         activestyle='none',
                                         borderwidth=0,
                                         highlightthickness=0)
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, 
                                 command=self.example_listbox.yview)
        self.example_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.example_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.example_listbox.bind('<<ListboxSelect>>', self.on_example_select)
        
        # Modern action buttons
        self.create_action_buttons(sidebar_frame)
        
    def create_action_buttons(self, parent):
        """Create modern action buttons"""
        button_frame = tk.Frame(parent, bg=self.colors['bg_tertiary'])
        button_frame.pack(fill='x')
        
        # Run button with icon
        self.run_button = tk.Button(button_frame, text="▶ Run Example",
                                   font=('Segoe UI', 10, 'bold'),
                                   bg=self.colors['success'],
                                   fg=self.colors['text_primary'],
                                   activebackground=self.colors['accent_secondary'],
                                   borderwidth=0, relief='flat',
                                   command=self.run_selected_example,
                                   state=tk.DISABLED, cursor='hand2')
        self.run_button.pack(fill='x', pady=(0, 8))
        
        # View button
        self.view_button = tk.Button(button_frame, text="👁 View Code",
                                    font=('Segoe UI', 10),
                                    bg=self.colors['accent_primary'],
                                    fg=self.colors['text_primary'],
                                    activebackground=self.colors['accent_secondary'],
                                    borderwidth=0, relief='flat',
                                    command=self.view_selected_example,
                                    state=tk.DISABLED, cursor='hand2')
        self.view_button.pack(fill='x', pady=(0, 8))
        
        # Refresh button
        self.refresh_button = tk.Button(button_frame, text="🔄 Refresh",
                                       font=('Segoe UI', 10),
                                       bg=self.colors['bg_secondary'],
                                       fg=self.colors['text_secondary'],
                                       activebackground=self.colors['button_hover'],
                                       borderwidth=0, relief='flat',
                                       command=self.load_examples,
                                       cursor='hand2')
        self.refresh_button.pack(fill='x')
        
    def on_search_change(self, event=None):
        """Handle search input changes"""
        query = self.search_var.get().lower()
        self.load_examples(filter_query=query)
        
    def create_content_area(self, parent):
        """Create modern content area with tabs"""
        # Content frame with card styling
        content_frame = ttk.Frame(parent, style='Card.TFrame', padding="15")
        content_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Content title
        content_title = tk.Label(content_frame, text="📄 Content Viewer",
                                font=('Segoe UI', 14, 'bold'),
                                fg=self.colors['text_primary'],
                                bg=self.colors['bg_tertiary'])
        content_title.pack(fill='x', pady=(0, 15))
        
        # Create modern notebook with enhanced tabs
        self.notebook = ttk.Notebook(content_frame, style='Modern.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Source Code tab
        self.code_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.code_frame, text="📝 Source Code")
        
        # Code viewer with modern styling
        code_container = tk.Frame(self.code_frame, bg=self.colors['bg_secondary'])
        code_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.code_text = scrolledtext.ScrolledText(code_container, 
                                                  wrap=tk.NONE, 
                                                  font=('Fira Code', 11),
                                                  bg=self.colors['bg_secondary'],
                                                  fg=self.colors['text_primary'],
                                                  insertbackground=self.colors['text_accent'],
                                                  selectbackground=self.colors['accent_primary'],
                                                  selectforeground=self.colors['text_primary'],
                                                  borderwidth=0, relief='flat')
        self.code_text.pack(fill=tk.BOTH, expand=True)
        
        # Embedded Application tab
        self.app_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.app_frame, text="🎮 Application")
        
        # Container for embedded applications
        self.app_container = tk.Frame(self.app_frame, bg=self.colors['bg_secondary'])
        self.app_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # No application message with modern styling
        self.no_app_label = tk.Label(self.app_container,
                                    text="Select an example with embedded app support\\nfrom the list to see it here.",
                                    font=('Segoe UI', 12),
                                    fg=self.colors['text_secondary'],
                                    bg=self.colors['bg_secondary'])
        self.no_app_label.pack(expand=True)
        
    def create_repl_tab(self):
        """Create interactive REPL tab"""
        # REPL tab
        self.repl_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.repl_frame, text="💻 Interactive REPL")
        
        # REPL container with modern styling
        repl_container = tk.Frame(self.repl_frame, bg=self.colors['bg_secondary'])
        repl_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # REPL title and status
        repl_header = tk.Frame(repl_container, bg=self.colors['bg_tertiary'], height=40)
        repl_header.pack(fill='x', pady=(0, 5))
        repl_header.pack_propagate(False)
        
        repl_title = tk.Label(repl_header, text="🔥 Sona Interactive REPL",
                             font=('Segoe UI', 12, 'bold'),
                             fg=self.colors['text_primary'],
                             bg=self.colors['bg_tertiary'])
        repl_title.pack(side='left', padx=15, pady=10)
        
        self.repl_status = tk.Label(repl_header, text="● Ready",
                                   font=('Segoe UI', 10),
                                   fg=self.colors['success'],
                                   bg=self.colors['bg_tertiary'])
        self.repl_status.pack(side='right', padx=15, pady=10)
        
        # REPL output area
        repl_output_frame = tk.Frame(repl_container, bg=self.colors['bg_secondary'])
        repl_output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.repl_output = scrolledtext.ScrolledText(repl_output_frame,
                                                    wrap=tk.WORD,
                                                    font=('Fira Code', 10),
                                                    bg='#0d1117',  # GitHub dark
                                                    fg='#f0f6fc',
                                                    insertbackground='#58a6ff',
                                                    selectbackground='#264f78',
                                                    borderwidth=0, relief='flat',
                                                    state='disabled')
        self.repl_output.pack(fill=tk.BOTH, expand=True)
        
        # REPL input area
        repl_input_frame = tk.Frame(repl_container, bg=self.colors['bg_tertiary'], height=60)
        repl_input_frame.pack(fill='x')
        repl_input_frame.pack_propagate(False)
        
        # Input prompt
        input_prompt = tk.Label(repl_input_frame, text="sona>",
                               font=('Fira Code', 11, 'bold'),
                               fg=self.colors['text_accent'],
                               bg=self.colors['bg_tertiary'])
        input_prompt.pack(side='left', padx=(10, 5), pady=15)
        
        # Input entry
        self.repl_input = tk.Entry(repl_input_frame,
                                  font=('Fira Code', 11),
                                  bg=self.colors['bg_secondary'],
                                  fg=self.colors['text_primary'],
                                  insertbackground=self.colors['text_accent'],
                                  borderwidth=0, relief='flat')
        self.repl_input.pack(side='left', fill='x', expand=True, padx=(0, 10), pady=15)
        self.repl_input.bind('<Return>', self.execute_repl_command)
        self.repl_input.bind('<Up>', self.repl_history_up)
        self.repl_input.bind('<Down>', self.repl_history_down)
        
        # REPL command history
        self.repl_history = []
        self.repl_history_index = 0
        
        # Initialize REPL with welcome message
        self.init_repl()
        
    def init_repl(self):
        """Initialize REPL with welcome message"""
        welcome_msg = '''Welcome to Sona Interactive REPL v0.7.0!
        
🚀 Ready to explore Sona language features
📚 Type expressions, variable assignments, imports
🔍 Use 'help' for commands, 'clear' to clear screen
⚡ Press Enter to execute, Up/Down for history

Example commands:
  let x = 42
  print("Hello, Sona!")
  import "math"
  
'''
        self.repl_output.config(state='normal')
        self.repl_output.insert(tk.END, welcome_msg)
        self.repl_output.config(state='disabled')
        self.repl_output.see(tk.END)
        
    def execute_repl_command(self, event=None):
        """Execute REPL command"""
        command = self.repl_input.get().strip()
        if not command:
            return
            
        # Add to history
        self.repl_history.append(command)
        self.repl_history_index = len(self.repl_history)
        
        # Display command in output
        self.repl_output.config(state='normal')
        self.repl_output.insert(tk.END, f"\\nsona> {command}\\n")
        
        # Update status
        self.repl_status.config(text="● Executing...", fg=self.colors['warning'])
        self.root.update()
        
        # Handle special commands
        if command == 'clear':
            self.repl_output.delete(1.0, tk.END)
            self.init_repl()
            self.repl_input.delete(0, tk.END)
            self.repl_status.config(text="● Ready", fg=self.colors['success'])
            return
        elif command == 'help':
            help_text = '''Available REPL commands:
  clear     - Clear the REPL screen
  help      - Show this help message
  exit      - Close REPL (use Ctrl+C or close tab)
  
Sona language features (v0.7.0):
  let var = value        - Variable assignment
  print("text")          - Print statements
  import "module"        - Module imports
  obj.property          - Property access
  "string" + "concat"   - String concatenation
'''
            self.repl_output.insert(tk.END, help_text)
            self.repl_input.delete(0, tk.END)
            self.repl_status.config(text="● Ready", fg=self.colors['success'])
            self.repl_output.config(state='disabled')
            self.repl_output.see(tk.END)
            return
            
        # Execute Sona command
        try:
            import subprocess
            import tempfile
            
            # Create temporary Sona file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sona', delete=False) as f:
                f.write(command)
                temp_file = f.name
            
            # Execute with Sona interpreter
            result = subprocess.run([sys.executable, "-m", "sona", temp_file],
                                  cwd=str(self.sona_dir),
                                  capture_output=True, text=True, timeout=5)
            
            # Display result
            if result.stdout:
                self.repl_output.insert(tk.END, result.stdout)
            if result.stderr:
                self.repl_output.insert(tk.END, f"Error: {result.stderr}", "error")
                
            # Clean up
            import os
            os.unlink(temp_file)
            
        except subprocess.TimeoutExpired:
            self.repl_output.insert(tk.END, "Error: Command timed out\\n")
        except Exception as e:
            self.repl_output.insert(tk.END, f"Error: {str(e)}\\n")
            
        # Reset status and clear input
        self.repl_status.config(text="● Ready", fg=self.colors['success'])
        self.repl_input.delete(0, tk.END)
        self.repl_output.config(state='disabled')
        self.repl_output.see(tk.END)
        
    def repl_history_up(self, event=None):
        """Navigate REPL history up"""
        if self.repl_history and self.repl_history_index > 0:
            self.repl_history_index -= 1
            self.repl_input.delete(0, tk.END)
            self.repl_input.insert(0, self.repl_history[self.repl_history_index])
            
    def repl_history_down(self, event=None):
        """Navigate REPL history down"""
        if self.repl_history and self.repl_history_index < len(self.repl_history) - 1:
            self.repl_history_index += 1
            self.repl_input.delete(0, tk.END)
            self.repl_input.insert(0, self.repl_history[self.repl_history_index])
        else:
            self.repl_history_index = len(self.repl_history)
            self.repl_input.delete(0, tk.END)
            
    def create_output_panel(self, parent):
        """Create modern output panel"""
        # Output frame with card styling
        output_frame = ttk.Frame(parent, style='Card.TFrame', padding="15")
        output_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Output title with controls
        output_header = tk.Frame(output_frame, bg=self.colors['bg_tertiary'])
        output_header.pack(fill='x', pady=(0, 15))
        
        output_title = tk.Label(output_header, text="📤 Output Console",
                               font=('Segoe UI', 14, 'bold'),
                               fg=self.colors['text_primary'],
                               bg=self.colors['bg_tertiary'])
        output_title.pack(side='left', pady=5)
        
        # Output controls
        controls_frame = tk.Frame(output_header, bg=self.colors['bg_tertiary'])
        controls_frame.pack(side='right', pady=5)
        
        self.clear_button = tk.Button(controls_frame, text="🗑",
                                     font=('Segoe UI', 12),
                                     bg=self.colors['error'],
                                     fg=self.colors['text_primary'],
                                     activebackground='#d32f2f',
                                     borderwidth=0, relief='flat',
                                     command=self.clear_output,
                                     cursor='hand2', width=3)
        self.clear_button.pack(side='left', padx=(0, 10))
        
        self.status_label = tk.Label(controls_frame, text="● Ready",
                                    font=('Segoe UI', 10, 'bold'),
                                    fg=self.colors['success'],
                                    bg=self.colors['bg_tertiary'])
        self.status_label.pack(side='left')
        
        # Output text area with modern styling
        output_container = tk.Frame(output_frame, bg=self.colors['bg_secondary'])
        output_container.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(output_container,
                                                    wrap=tk.WORD,
                                                    font=('Fira Code', 10),
                                                    bg=self.colors['bg_secondary'],
                                                    fg=self.colors['text_primary'],
                                                    insertbackground=self.colors['text_accent'],
                                                    selectbackground=self.colors['accent_primary'],
                                                    borderwidth=0, relief='flat')
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for colored output
        self.output_text.tag_configure("success", foreground=self.colors['success'])
        self.output_text.tag_configure("error", foreground=self.colors['error'])
        self.output_text.tag_configure("warning", foreground=self.colors['warning'])
        self.output_text.tag_configure("info", foreground=self.colors['text_accent'])
        
    def create_status_bar(self, parent):
        """Create modern status bar"""
        status_frame = tk.Frame(parent, bg=self.colors['bg_primary'], height=35)
        status_frame.grid(row=2, column=0, columnspan=3, sticky='ew', pady=(15, 0))
        status_frame.grid_propagate(False)
        
        # Left side - Directory info
        self.info_label = tk.Label(status_frame,
                                  text=f"📁 {self.sona_dir}",
                                  font=('Segoe UI', 9),
                                  fg=self.colors['text_secondary'],
                                  bg=self.colors['bg_primary'])
        self.info_label.pack(side='left', padx=15, pady=8)
        
        # Right side - App info
        app_info = tk.Label(status_frame,
                           text="Sona Platform v0.7.0 | Ready for Innovation",
                           font=('Segoe UI', 9),
                           fg=self.colors['text_accent'],
                           bg=self.colors['bg_primary'])
        app_info.pack(side='right', padx=15, pady=8)
        
    def create_menu(self):
        """Create the application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Example File...", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Examples menu
        examples_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Examples", menu=examples_menu)
        examples_menu.add_command(label="Run All Examples", command=self.run_all_examples)
        examples_menu.add_command(label="Open Examples Folder", command=self.open_examples_folder)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About Sona", command=self.show_about)
        help_menu.add_command(label="Language Features", command=self.show_features)
        
    def load_examples(self, filter_query=""):
        """Load example files into the listbox"""
        self.example_listbox.delete(0, tk.END)
        
        if not self.examples_dir.exists():
            self.output_text.insert(tk.END, f"Examples directory not found: {self.examples_dir}\n")
            return
        
        # Create sample embedded app files
        self.create_sample_apps()
          # Add working examples first
        for example in self.working_examples:
            if (self.examples_dir / example).exists():
                self.example_listbox.insert(tk.END, f"✓ {example}")
          # Add embedded app examples
        embedded_examples = ["calculator.sona", "snake_game.sona", "ping_pong.sona", 
                            "space_shooter.sona", "invaders.sona", "flappy_bird.sona", 
                            "doom_2d.sona", "bejeweled.sona", "painter.sona", "solitaire.sona", 
                            "tetris.sona", "mahjong.sona", "bubble_shooter.sona", "sudoku.sona", 
                            "todo_manager.sona", "notes_manager.sona", "calendar.sona", 
                            "file_organizer.sona", "media_player.sona", "text_editor.sona",
                            "visual_novel.sona", "endless_runner.sona", "platformer.sona"]
        for example in embedded_examples:
            if (self.examples_dir / example).exists():
                self.example_listbox.insert(tk.END, f"🎮 {example}")
                
        # Add other .sona files
        try:
            for file_path in self.examples_dir.glob("*.sona"):
                if (file_path.name not in self.working_examples and 
                    file_path.name not in embedded_examples):
                    self.example_listbox.insert(tk.END, f"? {file_path.name}")
        except Exception as e:
            self.output_text.insert(tk.END, f"Error loading examples: {e}\n")
            
        # Apply filter if any
        if filter_query:
            self.example_listbox.delete(0, tk.END)
            for example in self.working_examples + embedded_examples:
                if filter_query in example.lower():
                    self.example_listbox.insert(tk.END, f"✓ {example}" if example in self.working_examples else f"🎮 {example}")
        
    def on_example_select(self, event):
        """Handle example selection"""
        selection = self.example_listbox.curselection()
        if selection:
            self.run_button.config(state=tk.NORMAL)
            self.view_button.config(state=tk.NORMAL)
            self.view_selected_example()
            
            # Load embedded app if in embedded mode
            if self.execution_mode == AppExecutionMode.EMBEDDED_GUI:
                self.load_embedded_app()
            
    def get_selected_example(self):
        """Get the currently selected example filename"""
        selection = self.example_listbox.curselection()
        if not selection:
            return None
            
        item_text = self.example_listbox.get(selection[0])
        # Remove the status prefix (✓ or ?)
        return item_text[2:] if len(item_text) > 2 else item_text
        
    def view_selected_example(self):
        """View the code of the selected example"""
        example_name = self.get_selected_example()
        if not example_name:
            return
            
        example_path = self.examples_dir / example_name
        
        try:
            with open(example_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.code_text.delete(1.0, tk.END)
            self.code_text.insert(1.0, content)
            
            # Simple syntax highlighting for comments
            self.highlight_syntax()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read {example_name}: {e}")
            
    def highlight_syntax(self):
        """Simple syntax highlighting for Sona code"""
        # Configure tags
        self.code_text.tag_configure("comment", foreground="#008000")
        self.code_text.tag_configure("string", foreground="#BA2121")
        self.code_text.tag_configure("keyword", foreground="#0000FF", font=('Consolas', 10, 'bold'))
        
        content = self.code_text.get(1.0, tk.END)
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line_start = f"{i+1}.0"
            
            # Highlight comments
            if '//' in line:
                comment_pos = line.find('//')
                start_pos = f"{i+1}.{comment_pos}"
                end_pos = f"{i+1}.{len(line)}"
                self.code_text.tag_add("comment", start_pos, end_pos)
                
            # Highlight strings
            in_string = False
            string_start = 0
            for j, char in enumerate(line):
                if char == '"' and (j == 0 or line[j-1] != '\\'):
                    if not in_string:
                        string_start = j
                        in_string = True
                    else:
                        start_pos = f"{i+1}.{string_start}"
                        end_pos = f"{i+1}.{j+1}"
                        self.code_text.tag_add("string", start_pos, end_pos)
                        in_string = False
                        
            # Highlight keywords
            keywords = ['let', 'import', 'print', 'if', 'else', 'func']
            for keyword in keywords:
                start = 0
                while True:
                    pos = line.find(keyword, start)
                    if pos == -1:
                        break
                    # Check if it's a whole word
                    if (pos == 0 or not line[pos-1].isalnum()) and \
                       (pos + len(keyword) >= len(line) or not line[pos + len(keyword)].isalnum()):
                        start_pos = f"{i+1}.{pos}"
                        end_pos = f"{i+1}.{pos + len(keyword)}"
                        self.code_text.tag_add("keyword", start_pos, end_pos)
                    start = pos + 1
                    
    def run_selected_example(self):
        """Run the selected example"""
        example_name = self.get_selected_example()
        if not example_name:
            messagebox.showwarning("Warning", "Please select an example to run")
            return
            
        self.run_example(example_name)
        
    def run_example(self, example_name):
        """Run a specific example in a separate thread"""
        def run_thread():
            try:
                self.status_label.config(text="Running...")
                self.output_text.insert(tk.END, f"\n=== Running {example_name} ===\n")
                self.output_text.see(tk.END)
                
                # Run the example
                example_path = self.examples_dir / example_name
                cmd = [sys.executable, "-m", "sona", str(example_path)]
                
                process = subprocess.Popen(cmd, 
                                         cwd=str(self.sona_dir),
                                         stdout=subprocess.PIPE, 
                                         stderr=subprocess.PIPE,
                                         text=True)
                
                stdout, stderr = process.communicate()
                
                if stdout:
                    self.output_text.insert(tk.END, stdout)
                if stderr:
                    self.output_text.insert(tk.END, f"Error: {stderr}")
                    
                if process.returncode == 0:
                    self.output_text.insert(tk.END, f"✓ {example_name} completed successfully\n")
                    self.status_label.config(text="Success")
                else:
                    self.output_text.insert(tk.END, f"✗ {example_name} failed with code {process.returncode}\n")
                    self.status_label.config(text="Failed")
                    
                self.output_text.see(tk.END)
                
            except Exception as e:
                self.output_text.insert(tk.END, f"Error running {example_name}: {e}\n")
                self.status_label.config(text="Error")
                
        threading.Thread(target=run_thread, daemon=True).start()
        
    def run_all_examples(self):
        """Run all working examples"""
        if messagebox.askyesno("Confirm", "Run all working examples? This may take a moment."):
            def run_all_thread():
                for example in self.working_examples:
                    if (self.examples_dir / example).exists():
                        self.run_example(example)
                        # Small delay between examples
                        threading.Event().wait(0.5)
                        
            threading.Thread(target=run_all_thread, daemon=True).start()
            
    def clear_output(self):
        """Clear the output area"""
        self.output_text.delete(1.0, tk.END)
        self.status_label.config(text="Ready")
        
    def open_file(self):
        """Open a custom .sona file"""
        file_path = filedialog.askopenfilename(
            title="Open Sona File",
            filetypes=[("Sona files", "*.sona"), ("All files", "*.*")],
            initialdir=str(self.examples_dir)
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                self.code_text.delete(1.0, tk.END)
                self.code_text.insert(1.0, content)
                self.highlight_syntax()
                
                # Run the file
                self.output_text.insert(tk.END, f"\n=== Running {Path(file_path).name} ===\n")
                
                cmd = [sys.executable, "-m", "sona", file_path]
                process = subprocess.Popen(cmd, 
                                         cwd=str(self.sona_dir),
                                         stdout=subprocess.PIPE, 
                                         stderr=subprocess.PIPE,
                                         text=True)
                
                stdout, stderr = process.communicate()
                
                if stdout:
                    self.output_text.insert(tk.END, stdout)
                if stderr:
                    self.output_text.insert(tk.END, f"Error: {stderr}")
                    
                self.output_text.see(tk.END)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")
                
    def open_examples_folder(self):
        """Open the examples folder in file explorer"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(str(self.examples_dir))
            elif os.name == 'posix':  # macOS/Linux
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', 
                              str(self.examples_dir)])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")
            
    def show_about(self):
        """Show about dialog"""
        about_text = """Sona v0.7.0 Example Launcher

A graphical interface for exploring and running Sona programming language examples.

Features:
• Browse and run example files
• View source code with syntax highlighting  
• Real-time output display
• Support for all working v0.7.0 features

Developed for Sona Programming Language
Built with Python and tkinter"""
        
        messagebox.showinfo("About Sona Launcher", about_text)
        
    def show_features(self):
        """Show language features dialog"""
        features_text = """Sona v0.7.0 Language Features

✓ Supported Features:
• Variables and assignments
• Strings with concatenation
• Numbers (integers and floats)
• Dictionary literals and operations
• Property access with dot notation
• Module imports and function calls
• Print statements and basic I/O
• Comments and documentation

❌ Not Available in v0.7.0:
• Function definitions with parameters
• Object-oriented programming
• Control flow (if/else, loops)
• Boolean literals (use strings)
• Exception handling
• List/array operations

See the examples for practical demonstrations of working features."""        
        messagebox.showinfo("Language Features", features_text)

    def on_mode_change(self, event=None):
        """Handle execution mode change"""
        mode = self.mode_var.get()
        if mode == "Console":
            self.execution_mode = AppExecutionMode.CONSOLE_OUTPUT
            self.notebook.select(self.code_frame)
        elif mode == "Embedded App":
            self.execution_mode = AppExecutionMode.EMBEDDED_GUI
            self.notebook.select(self.app_frame)
            self.load_embedded_app()
        elif mode == "Separate Window":
            self.execution_mode = AppExecutionMode.SEPARATE_WINDOW
        elif mode == "Interactive REPL":
            self.execution_mode = AppExecutionMode.REPL_MODE
            self.notebook.select(self.repl_frame)
            self.repl_input.focus_set()
            
    def load_embedded_app(self):
        """Load embedded application for selected example"""
        example_name = self.get_selected_example()
        if not example_name:
            return
            
        # Clear existing app
        self.clear_embedded_app()
        
        # Check if example has embedded app support
        app_class = self.app_registry.get(example_name)
        if app_class:
            try:
                # Create and start embedded application
                app = app_class(self, example_name)
                app_widget = app.create_gui(self.app_container)
                if app_widget:
                    app.start()
                    self.embedded_apps[example_name] = app
                    self.no_app_label.pack_forget()
                    app_widget.pack(fill=tk.BOTH, expand=True)
                    self.status_label.config(text=f"Embedded: {example_name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load embedded app: {e}")
        else:
            # Show message for non-supported examples
            self.no_app_label.config(text=f"{example_name} does not have embedded app support.\nUse Console mode to run this example.")
            self.no_app_label.pack(expand=True)
            
    def clear_embedded_app(self):
        """Clear currently running embedded application"""
        for app in self.embedded_apps.values():
            app.stop()
        self.embedded_apps.clear()
        
        # Clear app container
        for widget in self.app_container.winfo_children():
            if widget != self.no_app_label:
                widget.destroy()
                
        self.no_app_label.pack(expand=True)
        
    def create_sample_apps(self):
        """Create sample .sona files for embedded applications"""
        sample_apps = {
            "calculator.sona": '''// Sona Calculator Application
// This is a placeholder - the actual calculator runs as an embedded GUI app
print("=== Sona Calculator ===")
print("This example demonstrates an embedded calculator application")
print("Switch to 'Embedded App' mode to use the interactive calculator")
''',
            "snake_game.sona": '''// Sona Snake Game
// This is a placeholder - the actual game runs as an embedded GUI app
print("=== Sona Snake Game ===") 
print("This example demonstrates an embedded snake game")
print("Switch to 'Embedded App' mode to play the interactive game")
print("Use WASD or arrow keys to control the snake")
''',
            "todo_manager.sona": '''// Sona Todo Manager
// This is a placeholder - the actual app runs as an embedded GUI app
print("=== Sona Todo Manager ===")
print("This example demonstrates an embedded todo management application")
print("Switch to 'Embedded App' mode to use the interactive todo manager")
''',
            "notes_manager.sona": '''// Sona Notes Manager
// This is a placeholder - the actual notes app runs as an embedded GUI app
print("=== Sona Notes Manager ===")
print("This example demonstrates an embedded notes management application")
print("Switch to 'Embedded App' mode to use the interactive notes manager")
''',
            "calendar.sona": '''// Sona Calendar Application
// This is a placeholder - the actual calendar runs as an embedded GUI app
print("=== Sona Calendar ===")
print("This example demonstrates an embedded calendar application")
print("Switch to 'Embedded App' mode to use the interactive calendar")
''',
            "file_organizer.sona": '''// Sona File Organizer
// This is a placeholder - the actual file organizer runs as an embedded GUI app
print("=== Sona File Organizer ===")
print("This example demonstrates an embedded file organization application")
print("Switch to 'Embedded App' mode to use the interactive file organizer")
''',
            "media_player.sona": '''// Sona Media Player
// This is a placeholder - the actual media player runs as an embedded GUI app
print("=== Sona Media Player ===")
print("This example demonstrates an embedded media player application")
print("Switch to 'Embedded App' mode to use the interactive media player")
''',
            "text_editor.sona": '''// Sona Text Editor
// This is a placeholder - the actual text editor runs as an embedded GUI app
print("=== Sona Text Editor ===")
print("This example demonstrates an embedded text editor application")
print("Switch to 'Embedded App' mode to use the interactive text editor")
''',
            "ping_pong.sona": '''// Sona Ping Pong Game
// This is a placeholder - the actual game runs as an embedded GUI app
print("=== Sona Ping Pong ===")
print("This example demonstrates an embedded ping pong game")
print("Switch to 'Embedded App' mode to play the interactive game")
print("Use W/S keys to control your paddle against the AI")
''',            "space_shooter.sona": '''// Sona Space Shooter Game
// This is a placeholder - the actual game runs as an embedded GUI app
print("=== Sona Space Shooter ===")
print("This example demonstrates an embedded 2D arcade shooter game")
print("Switch to 'Embedded App' mode to play the interactive shooter")
print("Use WASD keys to move and Spacebar to shoot")
''',
            "flappy_bird.sona": '''// Sona Flappy Bird Game
// This is a placeholder - the actual game runs as an embedded GUI app
print("=== Sona Flappy Bird ===")
print("This example demonstrates an embedded Flappy Bird style game")
print("Switch to 'Embedded App' mode to play the interactive game")
print("Press SPACE to flap and avoid obstacles")
''',
            "invaders.sona": '''// Sona Space Invaders Game
// This is a placeholder - the actual game runs as an embedded GUI app
print("=== Sona Space Invaders ===")
print("This example demonstrates a classic Space Invaders style game")
print("Switch to 'Embedded App' mode to play the interactive game")
print("Use Left/Right arrows to move and Spacebar to shoot")
'''
        }
        
        # Create sample files if they don't exist
        for filename, content in sample_apps.items():
            file_path = self.examples_dir / filename
            if not file_path.exists():
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                except Exception as e:
                    self.output_text.insert(tk.END, f"Warning: Could not create {filename}: {e}\n")
                    
    def update_embedded_apps(self):
        """Update all running embedded applications"""
        for app in self.embedded_apps.values():
            try:
                app.update()
            except Exception as e:
                self.output_text.insert(tk.END, f"App update error: {e}\n")
        
        # Schedule next update
        self.root.after(100, self.update_embedded_apps)

# Application execution modes and embedded app management
class AppExecutionMode:
    CONSOLE_OUTPUT = "console"
    EMBEDDED_GUI = "embedded"
    SEPARATE_WINDOW = "separate"
    REPL_MODE = "repl"

class EmbeddedApplication:
    """Base class for embedded GUI applications"""
    def __init__(self, parent, example_name):
        self.parent = parent
        self.example_name = example_name
        self.frame = None
        self.is_running = False
        
    def create_gui(self, container):
        """Override this method to create the application GUI"""
        self.frame = ttk.Frame(container)
        return self.frame
        
    def start(self):
        """Start the application"""
        self.is_running = True
        
    def stop(self):
        """Stop the application"""
        self.is_running = False
        if self.frame:
            self.frame.destroy()
            
    def update(self):
        """Update application state - called periodically"""
        pass

class CalculatorApp(EmbeddedApplication):
    """Scientific Calculator Application"""
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.display_var = tk.StringVar()
        self.display_var.set("0")
        self.memory = 0
        self.history = []
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        # Title
        title = ttk.Label(self.frame, text="Sona Calculator", 
                         font=('Arial', 14, 'bold'))
        title.grid(row=0, column=0, columnspan=4, pady=(0, 10))
        
        # Display
        display = ttk.Entry(self.frame, textvariable=self.display_var,
                           font=('Courier', 14), state='readonly',
                           justify='right', width=20)
        display.grid(row=1, column=0, columnspan=4, sticky='ew', pady=(0, 10))
        
        # Number and operation buttons
        buttons = [
            ('C', 2, 0), ('±', 2, 1), ('%', 2, 2), ('÷', 2, 3),
            ('7', 3, 0), ('8', 3, 1), ('9', 3, 2), ('×', 3, 3),
            ('4', 4, 0), ('5', 4, 1), ('6', 4, 2), ('-', 4, 3),
            ('1', 5, 0), ('2', 5, 1), ('3', 5, 2), ('+', 5, 3),
            ('0', 6, 0), ('.', 6, 1), ('=', 6, 2), ('√', 6, 3),
        ]
        
        for (text, row, col) in buttons:
            btn = ttk.Button(self.frame, text=text, width=5,
                           command=lambda t=text: self.button_click(t))
            btn.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
            
        # Configure grid weights
        for i in range(4):
            self.frame.columnconfigure(i, weight=1)
            
        # History display
        history_label = ttk.Label(self.frame, text="History:")
        history_label.grid(row=7, column=0, columnspan=4, sticky='w', pady=(10, 0))
        
        self.history_text = tk.Text(self.frame, height=4, width=30)
        self.history_text.grid(row=8, column=0, columnspan=4, sticky='ew', pady=(5, 0))
        
        return self.frame
        
    def button_click(self, button):
        current = self.display_var.get()
        
        if button == 'C':
            self.display_var.set("0")
        elif button == '=':
            try:
                # Simple expression evaluation
                expr = current.replace('×', '*').replace('÷', '/')
                result = eval(expr)
                self.display_var.set(str(result))
                self.history.append(f"{current} = {result}")
                self.update_history()
            except:
                self.display_var.set("Error")
        elif button == '√':
            try:
                result = float(current) ** 0.5
                self.display_var.set(str(result))
                self.history.append(f"√{current} = {result}")
                self.update_history()
            except:
                self.display_var.set("Error")
        elif button in '0123456789.':
            if current == "0":
                self.display_var.set(button)
            else:
                self.display_var.set(current + button)
        elif button in '+-×÷':
            if not current.endswith(('+', '-', '×', '÷')):
                self.display_var.set(current + button)
                
    def update_history(self):
        self.history_text.delete(1.0, tk.END)
        for entry in self.history[-5:]:  # Show last 5 entries
            self.history_text.insert(tk.END, entry + "\n")

class SnakeGameApp(EmbeddedApplication):
    """Enhanced Snake Game Application with improved controls"""
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.canvas = None
        self.snake = [(100, 100), (90, 100), (80, 100)]
        self.food = (200, 200)
        self.direction = "Right"
        self.next_direction = "Right"  # Buffer for direction changes
        self.score = 0
        self.game_running = False
        self.game_speed = 150  # ms between moves
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        # Title and score
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill='x', pady=(0, 10))
        
        title = ttk.Label(title_frame, text="🐍 Sona Snake Game", 
                         font=('Arial', 16, 'bold'))
        title.pack(side='left')
        
        self.score_var = tk.StringVar()
        self.score_var.set("Score: 0")
        score_label = ttk.Label(title_frame, textvariable=self.score_var,
                               font=('Arial', 14, 'bold'))
        score_label.pack(side='right')
        
        # Game canvas with border
        canvas_frame = ttk.Frame(self.frame)
        canvas_frame.pack(pady=(0, 10))
        
        self.canvas = tk.Canvas(canvas_frame, width=400, height=300, 
                               bg='#001122', highlightthickness=2,
                               highlightbackground='#00FF00')
        self.canvas.pack()
          # Control buttons
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x')
        
        # Hide start button - use Space/Enter to start
        # self.start_btn = ttk.Button(control_frame, text="🎮 Start Game",
        #                            command=self.start_game)
        # self.start_btn.pack(side='left', padx=(0, 5))
        
        self.pause_btn = ttk.Button(control_frame, text="⏸️ Pause",
                                   command=self.pause_game, state='disabled')
        self.pause_btn.pack(side='left', padx=(0, 5))
        
        reset_btn = ttk.Button(control_frame, text="🔄 Reset",
                              command=self.reset_game)
        reset_btn.pack(side='left', padx=(0, 5))
        
        # Speed control
        speed_frame = ttk.Frame(control_frame)
        speed_frame.pack(side='right', padx=20)
        
        ttk.Label(speed_frame, text="Speed:").pack(side='left')
        self.speed_var = tk.StringVar(value="Normal")
        speed_combo = ttk.Combobox(speed_frame, textvariable=self.speed_var,
                                  values=["Slow", "Normal", "Fast"],
                                  width=8, state="readonly")
        speed_combo.pack(side='left', padx=(5, 0))
        speed_combo.bind("<<ComboboxSelected>>", self.change_speed)
          # Instructions with better formatting
        instructions = ttk.Label(self.frame, 
                                text="🎮 Press SPACE or ENTER to start | WASD or Arrow Keys to move | Click canvas for focus",
                                font=('Arial', 10))
        instructions.pack(pady=(10, 0))
        
        # Enhanced key bindings - bind to multiple widgets
        self.setup_key_bindings()
        
        # Initialize the game display
        self.draw_game()
        
        return self.frame
        
    def setup_key_bindings(self):
        """Setup comprehensive key bindings"""
        # Make canvas focusable and bind events
        self.canvas.configure(takefocus=True)
        
        # Bind to canvas
        self.canvas.bind("<KeyPress>", self.key_pressed)
        self.canvas.bind("<Button-1>", lambda e: self.canvas.focus_set())
        
        # Bind to frame as well
        self.frame.bind("<KeyPress>", self.key_pressed)
        self.frame.configure(takefocus=True)
        
        # Ensure canvas gets focus when created
        self.frame.after(100, lambda: self.canvas.focus_set())        
    def change_speed(self, event=None):
        """Change game speed based on selection"""
        speed = self.speed_var.get()
        if speed == "Slow":
            self.game_speed = 250
        elif speed == "Normal":
            self.game_speed = 150
        elif speed == "Fast":
            self.game_speed = 100
        
    def start_game(self):
        """Start the game"""
        self.game_running = True
        # No start button to disable - use Space/Enter to start
        self.pause_btn.config(state='normal')
        self.canvas.focus_set()  # Ensure canvas has focus
        self.generate_food()  # Generate initial food
        self.game_loop()
        
    def pause_game(self):
        """Pause/Resume the game"""
        self.game_running = not self.game_running
        if self.game_running:
            self.pause_btn.config(text="⏸️ Pause")
            self.canvas.focus_set()
            self.game_loop()
        else:
            self.pause_btn.config(text="▶️ Resume")
            
    def reset_game(self):
        """Reset the game to initial state"""
        self.game_running = False
        self.snake = [(100, 100), (90, 100), (80, 100)]
        self.food = (200, 200)
        self.direction = "Right"
        self.next_direction = "Right"
        self.score = 0
        self.score_var.set("Score: 0")
        # No start button to re-enable - use Space/Enter to start
        self.pause_btn.config(state='disabled', text="⏸️ Pause")
        self.draw_game()
        
    def key_pressed(self, event):
        """Handle key press events with improved logic"""
        key = event.keysym.lower()
        
        # Start game with Space or Enter when not running
        if not self.game_running and key in ['space', 'return']:
            self.start_game()
            return
            
        if not self.game_running:
            return
        
        # Map keys to directions with buffer to prevent rapid direction changes
        if key in ['up', 'w'] and self.direction != "Down":
            self.next_direction = "Up"
        elif key in ['down', 's'] and self.direction != "Up":
            self.next_direction = "Down"
        elif key in ['left', 'a'] and self.direction != "Right":
            self.next_direction = "Left"
        elif key in ['right', 'd'] and self.direction != "Left":
            self.next_direction = "Right"
            
    def generate_food(self):
        """Generate food at a random location not on snake"""
        import random
        while True:
            food_x = random.randint(0, 39) * 10
            food_y = random.randint(0, 29) * 10
            self.food = (food_x, food_y)
            if self.food not in self.snake:
                break
            
    def game_loop(self):
        """Main game loop with improved collision detection"""
        if not self.game_running:
            return
            
        # Update direction from buffer
        self.direction = self.next_direction
        
        # Move snake
        head_x, head_y = self.snake[0]
        
        if self.direction == "Up":
            head_y -= 10
        elif self.direction == "Down":
            head_y += 10
        elif self.direction == "Left":
            head_x -= 10
        elif self.direction == "Right":
            head_x += 10
            
        new_head = (head_x, head_y)
        
        # Check wall collisions
        if head_x < 0 or head_x >= 400 or head_y < 0 or head_y >= 300:
            self.game_over("Hit the wall!")
            return
            
        # Check self collision
        if new_head in self.snake:
            self.game_over("Bit yourself!")
            return
            
        self.snake.insert(0, new_head)
        
        # Check food collision (exact match)
        if new_head == self.food:
            self.score += 10
            self.score_var.set(f"Score: {self.score}")
            self.generate_food()
            
            # Increase speed slightly as score increases
            if self.score % 50 == 0 and self.game_speed > 80:
                self.game_speed -= 5
        else:
            self.snake.pop()
            
        self.draw_game()
        self.frame.after(self.game_speed, self.game_loop)
        
    def draw_game(self):
        """Draw the game with enhanced graphics"""
        if not self.canvas:
            return
            
        self.canvas.delete("all")
        
        # Draw snake with gradient effect
        for i, segment in enumerate(self.snake):
            x, y = segment
            if i == 0:  # Head
                self.canvas.create_rectangle(x, y, x+10, y+10, 
                                           fill="#00FF00", outline="#FFFFFF", width=2)
                # Add eyes
                self.canvas.create_oval(x+2, y+2, x+4, y+4, fill="white")
                self.canvas.create_oval(x+6, y+2, x+8, y+4, fill="white")
            else:  # Body
                intensity = max(100, 255 - i * 10)
                color = f"#{intensity:02x}{intensity:02x}00"  # Fade to darker green
                self.canvas.create_rectangle(x, y, x+10, y+10, 
                                           fill=color, outline="#008800")
            
        # Draw food with animation effect
        x, y = self.food
        self.canvas.create_oval(x, y, x+10, y+10, 
                               fill="#FF0000", outline="#FFFF00", width=2)
        self.canvas.create_oval(x+2, y+2, x+8, y+8, 
                               fill="#FF4444", outline="")
        
    def game_over(self, reason="Game Over"):
        """Handle game over with reason"""
        self.game_running = False
        # No start button to re-enable - use Space/Enter to start
        self.pause_btn.config(state='disabled')
        
        # Draw game over message on canvas
        self.canvas.create_text(200, 150, text=f"{reason}\nFinal Score: {self.score}",
                               fill="white", font=('Arial', 16, 'bold'),
                               justify='center')
        messagebox.showinfo("Game Over", f"{reason}\nFinal Score: {self.score}")


class PingPongApp(EmbeddedApplication):
    """Ping Pong Game Application"""
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.canvas = None
        self.ball_x = 200
        self.ball_y = 150
        self.ball_dx = 3
        self.ball_dy = 3
        self.paddle1_y = 125
        self.paddle2_y = 125
        self.score1 = 0
        self.score2 = 0
        self.game_running = False
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill='x', pady=(0, 10))
        
        title = ttk.Label(title_frame, text="🏓 Ping Pong", 
                         font=('Arial', 16, 'bold'))
        title.pack(side='left')
        
        self.score_var = tk.StringVar()
        self.score_var.set("Player: 0 | AI: 0")
        score_label = ttk.Label(title_frame, textvariable=self.score_var,
                               font=('Arial', 12))
        score_label.pack(side='right')
        
        self.canvas = tk.Canvas(self.frame, width=400, height=300, 
                               bg='#000033', highlightthickness=2)
        self.canvas.pack(pady=(0, 10))
        
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x')
        
        # Hide start button - use Space/Enter to start
        # self.start_btn = ttk.Button(control_frame, text="Start",
        #                            command=self.start_game)
        # self.start_btn.pack(side='left', padx=(0, 5))
        
        reset_btn = ttk.Button(control_frame, text="Reset",
                              command=self.reset_game)
        reset_btn.pack(side='left')
        
        instructions = ttk.Label(self.frame, 
                                text="Press SPACE or ENTER to start | W/S keys to control left paddle")
        instructions.pack(pady=(10, 0))
        
        self.canvas.configure(takefocus=True)
        self.canvas.bind("<KeyPress>", self.key_pressed)
        self.canvas.bind("<Button-1>", lambda e: self.canvas.focus_set())
        
        # Ensure canvas gets focus immediately and when clicked
        self.frame.after(100, lambda: self.canvas.focus_set())
        self.frame.bind("<Button-1>", lambda e: self.canvas.focus_set())
        
        self.draw_game()
        return self.frame
        
    def start_game(self):
        self.game_running = True
        # No start button to disable - use Space/Enter to start
        self.canvas.focus_set()
        self.game_loop()
        
    def reset_game(self):
        self.game_running = False
        self.ball_x = 200
        self.ball_y = 150
        self.ball_dx = 3
        self.ball_dy = 3
        self.paddle1_y = 125
        self.paddle2_y = 125
        self.score1 = 0
        self.score2 = 0
        self.score_var.set("Player: 0 | AI: 0")
        # No start button to re-enable - use Space/Enter to start
        self.draw_game()
        
    def key_pressed(self, event):
        key = event.keysym.lower()
        
        # Start game with Space or Enter when not running
        if not self.game_running and key in ['space', 'return']:
            self.start_game()
            return
            
        if not self.game_running:
            return
            
        if key == 'w' and self.paddle1_y > 0:
            self.paddle1_y -= 10
        elif key == 's' and self.paddle1_y < 250:
            self.paddle1_y += 10
            
    def game_loop(self):
        if not self.game_running:
            return
            
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy
        
        if self.ball_y <= 0 or self.ball_y >= 290:
            self.ball_dy = -self.ball_dy
            
        # Paddle collisions
        if (self.ball_x <= 20 and 
            self.paddle1_y <= self.ball_y <= self.paddle1_y + 50):
            self.ball_dx = abs(self.ball_dx)
            
        if (self.ball_x >= 370 and 
            self.paddle2_y <= self.ball_y <= self.paddle2_y + 50):
            self.ball_dx = -abs(self.ball_dx)
            
        # AI paddle
        paddle_center = self.paddle2_y + 25
        if paddle_center < self.ball_y:
            self.paddle2_y += min(3, self.ball_y - paddle_center)
        elif paddle_center > self.ball_y:
            self.paddle2_y -= min(3, paddle_center - self.ball_y)
        self.paddle2_y = max(0, min(250, self.paddle2_y))
        
        # Scoring
        if self.ball_x <= 0:
            self.score2 += 1
            self.reset_ball()
        elif self.ball_x >= 400:
            self.score1 += 1
            self.reset_ball()
            
        self.score_var.set(f"Player: {self.score1} | AI: {self.score2}")
        
        if self.score1 >= 5 or self.score2 >= 5:
            self.game_over()
            return
            
        self.draw_game()
        self.frame.after(16, self.game_loop)
        
    def reset_ball(self):
        self.ball_x = 200
        self.ball_y = 150
        
    def draw_game(self):
        if not self.canvas:
            return
        self.canvas.delete("all")
        
        # Center line
        for y in range(0, 300, 20):
            self.canvas.create_rectangle(198, y, 202, y+10, fill="white")
            
        # Paddles
        self.canvas.create_rectangle(10, self.paddle1_y, 20, self.paddle1_y+50, 
                                   fill="#00FF00")
        self.canvas.create_rectangle(380, self.paddle2_y, 390, self.paddle2_y+50, 
                                   fill="#FF0000")
        
        # Ball
        self.canvas.create_oval(self.ball_x-5, self.ball_y-5,                               self.ball_x+5, self.ball_y+5, fill="white")
        
    def game_over(self):
        self.game_running = False
        # No start button to re-enable - use Space/Enter to start
        winner = "Player" if self.score1 >= 5 else "AI"
        messagebox.showinfo("Game Over", f"{winner} Wins!")


class ArcadeShooterApp(EmbeddedApplication):
    """Enhanced 2D Arcade Shooter Game with Power-ups"""
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.canvas = None
        self.player_x = 200
        self.player_y = 280
        self.bullets = []
        self.enemies = []
        self.enemy_bullets = []  # Store enemy bullets
        self.power_ups = []
        self.score = 0
        self.lives = 3
        self.level = 1
        self.game_running = False
        self.keys_pressed = set()
        
        # Power-up states
        self.rapid_fire = False
        self.double_shot = False
        self.shield = False
        self.rapid_fire_timer = 0
        self.double_shot_timer = 0
        self.shield_timer = 0
        
        # Upgrade timers
        self.power_up_spawn_timer = 0
        self.last_shot_time = 0
          # Enemy shooting variables
        self.enemy_shot_timer = 0
        self.enemy_shot_cooldown = 60  # Frames between enemy shots
        self.enemy_shot_chance = 0.1   # Probability of enemy shooting when eligible
        self.enemy_shot_speed = 4      # Speed of enemy bullets
        self.enemy_aim_accuracy = 0.7  # How accurately enemies aim at player (0-1)
        
        # Omni-directional movement
        self.player_velocity_x = 0
        self.player_velocity_y = 0
        self.move_speed = 5
        
        # Enemy movement
        self.enemy_velocities = {}     # Dictionary to track enemy velocities
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill='x', pady=(0, 10))
        
        title = ttk.Label(title_frame, text="🚀 Space Shooter", 
                         font=('Arial', 16, 'bold'))
        title.pack(side='left')
        
        stats_frame = ttk.Frame(title_frame)
        stats_frame.pack(side='right')
        
        self.score_var = tk.StringVar()
        self.score_var.set("Score: 0")
        score_label = ttk.Label(stats_frame, textvariable=self.score_var,
                               font=('Arial', 12))
        score_label.pack(side='top')
        
        self.lives_var = tk.StringVar()
        self.lives_var.set("Lives: 3")
        lives_label = ttk.Label(stats_frame, textvariable=self.lives_var,
                               font=('Arial', 12))
        lives_label.pack(side='top')
        
        self.canvas = tk.Canvas(self.frame, width=400, height=300, 
                               bg='#000011', highlightthickness=2)
        self.canvas.pack(pady=(0, 10))
        
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x')
          # Hide start button - use Space/Enter to start
        # self.start_btn = ttk.Button(control_frame, text="Start",
        #                            command=self.start_game)
        # self.start_btn.pack(side='left', padx=(0, 5))
        
        reset_btn = ttk.Button(control_frame, text="Reset",
                              command=self.reset_game)
        reset_btn.pack(side='left')
        
        instructions = ttk.Label(self.frame, 
                                text="Press SPACE or ENTER to start | A/D: Move, Space: Shoot")
        instructions.pack(pady=(10, 0))
        
        self.canvas.configure(takefocus=True)
        self.canvas.bind("<KeyPress>", self.key_press)
        self.canvas.bind("<KeyRelease>", self.key_release)
        self.canvas.bind("<Button-1>", lambda e: self.canvas.focus_set())
        
        self.draw_game()
        return self.frame
        
    def key_press(self, event):
        key = event.keysym.lower()
        
        # Start game with Space or Enter when not running
        if not self.game_running and key in ['space', 'return']:
            self.start_game()
            return
            
        self.keys_pressed.add(key)
        
    def key_release(self, event):
        self.keys_pressed.discard(event.keysym.lower())
        
    def start_game(self):
        self.game_running = True
        # No start button to disable - use Space/Enter to start        self.canvas.focus_set()
        self.enemy_timer = 0
        self.game_loop()
        
    def reset_game(self):
        self.game_running = False
        self.player_x = 200
        self.bullets = []
        self.enemies = []
        self.enemy_bullets = []
        self.enemy_velocities = {}  # Clear enemy velocity tracking
        self.score = 0
        self.lives = 3
        self.keys_pressed.clear()
        self.score_var.set("Score: 0")
        self.lives_var.set("Lives: 3")
        # No start button to re-enable - use Space/Enter to start
        self.draw_game()
        
    def game_loop(self):
        if not self.game_running:
            return
            
        # Handle omni-directional input
        self.player_velocity_x = 0
        self.player_velocity_y = 0
        
        # Horizontal movement
        if 'a' in self.keys_pressed or 'left' in self.keys_pressed:
            self.player_velocity_x = -self.move_speed
        if 'd' in self.keys_pressed or 'right' in self.keys_pressed:
            self.player_velocity_x = self.move_speed
            
        # Vertical movement
        if 'w' in self.keys_pressed or 'up' in self.keys_pressed:
            self.player_velocity_y = -self.move_speed
        if 's' in self.keys_pressed or 'down' in self.keys_pressed:
            self.player_velocity_y = self.move_speed
            
        # Apply movement with bounds checking
        self.player_x = max(10, min(390, self.player_x + self.player_velocity_x))
        self.player_y = max(40, min(280, self.player_y + self.player_velocity_y))
        
        # Handle shooting
        import time
        current_time = time.time() * 1000  # Convert to milliseconds
        shot_delay = 300  # ms between shots (reduced with rapid_fire)
        if self.rapid_fire:
            shot_delay = 100
            
        if 'space' in self.keys_pressed and len(self.bullets) < 5:
            if current_time - self.last_shot_time > shot_delay:
                self.bullets.append((self.player_x, self.player_y - 10))
                if self.double_shot:  # Add side bullets if double shot is active
                    self.bullets.append((self.player_x - 8, self.player_y - 5))
                    self.bullets.append((self.player_x + 8, self.player_y - 5))
                self.last_shot_time = current_time
            
        # Move player bullets
        self.bullets = [(x, y-8) for x, y in self.bullets if y > 0]
        
        # Enhanced enemy shooting logic with aiming
        import random
        self.enemy_shot_timer += 1
        if self.enemy_shot_timer >= self.enemy_shot_cooldown:
            self.enemy_shot_timer = 0
            # Choose eligible enemies to shoot (not too close to each other)
            if self.enemies:
                # Scale shooting frequency with number of enemies and level
                base_chance = min(0.6, 0.1 + (self.level * 0.05))
                num_shooters = min(3, max(1, len(self.enemies) // 3))
                
                # Select diverse enemy positions for shooting
                potential_shooters = random.sample(self.enemies, min(num_shooters, len(self.enemies)))
                
                for ex, ey in potential_shooters:
                    if random.random() < base_chance:
                        # Calculate aimed shot toward player
                        if self.enemy_aim_accuracy > random.random():
                            # Aimed shot - calculate trajectory toward player
                            dx = self.player_x - ex
                            dy = self.player_y - ey
                            if dy != 0:  # Avoid division by zero
                                # Normalize and apply speed
                                import math
                                distance = math.sqrt(dx*dx + dy*dy)
                                if distance > 0:
                                    bullet_dx = (dx / distance) * self.enemy_shot_speed * 0.3  # Slower horizontal
                                    bullet_dy = (dy / distance) * self.enemy_shot_speed
                                    # Store bullet with velocity
                                    self.enemy_bullets.append((ex, ey + 10, bullet_dx, bullet_dy))
                                else:
                                    # Fallback to straight down
                                    self.enemy_bullets.append((ex, ey + 10, 0, self.enemy_shot_speed))
                            else:
                                self.enemy_bullets.append((ex, ey + 10, 0, self.enemy_shot_speed))
                        else:
                            # Random shot - less accurate
                            spread = random.uniform(-2, 2)
                            self.enemy_bullets.append((ex, ey + 10, spread, self.enemy_shot_speed))
        
        # Move enemy bullets with trajectory
        new_enemy_bullets = []
        for bullet_data in self.enemy_bullets:
            if len(bullet_data) == 4:  # New format with velocity
                bx, by, vx, vy = bullet_data
                new_x = bx + vx
                new_y = by + vy
                if new_y < 300 and new_x > 0 and new_x < 400:  # Keep in bounds
                    new_enemy_bullets.append((new_x, new_y, vx, vy))
            else:  # Old format - straight down
                bx, by = bullet_data[:2]
                new_y = by + self.enemy_shot_speed
                if new_y < 300:
                    new_enemy_bullets.append((bx, new_y, 0, self.enemy_shot_speed))
        self.enemy_bullets = new_enemy_bullets
        
        # Enhanced omni-directional enemy movement
        new_enemies = []
        for i, (x, y) in enumerate(self.enemies):
            if y < 300:
                # Get or create velocity for this enemy
                enemy_id = f"{x}_{y}_{i}"
                if enemy_id not in self.enemy_velocities:
                    # Initialize with random movement pattern
                    pattern = random.choice(['aggressive', 'evasive', 'patrol', 'dive'])
                    if pattern == 'aggressive':
                        # Move toward player aggressively
                        target_x = self.player_x
                        target_y = self.player_y
                        dx = (target_x - x) * 0.015  # Slower approach
                        dy = abs(target_y - y) * 0.008 + 1.5  # Always move down
                    elif pattern == 'evasive':
                        # Move away from player
                        dx = (x - self.player_x) * 0.01
                        dy = 1.2
                        # Add some randomness
                        dx += random.uniform(-1, 1)
                    elif pattern == 'patrol':
                        # Patrol left-right while descending
                        dx = random.choice([-2, 2]) + random.uniform(-0.5, 0.5)
                        dy = 1.0
                    else:  # dive
                        # Dive straight down quickly
                        dx = random.uniform(-0.5, 0.5)
                        dy = 3.0
                    
                    self.enemy_velocities[enemy_id] = (dx, dy, pattern)
                else:
                    dx, dy, pattern = self.enemy_velocities[enemy_id]
                    
                    # Occasionally change behavior
                    if random.random() < 0.02:  # 2% chance per frame
                        new_pattern = random.choice(['aggressive', 'evasive', 'patrol', 'dive'])
                        if new_pattern == 'aggressive':
                            dx = (self.player_x - x) * 0.02
                            dy = abs(self.player_y - y) * 0.01 + 1.5
                        elif new_pattern == 'evasive':
                            dx = (x - self.player_x) * 0.015
                            dy = 1.2
                        elif new_pattern == 'patrol':
                            dx = random.choice([-2, 2])
                            dy = 1.0
                        else:  # dive
                            dx = random.uniform(-0.5, 0.5)
                            dy = 3.0
                        self.enemy_velocities[enemy_id] = (dx, dy, new_pattern)
                
                # Apply movement with bounds checking
                new_x = x + dx
                new_y = y + dy
                
                # Bounce off walls
                if new_x < 10 or new_x > 390:
                    dx = -dx * 0.8  # Reverse and reduce speed
                    new_x = max(10, min(390, new_x))
                    self.enemy_velocities[enemy_id] = (dx, dy, pattern)
                
                new_enemies.append((new_x, new_y))
        
        self.enemies = new_enemies
        
        # Spawn enemies with varied timing
        self.enemy_timer += 1
        spawn_threshold = max(20, 60 - self.score // 100)  # Spawn faster as score increases
        if self.enemy_timer >= spawn_threshold:
            # Sometimes spawn multiple enemies
            enemy_count = 1
            if random.random() < 0.2:  # 20% chance for extra enemies
                enemy_count = random.randint(2, 3)
            
            # Divide screen into sections to ensure more even distribution
            screen_width = 380
            segment_width = screen_width // enemy_count
            
            for i in range(enemy_count):
                # Calculate spawn position within the segment to ensure even distribution
                segment_start = 10 + (i * segment_width)
                segment_end = segment_start + segment_width
                spawn_x = random.randint(segment_start, segment_end - 10)
                
                # Occasionally add formation patterns for visual interest
                if random.random() < 0.15 and enemy_count > 1:  # 15% chance for patterns
                    pattern_type = random.choice(['v', 'line', 'diagonal'])
                    if pattern_type == 'v':
                        # V-shape formation
                        center_x = 200
                        offset = (i - (enemy_count-1)/2) * 30
                        spawn_x = center_x + offset
                    elif pattern_type == 'line':
                        # Horizontal line formation
                        spawn_x = segment_start + segment_width//2
                    # diagonal handled by default random positioning
                
                self.enemies.append((spawn_x, 0))
            self.enemy_timer = 0
              # Check collisions
        new_bullets = []
        new_enemies = []
        new_enemy_bullets = []
        
        # Check player bullets hitting enemies
        for bx, by in self.bullets:
            hit = False
            for ex, ey in self.enemies:
                if abs(bx - ex) < 15 and abs(by - ey) < 15:
                    self.score += 10
                    self.score_var.set(f"Score: {self.score}")
                    hit = True
                    break
            if not hit:
                new_bullets.append((bx, by))
                
        # Check which enemies were hit and clean up velocities
        new_enemies = []
        for i, (ex, ey) in enumerate(self.enemies):
            hit = False
            for bx, by in self.bullets:
                if abs(bx - ex) < 15 and abs(by - ey) < 15:
                    hit = True
                    # Clean up velocity tracking for destroyed enemy
                    enemy_id = f"{ex}_{ey}_{i}"
                    if enemy_id in self.enemy_velocities:
                        del self.enemy_velocities[enemy_id]
                    break
            if not hit:
                new_enemies.append((ex, ey))
                
        self.bullets = new_bullets
        self.enemies = new_enemies
          # Check enemy bullets hitting player
        new_enemy_bullets = []
        for bullet_data in self.enemy_bullets:
            if len(bullet_data) >= 2:
                ebx, eby = bullet_data[0], bullet_data[1]
                hit_player = abs(ebx - self.player_x) < 15 and abs(eby - self.player_y) < 15
                
                if hit_player:
                    if self.shield:
                        # Shield absorbs the hit
                        self.shield = False
                    else:
                        self.lives -= 1
                        self.lives_var.set(f"Lives: {self.lives}")
                    # Bullet is destroyed on hit, don't add to new list
                else:
                    # Bullet didn't hit, keep it
                    new_enemy_bullets.append(bullet_data)
        
        self.enemy_bullets = new_enemy_bullets
          
        # Check player collisions with enemies
        for ex, ey in self.enemies[:]:
            if abs(self.player_x - ex) < 20 and abs(self.player_y - ey) < 20:
                if self.shield:
                    # Shield protects from collision
                    self.shield = False
                else:
                    self.lives -= 1
                    self.lives_var.set(f"Lives: {self.lives}")
                self.enemies.remove((ex, ey))
                
        if self.lives <= 0:
            self.game_over()
            return
            
        self.draw_game()
        self.frame.after(16, self.game_loop)
        
    def draw_game(self):
        """Draw the enhanced game with power-ups and effects"""
        if not self.canvas:
            return
        self.canvas.delete("all")
        
        # Draw stars background
        import random
        random.seed(42)  # Fixed seed for consistent stars
        for _ in range(30):
            x = random.randint(0, 400)
            y = random.randint(0, 300)
            self.canvas.create_rectangle(x, y, x+1, y+1, fill="white", outline="")
        
        # Draw player (spaceship) with shield effect
        px, py = self.player_x, self.player_y
        if self.shield:
            # Draw shield effect
            self.canvas.create_oval(px-15, py-15, px+15, py+15,
                                   outline="#00FFFF", width=2, fill="")
        
        self.canvas.create_polygon(px, py-10, px-8, py+5, px+8, py+5,
                                  fill="#00FFFF", outline="white")
          # Draw player bullets with upgrade effects
        for bx, by in self.bullets:
            if self.rapid_fire:
                self.canvas.create_oval(bx-3, by-7, bx+3, by+7, 
                                       fill="red", outline="orange")
            elif self.double_shot:
                self.canvas.create_oval(bx-2, by-5, bx+2, by+5, 
                                       fill="blue", outline="cyan")
            else:
                self.canvas.create_oval(bx-2, by-5, bx+2, by+5, 
                                       fill="yellow", outline="orange")
                                         # Draw enemy bullets
        for bullet_data in self.enemy_bullets:
            if len(bullet_data) >= 2:
                ebx, eby = bullet_data[0], bullet_data[1]
                # Use different colors based on bullet type
                if len(bullet_data) >= 4:  # Aimed bullets with trajectory
                    vx, vy = bullet_data[2], bullet_data[3]
                    if abs(vx) > 1:  # Moving bullet
                        self.canvas.create_oval(ebx-3, eby-4, ebx+3, eby+4,
                                              fill="red", outline="orange")
                        # Add directional trail
                        trail_x = ebx - vx * 2
                        trail_y = eby - vy * 2
                        self.canvas.create_line(trail_x, trail_y, ebx, eby,
                                              fill="red", width=2)
                    else:  # Straight down bullet
                        self.canvas.create_oval(ebx-2, eby-4, ebx+2, eby+4,
                                              fill="purple", outline="magenta")
                        self.canvas.create_line(ebx, eby-6, ebx, eby+1,
                                              fill="purple", width=1)
                else:  # Old format bullets
                    self.canvas.create_oval(ebx-2, eby-4, ebx+2, eby+4,
                                          fill="purple", outline="magenta")
                    self.canvas.create_line(ebx, eby-6, ebx, eby+1,
                                          fill="purple", width=1)
        
        # Draw enemies with level-based colors
        enemy_colors = ["#FF0000", "#FF4444", "#FF8888", "#FFAAAA"]
        color = enemy_colors[min(self.level - 1, 3)]
        for ex, ey in self.enemies:
            self.canvas.create_polygon(ex, ey+10, ex-8, ey-5, ex+8, ey-5,
                                      fill=color, outline="white")
        
        # Draw power-ups
        for px, py, ptype in self.power_ups:
            if ptype == 'rapid_fire':
                self.canvas.create_rectangle(px-5, py-5, px+5, py+5,
                                           fill="red", outline="yellow")
                self.canvas.create_text(px, py, text="R", fill="white", font=('Arial', 8, 'bold'))
            elif ptype == 'double_shot':
                self.canvas.create_rectangle(px-5, py-5, px+5, py+5,
                                           fill="blue", outline="cyan")
                self.canvas.create_text(px, py, text="D", fill="white", font=('Arial', 8, 'bold'))
            elif ptype == 'shield':
                self.canvas.create_oval(px-5, py-5, px+5, py+5,
                                       fill="cyan", outline="white")
                self.canvas.create_text(px, py, text="S", fill="black", font=('Arial', 8, 'bold'))
            elif ptype == 'extra_life':
                self.canvas.create_rectangle(px-5, py-5, px+5, py+5,
                                           fill="green", outline="white")
                self.canvas.create_text(px, py, text="+", fill="white", font=('Arial', 8, 'bold'))
        
        # Draw UI elements
        self.canvas.create_text(50, 20, text=f"Level: {self.level}", 
                               fill="white", font=('Arial', 12, 'bold'))
          # Draw active upgrades
        y_offset = 40
        if self.rapid_fire:
            self.canvas.create_text(50, y_offset, text="RAPID FIRE!", 
                                   fill="red", font=('Arial', 10, 'bold'))
            y_offset += 20
        if self.double_shot:
            self.canvas.create_text(50, y_offset, text="DOUBLE SHOT!", 
                                   fill="blue", font=('Arial', 10, 'bold'))
            y_offset += 20
        if self.shield:            self.canvas.create_text(50, y_offset, text="SHIELD ACTIVE!", 
                                   fill="cyan", font=('Arial', 10, 'bold'))
        
    def game_over(self):
        self.game_running = False
        # No start button to re-enable - use Space/Enter to start
        messagebox.showinfo("Game Over", f"Final Score: {self.score}")


class InvadersApp(EmbeddedApplication):
    """Classic Space Invaders style game"""
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.canvas = None
        self.player_x = 200
        self.bullets = []
        self.enemies = []
        self.barriers = []
        self.score = 0
        self.lives = 3
        self.level = 1
        self.game_running = False
        self.keys_pressed = set()
        self.last_shot_time = 0
        self.shot_cooldown = 300  # milliseconds between shots
        self.enemy_move_timer = 0
        self.enemy_move_delay = 30  # frames between enemy movements
        self.enemy_direction = 1  # 1 = right, -1 = left
        self.enemy_descent_amount = 10  # pixels to move down when changing direction
        self.enemy_fire_rate = 200  # higher = less frequent shots
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill='x', pady=(0, 10))
        
        title = ttk.Label(title_frame, text="👾 Space Invaders", 
                         font=('Arial', 16, 'bold'))
        title.pack(side='left')
        
        stats_frame = ttk.Frame(title_frame)
        stats_frame.pack(side='right')
        
        self.score_var = tk.StringVar()
        self.score_var.set("Score: 0")
        score_label = ttk.Label(stats_frame, textvariable=self.score_var,
                               font=('Arial', 12))
        score_label.pack(side='top')
        
        self.lives_var = tk.StringVar()
        self.lives_var.set("Lives: 3")
        lives_label = ttk.Label(stats_frame, textvariable=self.lives_var,
                               font=('Arial', 12))
        lives_label.pack(side='top')
        
        self.canvas = tk.Canvas(self.frame, width=400, height=300, 
                               bg='#000011', highlightthickness=2)
        self.canvas.pack(pady=(0, 10))
        
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x')
        
        reset_btn = ttk.Button(control_frame, text="Reset",
                              command=self.reset_game)
        reset_btn.pack(side='left')
        
        instructions = ttk.Label(self.frame, 
                                text="Press SPACE or ENTER to start | Left/Right: Move, Space: Shoot")
        instructions.pack(pady=(10, 0))
        
        self.canvas.configure(takefocus=True)
        self.canvas.bind("<KeyPress>", self.key_press)
        self.canvas.bind("<KeyRelease>", self.key_release)
        self.canvas.bind("<Button-1>", lambda e: self.canvas.focus_set())
        
        self.initialize_barriers()
        self.draw_game()
        return self.frame
    
    def initialize_barriers(self):
        """Create defensive barriers for the player"""
        self.barriers = []
        for x_pos in [80, 160, 240, 320]:
            for x_offset in range(-15, 16, 5):
                for y_offset in range(0, 15, 5):
                    self.barriers.append({
                        'x': x_pos + x_offset,
                        'y': 230 + y_offset,
                        'health': 3  # Number of hits barrier can take
                    })
        
    def key_press(self, event):
        key = event.keysym.lower()
        
        # Start game with Space or Enter when not running
        if not self.game_running and key in ['space', 'return']:
            self.start_game()
            return
            
        self.keys_pressed.add(key)
        
    def key_release(self, event):
        self.keys_pressed.discard(event.keysym.lower())
        
    def start_game(self):
        if self.game_running:
            return
            
        self.game_running = True
        self.canvas.focus_set()
        self.setup_enemies()
        self.game_loop()
        
    def reset_game(self):
        self.game_running = False
        self.player_x = 200
        self.bullets = []
        self.enemies = []
        self.score = 0
        self.lives = 3
        self.level = 1
        self.keys_pressed.clear()
        self.enemy_direction = 1
        self.score_var.set("Score: 0")
        self.lives_var.set("Lives: 3")
        self.initialize_barriers()
        self.draw_game()
        
    def setup_enemies(self):
        """Create grid of enemies based on level"""
        self.enemies = []
        rows = min(5, 3 + self.level // 2)  # More rows in higher levels
        cols = 8
        
        for row in range(rows):
            for col in range(cols):
                enemy_type = min(2, row // 2)  # Different enemy types based on row
                self.enemies.append({
                    'x': 50 + col * 40,
                    'y': 50 + row * 30,
                    'type': enemy_type,
                    'alive': True
                })
    
    def game_loop(self):
        if not self.game_running:
            return
            
        # Handle player movement
        if 'left' in self.keys_pressed:
            self.player_x = max(20, self.player_x - 5)
        if 'right' in self.keys_pressed:
            self.player_x = min(380, self.player_x + 5)
            
        # Handle shooting
        import time
        current_time = int(time.time() * 1000)
        if 'space' in self.keys_pressed and current_time - self.last_shot_time > self.shot_cooldown:
            self.bullets.append({'x': self.player_x, 'y': 270, 'type': 'player'})
            self.last_shot_time = current_time
          
        # Move player bullets
        import random
        new_bullets = []
        for bullet in self.bullets:
            if bullet['type'] == 'player':
                new_y = bullet['y'] - 8
                if new_y > 0:
                    bullet['y'] = new_y
                    new_bullets.append(bullet)
            else:  # enemy bullet
                new_y = bullet['y'] + 5
                if new_y < 300:
                    bullet['y'] = new_y
                    new_bullets.append(bullet)
        self.bullets = new_bullets
        
        # Move enemies
        self.enemy_move_timer += 1
        if self.enemy_move_timer >= self.enemy_move_delay:
            self.enemy_move_timer = 0
            
            # Check if any enemies hit the edge
            edge_hit = False
            enemy_min_x = 400
            enemy_max_x = 0
            
            for enemy in self.enemies:
                if enemy['alive']:
                    enemy_min_x = min(enemy_min_x, enemy['x'])
                    enemy_max_x = max(enemy_max_x, enemy['x'])
            
            if enemy_min_x <= 20 and self.enemy_direction < 0:
                edge_hit = True
            elif enemy_max_x >= 380 and self.enemy_direction > 0:
                edge_hit = True
            
            if edge_hit:
                # Change direction and move down
                self.enemy_direction *= -1
                for enemy in self.enemies:
                    if enemy['alive']:
                        enemy['y'] += self.enemy_descent_amount
            else:
                # Move enemies horizontally
                for enemy in self.enemies:
                    if enemy['alive']:
                        enemy['x'] += 5 * self.enemy_direction
            
            # Random enemy shooting
            for enemy in self.enemies:
                if enemy['alive'] and random.randint(0, self.enemy_fire_rate) == 0:
                    self.bullets.append({'x': enemy['x'], 'y': enemy['y'] + 15, 'type': 'enemy'})
        
        # Check collisions
        # Check player bullets vs enemies
        for bullet in self.bullets[:]:
            if bullet['type'] != 'player':
                continue
                
            hit = False
            for enemy in self.enemies:
                if not enemy['alive']:
                    continue
                    
                if (abs(bullet['x'] - enemy['x']) < 15 and 
                    abs(bullet['y'] - enemy['y']) < 15):
                    enemy['alive'] = False
                    score_value = (3 - enemy['type']) * 10  # Higher score for tougher enemies
                    self.score += score_value
                    self.score_var.set(f"Score: {self.score}")
                    hit = True
                    break
                    
            if hit and bullet in self.bullets:
                self.bullets.remove(bullet)
        
        # Check enemy bullets vs player
        player_hit = False
        for bullet in self.bullets[:]:
            if bullet['type'] != 'enemy':
                continue
                
            if (abs(bullet['x'] - self.player_x) < 15 and 
                abs(bullet['y'] - 280) < 15):
                player_hit = True
                self.bullets.remove(bullet)
                break
        
        if player_hit:
            self.lives -= 1
            self.lives_var.set(f"Lives: {self.lives}")
            if self.lives <= 0:
                self.game_over()
                return
        
        # Check bullets vs barriers
        for bullet in self.bullets[:]:
            for barrier in self.barriers[:]:
                if (abs(bullet['x'] - barrier['x']) < 5 and 
                    abs(bullet['y'] - barrier['y']) < 5):
                    barrier['health'] -= 1
                    if barrier['health'] <= 0:
                        self.barriers.remove(barrier)
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break
        
        # Check for level completion
        alive_enemies = [enemy for enemy in self.enemies if enemy['alive']]
        if not alive_enemies:
            self.level_complete()
            return
            
        # Check if enemies reached the bottom
        for enemy in self.enemies:
            if enemy['alive'] and enemy['y'] >= 250:
                self.game_over()
                return
                
        self.draw_game()
        self.frame.after(16, self.game_loop)
        
    def level_complete(self):
        """Advance to the next level"""
        self.level += 1
        self.enemy_move_delay = max(10, self.enemy_move_delay - 2)  # Speed up enemies
        
        # Show level complete message
        self.canvas.create_rectangle(100, 120, 300, 180, fill='black', outline='green')
        self.canvas.create_text(200, 140, text=f"LEVEL {self.level-1} COMPLETE!", 
                              fill='green', font=('Arial', 12, 'bold'))
        self.canvas.create_text(200, 160, text="Press SPACE to continue", 
                              fill='white', font=('Arial', 10))
                              
        # Pause game loop until spacebar is pressed
        self.game_running = False
        
        # Setup to restart when space is pressed
        def continue_handler(event):
            if event.keysym.lower() == 'space':
                self.canvas.unbind('<KeyPress>', continue_id)
                self.start_game()
                
        continue_id = self.canvas.bind('<KeyPress>', continue_handler)
        
    def game_over(self):
        self.game_running = False
        messagebox.showinfo("Game Over", f"Final Score: {self.score}")
        self.reset_game()
        
    def draw_game(self):
        """Draw the game state"""
        if not self.canvas:
            return
        self.canvas.delete("all")
        
        # Draw black background with stars
        import random
        random.seed(42)  # Fixed seed for consistent stars
        for _ in range(30):
            x = random.randint(0, 400)
            y = random.randint(0, 300)
            self.canvas.create_rectangle(x, y, x+1, y+1, fill="white", outline="")
        
        # Draw player ship
        self.canvas.create_rectangle(self.player_x - 15, 280, 
                                   self.player_x + 15, 290,
                                   fill="green", outline="white")
        self.canvas.create_rectangle(self.player_x - 5, 275, 
                                   self.player_x + 5, 280,
                                   fill="green", outline="white")
        
        # Draw barriers
        for barrier in self.barriers:
            color = "#00FF00"  # Green
            if barrier['health'] == 2:
                color = "#CCFF00"  # Yellow-green
            elif barrier['health'] == 1:
                color = "#FFCC00"  # Orange
            
            self.canvas.create_rectangle(barrier['x'] - 3, barrier['y'] - 3,
                                       barrier['x'] + 3, barrier['y'] + 3,
                                       fill=color, outline="")
        
        # Draw bullets
        for bullet in self.bullets:
            if bullet['type'] == 'player':
                self.canvas.create_rectangle(bullet['x'] - 1, bullet['y'] - 4,
                                          bullet['x'] + 1, bullet['y'] + 4,
                                          fill="cyan", outline="")
            else:
                self.canvas.create_rectangle(bullet['x'] - 1, bullet['y'] - 4,
                                          bullet['x'] + 1, bullet['y'] + 4,
                                          fill="red", outline="")
        
        # Draw enemies
        enemy_colors = ["#FF0000", "#FF9900", "#FFEE00"]
        enemy_shapes = [
            lambda x, y: self.canvas.create_polygon(
                x-10, y, x-10, y-8, x-5, y-8, x-5, y-3, x+5, y-3, x+5, y-8, 
                x+10, y-8, x+10, y, fill=enemy_colors[0], outline="white"),
            lambda x, y: self.canvas.create_oval(
                x-10, y-10, x+10, y+5, fill=enemy_colors[1], outline="white"),
            lambda x, y: self.canvas.create_rectangle(
                x-8, y-8, x+8, y+3, fill=enemy_colors[2], outline="white")
        ]
        
        for enemy in self.enemies:
            if enemy['alive']:
                enemy_shapes[enemy['type']](enemy['x'], enemy['y'])
        
        # Draw UI elements
        self.canvas.create_text(50, 20, text=f"Level: {self.level}",                               fill="white", font=('Arial', 12, 'bold'))
        
        # If game is not running, show start message
        if not self.game_running and len([e for e in self.enemies if e.get('alive', False)]) == 0:
            self.canvas.create_text(200, 150, text="Press SPACE or ENTER to Start", 
                                  fill="white", font=('Arial', 14, 'bold'))


class FlappyBirdApp(EmbeddedApplication):
    """Flappy Bird style game with increasing difficulty"""
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.canvas = None
        self.bird_y = 150
        self.bird_velocity = 0
        self.pipes = []
        self.score = 0
        self.game_running = False
        self.level = 1
        self.gravity = 0.6
        self.jump_strength = -8
        self.pipe_speed = 3
        self.pipe_gap = 150  # Gap between top and bottom pipes
        self.pipe_frequency = 120  # Frames between new pipes
        self.frame_count = 0
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill='x', pady=(0, 10))
        
        title = ttk.Label(title_frame, text="🐦 Flappy Bird", 
                         font=('Arial', 16, 'bold'))
        title.pack(side='left')
        
        self.score_var = tk.StringVar()
        self.score_var.set("Score: 0")
        score_label = ttk.Label(title_frame, textvariable=self.score_var,
                               font=('Arial', 12))
        score_label.pack(side='right')
        
        self.level_var = tk.StringVar()
        self.level_var.set("Level: 1")
        level_label = ttk.Label(title_frame, textvariable=self.level_var,
                               font=('Arial', 12))
        level_label.pack(side='right', padx=(0, 15))
        
        self.canvas = tk.Canvas(self.frame, width=400, height=300, 
                               bg='#87CEEB', highlightthickness=2)  # Sky blue background
        self.canvas.pack(pady=(0, 10))
        
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x')
        
        reset_btn = ttk.Button(control_frame, text="Reset",
                              command=self.reset_game)
        reset_btn.pack(side='left')
        
        instructions = ttk.Label(self.frame, 
                                text="Press SPACE or ENTER to start | SPACE to flap | Avoid pipes")
        instructions.pack(pady=(10, 0))
        
        # Set up key bindings
        self.canvas.configure(takefocus=True)
        self.canvas.bind("<KeyPress>", self.key_press)
        self.canvas.bind("<Button-1>", lambda e: self.canvas.focus_set())
        
        self.draw_game()
        return self.frame
        
    def key_press(self, event):
        key = event.keysym.lower()
        
        # Start game with Space or Enter when not running
        if not self.game_running and key in ['space', 'return']:
            self.start_game()
            return
            
        # Flap the bird with space when game is running
        if self.game_running and key == 'space':
            self.bird_velocity = self.jump_strength
            
    def start_game(self):
        if self.game_running:
            return
            
        self.game_running = True
        self.bird_y = 150
        self.bird_velocity = 0
        self.pipes = []
        self.score = 0
        self.frame_count = 0
        self.level = 1
        self.pipe_speed = 3
        self.score_var.set(f"Score: {self.score}")
        self.level_var.set(f"Level: {self.level}")
        self.canvas.focus_set()
        self.game_loop()
        
    def reset_game(self):
        self.game_running = False
        self.bird_y = 150
        self.bird_velocity = 0
        self.pipes = []
        self.score = 0
        self.frame_count = 0
        self.level = 1
        self.pipe_speed = 3
        self.score_var.set(f"Score: {self.score}")
        self.level_var.set(f"Level: {self.level}")
        self.draw_game()
        
    def game_loop(self):
        if not self.game_running:
            return
            
        # Update bird position
        self.bird_velocity += self.gravity
        self.bird_y += self.bird_velocity
        
        # Boundary check
        if self.bird_y < 0:
            self.bird_y = 0
            self.bird_velocity = 0
        elif self.bird_y > 300:
            self.game_over()
            return
            
        # Update frame counter
        self.frame_count += 1
        
        # Generate new pipes
        if self.frame_count % self.pipe_frequency == 0:
            self.generate_pipe()
            
        # Move pipes
        self.move_pipes()
        
        # Check collisions
        if self.check_collisions():
            self.game_over()
            return
            
        # Update score
        for pipe in self.pipes:
            if not pipe['counted'] and pipe['x'] < 80:  # Bird's x position
                pipe['counted'] = True
                self.score += 1
                self.score_var.set(f"Score: {self.score}")
                
                # Level up after every 10 points
                if self.score > 0 and self.score % 10 == 0:
                    self.level_up()
            
        # Clean up off-screen pipes
        self.pipes = [p for p in self.pipes if p['x'] > -60]  # Pipe width is 60
                
        # Draw the current state
        self.draw_game()
        
        # Continue the game loop
        self.frame.after(16, self.game_loop)  # ~60 FPS
        
    def level_up(self):
        """Increase difficulty for next level"""
        self.level += 1
        self.level_var.set(f"Level: {self.level}")
        self.pipe_speed = min(8, 3 + self.level / 2)  # Increase speed up to a maximum
        self.pipe_gap = max(100, 150 - self.level * 5)  # Decrease gap with each level, minimum 100
        self.pipe_frequency = max(60, 120 - self.level * 10)  # Pipes appear more frequently
        
        # Show level up message
        self.canvas.create_rectangle(100, 120, 300, 180, fill='#000000', outline='green')
        self.canvas.create_text(200, 140, text=f"LEVEL {self.level}!", 
                              fill='green', font=('Arial', 16, 'bold'))
        self.canvas.create_text(200, 160, text="Difficulty increased!", 
                              fill='white', font=('Arial', 10))
        self.canvas.update()
        self.frame.after(1000)  # Pause briefly to show the message
        
    def generate_pipe(self):
        """Generate a new pipe with random height"""
        import random
        gap_start = random.randint(50, 200)  # Random position for the gap
        
        # Top pipe
        top_pipe = {
            'x': 400,
            'y': 0,
            'width': 60,
            'height': gap_start,
            'counted': False
        }
        
        # Bottom pipe
        bottom_pipe = {
            'x': 400,
            'y': gap_start + self.pipe_gap,
            'width': 60,
            'height': 300 - (gap_start + self.pipe_gap),
            'counted': False
        }
        
        self.pipes.append(top_pipe)
        self.pipes.append(bottom_pipe)
        
    def move_pipes(self):
        """Move all pipes to the left"""
        for pipe in self.pipes:
            pipe['x'] -= self.pipe_speed
            
    def check_collisions(self):
        """Check if the bird collides with any pipe"""
        bird_x = 80  # Fixed bird x-position
        bird_radius = 15  # Bird is represented as a circle
        
        for pipe in self.pipes:
            # Check if bird's bounding box overlaps with pipe's bounding box
            if (bird_x + bird_radius > pipe['x'] and 
                bird_x - bird_radius < pipe['x'] + pipe['width'] and
                (self.bird_y - bird_radius < pipe['y'] + pipe['height'] and 
                 self.bird_y + bird_radius > pipe['y'])):
                return True
        return False
        
    def draw_game(self):
        """Draw the game state"""
        if not self.canvas:
            return
            
        self.canvas.delete("all")
        
        # Draw background
        self.canvas.create_rectangle(0, 0, 400, 300, fill='#87CEEB', outline='')  # Sky
        self.canvas.create_rectangle(0, 280, 400, 300, fill='#8B4513', outline='')  # Ground
        
        # Draw pipes
        for pipe in self.pipes:
            # Pipes are green with a highlight
            self.canvas.create_rectangle(pipe['x'], pipe['y'], 
                                       pipe['x'] + pipe['width'], pipe['y'] + pipe['height'],
                                       fill='#32CD32', outline='#228B22')
                                       
        # Draw bird
        # Change bird color based on velocity to give feedback
        bird_color = '#FFD700'  # Default yellow
        if self.bird_velocity < 0:
            bird_color = '#FF8C00'  # Orange when going up
        elif self.bird_velocity > 5:
            bird_color = '#DC143C'  # Crimson when falling fast
            
        # Draw bird as a circle
        self.canvas.create_oval(65, self.bird_y - 15, 95, self.bird_y + 15,
                              fill=bird_color, outline='black')
                              
        # Draw beak
        self.canvas.create_polygon(95, self.bird_y, 105, self.bird_y - 5, 
                                 105, self.bird_y + 5, fill='#FF8C00')
                                 
        # Draw eye
        self.canvas.create_oval(85, self.bird_y - 8, 93, self.bird_y - 2,
                              fill='white', outline='black')
        self.canvas.create_oval(89, self.bird_y - 6, 91, self.bird_y - 4,
                              fill='black', outline='')
        
        # If game is not running, show start message
        if not self.game_running:
            self.canvas.create_rectangle(50, 100, 350, 180, fill='#000000', outline='#4682B4', width=2)
            self.canvas.create_text(200, 130, text="Flappy Bird", 
                                  fill='#FFD700', font=('Arial', 20, 'bold'))
            self.canvas.create_text(200, 160, text="Press SPACE or ENTER to Start", 
                                  fill='white', font=('Arial', 12))
        
    def game_over(self):
        """Handle game over"""
        self.game_running = False
        self.canvas.create_rectangle(100, 100, 300, 200, fill='#000000', outline='#DC143C', width=3)
        self.canvas.create_text(200, 135, text="Game Over!", 
                              fill='#DC143C', font=('Arial', 18, 'bold'))
        self.canvas.create_text(200, 165, text=f"Score: {self.score}", 
                              fill='white', font=('Arial', 14))
        messagebox.showinfo("Game Over", f"Final Score: {self.score}\nReached Level: {self.level}")


class TodoApp(EmbeddedApplication):
    """Todo Manager Application"""
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.tasks = []
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        # Title
        title = ttk.Label(self.frame, text="Sona Todo Manager", 
                         font=('Arial', 14, 'bold'))
        title.pack(pady=(0, 10))
        
        # Add task section
        add_frame = ttk.Frame(self.frame)
        add_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(add_frame, text="New Task:").pack(side='left')
        self.task_entry = ttk.Entry(add_frame, width=30)
        self.task_entry.pack(side='left', padx=(5, 5), fill='x', expand=True)
        
        add_btn = ttk.Button(add_frame, text="Add", command=self.add_task)
        add_btn.pack(side='right')
        
        # Task list
        list_frame = ttk.Frame(self.frame)
        list_frame.pack(fill='both', expand=True)
        
        # Treeview for tasks
        columns = ('Task', 'Status', 'Priority')
        self.task_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.task_tree.heading(col, text=col)
            self.task_tree.column(col, width=100)
            
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        self.task_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Task controls
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(control_frame, text="Mark Complete", 
                  command=self.mark_complete).pack(side='left', padx=(0, 5))
        ttk.Button(control_frame, text="Delete Task", 
                  command=self.delete_task).pack(side='left', padx=(0, 5))
        ttk.Button(control_frame, text="Clear All", 
                  command=self.clear_all).pack(side='left')
        
        # Bind enter key to add task
        self.task_entry.bind('<Return>', lambda e: self.add_task())
        
        return self.frame
        
    def add_task(self):
        task_text = self.task_entry.get().strip()
        if task_text:
            task_id = len(self.tasks)
            self.tasks.append({
                'id': task_id,
                'text': task_text,
                'completed': False,
                'priority': 'Normal'
            })
            
            self.task_tree.insert('', 'end', values=(
                task_text, 'Pending', 'Normal'
            ))            
            self.task_entry.delete(0, tk.END)
            
    def mark_complete(self):
        selection = self.task_tree.selection()
        if selection:
            item = selection[0]
            values = list(self.task_tree.item(item, 'values'))
            values[1] = 'Completed' if values[1] == 'Pending' else 'Pending'
            self.task_tree.item(item, values=values)
            
    def delete_task(self):
        selection = self.task_tree.selection()
        if selection:
            self.task_tree.delete(selection[0])
            
    def clear_all(self):
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        self.tasks.clear()


class NotesManagerApp(EmbeddedApplication):
    """Professional Notes Manager Application"""
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.notes = []
        self.current_note = None
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        # Title
        title = tk.Label(self.frame, text="📝 Sona Notes Manager",
                        font=('Segoe UI', 14, 'bold'),
                        fg=self.parent.colors['text_primary'],
                        bg=self.parent.colors['bg_secondary'])
        title.pack(fill='x', pady=(0, 15))
        
        # Simple note input
        self.note_entry = tk.Text(self.frame, height=10,
                                 font=('Segoe UI', 11),
                                 bg=self.parent.colors['bg_tertiary'],
                                 fg=self.parent.colors['text_primary'],
                                 insertbackground=self.parent.colors['text_accent'])
        self.note_entry.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Buttons
        btn_frame = tk.Frame(self.frame, bg=self.parent.colors['bg_secondary'])
        btn_frame.pack(fill='x')
        
        save_btn = tk.Button(btn_frame, text="💾 Save Note",
                            font=('Segoe UI', 10),
                            bg=self.parent.colors['success'],
                            fg=self.parent.colors['text_primary'],
                            borderwidth=0, relief='flat',
                            command=self.save_note)
        save_btn.pack(side='left', padx=(0, 10))
        
        clear_btn = tk.Button(btn_frame, text="🗑 Clear",
                             font=('Segoe UI', 10),
                             bg=self.parent.colors['error'],
                             fg=self.parent.colors['text_primary'],
                             borderwidth=0, relief='flat',
                             command=self.clear_note)
        clear_btn.pack(side='left')
        
        return self.frame
        
    def save_note(self):
        content = self.note_entry.get(1.0, tk.END)
        if content.strip():
            note = {
                'id': len(self.notes),
                'content': content,
                'created': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            self.notes.append(note)
            messagebox.showinfo("Saved", f"Note saved! Total notes: {len(self.notes)}")
        
    def clear_note(self):
        self.note_entry.delete(1.0, tk.END)


class CalendarApp(EmbeddedApplication):
    """Professional Calendar Application"""
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.events = []
        self.current_date = datetime.now()
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
          # Title
        title = tk.Label(self.frame, text="📅 Sona Calendar",
                         font=('Segoe UI', 14, 'bold'),
                         fg=self.parent.colors['text_primary'],
                         bg=self.parent.colors['bg_secondary'])
        title.pack(fill='x', pady=(0, 15))
        
        # Month navigation
        nav_frame = tk.Frame(self.frame, bg=self.parent.colors['bg_secondary'])
        nav_frame.pack(fill='x', pady=(0, 10))        
        prev_btn = tk.Button(nav_frame, text="◀",
                             font=('Segoe UI', 12),
                             bg=self.parent.colors['accent_primary'],
                             fg=self.parent.colors['text_primary'],
                             borderwidth=0, relief='flat',
                             command=self.prev_month, width=3)
        prev_btn.pack(side='left')
        
        self.month_label = tk.Label(nav_frame,
                                   text=self.current_date.strftime('%B %Y'),
                                   font=('Segoe UI', 12, 'bold'),
                                   fg=self.parent.colors['text_primary'],
                                   bg=self.parent.colors['bg_secondary'])
        self.month_label.pack(side='left', expand=True)
        
        next_btn = tk.Button(nav_frame, text="▶",
                            font=('Segoe UI', 12),
                            bg=self.parent.colors['accent_primary'],
                            fg=self.parent.colors['text_primary'],
                            borderwidth=0, relief='flat',
                            command=self.next_month, width=3)
        next_btn.pack(side='right')
        
        # Calendar grid
        self.calendar_frame = tk.Frame(self.frame, bg=self.parent.colors['bg_secondary'])
        self.calendar_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Event input
        event_frame = tk.Frame(self.frame, bg=self.parent.colors['bg_secondary'])
        event_frame.pack(fill='x')
        
        tk.Label(event_frame, text="📝 Add Event:",
                font=('Segoe UI', 10),
                fg=self.parent.colors['text_primary'],
                bg=self.parent.colors['bg_secondary']).pack(side='left')
        
        self.event_entry = tk.Entry(event_frame,
                                   font=('Segoe UI', 10),
                                   bg=self.parent.colors['bg_tertiary'],
                                   fg=self.parent.colors['text_primary'],
                                   insertbackground=self.parent.colors['text_accent'])
        self.event_entry.pack(side='left', padx=(5, 5), fill='x', expand=True)
        
        add_event_btn = tk.Button(event_frame, text="Add",
                                 font=('Segoe UI', 10),
                                 bg=self.parent.colors['success'],
                                 fg=self.parent.colors['text_primary'],
                                 borderwidth=0, relief='flat',
                                 command=self.add_event)
        add_event_btn.pack(side='right')
        
        self.draw_calendar()
        return self.frame
        
    def prev_month(self):
        self.current_date = self.current_date.replace(day=1)
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(month=12, year=self.current_date.year-1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month-1)
        self.update_calendar()
        
    def next_month(self):
        self.current_date = self.current_date.replace(day=1)
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(month=1, year=self.current_date.year+1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month+1)
        self.update_calendar()
        
    def update_calendar(self):
        self.month_label.config(text=self.current_date.strftime('%B %Y'))
        self.draw_calendar()
        
    def draw_calendar(self):
        # Clear existing calendar
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
            
        # Day headers
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i, day in enumerate(days):
            label = tk.Label(self.calendar_frame, text=day,
                           font=('Segoe UI', 10, 'bold'),
                           fg=self.parent.colors['text_accent'],
                           bg=self.parent.colors['bg_tertiary'],
                           width=8, height=2)
            label.grid(row=0, column=i, padx=1, pady=1, sticky='ew')
            
        # Calendar days
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        
        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day == 0:
                    continue
                    
                day_frame = tk.Frame(self.calendar_frame,
                                   bg=self.parent.colors['bg_tertiary'],
                                   relief='raised', borderwidth=1)
                day_frame.grid(row=week_num+1, column=day_num, padx=1, pady=1, sticky='ew')
                
                day_label = tk.Label(day_frame, text=str(day),
                                   font=('Segoe UI', 10),
                                   fg=self.parent.colors['text_primary'],
                                   bg=self.parent.colors['bg_tertiary'])
                day_label.pack()
                
        # Configure grid weights
        for i in range(7):
            self.calendar_frame.columnconfigure(i, weight=1)
            
    def add_event(self):
        event_text = self.event_entry.get().strip()
        if event_text:
            event = {
                'date': self.current_date,
                'text': event_text,
                'created': datetime.now()
            }
            self.events.append(event)
            self.event_entry.delete(0, tk.END)
            messagebox.showinfo("Event Added", f"Event '{event_text}' added for {self.current_date.strftime('%B %Y')}")


class FileOrganizerApp(EmbeddedApplication):
    """Professional File Organizer Application"""
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.current_path = Path.home()
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        # Title
        title = tk.Label(self.frame, text="📁 Sona File Organizer",
                        font=('Segoe UI', 14, 'bold'),
                        fg=self.parent.colors['text_primary'],
                        bg=self.parent.colors['bg_secondary'])
        title.pack(fill='x', pady=(0, 15))
        
        # Path navigation
        nav_frame = tk.Frame(self.frame, bg=self.parent.colors['bg_secondary'])
        nav_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(nav_frame, text="📂 Current Path:",
                font=('Segoe UI', 10),
                fg=self.parent.colors['text_primary'],
                bg=self.parent.colors['bg_secondary']).pack(side='left')
        
        self.path_label = tk.Label(nav_frame,
                                  text=str(self.current_path),
                                  font=('Segoe UI', 10),
                                  fg=self.parent.colors['text_accent'],
                                  bg=self.parent.colors['bg_secondary'])
        self.path_label.pack(side='left', padx=(5, 10))
        
        browse_btn = tk.Button(nav_frame, text="Browse",
                              font=('Segoe UI', 10),
                              bg=self.parent.colors['accent_primary'],
                              fg=self.parent.colors['text_primary'],
                              borderwidth=0, relief='flat',
                              command=self.browse_folder)
        browse_btn.pack(side='right')
        
        # File list
        list_frame = tk.Frame(self.frame, bg=self.parent.colors['bg_secondary'])
        list_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Treeview for files
        columns = ('Name', 'Type', 'Size', 'Modified')
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.file_tree.heading(col, text=col)
            self.file_tree.column(col, width=100)
            
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Organization controls
        control_frame = tk.Frame(self.frame, bg=self.parent.colors['bg_secondary'])
        control_frame.pack(fill='x')
        
        organize_btn = tk.Button(control_frame, text="🗂 Organize by Type",
                               font=('Segoe UI', 10),
                               bg=self.parent.colors['success'],
                               fg=self.parent.colors['text_primary'],
                               borderwidth=0, relief='flat',
                               command=self.organize_by_type)
        organize_btn.pack(side='left', padx=(0, 10))
        
        clean_btn = tk.Button(control_frame, text="🧹 Clean Empty Folders",
                             font=('Segoe UI', 10),
                             bg=self.parent.colors['warning'],
                             fg=self.parent.colors['text_primary'],
                             borderwidth=0, relief='flat',
                             command=self.clean_empty_folders)
        clean_btn.pack(side='left')
        
        self.refresh_files()
        return self.frame
        
    def browse_folder(self):
        """Browse and select a folder"""
        folder = filedialog.askdirectory(initialdir=str(self.current_path))
        if folder:
            self.current_path = Path(folder)
            self.refresh_files()
    
    def refresh_files(self):
        """Refresh the file list"""
        try:
            for item in self.file_tree.get_children():
                self.file_tree.delete(item)
                
            for item in self.current_path.iterdir():
                if item.is_file():
                    size = f"{item.stat().st_size / 1024:.1f} KB"
                    modified = datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                    self.file_tree.insert('', 'end', values=(
                        item.name, item.suffix or 'File', size, modified
                    ))
                elif item.is_dir():
                    self.file_tree.insert('', 'end', values=(
                        f"📁 {item.name}", 'Folder', '-', '-'
                    ))
        except PermissionError:
            messagebox.showerror("Error", "Permission denied to access this folder")
            
    def organize_by_type(self):
        try:
            file_types = {}
            for item in self.current_path.iterdir():
                if item.is_file() and item.suffix:
                    ext = item.suffix.lower()
                    if ext not in file_types:
                        file_types[ext] = []
                    file_types[ext].append(item)
                    
            if file_types:
                messagebox.showinfo("Organization", f"Found {len(file_types)} file types to organize.\n"
                                   f"This is a demonstration - actual organization not performed.")
            else:
                messagebox.showinfo("No Files", "No files with extensions found to organize.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze files: {e}")
            
    def clean_empty_folders(self):
        messagebox.showinfo("Clean Folders", "This is a demonstration feature.\n"
                           "In a real implementation, this would remove empty folders.")


class MediaPlayerApp(EmbeddedApplication):
    """Professional Media Player Application"""
    
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.playlist = []
        self.playlist_paths = []  # Store the actual file paths
        self.current_track = 0
        self.is_playing = False
        self.position = 0
        self.player = None
        
        # Initialize pygame mixer for audio playback
        try:
            import importlib.util
            if importlib.util.find_spec("pygame") is not None:
                import pygame
                pygame.mixer.init()
                self.has_player = True
            else:
                print("pygame not available, running in demo mode")
                self.has_player = False
        except (ImportError, ModuleNotFoundError):
            print("Error initializing audio player, running in demo mode")
            self.has_player = False
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        # Title
        title = tk.Label(self.frame, text="🎵 Sona Media Player",
                        font=('Segoe UI', 14, 'bold'),
                        fg=self.parent.colors['text_primary'],
                        bg=self.parent.colors['bg_secondary'])
        title.pack(fill='x', pady=(0, 15))
        
        # Current track display
        track_frame = tk.Frame(self.frame, bg=self.parent.colors['bg_tertiary'],
                              relief='sunken', borderwidth=2)
        track_frame.pack(fill='x', pady=(0, 15))
        
        self.track_label = tk.Label(track_frame,
                                   text="No track selected",
                                   font=('Segoe UI', 12, 'bold'),
                                   fg=self.parent.colors['text_primary'],
                                   bg=self.parent.colors['bg_tertiary'])
        self.track_label.pack(pady=10)
        
        self.time_label = tk.Label(track_frame,
                                  text="00:00 / 00:00",
                                  font=('Segoe UI', 10),
                                  fg=self.parent.colors['text_secondary'],
                                  bg=self.parent.colors['bg_tertiary'])
        self.time_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(track_frame,
                                           variable=self.progress_var,
                                           maximum=100)
        self.progress_bar.pack(fill='x', padx=20, pady=(0, 10))
        
        # Control buttons
        control_frame = tk.Frame(self.frame, bg=self.parent.colors['bg_secondary'])
        control_frame.pack(fill='x', pady=(0, 15))
        
        # Create control buttons with modern styling
        btn_style = {
            'font': ('Segoe UI', 12),
            'bg': self.parent.colors['accent_primary'],
            'fg': self.parent.colors['text_primary'],
            'borderwidth': 0,
            'relief': 'flat',
            'width': 4
        }
        
        prev_btn = tk.Button(control_frame, text="⏮", command=self.prev_track, **btn_style)
        prev_btn.pack(side='left', padx=5)
        
        self.play_btn = tk.Button(control_frame, text="▶", command=self.toggle_play, **btn_style)
        self.play_btn.pack(side='left', padx=5)
        
        stop_btn = tk.Button(control_frame, text="⏹", command=self.stop, **btn_style)
        stop_btn.pack(side='left', padx=5)
        
        next_btn = tk.Button(control_frame, text="⏭", command=self.next_track, **btn_style)
        next_btn.pack(side='left', padx=5)
        
        # Volume control
        volume_frame = tk.Frame(control_frame, bg=self.parent.colors['bg_secondary'])
        volume_frame.pack(side='right', padx=20)
        
        tk.Label(volume_frame, text="🔊",
                font=('Segoe UI', 12),
                fg=self.parent.colors['text_primary'],
                bg=self.parent.colors['bg_secondary']).pack(side='left')
        
        self.volume_var = tk.DoubleVar(value=70)
        volume_scale = ttk.Scale(volume_frame,
                               from_=0, to=100,
                               variable=self.volume_var,
                               orient='horizontal',
                               length=100)
        volume_scale.pack(side='left', padx=(5, 0))
        
        # Playlist
        playlist_frame = tk.Frame(self.frame, bg=self.parent.colors['bg_secondary'])
        playlist_frame.pack(fill='both', expand=True)
        
        tk.Label(playlist_frame, text="📋 Playlist",
                font=('Segoe UI', 12, 'bold'),
                fg=self.parent.colors['text_primary'],
                bg=self.parent.colors['bg_secondary']).pack(anchor='w', pady=(0, 5))
        
        # Playlist listbox
        self.playlist_listbox = tk.Listbox(playlist_frame,
                                          font=('Segoe UI', 10),
                                          bg=self.parent.colors['bg_tertiary'],
                                          fg=self.parent.colors['text_primary'],
                                          selectbackground=self.parent.colors['accent_primary'])
        self.playlist_listbox.pack(fill='both', expand=True, pady=(0, 10))
        
        # Bind double-click to play selected track
        self.playlist_listbox.bind('<Double-Button-1>', self.on_playlist_double_click)
        
        # Playlist controls
        playlist_controls = tk.Frame(playlist_frame, bg=self.parent.colors['bg_secondary'])
        playlist_controls.pack(fill='x')
        
        add_btn = tk.Button(playlist_controls, text="➕ Add Files",
                           font=('Segoe UI',  10),
                           bg=self.parent.colors['success'],
                           fg=self.parent.colors['text_primary'],
                           borderwidth=0, relief='flat',
                           command=self.add_files)
        add_btn.pack(side='left', padx=(0, 10))
        
        clear_btn = tk.Button(playlist_controls, text="🗑 Clear",
                             font=('Segoe UI', 10),
                             bg=self.parent.colors['error'],
                             fg=self.parent.colors['text_primary'],
                             borderwidth=0, relief='flat',
                             command=self.clear_playlist)
        clear_btn.pack(side='left')
        
        # Add some demo tracks
        self.add_demo_tracks()
        
        return self.frame
        
    def add_demo_tracks(self):
        demo_tracks = [
            "🎵 Demo Track 1 - Ambient Sounds",
            "🎵 Demo Track 2 - Classical Piece",
            "🎵 Demo Track 3 - Electronic Beat",
            "🎵 Demo Track 4 - Jazz Melody"
        ]        
        # For demo tracks, we'll use placeholders as we don't have actual files
        demo_paths = [
            "demo_track1.mp3",
            "demo_track2.mp3",
            "demo_track3.mp3",
            "demo_track4.mp3"
        ]
        
        for i, track in enumerate(demo_tracks):
            self.playlist.append(track)
            # Store placeholder paths - in a real app these would be actual file paths
            if i < len(demo_paths):
                self.playlist_paths.append(demo_paths[i])
            self.playlist_listbox.insert(tk.END, track)
            
    def toggle_play(self):
        self.is_playing = not self.is_playing
        
        if self.is_playing:
            self.play_btn.config(text="⏸")
            if self.playlist:
                current_track = self.playlist[self.current_track]
                self.track_label.config(text=current_track)
                
                if self.has_player and len(self.playlist_paths) > self.current_track:
                    try:
                        import pygame
                        # Stop any currently playing music
                        if pygame.mixer.music.get_busy():
                            pygame.mixer.music.stop()
                            
                        # Load and play the selected track
                        audio_file = self.playlist_paths[self.current_track]
                        pygame.mixer.music.load(audio_file)
                        pygame.mixer.music.play()
                        
                        # Set volume from slider
                        volume = self.volume_var.get() / 100.0
                        pygame.mixer.music.set_volume(volume)
                        
                        # Start progress tracking
                        self.update_progress()
                    except Exception as e:
                        print(f"Could not play audio: {e}")
                        self.time_label.config(text="Error playing audio")
                else:
                    # Fallback to demo mode if pygame not available                    self.time_label.config(text="Demo: 01:30 / 03:45")
                    self.progress_var.set(25)  # Demo progress
        else:
            self.play_btn.config(text="▶")
            # Stop playback
            if self.has_player:
                try:
                    import pygame
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.pause()
                except Exception:
                    pass
                    
    def stop(self):
        self.is_playing = False
        self.play_btn.config(text="▶")
        self.progress_var.set(0)
        self.time_label.config(text="00:00 / 00:00")
        
    def prev_track(self):
        if self.playlist and self.current_track > 0:
            self.current_track -= 1
            self.update_track_display()
            
    def next_track(self):
        if self.playlist and self.current_track < len(self.playlist) - 1:
            self.current_track += 1
            self.update_track_display()
            
    def update_track_display(self):
        if self.playlist:
            current_track = self.playlist[self.current_track]
            self.track_label.config(text=current_track)
            self.playlist_listbox.selection_clear(0, tk.END)
            self.playlist_listbox.selection_set(self.current_track)
            
    def add_files(self):
        from tkinter import filedialog
        files = filedialog.askopenfilenames(
            title="Select Audio Files",
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.m4a"), ("All Files", "*.*")]        )
        
        for file in files:
            filename = Path(file).name
            self.playlist.append(f"🎵 {filename}")
            self.playlist_paths.append(file)  # Store the actual path for playback
            self.playlist_listbox.insert(tk.END, f"🎵 {filename}")
            
    def update_progress(self):
        """Update the progress bar and time display for audio playback"""
        if not self.is_playing:
            return
        
        # Store track length data when available
        track_length_cache = getattr(self, "track_length_cache", {})
        
        # Demo mode or real player mode
        if not self.has_player:
            # Demo mode - simulate progress
            self.position = getattr(self, "position", 0) + 1
            total_length = 180  # 3 minutes in demo mode
            
            # Format time as MM:SS
            minutes = int(self.position // 60)
            seconds = int(self.position % 60)
            time_str = f"{minutes:02d}:{seconds:02d}"
            
            # Calculate progress
            progress_percent = min(100, (self.position / total_length) * 100)
            self.progress_var.set(progress_percent)
            self.time_label.config(text=f"{time_str} / 03:00")
            
            # Auto-advance if at end
            if self.position >= total_length:
                self.position = 0
                self.next_track()
            else:
                self.frame.after(1000, self.update_progress)
        else:
            # Real player mode using pygame
            try:
                import pygame
                if pygame.mixer.music.get_busy():
                    current_file = self.playlist_paths[self.current_track]
                    
                    # Get/cache track length (in real app would use mutagen or similar)
                    if current_file not in track_length_cache:
                        try:
                            # Use a default length if actual length can't be determined
                            track_length_cache[current_file] = 180  # 3 minutes default
                        except:
                            track_length_cache[current_file] = 180
                    
                    total_length = track_length_cache[current_file]
                    current_pos = pygame.mixer.music.get_pos() / 1000  # Convert to seconds
                    
                    # Handle position tracking better (pygame.mixer.music.get_pos() can reset)
                    if current_pos < 0:
                        current_pos = 0
                    
                    # Format times as MM:SS
                    minutes_current = int(current_pos // 60)
                    seconds_current = int(current_pos % 60)
                    
                    minutes_total = int(total_length // 60)
                    seconds_total = int(total_length % 60)
                    
                    time_str = f"{minutes_current:02d}:{seconds_current:02d} / {minutes_total:02d}:{seconds_total:02d}"
                    
                    # Calculate progress
                    progress_percent = min(100, (current_pos / total_length) * 100)
                    self.progress_var.set(progress_percent)
                    self.time_label.config(text=time_str)
                    
                    # Schedule next update
                    self.frame.after(500, self.update_progress)
                else:
                    # Song ended
                    self.next_track()
                    if self.is_playing:
                        self.toggle_play()  # Start playing next track
            except Exception as e:
                print(f"Error updating progress: {e}")
                # Fallback to demo progress display
                self.position = getattr(self, "position", 0) + 1
                progress_percent = min(100, (self.position / 180) * 100)
                self.progress_var.set(progress_percent)
                self.time_label.config(text=f"Demo: {self.position//60:02d}:{self.position%60:02d} / 03:00")
                self.frame.after(1000, self.update_progress)
        
        # Store position for next update
        self.position = getattr(self, "position", 0)        # Store track length cache
        self.track_length_cache = track_length_cache
            
    def clear_playlist(self):
        self.playlist.clear()
        self.playlist_listbox.delete(0, tk.END)
        self.current_track = 0
        self.track_label.config(text="No track selected")
        self.stop()
        
    def on_playlist_double_click(self, event=None):
        """Play the selected track when double-clicked"""
        selection = self.playlist_listbox.curselection()
        if selection:
            self.current_track = selection[0]
            self.update_track_display()
            self.is_playing = False  # Force restart
            self.toggle_play()  # Start playing the selected track


class TextEditorApp(EmbeddedApplication):
    """Professional Text Editor Application"""
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.current_file = None
        self.modified = False
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        # Title with file name
        title_frame = tk.Frame(self.frame, bg=self.parent.colors['bg_secondary'])
        title_frame.pack(fill='x', pady=(0, 10))
        
        self.title_label = tk.Label(title_frame, text="📝 Sona Text Editor",
                                   font=('Segoe UI', 14, 'bold'),
                                   fg=self.parent.colors['text_primary'],
                                   bg=self.parent.colors['bg_secondary'])
        self.title_label.pack(side='left')
        
        self.file_label = tk.Label(title_frame, text="Untitled",
                                  font=('Segoe UI', 12),
                                  fg=self.parent.colors['text_accent'],
                                  bg=self.parent.colors['bg_secondary'])
        self.file_label.pack(side='right')
        
        # Toolbar
        toolbar = tk.Frame(self.frame, bg=self.parent.colors['bg_tertiary'])
        toolbar.pack(fill='x', pady=(0, 10))
        
        # File operations
        new_btn = tk.Button(toolbar, text="📄 New",
                           font=('Segoe UI', 9),
                           bg=self.parent.colors['accent_primary'],
                           fg=self.parent.colors['text_primary'],
                           borderwidth=0, relief='flat',
                           command=self.new_file)
        new_btn.pack(side='left', padx=(5, 2))
        
        open_btn = tk.Button(toolbar, text="📂 Open",
                            font=('Segoe UI', 9),
                            bg=self.parent.colors['accent_primary'],
                            fg=self.parent.colors['text_primary'],
                            borderwidth=0, relief='flat',
                            command=self.open_file)
        open_btn.pack(side='left', padx=2)
        
        save_btn = tk.Button(toolbar, text="💾 Save",
                            font=('Segoe UI', 9),
                            bg=self.parent.colors['success'],
                            fg=self.parent.colors['text_primary'],
                            borderwidth=0, relief='flat',
                            command=self.save_file)
        save_btn.pack(side='left', padx=2)
        
        save_as_btn = tk.Button(toolbar, text="💾 Save As",
                               font=('Segoe UI', 9),
                               bg=self.parent.colors['success'],
                               fg=self.parent.colors['text_primary'],
                               borderwidth=0, relief='flat',
                               command=self.save_as_file)
        save_as_btn.pack(side='left', padx=(2, 10))
        
        # Edit operations
        cut_btn = tk.Button(toolbar, text="✂ Cut",
                           font=('Segoe UI', 9),
                           bg=self.parent.colors['warning'],
                           fg=self.parent.colors['text_primary'],
                           borderwidth=0, relief='flat',
                           command=self.cut_text)
        cut_btn.pack(side='left', padx=2)
        
        copy_btn = tk.Button(toolbar, text="📋 Copy",
                            font=('Segoe UI', 9),
                            bg=self.parent.colors['accent_primary'],
                            fg=self.parent.colors['text_primary'],
                            borderwidth=0, relief='flat',
                            command=self.copy_text)
        copy_btn.pack(side='left', padx=2)
        
        paste_btn = tk.Button(toolbar, text="📌 Paste",
                             font=('Segoe UI', 9),
                             bg=self.parent.colors['accent_primary'],
                             fg=self.parent.colors['text_primary'],
                             borderwidth=0, relief='flat',
                             command=self.paste_text)
        paste_btn.pack(side='left', padx=2)
        
        # Text editor
        editor_frame = tk.Frame(self.frame, bg=self.parent.colors['bg_secondary'])
        editor_frame.pack(fill='both', expand=True)
        
        # Line numbers (simulated)
        line_frame = tk.Frame(editor_frame, bg=self.parent.colors['bg_primary'], width=50)
        line_frame.pack(side='left', fill='y')
        
        self.line_text = tk.Text(line_frame, width=4,
                                font=('Fira Code', 10),
                                bg=self.parent.colors['bg_primary'],
                                fg=self.parent.colors['text_secondary'],
                                state='disabled',
                                borderwidth=0)
        self.line_text.pack(fill='both', expand=True)
        
        # Main text area
        self.text_editor = tk.Text(editor_frame,
                                  font=('Fira Code', 11),
                                  bg=self.parent.colors['bg_secondary'],
                                  fg=self.parent.colors['text_primary'],
                                  insertbackground=self.parent.colors['text_accent'],
                                  selectbackground=self.parent.colors['accent_primary'],
                                  borderwidth=0, relief='flat',
                                  wrap=tk.WORD,
                                  undo=True)
        self.text_editor.pack(side='left', fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(editor_frame, orient='vertical', command=self.text_editor.yview)
        self.text_editor.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        
        # Status bar
        status_frame = tk.Frame(self.frame, bg=self.parent.colors['bg_primary'])
        status_frame.pack(fill='x', pady=(10, 0))
        
        self.status_label = tk.Label(status_frame,
                                    text="Ready | Line 1, Column 1",
                                    font=('Segoe UI', 9),
                                    fg=self.parent.colors['text_secondary'],
                                    bg=self.parent.colors['bg_primary'])
        self.status_label.pack(side='left', padx=5)
        
        self.char_count_label = tk.Label(status_frame,
                                        text="Characters: 0",
                                        font=('Segoe UI', 9),
                                        fg=self.parent.colors['text_secondary'],
                                        bg=self.parent.colors['bg_primary'])
        self.char_count_label.pack(side='right', padx=5)
        
        # Bind events
        self.text_editor.bind('<KeyRelease>', self.on_text_change)
        self.text_editor.bind('<Button-1>', self.on_cursor_move)
        self.text_editor.bind('<KeyPress>', self.on_key_press)
        
        # Initialize with some sample text
        sample_text = """# Welcome to Sona Text Editor

This is a professional text editor embedded in the Sona platform.

Features:
- Syntax highlighting (basic)
- Line numbers
- Cut, Copy, Paste operations
- File operations (New, Open, Save, Save As)
- Character and line counting
- Undo/Redo support

Start typing to see the editor in action!
"""
        self.text_editor.insert(1.0, sample_text)
        self.update_line_numbers()
        
        return self.frame
        
    def new_file(self):
        if self.modified:
            result = messagebox.askyesnocancel("Save Changes", 
                                              "Do you want to save changes to the current file?")
            if result is True:
                self.save_file()
            elif result is None:
                return
                
        self.text_editor.delete(1.0, tk.END)
        self.current_file = None
        self.modified = False
        self.file_label.config(text="Untitled")
        self.update_line_numbers()
        
    def open_file(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[("Text Files", "*.txt"), ("Sona Files", "*.sona"), 
                      ("Python Files", "*.py"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                self.text_editor.delete(1.0, tk.END)
                self.text_editor.insert(1.0, content)
                self.current_file = file_path
                self.modified = False
                self.file_label.config(text=Path(file_path).name)
                self.update_line_numbers()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")
                
    def save_file(self):
        if self.current_file:
            try:
                content = self.text_editor.get(1.0, tk.END + '-1c')
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.modified = False
                messagebox.showinfo("Saved", f"File saved: {Path(self.current_file).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
        else:
            self.save_as_file()
            
    def save_as_file(self):
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("Sona Files", "*.sona"), 
                      ("Python Files", "*.py"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                content = self.text_editor.get(1.0, tk.END + '-1c')
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.current_file = file_path
                self.modified = False
                self.file_label.config(text=Path(file_path).name)
                messagebox.showinfo("Saved", f"File saved: {Path(file_path).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
                
    def cut_text(self):
        try:
            self.text_editor.event_generate("<<Cut>>")
        except:
            pass
            
    def copy_text(self):
        try:
            self.text_editor.event_generate("<<Copy>>")
        except:
            pass
            
    def paste_text(self):
        try:
            self.text_editor.event_generate("<<Paste>>")
        except:
            pass
            
    def on_text_change(self, event=None):
        self.modified = True
        self.update_line_numbers()
        self.update_status()
        
    def on_cursor_move(self, event=None):
        self.update_status()
        
    def on_key_press(self, event=None):
        self.frame.after_idle(self.update_status)
        
    def update_line_numbers(self):
        content = self.text_editor.get(1.0, tk.END)
        lines = content.count('\n')
        
        self.line_text.config(state='normal')
        self.line_text.delete(1.0, tk.END)
        
        line_numbers = '\n'.join(str(i) for i in range(1, lines + 1))
        self.line_text.insert(1.0, line_numbers)
        self.line_text.config(state='disabled')
        
    def update_status(self):
        try:
            cursor_pos = self.text_editor.index(tk.INSERT)
            line, col = cursor_pos.split('.')
            content = self.text_editor.get(1.0, tk.END + '-1c')
            char_count = len(content)
            
            self.status_label.config(text=f"Line {line}, Column {int(col)+1}")
            self.char_count_label.config(text=f"Characters: {char_count}")
        except:            pass


# ===== MISSING GAME CLASSES =====

class Doom2DApp(EmbeddedApplication):
    """Enhanced 2D Doom-style shooter game with improved UI and fluid controls"""
    
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.player_x = 5.0
        self.player_y = 5.0
        self.player_angle = 0.0
        self.fov = 60
        self.view_distance = 10
        
        # Enhanced map with more detail
        self.map_data = [
            [1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,0,0,0,1],
            [1,0,1,0,1,1,1,0,0,1],
            [1,0,1,0,0,0,1,0,0,1],
            [1,0,1,1,0,0,1,0,0,1],
            [1,0,0,0,0,0,0,0,0,1],
            [1,0,1,1,1,1,1,1,0,1],
            [1,0,0,0,0,0,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,1],
            [1,1,1,1,1,1,1,1,1,1]
        ]
        
        self.enemies = [(3.5, 3.5), (7.5, 7.5), (2.5, 8.5)]
        self.bullets = []
        self.score = 0
        self.health = 100
        self.ammo = 30
        self.game_running = False
        self.keys_pressed = set()
        self.last_mouse_x = None
        
        # Enhanced graphics settings
        self.render_quality = "high"  # high, medium, low
        self.show_minimap = True
        self.show_fps = True
        self.fps_counter = 0
        self.fps_timer = 0
        
        # Smooth movement
        self.smooth_movement = True
        self.mouse_sensitivity = 0.5
        
        # Visual effects
        self.muzzle_flash = 0
        self.damage_flash = 0
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="5")
        
        # Enhanced title bar with game info
        title_frame = tk.Frame(self.frame, bg='#1a1a2e', height=60)
        title_frame.pack(fill='x', pady=(0, 5))
        title_frame.pack_propagate(False)
        
        # Game title with gradient effect
        title = tk.Label(title_frame, text="🔫 DOOM 2D ENHANCED", 
                        font=('Arial', 18, 'bold'),
                        fg='#ff6b35', bg='#1a1a2e')
        title.pack(side='left', padx=20, pady=15)
        
        # Real-time stats
        stats_frame = tk.Frame(title_frame, bg='#1a1a2e')
        stats_frame.pack(side='right', padx=20, pady=10)
        
        self.score_var = tk.StringVar(value="SCORE: 0")
        self.health_var = tk.StringVar(value="HEALTH: 100")
        self.ammo_var = tk.StringVar(value="AMMO: 30")
        
        tk.Label(stats_frame, textvariable=self.score_var,
                font=('Arial', 11, 'bold'), fg='#ffd700', bg='#1a1a2e').pack()
        tk.Label(stats_frame, textvariable=self.health_var,
                font=('Arial', 11, 'bold'), fg='#00ff00', bg='#1a1a2e').pack()
        tk.Label(stats_frame, textvariable=self.ammo_var,
                font=('Arial', 11, 'bold'), fg='#00bfff', bg='#1a1a2e').pack()
        
        # Enhanced game canvas with better resolution
        canvas_frame = tk.Frame(self.frame, bg='#000000', relief='sunken', borderwidth=3)
        canvas_frame.pack(pady=(0, 5))
        
        self.canvas = tk.Canvas(canvas_frame, width=700, height=450, bg="black",
                               highlightthickness=0)
        self.canvas.pack(padx=2, pady=2)
        
        # Enhanced control panel
        control_frame = tk.Frame(self.frame, bg='#16213e', height=80)
        control_frame.pack(fill='x')
        control_frame.pack_propagate(False)
        
        # Game controls with modern styling
        btn_frame = tk.Frame(control_frame, bg='#16213e')
        btn_frame.pack(side='left', padx=20, pady=15)
        
        btn_style = {
            'font': ('Arial', 11, 'bold'),
            'borderwidth': 0,
            'relief': 'flat',
            'cursor': 'hand2',
            'width': 12,
            'height': 2
        }
          # Hide start button - use Space/Enter to start
        # self.start_btn = tk.Button(btn_frame, text="🎮 START MISSION",
        #                           bg='#00ff00', fg='#000000',
        #                           command=self.start_game, **btn_style)
        # self.start_btn.pack(side='left', padx=5)
        
        self.pause_btn = tk.Button(btn_frame, text="⏸️ PAUSE",
                                  bg='#ffa500', fg='#000000',
                                  command=self.pause_game, 
                                  state='disabled', **btn_style)
        self.pause_btn.pack(side='left', padx=5)
        
        self.reset_btn = tk.Button(btn_frame, text="🔄 RESET",
                                  bg='#ff4444', fg='#ffffff',
                                  command=self.reset_game, **btn_style)
        self.reset_btn.pack(side='left', padx=5)
        
        # Enhanced settings panel
        settings_frame = tk.Frame(control_frame, bg='#16213e')
        settings_frame.pack(side='right', padx=20, pady=15)
        
        # Quality settings
        tk.Label(settings_frame, text="GRAPHICS:", 
                font=('Arial', 9, 'bold'), fg='#ffffff', bg='#16213e').pack()
        
        quality_frame = tk.Frame(settings_frame, bg='#16213e')
        quality_frame.pack()
        
        self.quality_var = tk.StringVar(value="HIGH")
        for quality in ["LOW", "MEDIUM", "HIGH"]:
            rb = tk.Radiobutton(quality_frame, text=quality, variable=self.quality_var,
                               value=quality, font=('Arial', 8), fg='#ffffff', 
                               bg='#16213e', selectcolor='#533483',
                               command=self.change_quality)
            rb.pack(side='left', padx=2)
          # Enhanced instructions with styling
        instr_frame = tk.Frame(self.frame, bg='#0f3460')
        instr_frame.pack(fill='x', pady=(5, 0))
        
        instructions = "� Press SPACE or ENTER to start | �🎯 WASD: Move & Strafe | 🔄 A/D: Turn | 🔫 SPACE/CLICK: Shoot | 🖱️ Mouse: Look Around"
        tk.Label(instr_frame, text=instructions,
                font=('Arial', 10, 'bold'), fg='#64ffda', bg='#0f3460').pack(pady=8)
        
        # Set up enhanced controls
        self.setup_controls()
        
        # Draw initial enhanced view
        self.draw_3d_view()
        
        return self.frame
        
    def setup_controls(self):
        """Set up enhanced keyboard and mouse controls"""
        # Make canvas focusable with better focus management
        self.canvas.configure(takefocus=True)
        
        # Bind events with enhanced handling
        self.canvas.bind("<KeyPress>", self.handle_keypress)
        self.canvas.bind("<KeyRelease>", self.handle_keyrelease)
        self.canvas.bind("<Button-1>", self.handle_click)
        self.canvas.bind("<Motion>", self.handle_mouse)
        self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())
        
        # Ensure canvas gets focus immediately
        self.canvas.focus_set()
        
        # Bind to frame as well for better focus management
        self.frame.bind("<KeyPress>", self.handle_keypress)
        self.frame.bind("<KeyRelease>", self.handle_keyrelease)
        self.frame.configure(takefocus=True)
        
        # Draw initial enhanced view
        self.draw_3d_view()
        
        return self.frame
        
    def setup_controls(self):
        """Set up keyboard and mouse controls"""
        # Make canvas focusable
        self.canvas.configure(takefocus=True)
        
        # Bind events
        self.canvas.bind("<KeyPress>", self.handle_keypress)
        self.canvas.bind("<KeyRelease>", self.handle_keyrelease)
        self.canvas.bind("<Button-1>", self.handle_click)
        self.canvas.bind("<Motion>", self.handle_mouse)
        
        # Ensure canvas gets focus        self.canvas.focus_set()
        
        # Bind to frame as well for better focus management
        self.frame.bind("<KeyPress>", self.handle_keypress)
        self.frame.bind("<KeyRelease>", self.handle_keyrelease)
        self.frame.configure(takefocus=True)
        
    def start_game(self):
        """Start the game"""
        self.game_running = True
        # No start button to disable - use Space/Enter to start
        self.reset_btn.config(state='normal')
        self.canvas.focus_set()
        self.game_loop()
        
    def pause_game(self):
        """Pause/unpause the game"""
        self.game_running = not self.game_running
        if self.game_running:
            self.pause_btn.config(text="⏸️ PAUSE")
            self.game_loop()
        else:
            self.pause_btn.config(text="▶️ RESUME")
            
    def change_quality(self):
        """Change graphics quality setting"""
        self.render_quality = self.quality_var.get().lower()
        if self.game_running:
            self.draw_3d_view()
        
    def reset_game(self):
        """Reset the game to initial state"""
        self.game_running = False
        self.player_x = 5.0
        self.player_y = 5.0
        self.player_angle = 0.0
        self.enemies = [(3.5, 3.5), (7.5, 7.5), (2.5, 8.5)]
        self.bullets = []
        self.score = 0
        self.keys_pressed.clear()
        self.score_var.set("Score: 0")
        # No start button to re-enable - use Space/Enter to start
        self.reset_btn.config(state='disabled')
        self.draw_3d_view()
        
    def handle_keypress(self, event):
        """Handle key press events"""
        key = event.keysym.lower()
        
        # Start game with Space or Enter when not running
        if not self.game_running and key in ['space', 'return']:
            self.start_game()
            return
            
        if key not in self.keys_pressed:
            self.keys_pressed.add(key)
            
        # Immediate shooting on space when game is running
        if key == 'space' and self.game_running:
            self.shoot()
        
    def handle_keyrelease(self, event):
        """Handle key release events"""
        self.keys_pressed.discard(event.keysym.lower())
        
    def handle_click(self, event):
        """Handle mouse clicks"""
        if self.game_running:
            self.shoot()
        else:
            # Focus canvas when clicked
            self.canvas.focus_set()
    
    def handle_mouse(self, event):
        """Handle mouse movement for looking around"""
        if not self.game_running:
            return
            
        # Simple mouse look - only when button is held or in a smaller sensitivity
        if hasattr(self, 'last_mouse_x') and self.last_mouse_x is not None:
            dx = event.x - self.last_mouse_x
            # Reduced sensitivity
            self.player_angle += dx * 0.1
        self.last_mouse_x = event.x
    
    def is_valid_position(self, x, y):
        """Check if position is walkable"""
        grid_x, grid_y = int(x), int(y)
        if 0 <= grid_x < len(self.map_data[0]) and 0 <= grid_y < len(self.map_data):
            return self.map_data[grid_y][grid_x] == 0
        return False
    
    def shoot(self):
        """Fire a bullet"""
        if len(self.bullets) < 5:  # Limit bullets
            bullet_speed = 0.2
            bullet = {
                'x': self.player_x,
                'y': self.player_y,
                'dx': math.cos(math.radians(self.player_angle)) * bullet_speed,
                'dy': math.sin(math.radians(self.player_angle)) * bullet_speed,
                'life': 50
            }
            self.bullets.append(bullet)
    
    def update_movement(self):
        """Update player movement based on pressed keys"""
        if not self.game_running:
            return
            
        move_speed = 0.05
        turn_speed = 2
        
        # Movement
        if 'w' in self.keys_pressed:
            new_x = self.player_x + math.cos(math.radians(self.player_angle)) * move_speed
            new_y = self.player_y + math.sin(math.radians(self.player_angle)) * move_speed
            if self.is_valid_position(new_x, new_y):
                self.player_x, self.player_y = new_x, new_y
                
        if 's' in self.keys_pressed:
            new_x = self.player_x - math.cos(math.radians(self.player_angle)) * move_speed
            new_y = self.player_y - math.sin(math.radians(self.player_angle)) * move_speed
            if self.is_valid_position(new_x, new_y):
                self.player_x, self.player_y = new_x, new_y
        
        # Turning
        if 'a' in self.keys_pressed:
            self.player_angle -= turn_speed
        if 'd' in self.keys_pressed:
            self.player_angle += turn_speed
            
        # Keep angle in range
        self.player_angle = self.player_angle % 360
    
    def game_loop(self):
        """Main game loop"""
        if not self.game_running:
            return
            
        # Update player movement
        self.update_movement()
            
        # Update bullets
        for bullet in self.bullets[:]:
            bullet['x'] += bullet['dx']
            bullet['y'] += bullet['dy']
            bullet['life'] -= 1
            
            # Check wall collision or life expired
            if not self.is_valid_position(bullet['x'], bullet['y']) or bullet['life'] <= 0:
                self.bullets.remove(bullet)
                continue
                
            # Check enemy collision
            for enemy in self.enemies[:]:
                if abs(bullet['x'] - enemy[0]) < 0.5 and abs(bullet['y'] - enemy[1]) < 0.5:
                    self.enemies.remove(enemy)
                    self.bullets.remove(bullet)
                    self.score += 10
                    self.score_var.set(f"Score: {self.score}")
                    break
        
        # Draw the scene
        self.draw_3d_view()
        
        # Check win condition
        if not self.enemies:
            self.game_over()
            return
            
        # Continue game loop
        self.frame.after(32, self.game_loop)  # ~30 FPS
    
    def draw_3d_view(self):
        """Draw the 3D view using raycasting"""
        self.canvas.delete("all")
        width, height = 600, 400
        
        # Draw floor and ceiling
        self.canvas.create_rectangle(0, height//2, width, height, fill="#2a2a2a", outline="")
        self.canvas.create_rectangle(0, 0, width, height//2, fill="#1a1a1a", outline="")
        
        # Cast rays for walls
        num_rays = width // 2  # Reduced for performance
        for i in range(num_rays):
            ray_angle = self.player_angle - (self.fov // 2) + (i / num_rays) * self.fov
            distance = self.cast_ray(ray_angle)
            
            # Calculate wall height
            if distance > 0:
                wall_height = min(height, (height * 0.5) / distance)
            else:
                wall_height = height
            
            # Calculate color based on distance
            wall_color = max(30, 200 - int(distance * 15))
            color = f"#{wall_color:02x}{wall_color:02x}{wall_color:02x}"
            
            # Draw wall slice
            x = i * 2  # Each ray covers 2 pixels
            wall_top = (height - wall_height) // 2
            wall_bottom = (height + wall_height) // 2
            
            self.canvas.create_line(
                x, wall_top, x, wall_bottom,
                fill=color, width=2
            )
        
        # Draw enemies as sprites
        for enemy in self.enemies:
            self.draw_enemy_sprite(enemy[0], enemy[1])
            
        # Draw crosshair
        center_x, center_y = width // 2, height // 2
        self.canvas.create_line(center_x - 10, center_y, center_x + 10, center_y, 
                               fill="white", width=2)
        self.canvas.create_line(center_x, center_y - 10, center_x, center_y + 10, 
                               fill="white", width=2)
        
        # Draw HUD
        self.draw_hud()
    
    def cast_ray(self, angle):
        """Cast a ray and return distance to wall"""
        angle_rad = math.radians(angle)
        dx = math.cos(angle_rad) * 0.02
        dy = math.sin(angle_rad) * 0.02
        
        x, y = self.player_x, self.player_y
        distance = 0
        
        while distance < self.view_distance:
            x += dx
            y += dy
            distance += 0.02
            
            grid_x, grid_y = int(x), int(y)
            if (0 <= grid_x < len(self.map_data[0]) and 
                0 <= grid_y < len(self.map_data) and
                self.map_data[grid_y][grid_x] == 1):
                return distance
        
        return self.view_distance
    
    def draw_enemy_sprite(self, enemy_x, enemy_y):
        """Draw enemy as a sprite in 3D view"""
        # Calculate relative position
        rel_x = enemy_x - self.player_x
        rel_y = enemy_y - self.player_y
        
        # Rotate relative to player angle
        angle_rad = math.radians(-self.player_angle)
        screen_x = rel_x * math.cos(angle_rad) - rel_y * math.sin(angle_rad)
        screen_y = rel_x * math.sin(angle_rad) + rel_y * math.cos(angle_rad)
        
        # Only draw if in front of player
        if screen_y > 0.1:
            distance = math.sqrt(rel_x*rel_x + rel_y*rel_y)
            
            # Project to screen
            proj_x = 300 + (screen_x / screen_y) * 300
            proj_y = 200
            
            if 0 <= proj_x <= 600:
                # Size based on distance
                size = max(5, 30 / distance)
                
                # Draw enemy
                self.canvas.create_oval(
                    proj_x - size, proj_y - size,
                    proj_x + size, proj_y + size,
                    fill="red", outline="darkred", width=2
                )
    
    def draw_hud(self):
        """Draw heads-up display"""
        # Ammo indicator
        ammo_text = f"Ammo: {5 - len(self.bullets)}/5"
        self.canvas.create_text(50, 30, text=ammo_text, fill="white", 
                               font=('Arial', 10, 'bold'), anchor='w')
        
        # Health (placeholder)
        health_text = "Health: 100"
        self.canvas.create_text(50, 50, text=health_text, fill="green", 
                               font=('Arial', 10, 'bold'), anchor='w')
          # Enemies remaining
        enemies_text = f"Enemies: {len(self.enemies)}"
        self.canvas.create_text(550, 30, text=enemies_text, fill="yellow", 
                               font=('Arial', 10, 'bold'), anchor='e')
    
    def game_over(self):
        """Handle game over"""
        self.game_running = False
        # No start button to re-enable - use Space/Enter to start
        self.reset_btn.config(state='disabled')
        
        # Draw victory message
        self.canvas.create_text(300, 200, text="MISSION COMPLETE!", 
                               fill="green", font=('Arial', 24, 'bold'))
        self.canvas.create_text(300, 230, text=f"Final Score: {self.score}", 
                               fill="white", font=('Arial', 16))
        
        messagebox.showinfo("Victory!", f"All enemies defeated!\nFinal Score: {self.score}")


class BejeweledApp(EmbeddedApplication):
    """Bejeweled match-3 puzzle game"""
    
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.grid_size = 8
        self.cell_size = 50  # Size of each gem cell
        
        # Enhanced gem styles with colors
        self.gems = ['💎', '💍', '🔮', '💜', '🔴', '🔵', '🟡']
        self.gem_colors = {
            '💎': '#00FFFF',  # Cyan
            '💍': '#FFFFFF',  # White
            '🔮': '#800080',  # Purple
            '💜': '#8A2BE2',  # Violet
            '🔴': '#FF0000',  # Red
            '🔵': '#0000FF',  # Blue
            '🟡': '#FFFF00'   # Yellow
        }
        self.board = []
        self.selected = None
        self.score = 0
        self.moves = 0
        self.combo_multiplier = 1
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        # Title and score
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(title_frame, text="💎 Bejeweled", 
                 font=('Arial', 16, 'bold')).pack(side='left')
        
        self.score_var = tk.StringVar()
        self.score_var.set("Score: 0")
        ttk.Label(title_frame, textvariable=self.score_var,
                 font=('Arial', 14, 'bold')).pack(side='right')
        
        # Game board
        self.canvas = tk.Canvas(self.frame, width=400, height=400, bg="black")
        self.canvas.pack(pady=(0, 10))
        self.canvas.bind("<Button-1>", self.on_click)
        
        # Controls
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x')
        
        ttk.Button(control_frame, text="🎮 New Game",
                  command=self.new_game).pack(side='left', padx=(0, 5))
        
        self.moves_var = tk.StringVar()
        self.moves_var.set("Moves: 0")
        ttk.Label(control_frame, textvariable=self.moves_var,
                 font=('Arial', 12)).pack(side='right')
        
        self.new_game()
        return self.frame
        
    def new_game(self):
        self.score = 0
        self.moves = 0
        self.selected = None
        self.score_var.set("Score: 0")
        self.moves_var.set("Moves: 0")
        self.init_board()
        self.draw_board()
        
    def init_board(self):
        self.board = []
        for i in range(self.grid_size):
            row = []
            for j in range(self.grid_size):
                row.append(random.choice(self.gems))
            self.board.append(row)
    
    def on_click(self, event):
        x, y = event.x // 50, event.y // 50
        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            if self.selected is None:
                self.selected = (x, y)
                self.draw_board()
            elif self.selected == (x, y):
                self.selected = None
                self.draw_board()
            else:
                if self.is_adjacent(self.selected, (x, y)):
                    self.swap_gems(self.selected, (x, y))
                    if self.check_matches():
                        self.moves += 1
                        self.moves_var.set(f"Moves: {self.moves}")
                        self.process_matches()
                    else:
                        # Invalid move, swap back
                        self.swap_gems(self.selected, (x, y))
                self.selected = None
                self.draw_board()
    
    def is_adjacent(self, pos1, pos2):
        x1, y1 = pos1
        x2, y2 = pos2
        return abs(x1 - x2) + abs(y1 - y2) == 1
    
    def swap_gems(self, pos1, pos2):
        x1, y1 = pos1
        x2, y2 = pos2
        self.board[y1][x1], self.board[y2][x2] = self.board[y2][x2], self.board[y1][x1]
    
    def check_matches(self):
        matches = set()
        
        # Check horizontal matches
        for y in range(self.grid_size):
            count = 1
            current = self.board[y][0]
            for x in range(1, self.grid_size):
                if self.board[y][x] == current:
                    count += 1
                else:
                    if count >= 3:
                        for i in range(x - count, x):
                            matches.add((i, y))
                    count = 1
                    current = self.board[y][x]
            if count >= 3:
                for i in range(self.grid_size - count, self.grid_size):
                    matches.add((i, y))
        
        # Check vertical matches
        for x in range(self.grid_size):
            count = 1
            current = self.board[0][x]
            for y in range(1, self.grid_size):
                if self.board[y][x] == current:
                    count += 1
                else:
                    if count >= 3:
                        for i in range(y - count, y):
                            matches.add((x, i))
                    count = 1
                    current = self.board[y][x]
            if count >= 3:
                for i in range(self.grid_size - count, self.grid_size):
                    matches.add((x, i))
        
        self.matches = matches
        return len(matches) > 0
    
    def process_matches(self):
        if hasattr(self, 'matches') and self.matches:
            # Remove matched gems
            for x, y in self.matches:
                self.board[y][x] = None
                self.score += 10
            
            # Drop gems down
            for x in range(self.grid_size):
                empty_spots = 0
                for y in range(self.grid_size - 1, -1, -1):
                    if self.board[y][x] is None:
                        empty_spots += 1
                    elif empty_spots > 0:
                        self.board[y + empty_spots][x] = self.board[y][x]
                        self.board[y][x] = None
                
                # Fill with new gems
                for y in range(empty_spots):
                    self.board[y][x] = random.choice(self.gems)
            
            self.score_var.set(f"Score: {self.score}")
            self.draw_board()
              # Check for more matches
            if self.check_matches():
                self.frame.after(500, self.process_matches)
                
    def draw_board(self):
        self.canvas.delete("all")
        
        # Draw background with gradient
        self.canvas.create_rectangle(0, 0, 400, 400, fill="#151525", outline="")
        
        for i in range(0, 400, 8):
            self.canvas.create_line(0, i, 400, i, fill="#1a1a2e", width=1)
            self.canvas.create_line(i, 0, i, 400, fill="#1a1a2e", width=1)
        
        # Draw board grid
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                x1, y1 = x * self.cell_size, y * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                
                # Draw cell background
                self.canvas.create_rectangle(x1, y1, x2, y2, 
                                            fill="#202040", outline="#303060",
                                            width=2)
                
                # Draw gem with enhanced visuals
                gem = self.board[y][x]
                if gem:
                    # Draw gem background with color
                    color = self.gem_colors.get(gem, "#FFFFFF")
                    
                    # Create a "glow" effect around the gem
                    glow_radius = 3
                    self.canvas.create_oval(x1+5-glow_radius, y1+5-glow_radius, 
                                           x2-5+glow_radius, y2-5+glow_radius,
                                           fill="", outline=color, width=2)
                    
                    # Draw gem with background color
                    gem_bg = self.canvas.create_oval(x1+5, y1+5, x2-5, y2-5,
                                                    fill=color, outline="white")
                    
                    # Add shine effect to gem
                    self.canvas.create_oval(x1+10, y1+10, x1+18, y1+18,
                                           fill="white", outline="")
                    
                    # Draw gem symbol
                    self.canvas.create_text(x1 + self.cell_size//2, y1 + self.cell_size//2,
                                           text=gem, font=('Arial', 20))
                    
                    # Highlight selected gem with animation effect
                    if self.selected == (x, y):
                        self.canvas.create_rectangle(x1+2, y1+2, x2-2, y2-2,
                                                   outline="yellow", width=3, dash=(5, 2))


class PainterApp(EmbeddedApplication):
    """Digital painting application"""
    
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.brush_size = 3
        self.brush_color = "black"
        self.last_x = None
        self.last_y = None
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        # Title
        title = ttk.Label(self.frame, text="🎨 Sona Digital Painter", 
                         font=('Arial', 16, 'bold'))
        title.pack(pady=(0, 10))
        
        # Toolbar
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill='x', pady=(0, 10))
        
        # Color palette
        colors = ["black", "red", "blue", "green", "yellow", "purple", "orange", "brown"]
        for color in colors:
            btn = tk.Button(toolbar, bg=color, width=3, height=2,
                           command=lambda c=color: self.set_color(c))
            btn.pack(side='left', padx=2)
        
        # Brush size
        ttk.Label(toolbar, text="Brush:").pack(side='left', padx=(10, 5))
        self.size_var = tk.IntVar(value=3)
        size_scale = ttk.Scale(toolbar, from_=1, to=20, orient='horizontal',
                              variable=self.size_var, command=self.set_brush_size)
        size_scale.pack(side='left', padx=(0, 10))
        
        # Clear button
        ttk.Button(toolbar, text="🗑 Clear", command=self.clear_canvas).pack(side='right')
        
        # Canvas
        self.canvas = tk.Canvas(self.frame, width=600, height=400, bg="white")
        self.canvas.pack(pady=(0, 10))
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.start_paint)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_paint)
        
        return self.frame
        
    def set_color(self, color):
        self.brush_color = color
        
    def set_brush_size(self, value):
        self.brush_size = int(float(value))
        
    def start_paint(self, event):
        self.last_x = event.x
        self.last_y = event.y
        
    def paint(self, event):
        if self.last_x and self.last_y:
            self.canvas.create_line(
                self.last_x, self.last_y, event.x, event.y,
                width=self.brush_size, fill=self.brush_color,
                capstyle=tk.ROUND, smooth=tk.TRUE
            )
        self.last_x = event.x
        self.last_y = event.y
        
    def stop_paint(self, event):
        self.last_x = None
        self.last_y = None
        
    def clear_canvas(self):
        self.canvas.delete("all")


class SolitaireApp(EmbeddedApplication):
    """Enhanced Interactive Solitaire card game with full mouse controls"""
    
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.deck = []
        self.tableau = [[] for _ in range(7)]
        self.foundation = [[] for _ in range(4)]
        self.waste = []
        self.stock = []
        
        # Interactive game state
        self.selected_card = None
        self.selected_pile = None
        self.selected_index = None
        self.card_width = 70
        self.card_height = 100
        self.hover_card = None
        self.moves = 0
        self.game_won = False
        
        # Card face-up/face-down tracking
        self.tableau_face_up = [[] for _ in range(7)]
        
        # Animation state
        self.animation_active = False
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        # Title and stats
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill='x', pady=(0, 10))
        
        title = ttk.Label(title_frame, text="♠️♣️ Interactive Solitaire ♦️♥️", 
                         font=('Arial', 16, 'bold'))
        title.pack(side='left')
        
        self.moves_var = tk.StringVar()
        self.moves_var.set("Moves: 0")
        moves_label = ttk.Label(title_frame, textvariable=self.moves_var,
                               font=('Arial', 12))
        moves_label.pack(side='right')
        
        # Game canvas with improved size
        self.canvas = tk.Canvas(self.frame, width=720, height=520, bg="#1a5d1a",
                               highlightthickness=2, highlightbackground="#228b22")
        self.canvas.pack(pady=(0, 10))
        
        # Controls
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x')
        
        ttk.Button(control_frame, text="🎮 New Game",
                  command=self.new_game).pack(side='left')
        ttk.Button(control_frame, text="📚 Draw Cards",
                  command=self.draw_from_stock).pack(side='left', padx=(10, 0))
        ttk.Button(control_frame, text="🎯 Auto Move",
                  command=self.auto_move).pack(side='left', padx=(10, 0))
        ttk.Button(control_frame, text="💡 Hint",
                  command=self.show_hint).pack(side='left', padx=(10, 0))
        
        # Game status
        self.status_var = tk.StringVar()
        self.status_var.set("Click New Game to start!")
        status_label = ttk.Label(control_frame, textvariable=self.status_var,
                                font=('Arial', 10))
        status_label.pack(side='right')
        
        instructions = ttk.Label(self.frame, 
                                text="🖱️ Click to select cards | Drag to move | Right-click for auto-move | Double-click to send to foundation",
                                font=('Arial', 10))
        instructions.pack(pady=(10, 0))
        
        # Configure canvas for mouse events
        self.canvas.configure(takefocus=True)
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<KeyPress>", self.key_pressed)
        self.canvas.bind("<Button-1>", lambda e: self.canvas.focus_set())
        
        # Bind mouse drag events
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_drop)
        
        # Track drag state
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.dragging = False
        self.drag_cards = []
        
        # Ensure canvas gets focus
        self.frame.after(100, lambda: self.canvas.focus_set())
        
        self.new_game()
        return self.frame
        
    def new_game(self):
        """Initialize a new game"""
        # Create deck with proper suits and colors
        red_suits = ['♦', '♥']
        black_suits = ['♠', '♣']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        
        self.deck = []
        for suit in red_suits + black_suits:
            for rank in ranks:
                color = 'red' if suit in red_suits else 'black'
                self.deck.append({'rank': rank, 'suit': suit, 'color': color})
        
        random.shuffle(self.deck)
        
        # Deal to tableau
        self.tableau = [[] for _ in range(7)]
        self.tableau_face_up = [[] for _ in range(7)]
        card_index = 0
        
        for col in range(7):
            for row in range(col + 1):
                self.tableau[col].append(self.deck[card_index])
                # Only the last card in each column starts face up
                self.tableau_face_up[col].append(row == col)
                card_index += 1
        
        # Remaining cards go to stock
        self.stock = self.deck[card_index:]
        self.waste = []
        self.foundation = [[] for _ in range(4)]
        
        # Reset game state
        self.selected_card = None
        self.selected_pile = None
        self.selected_index = None
        self.moves = 0
        self.game_won = False
        self.moves_var.set("Moves: 0")
        self.status_var.set("Game started! Good luck!")
        
        self.draw_game()
        
    def draw_from_stock(self):
        """Draw cards from stock to waste pile"""
        if self.stock:
            # Draw 3 cards (or remaining if less than 3)
            for _ in range(min(3, len(self.stock))):
                self.waste.append(self.stock.pop())
            self.increment_moves()
        else:
            # Flip waste back to stock
            if self.waste:
                self.stock = self.waste[::-1]
                self.waste = []
                self.increment_moves()
        
        self.status_var.set("Cards drawn from stock")
        self.draw_game()
        
    def get_card_position(self, pile_type, pile_index, card_index=None):
        """Get the position of a card on the canvas"""
        if pile_type == 'stock':
            return (20, 20)
        elif pile_type == 'waste':
            return (110, 20)
        elif pile_type == 'foundation':
            return (300 + pile_index * 85, 20)
        elif pile_type == 'tableau':
            x = 20 + pile_index * 85
            if card_index is None:
                card_index = len(self.tableau[pile_index]) - 1
            y = 150 + card_index * 25
            return (x, y)
        return (0, 0)
        
    def get_clicked_card(self, x, y):
        """Determine which card was clicked based on coordinates"""
        # Check stock
        if 20 <= x <= 90 and 20 <= y <= 120:
            if self.stock:
                return ('stock', 0, 0)
                
        # Check waste
        if 110 <= x <= 180 and 20 <= y <= 120:
            if self.waste:
                return ('waste', 0, len(self.waste) - 1)
                
        # Check foundation
        for i in range(4):
            fx = 300 + i * 85
            if fx <= x <= fx + 70 and 20 <= y <= 120:
                if self.foundation[i]:
                    return ('foundation', i, len(self.foundation[i]) - 1)
                else:
                    return ('foundation', i, -1)  # Empty foundation pile
                    
        # Check tableau (check from bottom to top to get topmost card)
        for col in range(7):
            tx = 20 + col * 85
            if tx <= x <= tx + 70:
                for row in range(len(self.tableau[col]) - 1, -1, -1):
                    ty = 150 + row * 25
                    if ty <= y <= ty + 100:  # Card height
                        if self.tableau_face_up[col][row]:  # Only face-up cards are clickable
                            return ('tableau', col, row)
                        break
                        
        return None
        
    def on_left_click(self, event):
        """Handle left mouse click"""
        clicked = self.get_clicked_card(event.x, event.y)
        
        if not clicked:
            # Clicked empty space - deselect
            self.selected_card = None
            self.selected_pile = None
            self.selected_index = None
            self.draw_game()
            return
            
        pile_type, pile_index, card_index = clicked
        
        # Handle stock click
        if pile_type == 'stock':
            self.draw_from_stock()
            return
            
        # If clicking on already selected card, deselect
        if (self.selected_pile == pile_type and 
            self.selected_index == card_index and
            (pile_type != 'tableau' or self.selected_pile == pile_index)):
            self.selected_card = None
            self.selected_pile = None
            self.selected_index = None
            self.draw_game()
            return
            
        # If no card selected, select this card
        if self.selected_card is None:
            if pile_type == 'foundation' and card_index == -1:
                return  # Can't select empty foundation
            self.select_card(pile_type, pile_index, card_index)
        else:
            # Try to move selected card to clicked position
            self.try_move_card(pile_type, pile_index, card_index)
            
    def on_right_click(self, event):
        """Handle right mouse click for auto-move"""
        clicked = self.get_clicked_card(event.x, event.y)
        if clicked and clicked[0] in ['waste', 'tableau']:
            self.auto_move_card(clicked[0], clicked[1], clicked[2])
            
    def on_double_click(self, event):
        """Handle double-click to auto-move to foundation"""
        clicked = self.get_clicked_card(event.x, event.y)
        if clicked and clicked[0] in ['waste', 'tableau']:
            self.auto_move_to_foundation(clicked[0], clicked[1], clicked[2])
            
    def on_mouse_move(self, event):
        """Handle mouse movement for hover effects"""
        hovered = self.get_clicked_card(event.x, event.y)
        if hovered != self.hover_card:
            self.hover_card = hovered
            # Could add hover highlighting here
            
    def on_drag(self, event):
        """Handle mouse drag"""
        if not self.dragging and self.selected_card:
            # Start dragging
            self.dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            
    def on_drop(self, event):
        """Handle mouse button release (drop)"""
        if self.dragging:
            self.dragging = False
            # Find drop target
            target = self.get_clicked_card(event.x, event.y)
            if target and self.selected_card:
                self.try_move_card(target[0], target[1], target[2])
                
    def select_card(self, pile_type, pile_index, card_index):
        """Select a card for movement"""
        if pile_type == 'waste' and self.waste:
            self.selected_card = self.waste[-1]
            self.selected_pile = 'waste'
            self.selected_index = len(self.waste) - 1
        elif pile_type == 'tableau' and card_index < len(self.tableau[pile_index]):
            self.selected_card = self.tableau[pile_index][card_index]
            self.selected_pile = 'tableau'
            self.selected_index = (pile_index, card_index)
        elif pile_type == 'foundation' and self.foundation[pile_index]:
            self.selected_card = self.foundation[pile_index][-1]
            self.selected_pile = 'foundation'
            self.selected_index = pile_index
            
        self.draw_game()
        
    def try_move_card(self, target_pile, target_index, target_card_index):
        """Try to move the selected card to the target position"""
        if not self.selected_card:
            return
            
        moved = False
        
        if target_pile == 'foundation':
            moved = self.move_to_foundation(target_index)
        elif target_pile == 'tableau':
            moved = self.move_to_tableau(target_index)
            
        if moved:
            self.increment_moves()
            self.selected_card = None
            self.selected_pile = None
            self.selected_index = None
            self.check_for_face_up()
            self.check_win_condition()
            
        self.draw_game()
        
    def move_to_foundation(self, foundation_index):
        """Move selected card to foundation pile"""
        if not self.selected_card:
            return False
            
        card = self.selected_card
        foundation_pile = self.foundation[foundation_index]
        
        # Check if move is valid
        if not foundation_pile:
            # Empty foundation - only accept Ace
            if card['rank'] != 'A':
                self.status_var.set("Only Aces can start foundation piles!")
                return False
        else:
            # Check if card is next in sequence and same suit
            top_card = foundation_pile[-1]
            if (card['suit'] != top_card['suit'] or 
                not self.is_next_rank(top_card['rank'], card['rank'])):
                self.status_var.set("Invalid foundation move!")
                return False
                
        # Remove card from source
        if self.selected_pile == 'waste':
            self.waste.pop()
        elif self.selected_pile == 'tableau':
            col, row = self.selected_index
            self.tableau[col].pop()
            self.tableau_face_up[col].pop()
        elif self.selected_pile == 'foundation':
            self.foundation[self.selected_index].pop()
            
        # Add to foundation
        self.foundation[foundation_index].append(card)
        self.status_var.set("Card moved to foundation!")
        return True
        
    def move_to_tableau(self, tableau_index):
        """Move selected card(s) to tableau pile"""
        if not self.selected_card:
            return False
            
        card = self.selected_card
        tableau_pile = self.tableau[tableau_index]
        
        # Check if move is valid
        if not tableau_pile:
            # Empty tableau - only accept King
            if card['rank'] != 'K':
                self.status_var.set("Only Kings can start empty tableau piles!")
                return False
        else:
            # Check if card is next in sequence and opposite color
            top_card = tableau_pile[-1]
            if (card['color'] == top_card['color'] or 
                not self.is_previous_rank(top_card['rank'], card['rank'])):
                self.status_var.set("Invalid tableau move!")
                return False
                
        # For tableau moves, we might move multiple cards
        cards_to_move = []
        face_up_to_move = []
        
        if self.selected_pile == 'tableau':
            col, start_row = self.selected_index
            # Move all cards from selected position to end
            cards_to_move = self.tableau[col][start_row:]
            face_up_to_move = self.tableau_face_up[col][start_row:]
            # Remove from source
            self.tableau[col] = self.tableau[col][:start_row]
            self.tableau_face_up[col] = self.tableau_face_up[col][:start_row]
        else:
            # Moving single card from waste or foundation
            cards_to_move = [card]
            face_up_to_move = [True]
            
            if self.selected_pile == 'waste':
                self.waste.pop()
            elif self.selected_pile == 'foundation':
                self.foundation[self.selected_index].pop()
                
        # Add to target tableau
        self.tableau[tableau_index].extend(cards_to_move)
        self.tableau_face_up[tableau_index].extend(face_up_to_move)
        
        self.status_var.set("Cards moved to tableau!")
        return True
        
    def is_next_rank(self, current_rank, next_rank):
        """Check if next_rank follows current_rank in ascending order"""
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        try:
            current_index = ranks.index(current_rank)
            next_index = ranks.index(next_rank)
            return next_index == current_index + 1
        except ValueError:
            return False
            
    def is_previous_rank(self, current_rank, prev_rank):
        """Check if prev_rank comes before current_rank in descending order"""
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        try:
            current_index = ranks.index(current_rank)
            prev_index = ranks.index(prev_rank)
            return prev_index == current_index - 1
        except ValueError:
            return False
            
    def check_for_face_up(self):
        """Check if any tableau cards should be flipped face up"""
        for col in range(7):
            if (self.tableau[col] and 
                self.tableau_face_up[col] and 
                not self.tableau_face_up[col][-1]):
                # Flip the top card face up
                self.tableau_face_up[col][-1] = True
                
    def auto_move(self):
        """Automatically move cards to foundation if possible"""
        moved = False
        
        # Try to move from waste
        if self.waste:
            for foundation_index in range(4):
                self.selected_card = self.waste[-1]
                self.selected_pile = 'waste'
                self.selected_index = len(self.waste) - 1
                if self.move_to_foundation(foundation_index):
                    moved = True
                    break
                    
        # Try to move from tableau
        if not moved:
            for col in range(7):
                if self.tableau[col] and self.tableau_face_up[col][-1]:
                    for foundation_index in range(4):
                        self.selected_card = self.tableau[col][-1]
                        self.selected_pile = 'tableau'
                        self.selected_index = (col, len(self.tableau[col]) - 1)
                        if self.move_to_foundation(foundation_index):
                            moved = True
                            break
                    if moved:
                        break
                        
        if moved:
            self.increment_moves()
            self.check_for_face_up()
            self.check_win_condition()
            self.status_var.set("Auto-moved card to foundation!")
        else:
            self.status_var.set("No automatic moves available")
            
        self.selected_card = None
        self.selected_pile = None
        self.selected_index = None
        self.draw_game()
        
    def auto_move_card(self, pile_type, pile_index, card_index):
        """Auto-move a specific card to the best position"""
        self.select_card(pile_type, pile_index, card_index)
        self.auto_move()
        
    def auto_move_to_foundation(self, pile_type, pile_index, card_index):
        """Auto-move a specific card to foundation"""
        self.select_card(pile_type, pile_index, card_index)
        
        # Try each foundation pile
        for foundation_index in range(4):
            if self.move_to_foundation(foundation_index):
                self.increment_moves()
                self.check_for_face_up()
                self.check_win_condition()
                break
                
        self.selected_card = None
        self.selected_pile = None
        self.selected_index = None
        self.draw_game()
        
    def show_hint(self):
        """Show a hint for possible moves"""
        hints = []
        
        # Check for foundation moves
        if self.waste:
            card = self.waste[-1]
            for i, foundation in enumerate(self.foundation):
                if self.can_move_to_foundation(card, foundation):
                    hints.append(f"Move {card['rank']}{card['suit']} from waste to foundation {i+1}")
                    
        for col in range(7):
            if self.tableau[col] and self.tableau_face_up[col][-1]:
                card = self.tableau[col][-1]
                for i, foundation in enumerate(self.foundation):
                    if self.can_move_to_foundation(card, foundation):
                        hints.append(f"Move {card['rank']}{card['suit']} from tableau {col+1} to foundation {i+1}")
                        
        if hints:
            self.status_var.set(f"Hint: {hints[0]}")
        else:
            self.status_var.set("No obvious moves found - try moving cards between tableau piles")
            
    def can_move_to_foundation(self, card, foundation):
        """Check if a card can be moved to a foundation pile"""
        if not foundation:
            return card['rank'] == 'A'
        else:
            top_card = foundation[-1]
            return (card['suit'] == top_card['suit'] and 
                    self.is_next_rank(top_card['rank'], card['rank']))
                    
    def increment_moves(self):
        """Increment move counter"""
        self.moves += 1
        self.moves_var.set(f"Moves: {self.moves}")
        
    def check_win_condition(self):
        """Check if the game is won"""
        if all(len(foundation) == 13 for foundation in self.foundation):
            self.game_won = True
            self.status_var.set(f"🎉 Congratulations! You won in {self.moves} moves! 🎉")
            messagebox.showinfo("Victory!", f"Congratulations!\nYou won in {self.moves} moves!")
            
    def draw_game(self):
        """Draw the enhanced game with better graphics"""
        self.canvas.delete("all")
        
        # Draw background pattern
        for i in range(0, 720, 40):
            for j in range(0, 520, 40):
                self.canvas.create_rectangle(i, j, i+20, j+20, fill="#2d7d2d", outline="")
        
        # Draw stock pile
        self.draw_card_pile(20, 20, self.stock, "Stock", show_count=True)
        
        # Draw waste pile
        self.draw_waste_pile()
        
        # Draw foundation piles
        for i in range(4):
            x = 300 + i * 85
            self.draw_foundation_pile(x, 20, self.foundation[i], i)
            
        # Draw tableau piles
        for col in range(7):
            x = 20 + col * 85
            self.draw_tableau_pile(x, 150, col)
            
        # Highlight selected card
        if self.selected_card and self.selected_pile:
            self.highlight_selected_card()
            
    def draw_card_pile(self, x, y, pile, label, show_count=False):
        """Draw a pile of cards"""
        # Draw empty pile
        self.canvas.create_rectangle(x, y, x + self.card_width, y + self.card_height,
                                   fill="#ffffff", outline="#000000", width=2)
        
        if pile:
            # Draw card back or top card
            self.canvas.create_rectangle(x, y, x + self.card_width, y + self.card_height,
                                       fill="#0066cc", outline="#000000", width=2)
            self.canvas.create_text(x + self.card_width//2, y + self.card_height//2,
                                  text="🂠", font=('Arial', 24), fill="white")
        else:
            # Empty pile indicator
            self.canvas.create_text(x + self.card_width//2, y + self.card_height//2,
                                  text=label, font=('Arial', 10), fill="#666666")
                                  
        if show_count and pile:
            self.canvas.create_text(x + self.card_width - 5, y + 15,
                                  text=str(len(pile)), font=('Arial', 12, 'bold'),
                                  fill="yellow")
                                  
    def draw_waste_pile(self):
        """Draw the waste pile showing multiple cards"""
        x, y = 110, 20
        
        # Draw empty pile
        self.canvas.create_rectangle(x, y, x + self.card_width, y + self.card_height,
                                   fill="#ffffff", outline="#000000", width=2)
        
        if not self.waste:
            self.canvas.create_text(x + self.card_width//2, y + self.card_height//2,
                                  text="Waste", font=('Arial', 10), fill="#666666")
        else:
            # Show up to 3 cards in waste pile
            for i, card in enumerate(self.waste[-3:]):
                offset = i * 3
                self.draw_single_card(x + offset, y + offset, card)
                
    def draw_foundation_pile(self, x, y, pile, pile_index):
        """Draw a foundation pile"""
        # Draw empty pile with suit indicator
        suits = ['♠', '♣', '♦', '♥']
        self.canvas.create_rectangle(x, y, x + self.card_width, y + self.card_height,
                                   fill="#f0f0f0", outline="#000000", width=2)
        
        if pile:
            self.draw_single_card(x, y, pile[-1])
        else:
            # Empty foundation with suit
            color = "red" if suits[pile_index] in ['♦', '♥'] else "black"
            self.canvas.create_text(x + self.card_width//2, y + self.card_height//2,
                                  text=suits[pile_index], font=('Arial', 24), fill=color)
                                  
    def draw_tableau_pile(self, x, y, col):
        """Draw a tableau pile"""
        if not self.tableau[col]:
            # Empty tableau pile
            self.canvas.create_rectangle(x, y, x + self.card_width, y + self.card_height,
                                       fill="#ffffff", outline="#666666", width=2, dash=(5, 5))
            self.canvas.create_text(x + self.card_width//2, y + self.card_height//2,
                                  text="K", font=('Arial', 20), fill="#cccccc")
        else:
            for i, card in enumerate(self.tableau[col]):
                card_y = y + i * 25
                if self.tableau_face_up[col][i]:
                    self.draw_single_card(x, card_y, card)
                else:
                    # Face-down card
                    self.canvas.create_rectangle(x, card_y, x + self.card_width, card_y + self.card_height,
                                               fill="#0066cc", outline="#000000", width=2)
                    self.canvas.create_text(x + self.card_width//2, card_y + self.card_height//2,
                                          text="🂠", font=('Arial', 20), fill="white")
                                          
    def draw_single_card(self, x, y, card):
        """Draw a single card with proper styling"""
        # Card background
        self.canvas.create_rectangle(x, y, x + self.card_width, y + self.card_height,
                                   fill="white", outline="black", width=2)
        
        # Card color
        color = "red" if card['color'] == 'red' else "black"
        
        # Card rank and suit
        rank_text = card['rank']
        suit_text = card['suit']
        
        # Main rank and suit
        self.canvas.create_text(x + 10, y + 15, text=rank_text, 
                              font=('Arial', 12, 'bold'), fill=color, anchor='nw')
        self.canvas.create_text(x + 10, y + 30, text=suit_text,
                              font=('Arial', 14), fill=color, anchor='nw')
        
        # Center suit symbol
        self.canvas.create_text(x + self.card_width//2, y + self.card_height//2,
                              text=suit_text, font=('Arial', 24), fill=color)
        
        # Bottom rank and suit (upside down)
        self.canvas.create_text(x + self.card_width - 10, y + self.card_height - 15,
                              text=rank_text, font=('Arial', 12, 'bold'), fill=color, anchor='se')
        self.canvas.create_text(x + self.card_width - 10, y + self.card_height - 30,
                              text=suit_text, font=('Arial', 14), fill=color, anchor='se')
                              
    def highlight_selected_card(self):
        """Highlight the selected card"""
        if self.selected_pile == 'waste':
            x, y = 110, 20
            # Highlight with golden border
            self.canvas.create_rectangle(x-3, y-3, x + self.card_width + 3, y + self.card_height + 3,
                                       outline="gold", width=4)
        elif self.selected_pile == 'tableau':
            col, row = self.selected_index
            x = 20 + col * 85
            y = 150 + row * 25
            # Highlight selected card and all cards below it
            for i in range(row, len(self.tableau[col])):
                card_y = 150 + i * 25
                self.canvas.create_rectangle(x-3, card_y-3, x + self.card_width + 3, card_y + self.card_height + 3,
                                           outline="gold", width=4)
        elif self.selected_pile == 'foundation':
            x = 300 + self.selected_index * 85
            y = 20
            self.canvas.create_rectangle(x-3, y-3, x + self.card_width + 3, y + self.card_height + 3,
                                       outline="gold", width=4)
                                       
    def key_pressed(self, event):
        """Handle keyboard inputs for Solitaire game"""
        key = event.keysym.lower()
        
        # Space or Enter to draw cards
        if key in ['space', 'return']:
            self.draw_from_stock()
        elif key == 'h':
            self.show_hint()
        elif key == 'a':
            self.auto_move()
        elif key == 'n':
            self.new_game()


class ModernTetrisGame:
    """Modern Tetris game implementation"""
    def __init__(self, canvas, width=10, height=20):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.block_size = 25
        self.board = [[0 for _ in range(width)] for _ in range(height)]
        self.current_piece = None
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.running = False
        self.colors = {
            0: '#1a1a2e',  # Empty
            1: '#00bcd4',  # Cyan
            2: '#ffd700',  # Yellow
            3: '#ff6b6b',  # Red
            4: '#4ecdc4',  # Teal
            5: '#45b7d1',  # Blue
            6: '#f39c12',  # Orange
            7: '#9b59b6'   # Purple
        }
        
        # Tetris pieces (simplified)
        self.pieces = [
            [[1, 1, 1, 1]],  # I-piece
            [[1, 1], [1, 1]],  # O-piece
            [[1, 1, 1], [0, 1, 0]],  # T-piece
            [[1, 1, 1], [1, 0, 0]],  # L-piece
            [[1, 1, 1], [0, 0, 1]],  # J-piece
            [[0, 1, 1], [1, 1, 0]],  # S-piece
            [[1, 1, 0], [0, 1, 1]]   # Z-piece
        ]
        
        self.setup_initial_state()
    
    def setup_initial_state(self):
        """Setup initial game state with some blocks"""
        # Add some sample blocks at the bottom
        for i in range(18, 20):
            for j in range(3):
                self.board[i][j] = 2  # Yellow blocks
        
        for i in range(19, 20):
            for j in range(3, 5):
                self.board[i][j] = 2  # Yellow blocks
        
        # Add the cyan I-piece at top
        for i in range(4):
            self.board[2][4] = 1  # Cyan blocks
            self.board[3][4] = 1
            self.board[4][4] = 1
            self.board[5][4] = 1
    
    def draw(self):
        """Draw the game board"""
        self.canvas.delete("all")
        
        # Draw board
        for y in range(self.height):
            for x in range(self.width):
                x1 = x * self.block_size
                y1 = y * self.block_size
                x2 = x1 + self.block_size
                y2 = y1 + self.block_size
                
                color = self.colors[self.board[y][x]]
                
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline='#333',
                    width=1
                )
        
        # Draw grid lines
        for i in range(self.width + 1):
            x = i * self.block_size
            self.canvas.create_line(x, 0, x, self.height * self.block_size, fill='#333', width=1)
        
        for i in range(self.height + 1):
            y = i * self.block_size
            self.canvas.create_line(0, y, self.width * self.block_size, y, fill='#333', width=1)

class TetrisApp(EmbeddedApplication):
    """Modern Tetris puzzle game"""
    
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.score = 120
        self.level = 3
        self.lines_cleared = 8
        self.game_running = False
        
    def create_gui(self, container):
        """Create the modern Tetris GUI"""
        # Modern colors matching the dark theme
        self.colors = {
            'bg_primary': '#1a1a2e',
            'bg_secondary': '#16213e',
            'bg_tertiary': '#0f1419',
            'accent': '#00bcd4',
            'text_primary': '#ffffff',
            'text_secondary': '#b0b0b0',
            'highlight': '#ffd700'
        }
        
        # Main frame with dark theme
        self.frame = tk.Frame(container, bg=self.colors['bg_primary'])
        
        # Title area
        title_frame = tk.Frame(self.frame, bg=self.colors['bg_primary'])
        title_frame.pack(fill='x', pady=(20, 30))
        
        app_title = tk.Label(title_frame, text="TETRIS",
                            fg=self.colors['accent'],
                            bg=self.colors['bg_primary'],
                            font=('Segoe UI', 28, 'bold'))
        app_title.pack()
        
        # Game area
        game_frame = tk.Frame(self.frame, bg=self.colors['bg_tertiary'])
        game_frame.pack(pady=20, padx=40)
        
        # Create canvas for Tetris
        self.game_canvas = tk.Canvas(game_frame, 
                                   width=250, height=500,
                                   bg=self.colors['bg_tertiary'],
                                   highlightthickness=0)
        self.game_canvas.pack(padx=20, pady=20)
        
        # Initialize the modern Tetris game
        self.tetris_game = ModernTetrisGame(self.game_canvas)
        self.tetris_game.score = self.score
        self.tetris_game.level = self.level
        self.tetris_game.draw()
        
        # Stats area
        stats_frame = tk.Frame(self.frame, bg=self.colors['bg_primary'])
        stats_frame.pack(fill='x', padx=40, pady=(0, 20))
        
        # Score and Level
        score_frame = tk.Frame(stats_frame, bg=self.colors['bg_primary'])
        score_frame.pack(fill='x')
        
        self.score_label = tk.Label(score_frame, text=f"Score: {self.score}",
                                   fg=self.colors['text_primary'],
                                   bg=self.colors['bg_primary'],
                                   font=('Segoe UI', 16, 'bold'))
        self.score_label.pack(side='left')
        
        self.level_label = tk.Label(score_frame, text=f"Level: {self.level}",
                                   fg=self.colors['text_primary'],
                                   bg=self.colors['bg_primary'],
                                   font=('Segoe UI', 16, 'bold'))
        self.level_label.pack(side='right')
        
        # Game controls info
        controls_frame = tk.Frame(self.frame, bg=self.colors['bg_primary'])
        controls_frame.pack(fill='x', padx=40, pady=(0, 20))
        
        controls_text = "Controls: ← → Move • ↓ Drop • ↑ Rotate • Space Pause"
        controls_label = tk.Label(controls_frame, text=controls_text,
                                 fg=self.colors['text_secondary'],
                                 bg=self.colors['bg_primary'],
                                 font=('Segoe UI', 10))
        controls_label.pack()
        
        print(f"Tetris game initialized - Score: {self.score}, Level: {self.level}")
        
        return self.frame
    
    def start(self):
        """Start the Tetris game"""
        print("Tetris game started!")
        self.game_running = True
        if hasattr(self, 'tetris_game'):
            self.tetris_game.running = True
            
    def stop(self):
        """Stop the Tetris game"""
        print("Tetris game stopped!")
        self.game_running = False
        if hasattr(self, 'tetris_game'):
            self.tetris_game.running = False
            
    def update(self):
        """Update the Tetris game state"""
        if self.game_running and hasattr(self, 'tetris_game'):
            # Update game logic here
            pass
        
        # Bind keys
        self.canvas.bind("<KeyPress>", self.handle_keypress)
        self.canvas.focus_set()
        return self.frame
        
    def start_game(self):
        self.game_running = True
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.board = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.board_colors = [[None for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        # No start button to disable - use Space/Enter to start
        self.spawn_piece()
        self.game_loop()
        
    def spawn_piece(self):
        # Select random piece and matching color
        piece_index = random.randint(0, len(self.pieces) - 1)
        self.current_piece = self.pieces[piece_index]
        self.current_color = self.piece_colors[piece_index]
        self.current_x = self.grid_width // 2 - len(self.current_piece[0]) // 2
        self.current_y = 0
        
        # Check game over
        if self.check_collision():
            self.game_over()
            
    def handle_keypress(self, event):
        key = event.keysym.lower()
        
        # Start game with Space or Enter when not running
        if not self.game_running and key in ['space', 'return']:
            self.start_game()
            return
            
        if not self.game_running:
            return
            
        if key == 'a':
            self.move_piece(-1, 0)
        elif key == 'd':
            self.move_piece(1, 0)
        elif key == 's':
            self.move_piece(0, 1)
        elif key == 'w':
            self.rotate_piece()
            
    def move_piece(self, dx, dy):
        self.current_x += dx
        self.current_y += dy
        
        if self.check_collision():
            self.current_x -= dx
            self.current_y -= dy
            
            if dy > 0:  # Piece hit bottom
                self.place_piece()
                self.clear_lines()
                self.spawn_piece()
                
    def rotate_piece(self):
        # Simple rotation (transpose and reverse)
        original = self.current_piece
        self.current_piece = [list(row) for row in zip(*self.current_piece[::-1], strict=False)]
        
        if self.check_collision():
            self.current_piece = original
            
    def check_collision(self):
        for y, row in enumerate(self.current_piece):
            for x, cell in enumerate(row):
                if cell == '*':
                    new_x, new_y = self.current_x + x, self.current_y + y
                    if (new_x < 0 or new_x >= self.grid_width or
                        new_y >= self.grid_height or
                        (new_y >= 0 and self.board[new_y][new_x])):
                        return True
        return False
        
    def place_piece(self):
        for y, row in enumerate(self.current_piece):
            for x, cell in enumerate(row):
                if cell == '*':
                    board_x, board_y = self.current_x + x, self.current_y + y
                    if 0 <= board_y < self.grid_height and 0 <= board_x < self.grid_width:
                        self.board[board_y][board_x] = 1
                        self.board_colors[board_y][board_x] = self.current_color
                        
    def clear_lines(self):
        lines_to_clear = []
        for y in range(self.grid_height):
            if all(self.board[y]):
                lines_to_clear.append(y)
                
        for y in lines_to_clear:
            del self.board[y]
            self.board.insert(0, [0 for _ in range(self.grid_width)])
            self.lines_cleared += 1
            
        if lines_to_clear:
            self.score += len(lines_to_clear) * 100 * self.level
            self.level = self.lines_cleared // 10 + 1
            self.fall_time = max(50, 500 - (self.level - 1) * 50)            
            self.score_var.set(f"Score: {self.score}")
            self.level_var.set(f"Level: {self.level}")
            self.lines_var.set(f"Lines: {self.lines_cleared}")
            
    def draw_game(self):
        self.canvas.delete("all")
        
        # Draw board with colors
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                x1, y1 = x * self.cell_size + 1, y * self.cell_size + 1
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                
                if self.board[y][x]:
                    # Use stored color or default to cyan if no color (for backwards compatibility)
                    color = self.board_colors[y][x] if self.board_colors[y][x] else "cyan"
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="white")
                    # Add a 3D effect with inner shadows
                    self.canvas.create_line(x1+2, y2-2, x2-2, y2-2, fill="black", width=1)
                    self.canvas.create_line(x2-2, y1+2, x2-2, y2-2, fill="black", width=1)
                else:
                    # Grid cell with subtle gradient
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="#101010", outline="#303030")
        
        # Draw current piece with color
        if self.current_piece:
            for y, row in enumerate(self.current_piece):
                for x, cell in enumerate(row):
                    if cell == '*':
                        draw_x, draw_y = self.current_x + x, self.current_y + y
                        if 0 <= draw_y < self.grid_height and 0 <= draw_x < self.grid_width:
                            x1 = draw_x * self.cell_size + 1
                            y1 = draw_y * self.cell_size + 1
                            x2 = x1 + self.cell_size
                            y2 = y1 + self.cell_size
                            self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.current_color, outline="white")
                            # Add a 3D effect with highlights
                            self.canvas.create_line(x1+2, y1+2, x2-2, y1+2, fill="white", width=1)
                            self.canvas.create_line(x1+2, y1+2, x1+2, y2-2, fill="white", width=1)
                            
    def game_loop(self):
        if not self.game_running:
            return
            
        self.move_piece(0, 1)
        self.draw_game()
        self.frame.after(self.fall_time, self.game_loop)
        
    def game_over(self):
        self.game_running = False
        # No start button to re-enable - use Space/Enter to start
        messagebox.showinfo("Game Over", f"Final Score: {self.score}")


class MahjongApp(EmbeddedApplication):
    """Mahjong Solitaire tile matching game"""
    
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.tiles = []
        self.selected_tile = None
        self.score = 0
        self.matches = 0
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        # Title
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(title_frame, text="🀄 Mahjong Solitaire", 
                 font=('Arial', 16, 'bold')).pack(side='left')
        
        self.score_var = tk.StringVar()
        self.score_var.set("Score: 0")
        ttk.Label(title_frame, textvariable=self.score_var,
                 font=('Arial', 14, 'bold')).pack(side='right')
        
        # Game canvas
        self.canvas = tk.Canvas(self.frame, width=600, height=400, bg="darkgreen")
        self.canvas.pack(pady=(0, 10))
        self.canvas.bind("<Button-1>", self.on_click)
        
        # Controls
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x')
        
        ttk.Button(control_frame, text="🎮 New Game",
                  command=self.new_game).pack(side='left')
        
        self.matches_var = tk.StringVar()
        self.matches_var.set("Matches: 0")
        ttk.Label(control_frame, textvariable=self.matches_var,
                 font=('Arial', 12)).pack(side='right')
        
        self.new_game()
        return self.frame
        
    def new_game(self):
        self.score = 0
        self.matches = 0
        self.selected_tile = None
        self.score_var.set("Score: 0")
        self.matches_var.set("Matches: 0")
        self.create_tiles()
        self.draw_tiles()
        
    def create_tiles(self):
        # Simple tile symbols
        symbols = ['🀄', '🀅', '🀆', '🀇', '🀈', '🀉', '🀊', '🀋']
        self.tiles = []
        
        # Create pairs of tiles
        for symbol in symbols:
            for _ in range(4):  # 4 of each tile
                self.tiles.append({
                    'symbol': symbol,
                    'x': random.randint(50, 550),
                    'y': random.randint(50, 350),
                    'visible': True
                })
        
        random.shuffle(self.tiles)
        
    def draw_tiles(self):
        self.canvas.delete("all")
        
        for i, tile in enumerate(self.tiles):
            if tile['visible']:
                x, y = tile['x'], tile['y']
                
                # Highlight selected tile
                if self.selected_tile == i:
                    self.canvas.create_rectangle(x-2, y-2, x+42, y+62, fill="yellow", outline="gold", width=3)
                
                # Draw tile
                self.canvas.create_rectangle(x, y, x+40, y+60, fill="white", outline="black", width=2)
                self.canvas.create_text(x+20, y+30, text=tile['symbol'], font=('Arial', 16))
                
    def on_click(self, event):
        clicked_tile = None
        
        # Find clicked tile
        for i, tile in enumerate(self.tiles):
            if (tile['visible'] and 
                tile['x'] <= event.x <= tile['x'] + 40 and 
                tile['y'] <= event.y <= tile['y'] + 60):
                clicked_tile = i
                break
                
        if clicked_tile is not None:
            if self.selected_tile is None:
                self.selected_tile = clicked_tile
            elif self.selected_tile == clicked_tile:
                self.selected_tile = None
            else:
                # Check if tiles match
                if (self.tiles[self.selected_tile]['symbol'] == 
                    self.tiles[clicked_tile]['symbol']):
                    # Match found!
                    self.tiles[self.selected_tile]['visible'] = False
                    self.tiles[clicked_tile]['visible'] = False
                    self.matches += 1
                    self.score += 10
                    self.score_var.set(f"Score: {self.score}")
                    self.matches_var.set(f"Matches: {self.matches}")
                    
                    # Check win condition
                    if all(not tile['visible'] for tile in self.tiles):
                        messagebox.showinfo("Congratulations!", f"You won! Final Score: {self.score}")
                
                self.selected_tile = None
            
        self.draw_tiles()


class BubbleShooterApp(EmbeddedApplication):
    """Bubble Shooter puzzle game"""
    
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.bubbles = []
        self.shooter_angle = 90
        self.shooter_x = 300
        self.shooter_y = 550
        self.current_bubble = None
        self.score = 0
        self.colors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange']
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        # Title
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(title_frame, text="🫧 Bubble Shooter", 
                 font=('Arial', 16, 'bold')).pack(side='left')
        
        self.score_var = tk.StringVar()
        self.score_var.set("Score: 0")
        ttk.Label(title_frame, textvariable=self.score_var,
                 font=('Arial', 14, 'bold')).pack(side='right')
        
        # Game canvas
        self.canvas = tk.Canvas(self.frame, width=600, height=600, bg="black")
        self.canvas.pack(pady=(0, 10))
        self.canvas.bind("<Motion>", self.aim_shooter)
        self.canvas.bind("<Button-1>", self.shoot_bubble)
        
        # Controls
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x')
        
        ttk.Button(control_frame, text="🎮 New Game",
                  command=self.new_game).pack(side='left')
        
        ttk.Label(control_frame, text="Move mouse to aim, click to shoot",
                 font=('Arial', 10)).pack(side='right')
        
        self.new_game()
        return self.frame
        
    def new_game(self):
        self.score = 0
        self.score_var.set("Score: 0")
        self.create_bubble_field()
        self.new_bubble()
        self.draw_game()
        
    def create_bubble_field(self):
        self.bubbles = []
        bubble_radius = 20
        
        # Create initial bubble field
        for row in range(8):
            for col in range(15):
                if row % 2 == 1:  # Offset odd rows
                    x = col * (bubble_radius * 2) + bubble_radius * 2
                else:
                    x = col * (bubble_radius * 2) + bubble_radius
                    
                y = row * (bubble_radius * 1.5) + bubble_radius
                
                if x < 600 - bubble_radius:
                    self.bubbles.append({
                        'x': x,
                        'y': y,
                        'color': random.choice(self.colors),
                        'radius': bubble_radius
                    })
                    
    def new_bubble(self):
        self.current_bubble = {
            'color': random.choice(self.colors),
            'radius': 20
        }
        
    def aim_shooter(self, event):
        # Calculate angle to mouse
        dx = event.x - self.shooter_x
        dy = event.y - self.shooter_y
        self.shooter_angle = math.degrees(math.atan2(dy, dx))
        self.draw_game()
        
    def shoot_bubble(self, event):
        if self.current_bubble:
            # Create moving bubble
            angle_rad = math.radians(self.shooter_angle)
            speed = 10
            
            moving_bubble = {
                'x': self.shooter_x,
                'y': self.shooter_y,
                'dx': math.cos(angle_rad) * speed,
                'dy': math.sin(angle_rad) * speed,
                'color': self.current_bubble['color'],
                'radius': self.current_bubble['radius']
            }
            
            self.animate_bubble(moving_bubble)
            self.new_bubble()
            
    def animate_bubble(self, bubble):
        # Move bubble
        bubble['x'] += bubble['dx']
        bubble['y'] += bubble['dy']
        
        # Bounce off walls
        if bubble['x'] <= bubble['radius'] or bubble['x'] >= 600 - bubble['radius']:
            bubble['dx'] = -bubble['dx']
            
        # Check collision with existing bubbles
        collision = False
        for existing in self.bubbles:
            distance = math.sqrt((bubble['x'] - existing['x'])**2 + (bubble['y'] - existing['y'])**2)
            if distance < bubble['radius'] + existing['radius']:
                # Add bubble to field
                self.bubbles.append({
                    'x': bubble['x'],
                    'y': bubble['y'],
                    'color': bubble['color'],
                    'radius': bubble['radius']
                })
                collision = True
                self.check_matches(len(self.bubbles) - 1)
                break
                
        # Check if bubble reached top
        if bubble['y'] <= bubble['radius']:
            self.bubbles.append({
                'x': bubble['x'],
                'y': bubble['radius'],
                'color': bubble['color'],
                'radius': bubble['radius']
            })
            collision = True
            self.check_matches(len(self.bubbles) - 1)
            
        if not collision:
            self.draw_game()
            self.canvas.create_oval(
                bubble['x'] - bubble['radius'], bubble['y'] - bubble['radius'],
                bubble['x'] + bubble['radius'], bubble['y'] + bubble['radius'],
                fill=bubble['color'], outline="white"
            )
            self.frame.after(30, lambda: self.animate_bubble(bubble))
        else:
            self.draw_game()
            
    def check_matches(self, bubble_index):
        color = self.bubbles[bubble_index]['color']
        connected = self.find_connected_bubbles(bubble_index, color)
        
        if len(connected) >= 3:
            # Remove matched bubbles
            for i in sorted(connected, reverse=True):
                del self.bubbles[i]
            self.score += len(connected) * 10
            self.score_var.set(f"Score: {self.score}")
            
    def find_connected_bubbles(self, start_index, color):
        connected = {start_index}
        to_check = [start_index]
        
        while to_check:
            current = to_check.pop()
            current_bubble = self.bubbles[current]
            
            for i, bubble in enumerate(self.bubbles):
                if (i not in connected and bubble['color'] == color):
                    distance = math.sqrt(
                        (current_bubble['x'] - bubble['x'])**2 + 
                        (current_bubble['y'] - bubble['y'])**2
                    )
                    if distance < current_bubble['radius'] * 2.5:
                        connected.add(i)
                        to_check.append(i)
                        
        return connected
        
    def draw_game(self):
        self.canvas.delete("all")
        
        # Draw bubbles
        for bubble in self.bubbles:
            self.canvas.create_oval(
                bubble['x'] - bubble['radius'], bubble['y'] - bubble['radius'],
                bubble['x'] + bubble['radius'], bubble['y'] + bubble['radius'],
                fill=bubble['color'], outline="white"
            )
            
        # Draw shooter
        self.canvas.create_oval(
            self.shooter_x - 15, self.shooter_y - 15,
            self.shooter_x + 15, self.shooter_y + 15,
            fill="gray", outline="white"
        )
        
        # Draw current bubble
        if self.current_bubble:
            self.canvas.create_oval(
                self.shooter_x - 10, self.shooter_y - 25,
                self.shooter_x + 10, self.shooter_y - 5,
                fill=self.current_bubble['color'], outline="white"
            )
            
        # Draw aim line
        end_x = self.shooter_x + math.cos(math.radians(self.shooter_angle)) * 100
        end_y = self.shooter_y + math.sin(math.radians(self.shooter_angle)) * 100
        self.canvas.create_line(
            self.shooter_x, self.shooter_y, end_x, end_y,
            fill="white", dash=(5, 5)
        )


class SudokuApp(EmbeddedApplication):
    """Sudoku puzzle game"""
    
    def __init__(self, parent, example_name):
        super().__init__(parent, example_name)
        self.grid = [[0 for _ in range(9)] for _ in range(9)]
        self.solution = [[0 for _ in range(9)] for _ in range(9)]
        self.selected_cell = None
        
    def create_gui(self, container):
        self.frame = ttk.Frame(container, padding="10")
        
        # Title
        title = ttk.Label(self.frame, text="🔢 Sudoku", 
                         font=('Arial', 16, 'bold'))
        title.pack(pady=(0, 10))
        
        # Game canvas
        self.canvas = tk.Canvas(self.frame, width=450, height=450, bg="white")
        self.canvas.pack(pady=(0, 10))
        
        # Configure canvas for keyboard focus
        self.canvas.configure(takefocus=True)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<KeyPress>", self.key_pressed)
        
        # Add instructions for keyboard input
        ttk.Label(self.frame, text="Use keyboard numbers 1-9 to fill cells | Delete/Backspace to clear",
                 font=('Arial', 10)).pack(pady=(0, 10))
        
        # Number input buttons
        input_frame = ttk.Frame(self.frame)
        input_frame.pack()
        
        for i in range(1, 10):
            btn = ttk.Button(input_frame, text=str(i), width=4,
                           command=lambda n=i: self.input_number(n))
            btn.pack(side='left', padx=2)
            
        ttk.Button(input_frame, text="Clear", width=6,
                  command=lambda: self.input_number(0)).pack(side='left', padx=(10, 2))
        
        # Controls
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(control_frame, text="🎮 New Puzzle",
                  command=self.new_puzzle).pack(side='left')
        ttk.Button(control_frame, text="💡 Show Solution",
                  command=self.show_solution).pack(side='left', padx=(10, 0))
        ttk.Button(control_frame, text="✓ Check",
                  command=self.check_solution).pack(side='right')
        
        self.new_puzzle()
        return self.frame
        
    def new_puzzle(self):
        # Create a simple Sudoku puzzle (for demo purposes)
        self.solution = [
            [5,3,4,6,7,8,9,1,2],
            [6,7,2,1,9,5,3,4,8],
            [1,9,8,3,4,2,5,6,7],
            [8,5,9,7,6,1,4,2,3],
            [4,2,6,8,5,3,7,9,1],
            [7,1,3,9,2,4,8,5,6],
            [9,6,1,5,3,7,2,8,4],
            [2,8,7,4,1,9,6,3,5],
            [3,4,5,2,8,6,1,7,9]
        ]
        
        # Create puzzle by removing some numbers
        self.grid = [row[:] for row in self.solution]
        
        # Remove random numbers to create puzzle
        for _ in range(40):  # Remove 40 numbers
            row, col = random.randint(0, 8), random.randint(0, 8)
            self.grid[row][col] = 0
            
        self.selected_cell = None
        self.draw_grid()
        
    def draw_grid(self):
        self.canvas.delete("all")
        cell_size = 50
        
        for row in range(9):
            for col in range(9):
                x1, y1 = col * cell_size, row * cell_size
                x2, y2 = x1 + cell_size, y1 + cell_size
                
                # Highlight selected cell
                if self.selected_cell == (row, col):
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="lightblue", outline="black")
                else:
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="black")
                
                # Draw number
                if self.grid[row][col] != 0:
                    self.canvas.create_text(x1 + cell_size//2, y1 + cell_size//2,
                                          text=str(self.grid[row][col]),
                                          font=('Arial', 16, 'bold'))
          # Draw thick lines for 3x3 boxes
        for i in range(0, 10, 3):
            self.canvas.create_line(i * cell_size, 0, i * cell_size, 450, width=3)
            self.canvas.create_line(0, i * cell_size, 450, i * cell_size, width=3)
            
    def on_click(self, event):
        cell_size = 50
        col = event.x // cell_size
        row = event.y // cell_size
        
        if 0 <= row < 9 and 0 <= col < 9:
            self.selected_cell = (row, col)
            self.draw_grid()
            self.canvas.focus_set()  # Ensure canvas has focus for keyboard input
            
    def input_number(self, number):
        if self.selected_cell:
            row, col = self.selected_cell
            # Check if this cell was part of the original puzzle
            if not self.is_original_cell(row, col):
                self.grid[row][col] = number
                self.draw_grid()
                
    def key_pressed(self, event):
        """Handle keyboard number input"""
        key = event.keysym
        
        # Allow only number keys 1-9 and Delete/BackSpace for clearing
        if key in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
            if self.selected_cell:
                row, col = self.selected_cell
                if not self.is_original_cell(row, col):
                    self.grid[row][col] = int(key)
                    self.draw_grid()
        elif key in ['BackSpace', 'Delete', '0']:
            if self.selected_cell:
                row, col = self.selected_cell
                if not self.is_original_cell(row, col):
                    self.grid[row][col] = 0
                    self.draw_grid()
                    
    def is_original_cell(self, row, col):
        """Check if the cell was part of the original puzzle"""
        # Simplified check to prevent modification of original puzzle cells
        # In a real implementation, would check against the original puzzle state
        return self.solution[row][col] == self.grid[row][col] and self.grid[row][col] != 0
            
    def show_solution(self):
        self.grid = [row[:] for row in self.solution]
        self.draw_grid()
        
    def check_solution(self):
        if self.grid == self.solution:
            messagebox.showinfo("Congratulations!", "Puzzle solved correctly!")
        else:
            messagebox.showinfo("Not quite", "Keep trying! Some numbers are incorrect.")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = SonaExampleLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()