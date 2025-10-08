# Complete Guide: Installing Sona VS Code Extension

**The definitive guide to getting Sona syntax highlighting working in VS Code**

---

## 🎯 Goal

Install a working Sona VS Code extension that provides:
- ✅ Syntax highlighting for `.sona` files
- ✅ Language configuration (auto-close, comments)
- ✅ Code snippets
- ✅ Custom file icons

---

## 📋 Prerequisites

1. **VS Code installed** - Download from https://code.visualstudio.com/
2. **`code` command available** in terminal/command prompt
   - In VS Code: Press `Ctrl+Shift+P` → Type "Shell Command: Install 'code' command in PATH"
3. **Sona repository cloned** - This guide assumes you're in the repo root

---

## ⚡ Quick Installation (5 minutes)

### Step 1: Open Terminal in Sona Directory

```bash
cd /path/to/Sona
```

### Step 2: Run Installation Script

**Windows PowerShell:**
```powershell
.\install-extension.ps1
```

**Linux/Mac:**
```bash
./install-extension.sh
```

### Step 3: Restart VS Code

Close all VS Code windows and reopen.

### Step 4: Test It

Create a test file:
```bash
echo 'print("Hello from Sona!")' > test.sona
code test.sona
```

**Expected:** Keywords and strings are highlighted in color.

---

## 🔍 What the Scripts Do

The installation scripts automatically:

1. ✅ Check if VS Code is installed
2. ✅ Locate the v0.9.4 VSIX file
3. ✅ Uninstall any existing Sona extensions
4. ✅ Install the v0.9.4 extension
5. ✅ Verify installation succeeded

**No manual steps required!**

---

## 🛠️ Manual Installation (if scripts fail)

### Option A: Via VS Code UI

1. Open VS Code
2. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
3. Type: **"Extensions: Install from VSIX"**
4. Navigate to: `Sona/sona-ai-native-programming-0.9.4/sona-ai-native-programming-0.9.4.vsix`
5. Click **"Install"**
6. Click **"Reload"** when prompted

### Option B: Via Command Line

```bash
cd /path/to/Sona
code --install-extension sona-ai-native-programming-0.9.4/sona-ai-native-programming-0.9.4.vsix
```

Then restart VS Code.

---

## ✅ Verification

### Automatic Verification

Run the verification script:

**Windows:**
```powershell
.\verify-extension.ps1
```

**Linux/Mac:**
```bash
./verify-extension.sh
```

### Manual Verification

1. **Check Extensions List:**
   - Open Extensions view (Ctrl+Shift+X)
   - Search for "Sona"
   - Should see: "Sona AI-Native Programming Language v0.9.4"

2. **Test Syntax Highlighting:**
   - Create file: `test.sona`
   - Add code: `print("Hello!")`
   - Verify text is colored

3. **Check Language Mode:**
   - Look at bottom-right corner of VS Code
   - Should show: "Sona"

4. **Test Command:**
   - Press F1
   - Type "Sona: Hello World"
   - Should show message: "Hello from Sona AI-Native Programming Language!"

---

## 🎨 What You Get

### Syntax Highlighting

All language elements are colored:

```sona
// Comments - gray/green
let x = 42;                           // Keywords: let, numbers: 42
let name = "Hello, World!";           // Strings: yellow/orange

function greet(name) {                // Keywords: function, return
    return "Hello, " + name;
}

// AI-specific constructs
ai_explain(code, "beginner");         // AI functions
working_memory("context", "load");
focus_mode("debugging", "25min");
```

### Auto-Completion

Type these shortcuts and press Tab:

| Shortcut | Expands To |
|----------|------------|
| `func` | Function template |
| `if` | If statement |
| `for` | For loop |
| `while` | While loop |
| `ai` | AI function call |
| `wm` | Working memory |
| `fm` | Focus mode |

### Language Features

- **Auto-closing:** `()`, `{}`, `[]`, `""`, `''`
- **Comment toggle:** `Ctrl+/` (Windows/Linux) or `Cmd+/` (Mac)
- **Bracket matching:** Highlights matching brackets
- **Indentation:** Smart indentation

---

## ❌ What's NOT Included

This extension is **editor support only**. It does NOT provide:

- ❌ AI features (explain, optimize commands)
- ❌ REPL integration
- ❌ Code execution
- ❌ Debugging
- ❌ Linting/error checking

**For these features, use the Python CLI:**

```bash
# Install Sona
pip install -e .

# Run REPL
sona repl

# Execute files
sona run file.sona

# Get help
sona --help
```

---

## 🔧 Troubleshooting

### Problem: "command 'code' not found"

**Solution:**
1. Open VS Code
2. Press `Ctrl+Shift+P`
3. Type: "Shell Command: Install 'code' command in PATH"
4. Restart terminal

### Problem: Extension not activating

**Symptoms:** No syntax highlighting, file shows as "Plain Text"

**Solutions:**
1. Ensure file has `.sona` extension
2. Open a `.sona` file (triggers activation)
3. Try: View → Command Palette → "Change Language Mode" → "Sona"
4. Check Output: View → Output → "Extension Host" for errors
5. Restart VS Code

### Problem: Syntax highlighting not working

**Solutions:**
1. Close and reopen the file
2. Try a different color theme: File → Preferences → Color Theme
3. Verify extension is installed: Extensions view → Search "Sona"
4. Reload VS Code: `Ctrl+Shift+P` → "Developer: Reload Window"

### Problem: Installation script fails

**Error: "VS Code 'code' command not found"**
- Install VS Code shell integration (see above)

**Error: "VSIX file not found"**
- Ensure you're running the script from the Sona repository root

**Error: "Permission denied"** (Linux/Mac)
- Run: `chmod +x install-extension.sh`
- Or use: `bash install-extension.sh`

### Problem: Extension conflicts with old version

**Solution:**
1. Uninstall all Sona extensions:
   ```bash
   code --uninstall-extension waycoreinc.sona-ai-native-programming
   ```
2. Restart VS Code
3. Run installation script again

---

## 📚 Additional Resources

### Documentation Files

- **QUICK_INSTALL.md** - One-page quick reference
- **INSTALL_EXTENSION.md** - Detailed installation guide
- **EXTENSION_COMPARISON.md** - Comparison of extension versions
- **sona-ai-native-programming-0.9.4/README.md** - Extension-specific docs

### Scripts

- **install-extension.sh** - Linux/Mac installer
- **install-extension.ps1** - Windows PowerShell installer
- **verify-extension.sh** - Linux/Mac verification
- **verify-extension.ps1** - Windows PowerShell verification

### Example Files

Located in `sona-ai-native-programming-0.9.4/examples/`:
- Cognitive accessibility examples
- AI function examples
- Language feature demonstrations

---

## 🚀 Next Steps

After installation:

1. **Edit Sona Files**
   - Create `.sona` files
   - Enjoy syntax highlighting
   - Use code snippets

2. **Use the REPL**
   ```bash
   sona repl
   ```

3. **Run Sona Programs**
   ```bash
   sona run myprogram.sona
   ```

4. **Read the Docs**
   - Main README.md
   - CHANGELOG.md
   - Language documentation

5. **Explore Examples**
   ```bash
   cd examples/
   ls *.sona
   ```

---

## ❓ FAQ

**Q: Why use v0.9.4 instead of the newer TypeScript extension?**  
A: The TypeScript extension has dependency issues. v0.9.4 is stable and works perfectly for editing.

**Q: When will the TypeScript extension be fixed?**  
A: It's in development. See EXTENSION_COMPARISON.md for details.

**Q: Can I use both extensions?**  
A: No, they conflict. Use v0.9.4 for now.

**Q: How do I update the extension?**  
A: Run the installation script again. It uninstalls the old version first.

**Q: Where are the AI features?**  
A: Use the Python CLI (`sona repl`) for AI features.

**Q: Can I customize the syntax highlighting?**  
A: Yes, via VS Code color themes or by modifying the TextMate grammar.

---

## 🐛 Getting Help

If you encounter issues:

1. **Check this guide** - Most issues are covered above
2. **Run verification script** - `./verify-extension.sh` or `.\verify-extension.ps1`
3. **Check Output panel** - View → Output → Extension Host
4. **Search issues** - https://github.com/Bryantad/Sona/issues
5. **File a bug** - Create a new issue with details

Include this info in bug reports:
- OS and version
- VS Code version
- Error messages from Output panel
- Steps to reproduce

---

## ✨ Success Checklist

After following this guide, you should have:

- ✅ VS Code with Sona extension installed
- ✅ Syntax highlighting working for `.sona` files
- ✅ Custom file icons for `.sona` files
- ✅ Code snippets available
- ✅ Auto-closing brackets working
- ✅ Test file created and verified

**Congratulations! You're ready to write Sona code in VS Code! 🎉**

---

**Last Updated:** October 2024  
**Extension Version:** 0.9.4  
**Repository:** https://github.com/Bryantad/Sona
