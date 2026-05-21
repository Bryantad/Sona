# Sona v0.14.0 - Developer Usability Release

Sona `0.14.0` improves the developer experience across the CLI,
documentation, examples, packaging, and VS Code extension.

This release builds on the `0.13.x` runtime governance and native stdlib
contract foundation by making Sona easier to install, learn, run, and debug.

## Highlights

- Improved CLI help, version, and run behavior.
- Better user-facing error messages, including the canonical
  `docs/errors/v0.14-diagnostics.md` guide.
- Added `docs/QUICKSTART.md`.
- Added `docs/LANGUAGE_REFERENCE.md`.
- Added `docs/STDLIB_REFERENCE.md` for the stable user-facing stdlib surface.
- Added a validated official example suite.
- Added `tools/run_examples.py`.
- Improved VSIX metadata and onboarding copy.

## Notes

Official examples remain part of source-repository validation. They are not
required to ship inside the installed Python package.

No major syntax redesign, new governance architecture, or new memory feature is
included in this release.
