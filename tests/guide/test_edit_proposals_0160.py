"""Untrusted AI edit proposals are frontend-validated without side effects."""

from __future__ import annotations

import json

from sona.guide.service import MAX_SOURCE_BYTES, guide_request, request_json


def test_valid_proposal_returns_diagnostics_and_hashes_without_executing_source(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    source = 'import fs;\nfs.write_text("not-created.txt", "original");\n'
    proposed = 'import fs;\nfs.write_text("not-created.txt", "candidate");\n'
    result = guide_request(
        {
            "schema_version": 1,
            "action": "validate_proposal",
            "document": "proposal.sona",
            "source": source,
            "proposed_source": proposed,
        }
    )

    assert result["status"] == "valid"
    assert result["validation_code"] == "SONA-PROPOSAL-VALID"
    assert result["changed"] is True
    assert len(result["source_sha256"]) == 64
    assert len(result["proposed_sha256"]) == 64
    assert result["diagnostics"] == []
    assert source not in json.dumps(result)
    assert proposed not in json.dumps(result)
    assert list(tmp_path.iterdir()) == []


def test_candidate_with_new_frontend_errors_is_rejected():
    result = guide_request(
        {
            "schema_version": 1,
            "action": "validate_proposal",
            "source": "let value = 1;\n",
            "proposed_source": "let value = (1;\n",
        }
    )

    assert result["status"] == "rejected"
    assert result["validation_code"] == "SONA-PROPOSAL-VALIDATION-FAILED"
    assert result["validation_errors"]
    assert all(item["severity"] == "error" for item in result["validation_errors"])


def test_proposal_is_rejected_while_any_frontend_errors_remain():
    source = "let value = (1;\n"
    result = guide_request(
        {
            "schema_version": 1,
            "action": "validate_proposal",
            "source": source,
            "proposed_source": source + "let other = (2;\n",
        }
    )

    assert result["status"] == "rejected"
    assert result["validation_errors"]


def test_unchanged_proposal_is_rejected_as_no_change():
    source = "let value = 1;\n"
    result = guide_request(
        {
            "schema_version": 1,
            "action": "validate_proposal",
            "source": source,
            "proposed_source": source,
        }
    )

    assert result["status"] == "rejected"
    assert result["validation_code"] == "SONA-PROPOSAL-NO-CHANGE"


def test_malformed_or_oversized_proposal_fails_safely():
    missing = guide_request(
        {
            "schema_version": 1,
            "action": "validate_proposal",
            "source": "let value = 1;",
        }
    )
    oversized = guide_request(
        {
            "schema_version": 1,
            "action": "validate_proposal",
            "source": "let value = 1;",
            "proposed_source": "x" * (MAX_SOURCE_BYTES + 1),
        }
    )
    assert missing["status"] == "unavailable"
    assert oversized["status"] == "unavailable"
    assert "proposed_source" not in json.dumps(oversized)


def test_json_request_transport_exposes_same_validation_contract():
    request = {
        "schema_version": 1,
        "action": "validate_proposal",
        "source": "let value = 1;\n",
        "proposed_source": "let value = 2;\n",
    }
    assert request_json(json.dumps(request)) == guide_request(request)
