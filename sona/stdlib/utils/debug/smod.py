import os

def debug(msg):
    if os.environ.get("SONA_DEBUG") == "1":
        print(f"[DEBUG] {msg}")
# Debugging utility to print the type and dir of an object

class DebugModule:
    def type_of(self, x): return type(x).__name__
    def dir_of(self, x): return dir(x)

debug = DebugModule()
