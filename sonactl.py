#!/usr/bin/env python3
"""
sonactl.py

Lightweight bootstrap for running the Sona core runtime directly from the
repository. This mirrors the bundled `runtime/sonactl.py` used inside the
VS Code extension so you can run and verify the stdlib locally.

Usage:
  python sonactl.py --verify   # smoke-test core stdlib imports
  python sonactl.py            # interactive REPL with sona.stdlib on PYTHONPATH
"""
import sys
import os
import code

BANNER = "Sona runtime ready. Import modules from `sona.stdlib.*`"

# Ensure repository root is on sys.path so `import sona` resolves
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

def verify():
    # Minimal sanity checks used by the extension's verify script
    import importlib
    try:
        import sona.stdlib.json as sjson
        import sona.stdlib.regex as sregex
        import sona.stdlib.collection as scol
    except Exception as e:
        print(f"ERROR: could not import core stdlib modules: {e}")
        raise
    assert hasattr(sjson, "merge_patch"), "json.merge_patch missing"
    assert hasattr(sregex, "compile"), "regex.compile missing"
    assert hasattr(scol, "chunk"), "collection.chunk missing"
    print("OK: core stdlib imported")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify()
    else:
        # Provide a REPL with the repo on sys.path
        ns = {}
        try:
            # pre-import the stdlib package for convenience
            import sona
            ns['sona'] = sona
        except Exception:
            pass
        code.interact(banner=BANNER, local=ns)
