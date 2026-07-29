from sona.lsp_server import canonical_diagnostics
from sona.developer_intelligence.frontend import analyze_frontend
from sona.parser_v090 import create_parser


def test_lsp_uses_canonical_parser_ids_and_spans():
    source = "let value = (1;"
    parser_result = create_parser().validate_syntax(source)
    lsp = canonical_diagnostics("file:///fixture.sona", source)
    assert lsp
    assert lsp[0].diagnostic_id == parser_result["diagnostics"][0]["diagnostic_id"]
    assert lsp[0].span.start_line == parser_result["diagnostics"][0]["line"]
    assert lsp[0].span.start_column == parser_result["diagnostics"][0]["column"]
    assert [item.to_dict() for item in lsp] == [item.to_dict() for item in analyze_frontend(source, file="file:///fixture.sona")]
