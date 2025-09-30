#!/bin/bash

# Push Sona v0.5.1 Release to GitHub
# This script pushes the v0.5.1 release to GitHub with proper tags

echo "Pushing Sona v0.5.1 release to GitHub..."

# Change to the project root directory
cd "$(dirname "$0")/../.."
ROOT_DIR="$(pwd)"

# Make sure we're on the right branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "release/v0.5.1" ]]; then
  echo "Error: You are on branch $CURRENT_BRANCH, not on release/v0.5.1"
  echo "Please switch to release/v0.5.1 branch first."
  exit 1
fi

# Push changes
echo "Pushing changes to GitHub..."
git push origin release/v0.5.1

# Tag the release if it's not already tagged
if ! git tag | grep -q "v0.5.1"; then
  echo "Tagging v0.5.1 release..."
  git tag -a v0.5.1 -m "Sona Programming Language v0.5.1"
  git push origin v0.5.1
else
  echo "Tag v0.5.1 already exists."
fi

echo "Push complete! Sona v0.5.1 is now on GitHub."
echo "Release URL: https://github.com/Bryantad/Sona/releases/tag/v0.5.1"
