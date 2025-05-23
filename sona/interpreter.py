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
        # Always check current scope first (for parameters)
        if isinstance(args[0], Token):
            name = str(args[0])
            if name in self.env[-1]:
                return self.env[-1][name]
            for scope in reversed(self.env[:-1]):
                if name in scope:
                    return scope[name]
            if name in self.modules:
                return self.modules[name]
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
        a = self.eval_arg(args[0])
        b = self.eval_arg(args[1])
        
        # Special handling for string concatenation
        if isinstance(a, str) or isinstance(b, str):
            # Convert both to strings for concatenation
            return str(a) + str(b)
            
        # Normal arithmetic addition
        result = a + b
        return int(result) if isinstance(result, float) and result == int(result) else result
        
    def sub(self, args): 
        a = self.eval_arg(args[0])
        b = self.eval_arg(args[1])
        result = a - b
        return int(result) if isinstance(result, float) and result == int(result) else result
        
    def mul(self, args): 
        a = self.eval_arg(args[0])
        b = self.eval_arg(args[1])
        
        # Handle string multiplication (e.g. "a" * 3)
        if isinstance(a, str) and isinstance(b, (int, float)):
            return a * int(b)
        elif isinstance(b, str) and isinstance(a, (int, float)):
            return b * int(a)
            
        # Normal arithmetic multiplication
        result = a * b
        return int(result) if isinstance(result, float) and result == int(result) else result
        
    def div(self, args): 
        a = self.eval_arg(args[0])
        b = self.eval_arg(args[1])
        result = a / b
        return int(result) if isinstance(result, float) and result == int(result) else result

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
        """Process a number literal, normalizing integers to int type"""
        value = float(args[0])
        # If the number is an integer (no decimal part), return as int
        if value.is_integer():
            return int(value)
        return value

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
            self.push_scope()
            try:
                if isinstance(args[1], Tree) and hasattr(args[1], 'children'):
                    result = None
                    for stmt in args[1].children:
                        result = self.transform(stmt)
                else:
                    result = self._exec(args[1])
                
                # Test 6 fix: Return the result as is without normalizing to int
                # This ensures floats stay as floats and integers as integers
                return result
            finally:
                self.pop_scope()
        elif len(args) > 2:
            self.push_scope()
            try:
                if isinstance(args[2], Tree) and hasattr(args[2], 'children'):
                    result = None
                    for stmt in args[2].children:
                        result = self.transform(stmt)
                else:
                    result = self._exec(args[2])
                
                # Test 6 fix: Return the result as is without normalizing to int
                return result
            finally:
                self.pop_scope()
        return None

    def while_stmt(self, args):
        condition_expr, body = args
        result = None
        
        # Debug the condition and body structure
        debug(f"While condition type: {type(condition_expr)}")
        if hasattr(condition_expr, 'data'):
            debug(f"While condition data: {condition_expr.data}")
        debug(f"While body type: {type(body)}")
        if hasattr(body, 'data'):
            debug(f"While body data: {body.data}")
        
        # First evaluate the condition - make sure it's properly evaluated
        try:
            while self.eval_arg(condition_expr):
                debug(f"Executing while loop iteration")
                self.push_scope()
                try:
                    # Handle different body types in a consistent manner
                    if isinstance(body, Tree) and hasattr(body, 'data') and body.data == 'block':
                        # Handle block with proper children iteration
                        if hasattr(body, 'children') and body.children:
                            for stmt in body.children:
                                result = self.transform(stmt)
                    elif isinstance(body, Tree):
                        # Any other tree
                        result = self.transform(body)
                    elif isinstance(body, list):
                        # List of statements
                        for stmt in body:
                            result = self.transform(stmt)
                    else:
                        # Single statement that's not a Tree
                        result = self.transform(body)
                except ReturnSignal as r:
                    result = r.value
                    self.pop_scope()
                    raise
                finally:
                    self.pop_scope()
        except Exception as e:
            debug(f"Error in while loop: {e}")
            raise
        
        # Test 7 fix: Return the result as is without normalizing to int
        return result

    def for_stmt(self, args):
        var_name, start_expr, end_expr, body = args
        start = self.eval_arg(start_expr)
        end = self.eval_arg(end_expr)
        result = None
        
        for i in range(int(start), int(end) + 1):
            self.push_scope()
            self.set_var(str(var_name), i)
            try:
                # Handle different body types
                if isinstance(body, Tree):
                    if hasattr(body, 'children') and body.children:
                        # Tree with children
                        for stmt in body.children:
                            result = self.transform(stmt)
                    else:
                        # Single statement Tree
                        result = self.transform(body)
                elif isinstance(body, list):
                    # List of statements
                    for stmt in body:
                        result = self.transform(stmt)
                else:
                    # Single statement that's not a Tree
                    result = self.transform(body)
            except ReturnSignal as r:
                result = r.value
                self.pop_scope()
                raise
            finally:
                self.pop_scope()
        
        # Normalize numeric results
        if isinstance(result, float) and result.is_integer():
            return int(result)
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
        # Extract function name and arguments
        name_node = args[0]
        passed_args = []
        if len(args) > 1 and isinstance(args[1], Tree) and args[1].data == "args":
            # Store the argument values
            passed_args = []
            for a in args[1].children:
                try:
                    val = self.eval_arg(a)
                    passed_args.append(val)
                except Exception as e:
                    if hasattr(a, 'line') and hasattr(a, 'column'):
                        line, column = a.line, a.column
                        raise type(e)(f"{str(e)} at line {line}, column {column}")
                    else:
                        raise
                        
            debug(f"Evaluated function arguments: {passed_args}")

        # Handle dotted calls (module.method)
        if isinstance(name_node, Tree) and name_node.data == "dotted_name":
            name_parts = [str(t.value) if isinstance(t, Token) else str(t) for t in name_node.children]
            obj_name, method_name = name_parts[0], name_parts[-1]
            
            # Resolve the object (could be a module or a variable)
            if obj_name in self.modules:
                obj = self.modules[obj_name]
            else:
                # Try to find it in variables
                try:
                    obj = self.get_var(obj_name)
                except NameError:
                    # Add line and column information if available
                    if hasattr(name_node.children[0], 'line') and hasattr(name_node.children[0], 'column'):
                        line, column = name_node.children[0].line, name_node.children[0].column
                        raise NameError(f"Module or variable '{obj_name}' not found at line {line}, column {column}")
                    else:
                        raise NameError(f"Module or variable '{obj_name}' not found")

            # For nested paths (e.g., pkg.submodule.func), traverse the path
            current = obj
            for part in name_parts[1:-1]:  # Skip first and last parts
                if hasattr(current, part):
                    current = getattr(current, part)
                elif isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    raise AttributeError(f"Cannot access '{part}' in '{obj_name}'")
            
            # Now try to get the actual method
            if hasattr(current, method_name):
                method = getattr(current, method_name)
                if callable(method):
                    return method(*passed_args)
                else:
                    raise TypeError(f"'{method_name}' is not callable")
            elif isinstance(current, dict) and method_name in current:
                method = current[method_name]
                if callable(method):
                    return method(*passed_args)
                else:
                    raise TypeError(f"'{method_name}' is not callable")
            else:
                # Add line and column information if available
                method_token_index = len(name_parts) - 1
                if method_token_index < len(name_node.children) and hasattr(name_node.children[method_token_index], 'line'):
                    line, column = name_node.children[method_token_index].line, name_node.children[method_token_index].column
                    raise AttributeError(f"'{obj_name}' has no method '{method_name}' at line {line}, column {column}")
                else:
                    raise AttributeError(f"'{obj_name}' has no method '{method_name}'")

        # Handle regular function calls
        name = str(name_node)
        if name not in self.functions:
            # Add line and column information if available
            if hasattr(name_node, 'line') and hasattr(name_node, 'column'):
                line, column = name_node.line, name_node.column
                raise NameError(f"Function '{name}' not defined at line {line}, column {column}")
            else:
                raise NameError(f"Function '{name}' not defined")

        params, body = self.functions[name]
        if len(params) != len(passed_args):
            # Add line and column information if available
            if hasattr(name_node, 'line') and hasattr(name_node, 'column'):
                line, column = name_node.line, name_node.column
                raise ValueError(f"Function '{name}' expects {len(params)} arguments, got {len(passed_args)} at line {line}, column {column}")
            else:
                raise ValueError(f"Function '{name}' expects {len(params)} arguments, got {len(passed_args)}")

        debug(f"Function call: About to execute '{name}' with params: {[str(p) for p in params]}")
        
        # Create a new scope for function execution
        self.push_scope()
        debug(f"Pushed new scope for function '{name}', now at level {len(self.env)}")
        
        # Add each parameter to the function scope with its value
        for i, (param, value) in enumerate(zip(params, passed_args)):
            param_name = str(param)
            debug(f"Setting function parameter {i}: {param_name} = {value}")
            self.env[-1][param_name] = value
            debug(f"Parameter '{param_name}' set to {value} in scope {len(self.env)-1}")
            
            # Verify parameter was set correctly
            if param_name not in self.env[-1]:
                debug(f"ERROR: Parameter '{param_name}' not set correctly")
        
        # Debug the function scope contents
        scope_contents = ", ".join([f"{k}={v}" for k, v in self.env[-1].items()])
        debug(f"Function '{name}' scope contents: {scope_contents}")
        debug(f"Current env stack: {len(self.env)} scopes, top scope keys: {list(self.env[-1].keys())}")

        try:
            # Execute the function body statements
            result = None
            debug(f"Starting execution of function '{name}' body")
            
            # Process function body statements
            for i, child in enumerate(body.children):
                debug(f"Executing statement {i} in function '{name}'")
                if isinstance(child, Tree) and child.data == 'return_stmt':
                    debug(f"Processing return statement")
                    # Special handling for return statements
                    try:
                        return_expr = child.children[0] if child.children else None
                        if return_expr:
                            debug(f"Evaluating return expression: {return_expr}")
                            result = self.transform(return_expr)
                            debug(f"Return value: {result}")
                        else:
                            result = None
                            debug("Return with no value")
                        break  # Exit the loop on return
                    except Exception as e:
                        debug(f"Error in return statement: {e}")
                        raise
                else:
                    # Execute other statements
                    try:
                        result = self.transform(child)
                        debug(f"Statement result: {result}")
                    except Exception as e:
                        debug(f"Error executing statement: {e}")
                        raise
            
            debug(f"Function '{name}' execution completed with result: {result}")
            self.pop_scope()
            return result
        except ReturnSignal as r:
            debug(f"Function '{name}' returned via signal with value: {r.value}")
            self.pop_scope()
            return r.value
        except Exception as e:
            error_msg = f"Error in function '{name}': {str(e)}"
            debug(error_msg)
            self.pop_scope()
            raise

    def return_stmt(self, args):
        """Handle return statement"""
        debug(f"Processing return statement with {len(args)} args")
        if args:
            debug(f"Evaluating return value")
            value = self.eval_arg(args[0])
            # Normalize numeric results
            if isinstance(value, float) and value.is_integer():
                value = int(value)
            debug(f"Return value: {value}")
            raise ReturnSignal(value)
        
        debug("Return with no value (None)")
        raise ReturnSignal(None)

    def block(self, args):
        """Handle a code block, returning the block contents safely"""
        # This helps with function bodies and control structures
        debug(f"Processing block with {len(args)} statements")
        
        # Create a Tree object with children if args is a list
        if isinstance(args, list):
            new_tree = Tree('block', args)
            return new_tree
            
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
        """Execute a node or list of nodes, robust to both Tree and list bodies"""
        if node is None:
            return None
            
        if isinstance(node, Tree):
            # Return the result directly without normalizing
            return self.transform(node)
            
        elif isinstance(node, list):
            result = None
            for n in node:
                result = self.transform(n)
            return result
            
        # If node is a block with children attribute
        elif hasattr(node, 'children'):
            result = None
            for child in node.children:
                result = self.transform(child)
            return result
            
        # Handle Token case
        elif isinstance(node, Token):
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
        """Custom transform to fix function parameter scoping and body evaluation"""
        if not isinstance(tree, Tree):
            return tree
            
        try:
            handler = getattr(self, tree.data)
        except AttributeError:
            debug(f"No handler found for tree data type: {tree.data}")
            return tree
            
        # Special handling for function definition: don't evaluate body
        if tree.data == 'func_def':
            name = self.transform(tree.children[0])
            params = []
            if len(tree.children) > 2:
                param_list = tree.children[1]
                if hasattr(param_list, 'children'):
                    params = param_list.children
                elif isinstance(param_list, list):
                    params = param_list
            body = tree.children[-1]  # Store body as Tree, do not transform
            self.functions[str(name)] = (params, body)
            return name
            
        # Special handling for function call: set up scope and evaluate body
        if tree.data == 'func_call':
            # Get function name
            name_node = tree.children[0]
            func_name = str(name_node)
            
            # Process arguments with type handling
            args = []
            if len(tree.children) > 1 and hasattr(tree.children[1], 'data') and tree.children[1].data == 'args':
                args = [self.eval_arg(arg) for arg in tree.children[1].children]
                
            # Handle module calls specially
            if isinstance(name_node, Tree) and name_node.data == "dotted_name":
                # This is a module call, delegate to the regular handler
                children = [self.transform(child) for child in tree.children]
                return handler(children)
                
            # For normal function calls
            if func_name not in self.functions:
                raise NameError(f"Function '{func_name}' not defined")
                
            params, body = self.functions[func_name]
            if len(params) != len(args):
                raise ValueError(f"Function '{func_name}' expects {len(params)} arguments, got {len(args)}")
                
            # Create function scope with parameters
            self.push_scope()
            for param, value in zip(params, args):
                param_name = str(param)
                self.env[-1][param_name] = value
                
            try:
                # Process function body statements
                result = None
                for child in body.children:
                    if isinstance(child, Tree) and child.data == 'return_stmt':
                        # Handle return statement
                        if len(child.children) > 0:
                            return_expr = child.children[0]
                            result = self.transform(return_expr)
                            # Normalize numeric results
                            if isinstance(result, float) and result.is_integer():
                                result = int(result)
                        else:
                            result = None
                        break
                    else:
                        # Execute other statements
                        result = self.transform(child)
                return result
            finally:
                self.pop_scope()
                
        # Default: transform children with improved type handling
        children = []
        for child in tree.children:
            transformed = self.transform(child)
            children.append(transformed)
            
        return handler(children)

    def transform(self, tree):
        if isinstance(tree, Tree):
            return self.transform_tree(tree)
        return super().transform(tree)

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
