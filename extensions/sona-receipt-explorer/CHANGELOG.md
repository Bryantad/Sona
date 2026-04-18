# Changelog

## 0.13.0 - 2026-04-17

### Receipt Operations
- Added `Explore Receipts` command to reveal and refresh the receipt explorer view directly.
- Added `Verify Receipt Chain` command wired to `sona receipt verify-chain` for the active receipts directory.
- Added `Export Receipt Bundle` command wired to `sona receipt export` with optional workspace lockfile payload.

### Packaging
- Bumped extension metadata to `0.13.0`.
- Updated README command and governance docs for the 0.13 receipt workflow.

## 0.12.1 - 2026-03-16

### Architecture
- Decomposed monolithic `extension.ts` (~1,250 lines) into focused modules: `models.ts`, `parse.ts`, `cli.ts`, `tree.ts`, `views.ts`, `commands.ts`, and a slim `extension.ts` activation shell.

### Kind-Aware Receipt Support
- Introduced `ReceiptKind` discriminated union (`execution | directory | bundle | chain | redaction | unknown`) as the architectural pivot for multi-family receipt handling.
- Parser now detects receipt kind from JSON shape via `detectReceiptKind()` instead of hard-gating on execution-specific fields.
- Non-execution receipts (directory, unknown, future kinds) are no longer silently dropped — they degrade gracefully with full base-field display.
- Tree view renders kind-aware icons, tooltips, and descriptions per receipt family.
- Detail panel dispatches to kind-specific renderers (`renderExecutionReceipt`, `renderDirectoryReceipt`, `renderUnknownReceipt`).
- Diff formatter produces kind-aware markdown output.
- Export command generates kind-appropriate markdown.

### Guardrails
- Execution-only commands (Re-run, Copy Reproduce) now guard on `parsed.kind === 'execution'` with user-facing warnings for other kinds.

## 0.12.0 - 2026-03-16

- Align extension metadata and documentation with Sona core 0.12.0.
- Expanded the receipt detail view to surface receipt-chain, policy, signature, and redaction metadata directly.
- Expanded receipt compare and markdown export output with trust and governance fields already present in Sona receipts.

## 0.11.0 - 2026-03-04

- Align with Sona core 0.11.0 release.
- Added signature verification command (`Sona Receipts: Verify Receipt Signature`).
- Added deterministic redaction command (`Sona Receipts: Redact Receipt`) with profile selection.
- Tree view now surfaces receipt hash, policy fingerprint, signature, and redaction profile.

## 0.10.3

- Added deterministic VSIX packaging script (`npm run package:vsix`)
- Added reproducibility verification build (`npm run package:vsix:verify`)
- Normalized packaging artifacts to fixed metadata for byte-stable output
- Excluded local build/script artifacts from VSIX payload

## 0.10.2

- Feature update release
- Improved receipt loading stability with schema validation and safer error handling
- Added status-based filtering (`all`, `success`, `failed`) and configurable receipt glob
- Added `Open Raw Receipt JSON` command in context menu
- Hardened detail webview rendering with HTML escaping
- Improved compare flow to load receipts on demand and avoid stale diff documents
- Packaging and extension metadata updates

## 0.10.1

- Initial release
- Tree view with grouping by date
- Rich webview detail panel
- Receipt comparison (diff view)
- Re-run from receipt
- Copy reproduce command
- Export as markdown
- Delete receipt
- Auto-refresh on file changes
- Configurable settings
