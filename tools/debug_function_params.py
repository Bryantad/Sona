import os
from sona.interpreter import SonaInterpreter
from lark import Lark

def debug_func_params():
    """Debug function parameter issues"""
    print("=== Testing Function Parameters ===")
    
    # Enable debug output
    os.environ["SONA_DEBUG"] = "1"
    
    # Create a fresh parser and interpreter
    interpreter = SonaInterpreter()
    grammar_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sona', 'grammar.lark')
    with open(grammar_path, 'r') as f:
        grammar = f.read()
    
    parser = Lark(grammar, parser='lalr', propagate_positions=True)
    
    # Define a simple function
    func_code = """
    func test(x) {
        print("Parameter x = " + x)
        return x
    }
    """
    
    print("Defining function...")
    func_tree = parser.parse(func_code)
    interpreter.transform(func_tree)
    
    # Dump the interpreter state
    print("Interpreter functions:", interpreter.functions.keys())
    if 'test' in interpreter.functions:
        params, body = interpreter.functions['test']
        print(f"Function 'test' parameters: {[str(p) for p in params]}")
    
    # Call the function
    print("\nCalling function...")
    call_code = "test(42)"
    call_tree = parser.parse(call_code)
    
    # Add debugging
    original_push = interpreter.push_scope
    def debug_push():
        scope = original_push()
        print(f"Pushed new scope, now have {len(interpreter.env)} scopes")
        return scope
    interpreter.push_scope = debug_push
    
    original_get_var = interpreter.get_var
    def debug_get_var(name):
        print(f"Looking for variable '{name}' in {len(interpreter.env)} scopes")
        for i, scope in enumerate(interpreter.env):
            print(f"  Scope {i}: {list(scope.keys())}")
        try:
            result = original_get_var(name)
            print(f"  Found '{name}' = {result}")
            return result
        except Exception as e:
            print(f"  Error: {e}")
            raise
    interpreter.get_var = debug_get_var
    
    try:
        result = interpreter.transform(call_tree)
        print(f"Function call result: {result}")
    except Exception as e:
        print(f"Function call error: {e}")

if __name__ == "__main__":
    debug_func_params()
