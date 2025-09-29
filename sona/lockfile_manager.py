#!/usr/bin/env python3
"""
Lockfile management for Sona v0.9.4
Handles generation and verification of sona.lock.json for deterministic builds
"""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional


def calculate_file_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def get_git_commit() -> Optional[str]:
    """Get the current git commit hash"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path.cwd()
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def scan_sona_modules(workspace_dir: Path) -> List[Dict[str, str]]:
    """Scan workspace for Sona modules and calculate checksums"""
    modules = []
    
    # Core Sona files to track
    sona_files = [
        "sona/__init__.py",
        "sona/interpreter.py", 
        "sona/cli.py",
        "sona/type_system/__init__.py",
        "sona/type_system/runtime_checker.py",
        "sona/stdlib/core.py",
        "sona/stdlib/async_ops.py",
    ]
    
    for file_path_str in sona_files:
        file_path = workspace_dir / file_path_str
        if file_path.exists():
            try:
                sha256 = calculate_file_sha256(file_path)
                modules.append({
                    "module": file_path_str,
                    "rev": "workspace",  # Could be git rev in future
                    "sha256": sha256
                })
            except Exception as e:
                print(f"Warning: Could not hash {file_path}: {e}")
    
    return modules


def generate_lockfile(workspace_dir: Path) -> bool:
    """Generate sona.lock.json lockfile"""
    try:
        # Get current git commit
        commit_hash = get_git_commit()
        
        # Scan for modules
        modules = scan_sona_modules(workspace_dir)
        
        if not modules:
            print("Warning: No Sona modules found to track")
            return False
        
        # Create lockfile structure
        lockfile_data = {
            "version": 1,
            "created_at": str(Path.cwd()),
            "commit": commit_hash or "unknown",
            "entries": modules
        }
        
        # Write lockfile
        lockfile_path = workspace_dir / "sona.lock.json"
        with open(lockfile_path, 'w', encoding='utf-8') as f:
            json.dump(lockfile_data, f, indent=2, ensure_ascii=False)
        
        print(f"Generated lockfile with {len(modules)} modules")
        return True
        
    except Exception as e:
        print(f"Error generating lockfile: {e}")
        return False


def verify_lockfile(workspace_dir: Path) -> bool:
    """Verify sona.lock.json integrity against current workspace"""
    try:
        lockfile_path = workspace_dir / "sona.lock.json"
        
        if not lockfile_path.exists():
            print("[ERROR] sona.lock.json not found")
            return False
        
        # Load lockfile
        with open(lockfile_path, 'r', encoding='utf-8') as f:
            lockfile_data = json.load(f)
        
        # Check version
        if lockfile_data.get("version") != 1:
            print("[ERROR] Unsupported lockfile version")
            return False
        
        # Verify each tracked module
        entries = lockfile_data.get("entries", [])
        if not entries:
            print("[ERROR] No entries found in lockfile")
            return False
        
        failed_checks = 0
        for entry in entries:
            module_path = workspace_dir / entry["module"]
            expected_sha256 = entry["sha256"]
            
            if not module_path.exists():
                print(f"[ERROR] Module missing: {entry['module']}")
                failed_checks += 1
                continue
            
            try:
                actual_sha256 = calculate_file_sha256(module_path)
                if actual_sha256 != expected_sha256:
                    print(f"[ERROR] Checksum mismatch: {entry['module']}")
                    print(f"   Expected: {expected_sha256}")
                    print(f"   Actual:   {actual_sha256}")
                    failed_checks += 1
                else:
                    print(f"[OK] {entry['module']}")
            except Exception as e:
                print(f"[ERROR] Error checking {entry['module']}: {e}")
                failed_checks += 1
        
        if failed_checks == 0:
            print(f"[SUCCESS] All {len(entries)} modules verified successfully")
            return True
        else:
            print(f"[FAILED] {failed_checks} of {len(entries)} modules failed")
            return False
        
    except Exception as e:
        print(f"Error verifying lockfile: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2 or sys.argv[1] not in ["generate", "verify"]:
        print("Usage: python lockfile_manager.py [generate|verify]")
        sys.exit(1)
    
    workspace = Path.cwd()
    
    if sys.argv[1] == "generate":
        success = generate_lockfile(workspace)
        sys.exit(0 if success else 1)
    else:  # verify
        success = verify_lockfile(workspace)
        sys.exit(0 if success else 1)