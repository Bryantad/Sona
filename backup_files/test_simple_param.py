#!/usr/bin/env python3
# filepath: /Volumes/project usb/WayCore Inc/sona_core/test_simple_param.py

"""
Test function parameter handling using the simplified interpreter approach.
"""

import os
import sys
from pathlib import Path

# Make sure SONA_DEBUG is set
os.environ["SONA_DEBUG"] = "1"

# Simple function for testing (inlined to avoid imports)
def run_param_test():
    from lark import Lark, Transformer, Tree, Token, UnexpectedInput
    
    # Create a minimal interpreter based on the original but with parameter fixes
    class ReturnSignal(Exception):
        def __init__(self, value):
            self.value = value
    
    class MinimalInterpreter(Transformer):
        def __init__(self):
            super().__init__()
            self.env = [{}]  # Stack of scopes
            self.functions = {}
            
        def push_scope(self):
            self.env.append({})
            print(f"[DEBUG] Pushed new scope, now have {len(self.env)} scopes")
            
        def pop_scope(self):
            old_scope = self.env.pop()
            print(f"[DEBUG] Popped scope {old_scope}, now have {len(self.env)} scopes")
            
        def set_var(self, name, value):
            self.env[-1][name] = value
            print(f"[DEBUG] Set variable '{name}' = {value} in scope {len(self.env)-1}")
            
        def get_var(self, name):
            print(f"[DEBUG] Looking for '{name}' in scopes: {[list(scope.keys()) for scope in self.env]}")
            for scope in reversed(self.env):
                if name in scope:
                    print(f"[DEBUG] Found '{name}' = {scope[name]}")
                    return scope[name]
            raise NameError(f"Variable '{name}' not found")
            
        def var(self, args):
            name = str(args[0])
            print(f"[DEBUG] var() called for '{name}'")
            return self.get_var(name)
            
        def string(self, args):
            value = str(args[0])[1:-1]  # Remove quotes
            print(f"[DEBUG] string() -> '{value}'")
            return value
            
        def add(self, args):
            return self.transform(args[0]) + self.transform(args[1])
            
        def print_stmt(self, args):
            value = self.transform(args[0])
            print(f"OUTPUT: {value}")
            return None
            
        def func_def(self, args):
            name = str(args[0])
            param_list = args[1]
            body = args[2]
            
            # Extract parameter names from param_list
            params = []
            if param_list is not None:
                if isinstance(param_list, list):
                    params = [p for p in param_list if p is not None and not str(p).startswith(',')]
                else:
                    params = [param_list]
            
            print(f"[DEBUG] Defined function '{name}' with params: {[str(p) for p in params]}")
            self.functions[name] = (params, body)
            return None
            
        def func_call(self, args):
            name = str(args[0])
            # Get the arguments
            passed_args = []
            if len(args) > 1:
                passed_args = [self.transform(arg) for arg in args[1:]]
            
            print(f"[DEBUG] Calling function '{name}' with args: {passed_args}")
            
            # Look up the function
            if name not in self.functions:
                raise NameError(f"Function '{name}' not defined")
                
            params, body = self.functions[name]
            
            # Create new scope for function execution
            self.push_scope()
            
            # Set parameters in the new scope
            for i, (param, value) in enumerate(zip(params, passed_args)):
                param_name = str(param)
                print(f"[DEBUG] Setting parameter {i}: {param_name} = {value}")
                self.set_var(param_name, value)
                
            # Execute function body
            result = None
            try:
                for stmt in body:
                    result = self.transform(stmt)
            except ReturnSignal as r:
                result = r.value
                
            # Clean up scope
            print(f"[DEBUG] Function '{name}' completed with result: {result}")
            self.pop_scope()
            return result
            
        def return_stmt(self, args):
            if args:
                value = self.transform(args[0])
                print(f"[DEBUG] return statement with value: {value}")
                raise ReturnSignal(value)
            else:
                print(f"[DEBUG] return statement with no value")
                raise ReturnSignal(None)
                
        def start(self, args):
            for stmt in args:
                self.transform(stmt)
            return None
    
    # Use a simplified grammar for testing
    grammar = r'''
        start: statement*
        statement: func_def | func_call | print_stmt
        func_def: "func" NAME "(" [param_list] ")" "{" statement* "}"
        param_list: NAME ("," NAME)*
        func_call: NAME "(" [args] ")"
        args: expr ("," expr)*
        print_stmt: "print" "(" expr ")"
        return_stmt: "return" expr
        expr: string | func_call | var | add
        add: expr "+" expr
        string: ESCAPED_STRING
        var: NAME
        
        NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
        ESCAPED_STRING: /"[^"]*"/
        
        %import common.WS
        %ignore WS
        %ignore /\/\/[^\n]*/  // Line comments
    '''
    
    # Test code
    test_code = '''
    func test_param(x) {
        print("Parameter x = " + x)
        return x
    }
    
    print("Calling test_param with argument 'hello'")
    print("Result: " + test_param("hello"))
    '''
    
    # Parse and execute
    parser = Lark(grammar, start='start', parser='lalr')
    tree = parser.parse(test_code)
    print("[DEBUG] Parsed tree:", tree.pretty())
    
    interpreter = MinimalInterpreter()
    interpreter.transform(tree)

if __name__ == "__main__":
    run_param_test()
