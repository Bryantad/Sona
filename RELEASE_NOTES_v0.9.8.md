# Sona v0.9.8 Release Notes

**Release Date:** 2025-12-08  
**Status:** Stable / Backward Compatible with v0.9.7  
**Scope:** Parser hardening, security follow-ups, CI coverage uplift, local/Ollama guidance, micro-chunked AI workflows

## 🎯 Highlights

- 🧭 **Parser & runtime hardening** – Better BOM handling, escaped-path support, and stricter Unicode escape parsing to cut malformed-input crashes; clearer recovery messages for production runs.
- 🔒 **Security follow-ups** – Safer defaults for networked modules, FTP usage cautions, SQLi mitigation notes, and HuggingFace model pinning guidance to reduce supply-chain risk.
- 🧪 **CI + coverage uplift** – Coverage gate raised to 90% with randomized test ordering and flaky-test surfacing; pytest/coverage config documented in `pyproject.toml`.
- 🤖 **Micro-chunked AI workflows** – Smaller, deterministic AI task breakdowns for IDE assistance, improving focus/resume reliability and reducing context drift.
- 🖥️ **Local/Ollama support** – Documented local endpoints and Ollama setup so you can run without cloud dependencies; clarified how to point the tooling at on-prem endpoints.
- 📓 **Docs refresh** – README, security policy, and release notes updated to reflect 0.9.8 changes and current support window.

## 🚀 Installation & Upgrade

### Fresh install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

### Upgrade from v0.9.7

```bash
git pull origin main
pip install -e .
```

No breaking changes are expected when moving from 0.9.7 to 0.9.8.

## ✅ Verification

```powershell
# Full suite
.\run_all_tests.ps1

# Focused runtime check
python run_sona.py test_all_097.sona
```

Coverage gates and markers are configured in `pyproject.toml` (`--cov-fail-under=90`).

## 🔐 Security Notes

- Current support window: v0.9.8 (current) and v0.9.7 (prior minor).
- Prefer pinned models for HF downloads; avoid anonymous/unauthenticated pulls in production.
- Treat FTP as opt-in and avoid storing credentials in plain text; see SECURITY.md for contact and disclosure steps.
- SQL inputs should be parameterized; avoid string concatenation in `query` examples.

## 📌 Compatibility

- No known breaking language changes from v0.9.7.
- Standard library remains at 80 modules; existing code and tests should continue to pass.

## 📞 Links

- Project: https://github.com/Bryantad/Sona
- Issues: https://github.com/Bryantad/Sona/issues
- Security: security@sona-lang.dev
