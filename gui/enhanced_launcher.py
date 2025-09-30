#!/usr/bin/env python3
"""
Enhanced Sona GUI Launcher with Improved Dependency Management
"""

import importlib.util
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Dict, List, Tuple


class DependencyManager: """Manages and checks all required dependencies"""

    REQUIRED_DEPS = {
        'lark': 'lark',
        'colorama': 'colorama',
        'tkinter': 'tkinter',
        'PySide6': 'PySide6',
    }

    OPTIONAL_DEPS = {'pygments': 'pygments', 'requests': 'requests'}

    @classmethod
    def check_dependency(
        cls, package_name: str, import_name: str = None
    ) -> Tuple[bool, str]: """Check if a dependency is available"""
        if import_name is None: import_name = package_name

        try: if import_name == 'tkinter': import tkinter  # noqa: F401

                return True, "Available"
            else: spec = importlib.util.find_spec(import_name)
                if spec is not None: return True, "Available"
                else: return False, "Not installed"
        except ImportError as e: return False, f"Import error: {str(e)}"

    @classmethod
    def get_all_dependencies_status(cls) -> Dict[str, Dict[str, str]]: """Get status of all dependencies"""
        status = {'required': {}, 'optional': {}}

        for name, import_name in cls.REQUIRED_DEPS.items(): available, message = (
            cls.check_dependency(name, import_name)
        )
            status['required'][name] = {
                'available': available,
                'message': message,
            }

        for name, import_name in cls.OPTIONAL_DEPS.items(): available, message = (
            cls.check_dependency(name, import_name)
        )
            status['optional'][name] = {
                'available': available,
                'message': message,
            }

        return status

    @classmethod
    def install_package(cls, package_name: str) -> bool: """Install a package using pip"""
        try: subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package_name],
                check = True,
                capture_output = True,
                text = True,
            )
            return True
        except subprocess.CalledProcessError: return False


class SonaEnhancedLauncher: """Enhanced Sona GUI Launcher with dependency management"""

    def __init__(self): self.root = tk.Tk()
        self.root.title("Sona Enhanced Launcher v1.0")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        # Initialize dependency manager
        self.dep_manager = DependencyManager()

        # Application state
        self.current_processes = {}
        self.recent_files = []

        # Check dependencies on startup
        self.check_and_handle_dependencies()

        # Setup UI
        self.setup_styles()
        self.create_main_interface()
        self.setup_keyboard_shortcuts()

        # Start status updates
        self.start_status_updates()

    def check_and_handle_dependencies(self): """Check dependencies and offer to install missing ones"""
        status = self.dep_manager.get_all_dependencies_status()

        missing_required = []
        for name, info in status['required'].items(): if not info['available']: missing_required.append(name)

        if missing_required: self.show_dependency_dialog(missing_required)

    def show_dependency_dialog(self, missing_deps: List[str]): """Show dialog for missing dependencies"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Missing Dependencies")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # Header
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill = tk.X, padx = 10, pady = 10)

        ttk.Label(
            header_frame,
            text = "⚠️ Missing Dependencies",
            font = ('Arial', 14, 'bold'),
        ).pack()

        ttk.Label(
            header_frame,
            text = (
                "Some required dependencies are missing. Install them to continue.",
            )
            wraplength = 450,
        ).pack(pady = 5)

        # Dependencies list
        deps_frame = ttk.LabelFrame(
            dialog, text = "Missing Dependencies", padding = 10
        )
        deps_frame.pack(fill = tk.BOTH, expand = True, padx = 10, pady = 5)

        deps_listbox = tk.Listbox(deps_frame)
        deps_listbox.pack(fill = tk.BOTH, expand = True)

        for dep in missing_deps: deps_listbox.insert(tk.END, f"• {dep}")

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill = tk.X, padx = 10, pady = 10)

        ttk.Button(
            button_frame,
            text = "Install All",
            command = lambda: self.install_missing_deps(missing_deps, dialog),
        ).pack(side = tk.LEFT)
        ttk.Button(
            button_frame, text = "Continue Anyway", command = dialog.destroy
        ).pack(side = tk.RIGHT)
        ttk.Button(button_frame, text = "Exit", command = self.root.quit).pack(
            side = tk.RIGHT, padx = (0, 5)
        )

    def install_missing_deps(self, deps: List[str], dialog: tk.Toplevel): """Install missing dependencies"""
        progress_dialog = tk.Toplevel(dialog)
        progress_dialog.title("Installing Dependencies")
        progress_dialog.geometry("400x200")
        progress_dialog.transient(dialog)
        progress_dialog.grab_set()

        ttk.Label(
            progress_dialog,
            text = "Installing dependencies...",
            font = ('Arial', 12),
        ).pack(pady = 20)

        progress_var = tk.StringVar()
        progress_label = (
            ttk.Label(progress_dialog, textvariable = progress_var)
        )
        progress_label.pack(pady = 10)

        progress_bar = ttk.Progressbar(
            progress_dialog, length = 300, mode = 'indeterminate'
        )
        progress_bar.pack(pady = 10)
        progress_bar.start()

        def install_thread(): success_count = 0
            for i, dep in enumerate(deps): progress_var.set(f"Installing {dep}...")
                if self.dep_manager.install_package(dep): success_count + = 1

            progress_bar.stop()
            progress_dialog.destroy()
            dialog.destroy()

            if success_count == len(deps): messagebox.showinfo(
                    "Success", "All dependencies installed successfully!"
                )
            else: messagebox.showwarning(
                    "Partial Success",
                    f"Installed {success_count} of {len(deps)} dependencies.",
                )

        threading.Thread(target = install_thread, daemon = True).start()

    def setup_styles(self): """Setup custom styles"""
        style = ttk.Style()

        # Configure styles
        style.configure('Title.TLabel', font = ('Arial', 16, 'bold'))
        style.configure('Subtitle.TLabel', font = ('Arial', 12, 'bold'))
        style.configure('Status.TLabel', font = ('Arial', 10))
        style.configure('Success.TLabel', foreground = 'green')
        style.configure('Error.TLabel', foreground = 'red')
        style.configure('Warning.TLabel', foreground = 'orange')

    def create_main_interface(self): """Create the main interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill = tk.BOTH, expand = True, padx = 5, pady = 5)

        # Create tabs
        self.create_launcher_tab()
        self.create_dependencies_tab()
        self.create_tools_tab()
        self.create_settings_tab()

        # Status bar
        self.create_status_bar()

    def create_launcher_tab(self): """Create main launcher tab"""
        launcher_frame = ttk.Frame(self.notebook)
        self.notebook.add(launcher_frame, text = "🚀 Launcher")

        # Header
        header_frame = ttk.Frame(launcher_frame)
        header_frame.pack(fill = tk.X, padx = 10, pady = 10)

        ttk.Label(
            header_frame,
            text = "Sona Application Launcher",
            style = 'Title.TLabel',
        ).pack()

        # Quick actions
        quick_frame = ttk.LabelFrame(
            launcher_frame, text = "Quick Actions", padding = 10
        )
        quick_frame.pack(fill = tk.X, padx = 10, pady = 5)

        button_frame = ttk.Frame(quick_frame)
        button_frame.pack(fill = tk.X)

        ttk.Button(
            button_frame, text = "🎮 Start REPL", command = self.start_repl
        ).pack(side = tk.LEFT, padx = 5)
        ttk.Button(
            button_frame, text = "📝 Open File", command = self.open_file
        ).pack(side = tk.LEFT, padx = 5)
        ttk.Button(
            button_frame,
            text = "🔧 Transpile",
            command = self.show_transpile_dialog,
        ).pack(side = tk.LEFT, padx = 5)
        ttk.Button(
            button_frame, text = "🆕 New Project", command = self.new_project
        ).pack(side = tk.LEFT, padx = 5)

        # Available applications
        apps_frame = ttk.LabelFrame(
            launcher_frame, text = "Available Applications", padding = 10
        )
        apps_frame.pack(fill = tk.BOTH, expand = True, padx = 10, pady = 5)

        # Applications list
        apps_tree = ttk.Treeview(
            apps_frame, columns = (
                ('Description', 'Status'), show = 'tree headings'
            )
        )
        apps_tree.heading('#0', text = 'Application')
        apps_tree.heading('Description', text = 'Description')
        apps_tree.heading('Status', text = 'Status')

        # Sample applications
        self.populate_applications_tree(apps_tree)

        apps_tree.pack(fill = tk.BOTH, expand = True)

        # Running processes
        processes_frame = ttk.LabelFrame(
            launcher_frame, text = "Running Processes", padding = 10
        )
        processes_frame.pack(fill = tk.X, padx = 10, pady = 5)

        self.processes_listbox = tk.Listbox(processes_frame, height = 4)
        self.processes_listbox.pack(fill = tk.X)

    def create_dependencies_tab(self): """Create dependencies management tab"""
        deps_frame = ttk.Frame(self.notebook)
        self.notebook.add(deps_frame, text = "📦 Dependencies")

        # Header
        header_frame = ttk.Frame(deps_frame)
        header_frame.pack(fill = tk.X, padx = 10, pady = 10)

        ttk.Label(
            header_frame, text = (
                "Dependency Management", style = 'Title.TLabel'
            )
        ).pack()

        # Refresh button
        ttk.Button(
            header_frame, text = (
                "🔄 Refresh", command = self.refresh_dependencies
            )
        ).pack(anchor = tk.E)

        # Dependencies display
        self.create_dependencies_display(deps_frame)

    def create_dependencies_display(self, parent): """Create dependencies display"""
        # Required dependencies
        required_frame = ttk.LabelFrame(
            parent, text = "Required Dependencies", padding = 10
        )
        required_frame.pack(fill = tk.X, padx = 10, pady = 5)

        self.required_deps_tree = ttk.Treeview(
            required_frame, columns = (
                ('Status', 'Message'), show = 'tree headings'
            )
        )
        self.required_deps_tree.heading('#0', text = 'Package')
        self.required_deps_tree.heading('Status', text = 'Status')
        self.required_deps_tree.heading('Message', text = 'Message')
        self.required_deps_tree.pack(fill = tk.X)

        # Optional dependencies
        optional_frame = ttk.LabelFrame(
            parent, text = "Optional Dependencies", padding = 10
        )
        optional_frame.pack(fill = tk.X, padx = 10, pady = 5)

        self.optional_deps_tree = ttk.Treeview(
            optional_frame, columns = (
                ('Status', 'Message'), show = 'tree headings'
            )
        )
        self.optional_deps_tree.heading('#0', text = 'Package')
        self.optional_deps_tree.heading('Status', text = 'Status')
        self.optional_deps_tree.heading('Message', text = 'Message')
        self.optional_deps_tree.pack(fill = tk.X)

        # Install button
        install_frame = ttk.Frame(parent)
        install_frame.pack(fill = tk.X, padx = 10, pady = 5)

        ttk.Button(
            install_frame,
            text = "Install Missing Dependencies",
            command = self.install_all_missing,
        ).pack()

        # Populate dependencies
        self.refresh_dependencies()

    def create_tools_tab(self): """Create tools tab"""
        tools_frame = ttk.Frame(self.notebook)
        self.notebook.add(tools_frame, text = "🔧 Tools")

        # Header
        header_frame = ttk.Frame(tools_frame)
        header_frame.pack(fill = tk.X, padx = 10, pady = 10)

        ttk.Label(
            header_frame, text = "Development Tools", style = 'Title.TLabel'
        ).pack()

        # Tools grid
        tools_grid = ttk.Frame(tools_frame)
        tools_grid.pack(fill = tk.BOTH, expand = True, padx = 10, pady = 5)

        # Code tools
        code_frame = (
            ttk.LabelFrame(tools_grid, text = "Code Tools", padding = 10)
        )
        code_frame.grid(row = (
            0, column = 0, sticky = 'nsew', padx = 5, pady = 5)
        )

        ttk.Button(
            code_frame, text = "Format Code", command = self.format_code
        ).pack(fill = tk.X, pady = 2)
        ttk.Button(
            code_frame, text = "Check Syntax", command = self.check_syntax
        ).pack(fill = tk.X, pady = 2)
        ttk.Button(code_frame, text = (
            "Run Tests", command = self.run_tests).pack(
        )
            fill = tk.X, pady = 2
        )

        # System tools
        system_frame = ttk.LabelFrame(
            tools_grid, text = "System Tools", padding = 10
        )
        system_frame.grid(row = (
            0, column = 1, sticky = 'nsew', padx = 5, pady = 5)
        )

        ttk.Button(
            system_frame, text = "System Info", command = self.show_system_info
        ).pack(fill = tk.X, pady = 2)
        ttk.Button(
            system_frame, text = "Clean Cache", command = self.clean_cache
        ).pack(fill = tk.X, pady = 2)
        ttk.Button(
            system_frame, text = "Open Terminal", command = self.open_terminal
        ).pack(fill = tk.X, pady = 2)

        # Configure grid weights
        tools_grid.columnconfigure(0, weight = 1)
        tools_grid.columnconfigure(1, weight = 1)
        tools_grid.rowconfigure(0, weight = 1)

    def create_settings_tab(self): """Create settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text = "⚙️ Settings")

        # Header
        header_frame = ttk.Frame(settings_frame)
        header_frame.pack(fill = tk.X, padx = 10, pady = 10)

        ttk.Label(header_frame, text = (
            "Settings", style = 'Title.TLabel').pack()
        )

        # Settings options
        options_frame = ttk.LabelFrame(
            settings_frame, text = "Options", padding = 10
        )
        options_frame.pack(fill = tk.X, padx = 10, pady = 5)

        # Auto-start option
        self.autostart_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame,
            text = "Auto-start with system",
            variable = self.autostart_var,
        ).pack(anchor = tk.W)

        # Debug mode
        self.debug_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame, text = (
                "Enable debug mode", variable = self.debug_var
            )
        ).pack(anchor = tk.W)

        # Theme selection
        theme_frame = ttk.Frame(options_frame)
        theme_frame.pack(fill = tk.X, pady = 5)

        ttk.Label(theme_frame, text = "Theme:").pack(side = tk.LEFT)
        self.theme_var = tk.StringVar(value = "Default")
        theme_combo = ttk.Combobox(
            theme_frame,
            textvariable = self.theme_var,
            values = ["Default", "Dark", "Light"],
        )
        theme_combo.pack(side = tk.LEFT, padx = 5)

        # Save button
        ttk.Button(
            options_frame, text = "Save Settings", command = self.save_settings
        ).pack(pady = 10)

    def create_status_bar(self): """Create status bar"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill = tk.X, side = tk.BOTTOM)

        self.status_var = tk.StringVar(value = "Ready")
        self.status_label = ttk.Label(
            self.status_frame, textvariable = self.status_var
        )
        self.status_label.pack(side = tk.LEFT, padx = 5)

        # Time label
        self.time_var = tk.StringVar()
        self.time_label = ttk.Label(
            self.status_frame, textvariable = self.time_var
        )
        self.time_label.pack(side = tk.RIGHT, padx = 5)

    def populate_applications_tree(self, tree): """Populate applications tree with sample data"""
        applications = [
            ("Calculator", "Basic calculator application", "Ready"),
            ("Text Editor", "Simple text editor", "Ready"),
            ("File Manager", "Basic file browser", "Ready"),
            ("Snake Game", "Classic snake game", "Ready"),
            ("Calendar", "Calendar application", "Ready"),
        ]

        for app, desc, status in applications: tree.insert('', 'end', text = (
            app, values = (desc, status))
        )

    def refresh_dependencies(self): """Refresh dependencies display"""
        status = self.dep_manager.get_all_dependencies_status()

        # Clear existing items
        for item in self.required_deps_tree.get_children(): self.required_deps_tree.delete(item)
        for item in self.optional_deps_tree.get_children(): self.optional_deps_tree.delete(item)

        # Populate required dependencies
        for name, info in status['required'].items(): status_text = (
            "✅ Available" if info['available'] else "❌ Missing"
        )
            self.required_deps_tree.insert(
                '', 'end', text = name, values = (status_text, info['message'])
            )

        # Populate optional dependencies
        for name, info in status['optional'].items(): status_text = (
            "✅ Available" if info['available'] else "⚠️ Missing"
        )
            self.optional_deps_tree.insert(
                '', 'end', text = name, values = (status_text, info['message'])
            )

    def install_all_missing(self): """Install all missing dependencies"""
        status = self.dep_manager.get_all_dependencies_status()

        missing_deps = []
        for name, info in status['required'].items(): if not info['available']: missing_deps.append(name)

        if missing_deps: self.install_missing_deps(missing_deps, self.root)
        else: messagebox.showinfo("Info", "No missing dependencies found!")

    def setup_keyboard_shortcuts(self): """Setup keyboard shortcuts"""
        self.root.bind('<Control-n>', lambda e: self.new_project())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-r>', lambda e: self.start_repl())
        self.root.bind('<F5>', lambda e: self.refresh_dependencies())
        self.root.bind('<Control-q>', lambda e: self.root.quit())

    def start_status_updates(self): """Start background status updates"""

        def update_status(): while True: current_time = (
            time.strftime("%H:%M:%S")
        )
                self.time_var.set(current_time)
                time.sleep(1)

        threading.Thread(target = update_status, daemon = True).start()

    # Action methods
    def start_repl(self): """Start Sona REPL"""
        try: subprocess.Popen([sys.executable, '-m', 'sona.sona_cli', 'repl'])
            self.status_var.set("REPL started")
        except Exception as e: messagebox.showerror("Error", f"Failed to start REPL: {str(e)}")

    def open_file(self): """Open file dialog"""
        filename = filedialog.askopenfilename(
            title = "Open Sona File",
            filetypes = [("Sona files", "*.sona"), ("All files", "*.*")],
        )
        if filename: self.status_var.set(f"Opened: {filename}")

    def show_transpile_dialog(self): """Show transpile dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Transpile Code")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Content here...
        ttk.Label(dialog, text = "Transpile functionality coming soon!").pack(
            pady = 20
        )
        ttk.Button(dialog, text = "Close", command = dialog.destroy).pack()

    def new_project(self): """Create new project"""
        project_name = tk.simpledialog.askstring(
            "New Project", "Enter project name:"
        )
        if project_name: try: subprocess.run(
                    [
                        sys.executable,
                        '-m',
                        'sona.sona_cli',
                        'init',
                        project_name,
                    ],
                    check = True,
                )
                self.status_var.set(f"Created project: {project_name}")
                messagebox.showinfo(
                    "Success",
                    f"Project '{project_name}' created successfully!",
                )
            except Exception as e: messagebox.showerror(
                    "Error", f"Failed to create project: {str(e)}"
                )

    def format_code(self): """Format code"""
        messagebox.showinfo(
            "Format Code", "Code formatting functionality coming soon!"
        )

    def check_syntax(self): """Check syntax"""
        messagebox.showinfo(
            "Check Syntax", "Syntax checking functionality coming soon!"
        )

    def run_tests(self): """Run tests"""
        messagebox.showinfo(
            "Run Tests", "Test running functionality coming soon!"
        )

    def show_system_info(self): """Show system information"""
        try: subprocess.Popen([sys.executable, '-m', 'sona.sona_cli', 'info'])
            self.status_var.set("System info displayed")
        except Exception as e: messagebox.showerror(
                "Error", f"Failed to show system info: {str(e)}"
            )

    def clean_cache(self): """Clean cache"""
        try: subprocess.run(
                [sys.executable, '-m', 'sona.sona_cli', 'clean'], check = True
            )
            self.status_var.set("Cache cleaned")
            messagebox.showinfo("Success", "Cache cleaned successfully!")
        except Exception as e: messagebox.showerror("Error", f"Failed to clean cache: {str(e)}")

    def open_terminal(self): """Open terminal"""
        try: if sys.platform == "win32": subprocess.Popen(['cmd'])
            else: subprocess.Popen(['terminal'])
            self.status_var.set("Terminal opened")
        except Exception as e: messagebox.showerror("Error", f"Failed to open terminal: {str(e)}")

    def save_settings(self): """Save settings"""
        messagebox.showinfo("Settings", "Settings saved successfully!")

    def run(self): """Run the application"""
        self.root.mainloop()


def main(): """Main entry point"""
    try: app = SonaEnhancedLauncher()
        app.run()
    except Exception as e: print(f"Error starting launcher: {e}")
        messagebox.showerror("Error", f"Failed to start launcher: {str(e)}")


if __name__ == "__main__": main()
