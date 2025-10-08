# Sona VS Code Extension v0.9.4

**Production-ready extension for Sona language support in Visual Studio Code**

## Quick Install

### Windows
```powershell
cd /path/to/Sona
.\install-extension.ps1
```

### Linux/Mac
```bash
cd /path/to/Sona
./install-extension.sh
```

### Manual Install
```bash
code --install-extension sona-ai-native-programming-0.9.4.vsix
```

## Features

### ✅ What's Included

- **Syntax Highlighting** - Full TextMate grammar for Sona language
- **Language Configuration** - Auto-closing brackets, comments, indentation
- **Code Snippets** - Quick templates for common patterns
- **File Icons** - Custom icon for `.sona` files
- **Type Checking Config** - Settings for type checking mode

### ❌ What's NOT Included

This is a **basic language support extension**. It does NOT include:

- AI features (explain, optimize commands)
- REPL integration
- LSP server
- Advanced code analysis

For these features, use the Python CLI directly:

```bash
# Install Sona
pip install -e .

# Use REPL
sona repl

# Run files
sona run file.sona
```

## Extension Details

**Publisher:** Waycoreinc  
**Extension ID:** waycoreinc.sona-ai-native-programming  
**Version:** 0.9.4  
**Size:** ~345 KB  
**Type:** JavaScript (no dependencies)  

## File Structure

```
sona-ai-native-programming-0.9.4/
├── sona-ai-native-programming-0.9.4.vsix    # Pre-built extension (install this!)
├── package.json                             # Extension manifest
├── extension.js                             # Activation script
├── language-configuration.json              # Language rules
├── syntaxes/
│   └── sona.tmLanguage.json                # Syntax highlighting grammar
├── snippets/
│   └── sona.json                           # Code snippets
├── examples/
│   └── *.sona                              # Example files
└── sona/                                   # Python stdlib (22+ modules)
```

## Activation

The extension activates automatically when you:
- Open a `.sona` file
- Create a new `.sona` file

You'll see a message in the Output panel (Extension Host):
```
Sona AI-Native Programming Language extension is now active!
```

## Available Commands

- **Sona: Hello World** - Test command to verify extension is working

That's it! This is a minimal extension focused on editor support.

## Settings

Access via: File → Preferences → Settings → Sona

- **sona.typeChecking** - Type checking mode
  - `off` - No type checking (default)
  - `warn` - Type checking with warnings
  - `on` - Strict type checking

## Language Features

### Syntax Highlighting

Keywords, strings, comments, numbers, and operators are highlighted:

```sona
// Comments are highlighted
let x = 42;                    // Numbers
let name = "Hello, World!";    // Strings

function greet(name) {         // Keywords
    return "Hello, " + name;
}

// AI constructs
ai_explain(code, "beginner");
working_memory("context", "load");
focus_mode("task", "25min");
```

### Auto-Completion

Type shortcuts and press Tab:

- `func` → function template
- `if` → if statement
- `for` → for loop
- `ai` → AI function template

### Bracket Matching

Auto-closing for:
- `()` - Parentheses
- `{}` - Curly braces
- `[]` - Square brackets
- `""` - Double quotes
- `''` - Single quotes

### Comment Toggling

- Line comment: `//`
- Block comment: `/* ... */`

Use `Ctrl+/` (Windows/Linux) or `Cmd+/` (Mac) to toggle comments.

## Testing the Extension

1. **Create test file:**
   ```bash
   echo 'print("Hello from Sona!")' > test.sona
   ```

2. **Open in VS Code:**
   ```bash
   code test.sona
   ```

3. **Verify:**
   - Syntax highlighting appears
   - File icon shows Sona logo
   - Language mode shows "Sona" in bottom-right

## Troubleshooting

### Extension Not Activating

**Symptoms:** No syntax highlighting, language mode shows "Plain Text"

**Solutions:**
1. Check file extension is `.sona`
2. Try: View → Command Palette → "Change Language Mode" → "Sona"
3. Restart VS Code
4. Check Output panel: View → Output → "Extension Host" for errors

### Syntax Highlighting Not Working

**Solutions:**
1. Close and reopen the file
2. Verify extension is installed: Extensions view → Search "Sona"
3. Check theme compatibility (try a different color theme)
4. Reload window: Ctrl+Shift+P → "Developer: Reload Window"

### Command Not Found

**Remember:** This extension only has one command: "Sona: Hello World"

For AI features, REPL, and other commands, use the Python CLI:
```bash
sona --help
```

## Uninstalling

### Via VS Code
1. Extensions view (Ctrl+Shift+X)
2. Search "Sona"
3. Click gear icon → Uninstall
4. Reload VS Code

### Via Command Line
```bash
code --uninstall-extension waycoreinc.sona-ai-native-programming
```

## Verification

Run the verification script to check installation:

```bash
# Windows
.\verify-extension.ps1

# Linux/Mac
./verify-extension.sh
```

## Upgrading

To install a newer version:

1. Uninstall current version
2. Install new VSIX
3. Reload VS Code

The installer scripts handle this automatically.

## FAQ

**Q: Where are the AI features?**  
A: This is a basic language support extension. Use the Python CLI for AI features:
```bash
sona repl
>>> ai_explain("code here", "beginner")
```

**Q: Can I use the REPL from VS Code?**  
A: Not with this extension. Open a terminal in VS Code and run `sona repl`.

**Q: Why is this extension so simple?**  
A: It's designed to be lightweight, stable, and dependency-free. Advanced features are being developed in a separate extension.

**Q: When will advanced features be available?**  
A: The TypeScript extension with AI integration is in development. See EXTENSION_COMPARISON.md for details.

**Q: Can I contribute?**  
A: Yes! See Contributing.md in the main repository.

## Related Files

- **INSTALL_EXTENSION.md** - Detailed installation guide
- **QUICK_INSTALL.md** - Quick reference card
- **EXTENSION_COMPARISON.md** - Comparison with TypeScript version
- **verify-extension.sh/.ps1** - Verification scripts

## Support

- **Issues:** https://github.com/Bryantad/Sona/issues
- **Discussions:** https://github.com/Bryantad/Sona/discussions
- **Documentation:** Main README.md

## License

MIT - See LICENSE file

---

**This extension provides reliable, stable language support for Sona. Enjoy coding! 🚀**
