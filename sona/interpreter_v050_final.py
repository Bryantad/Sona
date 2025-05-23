import importlib.util
import importlib
import os
from lark import Lark, Transformer, Tree, Token
from pathlib import Path
from sona.utils.debug import debug, error

# Native module imports
from sona.stdlib import (
    env as env_module,
    time as time_module,
)

from sona.stdlib.native_stdin import native_stdin

debug_mode = False

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class SonaInterpreter(Transformer):
    def __init__(self):
        super().__init__()
        self.env = [{}]  # Stack of scopes, innermost scope at end
        self.functions = {}
        self.modules = {}

        # Register native modules
        self.modules["native_stdin"] = native_stdin
        self.modules["env"] = {
            "get": env_module.get,
            "set": env_module.set,
        }
        self.modules["time"] = {
            "now": time_module.now,
            "sleep": time_module.sleep,
        }

        # Preload commonly used modules
        try:
            from sona.stdlib.utils.array.smod import array
            self.modules["array"] = array
            debug(f"array module loaded")
        except ImportError:
            debug("Could not preload array module")

    def push_scope(self):
        """Push a new scope onto the scope stack"""
        debug(f"Pushing new scope (now at depth {len(self.env)+1})")
        self.env.append({})
        return self.env[-1]

    def pop_scope(self):
        """Pop the innermost scope from the stack"""
        if len(self.env) > 1:  # Always keep global scope
            debug(f"Popping scope (now at depth {len(self.env)-1})")
            return self.env.pop()
        debug("Cannot pop global scope")
        return None

    def get_current_scope(self):
        """Get the current (innermost) scope"""
        return self.env[-1]

    def set_var(self, name, value):
        """Set a variable in the current scope"""
        debug(f"Setting variable {name} = {value} in scope {len(self.env)-1}")
        self.env[-1][name] = value
        return value

    def find_var_scope(self, name):
        """Find which scope contains a variable, or None if not found"""
        # First check modules
        if name in self.modules:
            return self.modules

        # Then check scopes from most local to most global
        for scope in reversed(self.env):
            if name in scope:
                return scope
        return None

    def get_var(self, name):
        """Get a variable's value, checking all scopes"""
        # First check modules
        if name in self.modules:
            debug(f"Found module: {name}")
            return self.modules[name]

        # Then check scopes from most local to most global
        for i, scope in enumerate(reversed(self.env)):
            if name in scope:
                depth = len(self.env) - i - 1
                debug(f"Found variable {name} in scope {depth}")
                return scope[name]

        # Variable not found
        debug(f"Variable {name} not found in any scope")
        raise NameError(f"Variable '{name}' not found")

    def var(self, args):
        """Handle variable references"""
        if isinstance(args[0], Token):
            name = str(args[0])
            try:
                return self.get_var(name)
            except NameError:
                # Add line and column information to the error message
                raise Exception(f"VARIABLE ERROR: Variable '{name}' not found at line {args[0].line}, column {args[0].column}")
        return None

    def var_assign(self, args):
        """Handle let/const variable assignment"""
        if len(args) != 2:
            raise Exception("Invalid assignment")
        name = str(args[0])
        value = self.eval_arg(args[1])
        return self.set_var(name, value)

    def assign(self, args):
        """Handle normal variable assignment (without let/const)"""
        if len(args) != 2:
            raise Exception("Invalid assignment")
        name = str(args[0])
        value = self.eval_arg(args[1])
        scope = self.find_var_scope(name)
        if scope is None:
            raise Exception(f"Cannot assign to undeclared variable '{name}'")
        scope[name] = value
        return value

    def add(self, args): 
        return self.eval_arg(args[0]) + self.eval_arg(args[1])
        
    def sub(self, args): 
        return self.eval_arg(args[0]) - self.eval_arg(args[1])
        
    def mul(self, args): 
        return self.eval_arg(args[0]) * self.eval_arg(args[1])
        
    def div(self, args): 
        return self.eval_arg(args[0]) / self.eval_arg(args[1])

    def eq(self, args):
        return int(self.eval_arg(args[0]) == self.eval_arg(args[1]))
        
    def neq(self, args):
        return int(self.eval_arg(args[0]) != self.eval_arg(args[1]))
        
    def gt(self, args):
        return int(self.eval_arg(args[0]) > self.eval_arg(args[1]))
        
    def lt(self, args):
        return int(self.eval_arg(args[0]) < self.eval_arg(args[1]))
        
    def gte(self, args):
        return int(self.eval_arg(args[0]) >= self.eval_arg(args[1]))
        
    def lte(self, args):
        return int(self.eval_arg(args[0]) <= self.eval_arg(args[1]))
        
    def and_(self, args):
        return int(bool(self.eval_arg(args[0])) and bool(self.eval_arg(args[1])))
        
    def or_(self, args):
        return int(bool(self.eval_arg(args[0])) or bool(self.eval_arg(args[1])))

    def number(self, args):
        return float(args[0])

    def string(self, args):
        raw_str = str(args[0])
        
        # Handle triple-quoted strings (multi-line)
        if (raw_str.startswith('"""') and raw_str.endswith('"""')) or \
           (raw_str.startswith("'''") and raw_str.endswith("'''")):
            # Extract content between triple quotes
            return raw_str[3:-3]
        
        # Handle regular strings (single-line)
        if (raw_str.startswith('"') and raw_str.endswith('"')) or \
           (raw_str.startswith("'") and raw_str.endswith("'")):
            # Extract content between quotes
            return raw_str[1:-1]
        
        # Invalid string format
        raise Exception(f"Invalid string format: {raw_str}")

    def print_stmt(self, args):
        val = self.eval_arg(args[0])
        print(val)
        return val

    def if_stmt(self, args):
        condition = self.eval_arg(args[0])
        
        if condition:
            # Execute the "then" block
            debug("If condition is true, executing then block")
            self.push_scope()
            try:
                result = self._exec(args[1].children)
            finally:
                self.pop_scope()
            return result
        elif len(args) > 2:  # Has an "else" block
            # Execute the "else" block
            debug("If condition is false, executing else block")
            self.push_scope()
            try:
                result = self._exec(args[2].children)
            finally:
                self.pop_scope()
            return result
            
        return None

    def while_stmt(self, args):
        condition_expr, body = args
        result = None
        
        while self.eval_arg(condition_expr):
            self.push_scope()
            try:
                result = self._exec(body.children)
            except ReturnSignal:
                # If a return statement is encountered, propagate it
                self.pop_scope()
                raise
            finally:
                self.pop_scope()
        
        return result

    def for_stmt(self, args):
        var_name, start_expr, end_expr, body = args
        
        start = self.eval_arg(start_expr)
        end = self.eval_arg(end_expr)
        result = None
        
        for i in range(int(start), int(end) + 1):
            loop_scope = self.push_scope()
            # Set the loop variable in the new scope
            loop_scope[str(var_name)] = i
            
            try:
                result = self._exec(body.children)
            except ReturnSignal:
                # If a return statement is encountered, propagate it
                self.pop_scope()
                raise
            finally:
                self.pop_scope()
                
        return result

    def param_list(self, args):
        """Process function parameter list"""
        debug(f"Processing parameter list with {len(args)} parameters")
        return args  # Return the parameter tokens directly

    def func_def(self, args):
        """Process function definition without evaluating its body"""
        debug(f"Function definition with {len(args)} arguments")
        
        # Extract function name and body
        name = args[0]
        func_name = str(name)
        
        # Extract parameters list (could be None)
        param_list = None
        if len(args) > 1 and args[1] is not None:
            # We have parameters
            param_list = args[1]
        
        # Extract body (last argument)
        body = args[-1]
        
        # Process parameter tokens
        params = []
        if param_list is not None:
            if isinstance(param_list, list):
                params = param_list
            elif hasattr(param_list, 'children'):
                params = param_list.children
            elif isinstance(param_list, Token) and param_list.type == 'NAME':
                params = [param_list]
        
        # Store function definition without evaluating its body
        param_names = [str(p) for p in params]
        debug(f"Defined function '{func_name}' with parameters: {param_names}")
        self.functions[func_name] = (params, body)
        
        return func_name

    def func_call(self, args):
        """Handle function calls"""
        debug(f"Function call with {len(args)} arguments")
        
        # Get function name and arguments
        name_node = args[0]
        func_name = str(name_node)
        
        # Get arguments if any
        call_args = []
        if len(args) > 1 and isinstance(args[1], Tree) and args[1].data == "args":
            call_args = [self.eval_arg(arg) for arg in args[1].children]
        
        debug(f"Calling function '{func_name}' with args: {call_args}")
        
        # Handle built-in functions or modules
        if func_name in self.modules:
            if callable(self.modules[func_name]):
                return self.modules[func_name](*call_args)
            raise TypeError(f"Module '{func_name}' is not callable")
        
        # Handle user-defined functions
        if func_name not in self.functions:
            raise NameError(f"Function '{func_name}' is not defined")
        
        # Get function definition
        params, body = self.functions[func_name]
        
        # Check parameter count
        if len(params) != len(call_args):
            raise ValueError(f"Function '{func_name}' expects {len(params)} arguments, got {len(call_args)}")
        
        # Create new scope for function execution
        debug(f"Creating new scope for function '{func_name}'")
        self.push_scope()
        
        # Set parameters in the new scope
        for param, value in zip(params, call_args):
            param_name = str(param)
            debug(f"Setting parameter '{param_name}' = {value}")
            self.env[-1][param_name] = value
        
        # Execute function body
        try:
            debug(f"Executing function '{func_name}' body")
            result = None
            
            # Custom execution for function body
            if hasattr(body, 'children'):
                for stmt in body.children:
                    debug(f"Executing statement in function '{func_name}'")
                    try:
                        result = self.transform(stmt)
                    except ReturnSignal as r:
                        debug(f"Return signal caught with value: {r.value}")
                        result = r.value
                        break
            else:
                debug(f"Function '{func_name}' has no body")
            
            debug(f"Function '{func_name}' execution complete, returning: {result}")
            return result
        finally:
            # Always pop the function scope when done
            debug(f"Popping function scope for '{func_name}'")
            self.pop_scope()

    def return_stmt(self, args):
        """Handle return statement"""
        debug(f"Processing return statement with {len(args)} args")
        if args:
            debug(f"Evaluating return value")
            value = self.eval_arg(args[0])
            debug(f"Return value: {value}")
            raise ReturnSignal(value)
        
        debug("Return with no value (None)")
        raise ReturnSignal(None)

    def block(self, args):
        return args

    def start(self, args):
        result = None
        for stmt in args:
            result = self._exec(stmt)
        return result

    def array(self, args):
        if not args:
            return []
        if isinstance(args[0], list):
            return args[0]
        if hasattr(args[0], 'children'):
            return [self.eval_arg(item) for item in args[0].children]
        return [self.eval_arg(item) for item in args]

    def array_items(self, args):
        return [self.eval_arg(item) for item in args]

    def array_literal(self, args):
        return self.array(args)

    def _eval(self, node):
        return self.transform(node)

    def _exec(self, node):
        """Execute a node or list of nodes"""
        if isinstance(node, Tree):
            return self.transform(node)
        elif isinstance(node, list):
            result = None
            for n in node:
                result = self._exec(n)
            return result
        elif isinstance(node, Token):
            # Handle token nodes directly
            return self.transform(node)
        return node

    def eval_arg(self, arg):
        if isinstance(arg, (Tree, Token)):
            try:
                return self.transform(arg)
            except Exception as e:
                if hasattr(arg, 'line') and hasattr(arg, 'column'):
                    debug(f"Error evaluating argument at line {arg.line}, column {arg.column}: {e}")
                raise
        return arg

    def transform_tree(self, tree):
        """Override transform_tree to add better error handling"""
        # Custom transformation method with better error reporting
        if not isinstance(tree, Tree):
            return tree
        
        # Get the rule handler for this tree
        handler = getattr(self, tree.data)
        children = [self.transform(child) for child in tree.children]
        
        try:
            return handler(children)
        except Exception as e:
            # Add better error context
            if not hasattr(e, 'handled'):
                debug(f"Error in rule {tree.data}: {e}")
                e.handled = True
            raise

def run_code(code, debug_enabled=False):
    global debug_mode
    debug_mode = debug_enabled
    
    try:
        interpreter = SonaInterpreter()
        grammar_path = os.path.join(os.path.dirname(__file__), 'grammar.lark')
        with open(grammar_path, 'r') as f:
            grammar = f.read()
        
        parser = Lark(grammar, parser='lalr', propagate_positions=True)
        tree = parser.parse(code)
        return interpreter.transform(tree)
    except Exception as e:
        if hasattr(e, 'line') and hasattr(e, 'column'):
            lines = code.split('\n')
            error_line = lines[e.line-1] if e.line <= len(lines) else ""
            error_msg = f"ERROR at line {e.line}, column {e.column}:\n"
            error_msg += f"{e.line}: {error_line}\n"
            error_msg += " " * (e.column + len(str(e.line)) + 2) + "^\n"
            print(error_msg)
        raise
