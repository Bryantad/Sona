#!/usr/bin/env python3
"""
Sona Application Framework - Core Infrastructure
Provides the foundation for creating and managing Sona GUI applications
"""

import tkinter as tk
from tkinter import ttk
import threading
import subprocess
import queue
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import uuid


class AppState(Enum):
    """Application lifecycle states"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class WindowMode(Enum):
    """Application window display modes"""
    EMBEDDED = "embedded"
    FLOATING = "floating"
    DOCKED = "docked"
    FULLSCREEN = "fullscreen"


@dataclass
class AppCapabilities:
    """Declares what capabilities an application provides"""
    name: str
    category: str
    description: str
    version: str
    author: str
    requires_sona: str
    window_modes: List[WindowMode]
    has_menu: bool = False
    has_toolbar: bool = False
    has_statusbar: bool = False
    can_save_state: bool = False
    supports_themes: bool = True
    min_width: int = 400
    min_height: int = 300
    preferred_width: int = 800
    preferred_height: int = 600


@dataclass
class AppInstance:
    """Represents a running application instance"""
    id: str
    capabilities: AppCapabilities
    state: AppState
    window_mode: WindowMode
    process: Optional[subprocess.Popen] = None
    widget_container: Optional[tk.Widget] = None
    window: Optional[tk.Toplevel] = None
    last_heartbeat: float = 0
    startup_time: float = 0
    resource_usage: Dict[str, Any] = None


class ApplicationFramework:
    """Core framework for managing Sona GUI applications"""
    
    def __init__(self, parent_widget: tk.Widget):
        self.parent = parent_widget
        self.running_apps: Dict[str, AppInstance] = {}
        self.app_registry: Dict[str, AppCapabilities] = {}
        self.message_queue = queue.Queue()
        self.resource_monitor = ResourceMonitor()
        self.theme_manager = ThemeManager()
        
        # Start background monitoring
        self.monitoring_thread = threading.Thread(target=self._monitor_apps, daemon=True)
        self.monitoring_thread.start()
        
        # Register built-in applications
        self._register_builtin_apps()
    
    def _register_builtin_apps(self):
        """Register the built-in applications"""
        apps = [
            AppCapabilities(
                name="Calculator",
                category="Productivity",
                description="Scientific calculator with graphing capabilities",
                version="1.0.0",
                author="Sona Team",
                requires_sona="0.7.0",
                window_modes=[WindowMode.EMBEDDED, WindowMode.FLOATING, WindowMode.DOCKED],
                has_menu=True,
                has_toolbar=True,
                can_save_state=True,
                preferred_width=400,
                preferred_height=500
            ),
            AppCapabilities(
                name="Snake Game",
                category="Games",
                description="Classic snake game with multiplayer support",
                version="1.0.0",
                author="Sona Team",
                requires_sona="0.7.0",
                window_modes=[WindowMode.EMBEDDED, WindowMode.FLOATING, WindowMode.FULLSCREEN],
                has_menu=True,
                has_statusbar=True,
                can_save_state=True,
                preferred_width=600,
                preferred_height=500
            ),
            AppCapabilities(
                name="Calendar",
                category="Productivity",
                description="Full-featured calendar with event management",
                version="1.0.0",
                author="Sona Team",
                requires_sona="0.7.0",
                window_modes=[WindowMode.EMBEDDED, WindowMode.FLOATING, WindowMode.DOCKED],
                has_menu=True,
                has_toolbar=True,
                has_statusbar=True,
                can_save_state=True,
                preferred_width=800,
                preferred_height=600
            ),
            AppCapabilities(
                name="Todo Manager",
                category="Productivity",
                description="Advanced task management with projects and priorities",
                version="1.0.0",
                author="Sona Team",
                requires_sona="0.7.0",
                window_modes=[WindowMode.EMBEDDED, WindowMode.FLOATING, WindowMode.DOCKED],
                has_menu=True,
                has_toolbar=True,
                has_statusbar=True,
                can_save_state=True,
                preferred_width=700,
                preferred_height=500
            ),
            AppCapabilities(
                name="Text Editor",
                category="Development",
                description="Advanced text editor with syntax highlighting",
                version="1.0.0",
                author="Sona Team",
                requires_sona="0.7.0",
                window_modes=[WindowMode.EMBEDDED, WindowMode.FLOATING, WindowMode.DOCKED],
                has_menu=True,
                has_toolbar=True,
                has_statusbar=True,
                can_save_state=True,
                preferred_width=800,
                preferred_height=600
            ),
            AppCapabilities(
                name="File Manager",
                category="System",
                description="File browser with preview capabilities",
                version="1.0.0",
                author="Sona Team",
                requires_sona="0.7.0",
                window_modes=[WindowMode.EMBEDDED, WindowMode.FLOATING, WindowMode.DOCKED],
                has_menu=True,
                has_toolbar=True,
                has_statusbar=True,
                preferred_width=900,
                preferred_height=600
            )
        ]
        
        for app in apps:
            self.app_registry[app.name] = app
    
    def get_available_apps(self) -> List[AppCapabilities]:
        """Get list of all available applications"""
        return list(self.app_registry.values())
    
    def get_apps_by_category(self) -> Dict[str, List[AppCapabilities]]:
        """Get applications organized by category"""
        categories = {}
        for app in self.app_registry.values():
            if app.category not in categories:
                categories[app.category] = []
            categories[app.category].append(app)
        return categories
    
    def launch_app(self, app_name: str, window_mode: WindowMode = WindowMode.EMBEDDED) -> Optional[str]:
        """Launch an application and return its instance ID"""
        if app_name not in self.app_registry:
            raise ValueError(f"Application '{app_name}' not found in registry")
        
        capabilities = self.app_registry[app_name]
        
        # Check if window mode is supported
        if window_mode not in capabilities.window_modes:
            window_mode = capabilities.window_modes[0]  # Use first supported mode
        
        # Create application instance
        instance_id = str(uuid.uuid4())
        instance = AppInstance(
            id=instance_id,
            capabilities=capabilities,
            state=AppState.INITIALIZING,
            window_mode=window_mode,
            startup_time=time.time()
        )
        
        try:
            # Create the application widget/window
            if window_mode == WindowMode.FLOATING:
                instance.window = self._create_floating_window(instance)
            elif window_mode == WindowMode.EMBEDDED:
                instance.widget_container = self._create_embedded_container(instance)
            elif window_mode == WindowMode.DOCKED:
                instance.widget_container = self._create_docked_container(instance)
            elif window_mode == WindowMode.FULLSCREEN:
                instance.window = self._create_fullscreen_window(instance)
            
            # Initialize the actual application content
            self._initialize_app_content(instance)
            
            instance.state = AppState.RUNNING
            instance.last_heartbeat = time.time()
            
            self.running_apps[instance_id] = instance
            
            return instance_id
            
        except Exception as e:
            instance.state = AppState.ERROR
            print(f"Error launching {app_name}: {e}")
            return None
    
    def close_app(self, instance_id: str):
        """Close a running application"""
        if instance_id not in self.running_apps:
            return
        
        instance = self.running_apps[instance_id]
        instance.state = AppState.STOPPING
        
        try:
            # Save state if supported
            if instance.capabilities.can_save_state:
                self._save_app_state(instance)
            
            # Clean up GUI components
            if instance.window:
                instance.window.destroy()
            elif instance.widget_container:
                instance.widget_container.destroy()
            
            # Clean up process if any
            if instance.process:
                instance.process.terminate()
            
            instance.state = AppState.STOPPED
            
        except Exception as e:
            print(f"Error closing app {instance.capabilities.name}: {e}")
            instance.state = AppState.ERROR
        
        finally:
            del self.running_apps[instance_id]
    
    def get_running_apps(self) -> List[AppInstance]:
        """Get list of currently running applications"""
        return list(self.running_apps.values())
    
    def get_app_instance(self, instance_id: str) -> Optional[AppInstance]:
        """Get specific application instance"""
        return self.running_apps.get(instance_id)
    
    def _create_floating_window(self, instance: AppInstance) -> tk.Toplevel:
        """Create a floating window for the application"""
        window = tk.Toplevel(self.parent)
        window.title(instance.capabilities.name)
        window.geometry(f"{instance.capabilities.preferred_width}x{instance.capabilities.preferred_height}")
        window.minsize(instance.capabilities.min_width, instance.capabilities.min_height)
        
        # Apply theme
        self.theme_manager.apply_theme(window)
        
        return window
    
    def _create_embedded_container(self, instance: AppInstance) -> tk.Widget:
        """Create an embedded container for the application"""
        container = ttk.Frame(self.parent)
        container.pack(fill=tk.BOTH, expand=True)
        
        return container
    
    def _create_docked_container(self, instance: AppInstance) -> tk.Widget:
        """Create a docked container for the application"""
        # This would integrate with a docking system
        container = ttk.Frame(self.parent)
        container.pack(fill=tk.BOTH, expand=True)
        
        return container
    
    def _create_fullscreen_window(self, instance: AppInstance) -> tk.Toplevel:
        """Create a fullscreen window for the application"""
        window = tk.Toplevel(self.parent)
        window.title(instance.capabilities.name)
        window.attributes('-fullscreen', True)
        
        # Apply theme
        self.theme_manager.apply_theme(window)
        
        return window
    
    def _initialize_app_content(self, instance: AppInstance):
        """Initialize the actual application content"""
        app_name = instance.capabilities.name
        container = instance.window or instance.widget_container
        
        if app_name == "Calculator":
            self._create_calculator_app(container, instance)
        elif app_name == "Snake Game":
            self._create_snake_game_app(container, instance)
        elif app_name == "Calendar":
            self._create_calendar_app(container, instance)
        elif app_name == "Todo Manager":
            self._create_todo_app(container, instance)
        elif app_name == "Text Editor":
            self._create_text_editor_app(container, instance)
        elif app_name == "File Manager":
            self._create_file_manager_app(container, instance)
    
    def _create_calculator_app(self, container: tk.Widget, instance: AppInstance):
        """Create calculator application content"""
        from .calculator_app import CalculatorApp
        app = CalculatorApp(container, instance, self)
        
    def _create_snake_game_app(self, container: tk.Widget, instance: AppInstance):
        """Create snake game application content"""
        from .snake_app import SnakeGameApp
        app = SnakeGameApp(container, instance, self)
        
    def _create_calendar_app(self, container: tk.Widget, instance: AppInstance):
        """Create calendar application content"""
        from .calendar_app import CalendarApp
        app = CalendarApp(container, instance, self)
        
    def _create_todo_app(self, container: tk.Widget, instance: AppInstance):
        """Create todo manager application content"""
        from .todo_app import TodoManagerApp
        app = TodoManagerApp(container, instance, self)
        
    def _create_text_editor_app(self, container: tk.Widget, instance: AppInstance):
        """Create text editor application content"""
        from .text_editor_app import TextEditorApp
        app = TextEditorApp(container, instance, self)
        
    def _create_file_manager_app(self, container: tk.Widget, instance: AppInstance):
        """Create file manager application content"""
        from .file_manager_app import FileManagerApp
        app = FileManagerApp(container, instance, self)
    
    def _monitor_apps(self):
        """Background monitoring of running applications"""
        while True:
            try:
                current_time = time.time()
                
                for instance_id, instance in list(self.running_apps.items()):
                    # Check for unresponsive apps
                    if current_time - instance.last_heartbeat > 30:  # 30 second timeout
                        print(f"App {instance.capabilities.name} appears unresponsive")
                        instance.state = AppState.ERROR
                    
                    # Update resource usage
                    instance.resource_usage = self.resource_monitor.get_app_resources(instance_id)
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"Error in app monitoring: {e}")
                time.sleep(5)
    
    def _save_app_state(self, instance: AppInstance):
        """Save application state for restoration"""
        state_dir = Path("gui/app_states")
        state_dir.mkdir(exist_ok=True)
        
        state_file = state_dir / f"{instance.capabilities.name}_{instance.id}.json"
        
        state_data = {
            "app_name": instance.capabilities.name,
            "window_mode": instance.window_mode.value,
            "timestamp": time.time(),
            # Additional app-specific state would be added by each app
        }
        
        with open(state_file, 'w') as f:
            json.dump(state_data, f)


class ResourceMonitor:
    """Monitors system resources used by applications"""
    
    def get_app_resources(self, instance_id: str) -> Dict[str, Any]:
        """Get resource usage for a specific app instance"""
        # Placeholder implementation
        return {
            "memory_mb": 50.0,
            "cpu_percent": 2.5,
            "threads": 3
        }


class ThemeManager:
    """Manages themes and styling for applications"""
    
    def __init__(self):
        self.current_theme = "dark"
        self.themes = {
            "dark": {
                "bg": "#2b2b2b",
                "fg": "#ffffff",
                "select_bg": "#404040",
                "select_fg": "#ffffff"
            },
            "light": {
                "bg": "#ffffff",
                "fg": "#000000", 
                "select_bg": "#e0e0e0",
                "select_fg": "#000000"
            }
        }
    
    def apply_theme(self, widget: tk.Widget):
        """Apply current theme to a widget"""
        theme = self.themes[self.current_theme]
        
        try:
            widget.configure(bg=theme["bg"], fg=theme["fg"])
        except tk.TclError:
            pass  # Some widgets don't support these options
    
    def set_theme(self, theme_name: str):
        """Change the current theme"""
        if theme_name in self.themes:
            self.current_theme = theme_name
