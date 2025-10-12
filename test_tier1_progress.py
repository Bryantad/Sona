"""
Test Tier 1 Implementation Progress
Tests each feature as we implement it
"""
import sys
from pathlib import Path

# Add sona to path
sys.path.insert(0, str(Path(__file__).parent))

from sona.parser_v090 import SonaParserv090
from sona.interpreter import SonaInterpreter

def test_feature(name, code, expected_behavior):
    """Test a single feature"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    print(f"Code:\n{code}\n")
    
    try:
        parser = SonaParserv090()
        interpreter = SonaInterpreter()
        
        # Parse the code
        ast_nodes = parser.parse(code)
        
        if ast_nodes is None:
            print("❌ Parser returned None")
            return False
        
        print(f"✅ Parsed successfully: {len(ast_nodes)} nodes")
        
        # Execute the nodes
        result = None
        for node in ast_nodes:
            if hasattr(node, 'execute'):
                result = node.execute(interpreter)
            elif hasattr(node, 'evaluate'):
                result = node.evaluate(interpreter)
        
        print(f"✅ Executed successfully")
        if result is not None:
            print(f"Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

# Test 1: Comments (should be ignored by parser)
test_feature(
    "Comments - Double Slash Style",
    """
// This is a comment
let x = 5;
print(x);
""",
    "Should print 5"
)

# Test 2: Boolean Literals
test_feature(
    "Boolean Literals",
    """
let is_ready = true;
let is_done = false;
print(is_ready);
print(is_done);
""",
    "Should print true and false"
)

# Test 3: Lists
test_feature(
    "List Literals",
    """
let numbers = [1, 2, 3, 4, 5];
print(numbers);
""",
    "Should print [1, 2, 3, 4, 5]"
)

# Test 4: Function Definition
test_feature(
    "Function Definition",
    """
func add(a, b) {
    return a + b;
};
let result = add(5, 3);
print(result);
""",
    "Should print 8"
)

# Test 5: Import System
test_feature(
    "Import System",
    """
import math;
let x = math.sqrt(16);
print(x);
""",
    "Should print 4.0"
)

print("\n" + "="*60)
print("TIER 1 FEATURE TEST SUMMARY")
print("="*60)
