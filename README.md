# 🚀 Sona — **AI-Native** Programming Language

**Human × AI collaboration with cognitive accessibility at the core.**

[![Version](https://img.shields.io/badge/version-0.9.9-blue.svg)](https://github.com/Bryantad/Sona/releases/tag/v0.9.9)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://python.org)
[![Marketplace Installs](https://img.shields.io/visual-studio-marketplace/i/Waycoreinc.sona-ai-native-programming?label=VS%20Code%20Installs)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)
[![Marketplace Rating](https://img.shields.io/visual-studio-marketplace/r/Waycoreinc.sona-ai-native-programming?label=VS%20Code%20Rating)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)
[![GitHub Stars](https://img.shields.io/github/stars/Bryantad/Sona?style=social)](https://github.com/Bryantad/Sona/stargazers)
[![YouTube](https://img.shields.io/youtube/channel/subscribers/UCFWuiQHiQPrJSAeAVi5raZA?style=social)](https://www.youtube.com/channel/UCFWuiQHiQPrJSAeAVi5raZA)
[![X (Twitter) Follow](https://img.shields.io/twitter/follow/sona_org?style=social)](https://x.com/sona_org)

---

## Overview

Sona is an AI-native language and toolchain built with cognitive accessibility in mind. The project prioritizes a reliable, deterministic standard library before provider integrations. AI providers will ship via a separate `sona-ai` package so the core remains stable, testable, and network-free.

This repository includes:

- A pragmatic, network-free standard library with disciplined tests.
- A VS Code extension that surfaces Sona in the editor.
- Documentation and a roadmap for future AI provider support.

---

## Status (v0.9.4.1)

- Platform used for verification: Windows, Python 3.12
- Debug signal: `SONA_DEBUG=1` during test runs
- Tests: PASS (stdlib-only suite)
- Coverage: ~86% (gate ≥85%), branch coverage enabled
- Deterministic: no network dependencies in core tests
- Packaging: stdlib wiring corrected and locked with `sona/stdlib/MANIFEST.json`
- VS Code Marketplace: Overview, icon, banner, screenshots, keywords, Q&A present

### Maintainer note

The public 0.9.4 package missed proper stdlib wiring and shipped without a Marketplace Overview/icon. 0.9.4.1 corrects the packaging, adds the Overview and visuals, and locks the stdlib set so this does not regress.

---

## What’s solid today

### Standard library

- **JSON**
  - RFC 7396 Merge Patch: `merge_patch(target, patch)` (documented, tested)
  - JSON Pointer helpers (with “pointer gotchas” documented)
  - `deep_update(target, patch, *, list_strategy="replace"|"append"|"extend_unique", make_copy=True)`
    - Dicts recurse; lists replace by default; type conflicts resolve to `patch`
    - Back-compat shim: legacy `copy=` is still accepted and emits `DeprecationWarning`
- **Collections**
  - `chunk`, `unique_by`, `group_by` (order-preserving)
- **Regex**
  - Reusable handles, explicit timeout semantics, safe failure modes

### Extension (VS Code)

- Identifier: `Waycoreinc.sona-ai-native-programming`
- Overview: present
- Icon/Banner/Screenshots: present
- Categories/Keywords/Q&A: set for discoverability

---

## Installation

### Python toolchain

Requires Python 3.12+

```bash
pip install sona==0.9.4.1
# optional extras
pip install "sona[ai]==0.9.4.1"     # provider package placeholder (separate)
pip install "sona[dev]==0.9.4.1"    # development tooling
````

Verify environment:

```bash
sona build-info
sona doctor
```

### VS Code extension

Install from Marketplace:
[https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)

---

## Quickstart

REPL:

```bash
sona repl
```

Inside the REPL:

```sona
explain("Learning Sona")
```

Standard library examples:

```python
# json.merge_patch
from sona.stdlib import json as sjson

target = {"title": "Good", "meta": {"a": 1, "b": 2}}
patch = {"meta": {"b": None, "c": 3}}
assert sjson.merge_patch(target, patch) == {"title": "Good", "meta": {"a": 1, "c": 3}}

# json.deep_update
base = {"a": {"x": 1}, "list": [1, 2]}
upd  = {"a": {"y": 2}, "list": [9]}
out  = sjson.deep_update(base, upd)  # default replaces lists
assert out == {"a": {"x": 1, "y": 2}, "list": [9]}

# collections
from sona.stdlib import collection as col
assert col.chunk([1,2,3,4,5], 2, last="keep") == [[1,2],[3,4],[5]]
assert col.unique_by(["aa","ab","ba"], key=lambda s: s[0]) == ["aa","ba"]
assert col.group_by(["aa","ab","ba"], key=lambda s: s[0]) == {"a":["aa","ab"], "b":["ba"]}

# regex
from sona.stdlib import regex
h = regex.compile(r"^[a-z]+$", {"case_insensitive": True})
assert regex.match(h, "Alpha")["matched"] is True
```

---

## CLI reference (snapshot)

```bash
sona init <project>           # Create a new project
sona run <file>               # Execute Sona files
sona repl                     # Interactive REPL
sona transpile <file>         # Convert to other languages
sona format <file>            # Format code
sona check <file>             # Syntax validation
sona info                     # Environment information
sona build-info               # Build metadata + feature flags
sona doctor                   # Diagnostics
```

---

## Configuration

* `SONA_DEBUG=1` enables verbose stdlib/runtime diagnostics during development and CI.

---

## Testing and coverage

The CI focuses on the standard library to keep signals clean and actionable.

* Scope: `sona/stdlib/*` (excludes utils/ai/native\_\*, smod helpers)
* Commands:

```bash
# Windows PowerShell
$env:SONA_DEBUG = "1"

pytest -q
coverage run -m pytest
coverage report                # expect ≥85%
```

* Smoke test gate (excerpt): ensures ≥22 stdlib modules, imports succeed, public API or namespace children exist, and basic JSON/collections/regex probes pass.
* Deterministic: no network calls in core tests.

---

## Packaging integrity

A manifest is generated and version-controlled to prevent drift:

* `sona/stdlib/MANIFEST.json` lists the intended stdlib modules.
* A smoke test asserts the packaged modules match the manifest and that the count meets the minimum threshold.

Before packaging the VSIX:

```bash
python scripts/generate_stdlib_manifest.py
pytest -q && coverage run -m pytest && coverage report
npx vsce ls
npx vsce package
python scripts/check_vsix.py sona-ai-native-programming-0.9.4.1.vsix
```

The asset check fails if `extension/README.md`, `extension/media/icon.png`, or `extension/package.json` are missing.

---

## Roadmap (near term)

* Language Server Protocol (diagnostics, semantic tokens, quick fixes)
* Transpilation fidelity for a focused subset of constructs
* Package manager (publish/consume with lockfile and integrity checks)
* AI provider integrations via `sona-ai` (provider-agnostic, safe by default, tested offline with fakes)

These will not compromise stdlib stability.

---

## Release notes

* 0.9.4 — foundation and stdlib improvements (merge\_patch, deep\_update, collections)
* 0.9.4.1 — hotfix for packaging credibility (stdlib wiring, Marketplace Overview/icon/screenshots, keywords, Q\&A), README alignment, and a back-compat shim for `deep_update(copy=...)`

See releases: [https://github.com/Bryantad/Sona/releases](https://github.com/Bryantad/Sona/releases)

---

## Contributing

Contributions are welcome. Please:

1. Open an issue to discuss scope and approach.
2. Keep changes deterministic and testable.
3. Maintain the stdlib coverage gate (≥85%) and pass smoke tests.
4. Avoid introducing network dependencies into core tests.

---

## Community

* Issues: [https://github.com/Bryantad/Sona/issues](https://github.com/Bryantad/Sona/issues)
* Discussions: [https://github.com/Bryantad/Sona/discussions](https://github.com/Bryantad/Sona/discussions)

---

## License

MIT — see [LICENSE](LICENSE).
