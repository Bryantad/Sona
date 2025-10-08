# Installing Sona VS Code Extension - Clean Installation Guide

## Problem Summary

The TypeScript-based extension in `vscode-extension/sona-ai-native-programming/` has dependency issues (missing axios, complex build requirements). This guide uses the **working v0.9.4 VSIX** that's already included in the repository.

## Solution: Use the Pre-Built v0.9.4 VSIX

The repository includes a working, dependency-free extension at:
```
sona-ai-native-programming-0.9.4/sona-ai-native-programming-0.9.4.vsix
```

This is a **simple JavaScript extension** with:
- ✅ No external dependencies (no axios, no node_modules)
- ✅ No TypeScript compilation needed
- ✅ Syntax highlighting for `.sona` files
- ✅ Basic language support
- ✅ Snippets
- ✅ File icon theme

## Installation Steps

### Step 1: Uninstall Any Existing Sona Extensions

**Option A: Via VS Code UI**
1. Open VS Code
2. Click Extensions icon (Ctrl+Shift+X)
3. Search for "Sona"
4. Click the gear icon on any Sona extension
5. Click "Uninstall"
6. Reload VS Code when prompted

**Option B: Via Command Line**
```bash
# List installed extensions
code --list-extensions | grep -i sona

# Uninstall (replace with actual extension ID)
code --uninstall-extension waycoreinc.sona-ai-native-programming
```

**Option C: Manual Removal (if above fails)**
```bash
# Windows
rm -rf "%USERPROFILE%\.vscode\extensions\waycoreinc.sona*"

# Linux/Mac
rm -rf ~/.vscode/extensions/waycoreinc.sona*
```

### Step 2: Install the v0.9.4 VSIX

**Option A: Via VS Code UI (RECOMMENDED)**
1. Open VS Code
2. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
3. Type "Extensions: Install from VSIX"
4. Navigate to: `Sona/sona-ai-native-programming-0.9.4/sona-ai-native-programming-0.9.4.vsix`
5. Click "Install"
6. Reload VS Code when prompted

**Option B: Via Command Line**
```bash
cd /path/to/Sona
code --install-extension sona-ai-native-programming-0.9.4/sona-ai-native-programming-0.9.4.vsix
```

### Step 3: Verify Installation

1. **Check Extensions:**
   - Open Extensions view (Ctrl+Shift+X)
   - Search for "Sona"
   - Should see "Sona AI-Native Programming Language v0.9.4"

2. **Test Syntax Highlighting:**
   - Create a new file: `test.sona`
   - Add some code:
     ```sona
     // Test file
     print("Hello from Sona!")
     
     let x = 42;
     ```
   - Keywords should be highlighted

3. **Check File Icon:**
   - `.sona` files should have a custom icon in the file explorer

## What This Extension Provides

✅ **Syntax Highlighting** - Full TextMate grammar for Sona language
✅ **Language Configuration** - Auto-closing brackets, comments, etc.
✅ **Snippets** - Quick code templates
✅ **File Icons** - Custom icon for `.sona` files
✅ **Type Checking Settings** - Configurable via settings

## What This Extension Does NOT Provide

❌ **AI Features** - No AI explain/optimize commands (those were in the broken TypeScript version)
❌ **REPL Integration** - Use the Python REPL separately
❌ **Linting** - Use standalone tools

The v0.9.4 extension focuses on **core language support** without complex dependencies.

## Troubleshooting

### Extension Not Activating

The extension activates automatically when you open a `.sona` file. Try:
1. Open or create a `.sona` file
2. Check Output panel: View → Output → Select "Extension Host"
3. Look for: "Sona AI-Native Programming Language extension is now active!"

### Syntax Highlighting Not Working

1. Check file extension is `.sona`
2. Try closing and reopening the file
3. Try: View → Command Palette → "Change Language Mode" → Select "Sona"

### Extension Commands Not Found

The v0.9.4 extension only has one command: `sona.helloWorld`
- Press F1
- Type "Hello World"
- Should see "Hello from Sona AI-Native Programming Language!"

## Using Sona REPL

The extension provides editor support. To run Sona code:

```bash
# Install Sona Python package
pip install -e .

# Run REPL
sona repl

# Run a file
sona run test.sona
```

## Next Steps

Once the v0.9.4 extension is working:
- Edit `.sona` files with syntax highlighting
- Use the Python CLI for running code
- Check the main README.md for Sona language features

## Files Included in v0.9.4 VSIX

```
sona-ai-native-programming-0.9.4/
├── package.json              # Extension manifest
├── extension.js              # Simple activation script
├── language-configuration.json
├── syntaxes/
│   └── sona.tmLanguage.json  # Syntax highlighting rules
├── snippets/
│   └── sona.json             # Code snippets
├── examples/
│   └── *.sona                # Example files
└── sona/                     # Python stdlib (22+ modules)
```

Total size: ~345 KB
No node_modules, no external dependencies!

---

**This is the stable, working extension. Use this while the TypeScript version is being debugged.**
