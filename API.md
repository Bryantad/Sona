# API Reference (Overview)

This file provides a high-level reference to the public API surfaces in the Sona runtime. For a full, auto-generated reference, consider running a documentation generator over the Python packages (e.g., Sphinx, pdoc).

## Key Modules

- `sona.interpreter` - Main interpreter entry points and module loader. Important functions/classes:

  - `SonaUnifiedInterpreter` - high-level API to execute Sona code programmatically
  - `import_module(module_path, alias=None)` - import a stdlib module into interpreter

- `sona.parser_v090` - Parser utilities

  - `create_parser(grammar_file=None)`
  - `parse_file(file_path, parser=None)`
  - `parse_string(source_code, parser=None)`

- `sona.ai.real_ai_provider` - Real AI integrations (OpenAI/Anthropic) - requires API keys

  - `RealAIProvider` - methods: `ai_complete`, `ai_explain`, `ai_debug`

- `sona.ai` - AI helper modules for code generation and explanations

- `sona.vm` - Virtual machine opcodes and program loader

## Examples

Programmatically run a Sona script:

```python
from sona.interpreter import SonaUnifiedInterpreter
interp = SonaUnifiedInterpreter()
result = interp.run_file('examples/hello_world.sona')
print(result)
```

## Generating Full API Docs

Recommended:

```bash
pip install pdoc3
pdoc --output-dir docs/api --force sona
```

This will create HTML docs under `docs/api/` for the entire `sona` package.

---

If you want, I can auto-generate a fuller API set into `docs/api/` using `pdoc` or `sphinx` and add it to the docs index.
