# Language Server Support

Sona `0.15.0` established the metadata-driven LSP roadmap without claiming a
production-complete editor stack.

Sona `0.15.5` stabilizes a narrow Python language server for `.sona` and
`.smod` files. The server uses stdio JSON-RPC through pygls and is started by
the Sona VS Code extension from the selected Python environment.

## Supported in 0.15.5

- canonical diagnostics with the same IDs and source spans as `sona check`;
- completion for executable language keywords and local top-level declarations;
- manifest-backed stdlib module completion after `import`;
- stdlib member completion, including imports declared with an alias;
- hover information for known stdlib modules, stdlib members, and unambiguous
  local declarations;
- go to definition for one unambiguous top-level declaration in the current
  document;
- document symbols for top-level imports, functions, classes, `let`, `const`,
  and bare assignments; and
- correct initialize, open, change, close, shutdown, and exit lifecycle
  handling, including diagnostic clearing on close.

The local declaration index is intentionally conservative. It does not execute
or import user code, and it can return useful editor information while a file
contains incomplete syntax. Language validity still comes only from the
canonical frontend.

## Explicitly deferred

- cross-file and workspace indexing;
- scope-aware references;
- rename;
- LSP document formatting;
- signature help, semantic tokens, code actions, and workspace symbols; and
- Native Core language-server hosting.

References and formatting are not advertised to clients because lexical word
matching and textual rewriting are not safe substitutes for a scope model or a
canonical formatter. The separate CLI-backed extension commands are not LSP
capabilities.

## Runtime contract

Install Sona into the Python environment used by the extension:

```bash
python -m pip install --upgrade sona-lang
```

Set `sona.cli.pythonPath` when VS Code should use a specific interpreter. If the
setting is not explicitly configured, the extension checks the workspace
`.venv` before falling back to `python` on `PATH`. The startup preflight verifies
that both pygls and `sona.lsp_server` can be imported.

The implementation plan, support rationale, and pre-change baseline are in
[the 0.15.5 LSP stabilization plan](../plans/0.15.5-lsp-stabilization.md).
