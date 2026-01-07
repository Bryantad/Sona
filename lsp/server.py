#!/usr/bin/env python3
"""Compatibility entrypoint for the Sona LSP.

The real implementation lives in `sona.lsp_server` so it can be executed via
`python -m sona.lsp_server --stdio` anywhere the Sona package is installed.
"""

from sona.lsp_server import main


if __name__ == "__main__":
    raise SystemExit(main())
