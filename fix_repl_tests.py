#!/usr/bin/env python3
"""
Focused fix for Sona function parameter handling, targeting the REPL tests.
This fix addresses the core issue with evaluating parameters in function bodies.
"""

import sys
from pathlib import Path
from pathlib import Path

def apply_fix():
    """Apply a focused fix for function parameter issues"""
    print("=== Applying Function Parameter Fix ===")
    
    # Find the interpreter file
    interpreter_path = Path("sona/interpreter.py")
    if not interpreter_path.exists():
        print(f"ERROR: Could not find {interpreter_path}")
        return False
    
    # Create backup
    backup_path = Path("sona/interpreter.bak.py")
    with open(interpreter_path, 'r') as src:
        with open(backup_path, 'w') as dst:
            dst.write(src.read())
    print(f"Created backup at {backup_path}")
    
    # Fix the Transformer implementation
    with open(interpreter_path, 'r') as f:
        _ = f.readlines()  # Read but not used directly
    
    # New implementations for key methods
    transformer_fix = """
# Override Transformer methods to fix function parameter issues
from lark.visitors import Transformer_InPlace

class SonaTransformer(Transformer_InPlace):
    \"""Custom transformer that properly handles function parameters\"""
    
    def __init__(self, interpreter):
        super().__init__()
        self.interpreter = interpreter
        
    def transform(self, tree):
        \"""Override transform to correctly handle function bodies\"""
        if isinstance(tree, Tree):
            # Special handling for func_def
            if tree.data == 'func_def':
                return self._handle_func_def(tree)
            # Special handling for var in function context
            elif tree.data == 'var' and hasattr(self, '_in_function_body') and self._in_function_body:
                return self._handle_var_in_function(tree)
        
        # Default behavior
        return super().transform(tree)
    
    def _handle_func_def(self, tree):
        \"""Handle function definition without evaluating its body\"""
        # Get the function name (can safely transform)
        name = self.interpreter.transform(tree.children[0])
        
        # Extract parameters (no transformation needed)
        params = []
        if len(tree.children) > 2:
            param_list = tree.children[1]
            if hasattr(param_list, 'children'):
                params = param_list.children
            elif isinstance(param_list, list):
                params = param_list
        
        # Extract body (don't transform it yet)
        body = tree.children[-1]
        
        # Store the function definition
        self.interpreter.functions[str(name)] = (params, body)
        return name
    
    def _handle_var_in_function(self, tree):
        \"""Handle variable references in function bodies\"""
        name = str(tree.children[0])
        
        # First check current scope (where parameters should be)
        if name in self.interpreter.env[-1]:
            return self.interpreter.env[-1][name]
        
        # Then check outer scopes
        for scope in reversed(self.interpreter.env[:-1]):
            if name in scope:
                return scope[name]
                
        # Finally check modules
        if name in self.interpreter.modules:
            return self.interpreter.modules[name]
            
        # Not found
        raise NameError(f"Variable '{name}' not found")

# Patch SonaInterpreter to use our custom transformer
original_transform = SonaInterpreter.transform

def patched_transform(self, tree):
    \"""Patched transform method that uses our custom transformer for function bodies\"""
    # For function calls, we need special handling
    if isinstance(tree, Tree) and tree.data == 'func_call':
        return self._handle_func_call(tree)
    
    # Use original transform for everything else
    return original_transform(self, tree)

def _handle_func_call(self, tree):
    \"""Handle function call with proper parameter scoping\"""
    # Get function name
    name_node = tree.children[0]
    func_name = str(name_node)
    
    # Get arguments
    args = []
    if len(tree.children) > 1 and hasattr(tree.children[1], 'data') and tree.children[1].data == 'args':
        args = [self.eval_arg(arg) for arg in tree.children[1].children]
    
    # Handle modules or built-in functions
    if isinstance(name_node, Tree) and name_node.data == 'dotted_name':
        # Process dotted name as before...
        name_parts = [str(t) for t in name_node.children]
        obj_name, method_name = name_parts[0], name_parts[-1]
        
        try:
            obj = self.get_var(obj_name)
        except NameError:
            raise NameError(f"Module or variable '{obj_name}' not found")
            
        # Traverse the path
        current = obj
        for part in name_parts[1:-1]:
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict) and part in current:
                current = current[part]
            else:
                raise AttributeError(f"Cannot access '{part}' in '{obj_name}'")
        
        # Get the method
        method = None
        if hasattr(current, method_name):
            method = getattr(current, method_name)
        elif isinstance(current, dict) and method_name in current:
            method = current[method_name]
            
        if method is None:
            raise AttributeError(f"'{obj_name}' has no method '{method_name}'")
        if not callable(method):
            raise TypeError(f"'{method_name}' is not callable")
            
        return method(*args)
    
    # Regular function call
    if func_name not in self.functions:
        raise NameError(f"Function '{func_name}' not defined")
        
    params, body = self.functions[func_name]
    
    # Check parameter count
    if len(params) != len(args):
        raise ValueError(f"Function '{func_name}' expects {len(params)} arguments, got {len(args)}")
        
    # Create new scope and set parameters
    self.push_scope()
    for param, value in zip(params, args):
        param_name = str(param)
        self.env[-1][param_name] = value
    
    # Execute function body with our custom transformer
    try:
        transformer = SonaTransformer(self)
        transformer._in_function_body = True
        
        result = None
        for stmt in body.children:
            try:
                result = transformer.transform(stmt)
            except ReturnSignal as r:
                result = r.value
                break
        
        return result
    finally:
        self.pop_scope()

# Apply the patches
SonaInterpreter.transform = patched_transform
SonaInterpreter._handle_func_call = _handle_func_call
"""
    
    # Add the transformer fix to the file
    with open(interpreter_path, 'r') as f:
        code = f.read()
    
    # Find the ReturnSignal class definition
    insert_point = code.find("class ReturnSignal(Exception):")
    if insert_point == -1:
        print("ERROR: Could not find insertion point")
        return False
    
    # Find the end of the ReturnSignal class
    end_point = code.find("\n\n", insert_point)
    if end_point == -1:
        print("ERROR: Could not determine end of ReturnSignal class")
        return False
    
    # Insert our transformer fix after ReturnSignal
    fixed_code = code[:end_point+2] + transformer_fix + code[end_point+2:]
    
    # Write the fixed code
    with open(interpreter_path, 'w') as f:
        f.write(fixed_code)
    
    print("✅ Function parameter fix applied")
    return True

def run_repl_tests():
    """Run the REPL tests to verify the fix"""
    print("\n=== Running REPL Tests ===")
    
    try:
        import subprocess
        cmd = [sys.executable, "-c", 
               "from sona.repl import run_tests; run_tests()"]
               
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    if apply_fix():
        run_repl_tests()
