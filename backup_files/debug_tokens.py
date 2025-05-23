#!/usr/bin/env python3

import sys
import os
import importlib
from pathlib import Path
from lark import Lark, Transformer, Tree, Token

class DebugTransformer(Transformer):
    def import_stmt(self, args):
        print(f"IMPORT STATEMENT DEBUG")
        print(f"Args raw: {args}")
        print(f"Args length: {len(args)}")
        
        # Print each token with its type and value
        for i, arg in enumerate(args):
            if arg is None:
                print(f"  {i}: None")
            else:
                print(f"  {i}: {type(arg)} - {arg} - {repr(arg)}")
                
        # Process the tokens
        alias = None
        module_parts = []
        
        i = 0
        while i < len(args):
            if args[i] is None:
                i += 1
                continue
                
            current = str(args[i])
            if current == "as" and i + 1 < len(args):
                # Found the "as" keyword, the next token is the alias
                alias = str(args[i + 1])
                i += 2  # Skip both the "as" keyword and the alias
            else:
                module_parts.append(current)
                i += 1
        
        module_name = ".".join(module_parts)
        print(f"Module name: {module_name}")
        print(f"Alias: {alias}")
        
        return args

    def start(self, args):
        return args

def main():
    grammar = r'''
    start: import_stmt
    import_stmt: "import" NAME ("." NAME)* ["as" NAME] -> import_stmt
    %import common.CNAME -> NAME
    %import common.WS
    %ignore WS
    '''
    
    parser = Lark(grammar, parser="lalr")
    transformer = DebugTransformer()
    
    test_statements = [
        "import utils.math.smod",
        "import utils.math.smod as math",
        "import stdlib.math",
        "import stdlib.math as m",
    ]
    
    for stmt in test_statements:
        print(f"\n=== Testing: {stmt} ===")
        tree = parser.parse(stmt)
        print(f"Parse Tree:\n{tree.pretty()}")
        transformer.transform(tree)

if __name__ == "__main__":
    main()
