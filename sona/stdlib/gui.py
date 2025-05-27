# Sona GUI Module - Tkinter Backend
# Provides comprehensive GUI capabilities for Sona applications

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import threading
import time
from typing import Dict, Any, Optional

class SonaGUIModule:
    """Main GUI module for Sona applications with modern Tkinter backend"""
    
    def __init__(self):
        self.windows = {}
        self.widgets = {}
        self.event_handlers = {}
        self.current_window_id = None
        self.widget_counter = 0
        self.running = False
        
    def create_window(self, title="Sona App", width=800, height=600, resizable=True):
        """Create a new window and return its ID"""
        window_id = f"window_{len(self.windows)}"
        
        root = tk.Tk()
        root.title(title)
        root.geometry(f"{width}x{height}")
        root.resizable(resizable, resizable)
        
        # Apply modern styling
        style = ttk.Style()
        style.theme_use('clam')
        
        self.windows[window_id] = {
            'root': root,
            'title': title,
            'width': width,
            'height': height,
            'widgets': {},
            'canvas': None
        }
        
        self.current_window_id = window_id
        return window_id
    
    def set_window_background(self, window_id, color="#f0f0f0"):
        """Set window background color"""
        if window_id in self.windows:
            self.windows[window_id]['root'].configure(bg=color)
    
    def create_canvas(self, window_id, width=400, height=300, bg="white"):
        """Create a canvas for drawing operations"""
        if window_id not in self.windows:
            return None
            
        canvas = tk.Canvas(
            self.windows[window_id]['root'], 
            width=width, 
            height=height, 
            bg=bg,
            highlightthickness=0
        )
        canvas.pack(padx=10, pady=10)
        
        canvas_id = f"canvas_{self.widget_counter}"
        self.widget_counter += 1
        
        self.windows[window_id]['canvas'] = canvas
        self.widgets[canvas_id] = canvas
        
        return canvas_id
    
    def draw_rectangle(self, canvas_id, x, y, width, height, fill="blue", outline="black"):
        """Draw a rectangle on canvas"""
        if canvas_id in self.widgets:
            canvas = self.widgets[canvas_id]
            return canvas.create_rectangle(x, y, x + width, y + height, fill=fill, outline=outline)
    
    def draw_circle(self, canvas_id, x, y, radius, fill="red", outline="black"):
        """Draw a circle on canvas"""
        if canvas_id in self.widgets:
            canvas = self.widgets[canvas_id]
            return canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=fill, outline=outline)
    
    def draw_line(self, canvas_id, x1, y1, x2, y2, fill="black", width=1):
        """Draw a line on canvas"""
        if canvas_id in self.widgets:
            canvas = self.widgets[canvas_id]
            return canvas.create_line(x1, y1, x2, y2, fill=fill, width=width)
    
    def draw_text(self, canvas_id, x, y, text, fill="black", font=("Arial", 12)):
        """Draw text on canvas"""
        if canvas_id in self.widgets:
            canvas = self.widgets[canvas_id]
            return canvas.create_text(x, y, text=text, fill=fill, font=font)
    
    def clear_canvas(self, canvas_id):
        """Clear all drawings from canvas"""
        if canvas_id in self.widgets:
            canvas = self.widgets[canvas_id]
            canvas.delete("all")
    
    def create_button(self, window_id, text="Click Me", x=10, y=10, width=100, height=30):
        """Create a button widget"""
        if window_id not in self.windows:
            return None
            
        button = tk.Button(
            self.windows[window_id]['root'],
            text=text,
            width=width//8,  # Approximate character width
            height=height//20  # Approximate line height
        )
        button.place(x=x, y=y, width=width, height=height)
        
        button_id = f"button_{self.widget_counter}"
        self.widget_counter += 1
        self.widgets[button_id] = button
        
        return button_id
    
    def create_label(self, window_id, text="Label", x=10, y=10, font_size=12):
        """Create a label widget"""
        if window_id not in self.windows:
            return None
            
        label = tk.Label(
            self.windows[window_id]['root'],
            text=text,
            font=("Arial", font_size)
        )
        label.place(x=x, y=y)
        
        label_id = f"label_{self.widget_counter}"
        self.widget_counter += 1
        self.widgets[label_id] = label
        
        return label_id
    
    def create_entry(self, window_id, x=10, y=10, width=200, placeholder=""):
        """Create a text entry widget"""
        if window_id not in self.windows:
            return None
            
        entry = tk.Entry(self.windows[window_id]['root'])
        if placeholder:
            entry.insert(0, placeholder)
            entry.config(fg='grey')
        entry.place(x=x, y=y, width=width)
        
        entry_id = f"entry_{self.widget_counter}"
        self.widget_counter += 1
        self.widgets[entry_id] = entry
        
        return entry_id
    
    def set_widget_text(self, widget_id, text):
        """Set text for various widget types"""
        if widget_id in self.widgets:
            widget = self.widgets[widget_id]
            if hasattr(widget, 'config'):
                try:
                    widget.config(text=text)
                except:
                    # Try for Entry widgets
                    widget.delete(0, tk.END)
                    widget.insert(0, text)
    
    def get_widget_text(self, widget_id):
        """Get text from various widget types"""
        if widget_id in self.widgets:
            widget = self.widgets[widget_id]
            if hasattr(widget, 'get'):
                return widget.get()
            elif hasattr(widget, 'cget'):
                return widget.cget('text')
        return ""
    
    def bind_key(self, window_id, key, callback):
        """Bind keyboard events to window"""
        if window_id in self.windows:
            root = self.windows[window_id]['root']
            root.bind(f"<{key}>", lambda e: callback())
            root.focus_set()  # Ensure window can receive key events
    
    def bind_click(self, widget_id, callback):
        """Bind click events to widgets"""
        if widget_id in self.widgets:
            widget = self.widgets[widget_id]
            widget.config(command=callback)
    
    def show_message(self, title="Message", message="Hello from Sona!", type="info"):
        """Show message dialog"""
        if type == "info":
            messagebox.showinfo(title, message)
        elif type == "warning":
            messagebox.showwarning(title, message)
        elif type == "error":
            messagebox.showerror(title, message)
    
    def get_file_path(self, title="Select File", filetypes=[("All Files", "*.*")]):
        """Open file dialog and return selected path"""
        return filedialog.askopenfilename(title=title, filetypes=filetypes)
    
    def choose_color(self, initial_color="#ffffff"):
        """Open color chooser dialog"""
        color = colorchooser.askcolor(initialcolor=initial_color)
        return color[1] if color[1] else initial_color
    
    def update_window(self, window_id):
        """Update window (process events)"""
        if window_id in self.windows:
            self.windows[window_id]['root'].update()
    
    def update_all_windows(self):
        """Update all windows"""
        for window_id in self.windows:
            self.update_window(window_id)
    
    def start_mainloop(self, window_id):
        """Start the main event loop for a window"""
        if window_id in self.windows:
            self.running = True
            self.windows[window_id]['root'].mainloop()
    
    def close_window(self, window_id):
        """Close a specific window"""
        if window_id in self.windows:
            self.windows[window_id]['root'].destroy()
            del self.windows[window_id]
    
    def close_all_windows(self):
        """Close all windows"""
        for window_id in list(self.windows.keys()):
            self.close_window(window_id)
        self.running = False
    
    def is_running(self):
        """Check if GUI is still running"""
        return self.running and len(self.windows) > 0
    
    def get_window_size(self, window_id):
        """Get current window size"""
        if window_id in self.windows:
            root = self.windows[window_id]['root']
            return root.winfo_width(), root.winfo_height()
        return 0, 0
    
    def set_window_size(self, window_id, width, height):
        """Set window size"""
        if window_id in self.windows:
            self.windows[window_id]['root'].geometry(f"{width}x{height}")

# Create the module instance
gui = SonaGUIModule()

# Export for compatibility
__all__ = ['gui']
