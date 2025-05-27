import os
import sys
import ctypes
from ctypes import wintypes

# Windows console structures
class COORD(ctypes.Structure):
    _fields_ = [("X", ctypes.c_short),
                ("Y", ctypes.c_short)]

class SMALL_RECT(ctypes.Structure):
    _fields_ = [("Left", ctypes.c_short),
                ("Top", ctypes.c_short),
                ("Right", ctypes.c_short),
                ("Bottom", ctypes.c_short)]

class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
    _fields_ = [("dwSize", COORD),
                ("dwCursorPosition", COORD),
                ("wAttributes", ctypes.c_ushort),
                ("srWindow", SMALL_RECT),
                ("dwMaximumWindowSize", COORD)]

class ConsoleModule:
    def __init__(self):
        self.is_windows = sys.platform == "win32"
        if self.is_windows:
            self.kernel32 = ctypes.windll.kernel32
            self.handle = self.kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            
            # Define Windows console structures
            class CONSOLE_CURSOR_INFO(ctypes.Structure):
                _fields_ = [("size", ctypes.c_ulong),
                          ("visible", ctypes.c_bool)]
            self.CONSOLE_CURSOR_INFO = CONSOLE_CURSOR_INFO

    def move_cursor(self, x: int, y: int):
        if self.is_windows:
            position = COORD(x, y)
            self.kernel32.SetConsoleCursorPosition(self.handle, position)
        else:
            print(f"\033[{y};{x}H", end="")

    def get_cursor_position(self):
        if self.is_windows:
            info = CONSOLE_SCREEN_BUFFER_INFO()
            self.kernel32.GetConsoleScreenBufferInfo(self.handle, ctypes.byref(info))
            return (info.dwCursorPosition.X, info.dwCursorPosition.Y)
        return (0, 0)  # Fallback for non-Windows

    def hide_cursor(self):
        if self.is_windows:
            info = self.CONSOLE_CURSOR_INFO(1, False)
            self.kernel32.SetConsoleCursorInfo(self.handle, ctypes.byref(info))
        else:
            print("\033[?25l", end="")

    def show_cursor(self):
        if self.is_windows:
            info = self.CONSOLE_CURSOR_INFO(1, True)
            self.kernel32.SetConsoleCursorInfo(self.handle, ctypes.byref(info))
        else:            print("\033[?25h", end="")

    def set_color(self, fg: int, bg: int):
        if self.is_windows:
            self.kernel32.SetConsoleTextAttribute(self.handle, (bg << 4) | fg)
        else:
            print(f"\033[{30+fg};{40+bg}m", end="")
            
    def clear(self):
        if self.is_windows:
            _ = os.system('cls')  # Use actual command execution
        else:
            _ = os.system('clear')
    
    def write(self, text, color=None):
        """Write text at the current cursor position with optional color
        
        Args:
            text (str): Text to write
            color (str, optional): Color name ('red', 'green', 'blue', etc.)
        """
        if color:
            color_map = {
                'black': 0, 'blue': 1, 'green': 2, 'cyan': 3,
                'red': 4, 'magenta': 5, 'yellow': 6, 'white': 7
            }
            fg = color_map.get(color.lower(), 7)  # Default to white if invalid color
            self.set_color(fg, 0)
            print(text, end='')
            self.set_color(7, 0)  # Reset to default
        else:
            print(text, end='')
            
    def draw_box(self, x, y, width, height, title=None):
        """Draw a box with optional title
        
        Args:
            x (int): Left position
            y (int): Top position
            width (int): Width of box
            height (int): Height of box
            title (str, optional): Title to display in top border
        """
        # Box drawing characters
        if self.is_windows:
            h_line = "─"
            v_line = "│"
            tl = "┌"
            tr = "┐"
            bl = "└"
            br = "┘"
        else:
            h_line = "─"
            v_line = "│"
            tl = "┌"
            tr = "┐"
            bl = "└"
            br = "┘"
            
        # Draw top border
        self.move_cursor(x, y)
        if title and len(title) < width - 2:
            # Calculate padding for centered title
            padding = (width - 2 - len(title)) // 2
            top = tl + h_line * padding + title + h_line * (width - 2 - padding - len(title)) + tr
            self.write(top)
        else:
            self.write(tl + h_line * (width - 2) + tr)
            
        # Draw side borders
        for i in range(1, height - 1):
            self.move_cursor(x, y + i)
            self.write(v_line)
            self.move_cursor(x + width - 1, y + i)
            self.write(v_line)
            
        # Draw bottom border
        self.move_cursor(x, y + height - 1)
        self.write(bl + h_line * (width - 2) + br)
        
    def get_terminal_size(self):
        """Get the terminal size (width, height)
        
        Returns:
            tuple: (width, height) of terminal
        """
        if self.is_windows:
            info = CONSOLE_SCREEN_BUFFER_INFO()
            self.kernel32.GetConsoleScreenBufferInfo(self.handle, ctypes.byref(info))
            width = info.srWindow.Right - info.srWindow.Left + 1
            height = info.srWindow.Bottom - info.srWindow.Top + 1
            return (width, height)
        else:
            # Use os.get_terminal_size for Unix-like systems
            return os.get_terminal_size()
    
    def fill_area(self, x, y, width, height, char=' '):
        """Fill an area with a specific character
        
        Args:
            x (int): Left position
            y (int): Top position
            width (int): Width of area
            height (int): Height of area
            char (str, optional): Character to fill with, defaults to space
        """
        fill_line = char * width
        for i in range(height):
            self.move_cursor(x, y + i)
            print(fill_line, end='')
    
    def cleanup(self):
        """Reset console settings to default"""
        self.show_cursor()
        if self.is_windows:
            self.set_color(7, 0)  # Reset to default colors
        else:
            print("\033[0m", end="")