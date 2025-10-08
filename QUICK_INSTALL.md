# Sona VS Code Extension - Quick Installation Reference

## TL;DR - Install Working Extension NOW

```bash
# Windows PowerShell
.\install-extension.ps1

# Linux/Mac
./install-extension.sh
```

That's it! The script handles everything automatically.

---

## What You're Installing

**File:** `sona-ai-native-programming-0.9.4/sona-ai-native-programming-0.9.4.vsix`
**Size:** 345 KB
**Type:** Simple JavaScript extension (NO dependencies)

### What Works ✅

- ✅ Syntax highlighting for `.sona` files
- ✅ Language configuration (brackets, comments, indentation)
- ✅ Code snippets
- ✅ Custom file icons
- ✅ Type checking configuration

### What's NOT Included ❌

- ❌ AI features (explain, optimize commands)
- ❌ REPL integration
- ❌ Advanced LSP features

**Why?** The complex TypeScript extension has dependency issues. This v0.9.4 version is stable and works perfectly for editing `.sona` files.

---

## Manual Installation (if scripts fail)

### Step 1: Uninstall Old Extensions

**Via VS Code:**
1. Open VS Code
2. Extensions view (Ctrl+Shift+X)
3. Search "Sona"
4. Uninstall any found
5. Reload VS Code

**Via Command Line:**
```bash
code --uninstall-extension waycoreinc.sona-ai-native-programming
```

### Step 2: Install v0.9.4 VSIX

**Via VS Code:**
1. Press `Ctrl+Shift+P`
2. Type: "Extensions: Install from VSIX"
3. Select: `sona-ai-native-programming-0.9.4/sona-ai-native-programming-0.9.4.vsix`
4. Click Install
5. Reload VS Code

**Via Command Line:**
```bash
code --install-extension sona-ai-native-programming-0.9.4/sona-ai-native-programming-0.9.4.vsix
```

### Step 3: Test It

Create `test.sona`:
```sona
// Test file
print("Hello from Sona!")

let x = 42;
let name = "World";

// This should be highlighted
function greet(name) {
    return "Hello, " + name;
}
```

**Expected:** Keywords, strings, comments should be colored.

---

## Troubleshooting

### "command 'code' not found"

**Fix:** Install VS Code and enable shell integration:
1. Open VS Code
2. Press `Ctrl+Shift+P`
3. Type: "Shell Command: Install 'code' command in PATH"
4. Restart terminal

### Extension Not Activating

1. Open a `.sona` file (triggers activation)
2. Check: View → Output → Extension Host
3. Should see: "Sona AI-Native Programming Language extension is now active!"

### Syntax Highlighting Not Working

1. Check file extension is `.sona`
2. Close and reopen file
3. Try: View → Command Palette → "Change Language Mode" → "Sona"

---

## What About the TypeScript Extension?

The TypeScript extension in `vscode-extension/sona-ai-native-programming/` has these issues:

1. **Missing dependencies** - Requires axios but not packaged
2. **Complex build** - Needs TypeScript compilation + node_modules
3. **Case-sensitivity bugs** - Extension ID mismatch
4. **Build artifacts** - Missing compiled output

**Until fixed, use v0.9.4!**

---

## File Locations

```
Sona/
├── install-extension.sh         ← Linux/Mac installer
├── install-extension.ps1        ← Windows installer  
├── INSTALL_EXTENSION.md         ← Full installation guide
└── sona-ai-native-programming-0.9.4/
    ├── sona-ai-native-programming-0.9.4.vsix  ← Install this!
    ├── package.json
    ├── extension.js
    ├── syntaxes/
    │   └── sona.tmLanguage.json
    ├── snippets/
    │   └── sona.json
    └── language-configuration.json
```

---

## Next Steps After Installation

1. **Edit `.sona` files** - Enjoy syntax highlighting
2. **Use Sona REPL** - Run `sona repl` in terminal
3. **Run Sona code** - Use `sona run file.sona`
4. **Read docs** - Check main README.md

---

## Support

- **Issues:** https://github.com/Bryantad/Sona/issues
- **Docs:** Main README.md
- **REPL:** `sona --help`

---

**This v0.9.4 extension is production-ready and stable. Use it with confidence!**
