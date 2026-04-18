# Inline Validator Lens: Real-Time String Validation

[![Version](https://img.shields.io/badge/version-0.11.0-blue.svg)](https://github.com/Bryantad/Sona/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Marketplace](https://img.shields.io/badge/VS%20Code-Marketplace-blue)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.inline-validator-lens)
[![Part of Sona](https://img.shields.io/badge/part%20of-Sona%20Ecosystem-purple)](https://github.com/Bryantad/Sona)

---

A Visual Studio Code extension that provides **real-time validation badges** for string literals directly in your code. Part of the **Sona cognitive accessibility ecosystem**.

> See validation status at a glance — no more wondering if that regex is right.

---

## Overview

String literals containing emails, URLs, UUIDs, and other structured data often hide bugs that only appear at runtime. Inline Validator Lens detects these patterns and validates them **as you type**, showing ✓ or ✗ badges inline.

No linter rules to configure. No external tools. Just instant visual feedback.

---

## Key Features

### Automatic Detection

The extension automatically recognizes:

| Type            | Example                                | Validation           |
| --------------- | -------------------------------------- | -------------------- |
| **Email**       | `user@example.com`                     | RFC 5322 compliant   |
| **URL**         | `https://api.example.com`              | Protocol-aware       |
| **UUID**        | `550e8400-e29b-41d4-a716-446655440000` | v1-v5 format         |
| **IPv4**        | `192.168.1.1`                          | Octet range checking |
| **IPv6**        | `2001:0db8::1`                         | Full and compressed  |
| **ISO Date**    | `2025-01-20T10:30:00Z`                 | Date/time parsing    |
| **Phone**       | `+1-555-123-4567`                      | International format |
| **Credit Card** | `4111111111111111`                     | Luhn algorithm       |
| **Hex Color**   | `#FF5733`                              | #RGB and #RRGGBB     |
| **JSON**        | `{"key": "value"}`                     | Syntax validation    |

### Inline Badges

- **✓ Valid** — green checkmark with type label
- **✗ Invalid** — red X with error indication
- **Hover Details** — full validation message on hover

### Problems Panel Integration

Invalid strings appear in VS Code's Problems panel with:

- File path and line number
- Validation type and error message
- Click to navigate

### Performance Optimized

- **Debounced Updates** — 500ms delay after typing stops
- **Configurable Limits** — max validations per file
- **Minimum Length** — skip trivially short strings

---

## Commands

| Command            | Description                         |
| ------------------ | ----------------------------------- |
| Toggle Enabled     | Enable/disable all validation       |
| Validate Selection | Validate currently selected text    |
| Show All Issues    | Quick pick of all validation errors |
| Copy Valid Value   | Copy selected value to clipboard    |

---

## Settings

```json
{
  "validatorLens.enabled": true,
  "validatorLens.showInlineHints": true,
  "validatorLens.showCodeLens": false,
  "validatorLens.validateEmails": true,
  "validatorLens.validateUrls": true,
  "validatorLens.validateUuids": true,
  "validatorLens.validateIpAddresses": true,
  "validatorLens.validateDates": true,
  "validatorLens.validatePhoneNumbers": true,
  "validatorLens.validateCreditCards": false,
  "validatorLens.validateHexColors": true,
  "validatorLens.validateJson": true,
  "validatorLens.minStringLength": 5,
  "validatorLens.maxValidationsPerFile": 200
}
```

---

## Supported Languages

Works with any language using quoted strings:

- JavaScript / TypeScript
- Python
- JSON / YAML
- HTML / CSS / Markdown
- Sona / .smod files
- And many more...

---

## Examples

### Email Validation

```javascript
const valid = "user@example.com"; // ✓ Email
const invalid = "not-an-email"; // ✗ Email
```

### URL Validation

```python
api = "https://api.example.com/v1"    # ✓ URL
bad = "htp://missing-t.com"           # ✗ URL
```

### UUID Validation

```typescript
const id = "550e8400-e29b-41d4-a716-446655440000"; // ✓ UUID
const fake = "not-a-uuid"; // (no match)
```

### IP Address Validation

```json
{
  "server": "192.168.1.1", // ✓ IPv4
  "invalid": "256.0.0.1" // ✗ IPv4 (octet > 255)
}
```

---

## Use Cases

### API Development

> "Is this URL properly formatted?"

See validation instantly without running tests.

### Configuration Files

> "Did I get the UUID format right?"

Catch typos before they become runtime errors.

### Data Entry

> "Is this a valid email address?"

Validate user-provided data patterns.

### Code Review

> "Are all these IPs valid?"

Spot invalid data at a glance during reviews.

---

## Part of the Sona Ecosystem

Inline Validator Lens complements Sona's deterministic philosophy:

- **Catch Errors Early** — validation before execution
- **Visual Feedback** — reduce cognitive load
- **No Configuration** — works out of the box

---

## Known Limitations

1. Template literals with expressions (`${...}`) are skipped
2. Multi-line strings have limited support
3. Some regex edge cases may exist

---

## Requirements

- VS Code 1.74.0 or higher
- No additional dependencies

---

## Links

- [Sona Language](https://github.com/Bryantad/Sona)
- [Report Issues](https://github.com/Bryantad/Sona/issues)
- [Changelog](CHANGELOG.md)

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <i>Built with ✓ by WayCore Inc.</i>
</p>
