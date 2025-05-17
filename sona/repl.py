"""Sona REPL with support for all standard library modules"""

import os
from lark import Lark, UnexpectedInput
from pathlib import Path
from sona.interpreter import SonaInterpreter
from sona.utils.debug import debug, warn, error

# Import all stdlib modules
BUILTIN_MODULES = {
    "math": "utils.math.smod",
    "random": "utils.random.smod",
    "string": "utils.string.smod",
    "convert": "utils.convert.smod",
    "validate": "utils.validate.smod",
    "greeting": "greeting",
    "native_stdin": "native_stdin",
    "io": "native_io",
    "fs": "native_fs",
    "json": "native_json",
    "time": "time"
}

def preload_modules(interpreter):
    """Preload all standard library modules into the REPL environment"""
    from sona.utils.suppress import suppress_debug_output
    
    debug_mode = os.environ.get("SONA_DEBUG") == "1"
    
    # Import modules with output suppression if not in debug mode
    with suppress_debug_output():
        for name, module_path in BUILTIN_MODULES.items():
            try:
                code = f"import {module_path}"
                tree = interpreter.parser.parse(code)
                interpreter.transform(tree)
                debug(f"Successfully loaded {name} module")
            except Exception as e:
                if debug_mode:
                    warn(f"Could not preload {name} module: {str(e)}")

def expose_greeting_functions(interpreter):
    """Expose greeting functions to the global scope for easy access in the REPL"""
    try:
        # Create proxy functions in the global environment
        hi_func = lambda: interpreter.env[-1]["greeting"].hi()
        hello_func = lambda name="": interpreter.env[-1]["greeting"].hello(name)
        greet_func = lambda name="friend": interpreter.env[-1]["greeting"].greet(name)
        say_func = lambda message: interpreter.env[-1]["greeting"].say(message)
        
        # Register our proxy functions in the global environment
        # Make sure greeting module is loaded first
        try:
            if "greeting" not in interpreter.env[-1]:
                code = "import greeting"
                tree = interpreter.parser.parse(code)
                interpreter.transform(tree)
                debug("Successfully loaded greeting module for global functions")
                
            # Add the proxy functions to the global namespace
            interpreter.env[-1]["hi"] = hi_func
            debug("Successfully exposed hi() function globally")
            
            interpreter.env[-1]["hello"] = hello_func
            debug("Successfully exposed hello() function globally")
            
            interpreter.env[-1]["greet"] = greet_func
            debug("Successfully exposed greet() function globally")
            
            interpreter.env[-1]["say"] = say_func
            debug("Successfully exposed say() function globally")
        except Exception as e:
            warn(f"Could not expose greeting functions: {str(e)}")
    except Exception as e:
        warn(f"Could not expose greeting functions: {str(e)}")

def is_function_definition(code):
    return code.strip().startswith("func ")

def collect_multiline_block(start_line, prompt="....> "):
    lines = [start_line]
    open_braces = start_line.count("{")
    close_braces = start_line.count("}")
    while open_braces > close_braces:
        try:
            next_line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print("\n[REPL ERROR] Unexpected termination during multi-line block.")
            return ""
        lines.append(next_line)
        open_braces += next_line.count("{")
        close_braces += next_line.count("}")
    return "\n".join(lines)

def print_help():
    print("""\
[Sona REPL Commands]
:help     Show this help message
:version  Show Sona version information
:env      Display current variable values
:clear    Reset all variables and functions
:reload   Reload grammar and interpreter
:modules  List available modules
:doc      Show documentation for a module (e.g. :doc math)
:example  Show example code (e.g. :example math)
:exit     Exit the REPL
""")

def list_modules():
    """List all available modules with their status"""
    print("\nAvailable Modules:")
    print("================")
    # Get max length for padding
    max_name = max(len(name) for name in BUILTIN_MODULES.keys())
    
    for name, path in sorted(BUILTIN_MODULES.items()):
        # Check if documentation exists
        has_docs = False
        has_examples = False
        try:
            from sona.stdlib.docs import MODULE_DOCS
            if name in MODULE_DOCS:
                has_docs = "description" in MODULE_DOCS[name]
                has_examples = "example" in MODULE_DOCS[name]
        except ImportError:
            pass

        # Create status indicators
        doc_status = "📚" if has_docs else "  "
        example_status = "💡" if has_examples else "  "
        
        # Pad module names for alignment
        padded_name = name.ljust(max_name)
        print(f"- {padded_name}  {doc_status} {example_status}  =>  {path}")
    
    print("\nLegend:")
    print("📚 - Documentation available (:doc <module>)")
    print("💡 - Examples available (:example <module>)")

def show_module_doc(interpreter, module_name):
    """Show documentation for a module"""
    if module_name not in BUILTIN_MODULES:
        print(f"[ERROR] Unknown module '{module_name}'. Use :modules to list available modules.")
        return
    
    try:
        from sona.stdlib.docs import show_module_doc as _show_doc
        _show_doc(module_name)
    except (ImportError, AttributeError) as e:
        print(f"[ERROR] Documentation not available for module '{module_name}': {e}")

def show_module_example(interpreter, module_name):
    """Show example code for a module"""
    if module_name not in BUILTIN_MODULES:
        print(f"[ERROR] Unknown module '{module_name}'. Use :modules to list available modules.")
        return
        
    try:
        from sona.stdlib.docs import show_module_example as _show_example
        _show_example(module_name)
    except (ImportError, AttributeError) as e:
        print(f"[ERROR] Examples not available for module '{module_name}': {e}")

def handle_command(line, interpreter):
    """Handle REPL commands"""
    try:
        if line == ":help":
            print_help()
        elif line == ":version":
            from sona import __version__, __author__, __description__
            print(f"\nSona Language v{__version__}")
            print(f"Author: {__author__}")
            print(f"Description: {__description__}\n")
        elif line == ":env":
            if not interpreter.env or not interpreter.env[-1]:
                print("\nEnvironment is empty")
            else:
                print("\nCurrent environment:")
                for name, value in interpreter.env[-1].items():
                    print(f"{name} = {value}")
        elif line == ":clear":
            interpreter.env = [{}]
            interpreter.functions = {}
            print("Environment cleared")
        elif line == ":reload":
            try:
                interpreter.__init__()
                print("Grammar and interpreter reloaded")
                # Reload modules after interpreter reset
                preload_modules(interpreter)
            except Exception as e:
                print(f"[ERROR] Failed to reload interpreter: {str(e)}")
        elif line == ":modules":
            list_modules()
        elif line.startswith(":doc "):
            module_name = line[5:].strip()
            if not module_name:
                print("[ERROR] Missing module name. Usage: :doc <module_name>")
            else:
                show_module_doc(interpreter, module_name)
        elif line.startswith(":example "):
            module_name = line[9:].strip()
            if not module_name:
                print("[ERROR] Missing module name. Usage: :example <module_name>")
            else:
                show_module_example(interpreter, module_name)
        elif line == ":exit":
            return False
        else:
            print("Unknown command. Type :help for help")
        return True
    except Exception as e:
        print(f"[ERROR] Command failed: {str(e)}")
        return True  # Keep REPL running even if command fails

def repl():
    """Start the Sona REPL"""
    from sona import __version__
    debug_mode = os.environ.get("SONA_DEBUG") == "1"
    
    # Set environment variable to configure modules' debug output
    if not debug_mode:
        os.environ["SONA_MODULE_SILENT"] = "1"
        
    if debug_mode:
        print(f"Sona REPL v{__version__} [debug: on] - Type `:help` or `exit` to quit.\n")
    else:
        print(f"Sona REPL v{__version__} - Type `:help` or `exit` to quit.\n")

    def load_interpreter():
        """Load the Sona grammar and create interpreter instance"""
        grammar_path = Path(__file__).parent / "grammar.lark"
        with open(grammar_path) as f:
            grammar = f.read()
        parser = Lark(grammar, parser="lalr", propagate_positions=True)
        interpreter = SonaInterpreter()
        interpreter.parser = parser  # Store parser reference for module loading
        return parser, interpreter

    parser, interpreter = load_interpreter()
    preload_modules(interpreter)
    expose_greeting_functions(interpreter)
    buffer = []
    open_braces = 0

    while True:
        try:
            prompt = "....> " if open_braces > 0 else "sona> "
            user_input = input(prompt).rstrip()

            if user_input.strip() == "":
                continue

            if user_input.strip() in {"exit", ":exit"}:
                print("Exiting Sona REPL.")
                break

            # Handle REPL commands
            if user_input.strip().startswith(":"):
                if not handle_command(user_input.strip(), interpreter):
                    break
                continue

            # Collect multi-line function definitions
            if is_function_definition(user_input):
                user_input = collect_multiline_block(user_input)
                if not user_input.strip():
                    continue

            open_braces += user_input.count("{") - user_input.count("}")
            buffer.append(user_input)

            if open_braces > 0:
                continue

            code = "\n".join(buffer)
            
            # Special handling for greeting commands
            greeting_commands = {
                "hi": lambda: interpreter.env[-1]["greeting"].hi() if "greeting" in interpreter.env[-1] else None,
                "hello": lambda name="": interpreter.env[-1]["greeting"].hello(name) if "greeting" in interpreter.env[-1] else None,
                "greet": lambda name="friend": interpreter.env[-1]["greeting"].greet(name) if "greeting" in interpreter.env[-1] else None,
                "say": lambda message="": interpreter.env[-1]["greeting"].say(message) if "greeting" in interpreter.env[-1] else None,
            }
            
            # Check if this is a simple greeting command
            cmd_parts = code.strip().split()
            if cmd_parts and cmd_parts[0] in greeting_commands:
                cmd_name = cmd_parts[0]
                # Get arguments (everything after the command name)
                args = code.strip()[len(cmd_name):].strip()
                
                try:
                    # Handle different commands with their arguments
                    if cmd_name == "hi" and (not args or args.isspace()):
                        result = greeting_commands["hi"]()
                        if result is not None:
                            print(result)
                    elif cmd_name == "hello":
                        if args:
                            result = greeting_commands["hello"](args.strip())
                            if result is not None:
                                print(result)
                        else:
                            result = greeting_commands["hello"]()
                            if result is not None:
                                print(result)
                    elif cmd_name == "greet":
                        if args:
                            result = greeting_commands["greet"](args.strip())
                            if result is not None:
                                print(result)
                        else:
                            result = greeting_commands["greet"]()
                            if result is not None:
                                print(result)
                    elif cmd_name == "say" and args:
                        result = greeting_commands["say"](args.strip())
                        if result is not None:
                            print(result)
                    else:
                        # Fall back to regular parsing if command format is invalid
                        tree = parser.parse(code)
                        result = interpreter.transform(tree)
                        if result is not None:
                            print(result)
                except Exception as e:
                    if "greeting" not in interpreter.env[-1]:
                        print("[REPL ERROR] Greeting module not loaded. Try 'import greeting' first.")
                    else:
                        print(f"[REPL ERROR] {str(e)}")
            else:
                # Regular parsing for non-greeting commands
                try:
                    tree = parser.parse(code)
                    result = interpreter.transform(tree)
                    if result is not None:
                        print(result)
                except UnexpectedInput as e:
                    print(f"[SYNTAX ERROR] {str(e).strip()}")
                except Exception as e:
                    print(f"[REPL ERROR] {str(e)}")
            
            # Reset buffer regardless of success or failure
            buffer.clear()
            open_braces = 0

        except (KeyboardInterrupt, EOFError):
            print("\nExiting Sona REPL.")
            break

main = repl  # Alias main to repl for backwards compatibility

if __name__ == "__main__":
    repl()