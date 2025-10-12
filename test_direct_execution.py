"""
Direct test of Sona execution
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sona.parser_v090 import SonaParserv090
from sona.interpreter import SonaUnifiedInterpreter

code = """
func add(a, b) {
    return a + b;
};

let x = add(2, 3);
print(x);
"""

print("=== Creating interpreter ===")
interpreter = SonaUnifiedInterpreter()

print("\n=== Creating parser ===")
parser = SonaParserv090()

print("\n=== Parsing code ===")
ast_nodes = parser.parse(code)
print(f"Got {len(ast_nodes)} nodes")

# Debug: print function body
for node in ast_nodes:
    if hasattr(node, 'body'):
        print(f"\n{node.__class__.__name__} body:")
        for stmt in node.body:
            print(f"  {stmt}")
            if hasattr(stmt, 'expression'):
                print(f"    expression: {stmt.expression}")
                print(f"    expression type: {type(stmt.expression)}")
                if hasattr(stmt.expression, 'data'):
                    print(f"    tree data: {stmt.expression.data}")
                    print(f"    tree children: {stmt.expression.children}")

print("\n=== Executing nodes ===")
for i, node in enumerate(ast_nodes):
    print(f"\nNode {i}: {type(node).__name__}")
    if hasattr(node, 'arguments'):
        print(f"  Arguments: {node.arguments}")
        print(f"  Arg types: {[type(a) for a in node.arguments]}")
    try:
        result = node.execute(interpreter)
        print(f"  Result: {result}")
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()

print("\n=== Done ===")
