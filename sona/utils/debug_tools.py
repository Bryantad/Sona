"""
Sona REPL Diagnostic and Debug Tools Module

This module provides advanced developer tools for the Sona REPL, including:
- Function call tracing
- Execution profiling
- Parse tree visualization
- Variable state inspection

To use these tools within the REPL, use commands like :debug, :trace, :profile, and :watch.
"""

import time
import pprint
from lark import Tree, Token
from sona.interpreter import SonaInterpreter

# Global debug state
debug_state = {
    "last_error": None,
    "last_tree": None,
    "last_duration": None,
    "trace_enabled": False
}

def run_code_with_trace(code, interpreter=None, parser=None):
    """
    Run Sona code with function call tracing enabled.
    
    Args:
        code (str): The Sona code to execute
        interpreter (SonaInterpreter, optional): The interpreter instance
        parser (Lark parser, optional): The parser instance
        
    Returns:
        The result of the code execution
    """
    from sona.interpreter import run_code
    
    # Create a new interpreter if none was provided
    if not interpreter or not parser:
        from lark import Lark
        import os
        from pathlib import Path
        
        # Create a new interpreter instance
        from sona.interpreter import SonaInterpreter
        interpreter = SonaInterpreter()
        
        # Load parser if needed
        if not parser:
            grammar_path = os.path.join(os.path.dirname(__file__), '../grammar.lark')
            with open(grammar_path, 'r') as f:
                grammar = f.read()
            parser = Lark(grammar, parser='lalr', propagate_positions=True)
    
    # Save original function_call method to restore later
    original_func_call = interpreter.func_call
    
    # Create a tracing wrapper for func_call
    def traced_func_call(args):
        # Extract function name and arguments
        name_node = args[0]
        func_name = str(name_node)
        passed_args = []
        
        if len(args) > 1 and isinstance(args[1], Tree) and args[1].data == "args":
            passed_args = [interpreter.eval_arg(arg) for arg in args[1].children]
        
        print(f"[TRACE] Calling function '{func_name}' with args: {passed_args}")
        
        # Call the original method
        result = original_func_call(args)
        
        print(f"[TRACE] Returned from '{func_name}': {result}")
        return result
    
    try:
        # Replace with traced version
        interpreter.func_call = traced_func_call
        
        # Parse and execute
        tree = parser.parse(code)
        return interpreter.transform(tree)
    finally:
        # Restore original function
        interpreter.func_call = original_func_call

def run_with_profiling(func, *args, **kwargs):
    """
    Run a function with performance profiling.
    
    Args:
        func: The function to run
        *args: Arguments for the function
        **kwargs: Keyword arguments for the function
    
    Returns:
        tuple: (result, duration_ms)
    """
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000
    return result, duration_ms

def watch_variable(interpreter, var_name):
    """
    Find and display the value of a variable across all scopes.
    
    Args:
        interpreter (SonaInterpreter): The interpreter instance
        var_name (str): The name of the variable to watch
        
    Returns:
        tuple: (found, value, type_name, scope_idx) or None if not found
    """
    if not interpreter or not hasattr(interpreter, 'env'):
        return None
    
    # Check all scopes from most local to most global
    for scope_idx, scope in enumerate(reversed(interpreter.env)):
        depth = len(interpreter.env) - scope_idx - 1
        if var_name in scope:
            value = scope[var_name]
            return True, value, type(value).__name__, depth
    
    # Check modules
    if hasattr(interpreter, 'modules') and var_name in interpreter.modules:
        value = interpreter.modules[var_name]
        return True, value, "module", -1
    
    return False, None, None, None

def print_debug_info(interpreter, last_error=None, last_tree=None):
    """
    Print comprehensive debug information.
    
    Args:
        interpreter (SonaInterpreter): The interpreter instance
        last_error: The last error that occurred
        last_tree: The last parse tree
    """
    print("\n[DEBUG INFO]")
    print(f"Last Error: {last_error}")
    
    if last_tree:
        print("\nLast Parse Tree:")
        if hasattr(last_tree, 'pretty'):
            print(last_tree.pretty())
        else:
            print(pprint.pformat(last_tree))
    else:
        print("\nNo parse tree available.")
    
    print("\nEnv Scope:")
    if interpreter and hasattr(interpreter, 'env'):
        for scope_idx, scope in enumerate(interpreter.env):
            if scope_idx == 0:
                print("Global scope:")
            else:
                print(f"Scope {scope_idx}:")
            for name, value in scope.items():
                print(f"{name} = {value}")
    else:
        print("No environment available")
