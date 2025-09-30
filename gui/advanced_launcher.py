#!/usr/bin/env python3
"""
Sona Advanced Application Launcher - Main GUI Application
A sophisticated application platform for Sona programming language
"""

import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import List

# Import framework components
from framework.app_framework import (
    AppCapabilities,
    ApplicationFramework,
    AppState,
    WindowMode,
)


class SonaApplicationLauncher:
    """Main launcher application with advanced features"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sona Application Platform v2.0")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Initialize framework
        self.app_framework = ApplicationFramework(self.root)
        
        # Application state
        self.current_workspace = "Default"
        self.running_apps_widgets = {}
        self.docked_panels = {}
        
        # Setup UI
        self.setup_styles()
        self.create_menu_bar()
        self.create_main_interface()
        self.setup_keyboard_shortcuts()
        
        # Start status updates
        self.start_status_updates()
        
        # Load saved workspace
        self.load_workspace()
    
    def setup_styles(self):
        """Configure application styles and themes"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Custom styles
        self.style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        self.style.configure('Subtitle.TLabel', font=('Arial', 10, 'bold'))
        self.style.configure('AppCard.TFrame', relief='raised', borderwidth=1)
        self.style.configure('Status.TLabel', font=('Arial', 8))
    
    def create_menu_bar(self):
        """Create comprehensive menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Workspace...", command=self.new_workspace)
        file_menu.add_command(label="Open Workspace...", command=self.open_workspace)
        file_menu.add_command(label="Save Workspace", command=self.save_workspace)
        file_menu.add_separator()
        file_menu.add_command(label="Import Application...", command=self.import_application)
        file_menu.add_command(label="Export Applications...", command=self.export_applications)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Applications menu
        apps_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Applications", menu=apps_menu)
        apps_menu.add_command(label="Refresh Registry", command=self.refresh_app_registry)
        apps_menu.add_command(label="Close All Apps", command=self.close_all_apps)
        apps_menu.add_separator()
        
        # Add quick launch options for each app
        categories = self.app_framework.get_apps_by_category()
        for category, apps in categories.items():
            category_menu = tk.Menu(apps_menu, tearoff=0)
            apps_menu.add_cascade(label=category, menu=category_menu)
            for app in apps:
                category_menu.add_command(
                    label=app.name,
                    command=lambda a=app.name: self.quick_launch_app(a)
                )
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Sidebar", command=self.toggle_sidebar)
        view_menu.add_command(label="Toggle Status Bar", command=self.toggle_status_bar)
        view_menu.add_separator()
        
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_command(label="Dark Theme", command=lambda: self.set_theme("dark"))
        theme_menu.add_command(label="Light Theme", command=lambda: self.set_theme("light"))
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Resource Monitor", command=self.show_resource_monitor)
        tools_menu.add_command(label="Application Manager", command=self.show_app_manager)
        tools_menu.add_command(label="Sona REPL", command=self.launch_sona_repl)
        tools_menu.add_separator()
        tools_menu.add_command(label="Preferences...", command=self.show_preferences)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.show_user_guide)
        help_menu.add_command(label="Developer Documentation", command=self.show_dev_docs)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="About Sona Platform", command=self.show_about)
    
    def create_main_interface(self):
        """Create the main application interface"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create paned window for resizable layout
        self.main_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left sidebar
        self.create_sidebar()
        
        # Main content area
        self.create_content_area()
        
        # Status bar
        self.create_status_bar()
    
    def create_sidebar(self):
        """Create application sidebar with categories"""
        sidebar_frame = ttk.Frame(self.main_paned, width=300)
        self.main_paned.add(sidebar_frame, weight=0)
        
        # Sidebar header
        header_frame = ttk.Frame(sidebar_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(header_frame, text="Application Launcher", 
                 style='Title.TLabel').pack()
        
        # Workspace selector
        workspace_frame = ttk.Frame(header_frame)
        workspace_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(workspace_frame, text="Workspace:").pack(side=tk.LEFT)
        self.workspace_var = tk.StringVar(value=self.current_workspace)
        workspace_combo = ttk.Combobox(workspace_frame, textvariable=self.workspace_var,
                                     values=["Default", "Development", "Games"])
        workspace_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        workspace_combo.bind('<<ComboboxSelected>>', self.on_workspace_change)
        
        # Application categories
        self.create_app_categories(sidebar_frame)
        
        # Running applications panel
        self.create_running_apps_panel(sidebar_frame)
    
    def create_app_categories(self, parent):
        """Create categorized application browser"""
        categories_frame = ttk.LabelFrame(parent, text="Available Applications", padding=5)
        categories_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create notebook for categories
        self.categories_notebook = ttk.Notebook(categories_frame)
        self.categories_notebook.pack(fill=tk.BOTH, expand=True)
        
        categories = self.app_framework.get_apps_by_category()
        
        for category, apps in categories.items():
            self.create_category_tab(category, apps)
    
    def create_category_tab(self, category: str, apps: List[AppCapabilities]):
        """Create a tab for a specific category"""
        tab_frame = ttk.Frame(self.categories_notebook)
        self.categories_notebook.add(tab_frame, text=category)
        
        # Scrollable frame for apps
        canvas = tk.Canvas(tab_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollable components
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add application cards
        for app in apps:
            self.create_app_card(scrollable_frame, app)
    
    def create_app_card(self, parent, app: AppCapabilities):
        """Create an application card widget"""
        card_frame = ttk.Frame(parent, style='AppCard.TFrame')
        card_frame.pack(fill=tk.X, padx=2, pady=2)
        
        # App info
        info_frame = ttk.Frame(card_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # App name and version
        title_frame = ttk.Frame(info_frame)
        title_frame.pack(fill=tk.X)
        
        ttk.Label(title_frame, text=app.name, 
                 style='Subtitle.TLabel').pack(side=tk.LEFT)
        ttk.Label(title_frame, text=f"v{app.version}", 
                 style='Status.TLabel').pack(side=tk.RIGHT)
        
        # Description
        ttk.Label(info_frame, text=app.description, 
                 wraplength=250).pack(fill=tk.X, pady=(2, 0))
        
        # Launch buttons
        button_frame = ttk.Frame(info_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Quick launch button
        launch_btn = ttk.Button(button_frame, text="Launch",
                               command=lambda: self.launch_app(app.name))
        launch_btn.pack(side=tk.LEFT)
        
        # Window mode selection
        if len(app.window_modes) > 1:
            mode_var = tk.StringVar(value=app.window_modes[0].value)
            mode_menu = ttk.Combobox(button_frame, textvariable=mode_var,
                                   values=[mode.value for mode in app.window_modes],
                                   width=10, state="readonly")
            mode_menu.pack(side=tk.RIGHT)
            
            # Advanced launch button
            adv_btn = ttk.Button(button_frame, text="⚙",
                               command=lambda: self.launch_app_with_mode(app.name, mode_var.get()))
            adv_btn.pack(side=tk.RIGHT, padx=(5, 0))
    
    def create_running_apps_panel(self, parent):
        """Create panel showing running applications"""
        running_frame = ttk.LabelFrame(parent, text="Running Applications", padding=5)
        running_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Scrollable listbox for running apps
        self.running_apps_listbox = tk.Listbox(running_frame, height=6)
        running_scrollbar = ttk.Scrollbar(running_frame, orient="vertical",
                                        command=self.running_apps_listbox.yview)
        self.running_apps_listbox.configure(yscrollcommand=running_scrollbar.set)
        
        self.running_apps_listbox.pack(side="left", fill="both", expand=True)
        running_scrollbar.pack(side="right", fill="y")
        
        # Context menu for running apps
        self.running_apps_menu = tk.Menu(self.root, tearoff=0)
        self.running_apps_menu.add_command(label="Bring to Front", command=self.bring_app_to_front)
        self.running_apps_menu.add_command(label="Minimize", command=self.minimize_app)
        self.running_apps_menu.add_command(label="Close", command=self.close_selected_app)
        
        self.running_apps_listbox.bind("<Button-3>", self.show_running_apps_menu)
        self.running_apps_listbox.bind("<Double-Button-1>", self.bring_app_to_front)
    
    def create_content_area(self):
        """Create main content area for embedded applications"""
        content_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(content_frame, weight=1)
        
        # Create notebook for tabbed applications
        self.content_notebook = ttk.Notebook(content_frame)
        self.content_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Welcome tab
        self.create_welcome_tab()
        
        # Bind tab events
        self.content_notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def create_welcome_tab(self):
        """Create welcome/dashboard tab"""
        welcome_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(welcome_frame, text="Dashboard")
        
        # Welcome content
        welcome_canvas = tk.Canvas(welcome_frame, bg='white')
        welcome_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Center content
        content_frame = ttk.Frame(welcome_canvas)
        welcome_canvas.create_window(700, 400, window=content_frame)
        
        # Welcome message
        ttk.Label(content_frame, text="Welcome to Sona Application Platform",
                 style='Title.TLabel').pack(pady=20)
        
        ttk.Label(content_frame, 
                 text="Launch applications from the sidebar or use the quick actions below.",
                 font=('Arial', 11)).pack(pady=10)
        
        # Quick action buttons
        quick_frame = ttk.Frame(content_frame)
        quick_frame.pack(pady=20)
        
        ttk.Button(quick_frame, text="Calculator", 
                  command=lambda: self.quick_launch_app("Calculator")).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_frame, text="Text Editor",
                  command=lambda: self.quick_launch_app("Text Editor")).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_frame, text="Calendar",
                  command=lambda: self.quick_launch_app("Calendar")).pack(side=tk.LEFT, padx=5)
        
        # Recent applications
        recent_frame = ttk.LabelFrame(content_frame, text="Recent Applications", padding=10)
        recent_frame.pack(pady=20, fill=tk.X)
        
        # Placeholder for recent apps
        ttk.Label(recent_frame, text="No recent applications").pack()
    
    def create_status_bar(self):
        """Create status bar with system information"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Status labels
        self.status_left = ttk.Label(self.status_frame, text="Ready")
        self.status_left.pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(self.status_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Running apps count
        self.apps_count_label = ttk.Label(self.status_frame, text="0 apps running")
        self.apps_count_label.pack(side=tk.LEFT, padx=5)
        
        # System resources
        self.memory_label = ttk.Label(self.status_frame, text="Memory: 0 MB")
        self.memory_label.pack(side=tk.RIGHT, padx=5)
        
        ttk.Separator(self.status_frame, orient='vertical').pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        
        # Time
        self.time_label = ttk.Label(self.status_frame, text="")
        self.time_label.pack(side=tk.RIGHT, padx=5)
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind('<Control-n>', lambda e: self.new_workspace())
        self.root.bind('<Control-o>', lambda e: self.open_workspace())
        self.root.bind('<Control-s>', lambda e: self.save_workspace())
        self.root.bind('<Control-q>', lambda e: self.on_closing())
        self.root.bind('<F1>', lambda e: self.show_user_guide())
        self.root.bind('<F5>', lambda e: self.refresh_app_registry())
        
        # App-specific shortcuts
        self.root.bind('<Control-1>', lambda e: self.quick_launch_app("Calculator"))
        self.root.bind('<Control-2>', lambda e: self.quick_launch_app("Text Editor"))
        self.root.bind('<Control-3>', lambda e: self.quick_launch_app("Calendar"))
    
    def launch_app(self, app_name: str, window_mode: str = "embedded"):
        """Launch an application"""
        try:
            mode = WindowMode(window_mode.lower())
            instance_id = self.app_framework.launch_app(app_name, mode)
            
            if instance_id:
                self.update_running_apps_display()
                self.status_left.config(text=f"Launched {app_name}")
                
                # If embedded, add to notebook
                if mode == WindowMode.EMBEDDED:
                    instance = self.app_framework.get_app_instance(instance_id)
                    if instance and instance.widget_container:
                        self.content_notebook.add(instance.widget_container, text=app_name)
                        self.content_notebook.select(instance.widget_container)
            else:
                messagebox.showerror("Error", f"Failed to launch {app_name}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error launching {app_name}: {str(e)}")
    
    def quick_launch_app(self, app_name: str):
        """Quick launch with default settings"""
        self.launch_app(app_name, "embedded")
    
    def launch_app_with_mode(self, app_name: str, mode: str):
        """Launch app with specific window mode"""
        self.launch_app(app_name, mode)
    
    def update_running_apps_display(self):
        """Update the running applications display"""
        self.running_apps_listbox.delete(0, tk.END)
        
        running_apps = self.app_framework.get_running_apps()
        for app in running_apps:
            status_icon = "●" if app.state == AppState.RUNNING else "○"
            self.running_apps_listbox.insert(tk.END, 
                f"{status_icon} {app.capabilities.name} ({app.window_mode.value})")
        
        # Update status bar
        self.apps_count_label.config(text=f"{len(running_apps)} apps running")
    
    def start_status_updates(self):
        """Start background status updates"""
        def update_status():
            while True:
                try:
                    # Update time
                    current_time = time.strftime("%H:%M:%S")
                    self.time_label.config(text=current_time)
                    
                    # Update running apps
                    self.update_running_apps_display()
                    
                    # Update memory usage
                    total_memory = sum(
                        app.resource_usage.get("memory_mb", 0) if app.resource_usage else 0
                        for app in self.app_framework.get_running_apps()
                    )
                    self.memory_label.config(text=f"Memory: {total_memory:.1f} MB")
                    
                except Exception as e:
                    print(f"Status update error: {e}")
                
                time.sleep(1)
        
        status_thread = threading.Thread(target=update_status, daemon=True)
        status_thread.start()
    
    # Placeholder methods for menu actions
    def new_workspace(self): pass
    def open_workspace(self): pass
    def save_workspace(self): pass
    def load_workspace(self): pass
    def import_application(self): pass
    def export_applications(self): pass
    def refresh_app_registry(self): pass
    def close_all_apps(self): pass
    def toggle_sidebar(self): pass
    def toggle_status_bar(self): pass
    def set_theme(self, theme: str): pass
    def show_resource_monitor(self): pass
    def show_app_manager(self): pass
    def launch_sona_repl(self): pass
    def show_preferences(self): pass
    def show_user_guide(self): pass
    def show_dev_docs(self): pass
    def show_shortcuts(self): pass
    def show_about(self): pass
    def on_workspace_change(self, event): pass
    def show_running_apps_menu(self, event): pass
    def bring_app_to_front(self): pass
    def minimize_app(self): pass
    def close_selected_app(self): pass
    def on_tab_changed(self, event): pass
    
    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Close all applications and exit?"):
            self.close_all_apps()
            self.root.quit()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = SonaApplicationLauncher(root)
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    # Handle closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    root.mainloop()


if __name__ == "__main__":
    main()
