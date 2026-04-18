# Changelog

## 0.11.0 - 2026-03-04
- Align with Sona core 0.11.0 release.
- Version bump for marketplace publishing.
All notable changes to the Code Context extension will be documented in this file.

## [0.10.2] - 2025-01-20

### Added

- **Reason Types** - Semantic tags for enhanced filtering
  - ⏳ TEMP - Temporary code to be removed
  - 🔧 WORKAROUND - Workaround for a known issue
  - 🔒 SECURITY - Security-related decision
  - ⚡ PERFORMANCE - Performance optimization
  - 📦 LEGACY - Legacy code kept for compatibility
- **Enhanced Stale Warnings** - Exact age in days
  - "⚠️ This decision is 92 days old" (passive, no popups)
- **Git Blame Hint** - Read-only commit reference
  - Shows "near commit abc123" in hover
  - No syncing, no linking, just context
- **Context Density Indicator** - Status bar widget
  - Shows `💭 3` for files with notes
  - Includes stale count: `💭 5 (⚠️ 2 stale)`

### Configuration

- `showGitBlameHint` - Toggle git commit hints in hover
- `showStatusBarIndicator` - Toggle status bar note count

---

## [0.10.1] - 2025-01-20

### Added

- **Initial Release** 🎉
- Core context note functionality
  - Add notes to any selected code
  - Category quick-pick (💡 Decision, 🐛 Bug Fix, ⚠️ Temporary, 🔄 Refactor, 📝 Note)
  - Custom note text input
- Hover display
  - Rich markdown tooltips on hover
  - Relative timestamps ("2 days ago")
  - Quick edit/delete links in hover
- Inline decorations
  - Background highlighting for annotated lines
  - Configurable markers (emoji/icon/subtle)
  - Overview ruler indicators
- Explorer sidebar
  - "Context Notes" tree view in Explorer
  - Notes grouped by file
  - Click to navigate to note location
- Stale note detection
  - Configurable staleness threshold (default 30 days)
  - Visual warning for stale notes
  - Bulk cleanup command
- Export functionality
  - Export all notes as Markdown
  - Includes code snippets and timestamps
- Storage options
  - Workspace state (default, private)
  - `.code-context.json` file (opt-in, git-friendly)
- Keyboard shortcut: `Ctrl+Shift+N` / `Cmd+Shift+N`
- Right-click context menu integration

### Configuration

- `showInlineMarkers` - Toggle inline 💭 markers
- `showHoverNotes` - Toggle hover tooltips
- `markerStyle` - Choose emoji/icon/subtle
- `noteCategories` - Customizable category list
- `staleAfterDays` - Staleness threshold
- `syncWithGit` - Enable file-based storage

## [Unreleased]

### Planned (Lane 2 - Opt-In Power Features)

- Context search/filter
- Note pinning (prevent stale warnings)
- Timeline view integration
- Note templates

### Future (Lane 3 - Experimental, Never Default)

- AI-suggested context from commit messages
- Team analytics
- Cross-repo context
