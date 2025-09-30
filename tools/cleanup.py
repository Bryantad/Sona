#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/tools/cleanup.py
# Sona v0.5.0 Cleanup Utility

"""
This script helps clean up the Sona project directory by:
1. Removing __pycache__ and other temporary files
2. Organizing test files into tests/
3. Moving redundant files to backup_files/

Usage:
    python tools/cleanup.py
"""

import os
import shutil
from pathlib import Path


def remove_pycache():
    """Remove __pycache__ directories and .pyc files"""
    print("Removing __pycache__ directories and .pyc files...")
    removed = 0
    
    # Walk through all directories in the project
    for root, dirs, files in os.walk('.'):
        # Remove __pycache__ dirs
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            print(f"  Removing {cache_dir}")
            shutil.rmtree(cache_dir)
            removed += 1
        
        # Remove .pyc files
        for file in files:
            if file.endswith('.pyc'):
                pyc_file = os.path.join(root, file)
                print(f"  Removing {pyc_file}")
                os.remove(pyc_file)
                removed += 1
    
    print(f"Removed {removed} cache directories and files")

def organize_test_files():
    """Move test files to tests directory"""
    print("Organizing test files...")
    
    test_dir = Path('tests')
    if not test_dir.exists():
        test_dir.mkdir(exist_ok=True)
    
    # Find test files in the root directory
    test_files = []
    for file in os.listdir('.'):
        if (file.startswith('test_') or 'test' in file) and file.endswith('.sona'):
            test_files.append(file)
    
    # Move test files to tests directory
    moved = 0
    for file in test_files:
        src = Path(file)
        dst = test_dir / file
        
        if src.exists() and not dst.exists():
            print(f"  Moving {file} to tests/")
            shutil.copy2(src, dst)
            moved += 1
    
    print(f"Moved {moved} test files to tests/")

def organize_examples():
    """Make sure examples are in the examples directory"""
    print("Organizing example files...")
    
    example_dir = Path('examples')
    if not example_dir.exists():
        example_dir.mkdir(exist_ok=True)
    
    # Find example files in the root directory
    example_files = []
    for file in os.listdir('.'):
        if not file.startswith('test_') and file.endswith('.sona'):
            example_files.append(file)
    
    # Move example files to examples directory
    moved = 0
    for file in example_files:
        src = Path(file)
        dst = example_dir / file
        
        if src.exists() and not dst.exists():
            print(f"  Moving {file} to examples/")
            shutil.copy2(src, dst)
            moved += 1
    
    print(f"Moved {moved} example files to examples/")

if __name__ == "__main__":
    print("Sona v0.5.0 Cleanup Utility")
    print("==========================")
    
    # Create necessary directories
    os.makedirs('tests', exist_ok=True)
    os.makedirs('tools', exist_ok=True)
    os.makedirs('examples', exist_ok=True)
    
    remove_pycache()
    organize_test_files()
    organize_examples()
    
    print("\nCleanup completed successfully!")
