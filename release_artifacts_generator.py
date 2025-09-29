#!/usr/bin/env python3
"""
Sona v0.9.4 Release Artifacts Generator
Generates checksums, manifest.json, and prepares release artifacts
"""

import hashlib
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def get_git_info() -> Dict[str, str]:
    """Get git information"""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
        
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
        
        tag = subprocess.run(
            ["git", "describe", "--tags", "--exact-match", "HEAD"],
            capture_output=True, text=True
        ).stdout.strip() or None
        
        return {"commit": commit, "branch": branch, "tag": tag}
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"commit": "unknown", "branch": "unknown", "tag": None}


def get_file_info(file_path: Path) -> Dict[str, Any]:
    """Get file information including size and checksum"""
    if not file_path.exists():
        return None
    
    stat = file_path.stat()
    return {
        "path": str(file_path.relative_to(Path.cwd())),
        "size": stat.st_size,
        "sha256": calculate_sha256(file_path),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
    }


def main():
    """Generate release artifacts"""
    workspace = Path.cwd()
    print("[RELEASE] Generating Sona v0.9.4 release artifacts...")
    
    # Git information
    git_info = get_git_info()
    print(f"[INFO] Git commit: {git_info['commit']}")
    print(f"[INFO] Git branch: {git_info['branch']}")
    if git_info['tag']:
        print(f"[INFO] Git tag: {git_info['tag']}")
    
    # Key artifacts to track
    artifacts = [
        "sona.lock.json",
        "pyproject.toml", 
        "sona.toml",
        "sona/lockfile_manager.py",
        "sona-ai-native-programming-0.9.4/sona-ai-native-programming-0.9.4.vsix"
    ]
    
    # Generate checksums for all artifacts
    checksums = {}
    artifact_info = []
    
    print("[CHECKSUMS] Calculating artifact checksums...")
    for artifact_path in artifacts:
        file_path = workspace / artifact_path
        file_info = get_file_info(file_path)
        
        if file_info:
            checksums[artifact_path] = file_info["sha256"]
            artifact_info.append(file_info)
            print(f"[OK] {artifact_path}: {file_info['sha256'][:16]}...")
        else:
            print(f"[SKIP] {artifact_path}: not found")
    
    # Generate manifest.json
    manifest = {
        "version": "0.9.4",
        "release_type": "production",
        "timestamp": datetime.now().isoformat(),
        "git": git_info,
        "build": {
            "deterministic_packaging": True,
            "lockfile_version": 1,
            "cli_enhanced": True,
            "vscode_extension_publisher": "Waycoreinc"
        },
        "artifacts": artifact_info,
        "checksums": checksums,
        "features": {
            "lockfile_system": "implemented",
            "type_system_cli": "enhanced",
            "configuration_hierarchy": "sona.toml",
            "vscode_extension": "marketplace-ready",
            "exit_code_semantics": "ON=2, WARN=0, exceptions=1"
        },
        "next_release": "v0.9.4.1 (reserved for hotfix)"
    }
    
    # Write manifest.json
    manifest_path = workspace / "manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"[SUCCESS] Created manifest.json with {len(artifact_info)} tracked artifacts")
    
    # Write checksums.txt
    checksums_path = workspace / "checksums.txt"
    with open(checksums_path, 'w', encoding='utf-8') as f:
        f.write("# Sona v0.9.4 Release Checksums (SHA256)\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n")
        f.write(f"# Git commit: {git_info['commit']}\n\n")
        
        for artifact, checksum in checksums.items():
            f.write(f"{checksum}  {artifact}\n")
    
    print(f"[SUCCESS] Created checksums.txt with {len(checksums)} entries")
    
    # Generate release summary
    summary = f"""
# Sona v0.9.4 Release Summary

## Release Information
- Version: 0.9.4
- Type: Production Release
- Timestamp: {manifest['timestamp']}
- Git Commit: {git_info['commit']}

## Key Features Delivered
✅ Deterministic Packaging System (sona.lock.json)
✅ Enhanced CLI with lockfile commands (sona lock, sona verify)
✅ Global --types-status with proper exit codes (ON→2, WARN→0)
✅ Unified Configuration (sona.toml with precedence hierarchy)
✅ VS Code Extension with Waycoreinc publisher identity
✅ ASCII-safe output for Windows compatibility
✅ UTF-8 encoding enforcement

## Artifacts Generated
{len(artifact_info)} tracked artifacts with SHA256 checksums
- Core lockfile system implementation
- VS Code extension package (.vsix)
- Configuration files and build scripts

## Next Steps
- GitHub release creation with artifact upload
- Marketplace publication preparation
- Hotfix version v0.9.4.1 reserved for post-release issues
"""
    
    summary_path = workspace / "RELEASE_SUMMARY_v094.md"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print("[SUCCESS] Created RELEASE_SUMMARY_v094.md")
    print(f"\n[COMPLETE] Sona v0.9.4 release artifacts ready!")
    print(f"Tracked artifacts: {len(artifact_info)}")
    print(f"Total checksums: {len(checksums)}")
    
    return 0


if __name__ == "__main__":
    exit(main())