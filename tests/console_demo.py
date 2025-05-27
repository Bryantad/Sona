#!/usr/bin/env python3
# Simple script to test the console module's functionality

from sona.modules.console import ConsoleModule
import time

def main():
    console = ConsoleModule()
    
    try:
        # Clear the screen and hide the cursor
        console.clear()
        console.hide_cursor()
        
        # Get terminal size
        width, height = console.get_terminal_size()
        
        # Draw a box with title
        console.draw_box(2, 1, width - 4, height - 4, "Console Module Test")
        
        # Display information
        console.move_cursor(4, 3)
        console.write("Terminal size: ", "cyan")
        console.write(f"{width}x{height}")
        
        console.move_cursor(4, 5)
        console.write("Testing colors:", "white")
        
        # Show all colors
        colors = ["black", "blue", "green", "cyan", "red", "magenta", "yellow", "white"]
        for i, color in enumerate(colors):
            console.move_cursor(4, 6 + i)
            console.write(f"This text is {color}", color)
        
        # Draw a progress bar
        console.move_cursor(4, 15)
        console.write("Progress Bar Test:", "cyan")
        
        for i in range(0, 101, 5):
            bar_width = 50
            filled = int(bar_width * i / 100)
            console.move_cursor(4, 16)
            console.write("[")
            console.write("=" * filled, "green")
            console.write(" " * (bar_width - filled))
            console.write(f"] {i}%")
            time.sleep(0.1)
        
        # Animation test
        console.move_cursor(4, 18)
        console.write("Animation Test:", "cyan")
        
        spinner = "|/-\\"
        for i in range(20):
            console.move_cursor(20, 18)
            console.write(spinner[i % 4], "yellow")
            time.sleep(0.2)
            
        # Final message
        console.move_cursor(4, 20)
        console.write("Test complete! Press any key to exit...", "green")
        
    finally:
        # Always restore the console state
        console.move_cursor(0, height - 1)
        console.cleanup()

if __name__ == "__main__":
    main()
