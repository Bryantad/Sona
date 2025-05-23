import os

# sona/stdlib/native_stdin.py
# This file is part of the Sona programming language.
# Native stdin module for Sona v0.5.1

# Create a module-level object that can be imported
class StdinModule:
    def __init__(self):
        pass
        
    def input(self, prompt=""):
        """Get input from user with a prompt"""
        return __builtins__['input'](prompt)  # Use Python's built-in input
        
    def read_line(self, prompt=""):
        """Alias for input"""
        return self.input(prompt)

# Create the singleton instance that will be imported
native_stdin = StdinModule()

# Only print debug message if DEBUG environment variable is set
if os.environ.get('DEBUG', '').lower() in ('1', 'true', 'yes'):
    print("[DEBUG] native_stdin module loaded")
