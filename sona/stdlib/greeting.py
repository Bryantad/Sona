"""Sona standard library: greeting.smod"""
import os

class GreetingModule:
    def __init__(self):
        """Initialize the greeting module"""
        pass
    
    def say(self, message):
        """Say a message"""
        return message
        
    def hi(self):
        """Say hi"""
        return "Hello there!"
        
    def hello(self, name=""):
        """Say hello to someone"""
        if name:
            return f"Hello, {name}!"
        return "Hello, World!"
    
    def greet(self, name="friend"):
        """Greet someone"""
        return f"Greetings, {name}!"

# ✅ Export as instance (required by Sona's dynamic loader)
greeting = GreetingModule()
__all__ = ["greeting"]
import os
if os.environ.get("SONA_DEBUG") == "1" and os.environ.get("SONA_MODULE_SILENT") != "1":
    print("[DEBUG] greeting module loaded")
