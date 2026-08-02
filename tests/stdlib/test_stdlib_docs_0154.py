from __future__ import annotations

from pathlib import Path

from sona.parser_v090 import SonaParserv090


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference" / "stdlib"


def test_all_stdlib_reference_pages_are_present():
    assert {path.name for path in REFERENCE.glob("*.md")} == {
        "README.md",
        "data.md",
        "date-time.md",
        "fs.md",
        "http.md",
        "io-stdin.md",
        "runtime-capabilities.md",
    }


def test_documented_sona_examples_parse_with_the_canonical_frontend():
    parser = SonaParserv090()
    examples = []
    for path in sorted(REFERENCE.glob("*.md")):
        source = path.read_text(encoding="utf-8")
        for index, block in enumerate(source.split("```sona")[1:], start=1):
            code = block.split("```", 1)[0].strip()
            examples.append((path, index, code))

    assert len(examples) == 5
    for path, index, code in examples:
        assert parser.parse(code, filename=f"{path.as_posix()}#example-{index}")


def test_docs_state_native_http_and_random_boundaries_honestly():
    overview = (REFERENCE / "README.md").read_text(encoding="utf-8")
    http = (REFERENCE / "http.md").read_text(encoding="utf-8")
    data = (REFERENCE / "data.md").read_text(encoding="utf-8")
    assert "`http` | Bounded HTTP requests | PASS | UNSUPPORTED" in overview
    assert "SONA-HTTP-005" in http
    assert "does not claim identical cross-engine random sequences" in data
