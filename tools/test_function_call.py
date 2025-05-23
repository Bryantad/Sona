import os
from pathlib import Path
from sona.interpreter import SonaInterpreter, run_code
from lark import Lark

def get_parser():
    """Get a fresh parser instance"""
    grammar_path = Path(__file__).parent.parent / 'sona' / 'grammar.lark'
    with open(grammar_path) as f:
        grammar = f.read()
    return Lark(grammar, parser="lalr", propagate_positions=True)
    
def reset_env():
    """Reset the interpreter environment between tests"""
    return SonaInterpreter()

def test_function_call():
    """Test the function definition and call functionality"""
    print("\n=== Testing Function Parameters ===")
    
    os.environ["SONA_DEBUG"] = "1"  # Enable debug output
    
    # Code to test function parameters
    test_code = """
    func add(a, b) {
        return a + b
    }
    add(5, 7)
    """
    
    print("Original code:")
    print(test_code)
    
    # Set up parser and interpreter
    parser = get_parser()
    interpreter = reset_env()
    
    try:
        print("\nParsing code...")
        tree = parser.parse(test_code)
        print("Parse tree:", tree)
        
        print("\nRunning code...")
        result = interpreter.transform(tree)
        print("Result:", result)
        print("✅ Function call test passed!")
    except Exception as e:
        print(f"❌ Function call test failed: {e}")
    
if __name__ == "__main__":
    test_function_call()
