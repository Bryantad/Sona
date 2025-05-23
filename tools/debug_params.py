import os
import sys
from lark import Lark, Transformer, Tree, Token
from pathlib import Path

# Simplified interpreter for testing function parameters
class SimpleDebugTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.env = [{}]  # Scope stack
        self.functions = {}
        
    def push_scope(self):
        self.env.append({})
        print(f"Pushed scope, now at depth {len(self.env)}")
        return self.env[-1]
    
    def pop_scope(self):
        if len(self.env) > 1:
            scope = self.env.pop()
            print(f"Popped scope, now at depth {len(self.env)}")
            return scope
        return None
    
    def set_var(self, name, value):
        print(f"Setting var {name} = {value} in scope {len(self.env)-1}")
        self.env[-1][name] = value
        return value
    
    def get_var(self, name):
        for scope in reversed(self.env):
            if name in scope:
                return scope[name]
        raise NameError(f"Variable {name} not found")
    
    def var(self, args):
        name = str(args[0])
        print(f"Looking for variable: {name}")
        for i, scope in enumerate(self.env):
            print(f"  Scope {i}: {list(scope.keys())}")
        try:
            value = self.get_var(name)
            print(f"  Found {name} = {value}")
            return value
        except NameError:
            print(f"  Not found: {name}")
            raise Exception(f"Variable '{name}' not found")
    
    def param_list(self, args):
        print(f"PARAM LIST: {args}")
        return args
    
    def func_def(self, args):
        name, params, body = args
        func_name = str(name)
        
        # Process parameters
        param_tokens = []
        if params is not None:
            if isinstance(params, list):
                param_tokens = params
            elif hasattr(params, 'children'):
                param_tokens = params.children
        
        param_names = [str(t) for t in param_tokens]
        print(f"Defined function {func_name} with parameters: {param_names}")
        
        self.functions[func_name] = (param_tokens, body)
        return None
    
    def func_call(self, args):
        name_node, *rest = args
        func_name = str(name_node)
        
        # Get arguments
        call_args = []
        if len(rest) > 0 and hasattr(rest[0], 'data') and rest[0].data == 'args':
            call_args = [self.transform(arg) for arg in rest[0].children]
        
        print(f"Calling function {func_name} with args: {call_args}")
        
        if func_name not in self.functions:
            raise Exception(f"Function {func_name} not found")
        
        params, body = self.functions[func_name]
        param_names = [str(p) for p in params]
        
        print(f"Function {func_name} expects parameters: {param_names}")
        
        if len(params) != len(call_args):
            raise Exception(f"Function {func_name} expects {len(params)} args, got {len(call_args)}")
        
        # Create function scope and set parameters
        func_scope = self.push_scope()
        for param, value in zip(params, call_args):
            param_name = str(param)
            print(f"Setting parameter {param_name} = {value}")
            func_scope[param_name] = value
        
        # Execute function body
        result = None
        for stmt in body.children:
            result = self.transform(stmt)
        
        self.pop_scope()
        print(f"Function {func_name} returned: {result}")
        return result
    
    def args(self, args):
        print(f"ARGS: {args}")
        return args
    
    def add(self, args):
        left = self.transform(args[0])
        right = self.transform(args[1])
        return left + right
    
    def number(self, args):
        return float(args[0])
    
    def string(self, args):
        s = str(args[0])
        if s.startswith('"') and s.endswith('"'):
            return s[1:-1]
        return s
    
    def print_stmt(self, args):
        val = self.transform(args[0])
        print(f"PRINT: {val}")
        return val
    
    def var_assign(self, args):
        name = str(args[0])
        value = self.transform(args[1])
        return self.set_var(name, value)
    
    def block(self, args):
        return args
    
    def start(self, args):
        result = None
        for stmt in args:
            result = self.transform(stmt)
        return result

# Test code with a simple function that uses parameters
test_code = """
func add(a, b) {
    let result = a + b
    print(result)
    return result
}

add(5, 7)
"""

def run_test():
    """Run a focused test on function parameter handling"""
    print("=== Testing Function Parameter Handling ===")
    
    # Get the grammar
    grammar_path = Path(__file__).parent.parent / 'sona' / 'grammar.lark'
    with open(grammar_path, 'r') as f:
        grammar = f.read()
    
    # Parse the test code
    parser = Lark(grammar, parser='lalr', propagate_positions=True)
    tree = parser.parse(test_code)
    
    print("\nParse tree structure:")
    print(tree.pretty())
    
    # Transform the tree
    print("\nRunning transformation:")
    transformer = SimpleDebugTransformer()
    result = transformer.transform(tree)
    
    print("\nFinal result:", result)
    
if __name__ == "__main__":
    run_test()
