from __future__ import annotations

import json
from dataclasses import replace

import pytest

from sona.developer_intelligence.diagnostics import SourceSpan, diagnostic
from sona.developer_intelligence.frontend import analyze_frontend
from sona.guide import GuideError, GuideRequest, explain, render_text
from sona.guide.catalog import CATALOG
from sona.guide.models import MODES, STYLES


@pytest.mark.parametrize("identifier", list(CATALOG))
@pytest.mark.parametrize("mode", MODES)
def test_catalog_entry_has_stable_serializable_reference_output(identifier, mode):
    request = GuideRequest(identifier, mode=mode)
    response = explain(request)
    payload = response.to_dict()
    assert json.loads(json.dumps(payload)) == payload
    assert payload["schema_version"] == 1
    assert payload["diagnostic_id"] == identifier
    assert payload["basis"] == "catalog-reference"
    assert payload["diagnostic"] is None
    assert payload["fixes"] == []
    assert payload["provenance"]["source"] == "sona-guide-catalog"
    assert payload["concept_ids"]
    assert identifier in render_text(response)
    assert explain(request).to_dict() == payload


@pytest.mark.parametrize("style", STYLES)
def test_modes_preserve_exact_canonical_payload_and_control_only_presentation(style):
    original = diagnostic(
        "SONA-RUNTIME-003", "runtime", "Name 'quant' is not defined.",
        hint="Check which binding you meant.",
        span=SourceSpan(file="demo.sona", start_line=3, start_column=21),
        legacy_code="E0401", metadata={"names": ["quantity"]},
    )
    before = original.to_dict()
    responses = [explain(GuideRequest(original.diagnostic_id, original, mode, style)) for mode in MODES]
    texts = [render_text(response) for response in responses]
    assert all(response.to_dict()["diagnostic"] == before for response in responses)
    assert original.to_dict() == before
    assert all(response.basis == "reported-diagnostic" for response in responses)
    assert "Why this happens" in texts[0] and "Related concepts" in texts[0]
    assert "Next step" in texts[1] and "Related concepts" not in texts[1]
    assert texts[2] == "E0401 SONA-RUNTIME-003: Name 'quant' is not defined. (demo.sona:3:21)"
    assert len(texts[0]) > len(texts[1]) > len(texts[2])


def test_guide_consumes_real_parser_diagnostic_without_inventing_missing_token():
    original = analyze_frontend("let value = (1;", file="broken.sona")[0]
    assert original.diagnostic_id == "SONA-PARSE-003"
    response = explain(GuideRequest(original.diagnostic_id, original))
    assert response.to_dict()["diagnostic"] == original.to_dict()
    assert "missing `}`" not in render_text(response)
    assert response.to_dict()["fixes"] == []


@pytest.mark.parametrize("identifier", ["SONA-NAME-001", "UNKNOWN-123", "secret=private"])
def test_unknown_identifier_has_no_guessed_explanation(identifier):
    with pytest.raises(GuideError) as caught:
        explain(GuideRequest(identifier))
    assert caught.value.diagnostic_id == "SONA-GUIDE-001"
    assert identifier not in json.dumps(caught.value.to_dict())


@pytest.mark.parametrize("options", [
    {"mode": "adhd"}, {"style": "llm"}, {"density": "hide-errors"},
    {"diagnostic_id": ""}, {"diagnostic_id": "x" * 97}, {"diagnostic": {}},
])
def test_invalid_guide_request_is_structured(options):
    with pytest.raises(GuideError) as caught:
        GuideRequest(**{"diagnostic_id": "SONA-RUNTIME-003", **options})
    assert caught.value.diagnostic_id == "SONA-GUIDE-002"


def test_mismatched_diagnostic_identity_is_rejected():
    original = diagnostic("SONA-PARSE-003", "syntax", "Incomplete syntax.")
    with pytest.raises(GuideError, match="does not match"):
        GuideRequest("SONA-RUNTIME-003", original)


def test_text_renderer_escapes_terminal_controls_without_mutating_diagnostic():
    original = diagnostic("SONA-RUNTIME-003", "runtime", "Name '\x1b[2J' is not defined.")
    response = explain(GuideRequest(original.diagnostic_id, original, mode="expert"))
    assert "\x1b" not in render_text(response)
    assert "\\u001b" in render_text(response)
    assert response.to_dict()["diagnostic"] == original.to_dict()


def test_why_does_not_claim_receipt_authentication():
    request = GuideRequest("PROOF-VERIFY-005", style="technical")
    text = render_text(explain(request))
    assert "does not authenticate" in text
    assert "Reference explanation" in text
    assert "Receipt VALID" not in text
    assert "repair the receipt by replacing its hash" in text


def test_guidance_style_changes_explanation_without_changing_example_or_identity():
    request = GuideRequest("SONA-RUNTIME-003")
    outputs = [explain(replace(request, style=style)).to_dict() for style in STYLES]
    why = [next(section["body"] for section in output["sections"] if section["key"] == "why") for output in outputs]
    assert len(set(why)) == 3
    assert all(output["diagnostic_id"] == request.diagnostic_id for output in outputs)


def test_sona_catalog_examples_execute_in_the_real_interpreter(capsys):
    from sona.interpreter import SonaUnifiedInterpreter

    expected = {"names": "30", "delimiters": "5"}
    checked = set()
    for entry in CATALOG.values():
        if entry.example_kind != "sona" or entry.topic in checked:
            continue
        checked.add(entry.topic)
        SonaUnifiedInterpreter(compatibility_mode="sona").interpret(
            entry.example, filename="guide-example.sona"
        )
        assert capsys.readouterr().out.strip() == expected[entry.topic]
    assert checked == set(expected)
