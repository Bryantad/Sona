"""
Sona 0.9.6 Minimal Workspace - Core Files Lock
Ensures minimal tree integrity and prevents feature creep
"""

CORE_LOCK = {
    "version": "0.9.6",
    "lock_date": "2025-10-09",
    "description": "Minimal Sona 0.9.6 workspace - protected core files",
    
    "required_core": [
        "sona/__init__.py",
        "sona/interpreter.py",
        "sona/parser_v090.py",
        "sona/ast_nodes.py",
        "sona/grammar.lark",
        "sona/cli.py",
    ],
    
    "required_stdlib": [
        "sona/stdlib/__init__.py",
        "sona/stdlib/MANIFEST.json",
        # Core modules
        "sona/stdlib/math.py",
        "sona/stdlib/string.py",
        "sona/stdlib/json.py",
        "sona/stdlib/io.py",
        # All 30 modules from MANIFEST
        "sona/stdlib/numbers.py",
        "sona/stdlib/boolean.py",
        "sona/stdlib/type.py",
        "sona/stdlib/comparison.py",
        "sona/stdlib/operators.py",
        "sona/stdlib/time.py",
        "sona/stdlib/date.py",
        "sona/stdlib/random.py",
        "sona/stdlib/regex.py",
        "sona/stdlib/fs.py",
        "sona/stdlib/path.py",
        "sona/stdlib/env.py",
        "sona/stdlib/collection.py",
        "sona/stdlib/queue.py",
        "sona/stdlib/stack.py",
        "sona/stdlib/csv.py",
        "sona/stdlib/encoding.py",
        "sona/stdlib/timer.py",
        "sona/stdlib/validation.py",
        "sona/stdlib/statistics.py",
        "sona/stdlib/sort.py",
        "sona/stdlib/search.py",
        "sona/stdlib/uuid.py",
        "sona/stdlib/yaml.py",
        "sona/stdlib/toml.py",
        "sona/stdlib/hashing.py",
    ],
    
    "optional_smod": [
        "stdlib/math.smod",
        "stdlib/string.smod",
        "stdlib/io.smod",
        "stdlib/json.smod",
        "stdlib/time.smod",
        "stdlib/date.smod",
        "stdlib/regex.smod",
        "stdlib/fs.smod",
        "stdlib/path.smod",
        "stdlib/env.smod",
        "stdlib/csv.smod",
    ],
    
    "workspace_files": [
        "run_sona.py",
        "setup.py",
        "pyproject.toml",
        "requirements.txt",
        "README.md",
        "CHANGELOG.md",
    ],
    
    "test_files": [
        "test.sona",
        "test_hello.sona",
        "test_simple_096.sona",
        "test_demo_simple_096.sona",
        "test_stdlib_30.py",
    ],
}


def verify_workspace(verbose=True):
    """Verify that all required files exist"""
    import os
    from pathlib import Path
    
    workspace_root = Path(__file__).parent
    missing = []
    found = []
    
    # Check all required files
    all_required = (
        CORE_LOCK["required_core"] + 
        CORE_LOCK["required_stdlib"] + 
        CORE_LOCK["workspace_files"]
    )
    
    for file_path in all_required:
        full_path = workspace_root / file_path
        if full_path.exists():
            found.append(file_path)
            if verbose:
                print(f"✓ {file_path}")
        else:
            missing.append(file_path)
            if verbose:
                print(f"✗ MISSING: {file_path}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Workspace Verification: Sona {CORE_LOCK['version']}")
    print(f"{'='*60}")
    print(f"✓ Found: {len(found)}/{len(all_required)}")
    
    if missing:
        print(f"✗ Missing: {len(missing)}")
        print(f"\nMissing files:")
        for f in missing:
            print(f"  - {f}")
        return False
    else:
        print("🎉 All required files present!")
        print(f"Workspace is healthy and locked to v{CORE_LOCK['version']}")
        return True


if __name__ == "__main__":
    import sys
    success = verify_workspace(verbose=True)
    sys.exit(0 if success else 1)
