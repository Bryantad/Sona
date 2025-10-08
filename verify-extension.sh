#!/usr/bin/env bash
# verify-extension.sh - Verify Sona VS Code Extension Installation

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

echo -e "\n${CYAN}=== Sona Extension Verification ===${NC}\n"

# Check if code command exists
if ! command -v code &> /dev/null; then
    echo -e "${RED}❌ VS Code 'code' command not found${NC}"
    echo -e "${YELLOW}Cannot verify extension without VS Code CLI${NC}"
    exit 1
fi

# Test 1: Check if extension is installed
echo -e "${CYAN}Test 1: Extension Installation${NC}"
INSTALLED=$(code --list-extensions 2>&1 | grep "waycoreinc.sona-ai-native-programming" || true)

if [[ -n "$INSTALLED" ]]; then
    echo -e "${GREEN}✓ Extension installed: $INSTALLED${NC}"
    EXTENSION_INSTALLED=true
else
    echo -e "${RED}✗ Extension not installed${NC}"
    echo -e "${YELLOW}  Run: ./install-extension.sh${NC}"
    EXTENSION_INSTALLED=false
fi

# Test 2: Check extension directory
echo -e "\n${CYAN}Test 2: Extension Files${NC}"
EXT_DIR=""

if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    EXT_DIR="$HOME/.vscode/extensions/waycoreinc.sona-ai-native-programming-0.9.4"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    EXT_DIR="$HOME/.vscode/extensions/waycoreinc.sona-ai-native-programming-0.9.4"
fi

if [[ -d "$EXT_DIR" ]]; then
    echo -e "${GREEN}✓ Extension directory found${NC}"
    echo -e "${GRAY}  Location: $EXT_DIR${NC}"
    
    # Check key files
    if [[ -f "$EXT_DIR/package.json" ]]; then
        echo -e "${GREEN}  ✓ package.json present${NC}"
    else
        echo -e "${RED}  ✗ package.json missing${NC}"
    fi
    
    if [[ -f "$EXT_DIR/extension.js" ]]; then
        echo -e "${GREEN}  ✓ extension.js present${NC}"
    else
        echo -e "${RED}  ✗ extension.js missing${NC}"
    fi
    
    if [[ -f "$EXT_DIR/syntaxes/sona.tmLanguage.json" ]]; then
        echo -e "${GREEN}  ✓ Syntax highlighting grammar present${NC}"
    else
        echo -e "${RED}  ✗ Syntax grammar missing${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Extension directory not found at expected location${NC}"
    echo -e "${GRAY}  Expected: $EXT_DIR${NC}"
fi

# Test 3: Check VSIX source file
echo -e "\n${CYAN}Test 3: Source VSIX File${NC}"
VSIX_PATH="./sona-ai-native-programming-0.9.4/sona-ai-native-programming-0.9.4.vsix"

if [[ -f "$VSIX_PATH" ]]; then
    VSIX_SIZE=$(du -h "$VSIX_PATH" | cut -f1)
    echo -e "${GREEN}✓ Source VSIX found${NC}"
    echo -e "${GRAY}  Location: $VSIX_PATH${NC}"
    echo -e "${GRAY}  Size: $VSIX_SIZE${NC}"
else
    echo -e "${RED}✗ Source VSIX not found${NC}"
    echo -e "${YELLOW}  Expected: $VSIX_PATH${NC}"
fi

# Test 4: Create test file and check language association
echo -e "\n${CYAN}Test 4: Language Association Test${NC}"
TEST_FILE="/tmp/test_sona_ext_$$.sona"

cat > "$TEST_FILE" << 'EOF'
// Sona test file
print("Hello from Sona!")

let x = 42;
let name = "World";

function greet(name) {
    return "Hello, " + name;
}
EOF

echo -e "${GREEN}✓ Created test file: $TEST_FILE${NC}"
echo -e "${GRAY}  To test syntax highlighting:${NC}"
echo -e "${GRAY}    code $TEST_FILE${NC}"

# Summary
echo -e "\n${CYAN}=== Summary ===${NC}\n"

PASS_COUNT=0
TOTAL_TESTS=3

if [[ "$EXTENSION_INSTALLED" == true ]]; then
    ((PASS_COUNT++))
fi

if [[ -d "$EXT_DIR" ]] && [[ -f "$EXT_DIR/package.json" ]]; then
    ((PASS_COUNT++))
fi

if [[ -f "$VSIX_PATH" ]]; then
    ((PASS_COUNT++))
fi

echo -e "Tests passed: ${PASS_COUNT}/${TOTAL_TESTS}"

if [[ $PASS_COUNT -eq $TOTAL_TESTS ]]; then
    echo -e "\n${GREEN}✅ Extension verification PASSED!${NC}"
    echo -e "\n${CYAN}Next Steps:${NC}"
    echo -e "  1. Open VS Code: ${GRAY}code${NC}"
    echo -e "  2. Open test file: ${GRAY}code $TEST_FILE${NC}"
    echo -e "  3. Verify syntax highlighting works"
    echo -e "  4. Check status bar for extension indicator"
    exit 0
else
    echo -e "\n${YELLOW}⚠ Some tests failed${NC}"
    echo -e "\n${CYAN}To fix:${NC}"
    echo -e "  1. Run installation script: ${GRAY}./install-extension.sh${NC}"
    echo -e "  2. Restart VS Code"
    echo -e "  3. Run verification again"
    exit 1
fi
