import importlib.util
import importlib
import os
import math 
from lark import Lark, Transformer, Tree, Token
from pathlib import Path

# Native module imports
from sona.stdlib import (
    env as env_module,
    time as time_module,
)

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class SonaInterpreter(Transformer):
    def __init__(self):
        super().__init__()
        self.env = [{}]
        self.functions = {}
        self.modules = {}

        # Register native modules
        self.modules["native_stdin"] = native_stdin # type: ignore
        self.modules["env"] = {
            "get": env_module.get,
            "set": env_module.set,
        }
        self.modules["time"] = {
            "now": time_module.now,
            "sleep": time_module.sleep,
        }

    def eval_arg(self, arg):
        return self._eval(arg) if isinstance(arg, Tree) else arg
        
    def array(self, args):
        """Handle array literals like [1, 2, 3]"""
        if not args:
            return []
        if hasattr(args[0], 'children'):
            return [self.eval_arg(item) for item in args[0].children]
        return [self.eval_arg(item) for item in args]
    
    def array_literal(self, args):
        """Handle array literal syntax"""
        return args
    
    def array_items(self, args):
        """Process array items"""
        return args
    
    def push_scope(self):
        self.env.append({})

    def pop_scope(self):
        self.env.pop()

    def set_var(self, name, value):
        self.env[-1][name] = value

    def get_var(self, name):
        for scope in reversed(self.env):
            if name in scope:
                return scope[name]
        raise NameError(f"Variable '{name}' not found")

    def var(self, args):
        # Handle dotted_name: join tokens with '.'
        if isinstance(args[0], Tree) and args[0].data == "dotted_name":
            names = [str(t.value) for t in args[0].children]
            name = ".".join(names)
        else:
            name = str(args[0])
        return self.get_var(name)

    def _eval(self, node):
        return self.transform(node)

    def _exec(self, node):
        if isinstance(node, Tree):
            self.transform(node)
        elif isinstance(node, list):
            for n in node:
                self._exec(n)
