"""
Sona Programming Language - Unified Interpreter
Enhanced interpreter with cognitive programming capabilities
"""

import ast
from typing import Any, Dict, List


# Import the enhanced interpreter as the main interpreter
try:
    from .enhanced_interpreter import (
        SonaInterpreter as SonaUnifiedInterpreter,
        SonaInterpreterError as SonaRuntimeError,
        SonaMemoryManager,
        default_interpreter,
    )
    print("✅ Using enhanced Sona interpreter with full language support")
except ImportError:
    print("⚠️  Falling back to basic interpreter")
    # Keep the existing implementation as fallback
    import traceback
    from pathlib import Path

    class SonaMemoryManager:
        """Manages memory and variable scoping for Sona interpreter"""
        
        def __init__(self):
            self.global_scope = {}
            self.local_scopes = []
            self.call_stack = []
        
        def push_scope(self, scope_name: str = "local"):
            """Push a new local scope"""
            self.local_scopes.append({})
            self.call_stack.append(scope_name)
        
        def pop_scope(self):
            """Pop the current local scope"""
            if self.local_scopes:
                self.local_scopes.pop()
                self.call_stack.pop()
        
        def set_variable(self, name: str, value: Any, global_scope: bool = False):
            """Set a variable in the appropriate scope"""
            if global_scope or not self.local_scopes:
                self.global_scope[name] = value
            else:
                self.local_scopes[-1][name] = value
        
        def get_variable(self, name: str) -> Any:
            """Get a variable from the appropriate scope"""
            # Check local scopes first (most recent first)
            for scope in reversed(self.local_scopes):
                if name in scope:
                    return scope[name]
            
            # Check global scope
            if name in self.global_scope:
                return self.global_scope[name]
            
            raise NameError(f"Variable '{name}' is not defined")
    
    def has_variable(self, name: str) -> bool:
        """Check if a variable exists in any scope"""
        try:
            self.get_variable(name)
            return True
        except NameError:
            return False

class SonaFunction:
    """Represents a function in Sona"""
    
    def __init__(self, name: str, parameters: list[str], body: Any, interpreter):
        self.name = name
        self.parameters = parameters
        self.body = body
        self.interpreter = interpreter
    
    def call(self, arguments: list[Any]) -> Any:
        """Call the function with given arguments"""
        if len(arguments) != len(self.parameters):
            raise ValueError(f"Function '{self.name}' expects {len(self.parameters)} arguments, got {len(arguments)}")
        
        # Push new scope for function execution
        self.interpreter.memory.push_scope(f"function:{self.name}")
        
        try:
            # Set parameters as local variables
            for param, arg in zip(self.parameters, arguments, strict=False):
                self.interpreter.memory.set_variable(param, arg)
            
            # Execute function body
            result = self.interpreter.execute_block(self.body)
            return result
        finally:
            # Always pop the function scope
            self.interpreter.memory.pop_scope()

class SonaUnifiedInterpreter:
    """
    Unified interpreter for the Sona programming language.
    Supports cognitive programming, AI assistance, and enhanced control flow.
    """
    
    def __init__(self):
        """Initialize the interpreter with all necessary components"""
        self.memory = SonaMemoryManager()
        self.functions = {}
        self.modules = {}
        self.ai_enabled = False
        self.debug_mode = False
        self.execution_stack = []
        
        # Initialize built-in functions
        self._setup_builtins()
    
    def _setup_builtins(self):
        """Setup built-in functions and variables"""
        # Built-in functions
        self.memory.set_variable('print', self._builtin_print, global_scope=True)
        self.memory.set_variable('len', self._builtin_len, global_scope=True)
        self.memory.set_variable('type', self._builtin_type, global_scope=True)
        self.memory.set_variable('str', self._builtin_str, global_scope=True)
        self.memory.set_variable('int', self._builtin_int, global_scope=True)
        self.memory.set_variable('float', self._builtin_float, global_scope=True)
        
        # Built-in variables
        self.memory.set_variable('__version__', '0.9.0', global_scope=True)
        self.memory.set_variable('__sona__', True, global_scope=True)
    
    def _builtin_print(self, *args):
        """Built-in print function"""
        print(*args)
        return None
    
    def _builtin_len(self, obj):
        """Built-in len function"""
        return len(obj)
    
    def _builtin_type(self, obj):
        """Built-in type function"""
        return type(obj).__name__
    
    def _builtin_str(self, obj):
        """Built-in str function"""
        return str(obj)
    
    def _builtin_int(self, obj):
        """Built-in int function"""
        return int(obj)
    
    def _builtin_float(self, obj):
        """Built-in float function"""
        return float(obj)
    
    def interpret(self, code: str, filename: str = "<string>") -> Any:
        """
        Interpret Sona code from a string
        
        Args:
            code: The Sona source code
            filename: Optional filename for error reporting
            
        Returns:
            The result of the interpretation
        """
        try:
            # For now, treat as Python-like code
            # TODO: Implement proper Sona parser
            return self.execute_python_like(code, filename)
        except Exception as e:
            if self.debug_mode:
                traceback.print_exc()
            raise SonaRuntimeError(f"Interpretation error: {e}")
    
    def execute_python_like(self, code: str, filename: str = "<string>") -> Any:
        """Execute Python-like code (temporary implementation)"""
        try:
            # Parse as Python AST for now
            tree = ast.parse(code, filename=filename)
            return self.execute_ast_node(tree)
        except SyntaxError as e:
            raise SonaRuntimeError(f"Syntax error in {filename}: {e}")
    
    def execute_ast_node(self, node: ast.AST) -> Any:
        """Execute an AST node"""
        if isinstance(node, ast.Module):
            result = None
            for stmt in node.body:
                result = self.execute_ast_node(stmt)
            return result
        
        elif isinstance(node, ast.Expr):
            return self.execute_ast_node(node.value)
        
        elif isinstance(node, ast.Assign):
            value = self.execute_ast_node(node.value)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.memory.set_variable(target.id, value)
                else:
                    raise SonaRuntimeError(f"Unsupported assignment target: {type(target)}")
            return value
        
        elif isinstance(node, ast.Name):
            return self.memory.get_variable(node.id)
        
        elif isinstance(node, ast.Constant):
            return node.value
        
        elif isinstance(node, ast.BinOp):
            left = self.execute_ast_node(node.left)
            right = self.execute_ast_node(node.right)
            return self._execute_binary_op(node.op, left, right)
        
        elif isinstance(node, ast.Call):
            func = self.execute_ast_node(node.func)
            args = [self.execute_ast_node(arg) for arg in node.args]
            
            if callable(func):
                return func(*args)
            elif isinstance(func, SonaFunction):
                return func.call(args)
            else:
                raise SonaRuntimeError(f"'{func}' is not callable")
        
        elif isinstance(node, ast.If):
            condition = self.execute_ast_node(node.test)
            if condition:
                return self.execute_block(node.body)
            elif node.orelse:
                return self.execute_block(node.orelse)
            return None
        
        elif isinstance(node, ast.For):
            iterable = self.execute_ast_node(node.iter)
            result = None
            for item in iterable:
                if isinstance(node.target, ast.Name):
                    self.memory.set_variable(node.target.id, item)
                result = self.execute_block(node.body)
            return result
        
        elif isinstance(node, ast.While):
            result = None
            while self.execute_ast_node(node.test):
                result = self.execute_block(node.body)
            return result
        
        elif isinstance(node, ast.FunctionDef):
            params = [arg.arg for arg in node.args.args]
            func = SonaFunction(node.name, params, node.body, self)
            self.functions[node.name] = func
            self.memory.set_variable(node.name, func)
            return func
        
        elif isinstance(node, ast.Return):
            if node.value:
                return self.execute_ast_node(node.value)
            return None
        
        else:
            raise SonaRuntimeError(f"Unsupported AST node type: {type(node)}")
    
    def execute_block(self, statements: list[ast.AST]) -> Any:
        """Execute a block of statements"""
        result = None
        for stmt in statements:
            result = self.execute_ast_node(stmt)
        return result
    
    def _execute_binary_op(self, op: ast.operator, left: Any, right: Any) -> Any:
        """Execute a binary operation"""
        if isinstance(op, ast.Add):
            return left + right
        elif isinstance(op, ast.Sub):
            return left - right
        elif isinstance(op, ast.Mult):
            return left * right
        elif isinstance(op, ast.Div):
            return left / right
        elif isinstance(op, ast.Mod):
            return left % right
        elif isinstance(op, ast.Pow):
            return left ** right
        else:
            raise SonaRuntimeError(f"Unsupported binary operator: {type(op)}")
    
    def evaluate(self, expression: str) -> Any:
        """
        Evaluate a single Sona expression
        
        Args:
            expression: The expression to evaluate
            
        Returns:
            The result of the evaluation
        """
        try:
            # Parse as expression
            tree = ast.parse(expression, mode='eval')
            return self.execute_ast_node(tree.body)
        except Exception as e:
            raise SonaRuntimeError(f"Evaluation error: {e}")
    
    def execute_statement(self, statement: str) -> Any:
        """
        Execute a single Sona statement
        
        Args:
            statement: The statement to execute
            
        Returns:
            The result of the execution
        """
        return self.interpret(statement)
    
    def execute_file(self, filepath: str) -> Any:
        """
        Execute a Sona file
        
        Args:
            filepath: Path to the Sona file
            
        Returns:
            The result of the file execution
        """
        path = Path(filepath)
        if not path.exists():
            raise SonaRuntimeError(f"File not found: {filepath}")
        
        try:
            with open(filepath, encoding='utf-8') as f:
                code = f.read()
            return self.interpret(code, filename=filepath)
        except Exception as e:
            raise SonaRuntimeError(f"Error executing file {filepath}: {e}")
    
    def set_variable(self, name: str, value: Any, global_scope: bool = False):
        """Set a variable in the interpreter"""
        self.memory.set_variable(name, value, global_scope)
    
    def get_variable(self, name: str) -> Any:
        """Get a variable from the interpreter"""
        return self.memory.get_variable(name)
    
    def has_variable(self, name: str) -> bool:
        """Check if a variable exists"""
        return self.memory.has_variable(name)
    
    def enable_ai(self):
        """Enable AI assistance features"""
        self.ai_enabled = True
    
    def disable_ai(self):
        """Disable AI assistance features"""
        self.ai_enabled = False
    
    def enable_debug(self):
        """Enable debug mode"""
        self.debug_mode = True
    
    def disable_debug(self):
        """Disable debug mode"""
        self.debug_mode = False
    
    def reset(self):
        """Reset the interpreter state"""
        self.__init__()
    
    def get_state(self) -> dict[str, Any]:
        """Get the current interpreter state"""
        return {
            'variables': dict(self.memory.global_scope),
            'functions': list(self.functions.keys()),
            'modules': list(self.modules.keys()),
            'ai_enabled': self.ai_enabled,
            'debug_mode': self.debug_mode
        }

class SonaRuntimeError(Exception):
    """Runtime error in Sona interpretation"""
    pass

# Create a default interpreter instance for convenience
default_interpreter = SonaUnifiedInterpreter()

# Export the main classes and functions
__all__ = [
    'SonaUnifiedInterpreter',
    'SonaFunction',
    'SonaMemoryManager', 
    'SonaRuntimeError',
    'default_interpreter'
]
