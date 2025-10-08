# Sona VS Code Extension - Version Comparison

## Overview

There are **TWO different VS Code extensions** for Sona in this repository:

1. **v0.9.4 (Simple JavaScript)** ← **USE THIS ONE** ✅
2. **TypeScript Development Version** ← **Currently Broken** ❌

## v0.9.4 Extension (RECOMMENDED)

**Location:** `sona-ai-native-programming-0.9.4/`

### Characteristics

- **Type:** Simple JavaScript extension
- **Dependencies:** NONE (no node_modules required)
- **Build Required:** NO
- **Status:** ✅ **PRODUCTION READY**
- **Size:** ~345 KB

### What It Provides

✅ **Syntax Highlighting** - Full TextMate grammar
✅ **Language Configuration** - Brackets, comments, indentation
✅ **Code Snippets** - Quick templates
✅ **File Icons** - Custom `.sona` file icon
✅ **Settings** - Type checking configuration
✅ **Activation** - Opens automatically with `.sona` files

### What It Does NOT Provide

❌ AI Features (explain, optimize)
❌ REPL integration
❌ Runtime verification
❌ Advanced LSP features
❌ Command palette commands (except basic hello world)

### File Structure

```
sona-ai-native-programming-0.9.4/
├── package.json                      # Extension manifest (simple)
├── extension.js                      # Basic activation script (25 lines)
├── language-configuration.json       # Language rules
├── syntaxes/
│   └── sona.tmLanguage.json         # Syntax highlighting
├── snippets/
│   └── sona.json                    # Code snippets
├── examples/                         # Example .sona files
├── sona/                            # Python stdlib (22+ modules)
└── sona-ai-native-programming-0.9.4.vsix  # Pre-built VSIX ← Install this!
```

### Installation

```bash
# Windows
.\install-extension.ps1

# Linux/Mac
./install-extension.sh
```

### Pros

✅ Works out of the box
✅ No dependency hell
✅ Small and fast
✅ Stable and tested
✅ Perfect for basic editing

### Cons

❌ Limited features
❌ No AI integration
❌ No command palette commands

---

## TypeScript Extension (BROKEN - DO NOT USE)

**Location:** `vscode-extension/sona-ai-native-programming/`

### Characteristics

- **Type:** Complex TypeScript extension
- **Dependencies:** axios, @types/vscode
- **Build Required:** YES (npm install, tsc compile)
- **Status:** ❌ **BROKEN - DEPENDENCY ISSUES**
- **Size:** ~1.1 MB (with node_modules)

### What It's SUPPOSED to Provide

🎯 **AI Features** - Explain code, optimize, etc.
🎯 **REPL Integration** - Open REPL from VS Code
🎯 **Runtime Verification** - Check Python installation
🎯 **Focus Mode** - Cognitive accessibility
🎯 **Command Palette** - 10 commands
🎯 **Status Bar** - Extension status indicator

### Current Issues (Why It's Broken)

❌ **Missing Dependencies**
   - Requires axios but not included in VSIX
   - node_modules excluded by .vscodeignore
   - Build doesn't bundle dependencies

❌ **Case-Sensitivity Bug**
   - Extension ID uses capital 'W' in code
   - Should be lowercase 'w'
   - Breaks runtime commands

❌ **Build Complexity**
   - Requires TypeScript compilation
   - Needs npm install before packaging
   - Build process not documented

❌ **Incomplete Packaging**
   - .vscodeignore excludes node_modules
   - axios not bundled into output
   - Extension crashes on load

### File Structure

```
vscode-extension/sona-ai-native-programming/
├── package.json                     # Complex manifest (150+ lines)
├── tsconfig.json                    # TypeScript config
├── .vscodeignore                    # ← Excludes node_modules (problem!)
├── src/
│   ├── extension.ts                 # Main extension (200+ lines)
│   └── runtime.ts                   # Runtime utilities
├── out/                             # Compiled JS (when built)
├── node_modules/                    # Dependencies (when installed)
└── NO VSIX YET                      # Broken build
```

### What Needs Fixing

To make the TypeScript extension work:

1. **Bundle Dependencies**
   ```bash
   # Option A: Use webpack to bundle
   npm install --save-dev webpack
   # Configure webpack.config.js
   
   # Option B: Include dependencies in VSIX
   # Update .vscodeignore to include axios
   ```

2. **Fix Case-Sensitivity**
   ```typescript
   // In runtime.ts, change:
   "Waycoreinc.sona-ai-native-programming"
   // to:
   "waycoreinc.sona-ai-native-programming"
   ```

3. **Document Build Process**
   ```bash
   npm install
   npm run compile
   vsce package
   ```

4. **Test Packaging**
   - Verify axios is in VSIX
   - Check extension loads
   - Test all commands

### Installation (When Fixed)

```bash
cd vscode-extension/sona-ai-native-programming
npm install
npm run compile
vsce package
code --install-extension sona-ai-native-programming-0.9.6.vsix
```

---

## Comparison Table

| Feature | v0.9.4 Simple | TypeScript (Broken) |
|---------|---------------|---------------------|
| **Status** | ✅ Working | ❌ Broken |
| **Dependencies** | None | axios, @types/vscode |
| **Build Required** | No | Yes (npm + tsc) |
| **Size** | 345 KB | 1.1 MB |
| **Syntax Highlighting** | ✅ | ✅ |
| **Language Config** | ✅ | ✅ |
| **Snippets** | ✅ | ✅ |
| **File Icons** | ✅ | ✅ |
| **AI Features** | ❌ | 🎯 (when fixed) |
| **REPL Integration** | ❌ | 🎯 (when fixed) |
| **Command Palette** | 1 command | 10 commands |
| **Status Bar** | ❌ | 🎯 (when fixed) |
| **Focus Mode** | ❌ | 🎯 (when fixed) |

---

## Recommendations

### For Users

**Use v0.9.4 Extension:**
- ✅ If you want syntax highlighting NOW
- ✅ If you don't need AI features
- ✅ If you prefer stable, simple tools
- ✅ If you'll use the Python CLI for running code

**Wait for TypeScript Extension:**
- 🎯 If you need AI integration
- 🎯 If you want REPL in VS Code
- 🎯 If you need focus mode features
- 🎯 If you want command palette integration

### For Developers

**To fix the TypeScript extension:**

1. **Bundle dependencies with webpack:**
   ```bash
   npm install --save-dev webpack webpack-cli ts-loader
   ```

2. **Create webpack.config.js:**
   ```javascript
   module.exports = {
     target: 'node',
     entry: './src/extension.ts',
     output: {
       path: path.resolve(__dirname, 'out'),
       filename: 'extension.js',
       libraryTarget: 'commonjs2'
     },
     externals: {
       vscode: 'commonjs vscode'
     },
     resolve: {
       extensions: ['.ts', '.js']
     },
     module: {
       rules: [{ test: /\.ts$/, use: 'ts-loader' }]
     }
   };
   ```

3. **Update package.json scripts:**
   ```json
   {
     "scripts": {
       "compile": "webpack --mode production",
       "watch": "webpack --mode development --watch",
       "package": "vsce package"
     }
   }
   ```

4. **Fix case-sensitivity in runtime.ts**

5. **Test thoroughly before packaging**

---

## Timeline

**Current (October 2024):**
- ✅ v0.9.4 available and working
- ❌ TypeScript extension broken

**Near Future:**
- 🔧 Fix TypeScript extension dependencies
- 🔧 Bundle axios with webpack
- 🔧 Fix case-sensitivity bugs
- 🔧 Add comprehensive testing

**Long Term:**
- 🎯 LSP server implementation
- 🎯 Advanced AI features
- 🎯 Debugger integration
- 🎯 Multi-language support

---

## Conclusion

**For immediate use:** Install v0.9.4 with the provided scripts.

**For development:** Help fix the TypeScript extension by tackling the dependency bundling issue.

**Questions?** See INSTALL_EXTENSION.md or file an issue on GitHub.
