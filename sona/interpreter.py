"""
Sona Unified Interpreter v0.8.0

This interpreter supports both traditional programming syntax and 
the cognitive accessibility syntax documented in the Sona wiki.
"""

import importlib
import os
import sys
import time
from typing import Dict, Any, List, Optional, Union, Callable
from lark import Transformer, Tree, Token, Lark
from pathlib import Path

# Add debug support
def debug(msg):
    """Print debug messages when DEBUG environment variable is set"""
    if os.environ.get("DEBUG", "0") == "1":
        print(f"DEBUG: {msg}")

class ReturnSignal(Exception):
    """Signal to handle return statements"""
    def __init__(self, value=None):
        self.value = value
        super().__init__(value)

class BreakSignal(Exception):
    """Signal to handle break statements"""
    pass

class ContinueSignal(Exception):
    """Signal to handle continue statements"""
    pass

class SonaUnifiedInterpreter(Transformer):
    """Unified interpreter supporting both syntax styles"""
    
    def __init__(self):
        """Initialize the interpreter"""
        super().__init__()
        self.variables = {}
        self.functions = {}
        self.classes = {}
        self.call_stack = []
        
    def execute(self, code_str):
        """Execute Sona code"""
        try:
            # Load the unified grammar
            grammar_path = Path(__file__).parent / "unified_grammar.lark"
            with open(grammar_path, 'r') as f:
                grammar = f.read()
            
            # Create parser
            parser = Lark(grammar, start='start', parser='lalr')
            tree = parser.parse(code_str)
            
            # Transform the tree
            result = self.transform(tree)
            return result
        except Exception as e:
            print(f"Error executing code: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    # ======== Environment Management ========
    def push_environment(self):
        """Push a new environment onto the stack"""
        env_copy = self.variables.copy()
        self.call_stack.append(env_copy)
        return env_copy
    
    def pop_environment(self):
        """Pop an environment off the stack"""
        if self.call_stack:
            old_env = self.call_stack.pop()
            self.variables = old_env
            return old_env
        return {}
    
    # ======== Core Interpreter Methods ========
    def start(self, args):
        """Process the start rule (program root)"""
        result = None
        for stmt in args:
            if stmt is not None:  # Skip empty statements
                result = stmt
        return result
    
    # ======== Classic Syntax ========
    def var_assign(self, args):
        """Handle let/const assignments"""
        name, value = args
        self.variables[name] = value
        return value
    
    def print_stmt(self, args):
        """Handle print statements"""
        value = args[0] if args else ""
        print(value)
        return value
    
    def if_stmt(self, args):
        """Handle if statements"""
        condition = args[0]
        then_block = args[1]
        else_block = args[2] if len(args) > 2 else None
        
        if condition:
            for stmt in then_block:
                self.transform(stmt)
        elif else_block:
            for stmt in else_block:
                self.transform(stmt)
        return None
    
    def for_stmt(self, args):
        """Handle for loops"""
        var_name = args[0]
        iterable = args[1]
        block = args[2]
        
        # Save current value of loop variable if it exists
        old_value = self.variables.get(var_name)
        
        try:
            if isinstance(iterable, (list, tuple, str)):
                for item in iterable:
                    self.variables[var_name] = item
                    try:
                        for stmt in block:
                            self.transform(stmt)
                    except BreakSignal:
                        break
                    except ContinueSignal:
                        continue
            else:
                # Handle non-iterable values
                self.variables[var_name] = iterable
                try:
                    for stmt in block:
                        self.transform(stmt)
                except BreakSignal:
                    pass
                except ContinueSignal:
                    pass
        finally:
            # Restore old value or remove the variable
            if old_value is not None:
                self.variables[var_name] = old_value
            elif var_name in self.variables:
                del self.variables[var_name]
        
        return None
    
    def while_stmt(self, args):
        """Handle while loops"""
        condition_expr = args[0]
        block = args[1]
        
        while self.transform(condition_expr):
            try:
                for stmt in block:
                    self.transform(stmt)
            except BreakSignal:
                break
            except ContinueSignal:
                continue
        
        return None
    
    def func_def(self, args):
        """Handle function definitions"""
        name = args[0]
        params = args[1] if isinstance(args[1], list) else []
        body = args[-1]
        
        self.functions[name] = {
            'params': params,
            'body': body
        }
        
        return None
    
    def func_call(self, args):
        """Handle function calls"""
        name = args[0]
        call_args = args[1:] if len(args) > 1 else []
        
        if name in self.functions:
            func = self.functions[name]
            
            # Save current environment
            self.push_environment()
            old_vars = self.variables.copy()
            
            try:
                # Set parameters
                for i, param in enumerate(func['params']):
                    if i < len(call_args):
                        self.variables[param] = call_args[i]
                
                # Execute function body
                result = None
                try:
                    for stmt in func['body']:
                        result = self.transform(stmt)
                except ReturnSignal as ret:
                    return ret.value
                
                return result
            finally:
                # Restore environment
                self.variables = old_vars
                self.pop_environment()
        else:
            # Try built-in functions
            if name == "len":
                if call_args and len(call_args) == 1:
                    return len(call_args[0])
                return 0
            
            raise NameError(f"Function '{name}' not defined")
    
    def return_stmt(self, args):
        """Handle return statements"""
        value = args[0] if args else None
        raise ReturnSignal(value)
    
    def break_stmt(self, args):
        """Handle break statements"""
        raise BreakSignal()
    
    def continue_stmt(self, args):
        """Handle continue statements"""
        raise ContinueSignal()
    
    # ======== Cognitive Accessibility Syntax ========
    def bare_assign(self, args):
        """Handle bare assignments (without let/const)"""
        name = args[0]
        value = args[1]
        self.variables[name] = value
        return value
    
    def think_stmt(self, args):
        """Handle think statements - cognitive comments"""
        # These are for cognitive support, not output in normal mode
        return None
    
    def show_stmt(self, args):
        """Handle show statements - cognitive output"""
        value = args[0]
        print(value)
        return value
    
    def calculate_assign(self, args):
        """Handle calculate statements - cognitive assignments"""
        name = args[0]
        value = args[1]
        self.variables[name] = value
        return value
    
    def when_stmt(self, args):
        """Handle when statements - cognitive conditionals"""
        condition = args[0]
        then_block = args[1]
        else_block = args[2] if len(args) > 2 else None
        
        if condition:
            for stmt in then_block:
                self.transform(stmt)
        elif else_block:
            for stmt in else_block:
                self.transform(stmt)
        return None
    
    def repeat_times(self, args):
        """Handle repeat N times loops"""
        times = args[0]
        block = args[1]
        
        for i in range(int(times)):
            try:
                for stmt in block:
                    self.transform(stmt)
            except BreakSignal:
                break
            except ContinueSignal:
                continue
        
        return None
    
    def repeat_for_each(self, args):
        """Handle repeat for each item in list loops"""
        var_name = args[0]
        iterable = args[1]
        block = args[2]
        
        # Save current value of loop variable if it exists
        old_value = self.variables.get(var_name)
        
        try:
            if isinstance(iterable, (list, tuple, str)):
                for item in iterable:
                    self.variables[var_name] = item
                    try:
                        for stmt in block:
                            self.transform(stmt)
                    except BreakSignal:
                        break
                    except ContinueSignal:
                        continue
            else:
                # Handle non-iterable values
                self.variables[var_name] = iterable
                try:
                    for stmt in block:
                        self.transform(stmt)
                except BreakSignal:
                    pass
                except ContinueSignal:
                    pass
        finally:
            # Restore old value or remove the variable
            if old_value is not None:
                self.variables[var_name] = old_value
            elif var_name in self.variables:
                del self.variables[var_name]
        
        return None
    
    def repeat_for_range(self, args):
        """Handle repeat for i from start to end loops"""
        var_name = args[0]
        start = args[1]
        end = args[2]
        step = args[3] if len(args) > 3 and not isinstance(args[3], list) else 1
        block = args[-1]
        
        # Save current value of loop variable if it exists
        old_value = self.variables.get(var_name)
        
        try:
            start_val = int(start)
            end_val = int(end)
            step_val = int(step)
            
            # Handle step direction
            if start_val <= end_val:
                # Counting up
                i = start_val
                while i <= end_val:
                    self.variables[var_name] = i
                    try:
                        for stmt in block:
                            self.transform(stmt)
                    except BreakSignal:
                        break
                    except ContinueSignal:
                        pass
                    i += step_val
            else:
                # Counting down
                if step_val > 0:
                    step_val = -step_val
                i = start_val
                while i >= end_val:
                    self.variables[var_name] = i
                    try:
                        for stmt in block:
                            self.transform(stmt)
                    except BreakSignal:
                        break
                    except ContinueSignal:
                        pass
                    i += step_val
        finally:
            # Restore old value or remove the variable
            if old_value is not None:
                self.variables[var_name] = old_value
            elif var_name in self.variables:
                del self.variables[var_name]
        
        return None
    
    def repeat_for_range_step(self, args):
        """Handle repeat for i from start to end step N loops"""
        var_name = args[0]
        start = args[1]
        end = args[2]
        step = args[3]
        block = args[4]
        
        # Save current value of loop variable if it exists
        old_value = self.variables.get(var_name)
        
        try:
            start_val = int(start)
            end_val = int(end)
            step_val = int(step)
            
            # Handle step direction
            if step_val > 0:
                # Counting up
                i = start_val
                while i <= end_val:
                    self.variables[var_name] = i
                    try:
                        for stmt in block:
                            self.transform(stmt)
                    except BreakSignal:
                        break
                    except ContinueSignal:
                        pass
                    i += step_val
            else:
                # Counting down
                i = start_val
                while i >= end_val:
                    self.variables[var_name] = i
                    try:
                        for stmt in block:
                            self.transform(stmt)
                    except BreakSignal:
                        break
                    except ContinueSignal:
                        pass
                    i += step_val
                    
        finally:
            # Restore old value or remove the variable
            if old_value is not None:
                self.variables[var_name] = old_value
            elif var_name in self.variables:
                del self.variables[var_name]
        
        return None
    
    def destructure_assign(self, args):
        """Handle destructuring assignment like [a, b] = [1, 2]"""
        names = args[:-1]  # All but the last argument are variable names
        value = args[-1]   # Last argument is the value
        
        if isinstance(value, (list, tuple)):
            # Assign each element to corresponding variable
            for i, name in enumerate(names):
                if i < len(value):
                    self.variables[name] = value[i]
                else:
                    self.variables[name] = None
        else:
            # If not iterable, assign the value to the first variable
            if names:
                self.variables[names[0]] = value
                # Set other variables to None
                for name in names[1:]:
                    self.variables[name] = None
        
        return value

    # ======== Expression Evaluation ========
    def add(self, args):
        """Addition operator"""
        left, right = args
        # Handle string concatenation
        if isinstance(left, str) or isinstance(right, str):
            return str(left) + str(right)
        return left + right
    
    def sub(self, args):
        """Subtraction operator"""
        left, right = args
        return left - right
    
    def mul(self, args):
        """Multiplication operator"""
        left, right = args
        return left * right
    
    def div(self, args):
        """Division operator"""
        left, right = args
        if right == 0:
            raise ZeroDivisionError("Division by zero")
        return left / right
    
    def mod(self, args):
        """Modulo operator"""
        left, right = args
        return left % right
    
    def neg(self, args):
        """Unary negation"""
        return -args[0]
    
    def not_op(self, args):
        """Logical NOT operator"""
        return not args[0]
    
    def eq(self, args):
        """Equality operator"""
        left, right = args
        return left == right
    
    def neq(self, args):
        """Inequality operator"""
        left, right = args
        return left != right
    
    def gt(self, args):
        """Greater than operator"""
        left, right = args
        return left > right
    
    def lt(self, args):
        """Less than operator"""
        left, right = args
        return left < right
    
    def gte(self, args):
        """Greater than or equal operator"""
        left, right = args
        return left >= right
    
    def lte(self, args):
        """Less than or equal operator"""
        left, right = args
        return left <= right
    
    def and_op(self, args):
        """Logical AND operator"""
        left, right = args
        return bool(left and right)
    
    def or_op(self, args):
        """Logical OR operator"""
        left, right = args
        return bool(left or right)
    
    # ======== Values ========
    def number(self, args):
        """Handle number literals"""
        value = args[0]
        if '.' in value:
            return float(value)
        return int(value)
    
    def string(self, args):
        """Handle string literals"""
        value = args[0]
        # Remove quotes
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        if value.startswith("'") and value.endswith("'"):
            return value[1:-1]
        return value
    
    def true_val(self, args):
        """Handle true literal"""
        return True
    
    def false_val(self, args):
        """Handle false literal"""
        return False
    
    def var(self, args):
        """Handle variable references"""
        name = args[0]
        if name in self.variables:
            return self.variables[name]
        raise NameError(f"Undefined variable: {name}")
    
    def array(self, args):
        """Handle array literals"""
        return list(args)
    
    def dict(self, args):
        """Handle dictionary literals"""
        result = {}
        for i in range(0, len(args), 2):
            key = args[i]
            if i+1 < len(args):
                value = args[i+1]
                result[key] = value
        return result
    
    def property_access(self, args):
        """Handle property access"""
        obj, prop = args
        if isinstance(obj, dict):
            return obj.get(prop, None)
        else:
            return getattr(obj, prop, None)
    
    def index_access(self, args):
        """Handle index access for arrays and dicts"""
        obj, idx = args
        try:
            return obj[idx]
        except (IndexError, KeyError, TypeError):
            return None


# Create CLI function
def main():
    """CLI entry point for Sona interpreter"""
    interpreter = SonaUnifiedInterpreter()
    
    if len(sys.argv) > 1:
        # Run a file
        file_path = sys.argv[1]
        try:
            with open(file_path, 'r') as f:
                code = f.read()
            interpreter.execute(code)
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        # Interactive mode
        print("Sona 0.8.0 Interactive Mode (Ctrl+D to exit)")
        while True:
            try:
                line = input(">> ")
                result = interpreter.execute(line)
                if result is not None:
                    print(result)
            except EOFError:
                break
            except KeyboardInterrupt:
                print("\nKeyboardInterrupt")
                continue
            except Exception as e:
                print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
