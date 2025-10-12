# Sona VS Code Extension - v0.9.6 Release Guide

## 📦 Package Extension for Release

This guide walks you through packaging the Sona VS Code extension for the v0.9.6 release.

---

## ✅ Pre-Flight Checklist

Before packaging, verify:

- [x] **Version:** 0.9.6 in package.json
- [x] **Publisher:** Waycoreinc
- [x] **30 Modules:** All stdlib modules ready
- [ ] **Compiled:** TypeScript compiled to JavaScript
- [ ] **Tests:** Extension tests passing
- [ ] **README:** Updated with v0.9.6 features
- [ ] **CHANGELOG:** v0.9.6 entry added

---

## 🛠️ Build Steps

### Step 1: Install Dependencies

```powershell
# If not already installed
npm install
```

### Step 2: Compile TypeScript

```powershell
npm run compile
```

Expected output:
```
> sona-ai-native-programming@0.9.6 compile
> tsc -p ./
```

### Step 3: Verify Compilation

```powershell
# Check that out/ directory has compiled .js files
Get-ChildItem out -Recurse -Filter *.js
```

### Step 4: Install VSCE (VS Code Extension Manager)

```powershell
# If not already installed globally
npm install -g @vscode/vsce
```

### Step 5: Package the Extension

```powershell
# Create .vsix package
vsce package
```

This creates: `sona-ai-native-programming-0.9.6.vsix`

---

## 🧪 Test the Package

### Test 1: Install Locally

```powershell
# Install in VS Code
code --install-extension sona-ai-native-programming-0.9.6.vsix
```

### Test 2: Verify Installation

1. Open VS Code
2. Press `Ctrl+Shift+X` (Extensions)
3. Search for "Sona"
4. Verify version shows "0.9.6"

### Test 3: Test Functionality

1. Create a new `.sona` file
2. Verify syntax highlighting works
3. Test the REPL command
4. Test Focus Mode

---

## 📤 Publishing to Marketplace

### Option 1: Publish via VSCE

```powershell
# Publish to VS Code Marketplace
vsce publish
```

You'll need a Personal Access Token (PAT) from Azure DevOps.

### Option 2: Manual Upload

1. Go to: https://marketplace.visualstudio.com/manage
2. Sign in with publisher account (Waycoreinc)
3. Click "New Extension" → "Visual Studio Code"
4. Upload `sona-ai-native-programming-0.9.6.vsix`
5. Fill in details and publish

---

## 📊 Package Information

**Current Build:**
- **File:** sona-ai-native-programming-0.9.6.vsix
- **Size:** ~1.1 MB
- **Version:** 0.9.6
- **Release Date:** October 2025

**What's Included:**
- ✅ Syntax highlighting for .sona files
- ✅ 30-module stdlib support
- ✅ REPL integration
- ✅ Focus Mode
- ✅ AI-native commands (explain, optimize, debug)
- ✅ Cognitive accessibility features

---

## 🔍 Verify Package Contents

```powershell
# Extract and inspect VSIX contents
Expand-Archive sona-ai-native-programming-0.9.6.vsix -DestinationPath .\vsix-inspect -Force
Get-ChildItem .\vsix-inspect -Recurse
```

---

## 🚀 Quick Commands Reference

| Task | Command |
|------|---------|
| Install deps | `npm install` |
| Compile | `npm run compile` |
| Watch mode | `npm run watch` |
| Package | `vsce package` |
| Install locally | `code --install-extension sona-ai-native-programming-0.9.6.vsix` |
| Publish | `vsce publish` |

---

## 📝 Release Notes Template

```markdown
# Sona v0.9.6 - Complete Standard Library

## 🎉 What's New

- **30 Stdlib Modules:** Complete standard library (json, string, math, fs, yaml, toml, hashing, and more)
- **Enhanced Type System:** Improved type checking and validation
- **Better Error Messages:** Clearer diagnostics and suggestions
- **Performance Improvements:** Faster parsing and execution

## 📚 Module Categories

- Core System (12): json, string, math, numbers, boolean, type, comparison, operators, time, date, random, regex
- I/O & OS (4): fs, path, io, env
- Collections (3): collection, queue, stack
- Data Processing (7): csv, encoding, timer, validation, statistics, sort, search
- Advanced (4): uuid, yaml, toml, hashing

## 🔧 Improvements

- Syntax highlighting enhancements
- REPL stability improvements
- Focus Mode refinements
- Better AI command integration

## 📖 Documentation

See STDLIB_30_MODULES.md for complete module reference.
```

---

## ⚠️ Troubleshooting

### Error: "VSCE not found"
```powershell
npm install -g @vscode/vsce
```

### Error: "Compilation failed"
```powershell
# Clean and rebuild
Remove-Item out -Recurse -Force
npm run compile
```

### Error: "Publisher not verified"
```powershell
# Login to publisher account
vsce login Waycoreinc
```

---

## 📋 Post-Release Checklist

- [ ] VSIX uploaded to Marketplace
- [ ] GitHub release created with tag `v0.9.6`
- [ ] VSIX attached to GitHub release
- [ ] README updated on Marketplace
- [ ] Social media announcement
- [ ] Documentation site updated

---

**Ready to package your Sona v0.9.6 extension! 🚀**
