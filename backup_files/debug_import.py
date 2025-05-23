import sys
import importlib
from pathlib import Path
import os

# Set debug mode
os.environ["SONA_DEBUG"] = "1"

def debug(msg):
    print(f"[DEBUG] {msg}")

# Import the module directly to test
module_name = "utils.math.smod"
py_module = "sona.stdlib." + module_name

# Add the current directory to sys.path to make imports work
sys.path.insert(0, os.getcwd())
debug(f"Python path: {sys.path}")

try:
    # Import the module
    debug(f"Importing {py_module}")
    mod = importlib.import_module(py_module)
    
    # Check module attributes
    debug(f"Module attributes: {dir(mod)}")
    
    # Check if 'math' is in the module
    if hasattr(mod, 'math'):
        math_obj = getattr(mod, 'math')
        debug(f"Found math object: {math_obj}")
        debug(f"Math methods: {dir(math_obj)}")
        debug(f"PI value: {math_obj.PI}")
    else:
        debug("No 'math' attribute found in the module")
        
    # Check __all__
    if hasattr(mod, '__all__'):
        debug(f"__all__: {mod.__all__}")
    
except Exception as e:
    debug(f"Error: {e}")
