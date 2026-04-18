# Changelog

## 0.11.0 - 2026-03-04
- Align with Sona core 0.11.0 release.
- Version bump for marketplace publishing.
All notable changes to the Inline Validator Lens extension will be documented in this file.

## [0.10.1] - 2025-01-16

### Added
- **Initial Release** 🎉
- Email validation (RFC 5322 compliant)
- URL validation (protocol-aware)
- UUID validation (v1-v5 support)
- IPv4 address validation (octet range checking)
- IPv6 address validation (full and compressed formats)
- ISO 8601 date/datetime validation
- Phone number validation (international format)
- Credit card validation (Luhn algorithm)
- Hex color validation (#RGB and #RRGGBB)
- JSON syntax validation

### Features
- Inline decoration hints (✓/✗ badges)
- Hover tooltips with validation details
- Optional CodeLens support
- Diagnostics integration (Problems panel)
- Quick Pick for navigating issues
- Toggle command for enable/disable
- Validate selection command
- Copy valid value command

### Configuration
- Per-type enable/disable toggles
- Minimum string length threshold
- Maximum validations per file limit
- Inline hints toggle
- CodeLens toggle

### Performance
- Debounced updates (500ms)
- Configurable validation limits
- Efficient string extraction

## [Unreleased]

### Planned
- Credit card type detection (Visa, Mastercard, etc.)
- Custom regex pattern support
- Workspace-level ignore patterns
- Quick fix suggestions for common issues
- ISBN validation
- MAC address validation
- Semantic versioning validation
- Base64 detection and validation
