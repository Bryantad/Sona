#!/usr/bin/env python3
# Debug script for Sona imports
import sys
import os
from pathlib import Path
from lark import Lark, Transformer, Tree, Token

class TestTransformer(Transformer):
    def import_stmt(self, args):
        print(f"Raw args: {args}")
        
        # Check if the last argument is an alias (after 'as' keyword)
        alias = None
        module_args = args.copy()
        if len(module_args) >= 2 and str(module_args[-2]) == "as":
            alias = str(module_args[-1])
            # Remove 'as' and alias name from args for module name construction
            module_args = module_args[:-2]
        
        module_name = ".".join(str(a) for a in module_args)
        print(f"Import module: {module_name}")
        if alias:
            print(f"Using alias: {alias}")
            
        return args

    def start(self, args):
        return args

def main():
    # Define a simple grammar just for imports
    grammar = r'''
    start: import_stmt
    import_stmt: "import" NAME ("." NAME)* ["as" NAME] -> import_stmt
    %import common.CNAME -> NAME
    %import common.WS
    %ignore WS
    '''
    
    parser = Lark(grammar, parser="lalr")
    transformer = TestTransformer()
    
    # Test import statements
    tests = [
        "import utils.math.smod",
        "import utils.math.smod as math",
        "import math",
        "import utils.array.smod as arr"
    ]
    
    for test in tests:
        print(f"\nTesting: {test}")
        tree = parser.parse(test)
        print(f"Tree: {tree.pretty()}")
        result = transformer.transform(tree)
        print(f"Result: {result}")
        
if __name__ == "__main__":
    main()
