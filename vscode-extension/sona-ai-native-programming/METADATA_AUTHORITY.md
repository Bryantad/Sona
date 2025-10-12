# 🔒 Sona VSIX Metadata Authority Document

**Version:** 1.0  
**Date:** October 6, 2025  
**Status:** LOCKED - Non-Negotiable for All Future Releases

---

## 📋 Purpose

This document establishes the **authoritative** categories and keywords that must be included in **every future Sona VSIX release** to preserve:

1. **Marketplace Discoverability** - Ensures Sona appears in relevant searches
2. **Organic Install Factor** - Maintains the "wow + organic install" performance of v0.9.0
3. **Brand Identity** - Preserves Sona's unique positioning as the cognitive-accessibility-first AI-native language

**CRITICAL:** These are **non-negotiable**. Any VSIX missing these elements will have reduced discoverability.

---

## ✅ REQUIRED CATEGORIES (Must Include ALL 3)

```json
"categories": [
  "Programming Languages",
  "AI",
  "Other"
]
```

### Why These Matter:

| Category                  | Purpose                               | Impact                                                  |
| ------------------------- | ------------------------------------- | ------------------------------------------------------- |
| **Programming Languages** | Base discoverability in language tabs | Ensures Sona appears alongside Python, JavaScript, etc. |
| **AI**                    | Listed under AI/LLM extension feeds   | **Major install driver** - captures AI-curious users    |
| **Other**                 | Preserves older backlinks             | Maintains compatibility for generic searches            |

**Validation Rule:** All 3 categories MUST be present. Missing any category = **BLOCKED BUILD**.

---

## ✅ REQUIRED CORE KEYWORDS (Must Include ALL 9)

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

### Why These Matter:

**Cognitive Accessibility Anchors (Unique to Sona):**

- `cognitive-programming` - Only language with this positioning
- `adhd-friendly` - Directly targets ADHD developers
- `working-memory` - Speaks to core cognitive feature
- `focus-mode` - Highlights productivity feature
- `neurodivergent` - Captures broader accessibility audience

**AI-Native Positioning:**

- `ai-native` - Ties to trending AI language category
- `ai-collaboration` - Emphasizes human-AI workflow
- `azure-openai` - Captures Azure/OpenAI search traffic

**Emotional/Mission Appeal:**

- `revolutionary` - Appeals to early adopters and mission-driven users

**Validation Rule:** All 9 core keywords MUST be present. Missing any keyword = **BLOCKED BUILD**.

---

## ⚙️ RECOMMENDED SUPPLEMENTAL KEYWORDS

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

### Why These Matter:

**Technical Discovery:**

- `programming-language`, `repl`, `transpiler` - Standard language tooling terms
- `json`, `regex`, `merge-patch`, `deep-update` - Specific feature searches
- `timeout` - Unique async/error handling feature

**Accessibility Enhancement:**

- `accessibility`, `dyslexia-support` - Broader accessibility search
- `adhd`, `neurodiversity` - Related search terms
- `education` - Captures teaching/learning use cases

**Developer Tools:**

- `developer-tools` - Generic developer productivity searches

**Validation Rule:** These are **highly recommended** but NOT blocking. Missing supplemental keywords will generate **warnings** but won't block the build.

---

## 📦 Complete Combined List

**For easy copy-paste into package.json:**

```json
{
  "categories": ["Programming Languages", "AI", "Other"],
  "keywords": [
    "sona",
    "ai-native",
    "cognitive-programming",
    "neurodivergent",
    "accessibility",
    "adhd-friendly",
    "dyslexia-support",
    "working-memory",
    "focus-mode",
    "ai-collaboration",
    "azure-openai",
    "revolutionary",
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
}
```

**Total:** 3 categories, 25 keywords

---

## 🔧 Validation & Enforcement

### Automated Validation

A validation script has been created to enforce these requirements:

**Location:** `scripts/validate-metadata.js`

**Usage:**

```bash
# Run validation manually
node scripts/validate-metadata.js

# Add to package.json scripts
npm run validate-metadata
```

**Exit Codes:**

- `0` = All validation passed ✅
- `1` = Missing required categories/keywords (BLOCKS BUILD) ❌

### Validation Checks

The validator performs the following checks:

1. **Categories Check (BLOCKING)**

   - ✅ All 3 required categories present
   - ❌ Blocks build if any category missing

2. **Core Keywords Check (BLOCKING)**

   - ✅ All 9 core keywords present
   - ❌ Blocks build if any core keyword missing

3. **Supplemental Keywords Check (WARNING)**

   - ✅ All 15 supplemental keywords present
   - ⚠️ Warns if supplemental keywords missing (doesn't block)

4. **Version Format Check (BLOCKING)**

   - ✅ Valid version format (X.Y.Z or X.Y.Z.W)
   - ❌ Blocks if invalid format

5. **Display Name Check (WARNING)**

   - ✅ Contains "Sona" and mentions AI/cognitive/accessibility
   - ⚠️ Warns if missing brand/positioning terms

6. **Description Check (WARNING)**
   - ✅ Present and ≥50 characters
   - ⚠️ Warns if too short

### Integration with Build Process

**Recommended workflow:**

```json
{
  "scripts": {
    "validate-metadata": "node scripts/validate-metadata.js",
    "prebuild": "npm run validate-metadata",
    "build": "tsc && vsce package",
    "package": "npm run validate-metadata && vsce package"
  }
}
```

This ensures **every build** is validated before creating the VSIX.

---

## 📊 Quick Verification Snippet

**One-liner for manual verification:**

```bash
node -e "const m=require('./package.json');const needCats=['Programming Languages','AI','Other'];const needK=['ai-native','cognitive-programming','adhd-friendly','working-memory','focus-mode','neurodivergent','ai-collaboration','azure-openai','revolutionary'];for(const c of needCats)if(!(m.categories||[]).includes(c)){console.error('BLOCKER: missing category '+c);process.exit(1);}for(const k of needK)if(!(m.keywords||[]).includes(k)){console.error('BLOCKER: missing keyword '+k);process.exit(1);}console.log('✅ Categories & keywords verified');"
```

**Run from extension directory:**

```bash
cd vscode-extension/sona-ai-native-programming
node -e "const m=require('./package.json');const needCats=['Programming Languages','AI','Other'];const needK=['ai-native','cognitive-programming','adhd-friendly','working-memory','focus-mode','neurodivergent','ai-collaboration','azure-openai','revolutionary'];for(const c of needCats)if(!(m.categories||[]).includes(c)){console.error('BLOCKER: missing category '+c);process.exit(1);}for(const k of needK)if(!(m.keywords||[]).includes(k)){console.error('BLOCKER: missing keyword '+k);process.exit(1);}console.log('✅ Categories & keywords verified');"
```

---

## 🧠 TL;DR - The Absolute Non-Negotiables

| Type                        | Required Entries                                                                                                                                                                                                                            | Count | Enforcement  |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | ------------ |
| **Categories**              | `"Programming Languages"`, `"AI"`, `"Other"`                                                                                                                                                                                                | 3     | **BLOCKING** |
| **Keywords (Core)**         | `"ai-native"`, `"cognitive-programming"`, `"adhd-friendly"`, `"working-memory"`, `"focus-mode"`, `"neurodivergent"`, `"ai-collaboration"`, `"azure-openai"`, `"revolutionary"`                                                              | 9     | **BLOCKING** |
| **Keywords (Supplemental)** | `"sona"`, `"accessibility"`, `"dyslexia-support"`, `"programming-language"`, `"repl"`, `"transpiler"`, `"json"`, `"merge-patch"`, `"deep-update"`, `"regex"`, `"timeout"`, `"adhd"`, `"neurodiversity"`, `"education"`, `"developer-tools"` | 15    | **WARNING**  |

**Total Required:** 3 categories + 9 keywords (BLOCKING)  
**Total Recommended:** 3 categories + 24 keywords (full set)

---

## 🚨 What Happens If You Violate This

**Missing Required Categories:**

- ❌ Build script fails with exit code 1
- ❌ VSIX not created
- ❌ Reduced discoverability if manually bypassed
- ❌ Lower ranking in Marketplace searches

**Missing Required Core Keywords:**

- ❌ Build script fails with exit code 1
- ❌ VSIX not created
- ❌ Lost positioning as cognitive-first language
- ❌ Missed AI-native search traffic

**Missing Supplemental Keywords:**

- ⚠️ Build succeeds with warnings
- ⚠️ Some technical searches may miss Sona
- ⚠️ Slightly reduced discoverability

---

## 📅 Version History

| Version | Date        | Changes                    | Validator Version         |
| ------- | ----------- | -------------------------- | ------------------------- |
| 1.0     | Oct 6, 2025 | Initial authoritative list | validate-metadata.js v1.0 |

---

## 🔐 Authority & Ownership

**Maintained By:** Sona Core Team  
**Approval Required For Changes:** Project Lead + Marketing Lead  
**Review Frequency:** Quarterly (or when Marketplace algorithms change)

**Change Process:**

1. Propose change with data/rationale
2. Test impact on discoverability metrics
3. Get dual approval (technical + marketing)
4. Update this document + validator script
5. Announce to team + update all active branches

---

## ✅ Checklist for Every Release

Before packaging any VSIX:

- [ ] Run `node scripts/validate-metadata.js`
- [ ] Verify all 3 categories present
- [ ] Verify all 9 core keywords present
- [ ] Check supplemental keywords (optional but recommended)
- [ ] Confirm version format valid
- [ ] Review display name includes "Sona" + positioning terms
- [ ] Ensure description is compelling (≥50 chars)
- [ ] Build passes without errors
- [ ] Final VSIX size reasonable (<5MB typical)

---

**End of Authority Document**

_This document is the single source of truth for Sona VSIX metadata. All future releases must comply._
