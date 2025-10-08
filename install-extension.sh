#!/usr/bin/env bash
# install-extension.sh - Automated Sona VS Code Extension Installer
# This script uninstalls any existing Sona extensions and installs the working v0.9.4 VSIX

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

show_help() {
    cat << EOF
Sona VS Code Extension Installer
=================================

This script:
1. Uninstalls any existing Sona extensions
2. Installs the working v0.9.4 VSIX from the repository
3. Verifies the installation

Usage:
    ./install-extension.sh           # Normal installation
    ./install-extension.sh --help    # Show this help

Requirements:
- VS Code must be installed and 'code' command available in PATH
- Run from the Sona repository root directory

EOF
    exit 0
}

if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    show_help
fi

echo -e "\n${CYAN}=== Sona VS Code Extension Installer ===${NC}"
echo -e "${GREEN}Using clean v0.9.4 VSIX (no dependencies)${NC}"

# Check if VS Code is available
if ! command -v code &> /dev/null; then
    echo -e "\n${RED}❌ ERROR: VS Code 'code' command not found in PATH${NC}"
    echo -e "\n${YELLOW}Please ensure VS Code is installed and the 'code' command is available.${NC}"
    echo -e "${YELLOW}You may need to:${NC}"
    echo -e "${YELLOW}  1. Install VS Code from https://code.visualstudio.com/${NC}"
    echo -e "${YELLOW}  2. Open VS Code → Command Palette → 'Shell Command: Install code command in PATH'${NC}"
    exit 1
fi

# Locate the VSIX file
VSIX_PATH="${SCRIPT_DIR}/sona-ai-native-programming-0.9.4/sona-ai-native-programming-0.9.4.vsix"

if [[ ! -f "$VSIX_PATH" ]]; then
    echo -e "\n${RED}❌ ERROR: VSIX file not found at:${NC}"
    echo -e "${YELLOW}  $VSIX_PATH${NC}"
    echo -e "\n${YELLOW}Please ensure you're running this script from the Sona repository root.${NC}"
    exit 1
fi

VSIX_SIZE=$(du -h "$VSIX_PATH" | cut -f1)
echo -e "\n${GREEN}✓ Found VSIX: $VSIX_PATH${NC}"
echo -e "${GRAY}  Size: $VSIX_SIZE${NC}"

# Check for existing Sona extensions
echo -e "\n${CYAN}Checking for existing Sona extensions...${NC}"
EXISTING_EXTS=$(code --list-extensions 2>&1 | grep -i "sona" || true)

if [[ -n "$EXISTING_EXTS" ]]; then
    echo -e "${YELLOW}Found existing Sona extension(s):${NC}"
    echo -e "${YELLOW}$EXISTING_EXTS${NC}"
    
    echo -e "\n${CYAN}Uninstalling existing Sona extensions...${NC}"
    while IFS= read -r ext; do
        if [[ -n "$ext" ]]; then
            echo -e "${GRAY}  Uninstalling: $ext${NC}"
            code --uninstall-extension "$ext" > /dev/null 2>&1 || true
        fi
    done <<< "$EXISTING_EXTS"
    echo -e "${GREEN}✓ Uninstalled existing extensions${NC}"
else
    echo -e "${GREEN}✓ No existing Sona extensions found${NC}"
fi

# Install the v0.9.4 VSIX
echo -e "\n${CYAN}Installing Sona v0.9.4 extension...${NC}"
if code --install-extension "$VSIX_PATH" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Extension installed successfully!${NC}"
else
    echo -e "\n${RED}❌ ERROR: Failed to install extension${NC}"
    exit 1
fi

# Verify installation
echo -e "\n${CYAN}Verifying installation...${NC}"
INSTALLED=$(code --list-extensions 2>&1 | grep "waycoreinc.sona-ai-native-programming" || true)

if [[ -n "$INSTALLED" ]]; then
    echo -e "${GREEN}✓ Extension verified: $INSTALLED${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Extension may not be installed correctly${NC}"
    echo -e "${GRAY}  Run 'code --list-extensions' to check manually${NC}"
fi

# Success message
echo -e "\n${CYAN}==================================================${NC}"
echo -e "${GREEN}✅ Sona v0.9.4 Extension Installation Complete!${NC}"
echo -e "${CYAN}==================================================${NC}"

echo -e "\n${CYAN}Next Steps:${NC}"
echo -e "${NC}1. Restart VS Code (if it's currently running)${NC}"
echo -e "${NC}2. Open or create a .sona file to activate the extension${NC}"
echo -e "${NC}3. Check syntax highlighting is working${NC}"

echo -e "\n${CYAN}To test the extension:${NC}"
echo -e "${NC}  - Create a test file: test.sona${NC}"
echo -e "${NC}  - Add code: print(\"Hello from Sona!\")${NC}"
echo -e "${NC}  - Verify syntax highlighting appears${NC}"

echo -e "\n${CYAN}Extension Features:${NC}"
echo -e "${GREEN}  ✓ Syntax highlighting for .sona files${NC}"
echo -e "${GREEN}  ✓ Language configuration (auto-close, comments)${NC}"
echo -e "${GREEN}  ✓ Code snippets${NC}"
echo -e "${GREEN}  ✓ Custom file icons${NC}"

echo -e "\n${GRAY}For more info, see: INSTALL_EXTENSION.md${NC}\n"
