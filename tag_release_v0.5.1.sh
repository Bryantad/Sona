#!/bin/bash
# Script to tag and push the v0.5.1 release

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Display the current version
echo "Preparing release for Sona v0.5.1"
echo "--------------------------------"

# Check if there are uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
  echo "There are uncommitted changes. Please commit all changes before tagging."
  exit 1
fi

# Create the git tag
echo "Creating git tag v0.5.1..."
git tag -a v0.5.1 -m "Sona v0.5.1 - REPL diagnostic tools and bug fixes"

# Push the tag
echo "Pushing tag to remote repository..."
git push origin v0.5.1

echo "--------------------------------"
echo "Sona v0.5.1 has been tagged and pushed!"
echo "Release Notes: ./RELEASE_NOTES_v0.5.1.md"
