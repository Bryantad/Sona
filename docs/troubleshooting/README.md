# Troubleshooting & Debugging

This folder contains documentation for common issues, bug fixes, and debugging guides.

## 🔥 Critical Fixes

### [MODULE_LOADER_FIX.md](./MODULE_LOADER_FIX.md)

**PRIORITY: CRITICAL**

Fixed regression where 4 stdlib modules (collection, queue, stack, yaml) couldn't be imported in v0.9.6.

**Symptoms:**

- `ImportError: Module 'collection' not found`
- Modules that worked in v0.9.5 fail in v0.9.6

**Root Cause:**
Module loader only checked `native_*.py` files, missed regular `.py` modules.

**Status:** ✅ FIXED - All 30/30 modules now work

---

### [BREAK_CONTINUE_FIX.md](./BREAK_CONTINUE_FIX.md)

**PRIORITY: HIGH**

Fixed break and continue statements not working in loops.

**Symptoms:**

- `break` statement doesn't exit loop
- `continue` statement doesn't skip to next iteration
- No error messages, but control flow incorrect

**Root Cause:**

- Missing parser transformers
- Exception swallowing in execute_block()
- Missing loop control handlers

**Status:** ✅ FIXED - All 4 test cases passing

---

## 📦 Module Issues

### [WHERE_ARE_MY_MODULES.md](./WHERE_ARE_MY_MODULES.md)

Guide to understanding module import issues and how the module system works.

**Topics:**

- Module search paths
- Native vs regular modules
- Import troubleshooting steps

---

## 🏗️ Codebase Issues

### [EXTRACTION_REALITY_CHECK.md](./EXTRACTION_REALITY_CHECK.md)

Notes on codebase extraction and organization.

---

## Quick Debugging Checklist

When you encounter an issue:

1. **Import Errors?** → Check [MODULE_LOADER_FIX.md](./MODULE_LOADER_FIX.md)
2. **Break/Continue Not Working?** → Check [BREAK_CONTINUE_FIX.md](./BREAK_CONTINUE_FIX.md)
3. **Module Not Found?** → Check [WHERE_ARE_MY_MODULES.md](./WHERE_ARE_MY_MODULES.md)
4. **Syntax Errors?** → Check grammar files in `sona/grammar*.lark`
5. **Runtime Errors?** → Enable verbose logging and check interpreter trace

---

## Common Error Messages

| Error                     | Likely Cause                          | Solution                    |
| ------------------------- | ------------------------------------- | --------------------------- |
| `Module 'X' not found`    | Module loader issue or missing module | See MODULE_LOADER_FIX.md    |
| `break outside loop`      | Parser issue                          | See BREAK_CONTINUE_FIX.md   |
| `continue outside loop`   | Parser issue                          | See BREAK_CONTINUE_FIX.md   |
| `Unexpected token`        | Grammar/parser issue                  | Check grammar file syntax   |
| `Name 'X' is not defined` | Scoping or undefined variable         | Check variable declarations |

---

**Need More Help?**

- Check [../testing/TESTING_GUIDE.md](../testing/TESTING_GUIDE.md) for testing strategies
- See [../features/FEATURE_AUDIT_096.md](../features/FEATURE_AUDIT_096.md) for feature status
- Review [../development/](../development/) for implementation notes
