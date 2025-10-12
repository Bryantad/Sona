#!/usr/bin/env node
/**
 * SONA VSIX METADATA VALIDATOR
 * 
 * Enforces the authoritative categories and keywords that made v0.9.0
 * outperform later versions in Marketplace discoverability.
 * 
 * CRITICAL: This validator blocks any VSIX build that's missing the
 * non-negotiable categories/keywords that drive organic installs.
 * 
 * Usage:
 *   node scripts/validate-metadata.js
 *   npm run validate-metadata (add to package.json scripts)
 * 
 * Exit codes:
 *   0 = All validation passed
 *   1 = Missing required categories/keywords (BLOCKS BUILD)
 */

const fs = require('fs');
const path = require('path');

// ============================================================================
// AUTHORITATIVE NON-NEGOTIABLE LISTS
// ============================================================================

/**
 * CATEGORIES (must include ALL 3)
 * 
 * - "Programming Languages" → Base discoverability
 * - "AI" → Listed under AI/LLM extension feeds (major install driver)
 * - "Other" → Preserves older backlinks and generic searches
 */
const REQUIRED_CATEGORIES = [
  "Programming Languages",
  "AI",
  "Other"
];

/**
 * CORE KEYWORDS (the must-have set for identity + search magnetism)
 * 
 * These 9 keywords anchor Sona as:
 * 1. The only cognitive-accessibility-first language
 * 2. A trending AI-native tool
 * 3. A mission-driven revolution for neurodivergent developers
 */
const REQUIRED_KEYWORDS_CORE = [
  "ai-native",
  "cognitive-programming",
  "adhd-friendly",
  "working-memory",
  "focus-mode",
  "neurodivergent",
  "ai-collaboration",
  "azure-openai",
  "revolutionary"
];

/**
 * SUPPLEMENTAL KEYWORDS (highly recommended for technical discovery)
 * 
 * These enhance discoverability without replacing the story.
 * Not blocking, but logged as warnings if missing.
 */
const RECOMMENDED_KEYWORDS_SUPPLEMENTAL = [
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
];

// ============================================================================
// VALIDATION LOGIC
// ============================================================================

function loadPackageJson() {
  const packagePath = path.join(__dirname, '..', 'package.json');
  
  if (!fs.existsSync(packagePath)) {
    console.error('❌ FATAL: package.json not found at:', packagePath);
    process.exit(1);
  }
  
  try {
    const content = fs.readFileSync(packagePath, 'utf8');
    return JSON.parse(content);
  } catch (error) {
    console.error('❌ FATAL: Failed to parse package.json:', error.message);
    process.exit(1);
  }
}

function validateCategories(manifest) {
  console.log('\n📂 Validating Categories...');
  
  const categories = manifest.categories || [];
  const missing = REQUIRED_CATEGORIES.filter(cat => !categories.includes(cat));
  
  if (missing.length > 0) {
    console.error('\n❌ BLOCKER: Missing required categories:');
    missing.forEach(cat => console.error(`   - "${cat}"`));
    console.error('\nRequired categories (must include ALL):');
    REQUIRED_CATEGORIES.forEach(cat => console.error(`   - "${cat}"`));
    return false;
  }
  
  console.log('✅ All required categories present:');
  REQUIRED_CATEGORIES.forEach(cat => console.log(`   ✓ "${cat}"`));
  return true;
}

function validateKeywords(manifest) {
  console.log('\n🔑 Validating Keywords...');
  
  const keywords = manifest.keywords || [];
  const missingCore = REQUIRED_KEYWORDS_CORE.filter(kw => !keywords.includes(kw));
  const missingSupplemental = RECOMMENDED_KEYWORDS_SUPPLEMENTAL.filter(kw => !keywords.includes(kw));
  
  let passed = true;
  
  // Check CORE keywords (blocking)
  if (missingCore.length > 0) {
    console.error('\n❌ BLOCKER: Missing required CORE keywords:');
    missingCore.forEach(kw => console.error(`   - "${kw}"`));
    console.error('\nRequired CORE keywords (must include ALL):');
    REQUIRED_KEYWORDS_CORE.forEach(kw => console.error(`   - "${kw}"`));
    passed = false;
  } else {
    console.log('✅ All required CORE keywords present:');
    REQUIRED_KEYWORDS_CORE.forEach(kw => console.log(`   ✓ "${kw}"`));
  }
  
  // Check SUPPLEMENTAL keywords (warnings only)
  if (missingSupplemental.length > 0) {
    console.warn('\n⚠️  WARNING: Missing recommended SUPPLEMENTAL keywords:');
    missingSupplemental.forEach(kw => console.warn(`   - "${kw}"`));
    console.warn('\nThese are recommended but not blocking. Add them for better discoverability.');
  } else {
    console.log('✅ All recommended SUPPLEMENTAL keywords present');
  }
  
  return passed;
}

function validateVersion(manifest) {
  console.log('\n🔢 Validating Version...');
  
  if (!manifest.version || typeof manifest.version !== 'string') {
    console.error('❌ BLOCKER: Invalid or missing version field');
    return false;
  }
  
  // Version format: X.Y.Z or X.Y.Z.W
  const versionPattern = /^\d+\.\d+\.\d+(\.\d+)?$/;
  if (!versionPattern.test(manifest.version)) {
    console.error(`❌ BLOCKER: Invalid version format: "${manifest.version}"`);
    console.error('   Expected format: X.Y.Z or X.Y.Z.W (e.g., "0.9.6" or "0.9.6.1")');
    return false;
  }
  
  console.log(`✅ Valid version: ${manifest.version}`);
  return true;
}

function validateDisplayName(manifest) {
  console.log('\n📛 Validating Display Name...');
  
  if (!manifest.displayName || typeof manifest.displayName !== 'string') {
    console.error('❌ BLOCKER: Missing displayName field');
    return false;
  }
  
  // Should include "Sona" and mention cognitive/AI aspect
  const name = manifest.displayName.toLowerCase();
  if (!name.includes('sona')) {
    console.warn('⚠️  WARNING: displayName should include "Sona" for brand recognition');
  }
  
  if (!name.includes('ai') && !name.includes('cognitive') && !name.includes('accessibility')) {
    console.warn('⚠️  WARNING: displayName should mention AI/cognitive/accessibility for clarity');
  }
  
  console.log(`✅ Display name: "${manifest.displayName}"`);
  return true;
}

function validateDescription(manifest) {
  console.log('\n📝 Validating Description...');
  
  if (!manifest.description || typeof manifest.description !== 'string') {
    console.error('❌ BLOCKER: Missing description field');
    return false;
  }
  
  if (manifest.description.length < 50) {
    console.warn('⚠️  WARNING: Description is quite short (< 50 chars). Consider expanding for better Marketplace appeal.');
  }
  
  console.log(`✅ Description present (${manifest.description.length} chars)`);
  return true;
}

function generateSummaryReport(manifest) {
  console.log('\n' + '='.repeat(80));
  console.log('📊 VALIDATION SUMMARY REPORT');
  console.log('='.repeat(80));
  
  console.log('\n📦 Extension Details:');
  console.log(`   Name: ${manifest.name}`);
  console.log(`   Display Name: ${manifest.displayName}`);
  console.log(`   Version: ${manifest.version}`);
  console.log(`   Publisher: ${manifest.publisher}`);
  
  console.log('\n📂 Categories:');
  (manifest.categories || []).forEach(cat => console.log(`   - ${cat}`));
  
  console.log('\n🔑 Keywords:');
  console.log(`   Total: ${(manifest.keywords || []).length} keywords`);
  console.log(`   Core (required): ${REQUIRED_KEYWORDS_CORE.filter(kw => (manifest.keywords || []).includes(kw)).length}/${REQUIRED_KEYWORDS_CORE.length}`);
  console.log(`   Supplemental (recommended): ${RECOMMENDED_KEYWORDS_SUPPLEMENTAL.filter(kw => (manifest.keywords || []).includes(kw)).length}/${RECOMMENDED_KEYWORDS_SUPPLEMENTAL.length}`);
  
  console.log('\n' + '='.repeat(80));
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================

function main() {
  console.log('╔════════════════════════════════════════════════════════════════════════════╗');
  console.log('║                    SONA VSIX METADATA VALIDATOR                            ║');
  console.log('║                                                                            ║');
  console.log('║  Enforcing authoritative categories & keywords for Marketplace success     ║');
  console.log('╚════════════════════════════════════════════════════════════════════════════╝');
  
  const manifest = loadPackageJson();
  
  let allPassed = true;
  
  // Run all validations
  allPassed = validateCategories(manifest) && allPassed;
  allPassed = validateKeywords(manifest) && allPassed;
  allPassed = validateVersion(manifest) && allPassed;
  allPassed = validateDisplayName(manifest) && allPassed;
  allPassed = validateDescription(manifest) && allPassed;
  
  // Generate summary
  generateSummaryReport(manifest);
  
  // Final verdict
  console.log('\n' + '═'.repeat(80));
  if (allPassed) {
    console.log('✅ VALIDATION PASSED - Safe to build VSIX');
    console.log('═'.repeat(80));
    console.log('\nAll required categories and keywords are present.');
    console.log('This build maintains the discoverability standards of v0.9.0.\n');
    process.exit(0);
  } else {
    console.log('❌ VALIDATION FAILED - DO NOT BUILD VSIX');
    console.log('═'.repeat(80));
    console.error('\nFix the issues above before packaging.');
    console.error('Missing categories/keywords will reduce Marketplace discoverability.\n');
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = {
  REQUIRED_CATEGORIES,
  REQUIRED_KEYWORDS_CORE,
  RECOMMENDED_KEYWORDS_SUPPLEMENTAL,
  validateCategories,
  validateKeywords,
  validateVersion,
  validateDisplayName,
  validateDescription
};
