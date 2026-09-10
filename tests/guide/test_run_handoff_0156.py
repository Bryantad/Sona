from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from sona.guide.service import guide_request

ROOT = Path(__file__).resolve().parents[2]


def run(path, *flags):
    return subprocess.run([sys.executable, "-m", "sona", "run", str(path), *flags],
                          env={**os.environ, "PYTHONPATH": str(ROOT)}, cwd=path.parent,
                          text=True, capture_output=True, timeout=20, check=False)


def test_actual_runtime_diagnostic_reaches_all_guide_modes(tmp_path):
    source = 'let price = 10;\nlet quantity = 3;\nlet total = price * quant;\n'
    path = tmp_path / "flagship.sona"
    path.write_text(source, encoding="utf-8")
    ordinary = run(path)
    structured = run(path, "--json")
    assert structured.returncode == ordinary.returncode == 1
    packet = json.loads(structured.stdout)
    assert packet["streams"]["stderr"] == ordinary.stderr
    assert packet["source_sha256"] == "sha256:" + hashlib.sha256(source.encode()).hexdigest()
    assert packet["source_mapping"] == "original"
    assert len(packet["diagnostics"]) == 1
    diagnostic = packet["diagnostics"][0]
    assert diagnostic["diagnostic_id"] == "SONA-RUNTIME-003"
    for mode in ("guided", "balanced", "expert"):
        result = guide_request({"schema_version": 1, "action": "diagnostic", "diagnostic": diagnostic,
                                "source": source, "document": str(path), "options": {"mode": mode}})
        assert result["diagnostic"]["diagnostic_id"] == diagnostic["diagnostic_id"]
        assert result["fixes"][0]["edits"][0]["expected"] == "quant"
        assert result["fixes"][0]["edits"][0]["replacement"] == "quantity"


@pytest.mark.parametrize("source", ['print("ok");', 'print("{\\\"status\\\":\\\"ok\\\"}");'])
def test_program_stdout_cannot_replace_run_envelope(source, tmp_path):
    path = tmp_path / "output.sona"
    path.write_text(source, encoding="utf-8")
    ordinary = run(path)
    result = run(path, "--json")
    assert result.returncode == ordinary.returncode == 0
    packet = json.loads(result.stdout)
    assert packet["streams"]["stdout"] == ordinary.stdout
    assert packet["diagnostics"] == []


def test_missing_file_reports_unavailable_diagnostic_without_inventing_name_error(tmp_path):
    result = run(tmp_path / "missing.sona", "--json")
    assert result.returncode == 1
    packet = json.loads(result.stdout)
    assert packet["diagnostic_status"] == "unavailable"
    assert packet["diagnostics"] == [] and packet["source_sha256"] is None


def test_capture_prefix_is_explicitly_truncated_without_changing_exit_code(tmp_path):
    from argparse import Namespace
    from contextlib import redirect_stdout
    from io import StringIO

    from sona.run_result import MAX_CAPTURE_CHARACTERS, run_json

    def handler(_args):
        print("x" * (MAX_CAPTURE_CHARACTERS + 20))
        return 0

    output = StringIO()
    with redirect_stdout(output):
        assert run_json(Namespace(json=True), handler) == 0
    packet = json.loads(output.getvalue())
    assert packet["truncated"]["stdout"] is True
    assert len(packet["streams"]["stdout"]) == MAX_CAPTURE_CHARACTERS


def test_source_identity_normalizes_bom_and_crlf(tmp_path):
    source = 'let quantity = 3;\nprint(quant);\n'
    path = tmp_path / "windows.sona"
    path.write_bytes(b"\xef\xbb\xbf" + source.replace("\n", "\r\n").encode())
    packet = json.loads(run(path, "--json").stdout)
    assert packet["source_identity_format"] == "utf8-decoded-text-lf"
    assert packet["source_sha256"] == "sha256:" + hashlib.sha256(source.encode()).hexdigest()


def test_embedded_python_marks_source_mapping_transformed(tmp_path):
    path = tmp_path / "mixed.sona"
    path.write_text('@check_types\ndef plus(value):\n    return value + 1\n\nprint(quant);\n', encoding="utf-8")
    packet = json.loads(run(path, "--json").stdout)
    assert packet["source_mapping"] == "transformed"
