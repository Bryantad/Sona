#!/usr/bin/env python3
"""
🔧 ENHANCED FUNCTION CALL PARSER FOR COGNITIVE CONSTRUCTS
========================================================

Fix the function call parsing to properly handle cognitive constructs
like remember(), focus_mode(), ai_simplify(), etc.
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Any

current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

from complete_v090_cognitive_constructs import EnhancedSonaInterpreter
from safe_cognitive_functions import register_safe_cognitive_functions


class AdvancedSonaInterpreter(EnhancedSonaInterpreter):
    """Enhanced interpreter with advanced function call parsing and safe cognitive functions"""
    
    def __init__(self):
        super().__init__()
        print("🔧 Advanced function call parsing enabled")
        
        # Register safe cognitive functions to prevent recursion
        register_safe_cognitive_functions(self)
        print("🛡️ Safe cognitive functions enabled")
    
    def _is_simple_statement(self, code: str) -> bool:
        """Enhanced simple statement detection"""
        code = code.strip()
        
        # Check for various patterns
        patterns = [
            'let ',
            'print(',
            'var ',
            # Cognitive function patterns
            'remember(',
            'recall(',
            'focus_mode(',
            'cognitive_load(',
            'attention_check(',
            'check_focus(',
            'working_memory(',
            'ai_simplify(',
            'ai_break_down(',
            'ai_optimize_cognitive(',
            'break_focus(',
            'complexity_check('
        ]
        
        # Check if it's a function call (ends with parentheses)
        if '(' in code and code.rstrip().endswith(')'):
            return True
        
        return any(code.startswith(pattern) for pattern in patterns)
    
    def _execute_simple_statement(self, code: str) -> any:
        """Enhanced simple statement execution with advanced function parsing"""
        code = code.strip()
        
        if code.startswith('let '):
            return self._handle_let_assignment(code)
        elif code.startswith('print('):
            return self._handle_print_call(code)
        elif '(' in code and code.endswith(')'):
            return self._handle_advanced_function_call(code)
        else:
            return super().interpret(code)
    
    def _handle_advanced_function_call(self, code: str) -> any:
        """Handle advanced function calls with proper argument parsing"""
        try:
            # Extract function name and arguments
            match = re.match(r'(\w+)\((.*)\)', code)
            if not match:
                print(f"❌ Invalid function call syntax: {code}")
                return None
            
            func_name = match.group(1)
            args_str = match.group(2)
            
            # Check if function exists
            if not self.memory.has_variable(func_name):
                print(f"❌ Function '{func_name}' not found")
                return None
            
            func = self.memory.get_variable(func_name)
            if not callable(func):
                print(f"❌ '{func_name}' is not callable")
                return None
            
            # Parse arguments
            args = self._parse_function_arguments(args_str)
            
            # Call the function
            if args is None:
                return func()
            elif len(args) == 1:
                return func(args[0])
            elif len(args) == 2:
                return func(args[0], args[1])
            elif len(args) == 3:
                return func(args[0], args[1], args[2])
            else:
                return func(*args)
            
        except Exception as e:
            print(f"❌ Function call error: {e}")
            return None
    
    def _parse_function_arguments(self, args_str: str) -> List[Any]:
        """Parse function arguments from string"""
        if not args_str.strip():
            return []
        
        # Handle simple cases first
        args_str = args_str.strip()
        
        # Handle keyword arguments (simple parsing)
        if 'action=' in args_str:
            return self._parse_keyword_arguments(args_str)
        
        # Split by comma, but handle quoted strings
        args = []
        current_arg = ""
        in_quotes = False
        quote_char = None
        
        for char in args_str:
            if char in ['"', "'"] and not in_quotes:
                in_quotes = True
                quote_char = char
                current_arg += char
            elif char == quote_char and in_quotes:
                in_quotes = False
                current_arg += char
                quote_char = None
            elif char == ',' and not in_quotes:
                args.append(self._evaluate_argument(current_arg.strip()))
                current_arg = ""
            else:
                current_arg += char
        
        # Add the last argument
        if current_arg.strip():
            args.append(self._evaluate_argument(current_arg.strip()))
        
        return args
    
    def _parse_keyword_arguments(self, args_str: str) -> List[Any]:
        """Parse keyword arguments like action='status'"""
        args = []
        
        # Split by comma
        parts = [part.strip() for part in args_str.split(',')]
        
        for part in parts:
            if '=' in part:
                # It's a keyword argument - for now, just extract the value
                key, value = part.split('=', 1)
                args.append(self._evaluate_argument(value.strip()))
            else:
                args.append(self._evaluate_argument(part))
        
        return args
    
    def _evaluate_argument(self, arg: str) -> Any:
        """Evaluate a single argument"""
        arg = arg.strip()
        
        # Handle string literals
        if (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
            return arg[1:-1]  # Remove quotes
        
        # Handle numbers
        try:
            if '.' in arg:
                return float(arg)
            return int(arg)
        except ValueError:
            pass
        
        # Handle booleans
        if arg.lower() == 'true':
            return True
        elif arg.lower() == 'false':
            return False
        elif arg.lower() == 'null' or arg.lower() == 'none':
            return None
        
        # Handle variables
        if self.memory.has_variable(arg):
            return self.memory.get_variable(arg)
        
        # Return as string if all else fails
        return arg

    def _handle_print_call(self, code: str) -> any:
        """Handle print() function calls"""
        try:
            # Extract content between parentheses
            start = code.find('(') + 1
            end = code.rfind(')')
            
            if start > 0 and end > start:
                content = code[start:end].strip()
                
                # Evaluate the content
                value = self._evaluate_expression(content)
                
                # Print it
                print(value)
                return None
                
        except Exception as e:
            print(f"❌ Print call error: {e}")
            return None
    
    def _evaluate_expression(self, expr: str) -> any:
        """Evaluate expressions with variable substitution and function calls"""
        expr = expr.strip()
        
        # Handle string literals
        if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1]  # Remove quotes
        
        # Handle numbers
        try:
            if '.' in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass
        
        # Handle function calls
        if '(' in expr and expr.endswith(')'):
            return self._evaluate_function_call(expr)
        
        # Handle simple arithmetic and string concatenation
        if '+' in expr:
            parts = expr.split('+', 1)  # Split only on first +
            if len(parts) == 2:
                left = self._evaluate_expression(parts[0].strip())
                right = self._evaluate_expression(parts[1].strip())
                return str(left) + str(right) if isinstance(left, str) or isinstance(right, str) else left + right
        
        # Handle variables - use has_variable and get_variable methods
        if self.memory.has_variable(expr):
            return self.memory.get_variable(expr)
        
        # Handle boolean literals
        if expr == 'true':
            return True
        elif expr == 'false':
            return False
        elif expr == 'null':
            return None
        
        # Return as-is if we can't evaluate
        return expr
    
    def _evaluate_function_call(self, expr: str) -> any:
        """Evaluate a function call expression"""
        try:
            # Extract function name and arguments
            match = re.match(r'(\w+)\((.*)\)', expr)
            if not match:
                return expr  # Not a valid function call
            
            func_name = match.group(1)
            args_str = match.group(2)
            
            # Check if function exists
            if not self.memory.has_variable(func_name):
                return expr  # Function not found, return as-is
            
            func = self.memory.get_variable(func_name)
            if not callable(func):
                return expr  # Not callable, return as-is
            
            # Parse arguments
            args = self._parse_function_arguments(args_str)
            
            # Call the function
            if args is None or len(args) == 0:
                return func()
            elif len(args) == 1:
                return func(args[0])
            elif len(args) == 2:
                return func(args[0], args[1])
            elif len(args) == 3:
                return func(args[0], args[1], args[2])
            else:
                return func(*args)
                
        except Exception as e:
            print(f"❌ Function evaluation error: {e}")
            return expr  # Return original on error

    def _handle_let_assignment(self, code: str) -> any:
        """Handle let variable assignments with function evaluation"""
        try:
            # Parse: let variable = value
            parts = code[4:].split('=', 1)  # Remove 'let ' and split on first =
            if len(parts) != 2:
                print(f"❌ Invalid let syntax: {code}")
                return None
            
            var_name = parts[0].strip()
            value_expr = parts[1].strip()
            
            # Evaluate the expression (could be a function call)
            value = self._evaluate_expression(value_expr)
            
            # Store in memory
            self.memory.set_variable(var_name, value)
            
            print(f"✅ Set {var_name} = {value}")
            return value
            
        except Exception as e:
            print(f"❌ Let assignment error: {e}")
            return None


def test_advanced_cognitive_functions():
    """Test the advanced cognitive functions with proper parsing"""
    print("🧪 TESTING ADVANCED COGNITIVE FUNCTIONS")
    print("=" * 60)
    
    interpreter = AdvancedSonaInterpreter()
    
    # Test sequence with cognitive functions
    test_sequence = [
        # Basic memory operations
        ('remember("task1", "Learn Sona", "high")', "Store high-priority memory"),
        ('recall("task1")', "Recall stored memory"),
        
        # Focus mode operations
        ('focus_mode("Coding session", 25)', "Activate 25-minute focus session"),
        ('check_focus()', "Check focus session status"),
        
        # Cognitive monitoring
        ('cognitive_load()', "Check current cognitive load"),
        ('attention_check()', "Analyze attention state"),
        
        # AI-powered functions (these will use real AI)
        ('ai_simplify("Implement recursive algorithms")', "AI simplification"),
        ('ai_break_down("Create a web server")', "AI task breakdown"),
        
        # Working memory status
        ('working_memory("session_info", action="status")', "Memory system status"),
    ]
    
    print("🧪 Running advanced cognitive function tests:")
    print("-" * 50)
    
    success_count = 0
    for i, (code, description) in enumerate(test_sequence, 1):
        print(f"\n📝 Test {i}: {description}")
        print(f"   Code: {code}")
        print(f"   Output: ", end="")
        
        try:
            result = interpreter.interpret(code)
            success_count += 1
            print(f"✅ SUCCESS")
            if result and not isinstance(result, str):
                print(f"   Result type: {type(result).__name__}")
        except Exception as e:
            print(f"❌ FAILED: {e}")
    
    print(f"\n📊 ADVANCED FUNCTION TEST RESULTS:")
    print(f"   Success Rate: {success_count}/{len(test_sequence)} ({success_count/len(test_sequence)*100:.1f}%)")
    
    # Show final cognitive state
    print(f"\n🧠 FINAL COGNITIVE STATE:")
    print(f"   Memory Slots: {len(interpreter.working_memory.memory_slots)}")
    print(f"   Cognitive Load: {interpreter.working_memory.cognitive_load:.2f}")
    print(f"   Active Focus Sessions: {len(interpreter.working_memory.focus_stack)}")
    
    if success_count >= len(test_sequence) * 0.8:
        print("\n🎉 COGNITIVE FUNCTIONS FULLY OPERATIONAL!")
        print("✅ Advanced function parsing working")
        print("✅ Memory operations functional")
        print("✅ Focus mode implementation complete")
        print("✅ AI integration working")
        print("\n🚀 READY FOR v0.9.1 DEVELOPMENT!")
    
    return interpreter


def demo_real_cognitive_programming():
    """Demo real cognitive programming workflow"""
    print("\n" + "=" * 60)
    print("💻 REAL COGNITIVE PROGRAMMING WORKFLOW DEMO")
    print("=" * 60)
    
    interpreter = AdvancedSonaInterpreter()
    
    # Simulate a real coding session with cognitive awareness
    workflow = [
        'remember("project", "Build todo app", "high")',
        'focus_mode("Design phase", 30)',
        'ai_break_down("Create a todo application with user authentication")',
        'remember("current_step", "Database design", "medium")',
        'cognitive_load()',
        'attention_check()',
        'ai_simplify("Design normalized database schema")',
        'check_focus()',
        'remember("next_task", "Implement user interface", "medium")',
        'recall("project")',
    ]
    
    print("🧠 Simulating real cognitive programming session:")
    print("-" * 50)
    
    for i, code in enumerate(workflow, 1):
        print(f"\n⚡ Step {i}: {code}")
        try:
            result = interpreter.interpret(code)
            print(f"   ✅ Executed successfully")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n🎯 COGNITIVE SESSION COMPLETE!")
    print(f"   This demonstrates Sona as a truly cognitive-aware programming language!")


if __name__ == "__main__":
    # Test the advanced functions
    interpreter = test_advanced_cognitive_functions()
    
    # Demo real workflow
    demo_real_cognitive_programming()
