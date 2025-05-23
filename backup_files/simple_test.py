#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.getcwd())

print("Testing simple import...")

# Import necessary modules
from sona.utils.debug import debug

# Try direct import
try:
    from sona.stdlib.utils.math.smod import math as math_module
    print(f"Successfully imported utils.math.smod: {math_module}")
    print(f"PI value: {math_module.PI}")
    print(f"Available methods: {dir(math_module)}")
except Exception as e:
    print(f"Error importing direct module: {e}")

# Confirm the file exists
module_path = Path("sona/stdlib/utils/math/smod.py")
print(f"File exists: {module_path.exists()}")

# Create a simple test file
test_file = "simple_import_test.sona"
with open(test_file, "w") as f:
    f.write("// Simple import test\nimport utils.math.smod\nprint(utils.math.smod.PI)\n")

# Run the test file
print("\nRunning simple import test:")
os.system(f"python -m sona {test_file}")

# Create a test file with an alias
test_file_alias = "alias_import_test.sona"
with open(test_file_alias, "w") as f:
    f.write("// Alias import test\nimport math\nprint(math.PI)\n")

# Run the test file with alias
print("\nRunning alias import test:")
os.system(f"python -m sona {test_file_alias}")

# Create a cleaned up test
test_file_clean = "simple_v0.5.0_test.sona"
with open(test_file_clean, "w") as f:
    f.write('''// Clean v0.5.0 test
// Define a function
func greeting() {
    return "Hello from v0.5.0!"
}

// Use multi-line string
let msg = """
Multi-line
string
test
"""

// Print results
print(greeting())
print(msg)
''')

# Run the clean test
print("\nRunning clean v0.5.0 test:")
os.system(f"python -m sona {test_file_clean}")
