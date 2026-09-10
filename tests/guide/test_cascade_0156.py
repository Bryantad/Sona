from __future__ import annotations

import json

import pytest

from sona.developer_intelligence.diagnostics import SourceSpan, diagnostic
from sona.guide import GuideError, focus_diagnostics, render_focus_text


def diag(identifier: str, line: int, column: int, *, file: str = "broken.sona"):
    return diagnostic(
        identifier,
        "syntax" if identifier.startswith("SONA-PARSE-") else "runtime",
        f"{identifier} message",
        hint="Review this diagnostic.",
        span=SourceSpan(file=file, start_line=line, start_column=column),
    )


def test_focus_groups_reviewed_downstream_delimiter_noise_without_losing_complete_output():
    diagnostics = (
        diag("SONA-PARSE-003", 1, 13),
        diag("SONA-PARSE-001", 2, 1),
        diag("SONA-RUNTIME-003", 3, 9),
    )

    focused = focus_diagnostics(diagnostics, density="focused")
    payload = focused.to_dict()

    assert focused.visible_indices == (0,)
    assert focused.root_indices == (0,)
    assert focused.suppressed_count == 2
    assert [item.to_dict() for item in diagnostics] == payload["diagnostics"]
    assert payload["visible_diagnostics"] == [diagnostics[0].to_dict()]
    assert [relation["secondary_index"] for relation in payload["relations"]] == [1, 2]
    assert payload["provenance"]["rules"] == ["guide.cascade.unclosed-delimiter-downstream"]


def test_complete_density_keeps_original_diagnostic_order_visible():
    diagnostics = (
        diag("SONA-RUNTIME-004", 5, 1),
        diag("SONA-PARSE-003", 1, 13),
        diag("SONA-PARSE-001", 4, 1),
    )

    result = focus_diagnostics(diagnostics, density="complete")

    assert result.visible_indices == (0, 1, 2)
    assert [item["diagnostic_id"] for item in result.to_dict()["visible_diagnostics"]] == [
        "SONA-RUNTIME-004",
        "SONA-PARSE-003",
        "SONA-PARSE-001",
    ]


def test_normal_density_keeps_roots_and_hides_only_reviewed_secondaries():
    diagnostics = (
        diag("SONA-PARSE-003", 1, 13),
        diag("SONA-PARSE-001", 2, 1),
        diag("SONA-RUNTIME-004", 3, 1),
    )

    result = focus_diagnostics(diagnostics, density="normal")

    assert result.visible_indices == (0, 2)
    assert result.suppressed_count == 1


def test_delimiter_relations_do_not_cross_files_or_hide_infrastructure_errors():
    diagnostics = (
        diag("SONA-PARSE-003", 1, 13, file="a.sona"),
        diag("SONA-PARSE-001", 2, 1, file="b.sona"),
        diag("SONA-PARSE-099", 3, 1, file="a.sona"),
    )

    result = focus_diagnostics(diagnostics, density="focused")

    assert result.relations == ()
    assert result.visible_indices == (0,)
    assert set(result.root_indices) == {0, 1, 2}


def test_focus_payload_is_serializable_and_text_renderer_escapes_controls():
    diagnostics = (
        diagnostic(
            "SONA-PARSE-003",
            "syntax",
            "bad \x1b[2J message",
            span=SourceSpan(file="broken.sona", start_line=1, start_column=1),
        ),
    )

    result = focus_diagnostics(diagnostics, density="focused")
    assert json.loads(json.dumps(result.to_dict())) == result.to_dict()
    text = render_focus_text(result)
    assert "\x1b" not in text
    assert "\\u001b" in text


def test_focus_rejects_non_canonical_diagnostics():
    with pytest.raises(GuideError) as caught:
        focus_diagnostics([{"diagnostic_id": "SONA-PARSE-003"}])  # type: ignore[list-item]

    assert caught.value.diagnostic_id == "SONA-GUIDE-002"
