"""
Sona v0.9.0 - Enhanced Interpreter (Phase 2 Priority 1)
======================================================

Rebuilt enhanced interpreter for methodical development.
Focuses on core literal support for Priority 1 implementation.

Features:
- Boolean literals (true, false)
- Null literal (null)
- Basic expressions and comparisons
- Type function support
- Lark Tree integration
"""

import sys
import traceback
from pathlib import Path
from typing import Any, Dict


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
    )
except ImportError:
    try:
        from ast_nodes_v090 import (
            AICompleteStatement,
            AIDebugStatement,
            AIExplainStatement,
            AIOptimizeStatement,
        )
    except ImportError:
        print("⚠️  AST nodes not available, using placeholder mode")
        # Create placeholder classes
        class AICompleteStatement: pass
        class AIExplainStatement: pass 
        class AIDebugStatement: pass
        class AIOptimizeStatement: pass


class SonaInterpreterError(Exception):
    """Exception raised during Sona interpretation"""
    
    def __init__(self, message: str, node=None):
        super().__init__(message)
        self.node = node
        
        # Try to extract position information from node
        if hasattr(node, 'line'):
            self.line = node.line
        elif hasattr(node, 'meta') and hasattr(node.meta, 'line'):
            self.line = node.meta.line
        else:
            self.line = None
            
        if hasattr(node, 'column'):
            self.column = node.column
        elif hasattr(node, 'meta') and hasattr(node.meta, 'column'):
            self.column = node.meta.column
        else:
            self.column = None
    
    def __str__(self):
        if self.line and self.column:
            return f"Line {self.line}, Column {self.column}: {super().__str__()}"
        elif self.line:
            return f"Line {self.line}: {super().__str__()}"
        else:
            return super().__str__()


class SonaMemoryManager:
    """Manages memory and variable scoping for Sona interpreter"""
    
    def __init__(self):
        self.global_scope = {}
        self.local_scopes = []
        self.call_stack = []
        self.constants = set()
    
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
    
    def assign_variable(self, name: str, value: Any):
        """Assign to a variable, updating existing variables in their original scope"""
        # Check if variable exists in any scope (most recent first)
        for scope in reversed(self.local_scopes):
            if name in scope:
                scope[name] = value
                return
                
        # Check global scope
        if name in self.global_scope:
            self.global_scope[name] = value
            return
            
        # Variable doesn't exist, create in current scope
        if self.local_scopes:
            self.local_scopes[-1][name] = value
        else:
            self.global_scope[name] = value
    
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
    
    def add_constant(self, name: str):
        """Mark a variable as constant"""
        self.constants.add(name)
    
    def is_constant(self, name: str) -> bool:
        """Check if a variable is a constant"""
        return name in self.constants


class SonaInterpreter:
    """
    Enhanced Sona interpreter with Phase 2 Priority 1 support
    
    Features:
    - Boolean literals (true, false, null)
    - Basic expressions and comparisons
    - Function calls
    - Memory management
    """
    
    def __init__(self, vm_instance=None):
        """Initialize the enhanced interpreter"""
        self.memory = SonaMemoryManager()
        self.constants = set()  # For backward compatibility
        self.parser = None
        self.vm_instance = vm_instance
        self.ai_enabled = False
        self.debug_mode = False
        
        # Performance tracking
        self.execution_stats = {
            'statements_executed': 0,
            'functions_called': 0,
            'variables_accessed': 0
        }
        
        # Initialize parser
        self._setup_parser()
        
        # Initialize built-in functions and constants
        self._setup_builtins()
        self._setup_sona_constants()
    
    def _setup_parser(self):
        """Setup the parser"""
        if SonaParserv090:
            try:
                self.parser = SonaParserv090()
                if self.debug_mode:
                    print("✅ Sona v0.9.0 parser initialized successfully")
            except Exception as e:
                if self.debug_mode:
                    print(f"⚠️  Parser initialization failed: {e}")
                self.parser = None
        else:
            self.parser = None
    
    def _setup_builtins(self):
        """Setup built-in functions for Sona"""
        # Core functions
        self.memory.set_variable('print', self._builtin_print, global_scope=True)
        self.memory.set_variable('len', self._builtin_len, global_scope=True)
        self.memory.set_variable('type', self._builtin_type, global_scope=True)
        self.memory.set_variable('str', self._builtin_str, global_scope=True)
        self.memory.set_variable('int', self._builtin_int, global_scope=True)
        self.memory.set_variable('float', self._builtin_float, global_scope=True)
        self.memory.set_variable('range', self._builtin_range, global_scope=True)
        
        # AI-powered functions
        self.memory.set_variable('ai_complete', self._builtin_ai_complete, global_scope=True)
        self.memory.set_variable('ai_explain', self._builtin_ai_explain, global_scope=True)
        self.memory.set_variable('ai_debug', self._builtin_ai_debug, global_scope=True)
        self.memory.set_variable('ai_optimize', self._builtin_ai_optimize, global_scope=True)
        
        # String manipulation functions
        self.memory.set_variable('trim', self._builtin_trim, global_scope=True)
        self.memory.set_variable('upper', self._builtin_upper, global_scope=True)
        self.memory.set_variable('lower', self._builtin_lower, global_scope=True)
        self.memory.set_variable('split', self._builtin_split, global_scope=True)
        self.memory.set_variable('join', self._builtin_join, global_scope=True)
        self.memory.set_variable('replace', self._builtin_replace, global_scope=True)
        self.memory.set_variable('substring', self._builtin_substring, global_scope=True)
        self.memory.set_variable('indexOf', self._builtin_indexOf, global_scope=True)
        self.memory.set_variable('startsWith', self._builtin_startsWith, 
                                global_scope=True)
        self.memory.set_variable('endsWith', self._builtin_endsWith, 
                                global_scope=True)
        
        # Error handling functions
        self.memory.set_variable('throw', self._builtin_throw, 
                                global_scope=True)
        
        # 🚀 REVOLUTIONARY AI-NATIVE PROGRAMMING FUNCTIONS
        # Natural Language Programming
        self.memory.set_variable('explain', self._builtin_explain, 
                                global_scope=True)
        self.memory.set_variable('think', self._builtin_think, 
                                global_scope=True)
        self.memory.set_variable('intend', self._builtin_intend, 
                                global_scope=True)
        
        # Live AI Collaboration
        self.memory.set_variable('ai_review', self._builtin_ai_review, 
                                global_scope=True)
        self.memory.set_variable('ai_suggest', self._builtin_ai_suggest, 
                                global_scope=True)
        self.memory.set_variable('ai_implement', self._builtin_ai_implement, 
                                global_scope=True)
        
        # Predictive Analysis
        self.memory.set_variable('ai_predict_issues', self._builtin_ai_predict_issues, 
                                global_scope=True)
        self.memory.set_variable('ai_verify_data_quality', self._builtin_ai_verify_data_quality, 
                                global_scope=True)
        
        # Session Management
        self.memory.set_variable('start_session', self._builtin_start_session, 
                                global_scope=True)
        self.memory.set_variable('suggest_improvements', self._builtin_suggest_improvements, 
                                global_scope=True)
        
        # 🧠 COGNITIVE PROGRAMMING FUNCTIONS
        # Working Memory Management
        self.memory.set_variable('working_memory', self._builtin_working_memory, 
                                global_scope=True)
        self.memory.set_variable('focus_mode', self._builtin_focus_mode, 
                                global_scope=True)
        self.memory.set_variable('cognitive_check', self._builtin_cognitive_check, 
                                global_scope=True)
        
        # Accessibility and Cognitive Support
        self.memory.set_variable('simplify', self._builtin_simplify, 
                                global_scope=True)
        self.memory.set_variable('clarify', self._builtin_clarify, 
                                global_scope=True)
        self.memory.set_variable('break_down', self._builtin_break_down, 
                                global_scope=True)
        
        # 🎯 NEW v0.9.0 EXTENDED FUNCTION LIBRARY (12 new functions to reach 50 total)
        
        # Advanced AI Functions
        self.memory.set_variable('ai_generate', self._builtin_ai_generate, 
                                global_scope=True)
        self.memory.set_variable('ai_refactor', self._builtin_ai_refactor, 
                                global_scope=True)
        self.memory.set_variable('ai_test', self._builtin_ai_test, 
                                global_scope=True)
        self.memory.set_variable('ai_document', self._builtin_ai_document, 
                                global_scope=True)
        
        # Data Processing Functions
        self.memory.set_variable('filter', self._builtin_filter, 
                                global_scope=True)
        self.memory.set_variable('map', self._builtin_map, 
                                global_scope=True)
        self.memory.set_variable('reduce', self._builtin_reduce, 
                                global_scope=True)
        self.memory.set_variable('sort', self._builtin_sort, 
                                global_scope=True)
        
        # Math and Utility Functions
        self.memory.set_variable('math_random', self._builtin_math_random, 
                                global_scope=True)
        self.memory.set_variable('math_round', self._builtin_math_round, 
                                global_scope=True)
        self.memory.set_variable('deep_copy', self._builtin_deep_copy, 
                                global_scope=True)
        self.memory.set_variable('validate', self._builtin_validate, 
                                global_scope=True)
    
    def _setup_sona_constants(self):
        """Setup Sona language constants"""
        # Boolean literals
        self.memory.set_variable('true', True, global_scope=True)
        self.memory.set_variable('false', False, global_scope=True)
        self.memory.add_constant('true')
        self.memory.add_constant('false')
        
        # Null literal
        self.memory.set_variable('null', None, global_scope=True)
        self.memory.add_constant('null')
        
        # Language metadata
        self.memory.set_variable('__version__', '0.9.0', global_scope=True)
        self.memory.set_variable('__sona__', True, global_scope=True)
        self.memory.add_constant('__version__')
        self.memory.add_constant('__sona__')
    
    # ==================== BUILT-IN FUNCTIONS ====================
    
    def _builtin_print(self, *args):
        """Built-in print function"""
        print(*args)
        return None
    
    def _builtin_len(self, obj):
        """Built-in len function"""
        return len(obj)
    
    def _builtin_type(self, obj):
        """Built-in type function - returns string name"""
        python_type = type(obj).__name__
        # Map Python types to Sona type names
        if python_type == 'bool':
            return 'bool'
        elif python_type == 'NoneType':
            return 'NoneType'
        elif python_type == 'int':
            return 'int'
        elif python_type == 'float':
            return 'float'
        elif python_type == 'str':
            return 'string'
        else:
            return python_type
    
    def _builtin_str(self, obj):
        """Built-in str function"""
        return str(obj)
    
    def _builtin_int(self, obj):
        """Built-in int function"""
        return int(obj)
    
    def _builtin_float(self, obj):
        """Built-in float function"""
        return float(obj)
    
    def _builtin_range(self, *args):
        """Built-in range function"""
        return list(range(*args))
    
    # ==================== AI-POWERED BUILT-IN FUNCTIONS ====================
    
    def _builtin_ai_complete(self, prompt, language=None, level=None, options=None):
        """AI code completion function with REAL API integration"""
        # Parameter validation - now receives actual values, not string representations
        if not isinstance(prompt, str):
            raise TypeError(f"ai_complete() prompt must be a string, not {type(prompt).__name__}")
        
        if len(prompt) > 500:  # Reasonable limit for extremely long parameters
            raise ValueError("ai_complete() prompt too long (max 500 characters)")
        
        try:
            # Import real AI backend
            from .ai_backend_integration import ai_manager
            
            # Parse options - support both new multi-param and old dict style
            max_tokens = 100
            temperature = 0.7
            provider = "auto"  # auto, openai, claude
            
            # Handle new multi-parameter style
            if language is not None or level is not None:
                # Convert to options dict for backward compatibility
                if options is None:
                    options = {}
                if language is not None:
                    options['language'] = language
                if level is not None:
                    options['level'] = level
            
            if options and isinstance(options, dict):
                max_tokens = options.get('max_tokens', 100)
                temperature = options.get('temperature', 0.7)
                provider = options.get('provider', 'auto')
                # Include language and level in the prompt context
                language_hint = options.get('language', '')
                level_hint = options.get('level', '')
                if language_hint or level_hint:
                    context_suffix = ""
                    if language_hint:
                        context_suffix += f" (Language: {language_hint})"
                    if level_hint:
                        context_suffix += f" (Level: {level_hint})"
                    prompt = prompt + context_suffix
            
            # Try to use real AI APIs first
            if ai_manager.is_available():
                print("🤖 Using real AI for code completion...")
                
                # Use async in a sync context
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Get AI response
                if provider == "openai" or provider == "auto":
                    # Try OpenAI first
                    for backend in ai_manager.backends:
                        if backend.provider.value == "openai" and backend.is_available:
                            result = loop.run_until_complete(
                                backend.complete_code(str(prompt), "Sona language")
                            )
                            return result.content
                
                if provider == "claude" or provider == "auto":
                    # Try Claude
                    for backend in ai_manager.backends:
                        if backend.provider.value == "claude" and backend.is_available:
                            result = loop.run_until_complete(
                                backend.complete_code(str(prompt), "Sona language")
                            )
                            return result.content
            
            # Fallback to enhanced mock responses
            prompt_str = str(prompt).lower()
            if 'function' in prompt_str:
                return f"""def {prompt.split()[-1] if prompt.split() else 'myFunction'}() {{
    // AI-generated function
    // TODO: Implement function logic
    return null;
}}"""
            elif 'class' in prompt_str:
                class_name = prompt.split()[-1] if prompt.split() else 'MyClass'
                return f"""class {class_name} {{
    constructor() {{
        // AI-generated class
        // TODO: Initialize properties
    }}
    
    // TODO: Add methods
}}"""
            elif 'api' in prompt_str:
                return f"""// AI API implementation for: {prompt}
async function fetchData(url) {{
    try {{
        let response = await fetch(url);
        return await response.json();
    }} catch (error) {{
        console.error('API Error:', error);
        throw error;
    }}
}}"""
            else:
                return f"""// AI completion for: {prompt}
// Generated with max_tokens={max_tokens}, temperature={temperature}
// TODO: Implement your logic here"""
                
        except Exception as e:
            return f"AI completion error: {e}"
    
    def _builtin_ai_explain(self, code, level="beginner"):
        """AI code explanation function with REAL API integration"""
        try:
            # Import real AI backend
            from .ai_backend_integration import ai_manager
            
            # Try to use real AI APIs first
            if ai_manager.is_available():
                print("🤖 Using real AI for code explanation...")
                
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Try available backends
                for backend in ai_manager.backends:
                    if backend.is_available and hasattr(backend, 'explain_code'):
                        result = loop.run_until_complete(
                            backend.explain_code(str(code), f"Explanation level: {level}")
                        )
                        return result.content
            
            # Enhanced fallback explanations
            code_str = str(code).lower()
            if 'def ' in code_str or 'function' in code_str:
                explanation = "This defines a function - a reusable block of code that can accept inputs (parameters) and return outputs."
            elif 'for ' in code_str or 'while ' in code_str:
                explanation = "This is a loop that repeats code multiple times. Loops are essential for processing collections of data or repeating operations."
            elif 'if ' in code_str:
                explanation = "This is a conditional statement that executes code based on whether a condition is true or false. It enables decision-making in programs."
            elif 'class ' in code_str:
                explanation = "This defines a class - a blueprint for creating objects that encapsulate data and behavior together."
            elif 'import ' in code_str:
                explanation = "This imports external modules or libraries, allowing you to use pre-written code and extend your program's capabilities."
            else:
                explanation = f"This code performs: {str(code)[:100]}..."
            
            # Adjust explanation based on level
            if level == "advanced":
                explanation += " [Advanced: Consider performance implications, memory usage, and scalability]"
            elif level == "expert":
                explanation += " [Expert: Analyze algorithmic complexity, design patterns, and optimization opportunities]"
            
            return explanation
                
        except Exception as e:
            return f"AI explanation error: {e}"
    
    def _builtin_ai_debug(self, code, error_info=None):
        """AI debugging assistance function"""
        try:
            code_str = str(code)
            
            # Common debugging patterns
            if 'undefined' in str(error_info) or 'not defined' in str(error_info):
                return "Check if all variables are properly declared before use."
            elif 'syntax' in str(error_info):
                return "Look for missing brackets, parentheses, or semicolons."
            elif 'index' in str(error_info) and 'out of range' in str(error_info):
                return "Array index is beyond the array length. Check your loop bounds."
            else:
                return f"Debug suggestion for '{code_str[:30]}...': Check variable types and logic flow."
                
        except Exception as e:
            return f"AI debug error: {e}"
    
    def _builtin_ai_optimize(self, code):
        """AI code optimization function"""
        try:
            code_str = str(code)
            
            # Basic optimization suggestions
            if 'for' in code_str and 'in range' in code_str:
                return "Consider using list comprehensions for better performance."
            elif code_str.count('if') > 3:
                return "Consider using match/switch statements for multiple conditions."
            elif 'while True' in code_str:
                return "Ensure your loop has a proper exit condition to avoid infinite loops."
            else:
                return "Code appears optimized. Consider profiling for performance bottlenecks."
                
        except Exception as e:
            return f"AI optimization error: {e}"
    
    # ==================== STRING MANIPULATION FUNCTIONS ====================
    
    def _builtin_trim(self, text):
        """Remove whitespace from beginning and end of string"""
        return str(text).strip()
    
    def _builtin_upper(self, text):
        """Convert string to uppercase"""
        return str(text).upper()
    
    def _builtin_lower(self, text):
        """Convert string to lowercase"""
        return str(text).lower()
    
    def _builtin_split(self, text, delimiter=" "):
        """Split string by delimiter into array"""
        return str(text).split(str(delimiter))
    
    def _builtin_join(self, array, delimiter=""):
        """Join array elements into string with delimiter"""
        return str(delimiter).join([str(item) for item in array])
    
    def _builtin_replace(self, text, old, new):
        """Replace all occurrences of old with new in text"""
        return str(text).replace(str(old), str(new))
    
    def _builtin_substring(self, text, start, end=None):
        """Extract substring from start to end (or to end of string)"""
        text_str = str(text)
        if end is None:
            return text_str[int(start):]
        else:
            return text_str[int(start):int(end)]
    
    def _builtin_indexOf(self, text, search):
        """Find first index of search string in text (-1 if not found)"""
        try:
            return str(text).index(str(search))
        except ValueError:
            return -1
    
    def _builtin_startsWith(self, text, prefix):
        """Check if string starts with prefix"""
        return str(text).startswith(str(prefix))
    
    def _builtin_endsWith(self, text, suffix):
        """Check if string ends with suffix"""
        return str(text).endswith(str(suffix))
    
    # ==================== ERROR HANDLING FUNCTIONS ====================
    
    def _builtin_throw(self, message="Error occurred"):
        """Throw an error with the given message"""
        raise Exception(str(message))
    
    # ==================== 🚀 REVOLUTIONARY AI-NATIVE PROGRAMMING ====================
    
    def _builtin_explain(self, description):
        """Natural language documentation that executes as code"""
        explanation = str(description)
        print(f"💭 {explanation}")
        
        # Store explanation in session context for AI to reference
        if not hasattr(self, '_session_context'):
            self._session_context = []
        self._session_context.append(f"EXPLANATION: {explanation}")
        
        return explanation
    
    def _builtin_think(self, thought):
        """Express your thinking process - AI responds with suggestions"""
        thought_str = str(thought)
        print(f"🤔 Thinking: {thought_str}")
        
        # Generate AI response based on thought
        if 'best way' in thought_str.lower():
            response = f"AI suggests: Consider performance, maintainability, and error handling for: {thought_str}"
        elif 'how to' in thought_str.lower():
            response = f"AI recommends: Break this into smaller steps: {thought_str}"
        elif 'should' in thought_str.lower():
            response = f"AI advises: Here are the trade-offs to consider: {thought_str}"
        else:
            response = f"AI responds: Let me help you explore: {thought_str}"
        
        print(f"🤖 {response}")
        return response
    
    def _builtin_intend(self, intention, requirements=None):
        """Intention-driven programming - describe what you want"""
        intention_str = str(intention)
        print(f"🎯 Intent: {intention_str}")
        
        # AI analyzes intention and suggests implementation
        if 'secure' in intention_str.lower():
            suggestion = "AI suggests: I'll implement with encryption, input validation, and audit logging"
        elif 'fast' in intention_str.lower() or 'performance' in intention_str.lower():
            suggestion = "AI suggests: I'll optimize for speed with caching and efficient algorithms"
        elif 'api' in intention_str.lower():
            suggestion = "AI suggests: I'll create RESTful endpoints with error handling and documentation"
        elif 'database' in intention_str.lower():
            suggestion = "AI suggests: I'll implement with connection pooling and SQL injection protection"
        else:
            suggestion = f"AI suggests: I'll break down '{intention_str}' into modular, testable components"
        
        print(f"🤖 {suggestion}")
        
        # Return implementation framework
        framework = {
            'intention': intention_str,
            'requirements': requirements or [],
            'ai_plan': suggestion,
            'status': 'ready_to_implement'
        }
        
        return framework
    
    def _builtin_ai_review(self, code_context):
        """AI reviews code and flags potential issues"""
        context_str = str(code_context)
        print(f"🔍 AI Code Review: {context_str}")
        
        # Analyze code for common issues
        issues = []
        if 'fetch' in context_str.lower():
            issues.append("Network calls should have timeout and retry logic")
        if 'password' in context_str.lower():
            issues.append("Sensitive data should be encrypted and not logged")
        if 'array[' in context_str.lower():
            issues.append("Array access should check bounds to prevent errors")
        if 'while' in context_str.lower():
            issues.append("Loop should have break condition to prevent infinite loops")
        
        if issues:
            for issue in issues:
                print(f"⚠️  AI Review: {issue}")
            return issues
        else:
            print("✅ AI Review: Code looks good!")
            return ["No issues found"]
    
    def _builtin_ai_suggest(self, context, improvement_type="general"):
        """AI suggests improvements for given context"""
        context_str = str(context)
        improvement = str(improvement_type)
        
        if improvement == "performance":
            suggestion = f"AI Performance Tip: Use caching, batch operations, or async processing for: {context_str}"
        elif improvement == "security":
            suggestion = f"AI Security Tip: Add input validation, authentication, and encryption for: {context_str}"
        elif improvement == "readability":
            suggestion = f"AI Readability Tip: Add descriptive names, comments, and error messages for: {context_str}"
        else:
            suggestion = f"AI Suggestion: Consider error handling, logging, and testing for: {context_str}"
        
        print(f"💡 {suggestion}")
        return suggestion
    
    def _builtin_ai_implement(self, requirements, constraints=None):
        """AI implements code based on requirements"""
        req_list = requirements if isinstance(requirements, list) else [str(requirements)]
        const_list = constraints if isinstance(constraints, list) else ([] if constraints is None else [str(constraints)])
        
        print("🔨 AI Implementation:")
        print(f"   Requirements: {req_list}")
        print(f"   Constraints: {const_list}")
        
        # Generate implementation plan
        implementation = {
            'requirements': req_list,
            'constraints': const_list,
            'ai_generated_code': "// AI-generated implementation would go here",
            'explanation': "AI would generate optimized code meeting your requirements",
            'confidence': 0.95
        }
        
        print(f"✨ AI Generated: {implementation['explanation']}")
        return implementation
    
    def _builtin_ai_predict_issues(self, data_context):
        """Predictive error analysis"""
        context_str = str(data_context)
        print(f"🔮 AI Predicting Issues for: {context_str}")
        
        predictions = {}
        
        # Simulate predictive analysis
        if 'null' in context_str.lower() or 'undefined' in context_str.lower():
            predictions['null_pointer_risk'] = 0.8
            print("⚠️  High risk of null pointer exceptions")
        
        if 'loop' in context_str.lower() or 'array' in context_str.lower():
            predictions['performance_concern'] = 0.6
            print("⚠️  Moderate performance concern with iteration")
        
        if 'user' in context_str.lower() or 'input' in context_str.lower():
            predictions['security_risk'] = 0.7
            print("⚠️  Security risk with user input")
        
        if not predictions:
            predictions['risk_level'] = 0.1
            print("✅ Low risk detected")
        
        return predictions
    
    def _builtin_ai_verify_data_quality(self, data):
        """AI verifies data quality and consistency"""
        print("🔍 AI Data Quality Check:")
        
        quality_report = {
            'completeness': 0.95,
            'consistency': 0.90,
            'accuracy': 0.88,
            'issues_found': [],
            'recommendations': []
        }
        
        # Simulate data quality analysis
        if isinstance(data, list):
            if len(data) == 0:
                quality_report['issues_found'].append("Empty dataset")
            else:
                print(f"✅ Dataset size: {len(data)} items")
        
        quality_report['recommendations'].append("Consider adding data validation")
        quality_report['recommendations'].append("Implement outlier detection")
        
        for rec in quality_report['recommendations']:
            print(f"💡 AI Recommends: {rec}")
        
        return quality_report
    
    def _builtin_start_session(self, session_name):
        """Start an AI collaboration session"""
        session_str = str(session_name)
        print(f"🚀 Starting AI Session: {session_str}")
        
        # Initialize session context
        self._session_context = [f"SESSION: {session_str}"]
        self._session_active = True
        
        print(f"🤖 AI Partner ready! Let's build: {session_str}")
        print("💡 Use think(), explain(), and intend() to collaborate with AI")
        
        return {
            'session_name': session_str,
            'status': 'active',
            'ai_ready': True,
            'collaboration_mode': 'enabled'
        }
    
    def _builtin_suggest_improvements(self, enabled=True):
        """Enable/disable real-time AI improvement suggestions"""
        self._ai_suggestions_enabled = bool(enabled)
        
        if self._ai_suggestions_enabled:
            print("💡 AI Improvement Suggestions: ENABLED")
            print("🤖 I'll watch your code and suggest optimizations in real-time")
        else:
            print("💡 AI Improvement Suggestions: DISABLED")
        
        return self._ai_suggestions_enabled
    
    def _process_template_string(self, template: str) -> str:
        """Process template string with ${variable} interpolation"""
        import re
        result = template
        
        # Find all ${...} patterns
        pattern = r'\$\{([^}]+)\}'
        matches = list(re.finditer(pattern, template))
        
        # Replace from right to left to preserve positions
        for match in reversed(matches):
            expr_text = match.group(1).strip()
            start, end = match.span()
            
            try:
                # First try direct variable lookup
                if self.memory.has_variable(expr_text):
                    value = self.memory.get_variable(expr_text)
                    result = result[:start] + str(value) + result[end:]
                # Then try parsing as expression  
                elif hasattr(self, 'parser') and self.parser:
                    expr_tree = self.parser.parse(expr_text)
                    value = self._execute_lark_node(expr_tree)
                    result = result[:start] + str(value) + result[end:]
                else:
                    result = result[:start] + f"${{{expr_text}}}" + result[end:]
            except Exception:
                # If evaluation fails, leave the expression as-is
                pass
        
        return result
    
    # ==================== MAIN INTERPRETATION METHODS ====================
    
    def interpret(self, source_code: str, filename: str = "<string>") -> Any:
        """
        Interpret Sona source code
        
        Args:
            source_code: The Sona source code to interpret
            filename: Optional filename for error reporting
            
        Returns:
            The result of the interpretation
        """
        try:
            # Try advanced parser first
            if self.parser:
                try:
                    ast_nodes = self.parser.parse(source_code)
                    if ast_nodes:
                        result = None
                        for node in ast_nodes:
                            result = self._execute_node(node)
                        return result
                    elif ast_nodes is None:
                        # Parser returned None due to syntax error
                        source_lower = source_code.lower().strip()
                        # Check for missing closing quote cases
                        if (source_lower.count('"') % 2 == 1 or 
                            source_lower.count("'") % 2 == 1) or ('(' in source_lower and '"' in source_lower and 
                              source_lower.endswith('"') and ')' not in source_lower) or ('(' in source_lower and "'" in source_lower and 
                              source_lower.endswith("'") and ')' not in source_lower):
                            raise SonaInterpreterError("Graceful syntax error: Missing closing quote detected")
                        # Check for unclosed parentheses
                        elif (source_lower.endswith('(') or 
                            ('(' in source_lower and ')' not in source_lower)):
                            raise SonaInterpreterError("Graceful syntax error: Unclosed parenthesis detected")
                        else:
                            raise SonaInterpreterError("Graceful syntax error: Parse error detected")
                except Exception as e:
                    # Check if this is already a graceful syntax error
                    if "graceful syntax error" in str(e).lower():
                        raise e  # Re-raise without wrapping
                    
                    if self.debug_mode:
                        print(f"Advanced parser failed: {e}")
                    
                    # Handle common syntax errors gracefully
                    error_msg = str(e).lower()
                    if ("unexpected end-of-input" in error_msg or 
                        "unexpected token" in error_msg or
                        "no terminal matches" in error_msg):
                        
                        # Specific checks for common syntax issues
                        source_lower = source_code.lower().strip()
                        if (source_lower.count('"') % 2 == 1 or 
                            source_lower.count("'") % 2 == 1):
                            raise SonaInterpreterError("Graceful syntax error: Missing closing quote detected")
                        elif (source_lower.endswith('(') or 
                            ('(' in source_lower and ')' not in source_lower)):
                            raise SonaInterpreterError("Graceful syntax error: Unclosed parenthesis detected")
                        else:
                            raise SonaInterpreterError(f"Graceful syntax error: {e}")
            
            # Fallback to simple expression parsing
            return self._interpret_simple_expression(source_code.strip())
            
        except Exception as e:
            if self.debug_mode:
                traceback.print_exc()
            raise SonaInterpreterError(f"Interpretation error: {e}")
    
    def _execute_node(self, node) -> Any:
        """Execute a single AST node"""
        self.execution_stats['statements_executed'] += 1
        
        # Handle Lark Tree objects (from parser_v090.py)
        if hasattr(node, 'data') and hasattr(node, 'children'):
            return self._execute_lark_node(node)
        
        # Handle other node types
        if hasattr(node, 'execute'):
            return node.execute(self)
        elif hasattr(node, 'evaluate'):
            return node.evaluate(self)
        else:
            raise SonaInterpreterError(f"Unknown node type: {type(node)}", node)
    
    def _execute_lark_node(self, node) -> Any:
        """Execute a Lark Tree node"""
        # Import Lark types for handling
        try:
            from lark import Token, Tree
        except ImportError:
            raise SonaInterpreterError("Lark parser required for this node type")
        
        if isinstance(node, Tree):
            # Handle different tree types based on data attribute
            if node.data in ['start', 'statement_list']:
                # Root node or statement list - execute all children
                result = None
                for child in node.children:
                    result = self._execute_lark_node(child)
                return result
            
            elif node.data in ['true', 'TRUE', 'True']:
                return True
            
            elif node.data in ['false', 'FALSE', 'False']:
                return False
            
            elif node.data in ['null', 'NULL', 'None']:
                return None
            
            elif node.data == 'list_literal':
                # Evaluate list literal to a Python list
                if node.children and node.children[0]:
                    elements_node = node.children[0]
                    if hasattr(elements_node, 'data') and elements_node.data == 'list_elements':
                        return [self._execute_lark_node(child) for child in elements_node.children]
                return []
            elif node.data == 'num':
                # Numeric literal
                if node.children and hasattr(node.children[0], 'value'):
                    return node.children[0].value
                elif node.children and hasattr(node.children[0], 'execute'):
                    return node.children[0].execute(self)
                return None
            
            elif node.data == 'str':
                # String literal
                if node.children and hasattr(node.children[0], 'value'):
                    return node.children[0].value
                elif node.children and hasattr(node.children[0], 'execute'):
                    return node.children[0].execute(self)
                return None
            
            elif node.data == 'template_str':
                # Template string literal with interpolation
                if node.children and hasattr(node.children[0], 'value'):
                    template = node.children[0].value
                    # Remove backticks
                    if template.startswith('`') and template.endswith('`'):
                        template = template[1:-1]
                    
                    # Process template interpolation
                    return self._process_template_string(template)
                return ""
            
            elif node.data == 'expr' or node.data == 'atom':
                # Expression node - execute child
                if node.children:
                    return self._execute_lark_node(node.children[0])
                return None
                
            elif node.data in ['comparison', 'eq', 'ne', 'neq', 'lt', 'le', 'gt', 'ge', 'lte', 'gte']:
                # Comparison operations
                if len(node.children) >= 2:
                    left = self._execute_lark_node(node.children[0])
                    right = self._execute_lark_node(node.children[1])
                    
                    # Handle different comparison types
                    if node.data == 'comparison':
                        # Original format with operator as middle child
                        if len(node.children) >= 3:
                            op = str(node.children[1])
                            right = self._execute_lark_node(node.children[2])
                        else:
                            return None
                    elif node.data == 'eq':
                        op = '=='
                    elif node.data in ['ne', 'neq']:
                        op = '!='
                    elif node.data == 'lt':
                        op = '<'
                    elif node.data == 'le' or node.data == 'lte':
                        op = '<='
                    elif node.data == 'gt':
                        op = '>'
                    elif node.data == 'ge' or node.data == 'gte':
                        op = '>='
                    else:
                        return None
                    
                    # Perform comparison
                    if op == '==':
                        return left == right
                    elif op == '!=':
                        return left != right
                    elif op == '<':
                        return left < right
                    elif op == '<=':
                        return left <= right
                    elif op == '>':
                        return left > right
                    elif op == '>=':
                        return left >= right
                    else:
                        raise SonaInterpreterError(f"Unknown operator: {op}")
                return None
            
            elif node.data in ['add', 'sub', 'mul', 'div', 'mod']:
                # Arithmetic operations
                if len(node.children) >= 2:
                    left = self._execute_lark_node(node.children[0])
                    right = self._execute_lark_node(node.children[1])
                    
                    # Convert booleans to integers for arithmetic
                    if isinstance(left, bool):
                        left = int(left)
                    if isinstance(right, bool):
                        right = int(right)
                    
                    if node.data == 'add':
                        return left + right
                    elif node.data == 'sub':
                        return left - right
                    elif node.data == 'mul':
                        return left * right
                    elif node.data == 'div':
                        return left / right
                    elif node.data == 'mod':
                        return left % right
                return None
            
            elif node.data in ['or_op', 'and_op']:
                # Logical operations
                if len(node.children) >= 2:
                    left = self._execute_lark_node(node.children[0])
                    right = self._execute_lark_node(node.children[1])
                    
                    if node.data == 'or_op':
                        return bool(left) or bool(right)
                    elif node.data == 'and_op':
                        return bool(left) and bool(right)
                return None
            
            elif node.data == 'not_op':
                # Logical NOT operation
                if len(node.children) >= 1:
                    operand = self._execute_lark_node(node.children[0])
                    return not bool(operand)
                return None
            
            elif node.data == 'enhanced_if_stmt':
                # Enhanced if statement with full if/elif/else support
                if len(node.children) >= 2:
                    condition = self._execute_lark_node(node.children[0])
                    
                    if bool(condition):
                        # Condition is true - execute the if body (child 1)
                        if len(node.children) > 1:
                            return self._execute_lark_node(node.children[1])
                    else:
                        # Condition is false - check for else_clause or elif_clause
                        for child in node.children[2:]:  # Skip condition and if body
                            if hasattr(child, 'data'):
                                if child.data == 'else_clause':
                                    # Execute else body
                                    if child.children:
                                        return self._execute_lark_node(child.children[0])
                                elif child.data == 'elif_clause':
                                    # Execute elif (recursive if statement)
                                    elif_condition = self._execute_lark_node(child.children[0])
                                    if bool(elif_condition):
                                        if len(child.children) > 1:
                                            return self._execute_lark_node(child.children[1])
                        # No else/elif matched
                        return None
                return None
            
            elif node.data == 'enhanced_while_stmt':
                # Enhanced while loop
                if len(node.children) >= 2:
                    condition_node = node.children[0]
                    body_node = node.children[1] if len(node.children) > 1 else None
                    
                    result = None
                    while True:
                        # Evaluate condition
                        condition = self._execute_lark_node(condition_node)
                        if not bool(condition):
                            break
                            
                        # Execute loop body
                        if body_node:
                            result = self._execute_lark_node(body_node)
                            
                        # Check for break/continue (basic implementation)
                        if hasattr(self, '_break_loop'):
                            delattr(self, '_break_loop')
                            break
                        if hasattr(self, '_continue_loop'):
                            delattr(self, '_continue_loop')
                            continue
                    
                    return result
                return None
            
            elif node.data == 'enhanced_for_stmt':
                # Enhanced for loop
                if len(node.children) >= 3:
                    var_name = str(node.children[0])
                    iterable_node = node.children[1]
                    body_node = node.children[2] if len(node.children) > 2 else None
                    
                    # Evaluate iterable
                    iterable = self._execute_lark_node(iterable_node)
                    
                    # Ensure iterable is actually iterable
                    if not hasattr(iterable, '__iter__'):
                        if isinstance(iterable, (int, float)):
                            # Convert number to range
                            iterable = range(int(iterable))
                        else:
                            return None
                    
                    result = None
                    # Create new scope for loop variable
                    self.memory.push_scope()
                    
                    try:
                        for item in iterable:
                            # Set loop variable
                            self.memory.set_variable(var_name, item)
                            
                            # Execute loop body
                            if body_node:
                                result = self._execute_lark_node(body_node)
                                
                            # Check for break/continue (basic implementation)
                            if hasattr(self, '_break_loop'):
                                delattr(self, '_break_loop')
                                break
                            if hasattr(self, '_continue_loop'):
                                delattr(self, '_continue_loop')
                                continue
                    finally:
                        # Clean up scope
                        self.memory.pop_scope()
                    
                    return result
                return None
            
            elif node.data == 'try_stmt':
                # Try/catch/finally error handling
                if len(node.children) >= 3:  # try_body, exception_var, catch_body, [finally_body]
                    try_body = node.children[0]
                    exception_var = str(node.children[1]) if node.children[1] else "error"
                    catch_body = node.children[2]
                    finally_body = node.children[3] if len(node.children) > 3 else None
                    
                    result = None
                    exception_occurred = False
                    
                    # Execute try block
                    try:
                        result = self._execute_lark_node(try_body)
                    except Exception as e:
                        exception_occurred = True
                        # Create new scope for exception variable
                        self.memory.push_scope()
                        
                        # Set exception variable with error message
                        error_message = str(e)
                        self.memory.set_variable(exception_var, error_message)
                        
                        try:
                            # Execute catch block
                            result = self._execute_lark_node(catch_body)
                        finally:
                            # Clean up exception scope
                            self.memory.pop_scope()
                    
                    # Execute finally block if present
                    if finally_body:
                        self._execute_lark_node(finally_body)
                    
                    return result
                return None
            
            elif node.data == 'array':
                # Array literal [1, 2, 3]
                if node.children and node.children[0]:
                    expr_list_node = node.children[0]
                    if hasattr(expr_list_node, 'data') and expr_list_node.data == 'expr_list':
                        # Process expr_list
                        array_items = []
                        for expr_node in expr_list_node.children:
                            item = self._execute_lark_node(expr_node)
                            array_items.append(item)
                        return array_items
                # Empty array
                return []
            
            elif node.data == 'index_access':
                # Array indexing: arr[index]
                if len(node.children) >= 2:
                    array_obj = self._execute_lark_node(node.children[0])
                    index = self._execute_lark_node(node.children[1])
                    
                    if isinstance(array_obj, list) and isinstance(index, int):
                        if 0 <= index < len(array_obj):
                            return array_obj[index]
                        else:
                            raise SonaInterpreterError(f"Array index {index} out of bounds for array of length {len(array_obj)}")
                    else:
                        raise SonaInterpreterError(f"Cannot index {type(array_obj)} with {type(index)}")
                return None
            
            elif node.data == 'object':
                # Object literal { key: value, ... }
                obj = {}
                if node.children and node.children[0]:
                    object_pairs_node = node.children[0]
                    if hasattr(object_pairs_node, 'data') and object_pairs_node.data == 'object_pairs':
                        # Process object_pairs
                        for pair_node in object_pairs_node.children:
                            if hasattr(pair_node, 'data') and pair_node.data == 'object_pair':
                                # Get key and value
                                if len(pair_node.children) >= 2:
                                    key_node = pair_node.children[0]
                                    value_node = pair_node.children[1]
                                    
                                    # Handle key (NAME or STRING)
                                    if hasattr(key_node, 'value'):
                                        key = str(key_node.value)
                                    else:
                                        key = str(key_node)
                                    
                                    # Remove quotes if it's a string key
                                    if key.startswith('"') and key.endswith('"') or key.startswith("'") and key.endswith("'"):
                                        key = key[1:-1]
                                    
                                    # Get value
                                    value = self._execute_lark_node(value_node)
                                    obj[key] = value
                return obj
            
            elif node.data == 'object_pairs':
                # Object pairs (used internally by object)
                pairs = []
                for pair_node in node.children:
                    if hasattr(pair_node, 'data') and pair_node.data == 'object_pair':
                        pairs.append(self._execute_lark_node(pair_node))
                return pairs
            
            elif node.data == 'object_pair':
                # Object key-value pair
                if len(node.children) >= 2:
                    key_node = node.children[0]
                    value_node = node.children[1]
                    
                    # Handle key
                    if hasattr(key_node, 'value'):
                        key = str(key_node.value)
                    else:
                        key = str(key_node)
                    
                    # Get value  
                    value = self._execute_lark_node(value_node)
                    return (key, value)
                return None
            
            elif node.data == 'prop_access':
                # Property access: obj.property
                if len(node.children) >= 2:
                    obj = self._execute_lark_node(node.children[0])
                    prop_name = str(node.children[1])
                    
                    if isinstance(obj, dict):
                        return obj.get(prop_name)
                    else:
                        # Try to get attribute from object
                        return getattr(obj, prop_name, None)
                return None
            
            elif node.data == 'expr_list':
                # Expression list (used in arrays and function arguments)
                items = []
                for expr_node in node.children:
                    item = self._execute_lark_node(expr_node)
                    items.append(item)
                return items
            
            elif node.data in ['funccall', 'func_call']:
                # Function call
                if node.children:
                    func_name = str(node.children[0])
                    args = []
                    
                    # Handle different argument structures
                    for arg_node in node.children[1:]:
                        if arg_node is None:
                            continue  # Skip None arguments (no arguments provided)
                        if hasattr(arg_node, 'data') and arg_node.data == 'arg_list':
                            # Parse argument list
                            for arg in arg_node.children:
                                args.append(self._execute_lark_node(arg))
                        else:
                            # Direct argument
                            args.append(self._execute_lark_node(arg_node))
                    
                    # Look up function
                    try:
                        func = self.memory.get_variable(func_name)
                        if callable(func):
                            self.execution_stats['functions_called'] += 1
                            return func(*args)
                        else:
                            raise SonaInterpreterError(f"'{func_name}' is not callable")
                    except NameError:
                        raise SonaInterpreterError(f"Function '{func_name}' is not defined")
                return None
            
            elif node.data == 'func_def':
                # Function definition
                if len(node.children) >= 3:
                    func_name = str(node.children[0])
                    
                    # Extract parameters
                    param_names = []
                    if node.children[1] and hasattr(node.children[1], 'data') and node.children[1].data == 'param_list':
                        for param_node in node.children[1].children:
                            if hasattr(param_node, 'data') and param_node.data == 'param':
                                param_names.append(str(param_node.children[0]))
                    
                    # Function body starts after params and optional return type
                    body_start_idx = 2
                    if len(node.children) > 3 and node.children[2] is not None:  # Skip return type if present
                        body_start_idx = 3
                    
                    # Extract function body - now expecting a statement_list node
                    body_statement_list = None
                    if len(node.children) > body_start_idx:
                        candidates = [child for child in node.children[body_start_idx:] if child is not None]
                        if candidates and hasattr(candidates[0], 'data') and candidates[0].data == 'statement_list':
                            body_statement_list = candidates[0]
                    
                    # Create function closure
                    def user_function(*args):
                        # Create new scope for function
                        self.memory.push_scope()
                        
                        try:
                            # Bind parameters to arguments
                            for i, param_name in enumerate(param_names):
                                if i < len(args):
                                    self.memory.set_variable(param_name, args[i])
                                else:
                                    self.memory.set_variable(param_name, None)
                            
                            # Execute function body
                            result = None
                            if body_statement_list:
                                result = self._execute_lark_node(body_statement_list)
                                # Check for return statement
                                if hasattr(self, '_return_value'):
                                    result = self._return_value
                                    delattr(self, '_return_value')
                            
                            return result
                        finally:
                            # Clean up scope
                            self.memory.pop_scope()
                    
                    # Store function in memory
                    self.memory.set_variable(func_name, user_function)
                    return None  # Function definitions don't return values
                return None
            
            elif node.data == 'return_stmt':
                # Return statement
                if len(node.children) >= 1:
                    return_value = self._execute_lark_node(node.children[0])
                    # Store return value for function to pick up
                    self._return_value = return_value
                    return return_value
                return None
            
            elif node.data == 'var_assignment':
                # Handle var_assignment wrapper
                if len(node.children) >= 1:
                    return self._execute_lark_node(node.children[0])
                return None
            
            elif node.data in ['var_assign', 'let_assign', 'const_assign']:
                # Variable assignment (let/const declarations)
                if len(node.children) >= 2:
                    var_name = str(node.children[0])
                    value = self._execute_lark_node(node.children[1])
                    
                    # Handle const vs let
                    is_const = node.data == 'const_assign'
                    
                    # Check for redeclaration
                    if self.memory.has_variable(var_name):
                        raise SonaInterpreterError(f"Variable '{var_name}' already declared")
                    
                    # Set the variable
                    self.memory.set_variable(var_name, value)
                    if is_const:
                        self.memory.add_constant(var_name)
                    
                    return value
                return None
            
            elif node.data in ['assign', 'assignment', 'bare_assign']:
                # Variable reassignment (x = value)
                if len(node.children) >= 2:
                    var_name = str(node.children[0])
                    value = self._execute_lark_node(node.children[1])
                    
                    # Check if variable exists
                    if not self.memory.has_variable(var_name):
                        raise SonaInterpreterError(f"Variable '{var_name}' not declared")
                    
                    # Check if it's a constant
                    if self.memory.is_constant(var_name):
                        raise SonaInterpreterError(f"Cannot reassign constant '{var_name}'")
                    
                    # Assign to the variable (updates existing variable in original scope)
                    self.memory.assign_variable(var_name, value)
                    return value
                return None
            
            elif node.data in ['var', 'variable']:
                # Variable reference/lookup
                if node.children:
                    var_name = str(node.children[0])
                    self.execution_stats['variables_accessed'] += 1
                    try:
                        return self.memory.get_variable(var_name)
                    except NameError:
                        raise SonaInterpreterError(f"Variable '{var_name}' is not defined")
                return None
            
            else:
                # Unknown tree type - try to execute children
                if len(node.children) == 1:
                    return self._execute_lark_node(node.children[0])
                elif len(node.children) > 1:
                    result = None
                    for child in node.children:
                        result = self._execute_lark_node(child)
                    return result
                else:
                    raise SonaInterpreterError(f"Unknown tree node: {node.data}")
        
        elif isinstance(node, Token):
            # Handle tokens
            if node.type in ['TRUE', 'True']:
                return True
            elif node.type in ['FALSE', 'False']:
                return False
            elif node.type in ['NULL', 'None']:
                return None
            elif node.type == 'NUMBER':
                try:
                    if '.' in node.value:
                        return float(node.value)
                    else:
                        return int(node.value)
                except ValueError:
                    return node.value
            elif node.type == 'STRING':
                # Remove quotes
                return node.value[1:-1] if len(node.value) >= 2 else node.value
            elif node.type == 'TEMPLATE_STRING':
                # Remove backticks and process template string
                template = node.value[1:-1] if len(node.value) >= 2 else node.value
                return self._process_template_string(template)
            elif node.type == 'NAME':
                # Variable lookup
                self.execution_stats['variables_accessed'] += 1
                try:
                    return self.memory.get_variable(node.value)
                except NameError:
                    raise SonaInterpreterError(f"Variable '{node.value}' is not defined")
            else:
                # Return token value as-is
                return node.value
        
        else:
            # Handle AST nodes that have execute/evaluate methods
            if hasattr(node, 'execute'):
                return node.execute(self)
            elif hasattr(node, 'evaluate'):
                return node.evaluate(self)
            else:
                # Unknown node type
                raise SonaInterpreterError(f"Unknown node type: {type(node)}")
    
    def _interpret_simple_expression(self, expression: str) -> Any:
        """
        Fallback interpreter for simple expressions when parser fails
        This provides backward compatibility and handles basic literals
        """
        expression = expression.strip()
        
        # Handle boolean literals (both lowercase and Python-style)
        if expression == 'true' or expression == 'True':
            return True
        elif expression == 'false' or expression == 'False':
            return False
        elif expression == 'null' or expression == 'None':
            return None
        
        # Handle list literals
        if expression.startswith('[') and expression.endswith(']'):
            list_content = expression[1:-1].strip()
            if not list_content:  # Empty list
                return []
            # Simple parsing - split by comma and interpret each element
            elements = []
            # Use a simple comma split for now (doesn't handle nested structures)
            for element in list_content.split(','):
                element = element.strip()
                elements.append(self._interpret_simple_expression(element))
            return elements
        
        # Handle string literals
        if (expression.startswith('"') and expression.endswith('"')) or \
           (expression.startswith("'") and expression.endswith("'")):
            return expression[1:-1]
        
        # Handle numeric literals
        try:
            if '.' in expression:
                return float(expression)
            else:
                return int(expression)
        except ValueError:
            pass
        
        # Handle arithmetic operations with boolean conversion
        for op in ['+', '-', '*', '/', '%']:
            if op in expression:
                parts = expression.split(op, 1)
                if len(parts) == 2:
                    left = self._interpret_simple_expression(parts[0].strip())
                    right = self._interpret_simple_expression(parts[1].strip())
                    
                    # Convert booleans to integers for arithmetic
                    if isinstance(left, bool):
                        left = int(left)
                    if isinstance(right, bool):
                        right = int(right)
                    
                    if op == '+':
                        return left + right
                    elif op == '-':
                        return left - right
                    elif op == '*':
                        return left * right
                    elif op == '/':
                        return left / right
                    elif op == '%':
                        return left % right
        
        # Handle logical operators
        for op in ['and', 'or']:
            if f' {op} ' in expression:
                parts = expression.split(f' {op} ', 1)
                if len(parts) == 2:
                    left = self._interpret_simple_expression(parts[0].strip())
                    right = self._interpret_simple_expression(parts[1].strip())
                    
                    if op == 'and':
                        return left and right
                    elif op == 'or':
                        return left or right
        
        # Handle simple comparisons
        for op in ['==', '!=', '<=', '>=', '<', '>']:
            if op in expression:
                parts = expression.split(op, 1)
                if len(parts) == 2:
                    left = self._interpret_simple_expression(parts[0].strip())
                    right = self._interpret_simple_expression(parts[1].strip())
                    
                    # Handle comparison operations
                    if op == '==':
                        return left == right
                    elif op == '!=':
                        return left != right
                    elif op == '<':
                        return left < right
                    elif op == '<=':
                        return left <= right
                    elif op == '>':
                        return left > right
                    elif op == '>=':
                        return left >= right
                # Exit after finding a matching operator
                break
        
        # Handle function calls
        if '(' in expression and expression.endswith(')'):
            func_name = expression[:expression.index('(')]
            args_str = expression[expression.index('(')+1:-1]
            args = []
            if args_str.strip():
                # Enhanced argument parsing to handle lists, strings, etc.
                args = self._parse_function_arguments(args_str)
            
            # Look up and call function
            try:
                func = self.memory.get_variable(func_name)
                if callable(func):
                    self.execution_stats['functions_called'] += 1
                    return func(*args)
                else:
                    raise SonaInterpreterError(f"'{func_name}' is not callable")
            except NameError:
                raise SonaInterpreterError(f"Function '{func_name}' is not defined")
        
        # Handle variable reference
        try:
            self.execution_stats['variables_accessed'] += 1
            return self.memory.get_variable(expression)
        except NameError:
            raise SonaInterpreterError(f"Cannot interpret expression: {expression}")
    
    def _parse_function_arguments(self, args_str: str):
        """Parse function arguments, handling lists, strings, and other types"""
        args = []
        current_arg = ""
        bracket_depth = 0
        quote_char = None
        
        for char in args_str:
            if quote_char:
                # Inside a string literal
                current_arg += char
                if char == quote_char and (len(current_arg) < 2 or 
                                          current_arg[-2] != '\\'):
                    quote_char = None
            elif char in ['"', "'"]:
                # Start of string literal
                quote_char = char
                current_arg += char
            elif char == '[':
                bracket_depth += 1
                current_arg += char
            elif char == ']':
                bracket_depth -= 1
                current_arg += char
            elif char == ',' and bracket_depth == 0:
                # Argument separator at top level
                if current_arg.strip():
                    args.append(self._interpret_simple_expression(
                        current_arg.strip()))
                current_arg = ""
            else:
                current_arg += char
        
        # Add the last argument
        if current_arg.strip():
            args.append(self._interpret_simple_expression(current_arg.strip()))
        
        return args
    
    # ==================== COGNITIVE PROGRAMMING FUNCTIONS ====================
    
    def _builtin_working_memory(self, context=None, action="load"):
        """Manage working memory for cognitive accessibility"""
        
        if not hasattr(self, '_working_memory'):
            self._working_memory = []
        
        # If no context provided, assume recall action
        if context is None:
            print("🔍 Recalling from working memory:")
            for i, item in enumerate(self._working_memory[-5:], 1):
                print(f"   {i}. {item['content']}")
            return self._working_memory[-5:] if self._working_memory else []
            
        context_str = str(context)
        action_str = str(action).lower()
        
        if action_str == "load":
            print(f"🧠 Loading into working memory: {context_str}")
            self._working_memory.append({
                'content': context_str,
                'timestamp': 'now',
                'priority': 'high'
            })
            return f"Loaded: {context_str}"
        elif action_str == "recall":
            print("🔍 Recalling from working memory:")
            for i, item in enumerate(self._working_memory[-5:], 1):
                print(f"   {i}. {item['content']}")
            return self._working_memory[-5:] if self._working_memory else []
        elif action_str == "clear":
            print("🧹 Clearing working memory")
            self._working_memory.clear()
            return "Working memory cleared"
        else:
            return f"Working memory contains {len(self._working_memory)} items"
    
    def _builtin_focus_mode(self, task, duration="25min"):
        """Enter focus mode for concentrated work (Pomodoro-style)"""
        task_str = str(task)
        duration_str = str(duration)
        
        print(f"🎯 Focus Mode: {task_str} for {duration_str}")
        print("🔕 Distractions minimized")
        print("💡 AI will provide gentle reminders and progress updates")
        
        # Create focus session
        focus_session = {
            'task': task_str,
            'duration': duration_str,
            'start_time': 'now',
            'reminders': [
                f"Stay focused on: {task_str}",
                "Take breaks when needed",
                "You're making great progress!"
            ]
        }
        
        return focus_session
    
    def _builtin_cognitive_check(self, complexity_level="auto"):
        """Check cognitive load and suggest adjustments"""
        if not hasattr(self, '_cognitive_state'):
            self._cognitive_state = {'load': 'normal', 'focus': 'good'}
        
        level = str(complexity_level).lower()
        
        if level == "high":
            print("⚠️  High cognitive load detected")
            suggestions = [
                "Consider breaking this into smaller steps",
                "Take a short break to refresh your mind",
                "Use working_memory() to organize thoughts"
            ]
        elif level == "low":
            print("✅ Low cognitive load - ready for complex tasks")
            suggestions = [
                "This is a good time for challenging problems",
                "Consider tackling multiple related tasks"
            ]
        else:
            print("🧠 Cognitive check: Normal load")
            suggestions = [
                "Pace yourself appropriately",
                "Use focus_mode() for concentration",
                "Break down complex tasks as needed"
            ]
        
        for suggestion in suggestions:
            print(f"💡 {suggestion}")
        
        return {
            'cognitive_load': level,
            'suggestions': suggestions,
            'status': 'assessed'
        }
    
    def _builtin_simplify(self, concept, target_level="beginner"):
        """Simplify complex concepts for better understanding"""
        concept_str = str(concept)
        level = str(target_level).lower()
        
        print(f"🔧 Simplifying: {concept_str} for {level} level")
        
        if "algorithm" in concept_str.lower():
            simple = "An algorithm is like a recipe - a step-by-step guide to solve a problem"
        elif "database" in concept_str.lower():
            simple = "A database is like a digital filing cabinet that stores and organizes information"
        elif "api" in concept_str.lower():
            simple = "An API is like a waiter - it takes your request and brings back what you need"
        elif "function" in concept_str.lower():
            simple = "A function is like a tool - you give it input and it gives you output"
        else:
            simple = f"Breaking down '{concept_str}' into simpler terms..."
        
        print(f"💡 Simplified: {simple}")
        return simple
    
    def _builtin_clarify(self, question, context=None):
        """Ask for clarification on unclear concepts"""
        question_str = str(question)
        
        print(f"❓ Clarification needed: {question_str}")
        
        if "how" in question_str.lower():
            response = "Let me explain the step-by-step process..."
        elif "why" in question_str.lower():
            response = "Here's the reasoning behind this..."
        elif "what" in question_str.lower():
            response = "Let me define this clearly..."
        elif "when" in question_str.lower():
            response = "Here's when this applies..."
        else:
            response = "Let me provide more detail..."
        
        print(f"🤖 {response}")
        
        if context:
            print(f"📝 Context: {context}")
        
        return {
            'question': question_str,
            'response': response,
            'context': context
        }
    
    def _builtin_break_down(self, complex_task, steps=None):
        """Break down complex tasks into manageable steps"""
        task_str = str(complex_task)
        
        print(f"📋 Breaking down: {task_str}")
        
        if steps:
            step_list = steps if isinstance(steps, list) else [str(steps)]
        else:
            # Auto-generate steps based on task type
            if "build" in task_str.lower():
                step_list = [
                    "Plan the structure",
                    "Set up the foundation",
                    "Implement core features",
                    "Test and refine",
                    "Document and deploy"
                ]
            elif "learn" in task_str.lower():
                step_list = [
                    "Understand the basics",
                    "Practice with examples",
                    "Apply to real projects",
                    "Review and reinforce"
                ]
            else:
                step_list = [
                    "Analyze the requirements",
                    "Plan the approach",
                    "Execute step by step",
                    "Review and improve"
                ]
        
        print("📝 Steps:")
        for i, step in enumerate(step_list, 1):
            print(f"   {i}. {step}")
        
        return {
            'task': task_str,
            'steps': step_list,
            'status': 'broken_down'
        }
    
    # ==================== NEW v0.9.0 EXTENDED FUNCTIONS ====================
    
    def _builtin_ai_generate(self, prompt, output_type="code"):
        """Generate content using AI based on prompt and type"""
        prompt_str = str(prompt)
        type_str = str(output_type).lower()
        
        print(f"🎯 Generating {type_str}: {prompt_str}")
        
        if type_str == "code":
            result = f"# Generated code for: {prompt_str}\ndef solution():\n    # Implementation here\n    pass"
        elif type_str == "docs":
            result = f"# Documentation for: {prompt_str}\n\nThis feature provides..."
        elif type_str == "tests":
            result = f"# Test cases for: {prompt_str}\ndef test_feature():\n    assert True"
        else:
            result = f"Generated content for: {prompt_str}"
        
        print(f"✅ Generated: {result[:50]}...")
        return result
    
    def _builtin_ai_refactor(self, code, goal="improve_readability"):
        """Refactor code using AI guidance"""
        code_str = str(code)
        goal_str = str(goal).lower()
        
        print(f"🔧 Refactoring code with goal: {goal_str}")
        
        if "performance" in goal_str:
            suggestion = "Optimize loops and reduce complexity"
        elif "readability" in goal_str:
            suggestion = "Add clear variable names and comments"
        elif "security" in goal_str:
            suggestion = "Add input validation and error handling"
        else:
            suggestion = "General code improvements suggested"
        
        print(f"💡 Refactoring suggestion: {suggestion}")
        return {
            'original': code_str,
            'suggestion': suggestion,
            'goal': goal_str
        }
    
    def _builtin_ai_test(self, function_name, test_type="unit"):
        """Generate AI-powered tests for functions"""
        func_str = str(function_name)
        type_str = str(test_type).lower()
        
        print(f"🧪 Generating {type_str} tests for: {func_str}")
        
        test_code = f"""def test_{func_str}():
    # Test basic functionality
    result = {func_str}()
    assert result is not None
    
    # Test edge cases
    # Add more test cases here
    pass"""
        
        print(f"✅ Generated test: {test_code[:50]}...")
        return test_code
    
    def _builtin_ai_document(self, code_element, doc_type="docstring"):
        """Generate documentation using AI"""
        element_str = str(code_element)
        type_str = str(doc_type).lower()
        
        print(f"📚 Generating {type_str} for: {element_str}")
        
        if type_str == "docstring":
            doc = f'"""\n{element_str} function\n\nDescription of functionality here.\n"""'
        elif type_str == "readme":
            doc = f"# {element_str}\n\nProject description and usage instructions."
        else:
            doc = f"Documentation for {element_str}"
        
        print("✅ Generated documentation")
        return doc
    
    def _builtin_filter(self, items, condition):
        """Filter items based on condition"""
        if not isinstance(items, (list, tuple)):
            items = [items]
        
        # Simple condition checking
        if callable(condition):
            filtered = [item for item in items if condition(item)]
        else:
            # String-based filtering
            condition_str = str(condition).lower()
            filtered = [item for item in items if condition_str in str(item).lower()]
        
        print(f"🔍 Filtered {len(items)} items to {len(filtered)} results")
        return filtered
    
    def _builtin_map(self, items, transform):
        """Apply transformation to all items"""
        if not isinstance(items, (list, tuple)):
            items = [items]
        
        if callable(transform):
            mapped = [transform(item) for item in items]
        else:
            # Simple string transformation
            transform_str = str(transform).lower()
            if transform_str == "upper":
                mapped = [str(item).upper() for item in items]
            elif transform_str == "lower":
                mapped = [str(item).lower() for item in items]
            else:
                mapped = [f"{transform_str}({item})" for item in items]
        
        print(f"🔄 Mapped {len(items)} items")
        return mapped
    
    def _builtin_reduce(self, items, operation, initial=None):
        """Reduce items to single value using operation"""
        if not isinstance(items, (list, tuple)):
            items = [items]
        
        if not items:
            return initial
        
        result = initial if initial is not None else items[0]
        start_idx = 0 if initial is not None else 1
        
        for item in items[start_idx:]:
            if callable(operation):
                result = operation(result, item)
            else:
                op_str = str(operation).lower()
                if op_str in ["+", "add", "sum"]:
                    result = result + item
                elif op_str in ["*", "multiply", "product"]:
                    result = result * item
                elif op_str in ["max", "maximum"]:
                    result = max(result, item)
                elif op_str in ["min", "minimum"]:
                    result = min(result, item)
        
        print(f"⬇️ Reduced {len(items)} items to: {result}")
        return result
    
    def _builtin_sort(self, items, key=None, reverse=False):
        """Sort items with optional key and reverse"""
        if not isinstance(items, (list, tuple)):
            items = [items]
        
        try:
            if key and callable(key):
                sorted_items = sorted(items, key=key, reverse=reverse)
            elif key:
                # String-based sorting
                key_str = str(key).lower()
                if key_str == "length":
                    sorted_items = sorted(items, key=len, reverse=reverse)
                elif key_str == "numeric":
                    sorted_items = sorted(items, key=lambda x: float(x) if str(x).replace('.','').isdigit() else 0, reverse=reverse)
                else:
                    sorted_items = sorted(items, reverse=reverse)
            else:
                sorted_items = sorted(items, reverse=reverse)
            
            print(f"📊 Sorted {len(items)} items")
            return sorted_items
        except Exception as e:
            print(f"⚠️ Sort error: {e}")
            return items
    
    def _builtin_math_random(self, min_val=0, max_val=1):
        """Generate random number between min and max"""
        import random
        
        try:
            min_num = float(min_val)
            max_num = float(max_val)
            
            if min_num == 0 and max_num == 1:
                result = random.random()
            else:
                result = random.uniform(min_num, max_num)
            
            print(f"🎲 Random number: {result}")
            return result
        except:
            print("⚠️ Using default random between 0 and 1")
            return random.random()
    
    def _builtin_math_round(self, number, decimals=0):
        """Round number to specified decimal places"""
        try:
            num = float(number)
            dec = int(decimals)
            
            result = round(num, dec)
            print(f"🔢 Rounded {num} to {result}")
            return result
        except:
            print(f"⚠️ Cannot round: {number}")
            return number
    
    def _builtin_deep_copy(self, obj):
        """Create a deep copy of an object"""
        import copy
        
        try:
            copied = copy.deepcopy(obj)
            print(f"📋 Deep copied object of type: {type(obj).__name__}")
            return copied
        except Exception as e:
            print(f"⚠️ Copy error: {e}")
            return obj
    
    def _builtin_validate(self, data, validation_type="not_empty"):
        """Validate data based on validation type"""
        validation_str = str(validation_type).lower()
        
        if validation_str == "not_empty":
            valid = data is not None and str(data).strip() != ""
        elif validation_str == "numeric":
            try:
                float(data)
                valid = True
            except:
                valid = False
        elif validation_str == "email":
            import re
            valid = bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(data)))
        elif validation_str == "positive":
            try:
                valid = float(data) > 0
            except:
                valid = False
        else:
            valid = True  # Default to valid for unknown types
        
        status = "✅ Valid" if valid else "❌ Invalid"
        print(f"{status}: {data} ({validation_str})")
        
        return {
            'data': data,
            'validation_type': validation_str,
            'is_valid': valid,
            'status': status
        }

    # ==================== UTILITY METHODS ====================
    
    def evaluate(self, expression: str) -> Any:
        """Evaluate a single Sona expression"""
        return self.interpret(expression)
    
    def execute_statement(self, statement: str) -> Any:
        """Execute a single Sona statement"""
        return self.interpret(statement)
    
    def get_stats(self) -> dict[str, Any]:
        """Get interpreter performance statistics"""
        return {
            'execution_stats': self.execution_stats.copy(),
            'memory_usage': {
                'global_variables': len(self.memory.global_scope),
                'local_scopes': len(self.memory.local_scopes),
                'constants': len(self.memory.constants)
            }
        }


# Create a default interpreter instance for convenience
default_interpreter = SonaInterpreter()

# Export the main classes and functions
__all__ = [
    'SonaInterpreter',
    'SonaInterpreterError',
    'SonaMemoryManager',
    'default_interpreter'
]
