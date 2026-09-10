from __future__ import annotations

import json

import pytest

from sona.developer_intelligence.diagnostics import SourceSpan, diagnostic
from sona.guide import GuideError, GuideRequest, apply_fixes, explain_with_fixes
from sona.guide.fixes import preview_diagnostic_fixes, preview_stdlib_api_migration


def undefined_name(name: str = "quant", *, line: int = 3, column: int = 21):
    return diagnostic(
        "SONA-RUNTIME-003",
        "runtime",
        f"Name '{name}' is not defined.",
        span=SourceSpan(file="cart.sona", start_line=line, start_column=column),
        legacy_code="E0401",
    )


def test_undefined_name_fix_previews_exact_unique_binding_edit():
    source = "let price = 10;\nlet quantity = 3;\nlet total = price * quant;\nprint(total);\n"

    fixes = preview_diagnostic_fixes(
        GuideRequest("SONA-RUNTIME-003", undefined_name()),
        source,
        document="cart.sona",
    )

    assert len(fixes) == 1
    edit = fixes[0].edits[0]
    assert edit.rule_id == "guide.undefined-name.closest-binding"
    assert edit.start_line == 3 and edit.start_column == 21
    assert edit.end_line == 3 and edit.end_column == 26
    assert edit.expected == "quant"
    assert edit.replacement == "quantity"
    assert apply_fixes(source, fixes).splitlines()[2] == "let total = price * quantity;"


def test_undefined_name_fix_is_embedded_in_schema1_explanation():
    source = "let price = 10;\nlet quantity = 3;\nlet total = price * quant;\n"
    response = explain_with_fixes(
        GuideRequest("SONA-RUNTIME-003", undefined_name()),
        source,
        document="cart.sona",
    )

    payload = response.to_dict()
    assert json.loads(json.dumps(payload)) == payload
    assert payload["fixes"][0]["edits"][0]["stale_protection"] == "expected-original"
    assert payload["diagnostic"]["diagnostic_id"] == "SONA-RUNTIME-003"


def test_undefined_name_fix_refuses_ambiguous_candidates():
    source = "let quart = 1;\nlet quint = 2;\nprint(quant);\n"

    fixes = preview_diagnostic_fixes(
        GuideRequest("SONA-RUNTIME-003", undefined_name(line=3, column=7)),
        source,
        document="ambiguous.sona",
    )

    assert fixes == ()


def test_undefined_name_fix_uses_function_parameters_inside_the_function():
    source = "func total(quantity) {\n    let value = quant;\n    return value;\n}\nprint(total(3));\n"

    fixes = preview_diagnostic_fixes(
        GuideRequest("SONA-RUNTIME-003", undefined_name(line=2, column=17)),
        source,
        document="function.sona",
    )

    assert fixes[0].edits[0].replacement == "quantity"


def test_stale_source_refuses_to_apply_previous_preview():
    source = "let price = 10;\nlet quantity = 3;\nlet total = price * quant;\n"
    fixes = preview_diagnostic_fixes(
        GuideRequest("SONA-RUNTIME-003", undefined_name()),
        source,
        document="cart.sona",
    )

    with pytest.raises(GuideError) as caught:
        apply_fixes(source.replace("quant", "amount"), fixes)

    assert caught.value.diagnostic_id == "SONA-GUIDE-003"


def test_stdlib_api_migration_uses_manifest_replacements_and_adds_fs_import():
    source = (
        "import io;\n"
        "let body = io.read_file(\"in.txt\");\n"
        "io.write_file(\"out.txt\", body);\n"
        "print(\"io.read_file stays text\");\n"
        "# io.write_file stays comment\n"
    )

    fixes = preview_stdlib_api_migration(source, document="legacy.sona")
    updated = apply_fixes(source, fixes)

    assert [edit.replacement for edit in fixes[0].edits] == [
        "import fs;\n",
        "fs.read_text",
        "fs.write_text",
    ]
    assert "import fs;\nlet body = fs.read_text" in updated
    assert 'print("io.read_file stays text");' in updated
    assert "# io.write_file stays comment" in updated


def test_stdlib_api_migration_preserves_existing_fs_import_and_requires_io_import():
    with_fs = "import io;\nimport fs;\nlet body = io.read_file(\"in.txt\");\n"
    fixes = preview_stdlib_api_migration(with_fs, document="legacy.sona")
    assert [edit.replacement for edit in fixes[0].edits] == ["fs.read_text"]

    local_object = "let io = {};\nlet body = io.read_file(\"in.txt\");\n"
    assert preview_stdlib_api_migration(local_object, document="local.sona") == ()


@pytest.mark.parametrize("source", [
    'import io;\nfunc read(io) { return io.read_file("in.txt"); }\n',
    'import io;\nlet io = {};\nio.read_file("in.txt");\n',
    'import io;\nlet fs = {};\nio.read_file("in.txt");\n',
    'func read() {\nimport io;\nreturn io.read_file("in.txt");\n}\n',
    'import io;\nlet box = {};\nbox.io.read_file("in.txt");\n',
])
def test_migration_refuses_shadowed_nested_or_member_bindings(source):
    assert preview_stdlib_api_migration(source, document="ambiguous.sona") == ()


@pytest.mark.parametrize("line,column", [
    ('print("quant");', 8), ('# quant', 3), ('print(quantum);', 7),
    ('print(obj.quant);', 11),
])
def test_name_fix_requires_whole_unqualified_code_identifier(line, column):
    source = "let quantity = 3;\n" + line + "\n"
    assert preview_diagnostic_fixes(
        GuideRequest("SONA-RUNTIME-003", undefined_name(line=2, column=column)), source, document="stale.sona",
    ) == ()
