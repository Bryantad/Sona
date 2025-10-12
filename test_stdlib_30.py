# Sona v0.9.6 Stdlib - 30 Module Verification Test
# Tests that all 30 modules can be imported successfully

import sys
import os

# Add SonaMinimal to path
sys.path.insert(0, r'F:\SonaMinimal')

print("\n" + "="*60)
print("Sona v0.9.6 Standard Library - Module Import Test")
print("Testing all 30 official modules...")
print("="*60 + "\n")

# Official v0.9.6 30 Modules (from MANIFEST.json)
modules = [
    "json", "string", "math", "numbers", "boolean", "type",
    "comparison", "operators", "time", "date", "random", "regex",
    "fs", "path", "io", "env", "collection", "queue", "stack",
    "csv", "encoding", "timer", "validation", "statistics",
    "sort", "search", "uuid", "yaml", "toml", "hashing"
]

success_count = 0
failed_count = 0
failed_modules = []

for i, module_name in enumerate(modules, 1):
    try:
        # Try importing from sona.stdlib
        module = __import__(f'sona.stdlib.{module_name}', fromlist=[module_name])
        print(f"[{i:2d}/30] ✓ {module_name:15s} - OK")
        success_count += 1
    except Exception as e:
        print(f"[{i:2d}/30] ✗ {module_name:15s} - FAILED: {str(e)[:40]}")
        failed_count += 1
        failed_modules.append(module_name)

print("\n" + "="*60)
print("Test Results:")
print("="*60)
print(f"✓ Successful imports: {success_count}/30")
print(f"✗ Failed imports: {failed_count}/30")

if failed_count > 0:
    print(f"\nFailed modules: {', '.join(failed_modules)}")
    print("\nStatus: INCOMPLETE - Some modules need attention")
else:
    print("\nStatus: ✓ COMPLETE - All 30 modules ready!")
    print("Sona v0.9.6 stdlib is fully functional!")

print("="*60 + "\n")

# Exit code
sys.exit(0 if failed_count == 0 else 1)
