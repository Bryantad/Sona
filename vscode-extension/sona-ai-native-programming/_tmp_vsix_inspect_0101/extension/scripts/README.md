# 🔧 Sona VSIX Build Scripts

This directory contains build, validation, and packaging scripts for the Sona VS Code extension.

---

## 📜 Scripts Overview

### `validate-metadata.js` ⭐ **CRITICAL**

**Purpose:** Enforces authoritative categories and keywords for Marketplace discoverability.

**What It Does:**

- ✅ Validates all 3 required categories are present
- ✅ Validates all 9 required core keywords are present
- ⚠️ Warns if supplemental keywords are missing
- ✅ Checks version format (X.Y.Z or X.Y.Z.W)
- ⚠️ Validates display name and description

**Usage:**

```bash
# Manual validation
node scripts/validate-metadata.js

# Via npm (recommended)
npm run validate-metadata
```

**Exit Codes:**

- `0` = Validation passed ✅
- `1` = Validation failed (blocks build) ❌

**When It Runs:**

- Before every `npm run package`
- Before every `npm run build`
- Before every `vscode:prepublish`
- Manual: `npm run validate-metadata`

**Required Categories (ALL 3):**

- "Programming Languages"
- "AI"
- "Other"

**Required Core Keywords (ALL 9):**

- "ai-native"
- "cognitive-programming"
- "adhd-friendly"
- "working-memory"
- "focus-mode"
- "neurodivergent"
- "ai-collaboration"
- "azure-openai"
- "revolutionary"

**See Also:** `../METADATA_AUTHORITY.md` for complete documentation

---

## 🔄 Script Integration in package.json

```json
{
  "scripts": {
    "validate-metadata": "node scripts/validate-metadata.js",
    "vscode:prepublish": "npm run validate-metadata && python ../../scripts/prepare_extension_runtime.py && npm run compile",
    "prebuild": "npm run validate-metadata",
    "build": "npm run compile && npm run package",
    "package": "npm run validate-metadata && vsce package",
    "package:minor": "npm version minor && npm run validate-metadata && vsce package",
    "package:patch": "npm version patch && npm run validate-metadata && vsce package",
    "test": "npm run validate-metadata"
  }
}
```

**This ensures:**

1. **Every build** validates metadata
2. **Every package** validates metadata
3. **Every publish** validates metadata
4. **No drift** from authoritative standards

---

## 🚀 Build Workflow

### Standard Build (with validation)

```bash
# 1. Validate metadata
npm run validate-metadata

# 2. Compile TypeScript
npm run compile

# 3. Package VSIX (includes validation)
npm run package
```

**Output:** `sona-ai-native-programming-<version>.vsix`

### Quick Build (all-in-one)

```bash
npm run build
```

**Does:**

1. Runs metadata validation
2. Compiles TypeScript
3. Packages VSIX

### Version Bump + Package

```bash
# Patch version (0.9.6 → 0.9.7)
npm run package:patch

# Minor version (0.9.6 → 0.10.0)
npm run package:minor
```

**Does:**

1. Bumps version in package.json
2. Runs metadata validation
3. Packages VSIX with new version

---

## ✅ Validation Output Examples

### ✅ Success (all checks pass)

```
╔════════════════════════════════════════════════════════════════════════════╗
║                    SONA VSIX METADATA VALIDATOR                            ║
║                                                                            ║
║  Enforcing authoritative categories & keywords for Marketplace success     ║
╚════════════════════════════════════════════════════════════════════════════╝

📂 Validating Categories...
✅ All required categories present:
   ✓ "Programming Languages"
   ✓ "AI"
   ✓ "Other"

🔑 Validating Keywords...
✅ All required CORE keywords present:
   ✓ "ai-native"
   ✓ "cognitive-programming"
   ✓ "adhd-friendly"
   ✓ "working-memory"
   ✓ "focus-mode"
   ✓ "neurodivergent"
   ✓ "ai-collaboration"
   ✓ "azure-openai"
   ✓ "revolutionary"
✅ All recommended SUPPLEMENTAL keywords present

🔢 Validating Version...
✅ Valid version: 0.9.6

📛 Validating Display Name...
✅ Display name: "Sona: AI-Native Programming with Cognitive Accessibility"

📝 Validating Description...
✅ Description present (150 chars)

════════════════════════════════════════════════════════════════════════════
📊 VALIDATION SUMMARY REPORT
════════════════════════════════════════════════════════════════════════════

📦 Extension Details:
   Name: sona-ai-native-programming
   Display Name: Sona: AI-Native Programming with Cognitive Accessibility
   Version: 0.9.6
   Publisher: Waycoreinc

📂 Categories:
   - Programming Languages
   - AI
   - Other

🔑 Keywords:
   Total: 25 keywords
   Core (required): 9/9
   Supplemental (recommended): 15/15

════════════════════════════════════════════════════════════════════════════
✅ VALIDATION PASSED - Safe to build VSIX
════════════════════════════════════════════════════════════════════════════

All required categories and keywords are present.
This build maintains the discoverability standards of v0.9.0.
```

### ❌ Failure (missing required items)

```
╔════════════════════════════════════════════════════════════════════════════╗
║                    SONA VSIX METADATA VALIDATOR                            ║
║                                                                            ║
║  Enforcing authoritative categories & keywords for Marketplace success     ║
╚════════════════════════════════════════════════════════════════════════════╝

📂 Validating Categories...

❌ BLOCKER: Missing required categories:
   - "AI"

Required categories (must include ALL):
   - "Programming Languages"
   - "AI"
   - "Other"

🔑 Validating Keywords...

❌ BLOCKER: Missing required CORE keywords:
   - "adhd-friendly"
   - "focus-mode"

Required CORE keywords (must include ALL):
   - "ai-native"
   - "cognitive-programming"
   - "adhd-friendly"
   - "working-memory"
   - "focus-mode"
   - "neurodivergent"
   - "ai-collaboration"
   - "azure-openai"
   - "revolutionary"

════════════════════════════════════════════════════════════════════════════
❌ VALIDATION FAILED - DO NOT BUILD VSIX
════════════════════════════════════════════════════════════════════════════

Fix the issues above before packaging.
Missing categories/keywords will reduce Marketplace discoverability.
```

**Build stops here** - VSIX not created ❌

---

## 🔍 Troubleshooting

### Problem: "package.json not found"

**Solution:** Run from extension directory:

```bash
cd vscode-extension/sona-ai-native-programming
npm run validate-metadata
```

### Problem: Validation fails but metadata looks correct

**Solution:** Check for typos in categories/keywords:

```bash
# Categories are case-sensitive: "AI" not "ai"
# Keywords must match exactly: "adhd-friendly" not "adhd_friendly"
```

### Problem: Want to skip validation temporarily (NOT RECOMMENDED)

**Solution:** Run vsce directly (bypasses validation):

```bash
vsce package  # Skips validation - use with extreme caution
```

**WARNING:** Skipping validation can result in reduced Marketplace discoverability.

### Problem: Validation passes but build fails

**Solution:** Check TypeScript compilation:

```bash
npm run compile  # Run compiler separately to see errors
```

---

## 📚 Documentation References

- **Metadata Authority:** `../METADATA_AUTHORITY.md` - Complete category/keyword documentation
- **Extension Docs:** `../README.md` - User-facing extension documentation
- **Validation Script:** `./validate-metadata.js` - Validator source code
- **Sona Project:** `../../README.md` - Main project documentation

---

## 🔐 Maintenance

### When to Update This Script

**Update validator when:**

1. VS Code Marketplace algorithm changes
2. Sona positioning evolves (approved by Project Lead + Marketing)
3. New critical keywords identified through analytics
4. Bug fixes or improvements to validation logic

**Update Process:**

1. Modify `validate-metadata.js`
2. Update `METADATA_AUTHORITY.md`
3. Test with: `npm run validate-metadata`
4. Document changes in version history
5. Notify team of new requirements

### Version History

| Version | Date        | Changes                                               |
| ------- | ----------- | ----------------------------------------------------- |
| 1.0     | Oct 6, 2025 | Initial validator with 3 categories + 9 core keywords |

---

## ✅ Quick Reference

**Validate metadata:**

```bash
npm run validate-metadata
```

**Build VSIX (with validation):**

```bash
npm run package
```

**Full build workflow:**

```bash
npm run build
```

**Version bump + package:**

```bash
npm run package:patch  # 0.9.6 → 0.9.7
npm run package:minor  # 0.9.6 → 0.10.0
```

**Manual validation (one-liner):**

```bash
node -e "const m=require('./package.json');const needCats=['Programming Languages','AI','Other'];const needK=['ai-native','cognitive-programming','adhd-friendly','working-memory','focus-mode','neurodivergent','ai-collaboration','azure-openai','revolutionary'];for(const c of needCats)if(!(m.categories||[]).includes(c)){console.error('BLOCKER: missing category '+c);process.exit(1);}for(const k of needK)if(!(m.keywords||[]).includes(k)){console.error('BLOCKER: missing keyword '+k);process.exit(1);}console.log('✅ Categories & keywords verified');"
```

---

**End of Scripts Documentation**
