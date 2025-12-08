"""
Sona v0.9.7 - Enhanced Interpreter with Full Loop Support
========================================================

Production-grade interpreter with complete language feature support.
Includes all control flow constructs, module system, and cognitive features.

Features:
- Full control flow (if/else/elif, while, for, repeat)
- Break/continue statements
- Module system (import/export)
- AI integration statements
- Cognitive programming support
- Try/catch/finally exception handling
- Function definitions with parameters
- Class definitions and methods
- Complete expression evaluation
"""

import ast
import sys
import time
import traceback
from pathlib import Path
from typing import Any  # Ruff UP035: will migrate away from Dict/List


# Add current directory to path for imports
if str(Path(__file__).parent) not in sys.path:
    sys.path.append(str(Path(__file__).parent))

# Import parser
try:
    from .parser_v090 import SonaParserv090
except ImportError:
    try:
        from parser_v090 import SonaParserv090
    except ImportError:
        print("⚠️  Advanced parser not available, using basic mode")
        SonaParserv090 = None

# Import AST nodes
try:
    from .ast_nodes_v090 import (
        AICompleteStatement,
        AIDebugStatement,
        AIExplainStatement,
        AIOptimizeStatement,
        ReturnValue,
    )
except ImportError:
    try:
        from ast_nodes_v090 import (
            AICompleteStatement,
            AIDebugStatement,
            AIExplainStatement,
            AIOptimizeStatement,
            ReturnValue,
        )
    except ImportError:
        print("⚠️  AST nodes not available, using placeholder mode")
        # Create placeholder classes

        class AICompleteStatement:
            pass

        class AIExplainStatement:
            pass

        class AIDebugStatement:
            pass

        class AIOptimizeStatement:
            pass

# Import Cognitive Assistant
try:
    from .ai.cognitive_assistant import CognitiveAssistant
except ImportError:
    try:
        from ai.cognitive_assistant import CognitiveAssistant
    except ImportError:
        print("[WARN] CognitiveAssistant not available, using placeholder mode")

        class CognitiveAssistant:
            def __init__(self):
                pass

            def analyze_working_memory(self, *args, **kwargs):
                return {'cognitive_load': 'medium', 'suggestions': []}

            def detect_hyperfocus(self, *args, **kwargs):
                return {'hyperfocus_detected': False}

            def analyze_executive_function(self, *args, **kwargs):
                return {'task_breakdown': [], 'support_strategies': []}


class SonaInterpreterError(Exception):
    """Base class for Sona interpreter errors"""
    pass


class SonaRuntimeError(Exception):
    """Runtime error in Sona interpretation"""
    pass


class BreakException(Exception):
    """Exception for break statement flow control"""
    pass


class ContinueException(Exception):
    """Exception for continue statement flow control"""
    pass


class SimpleModuleSystem:
    """Simple module system for loading stdlib modules"""

    def __init__(self, interpreter):
        self.interpreter = interpreter
        self.loaded_modules = {}
        self.stdlib_path = Path(__file__).parent / "stdlib"

    def import_module(self, module_path: str, alias: str | None = None):
        """Import a module and make it available in the interpreter

        Supports nested namespaces like 'collection.list':
        - collection.list → sona/stdlib/collection/list.py
        - http → sona/stdlib/http.py or native_http.py
        """
        module_name = alias if alias else module_path

        # Check if already loaded
        if module_name in self.loaded_modules:
            return self.loaded_modules[module_name]

        # Handle nested namespaces (e.g., collection.list)
        parts = module_path.split('.')

        if len(parts) > 1:
            # Nested namespace: collection.list
            # Build path: sona/stdlib/collection/list.py
            namespace_dir = self.stdlib_path / parts[0]
            module_file = namespace_dir / f"{parts[1]}.py"

            if module_file.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    f"sona.stdlib.{module_path}",
                    module_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Store module object
                    self.loaded_modules[module_name] = module

                    # Make module available as a variable
                    self.interpreter.memory.set_variable(
                        module_name,
                        module,
                        global_scope=True
                    )

                    return module

            raise ImportError(
                f"Nested module '{module_path}' not found at {module_file}"
            )

        # Single-level module: try native first, then regular
        # Try native module first (native_{module}.py)
        native_module_path = self.stdlib_path / f"native_{module_path}.py"

        if native_module_path.exists():
            # Load native Python module
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                f"sona.stdlib.native_{module_path}",
                native_module_path
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Store module object
                self.loaded_modules[module_name] = module

                # Make module available as a variable
                self.interpreter.memory.set_variable(
                    module_name,
                    module,
                    global_scope=True
                )

                return module

        # Try regular module (module.py)
        regular_module_path = self.stdlib_path / f"{module_path}.py"

        if regular_module_path.exists():
            # Load regular Python module
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                f"sona.stdlib.{module_path}",
                regular_module_path
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Store module object
                self.loaded_modules[module_name] = module

                # Make module available as a variable
                self.interpreter.memory.set_variable(
                    module_name,
                    module,
                    global_scope=True
                )

                return module

        raise ImportError(f"Module '{module_path}' not found")


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

    def has_variable(
        self,
        name: str
    ) -> bool:
        """Check if a variable exists in any scope"""
        try:
            self.get_variable(name)
            return True
        except NameError:
            return False


class SonaFunction:
    """Represents a function in Sona"""

    def __init__(
        self,
        name: str,
        parameters: list[str],
        body: Any,
        interpreter
    ):
        self.name = name
        self.parameters = parameters
        self.body = body
        self.interpreter = interpreter

    def call(
        self,
        arguments: list[Any]
    ) -> Any:
        """Call the function with given arguments"""
        if len(arguments) != len(self.parameters):
            raise ValueError(
                f"Function '{self.name}' expects {len(self.parameters)} "
                f"arguments, got {len(arguments)}"
            )

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

        # Initialize module system
        self.module_system = SimpleModuleSystem(self)

        # Initialize cognitive assistant
        self.cognitive_assistant = CognitiveAssistant()
        self.session_start_time = time.time()
        self.current_context = ""

        # Initialize built-in functions
        self._setup_builtins()

    def _setup_builtins(self):
        """Setup built-in functions and variables"""
        # Built-in functions
        gv = self.memory.set_variable
        gv('print', self._builtin_print, global_scope=True)
        gv('len', self._builtin_len, global_scope=True)
        gv('type', self._builtin_type, global_scope=True)
        gv('str', self._builtin_str, global_scope=True)
        gv('int', self._builtin_int, global_scope=True)
        gv('float', self._builtin_float, global_scope=True)
        gv('bool', self._builtin_bool, global_scope=True)
        gv('list', self._builtin_list, global_scope=True)
        gv('dict', self._builtin_dict, global_scope=True)
        gv('range', self._builtin_range, global_scope=True)
        gv('sum', self._builtin_sum, global_scope=True)
        gv('max', self._builtin_max, global_scope=True)
        gv('min', self._builtin_min, global_scope=True)

        # Cognitive AI built-in functions
        self.memory.set_variable('think', self._cognitive_think,
                                 global_scope=True)
        self.memory.set_variable('remember', self._cognitive_remember,
                                 global_scope=True)
        self.memory.set_variable('focus', self._cognitive_focus,
                                 global_scope=True)
        self.memory.set_variable('analyze_load', self._cognitive_analyze_load,
                                 global_scope=True)

        # REAL AI-Native Language Features - NO MOCKS
        self.memory.set_variable('ai_complete', self._real_ai_complete,
                                 global_scope=True)
        self.memory.set_variable('ai_explain', self._real_ai_explain,
                                 global_scope=True)
        self.memory.set_variable('ai_simplify', self._real_ai_simplify,
                                 global_scope=True)
        self.memory.set_variable('ai_debug', self._real_ai_debug,
                                 global_scope=True)
        # Week 2: Advanced AI Programming Constructs
        self.memory.set_variable('ai_reason', self._real_ai_reason,
                                 global_scope=True)
        self.memory.set_variable('ai_refactor', self._real_ai_refactor,
                                 global_scope=True)
        self.memory.set_variable('ai_test', self._real_ai_test,
                                 global_scope=True)
        self.memory.set_variable('ai_analyze', self._real_ai_analyze,
                                 global_scope=True)
        self.memory.set_variable('ai_generate', self._real_ai_generate,
                                 global_scope=True)
        # Week 3: AI-Enhanced Development Environment Integration
        self.memory.set_variable('ai_context', self._real_ai_context,
                                 global_scope=True)
        self.memory.set_variable('ai_suggest', self._real_ai_suggest,
                                 global_scope=True)
        self.memory.set_variable('ai_document', self._real_ai_document,
                                 global_scope=True)
        self.memory.set_variable('ai_optimize', self._real_ai_optimize,
                                 global_scope=True)
        self.memory.set_variable('ai_security', self._real_ai_security,
                                 global_scope=True)
        self.memory.set_variable('ai_mentor', self._real_ai_mentor,
                                 global_scope=True)
        self.memory.set_variable('generate_code', self._real_ai_generate_code,
                                 global_scope=True)
        self.memory.set_variable('complete_function',
                                 self._real_ai_complete_function,
                                 global_scope=True)
        self.memory.set_variable('explain_code', self._real_ai_explain_code,
                                 global_scope=True)
        self.memory.set_variable('suggest_improvements',
                                 self._real_ai_suggest_improvements,
                                 global_scope=True)
        self.memory.set_variable('when_confused',
                                 self._cognitive_when_confused,
                                 global_scope=True)
        self.memory.set_variable('break_if_overwhelmed',
                                 self._cognitive_break_if_overwhelmed,
                                 global_scope=True)
        self.memory.set_variable('simplify_task',
                                 self._cognitive_simplify_task,
                                 global_scope=True)
        self.memory.set_variable('review_progress',
                                 self._cognitive_review_progress,
                                 global_scope=True)

        # Day 3C: Advanced AI Constructs
        self.memory.set_variable('adaptive_learning',
                                 self._ai_adaptive_learning,
                                 global_scope=True)
        self.memory.set_variable('meta_cognition',
                                 self._ai_meta_cognition,
                                 global_scope=True)
        self.memory.set_variable('dynamic_context_switching',
                                 self._ai_dynamic_context_switching,
                                 global_scope=True)
        self.memory.set_variable('multi_step_reasoning',
                                 self._ai_multi_step_reasoning,
                                 global_scope=True)

        # Built-in variables
        self.memory.set_variable('__version__', '0.9.7', global_scope=True)
        self.memory.set_variable('__sona__', True, global_scope=True)
        self.memory.set_variable('True', True, global_scope=True)
        self.memory.set_variable('False', False, global_scope=True)
        self.memory.set_variable('None', None, global_scope=True)

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

    def _builtin_bool(self, obj):
        """Built-in bool function"""
        return bool(obj)

    def _builtin_list(self, obj=None):
        """Built-in list function"""
        if obj is None:
            return []
        return list(obj)

    def _builtin_dict(self, *args, **kwargs):
        """Built-in dict function"""
        return dict(*args, **kwargs)

    def _builtin_range(self, *args):
        """Built-in range function"""
        return list(range(*args))

    def _builtin_sum(self, iterable, start=0):
        """Built-in sum function"""
        return sum(iterable, start)

    def _builtin_max(self, *args):
        """Built-in max function"""
        if len(args) == 1 and hasattr(args[0], '__iter__'):
            return max(args[0])
        return max(args)

    def _builtin_min(self, *args):
        """Built-in min function"""
        if len(args) == 1 and hasattr(args[0], '__iter__'):
            return min(args[0])
        return min(args)

    # ========================================================================
    # FUNCTION MANAGEMENT (v0.9.6)
    # ========================================================================

    def define_function(self, name: str, func_def):
        """Define a user function"""
        self.functions[name] = SonaFunction(
            name=name,
            parameters=func_def.parameters,
            body=func_def.body,
            interpreter=self
        )
        # Also register in variable scope for calling
        self.memory.set_variable(name, self.functions[name], global_scope=True)

    def call_function(self, name: str, arguments: list[Any]) -> Any:
        """Call a user-defined or built-in function"""
        # Check built-in functions first
        if name == "range":
            if len(arguments) == 1:
                return list(range(int(arguments[0])))
            elif len(arguments) == 2:
                return list(range(int(arguments[0]), int(arguments[1])))
            elif len(arguments) == 3:
                return list(
                    range(
                        int(arguments[0]),
                        int(arguments[1]),
                        int(arguments[2])
                    )
                )
            else:
                raise TypeError(
                    f"range() takes 1-3 arguments, got {len(arguments)}"
                )
        elif name == "len":
            if len(arguments) != 1:
                raise TypeError(
                    f"len() takes exactly 1 argument, got {len(arguments)}"
                )
            return len(arguments[0])

        # Check user-defined functions
        if name not in self.functions:
            raise NameError(f"Function '{name}' is not defined")

        func = self.functions[name]
        return func.call(arguments)

    def execute_block(self, statements: list) -> Any:
        """Execute a block of Sona AST statements"""
        result = None
        for stmt in statements:
            try:
                if hasattr(stmt, 'execute'):
                    # Custom Sona AST node
                    result = stmt.execute(self)
                elif hasattr(stmt, 'evaluate'):
                    # Custom Sona AST node
                    result = stmt.evaluate(self)
                else:
                    # Python AST node or other
                    result = self.execute_ast_node(stmt)
            except ReturnValue as ret:
                # Return from function
                return ret.value
            except (BreakException, ContinueException):
                # Re-raise break/continue to propagate to enclosing loop
                raise
        return result

    # Alias for compatibility with AST nodes
    def execute_statements(self, statements: list) -> Any:
        """Alias for execute_block for AST node compatibility"""
        return self.execute_block(statements)

    # ========================================================================
    # CODE INTERPRETATION
    # ========================================================================

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
            # Use Sona parser if available and code contains Sona syntax
            if SonaParserv090 and self._is_sona_syntax(code):
                return self._execute_sona_code(code, filename)
            else:
                # Fallback to Python-like compatibility mode
                if not SonaParserv090:
                    print("⚠️  Sona parser not available, using Python compatibility mode")
                return self.execute_python_like(code, filename)
        except Exception as e:
            if self.debug_mode:
                traceback.print_exc()
            raise SonaRuntimeError(f"Interpretation error: {e}") from e

    def _is_sona_syntax(self, code: str) -> bool:
        """Detect if code contains Sona-specific syntax"""

        # AI-native function names that should use Python execution
        ai_functions = [
            'think', 'remember', 'focus', 'analyze_load',
            'generate_code', 'complete_function', 'explain_code',
            'suggest_improvements', 'when_confused', 'break_if_overwhelmed',
            'simplify_task', 'review_progress',
            # Day 3C: Advanced AI Constructs
            'adaptive_learning', 'meta_cognition', 'dynamic_context_switching',
            'multi_step_reasoning'
        ]

        # Check for AI function calls - these should use Python execution
        for func_name in ai_functions:
            if f'{func_name}(' in code:
                return False  # Force Python execution for AI functions

        sona_keywords = [
            'let', 'const', 'func', 'function', '=>',
            'if', 'else', 'while', 'for', 'match', 'case',
            'class', 'extends', 'import', 'export',
            'true', 'false', 'null', 'undefined'
        ]

        # Check for Sona keywords
        for keyword in sona_keywords:
            if keyword in code:
                return True

        # Check for Sona-style syntax patterns
        sona_patterns = [
            ' = [',  # List assignments
            ' = {',  # Object assignments
            'let ',  # Variable declarations
            'const ', # Constant declarations
        ]

        return any(pattern in code for pattern in sona_patterns)

        return False

    def _convert_sona_to_python(self, code: str) -> str:
        """Convert Sona C-style syntax to Python for compatibility"""
        import re

        # First, handle line-by-line conversion of keywords
        lines = code.split('\n')
        result_lines = []
        i = 0
        indent_level = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                result_lines.append('')
                i += 1
                continue

            # Remove trailing semicolons
            if stripped.endswith(';'):
                stripped = stripped[:-1]

            # Handle closing braces
            if stripped.startswith('}'):
                indent_level = max(0, indent_level - 1)
                i += 1
                continue

            # Convert while (condition) { to while condition:
            if 'while' in stripped and '{' in stripped:
                # Extract condition
                match = re.search(
                    r'while\s*\(?\s*(.+?)\s*\)?\s*\{',
                    stripped
                )
                if match:
                    condition = match.group(1).strip()
                    result_lines.append(
                        '    ' * indent_level + f'while {condition}:'
                    )
                    indent_level += 1
                    i += 1
                    continue

            # Convert if (condition) { to if condition:
            if 'if' in stripped and '{' in stripped:
                match = re.search(
                    r'if\s*\(?\s*(.+?)\s*\)?\s*\{',
                    stripped
                )
                if match:
                    condition = match.group(1).strip()
                    result_lines.append(
                        '    ' * indent_level + f'if {condition}:'
                    )
                    indent_level += 1
                    i += 1
                    continue

            # Convert repeat N times { to for _ in range(N):
            if 'repeat' in stripped and 'times' in stripped and '{' in stripped:
                match = re.search(
                    r'repeat\s+(.+?)\s+times\s*\{',
                    stripped
                )
                if match:
                    count = match.group(1).strip()
                    result_lines.append(
                        '    ' * indent_level + f'for _ in range({count}):'
                    )
                    indent_level += 1
                    i += 1
                    continue

            # Convert repeat N { to for _ in range(N):
            if 'repeat' in stripped and '{' in stripped and 'times' not in stripped:
                match = re.search(
                    r'repeat\s+(.+?)\s*\{',
                    stripped
                )
                if match:
                    count = match.group(1).strip()
                    result_lines.append(
                        '    ' * indent_level + f'for _ in range({count}):'
                    )
                    indent_level += 1
                    i += 1
                    continue

            # Convert for x in y { to for x in y:
            if 'for' in stripped and 'in' in stripped and '{' in stripped:
                match = re.search(
                    r'for\s+(\w+)\s+in\s+(.+?)\s*\{',
                    stripped
                )
                if match:
                    var = match.group(1).strip()
                    iter_expr = match.group(2).strip()
                    result_lines.append(
                        '    ' * indent_level + f'for {var} in {iter_expr}:'
                    )
                    indent_level += 1
                    i += 1
                    continue

            # Regular statement (add indentation)
            result_lines.append('    ' * indent_level + stripped)
            i += 1

        return '\n'.join(result_lines)

    def _execute_sona_code(self, code: str, filename: str = "<string>") -> Any:
        """Execute Sona code using the proper Sona parser"""
        try:
            # Create parser instance
            parser = SonaParserv090()

            # Parse Sona code into AST nodes
            ast_nodes = parser.parse(code, filename)

            if ast_nodes is None:
                raise SonaRuntimeError(
                    f"Failed to parse Sona code in {filename}"
                )

            # Execute AST nodes
            result = None
            for node in ast_nodes:
                if hasattr(node, 'execute'):
                    result = node.execute(self)
                elif hasattr(node, 'evaluate'):
                    result = node.evaluate(self)
                else:
                    # Handle raw values or simple nodes
                    result = self._handle_simple_node(node)

            return result

        except Exception as e:
            print(f"DEBUG: Exception in _execute_sona_code: {e}")
            print(f"DEBUG: Exception type: {type(e)}")

            # If Sona parsing fails, try converting to Python
            has_braces = '{' in code
            has_keywords = any(
                kw in code for kw in ['while', 'for', 'if', 'repeat']
            )

            print(f"DEBUG: has_braces={has_braces}, has_keywords={has_keywords}")

            if has_braces and has_keywords:
                try:
                    print("DEBUG: Converting Sona to Python...")
                    converted_code = self._convert_sona_to_python(code)
                    print(
                        "DEBUG: Conversion successful, executing converted code..."
                    )
                    result = self.execute_python_like(
                        converted_code,
                        filename
                    )
                    print("DEBUG: Converted code executed successfully!")
                    return result
                except Exception as convert_error:
                    print(f"Convert error: {convert_error}")
                    import traceback
                    traceback.print_exc()

            # If Sona parsing fails, try Python compatibility mode
            print(f"⚠️  Sona parsing failed: {e}")
            print("   Falling back to Python compatibility mode")
            return self.execute_python_like(code, filename)

    def _handle_simple_node(self, node) -> Any:
        """Handle simple AST nodes that don't have execute/evaluate methods"""
        if hasattr(node, 'value'):
            return node.value
        elif isinstance(node, (int, float, str, bool)):
            return node
        else:
            return str(node)

    def execute_python_like(
        self,
        code: str,
        filename: str = "<string>"
    ) -> Any:
        """Execute Python-like code (temporary implementation)"""
        try:
            # Parse as Python AST for now
            tree = ast.parse(code, filename=filename)
            return self.execute_ast_node(tree)
        except SyntaxError as e:
            raise SonaRuntimeError(f"Syntax error in {filename}: {e}") from e

    def execute(
        self,
        tree
    ) -> Any:
        """Execute a parse tree (main entry point for CLI)"""
        try:
            # For now, if it's a Lark tree, convert to string and parse as Python
            if hasattr(tree, 'pretty'):
                # Lark tree - convert to string representation
                tree_str = str(tree.pretty())
                return self.execute_python_like(tree_str)
            elif hasattr(tree, 'data'):
                # Lark tree node - basic handling
                return self.execute_python_like(str(tree))
            elif isinstance(tree, str):
                # String code
                return self.execute_python_like(tree)
            else:
                # Assume it's an AST node
                return self.execute_ast_node(tree)
        except Exception as e:
            if self.debug_mode:
                traceback.print_exc()
            raise SonaRuntimeError(f"Execution error: {e}") from e

    def execute_ast_node(
        self,
        node: ast.AST
    ) -> Any:
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

        elif isinstance(node, ast.AugAssign):
            # Augmented assignment (+=, -=, etc.)
            if isinstance(node.target, ast.Name):
                current_value = self.memory.get_variable(node.target.id)
                new_value = self.execute_ast_node(node.value)
                result = self._execute_binary_op(node.op, current_value, new_value)
                self.memory.set_variable(node.target.id, result)
                return result
            else:
                raise SonaRuntimeError(f"Unsupported augmented assignment target: {type(node.target)}")

        elif isinstance(node, ast.Name):
            return self.memory.get_variable(node.id)

        elif isinstance(node, ast.Constant):
            return node.value

        elif isinstance(node, ast.BinOp):
            left = self.execute_ast_node(node.left)
            right = self.execute_ast_node(node.right)
            return self._execute_binary_op(node.op, left, right)

        elif isinstance(node, ast.Compare):
            left = self.execute_ast_node(node.left)
            result = left
            for op, comparator in zip(node.ops, node.comparators, strict=False):
                right = self.execute_ast_node(comparator)
                result = self._execute_compare_op(op, result, right)
                if not result:
                    break
                result = right  # For chained comparisons
            return bool(result)

        elif isinstance(node, ast.List):
            return [self.execute_ast_node(elt) for elt in node.elts]

        elif isinstance(node, ast.Subscript):
            value = self.execute_ast_node(node.value)
            index = self.execute_ast_node(node.slice)
            return value[index]

        elif isinstance(node, ast.Dict):
            result = {}
            for key, value in zip(node.keys, node.values, strict=False):
                key_val = self.execute_ast_node(key)
                value_val = self.execute_ast_node(value)
                result[key_val] = value_val
            return result

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
            try:
                for item in iterable:
                    if isinstance(node.target, ast.Name):
                        self.memory.set_variable(node.target.id, item)
                    try:
                        result = self.execute_block(node.body)
                    except ContinueException:
                        continue
                    except BreakException:
                        break
            except BreakException:
                pass
            return result

        elif isinstance(node, ast.While):
            result = None
            try:
                while self.execute_ast_node(node.test):
                    try:
                        result = self.execute_block(node.body)
                    except ContinueException:
                        continue
                    except BreakException:
                        break
            except BreakException:
                pass
            return result

        elif hasattr(ast, 'Repeat') and isinstance(node, ast.Repeat):
            # Handle repeat N times { ... } construct
            # This is a custom AST node that may come from Lark parser
            count = self.execute_ast_node(node.count)
            result = None
            try:
                for _ in range(int(count)):
                    try:
                        result = self.execute_block(node.body)
                    except ContinueException:
                        continue
                    except BreakException:
                        break
            except BreakException:
                pass
            return result

        elif isinstance(node, ast.FunctionDef):
            params = [arg.arg for arg in node.args.args]
            func = SonaFunction(node.name, params, node.body, self)
            self.functions[node.name] = func
            self.memory.set_variable(node.name, func)
            return func

        elif isinstance(node, ast.Lambda):
            params = [arg.arg for arg in node.args.args]
            # Create anonymous function with lambda body
            lambda_func = SonaFunction(
                name=f"<lambda_{id(node)}>",
                parameters=params,
                body=[ast.Return(value=node.body)],  # Wrap lambda body in return
                interpreter=self
            )
            return lambda_func

        elif isinstance(node, ast.Return):
            if node.value:
                return self.execute_ast_node(node.value)
            return None

        elif isinstance(node, ast.Break):
            raise BreakException()

        elif isinstance(node, ast.Continue):
            raise ContinueException()

        elif isinstance(node, ast.Attribute):
            obj = self.execute_ast_node(node.value)
            return getattr(obj, node.attr)

        elif isinstance(node, ast.ListComp):
            # List comprehension: [expr for target in iter if condition]
            result = []
            iterable = self.execute_ast_node(node.generators[0].iter)
            for item in iterable:
                # Set the target variable
                if isinstance(node.generators[0].target, ast.Name):
                    old_value = None
                    var_name = node.generators[0].target.id
                    # Save old value if it exists
                    if self.memory.has_variable(var_name):
                        old_value = self.memory.get_variable(var_name)

                    self.memory.set_variable(var_name, item)

                    # Check conditions
                    include = True
                    for condition in node.generators[0].ifs:
                        if not self.execute_ast_node(condition):
                            include = False
                            break

                    # Add to result if conditions met
                    if include:
                        result.append(self.execute_ast_node(node.elt))

                    # Restore old value or remove variable
                    if old_value is not None:
                        self.memory.set_variable(var_name, old_value)
                    elif self.memory.has_variable(var_name):
                        # Note: This is simplified - proper scope handling needed
                        pass
            return result

        elif isinstance(node, ast.JoinedStr):
            # f-string support
            result = ""
            for value in node.values:
                if isinstance(value, ast.Constant):
                    result += str(value.value)
                elif isinstance(value, ast.FormattedValue):
                    formatted_val = self.execute_ast_node(value.value)
                    result += str(formatted_val)
                else:
                    result += str(self.execute_ast_node(value))
            return result

        else:
            raise SonaRuntimeError(f"Unsupported AST node type: {type(node)}")

    def execute_python_block(self, statements: list[ast.AST]) -> Any:
        """Execute a block of Python AST statements"""
        result = None
        for stmt in statements:
            result = self.execute_ast_node(stmt)
        return result

    def _execute_binary_op(
        self,
        op: ast.operator,
        left: Any,
        right: Any
    ) -> Any:
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

    def _execute_compare_op(
        self,
        op: ast.cmpop,
        left: Any,
        right: Any
    ) -> bool:
        """Execute a comparison operation"""
        if isinstance(op, ast.Eq):
            return left == right
        elif isinstance(op, ast.NotEq):
            return left != right
        elif isinstance(op, ast.Lt):
            return left < right
        elif isinstance(op, ast.LtE):
            return left <= right
        elif isinstance(op, ast.Gt):
            return left > right
        elif isinstance(op, ast.GtE):
            return left >= right
        elif isinstance(op, ast.Is):
            return left is right
        elif isinstance(op, ast.IsNot):
            return left is not right
        elif isinstance(op, ast.In):
            return left in right
        elif isinstance(op, ast.NotIn):
            return left not in right
        else:
            raise SonaRuntimeError(f"Unsupported comparison operator: {type(op)}")

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
            raise SonaRuntimeError(f"Evaluation error: {e}") from e

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
            raise SonaRuntimeError(f"Error executing file {filepath}: {e}") from e

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

    # Cognitive AI Built-in Functions

    def _cognitive_think(self, prompt: str) -> dict[str, Any]:
        """Built-in cognitive thinking function"""
        self.current_context = prompt
        session_time = time.time() - self.session_start_time

        # Provide compatible parameters for both real and placeholder
        try:
            analysis = self.cognitive_assistant.analyze_working_memory(
                current_task=prompt,
                context=self.current_context
            )
        except TypeError:
            # Fallback for placeholder or different interface
            analysis = self.cognitive_assistant.analyze_working_memory()

        return {
            'thought': prompt,
            'cognitive_analysis': analysis,
            'timestamp': time.time(),
            'session_duration': session_time
        }

    def _cognitive_remember(self, key: str, value: Any = None) -> Any:
        """Built-in cognitive memory function"""
        memory_key = f"_cognitive_memory_{key}"

        if value is not None:
            # Store memory
            self.memory.set_variable(memory_key, value, global_scope=True)
            return {
                'action': 'stored',
                'key': key,
                'value': value,
                'timestamp': time.time()
            }
        else:
            # Retrieve memory
            try:
                stored_value = self.memory.get_variable(memory_key)
                return stored_value
            except NameError:
                return {
                    'action': 'not_found',
                    'key': key,
                    'message': f"No memory found for key '{key}'"
                }

    def _cognitive_focus(self, task_description: str) -> dict[str, Any]:
        """Built-in cognitive focus function"""
        session_time = time.time() - self.session_start_time

        # Provide compatible parameters for both real and placeholder
        try:
            # Real CognitiveAssistant expects typing_data
            typing_data = [{'timestamp': time.time(),
                           'chars': len(task_description)}]
            hyperfocus_analysis = self.cognitive_assistant.\
                detect_hyperfocus(typing_data)
        except TypeError:
            hyperfocus_analysis = self.cognitive_assistant.detect_hyperfocus()

        try:
            executive_analysis = self.cognitive_assistant.\
                analyze_executive_function(task_description)
        except TypeError:
            executive_analysis = self.cognitive_assistant.\
                analyze_executive_function()

        return {
            'task': task_description,
            'hyperfocus_state': hyperfocus_analysis,
            'executive_function': executive_analysis,
            'focus_timestamp': time.time(),
            'session_duration': session_time
        }

    def _cognitive_analyze_load(self) -> dict[str, Any]:
        """Built-in cognitive load analysis function"""
        session_time = time.time() - self.session_start_time

        # Provide compatible parameters for both real and placeholder
        try:
            memory_analysis = self.cognitive_assistant.analyze_working_memory(
                current_task=self.current_context or "General analysis",
                context=f"Session: {session_time:.1f}s, "
                        f"Vars: {len(self.memory.global_scope)}, "
                        f"Funcs: {len(self.functions)}"
            )
        except TypeError:
            memory_analysis = self.cognitive_assistant.analyze_working_memory()

        return {
            'cognitive_load': memory_analysis.get('cognitive_load', 'medium'),
            'working_memory_analysis': memory_analysis,
            'session_metrics': {
                'duration': session_time,
                'scope_depth': len(self.memory.local_scopes),
                'variables': len(self.memory.global_scope),
                'functions': len(self.functions),
                'modules': len(self.modules)
            },
            'recommendations': memory_analysis.get('suggestions', []),
            'timestamp': time.time()
        }

    # AI-Native Language Features (Day 3B)

    # REAL AI IMPLEMENTATION METHODS - NO MOCKS
    def _setup_real_ai_provider(self):
        """Initialize REAL AI provider using MultiAIProvider - NO MOCKS"""
        try:
            # Use our MultiAIProvider with external credentials
            import sys
            from pathlib import Path

            # Add current directory to path for imports
            sona_root = Path(__file__).parent.parent
            if str(sona_root) not in sys.path:
                sys.path.append(str(sona_root))

            from multi_ai_provider import MultiAIProvider
            self.real_ai = MultiAIProvider()
            print("✅ REAL AI provider initialized with MultiAIProvider")
        except ImportError as e:
            print(f"❌ Failed to import MultiAIProvider: {e}")
            # Fallback to original real AI provider
            try:
                from .ai.real_ai_provider import REAL_AI_PROVIDER
                self.real_ai = REAL_AI_PROVIDER
                print("✅ REAL AI provider initialized (fallback)")
            except ImportError:
                print("❌ Failed to import fallback AI provider")
                self.real_ai = None

    def _real_ai_complete(self, code_context: str) -> str:
        """REAL AI code completion - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_complete(code_context)
                # MultiAIProvider returns string directly, not object with .content
                if isinstance(response, str):
                    return response
                elif hasattr(response, 'content'):
                    return response.content
                else:
                    return str(response)
            except Exception as e:
                return f"# AI completion failed: {e}"
        else:
            return "# Real AI not available - check configuration"

    def _real_ai_explain(self, code_snippet: str,
                         level: str = "intermediate") -> str:
        """REAL AI code explanation - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_explain(code_snippet, level)
                # MultiAIProvider returns string directly, not object with .content
                if isinstance(response, str):
                    return response
                elif hasattr(response, 'content'):
                    return response.content
                else:
                    return str(response)
            except Exception as e:
                return f"AI explanation failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_debug(self, error_context: str, code: str = "") -> str:
        """REAL AI debugging assistance - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_debug(error_context, code)
                return response.content
            except Exception as e:
                return f"AI debugging failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_generate_code(self, description: str) -> dict[str, Any]:
        """REAL AI code generation - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                prompt = f"Generate Python code for: {description}"
                response = self.real_ai.ai_complete(prompt)
                return {
                    'description': description,
                    'generated_code': response.content,
                    'source': 'REAL_AI',
                    'cost_usd': response.cost_usd,
                    'tokens_used': response.tokens_used,
                    'timestamp': time.time(),
                    'ready_to_execute': True
                }
            except Exception as e:
                return {
                    'description': description,
                    'generated_code': f"# Real AI generation failed: {e}",
                    'source': 'error',
                    'error': str(e),
                    'timestamp': time.time(),
                    'ready_to_execute': False
                }
        else:
            return {
                'description': description,
                'generated_code': "# Real AI not available - check configuration",
                'source': 'error',
                'timestamp': time.time(),
                'ready_to_execute': False
            }

    def _real_ai_complete_function(self, signature: str, description: str = "") -> dict[str, Any]:
        """REAL AI function completion - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                prompt = f"Complete this Python function:\n{signature}\n# {description}"
                response = self.real_ai.ai_complete(prompt)
                return {
                    'signature': signature,
                    'description': description,
                    'complete_function': response.content,
                    'source': 'REAL_AI',
                    'cost_usd': response.cost_usd,
                    'tokens_used': response.tokens_used,
                    'timestamp': time.time()
                }
            except Exception as e:
                return {
                    'signature': signature,
                    'description': description,
                    'complete_function': f"# Real AI completion failed: {e}",
                    'source': 'error',
                    'error': str(e),
                    'timestamp': time.time()
                }
        else:
            return {
                'signature': signature,
                'description': description,
                'complete_function': "# Real AI not available - check configuration",
                'source': 'error',
                'timestamp': time.time()
            }

    def _real_ai_explain_code(self, code: str, level: str = "intermediate") -> dict[str, Any]:
        """REAL AI code explanation - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_explain(code, level)
                return {
                    'code': code,
                    'explanation': response.content,
                    'level': level,
                    'source': 'REAL_AI',
                    'cost_usd': response.cost_usd,
                    'tokens_used': response.tokens_used,
                    'timestamp': time.time()
                }
            except Exception as e:
                return {
                    'code': code,
                    'explanation': f"Real AI explanation failed: {e}",
                    'level': level,
                    'source': 'error',
                    'error': str(e),
                    'timestamp': time.time()
                }
        else:
            return {
                'code': code,
                'explanation': "Real AI not available - check configuration",
                'level': level,
                'source': 'error',
                'timestamp': time.time()
            }

    def _real_ai_suggest_improvements(self, code: str) -> dict[str, Any]:
        """REAL AI code improvement suggestions - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                prompt = f"Suggest improvements for this Python code:\n{code}"
                response = self.real_ai.ai_complete(prompt)
                return {
                    'original_code': code,
                    'suggestions': response.content,
                    'source': 'REAL_AI',
                    'cost_usd': response.cost_usd,
                    'tokens_used': response.tokens_used,
                    'timestamp': time.time()
                }
            except Exception as e:
                return {
                    'original_code': code,
                    'suggestions': f"Real AI suggestions failed: {e}",
                    'source': 'error',
                    'error': str(e),
                    'timestamp': time.time()
                }
        else:
            return {
                'original_code': code,
                'suggestions': "Real AI not available - check configuration",
                'source': 'error',
                'timestamp': time.time()
            }

    # Week 2: Advanced AI Programming Constructs
    def _real_ai_reason(self, problem: str, steps: int = 3) -> str:
        """REAL AI multi-step reasoning - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_reason(problem, steps)
                return str(response)
            except Exception as e:
                return f"AI reasoning failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_refactor(self, code: str, goal: str = "optimize") -> str:
        """REAL AI code refactoring - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_refactor(code, goal)
                return str(response)
            except Exception as e:
                return f"AI refactoring failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_test(self, function: str, test_type: str = "unit") -> str:
        """REAL AI test generation - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_test(function, test_type)
                return str(response)
            except Exception as e:
                return f"AI test generation failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_analyze(self, code: str, focus: str = "quality") -> str:
        """REAL AI code analysis - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_analyze(code, focus)
                return str(response)
            except Exception as e:
                return f"AI analysis failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_generate(self, specification: str,
                          language: str = "python") -> str:
        """REAL AI spec-to-code generation - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_generate(specification, language)
                return str(response)
            except Exception as e:
                return f"AI generation failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_simplify(self, text: str) -> str:
        """REAL AI text simplification - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_simplify(text)
                return str(response)
            except Exception as e:
                return f"AI simplification failed: {e}"
        else:
            return "Real AI not available - check configuration"

    # Week 3: AI-Enhanced Development Environment Integration
    def _real_ai_context(self, code: str, file_path: str = "") -> str:
        """REAL AI code context understanding - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_context(code, file_path)
                return str(response)
            except Exception as e:
                return f"AI context analysis failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_suggest(self, code: str, cursor_position: int = 0) -> str:
        """REAL AI code suggestions - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_suggest(code, cursor_position)
                return str(response)
            except Exception as e:
                return f"AI suggestions failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_document(self, code: str, style: str = "google") -> str:
        """REAL AI documentation generation - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_document(code, style)
                return str(response)
            except Exception as e:
                return f"AI documentation failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_optimize(self, code: str, focus: str = "performance") -> str:
        """REAL AI optimization recommendations - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_optimize(code, focus)
                return str(response)
            except Exception as e:
                return f"AI optimization failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_security(self, code: str, framework: str = "general") -> str:
        """REAL AI security analysis - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_security(code, framework)
                return str(response)
            except Exception as e:
                return f"AI security analysis failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_mentor(self, question: str, level: str = "beginner") -> str:
        """REAL AI mentoring assistance - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_mentor(question, level)
                return str(response)
            except Exception as e:
                return f"AI mentoring failed: {e}"
        else:
            return "Real AI not available - check configuration"

    # EXISTING MOCK METHODS (TO BE REPLACED COMPLETELY)
        """AI-powered code generation from natural language description"""
        try:
            # Use GPT-2 through cognitive assistant if available
            if hasattr(self.cognitive_assistant, 'gpt2') and \
               self.cognitive_assistant.gpt2:
                prompt = f"Generate Python code for: {description}\n\n# Code:"
                generated_code = self.cognitive_assistant.gpt2.\
                    generate_completion(prompt, max_new_tokens=100,
                                        temperature=0.3)

                # Ensure generated_code is a string
                if isinstance(generated_code, list):
                    generated_code = ' '.join(str(x) for x in generated_code)
                elif not isinstance(generated_code, str):
                    generated_code = str(generated_code)

                # Clean up the generated code
                lines = generated_code.split('\n')
                code_lines = []
                for line in lines:
                    if line.strip() and not line.strip().startswith('#'):
                        code_lines.append(line)
                    if len(code_lines) >= 10:  # Limit output length
                        break

                generated_code = '\n'.join(code_lines)
            else:
                # Fallback for when AI is not available
                generated_code = f"# Generated code for: {description}\n" \
                                 f"# TODO: Implement {description.lower()}\n" \
                                 f"pass"

            return {
                'description': description,
                'generated_code': generated_code,
                'source': 'AI' if hasattr(self.cognitive_assistant, 'gpt2')
                          else 'template',
                'timestamp': time.time(),
                'ready_to_execute': True
            }

        except Exception as e:
            return {
                'description': description,
                'generated_code': f"# Error generating code: {e}\n# TODO: "
                                  f"Implement {description}",
                'source': 'error',
                'error': str(e),
                'timestamp': time.time(),
                'ready_to_execute': False
            }

    def _ai_complete_function(self, signature: str,
                              description: str = "") -> dict[str, Any]:
        """AI-powered function completion"""
        try:
            if hasattr(self.cognitive_assistant, 'gpt2') and \
               self.cognitive_assistant.gpt2:
                prompt = f"Complete this Python function:\n{signature}\n" \
                        f"    # {description}\n    "
                completion = self.cognitive_assistant.gpt2.\
                    generate_completion(prompt, max_new_tokens=80,
                                        temperature=0.2)

                # Ensure completion is a string
                if isinstance(completion, list):
                    completion = ' '.join(str(x) for x in completion)
                elif not isinstance(completion, str):
                    completion = str(completion)

                # Clean and format the completion
                lines = completion.split('\n')
                body_lines = []
                for line in lines:
                    if line.strip():
                        body_lines.append(f"    {line.strip()}")
                    if len(body_lines) >= 8:
                        break

                complete_function = f"{signature}\n" + '\n'.join(body_lines)
            else:
                complete_function = f"{signature}\n    # {description}\n" \
                                   f"    # TODO: Implement function body\n" \
                                   f"    pass"

            return {
                'signature': signature,
                'description': description,
                'complete_function': complete_function,
                'source': 'AI' if hasattr(self.cognitive_assistant, 'gpt2')
                          else 'template',
                'timestamp': time.time()
            }

        except Exception as e:
            return {
                'signature': signature,
                'description': description,
                'complete_function': f"{signature}\n    # Error: {e}\n"
                                     f"    pass",
                'source': 'error',
                'error': str(e),
                'timestamp': time.time()
            }

    def _ai_explain_code(self, code: str) -> dict[str, Any]:
        """AI-powered code explanation in natural language"""
        try:
            if hasattr(self.cognitive_assistant, 'gpt2') and \
               self.cognitive_assistant.gpt2:
                prompt = f"Explain this Python code in simple terms:\n\n" \
                        f"{code}\n\nExplanation:"
                explanation = self.cognitive_assistant.gpt2.\
                    generate_completion(prompt, max_new_tokens=80,
                                        temperature=0.3)

                # Ensure explanation is a string
                if isinstance(explanation, list):
                    explanation = ' '.join(str(x) for x in explanation)
                elif not isinstance(explanation, str):
                    explanation = str(explanation)

                # Clean up explanation
                explanation = explanation.strip()
                if len(explanation) > 200:
                    explanation = explanation[:200] + "..."
            else:
                # Simple pattern-based explanation for fallback
                lines = code.split('\n')
                elements = []
                for line in lines:
                    line = line.strip()
                    if line.startswith('def '):
                        elements.append("defines a function")
                    elif line.startswith('for '):
                        elements.append("loops through items")
                    elif line.startswith('if '):
                        elements.append("checks a condition")
                    elif '=' in line and not line.startswith('#'):
                        elements.append("assigns a value")

                explanation = f"This code {', '.join(elements[:3])}"
                if len(elements) > 3:
                    explanation += " and more"
                explanation += "."

            return {
                'code': code,
                'explanation': explanation,
                'source': 'AI' if hasattr(self.cognitive_assistant, 'gpt2')
                          else 'pattern',
                'timestamp': time.time(),
                'clarity_level': 'beginner'
            }

        except Exception as e:
            return {
                'code': code,
                'explanation': f"Unable to explain code: {e}",
                'source': 'error',
                'error': str(e),
                'timestamp': time.time(),
                'clarity_level': 'unknown'
            }

    def _ai_suggest_improvements(self, code: str) -> dict[str, Any]:
        """AI-powered code improvement suggestions"""
        try:
            suggestions = []

            # Basic pattern-based suggestions (always available)
            lines = code.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if len(line) > 100:
                    suggestions.append(f"Line {i+1}: Consider breaking "
                                     f"long line for readability")
                if 'TODO' in line or 'FIXME' in line:
                    suggestions.append(f"Line {i+1}: Complete the TODO item")
                if line.count('(') != line.count(')'):
                    suggestions.append(f"Line {i+1}: Check parentheses "
                                     f"balance")

            # AI-powered suggestions if available
            if hasattr(self.cognitive_assistant, 'gpt2') and \
               self.cognitive_assistant.gpt2:
                prompt = f"Suggest improvements for this Python code:\n\n" \
                        f"{code}\n\nSuggestions:"
                ai_suggestions = self.cognitive_assistant.gpt2.\
                    generate_completion(prompt, max_new_tokens=60,
                                        temperature=0.4)

                # Ensure ai_suggestions is a string
                if isinstance(ai_suggestions, list):
                    ai_suggestions = ' '.join(str(x) for x in ai_suggestions)
                elif not isinstance(ai_suggestions, str):
                    ai_suggestions = str(ai_suggestions)

                # Parse AI suggestions
                ai_lines = ai_suggestions.strip().split('\n')
                for line in ai_lines[:3]:  # Limit to 3 AI suggestions
                    if line.strip() and len(line.strip()) > 10:
                        suggestions.append(f"AI: {line.strip()}")

            return {
                'code': code,
                'suggestions': suggestions[:5],  # Limit total suggestions
                'improvement_areas': ['readability', 'performance', 'style'],
                'source': 'hybrid',
                'timestamp': time.time(),
                'priority': 'medium'
            }

        except Exception as e:
            return {
                'code': code,
                'suggestions': [f"Error analyzing code: {e}"],
                'improvement_areas': ['unknown'],
                'source': 'error',
                'error': str(e),
                'timestamp': time.time(),
                'priority': 'low'
            }

    # Cognitive Programming Constructs (Day 3B)

    def _cognitive_when_confused(self, explanation: str) -> dict[str, Any]:
        """Cognitive clarity assistance when confused"""
        try:
            clarity_response = {
                'confusion_noted': explanation,
                'timestamp': time.time(),
                'assistance_provided': [],
                'next_steps': []
            }

            # Analyze the confusion and provide assistance
            if hasattr(self.cognitive_assistant, 'gpt2') and \
               self.cognitive_assistant.gpt2:
                prompt = f"Help clarify this programming confusion: " \
                        f"{explanation}\n\nClarification:"
                clarification = self.cognitive_assistant.gpt2.\
                    generate_completion(prompt, max_new_tokens=60,
                                        temperature=0.3)
                clarity_response['assistance_provided'].append(
                    f"AI: {clarification.strip()}")

            # Provide structured next steps
            clarity_response['next_steps'] = [
                "Break down the problem into smaller parts",
                "Look for examples of similar code patterns",
                "Try explaining the problem out loud",
                "Consider asking for help or reviewing documentation"
            ]

            # Log confusion for learning
            confusion_key = f"_confusion_{int(time.time())}"
            self.memory.set_variable(confusion_key, {
                'explanation': explanation,
                'timestamp': time.time(),
                'context': self.current_context
            }, global_scope=True)

            return clarity_response

        except Exception as e:
            return {
                'confusion_noted': explanation,
                'assistance_provided': [f"Error providing assistance: {e}"],
                'next_steps': ["Try a different approach", "Seek help"],
                'timestamp': time.time(),
                'error': str(e)
            }

    def _cognitive_break_if_overwhelmed(self) -> dict[str, Any]:
        """Automatic cognitive load management and break suggestion"""
        try:
            # Analyze current cognitive load
            load_analysis = self._cognitive_analyze_load()

            current_load = load_analysis['cognitive_load']
            session_duration = load_analysis['session_metrics']['duration']

            # Determine if a break is needed
            break_needed = False
            break_reason = ""

            if current_load in ['high', 'very_high']:
                break_needed = True
                break_reason = "High cognitive load detected"
            elif session_duration > 3600:  # 1 hour
                break_needed = True
                break_reason = "Long session duration"
            elif len(self.memory.global_scope) > 50:
                break_needed = True
                break_reason = "High memory complexity"

            response = {
                'break_recommended': break_needed,
                'reason': break_reason,
                'current_load': current_load,
                'session_duration_minutes': session_duration / 60,
                'timestamp': time.time()
            }

            if break_needed:
                # Get break suggestions from cognitive assistant
                break_suggestions = self.cognitive_assistant.\
                    suggest_break_activity(current_load)
                response['break_suggestions'] = break_suggestions
                response['recommended_break_duration'] = \
                    break_suggestions.get('recommended_duration', 15)

                print(f"🧠 Break recommended: {break_reason}")
                activities = break_suggestions.get('suggested_activities', [])
                print(f"💡 Suggested activities: {', '.join(activities[:2])}")

            return response

        except Exception as e:
            return {
                'break_recommended': True,
                'reason': f"Error analyzing load: {e}",
                'break_suggestions': {
                    'suggested_activities': ['Take a short break']
                },
                'timestamp': time.time(),
                'error': str(e)
            }

    def _cognitive_simplify_task(self,
                                 complex_operation: str) -> dict[str, Any]:
        """AI-powered task decomposition and simplification"""
        try:
            simplified_response = {
                'original_task': complex_operation,
                'simplified_steps': [],
                'estimated_time': 0,
                'complexity_reduction': 'medium',
                'timestamp': time.time()
            }

            # Use cognitive assistant for task breakdown
            try:
                breakdown = self.cognitive_assistant.\
                    analyze_executive_function(complex_operation)
                simplified_response['simplified_steps'] = \
                    breakdown.get('task_breakdown', [])
                simplified_response['estimated_time'] = \
                    breakdown.get('estimated_time', 30)
                simplified_response['support_strategies'] = \
                    breakdown.get('support_strategies', [])
            except Exception:
                # Fallback to pattern-based simplification
                steps = []
                if 'function' in complex_operation.lower():
                    steps.extend([
                        "1. Define function signature",
                        "2. Write basic structure",
                        "3. Implement core logic",
                        "4. Add error handling",
                        "5. Test the function"
                    ])
                elif 'class' in complex_operation.lower():
                    steps.extend([
                        "1. Define class structure",
                        "2. Add __init__ method",
                        "3. Implement core methods",
                        "4. Add properties if needed",
                        "5. Test the class"
                    ])
                else:
                    steps.extend([
                        "1. Understand the requirements",
                        "2. Break into smaller parts",
                        "3. Implement each part",
                        "4. Combine and test",
                        "5. Refactor if needed"
                    ])

                simplified_response['simplified_steps'] = steps
                simplified_response['estimated_time'] = len(steps) * 10

            return simplified_response

        except Exception as e:
            return {
                'original_task': complex_operation,
                'simplified_steps': [
                    "1. Break down the problem",
                    "2. Start with the simplest part",
                    f"3. Handle error: {e}"
                ],
                'estimated_time': 20,
                'timestamp': time.time(),
                'error': str(e)
            }

    def _cognitive_review_progress(self) -> dict[str, Any]:
        """Review session progress and provide insights"""
        try:
            session_duration = time.time() - self.session_start_time

            # Gather session statistics
            stats = {
                'session_duration_minutes': session_duration / 60,
                'variables_created': len(self.memory.global_scope),
                'functions_defined': len(self.functions),
                'current_scope_depth': len(self.memory.local_scopes),
                'cognitive_memories': len([k for k in self.memory.global_scope
                                            if k.startswith('_cognitive_memory_')]),
                'confusion_instances': len([k for k in self.memory.global_scope
                                             if k.startswith('_confusion_')])
            }

            # Generate insights
            insights = []
            if stats['session_duration_minutes'] > 60:
                insights.append("Long productive session - consider a break soon")
            if stats['functions_defined'] > 3:
                insights.append("Good function organization!")
            if stats['cognitive_memories'] > 0:
                insights.append(f"Stored {stats['cognitive_memories']} insights")
            if stats['confusion_instances'] == 0:
                insights.append("Clear coding session - great focus!")
            elif stats['confusion_instances'] > 3:
                insights.append("Several confusion points - consider simpler approach")

            # AI-powered insights if available
            if hasattr(self.cognitive_assistant, 'gpt2') and \
               self.cognitive_assistant.gpt2:
                prompt = f"Generate programming session insight for: " \
                        f"{stats['session_duration_minutes']:.1f} min session, " \
                        f"{stats['functions_defined']} functions, " \
                        f"{stats['variables_created']} variables\n\nInsight:"
                ai_insight = self.cognitive_assistant.gpt2.\
                    generate_completion(prompt, max_new_tokens=40,
                                        temperature=0.4)
                if ai_insight.strip():
                    insights.append(f"AI: {ai_insight.strip()}")

            return {
                'session_stats': stats,
                'insights': insights,
                'productivity_score': min(10, stats['functions_defined'] * 2 +
                                        stats['variables_created'] * 0.1),
                'learning_progress': 'steady' if stats['confusion_instances'] < 3
                                   else 'challenging',
                'timestamp': time.time(),
                'next_session_tips': [
                    "Set clear goals at the start",
                    "Take breaks when cognitive load is high",
                    "Use the think() function for complex problems"
                ]
            }

        except Exception as e:
            return {
                'session_stats': {'error': str(e)},
                'insights': [f"Error reviewing progress: {e}"],
                'productivity_score': 0,
                'timestamp': time.time(),
                'error': str(e)
            }

    # Day 3C: Advanced AI Constructs
    def _ai_adaptive_learning(self, feedback: str) -> dict[str, Any]:
        """AI-powered adaptive learning from user feedback"""
        try:
            from advanced_ai.adaptive_learning import AdaptiveLearning
            adaptive_learning = AdaptiveLearning(self.cognitive_assistant)
            return adaptive_learning.learn_from_feedback(feedback)
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Adaptive learning error: {str(e)}',
                'fallback_action': 'feedback_noted'
            }

    def _ai_meta_cognition(self,
                           task_description: str = "current_task") -> dict[str, Any]:
        """AI-powered meta-cognitive self-assessment"""
        try:
            from advanced_ai.meta_cognition import MetaCognition
            meta_cognition = MetaCognition(self.cognitive_assistant)
            return meta_cognition.self_assess(task_description)
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Meta-cognition error: {str(e)}',
                'fallback_assessment': 'self_reflection_needed'
            }

    def _ai_dynamic_context_switching(self, new_context: str) -> dict[str, Any]:
        """AI-powered dynamic context switching"""
        try:
            from advanced_ai.dynamic_context_switching import (
                DynamicContextSwitching,
            )
            context_switcher = DynamicContextSwitching(self.cognitive_assistant)
            old_context = self.current_context
            result = context_switcher.switch_context(old_context, new_context)
            if result.get('status') == 'success':
                self.current_context = new_context
            return result
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Context switching error: {str(e)}',
                'current_context': self.current_context
            }

    def _ai_multi_step_reasoning(self, problem_description: str) -> dict[str, Any]:
        """AI-powered multi-step problem reasoning"""
        try:
            from advanced_ai.multi_step_reasoning import MultiStepReasoning
            reasoner = MultiStepReasoning(self.cognitive_assistant)
            return reasoner.solve_problem(problem_description)
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Multi-step reasoning error: {str(e)}',
                'fallback_approach': 'break_problem_manually'
            }


# Create a default interpreter instance for convenience
default_interpreter = SonaUnifiedInterpreter()

# Alias for backward compatibility
SonaInterpreter = SonaUnifiedInterpreter

# Export the main classes and functions
__all__ = [
    'SonaInterpreter',
    'SonaUnifiedInterpreter',
    'SonaFunction',
    'SonaMemoryManager',
    'SonaRuntimeError',
    'default_interpreter'
]
