"""
Debug Sona Execution - Check why print statements don't output
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sona.parser_v090 import SonaParserv090
from sona.interpreter import SonaInterpreter

code = """
let x = 5;
print(x);
"""

print("=== Parsing ===")
parser = SonaParserv090()
ast_nodes = parser.parse(code)

print(f"Parsed: {type(ast_nodes)}")

# Handle if we got a list of lists
if isinstance(ast_nodes, list) and len(ast_nodes) == 1 and isinstance(ast_nodes[0], list):
    ast_nodes = ast_nodes[0]

print(f"Processing {len(ast_nodes)} nodes")
for i, node in enumerate(ast_nodes):
    print(f"Node {i}: {type(node).__name__}")
    print(f"  Has execute: {hasattr(node, 'execute')}")
    print(f"  Has evaluate: {hasattr(node, 'evaluate')}")
    print(f"  Node: {node}")

print("\n=== Executing ===")
interpreter = SonaInterpreter()
for i, node in enumerate(ast_nodes):
    print(f"\nExecuting node {i}...")
    if hasattr(node, 'execute'):
        result = node.execute(interpreter)
        print(f"  execute() returned: {result}")
    elif hasattr(node, 'evaluate'):
        result = node.evaluate(interpreter)
        print(f"  evaluate() returned: {result}")
    else:
        print(f"  No execute/evaluate method!")
