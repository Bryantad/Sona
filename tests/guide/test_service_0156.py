from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from sona.developer_intelligence.diagnostics import SourceSpan, diagnostic
from sona.guide.adapters import diagnostic_from_payload
from sona.guide.catalog import CONCEPTS
from sona.guide.profile import LearningProfile
from sona.guide.service import MAX_SOURCE_BYTES, guide_request, request_json

ROOT = Path(__file__).resolve().parents[2]


def test_diagnostic_adapters_preserve_related_locations_node_type_and_native_fields():
    original = replace(diagnostic(
        "SONA-RUNTIME-003", "runtime", "Name 'quant' is not defined.",
        span=SourceSpan(file="demo.sona", start_line=2, start_column=7, node_type="VariableExpression"),
        metadata={"name": "quant"}, legacy_code="E0401",
    ), related_locations=(SourceSpan(file="demo.sona", start_line=1, start_column=5),))
    assert diagnostic_from_payload(original.to_dict()).to_dict() == original.to_dict()
    native = diagnostic_from_payload({
        "diagnostic_id": "SONA-NATIVE-RUNTIME-003", "message": "Undefined name 'quant'.",
        "location": {"file": "demo.sona", "line": 2, "column": 7},
        "code": "E0401", "suggestion": "Check visible names.",
    })
    assert native.span == SourceSpan(file="demo.sona", start_line=2, start_column=7)
    assert native.hint == "Check visible names." and native.legacy_code == "E0401"


@pytest.mark.parametrize("mode", ["guided", "balanced", "expert"])
def test_request_cli_parity_preserves_diagnostic_fixes_and_creates_no_state(tmp_path, mode):
    item = diagnostic(
        "SONA-RUNTIME-003", "runtime", "Name 'quant' is not defined.",
        span=SourceSpan(file="demo.sona", start_line=2, start_column=7),
        metadata={"name": "quant"},
    ).to_dict()
    request = {
        "schema_version": 1, "action": "diagnostic", "document": "demo.sona",
        "source": "let quantity = 3;\nprint(quant);\n", "diagnostic": item, "options": {"mode": mode},
    }
    expected = guide_request(request)
    result = subprocess.run(
        [sys.executable, "-m", "sona", "guide", "request", "--json", "--no-profile"],
        input=json.dumps(request), capture_output=True, text=True, cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT)}, timeout=15, check=False,
    )
    assert result.returncode == 0 and result.stderr == ""
    assert json.loads(result.stdout) == expected
    assert expected["diagnostic"] == item
    assert expected["fixes"][0]["edits"][0]["replacement"] == "quantity"
    assert list(tmp_path.iterdir()) == []


def test_selection_uses_parser_ranges_and_never_executes_source(tmp_path, monkeypatch):
    from sona.developer_intelligence.frontend import analyze_frontend

    monkeypatch.chdir(tmp_path)
    source = 'import fs;\nlet values = [1, 2];\nfs.write_text("must-not-exist.txt", "secret");\n'
    result = guide_request({
        "schema_version": 1, "action": "selection", "source": source,
        "selection": {"start_line": 2, "start_column": 14, "end_line": 2, "end_column": 20},
    })
    assert result["basis"] == "static-selection"
    assert [item["id"] for item in result["concepts"]] == ["variables", "collections"]
    assert result["focus"]["diagnostics"] == [item.to_dict() for item in analyze_frontend(source, file="<editor>")]
    assert "secret" not in json.dumps(result)
    assert list(tmp_path.iterdir()) == []
    broken = guide_request({"schema_version": 1, "action": "selection", "source": "let x = (1;"})
    assert broken["concepts"] == []
    assert broken["focus"]["diagnostics"][0]["diagnostic_id"] == "SONA-PARSE-003"


def test_quiet_and_profile_decay_change_presentation_only():
    items = [
        diagnostic("SONA-PARSE-090", "syntax", "Warning.", severity="warning").to_dict(),
        diagnostic("SONA-RUNTIME-003", "runtime", "Name 'x' is not defined.").to_dict(),
    ]
    profile = LearningProfile(quiet=True, concepts={"variables": "comfortable", "scope": "comfortable"})
    result = guide_request({
        "schema_version": 1, "action": "focus", "diagnostics": items,
        "options": {"density": "complete"},
    }, profile=profile)
    assert result["diagnostics"] == items
    assert result["visible_indices"] == [1] and result["suppressed_count"] == 1
    request = {"schema_version": 1, "action": "diagnostic", "diagnostic": items[1]}
    assert guide_request(request, profile=profile)["mode"] == "balanced"
    assert guide_request({**request, "options": {"mode": "guided"}}, profile=profile)["mode"] == "guided"


@pytest.mark.parametrize("payload", [
    [], {}, {"schema_version": True}, {"schema_version": 2},
    {"schema_version": 1, "action": "secret"},
    {"schema_version": 1, "action": "diagnostic", "diagnostic": []},
    {"schema_version": 1, "action": "diagnostic", "diagnostic_id": "secret"},
    {"schema_version": 1, "action": "selection", "source": "secret" * MAX_SOURCE_BYTES},
    {"schema_version": 1, "action": "selection", "source": "let x = 1;", "options": {"mode": "medical"}},
    {"schema_version": 1, "action": "selection", "source": "let x = 1;", "selection": {}},
    {"schema_version": 1, "action": "concept", "concept_id": "variables", "options": {"quiet": "true"}},
])
def test_invalid_requests_fail_without_echoing_input(payload):
    result = guide_request(payload)
    assert result["status"] == "unavailable"
    assert "secret" not in json.dumps(result) and "medical" not in json.dumps(result)


def test_json_transport_rejects_duplicates_and_malformed_json():
    for raw in ('{', '{"schema_version":1,"schema_version":1}', 'NaN'):
        assert request_json(raw)["status"] == "unavailable"


def test_reviewed_concept_sona_examples_execute(capsys):
    from sona.interpreter import SonaUnifiedInterpreter

    outputs = {"variables": "3", "conditions": "yes", "loops": "1\n2\n3", "functions": "6", "collections": "1", "modules": "3.0", "files": "", "guardian": ""}
    for identifier, expected in outputs.items():
        SonaUnifiedInterpreter(compatibility_mode="sona").interpret(
            CONCEPTS[identifier].example, filename="guide-concept.sona",
        )
        assert capsys.readouterr().out.strip() == expected
