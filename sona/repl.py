"""Sona REPL with support for all standard library modules"""

import os
import sys
import time
import pprint
from pathlib import Path
from lark import UnexpectedInput, Lark, Tree, Token
from sona.interpreter import run_code
from sona.interpreter import SonaInterpreter
from sona.interpreter import debug_mode

# Debug state dictionary to store diagnostic information
debug_state = {
    "last_error": None,
    "last_tree": None,
    "last_duration": None,
    "trace_enabled": False
}

def run_repl():
    """Run the Sona REPL (Read-Eval-Print Loop)"""
    print("Sona REPL v0.5.1 - Type `:help` or `exit` to quit.")
    
    # Environment setup
    env = {}
    multiline_input = []
    multiline_mode = False
    interpreter = None
    parser = None
    
    # Initialize parser and interpreter for debug tools
    from lark import Lark
    grammar_path = Path(__file__).parent / 'grammar.lark'
    with open(grammar_path) as f:
        grammar = f.read()
    parser = Lark(grammar, parser="lalr", propagate_positions=True)
    interpreter = SonaInterpreter()
    
    # Main REPL loop
    while True:
        try:
            # Determine prompt based on multiline mode
            if multiline_mode:
                prompt = "...> "
            else:
                prompt = "sona> "
                
            # Get user input
            line = input(prompt)
            
            # Handle empty lines in normal mode
            if not line.strip() and not multiline_mode:
                continue
            
            # Handle commands in normal mode (not in multiline)
            if not multiline_mode:
                # Handle commands with colon prefix
                if line.startswith(":"):
                    cmd = line[1:].strip().lower()
                    
                    # Exit commands
                    if cmd in ["exit", "quit"]:
                        print("Exiting Sona REPL.")
                        break
                        
                    # Help command
                    elif cmd == "help":
                        print("Available commands:")
                        print("  :help       - Show this help message")
                        print("  :exit, :quit- Exit the REPL")
                        print("  :calc       - Launch calculator application")
                        print("  :quiz       - Launch quiz application")
                        print("  :clear      - Clear the screen")
                        print("  :version    - Show Sona version")
                        print("  :test       - Run diagnostic tests")
                        print("\nDeveloper Tools:")
                        print("  :debug      - Show last error and parse tree")
                        print("  :profile    - Measure execution time of the last command")
                        print("  :watch <var>- Print live value of a specific variable")
                        print("  :trace      - Toggle tracing of function calls and returns")
                        continue
                    
                    # Version command
                    elif cmd == "version":
                        print("Sona v0.5.1")
                        continue
                    
                    # Clear screen command
                    elif cmd == "clear":
                        os.system('cls' if os.name == 'nt' else 'clear')
                        continue
                        
                    # Calculator command - added this in v0.5.1 after users requested it
                    elif cmd.lower() in ["calc", "cal", "calculator"]:
                        print("\n=== Launching Sona Calculator ===")
                        
                        # TODO: Maybe we should cache these files for faster loading?
                        base_dir = Path(__file__).parent.parent
                        calc_path = base_dir / "examples" / "calculator.sona"
                        
                        if calc_path.exists():
                            try:
                                with open(calc_path, "r") as f:
                                    calc_code = f.read()
                                run_code(calc_code)
                                print("\nReturned to Sona REPL.")
                            except Exception as e:
                                print(f"Error running calculator: {str(e)}")
                        else:
                            print(f"Error: Calculator application not found at {calc_path}")
                        continue
                        
                    # Quiz command
                    elif cmd in ["quiz"]:
                        print("\n=== Launching Sona Quiz ===")
                        
                        # Find quiz application
                        base_dir = Path(__file__).parent.parent
                        quiz_path = base_dir / "examples" / "quiz.sona"
                        
                        if quiz_path.exists():
                            try:
                                with open(quiz_path, "r") as f:
                                    quiz_code = f.read()
                                run_code(quiz_code)
                                print("\nReturned to Sona REPL.")
                            except Exception as e:
                                print(f"Error running quiz: {str(e)}")
                        else:
                            print(f"Error: Quiz application not found at {quiz_path}")
                        continue
                    
                    # Test command
                    elif cmd == "test":
                        run_tests()
                        continue
                    
                    # Debug command - Show last error and parse tree
                    elif cmd == "debug":
                        print("\n[DEBUG INFO]")
                        print(f"Last Error: {debug_state['last_error']}")
                        
                        if debug_state['last_tree']:
                            print("\nLast Parse Tree:")
                            if hasattr(debug_state['last_tree'], 'pretty'):
                                print(debug_state['last_tree'].pretty())
                            else:
                                print(pprint.pformat(debug_state['last_tree']))
                        else:
                            print("\nNo parse tree available. Run some code first.")
                        
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
                            
                        print("\nTip: Run some Sona code first, then use :debug to see details about its execution.")
                        continue
                    
                    # Profile command - Display execution time
                    elif cmd == "profile":
                        if debug_state['last_duration'] is not None:
                            duration_ms = debug_state['last_duration']
                            print(f"[PROFILE] Last command took {duration_ms:.2f}ms")
                            
                            # Provide context on execution time
                            if duration_ms < 1.0:
                                print("That's very fast! Less than 1ms execution time.")
                            elif duration_ms < 10.0:
                                print("That's fast! Less than 10ms execution time.")
                            elif duration_ms < 100.0:
                                print("That's a reasonable execution time.")
                            else:
                                print("That's relatively slow. Consider optimizing if this is in a loop.")
                        else:
                            print("[PROFILE] No previous command execution recorded")
                            print("Tip: Run some Sona code first, then use :profile to see its execution time.")
                        continue
                    
                    # Watch command - Print variable value
                    elif cmd.startswith("watch"):
                        var_name = cmd[5:].strip()
                        if not var_name:
                            print("[WATCH] Error: No variable name specified")
                            print("Usage: :watch <variable_name>")
                            print("Examples: ")
                            print("  :watch x       - Watch the variable 'x'")
                            print("  :watch counter - Watch the variable 'counter'")
                            continue
                        
                        if interpreter:
                            found = False
                            # Search through all scopes manually
                            for scope_idx, scope in enumerate(reversed(interpreter.env)):
                                depth = len(interpreter.env) - scope_idx - 1
                                if var_name in scope:
                                    value = scope[var_name]
                                    found = True
                                    scope_name = "global" if depth == 0 else f"local (depth {depth})"
                                    print(f"[WATCH] {var_name} = {value} (type: {type(value).__name__}) [scope: {scope_name}]")
                                    break
                            
                            # Check modules
                            if not found and hasattr(interpreter, 'modules') and var_name in interpreter.modules:
                                value = interpreter.modules[var_name]
                                found = True
                                print(f"[WATCH] {var_name} = {value} (type: module)")
                            
                            if not found:
                                print(f"[WATCH] Variable '{var_name}' not found in any scope")
                                print("Tip: Run 'let {0} = value' to define the variable first.".format(var_name))
                        else:
                            print("[WATCH] No interpreter available")
                            print("Tip: Run some code first to initialize the interpreter.")
                        continue
                    
                    # Trace command - Toggle function call tracing
                    elif cmd == "trace":
                        debug_state["trace_enabled"] = not debug_state["trace_enabled"]
                        status = "enabled" if debug_state["trace_enabled"] else "disabled"
                        print(f"[TRACE] Function call tracing is now {status}")
                        
                        if debug_state["trace_enabled"]:
                            print("Example trace output:")
                            print("  [TRACE] Calling function 'square' with args: [5]")
                            print("  [TRACE] Returned from 'square': 25")
                            print("Run any Sona code with function calls to see the trace.")
                        
                        continue
                        
                    # Unknown command
                    else:
                        print(f"Unknown command. Type :help for help")
                        continue
                
                # Also handle exit/quit when typed directly without colon
                lower_line = line.strip().lower()
                if lower_line in ["exit", "quit"]:
                    print("Exiting Sona REPL.")
                    break
            
            # Handle multiline input
            if not multiline_mode:
                # Start multiline mode if line ends with '{'
                if line.strip().endswith("{"):
                    multiline_mode = True
                    multiline_input = [line]
                    continue
                
                # Single line execution
                try:
                    # Reset the error state
                    debug_state["last_error"] = None
                    
                    # Parse the code (for debugging tools)
                    try:
                        debug_state["last_tree"] = parser.parse(line)
                    except Exception as parse_error:
                        # Continue with execution even if parsing for debug fails
                        debug_state["last_tree"] = None
                    
                    # Execute with timing
                    start_time = time.perf_counter()
                    
                    # Run with trace if enabled
                    if debug_state["trace_enabled"]:
                        # Create a fresh interpreter for consistent tracing
                        fresh_interpreter = SonaInterpreter()
                        result = run_code_with_trace(line, fresh_interpreter, parser)
                        # Update our reference to the interpreter for debugging
                        interpreter = fresh_interpreter
                    else:
                        # Use standard run_code but capture the interpreter for debugging
                        # We need to create a custom interpreter to capture it
                        fresh_interpreter = SonaInterpreter()
                        grammar_path = os.path.join(os.path.dirname(__file__), 'grammar.lark')
                        with open(grammar_path, 'r') as f:
                            grammar = f.read()
                        fresh_parser = Lark(grammar, parser='lalr', propagate_positions=True)
                        tree = fresh_parser.parse(line)
                        result = fresh_interpreter.transform(tree)
                        # Update our reference to the interpreter
                        interpreter = fresh_interpreter
                        
                    debug_state["last_duration"] = (time.perf_counter() - start_time) * 1000
                    
                    if result is not None:
                        print(result)
                except UnexpectedInput as ui:
                    debug_state["last_error"] = ui
                    print(f"Syntax error: {str(ui)}")
                except Exception as e:
                    debug_state["last_error"] = e
                    print(f"Error: {str(e)}")
                    
            else:
                # Add to multiline input
                multiline_input.append(line)
                
                # Check for end of multiline
                if line.strip() == "}":
                    # Execute multiline code
                    try:
                        multiline_code = "\n".join(multiline_input)
                        
                        # Reset the error state
                        debug_state["last_error"] = None
                        
                        # Parse the code (for debugging tools)
                        try:
                            debug_state["last_tree"] = parser.parse(multiline_code)
                        except Exception as parse_error:
                            # Continue with execution even if parsing for debug fails
                            debug_state["last_tree"] = None
                            
                        # Execute with timing
                        start_time = time.perf_counter()
                        
                        # Run with trace if enabled
                        if debug_state["trace_enabled"]:
                            # Create a fresh interpreter for consistent tracing
                            fresh_interpreter = SonaInterpreter()
                            result = run_code_with_trace(multiline_code, fresh_interpreter, parser)
                            # Update our reference to the interpreter for debugging
                            interpreter = fresh_interpreter
                        else:
                            # Use standard run_code but capture the interpreter for debugging
                            # We need to create a custom interpreter to capture it
                            fresh_interpreter = SonaInterpreter()
                            grammar_path = os.path.join(os.path.dirname(__file__), 'grammar.lark')
                            with open(grammar_path, 'r') as f:
                                grammar = f.read()
                            fresh_parser = Lark(grammar, parser='lalr', propagate_positions=True)
                            tree = fresh_parser.parse(multiline_code)
                            result = fresh_interpreter.transform(tree)
                            # Update our reference to the interpreter
                            interpreter = fresh_interpreter
                            
                        debug_state["last_duration"] = (time.perf_counter() - start_time) * 1000
                        
                        if result is not None:
                            print(result)
                    except UnexpectedInput as ui:
                        debug_state["last_error"] = ui
                        print(f"Syntax error: {str(ui)}")
                    except Exception as e:
                        debug_state["last_error"] = e
                        print(f"Error: {str(e)}")
                    
                    multiline_mode = False
                    multiline_input = []
                
        except KeyboardInterrupt:
            print("\nKeyboard interrupt. Type :exit to quit.")
            multiline_mode = False
            multiline_input = []
        except EOFError:
            print("\nExiting Sona REPL.")
            break

def run_code_with_trace(code, interpreter=None, parser=None):
    """Run code with function call tracing"""
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
            grammar_path = os.path.join(os.path.dirname(__file__), 'grammar.lark')
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

def run_tests():
    """Run diagnostic tests for the Sona REPL and language features"""
    print("\n=== Running Sona v0.5.1 Diagnostic Tests ===\n")
    
    test_results = {
        "passed": 0,
        "failed": 0,
        "total": 0
    }
    
    from sona.interpreter import SonaInterpreter
    from lark import Lark
    import os
    from pathlib import Path
    
    def get_parser():
        """Get a fresh parser instance"""
        grammar_path = Path(__file__).parent / 'grammar.lark'
        with open(grammar_path) as f:
            grammar = f.read()
        return Lark(grammar, parser="lalr", propagate_positions=True)
        
    def reset_env():
        """Reset the interpreter environment between tests"""
        return SonaInterpreter()
    
    def test(name, test_func):
        """Run a single test and report result"""
        test_results["total"] += 1
        print(f"Test {test_results['total']}: {name}...")
        
        try:
            interpreter = reset_env()  # Fresh environment for each test
            parser = get_parser()  # Fresh parser for each test
            result = test_func(interpreter, parser)
            if result:
                test_results["passed"] += 1
                print(f"  ✅ PASSED")
                return True
            else:
                test_results["failed"] += 1
                print(f"  ❌ FAILED")
                return False
        except Exception as e:
            test_results["failed"] += 1
            print(f"  ❌ FAILED with error: {str(e)}")
            return False
    
    # Test 1: Basic expression evaluation
    def test_basic_expression(interpreter, parser):
        tree = parser.parse("2 + 3 * 4")
        result = interpreter.transform(tree)
        return result == 14
    
    test("Basic arithmetic expressions", test_basic_expression)
    
    # Test 2: Variable assignment and access
    def test_variables(interpreter, parser):
        # Define variable
        var_tree = parser.parse("let x = 42")
        interpreter.transform(var_tree)
        
        # Access variable
        get_tree = parser.parse("x")
        result = interpreter.transform(get_tree)
        return result == 42
    
    test("Variable assignment and access", test_variables)
    
    # Test 3: Function definition and call
    def test_functions(interpreter, parser):
        # Define function
        func_tree = parser.parse("""
        func add(a, b) {
            return a + b
        }
        """)
        interpreter.transform(func_tree)
        
        # Call function
        call_tree = parser.parse("add(5, 7)")
        result = interpreter.transform(call_tree)
        return result == 12
    
    test("Function definition and call", test_functions)
    
    # Test 4: Nested function scopes
    def test_function_scope(interpreter, parser):
        # Define outer and inner functions
        funcs_tree = parser.parse("""
        let x = 10
        func outer(a) {
            let x = 20
            func inner(b) {
                return x + b
            }
            return inner(a)
        }
        """)
        interpreter.transform(funcs_tree)
        
        # Call outer function
        call_tree = parser.parse("outer(5)")
        result = interpreter.transform(call_tree)
        return result == 25
    
    test("Nested function scopes", test_function_scope)
    
    # Test 5: String operations
    def test_strings(interpreter, parser):
        # Define strings
        strings_tree = parser.parse("""
        let greeting = "Hello"
        let name = "World"
        let message = greeting + ", " + name + "!"
        """)
        interpreter.transform(strings_tree)
        
        # Access result
        result_tree = parser.parse("message")
        result = interpreter.transform(result_tree)
        return result == "Hello, World!"
    
    test("String operations", test_strings)
    
    # Test 6: Control structures (if statements)
    def test_if_else(interpreter, parser):
        # Define max function
        func_tree = parser.parse("""
        func max(a, b) {
            if a > b {
                return a
            } else {
                return b
            }
        }
        """)
        interpreter.transform(func_tree)
        
        # Call max function
        call_tree = parser.parse("max(8, 5)")
        result = interpreter.transform(call_tree)
        return result == 8
    
    test("If-else statements", test_if_else)
    
    # Test 7: Loops
    def test_loops(interpreter, parser):
        # Define sum function
        func_tree = parser.parse("""
        func sum_to(n) {
            let total = 0
            let i = 1
            while i <= n {
                total = total + i
                i = i + 1
            }
            return total
        }
        """)
        interpreter.transform(func_tree)
        
        # Call sum function
        call_tree = parser.parse("sum_to(5)")
        result = interpreter.transform(call_tree)
        return result == 15  # 1+2+3+4+5 = 15
    
    test("While loops", test_loops)
    
    # Test 8: Range operations
    def test_range_ops(interpreter, parser):
        # Define factorial function
        func_tree = parser.parse("""
        func factorial(n) {
            let result = 1
            let i = 1
            while i <= n {
                result = result * i
                i = i + 1
            }
            return result
        }
        """)
        interpreter.transform(func_tree)
        
        # Call factorial function
        call_tree = parser.parse("factorial(5)")
        result = interpreter.transform(call_tree)
        return result == 120  # 5! = 120
    
    test("Range operations", test_range_ops)
    
    # Test 9: Module import (if stdlib modules are set up)
    def test_module_import(interpreter, parser):
        try:
            # Import math module
            import_tree = parser.parse("""
            import utils.math.smod as math
            """)
            interpreter.transform(import_tree)
            
            # Access PI constant
            pi_tree = parser.parse("math.PI")
            result = interpreter.transform(pi_tree)
            return isinstance(result, (int, float)) and abs(result - 3.14159) < 0.1
        except:
            print("  ⚠️ Skipped: math module not available")
            return True
    
    test("Module import", test_module_import)
    
    # Test 10: Multiple statements
    def test_multi_statement(interpreter, parser):
        # Define and evaluate multiple statements
        tree = parser.parse("""
        let a = 10
        let b = 20
        a + b
        """)
        result = interpreter.transform(tree)
        return result == 30
    
    test("Multiple statements", test_multi_statement)
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Total tests: {test_results['total']}")
    print(f"Passed: {test_results['passed']}")
    print(f"Failed: {test_results['failed']}")
    
    if test_results['failed'] == 0:
        print("\n✅ All tests passed! Your Sona v0.5.1 installation is working correctly.")
    else:
        print("\n❌ Some tests failed. Please review the output above for details.")

def main():
    """Entry point for the Sona REPL"""
    # Check for debug mode flag
    if os.environ.get("SONA_DEBUG", "0") == "1":
        import sona.interpreter
        sona.interpreter.debug_mode = True
        print("[DEBUG] Debug mode enabled")
    
    run_repl()

if __name__ == "__main__":
    main()