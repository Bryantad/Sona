# 🔒 SONA VSIX METADATA - QUICK REFERENCE

**Lock Date:** October 6, 2025  
**Validator:** `scripts/validate-metadata.js`

---

## ✅ REQUIRED CATEGORIES (ALL 3 - BLOCKING)

```json
"categories": [
  "Programming Languages",
  "AI",
  "Other"
]
```

---

## ✅ REQUIRED CORE KEYWORDS (ALL 9 - BLOCKING)

```json
"keywords": [
  "ai-native",
  "cognitive-programming",
  "adhd-friendly",
  "working-memory",
  "focus-mode",
  "neurodivergent",
  "ai-collaboration",
  "azure-openai",
  "revolutionary"
]
```

---

## ⚙️ SUPPLEMENTAL KEYWORDS (15 - RECOMMENDED)

```json
"keywords": [
  "sona",
  "accessibility",
  "dyslexia-support",
  "programming-language",
  "repl",
  "transpiler",
  "json",
  "merge-patch",
  "deep-update",
  "regex",
  "timeout",
  "adhd",
  "neurodiversity",
  "education",
  "developer-tools"
]
```

---

## 🚀 QUICK COMMANDS

**Validate:**

```bash
npm run validate-metadata
```

**Package (with validation):**

```bash
npm run package
```

**Full build:**

```bash
npm run build
```

---

## 📚 DOCUMENTATION

- **Full Authority Doc:** `METADATA_AUTHORITY.md`
- **Scripts Guide:** `scripts/README.md`
- **Implementation Summary:** `VSIX_METADATA_ENFORCEMENT_COMPLETE.md`

---

## ⚠️ RULES

1. **NEVER remove** required categories/keywords
2. **ALWAYS run** `npm run validate-metadata` before manual edits
3. **GET APPROVAL** from Project Lead + Marketing before changes
4. **UPDATE DOCS** (METADATA_AUTHORITY.md) when changing standards

---

**Missing required items = BUILD BLOCKED ❌**
