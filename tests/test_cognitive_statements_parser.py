from sona.parser_v090 import SonaParserv090
from sona.ast_nodes import (
    IntentStatement,
    DecisionStatement,
    CognitiveTraceStatement,
    ExplainStepStatement,
    CognitiveScopeStatement,
    ProfileStatement,
)


def test_parse_cognitive_statements():
    parser = SonaParserv090()
    code = """
    intent(goal="ship");
    decision("approach", rationale="simple");
    cognitive_trace(true);
    explain_step();
    profile("adhd");
    cognitive_scope("feature") { intent(goal="subtask"); }
    """
    ast_nodes = parser.parse(code, "<cog>")
    assert any(isinstance(n, IntentStatement) for n in ast_nodes)
    assert any(isinstance(n, DecisionStatement) for n in ast_nodes)
    assert any(isinstance(n, CognitiveTraceStatement) for n in ast_nodes)
    assert any(isinstance(n, ExplainStepStatement) for n in ast_nodes)
    assert any(isinstance(n, ProfileStatement) for n in ast_nodes)
    assert any(isinstance(n, CognitiveScopeStatement) for n in ast_nodes)
