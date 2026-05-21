import gc
import os
import re
import shutil
from pathlib import Path

import run_sona
from sona.interpreter import SonaUnifiedInterpreter


ROOT = Path(__file__).resolve().parents[1]
STDLIB_DOC = ROOT / "docs" / "STDLIB_REFERENCE.md"
RUNNABLE_FENCE = re.compile(r"```sona\s+runnable\s*\n(.*?)```", re.DOTALL)
STABLE_MODULES = [
    "csv",
    "date",
    "env",
    "fs",
    "hashing",
    "io",
    "json",
    "math",
    "memory",
    "path",
    "string",
    "time",
]


def _clean_runtime_artifacts(root: Path) -> None:
    for path in root.rglob(".sona"):
        if path.is_dir() and root in path.resolve().parents:
            shutil.rmtree(path, ignore_errors=True)


def test_stdlib_reference_has_required_modules():
    content = STDLIB_DOC.read_text(encoding="utf-8")

    for module in STABLE_MODULES:
        assert f"## {module}\n" in content


def test_runnable_stdlib_doc_examples_execute(tmp_path):
    content = STDLIB_DOC.read_text(encoding="utf-8")
    snippets = RUNNABLE_FENCE.findall(content)
    assert snippets

    examples_src = ROOT / "examples"
    examples_dst = tmp_path / "examples"
    shutil.copytree(examples_src, examples_dst, ignore=shutil.ignore_patterns(".sona"))

    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        for index, snippet in enumerate(snippets, start=1):
            path = tmp_path / f"stdlib_doc_{index}.sona"
            path.write_text(snippet.strip() + "\n", encoding="utf-8")
            interpreter = SonaUnifiedInterpreter(project_root=tmp_path)
            exit_code, _source, _error = run_sona.run_sona_file(
                str(path),
                interpreter=interpreter,
            )
            del interpreter
            gc.collect()
            assert exit_code == 0, f"runnable stdlib docs example failed: {index}"
    finally:
        os.chdir(original_cwd)
        _clean_runtime_artifacts(tmp_path)
