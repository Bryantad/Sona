"""Read-only validation for untrusted whole-source Guide proposals."""

from __future__ import annotations

import hashlib

from sona.developer_intelligence.frontend import analyze_frontend

from .service_limits import MAX_PROPOSAL_SOURCE_BYTES


def validate_source_proposal(
    source: str,
    proposed_source: str,
    *,
    document: str = "<editor>",
) -> dict:
    """Check a candidate with Sona's deterministic frontend; never write or execute it."""
    if not isinstance(source, str) or not isinstance(proposed_source, str):
        raise ValueError("proposal source must be text")
    try:
        source_bytes = source.encode("utf-8", errors="strict")
        proposed_bytes = proposed_source.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ValueError("proposal source must be valid UTF-8 text") from exc
    if max(len(source_bytes), len(proposed_bytes)) > MAX_PROPOSAL_SOURCE_BYTES:
        raise ValueError("proposal source exceeds its size limit")
    if not isinstance(document, str) or not document or len(document) > 4096:
        raise ValueError("proposal document identifier is invalid")

    after = analyze_frontend(proposed_source, file=document)
    validation_errors = [item.to_dict() for item in after if item.severity == "error"]

    changed = source_bytes != proposed_bytes
    valid = changed and not validation_errors
    if not changed:
        validation_code = "SONA-PROPOSAL-NO-CHANGE"
    elif validation_errors:
        validation_code = "SONA-PROPOSAL-VALIDATION-FAILED"
    else:
        validation_code = "SONA-PROPOSAL-VALID"
    return {
        "schema_version": 1,
        "status": "valid" if valid else "rejected",
        "validation_code": validation_code,
        "changed": changed,
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "proposed_sha256": hashlib.sha256(proposed_bytes).hexdigest(),
        "diagnostics": [item.to_dict() for item in after],
        "validation_errors": validation_errors,
        "note": (
            "Validation is deterministic and read-only; it does not approve, "
            "apply, or execute the proposal."
        ),
    }
