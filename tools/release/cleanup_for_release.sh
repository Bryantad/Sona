#!/bin/bash

# Sona v0.5.1 Release Cleanup Script
# This script cleans up temporary files and prepares the workspace for release

echo "Starting Sona v0.5.1 release cleanup..."

# Change to the project root directory
cd "$(dirname "$0")/.."
ROOT_DIR="$(pwd)"

# Remove Python cache files
echo "Removing Python cache files..."
find "$ROOT_DIR" -type d -name "__pycache__" -exec rm -rf {} +
find "$ROOT_DIR" -type f -name "*.pyc" -delete
find "$ROOT_DIR" -type f -name "*.pyo" -delete
find "$ROOT_DIR" -type f -name "*.pyd" -delete

# Remove test cache files
echo "Removing test cache files..."
find "$ROOT_DIR" -type d -name ".pytest_cache" -exec rm -rf {} +
find "$ROOT_DIR" -type d -name ".coverage" -exec rm -rf {} +

# Remove temporary files
echo "Removing temporary files..."
find "$ROOT_DIR" -type f -name "*.log" -delete
find "$ROOT_DIR" -type f -name "*.tmp" -delete
find "$ROOT_DIR" -type f -name ".DS_Store" -delete

# Remove any editor-specific files/directories
echo "Removing editor-specific files..."
find "$ROOT_DIR" -type d -name ".vscode" -exec rm -rf {} +
find "$ROOT_DIR" -type d -name ".idea" -exec rm -rf {} +
find "$ROOT_DIR" -type f -name "*.swp" -delete
find "$ROOT_DIR" -type f -name "*~" -delete

# Remove build artifacts
echo "Cleaning build artifacts..."
rm -rf "$ROOT_DIR/build/lib"
rm -rf "$ROOT_DIR/dist"

echo "Cleanup complete! Workspace is ready for v0.5.1 release."
