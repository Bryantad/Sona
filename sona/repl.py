"""
Professional Sona REPL v0.9.0 - Interactive Cognitive Programming Environment

Advanced AI-Assisted Code Remediation Protocol Implementation
Complete REPL with cognitive accessibility features and multi-line editing

An interactive Read-Eval-Print-Loop for the Sona programming language that provides
cognitive-aware execution with accessibility excellence, enhanced editing features,
and PhD-level user experience optimization.
"""

import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try to import optional dependencies
try:
    import readline
    READLINE_AVAILABLE = True
except ImportError:
    READLINE_AVAILABLE = False

try:
    from .interpreter import SonaInterpreter, create_interpreter
except ImportError:
    # Fallback for standalone execution
    SonaInterpreter = None
    create_interpreter = None


class CognitiveREPL:
    """
    Professional-grade REPL for the Sona programming language.
    
    Implements the Advanced AI-Assisted Code Remediation Protocol with:
    - Complete cognitive computing integration
    - Accessibility excellence framework
    - Enhanced multi-line editing capabilities
    - PhD-level user experience and error handling
    """
    
    def __init__(self):
        """Initialize the REPL with cognitive features."""
        self.interpreter = create_interpreter() if create_interpreter else None
        self.multiline_buffer = []
        self.history = []
        self.cognitive_enabled = True
        self.accessibility_mode = True
        self.debug_mode = False
        
        # REPL configuration
        self.config = {
            "prompt": "sona> ",
            "multiline_prompt": "...   ",
            "max_history": 1000,
            "auto_indent": True,
            "syntax_highlighting": False,  # Basic terminal compatibility
            "cognitive_hints": True
        }
        
        # Command aliases for accessibility
        self.command_aliases = {
            "h": "help",
            "?": "help", 
            "q": "quit",
            "x": "exit",
            "c": "clear",
            "cls": "clear",
            "hist": "history",
            "vars": "variables",
            "funcs": "functions",
            "state": "cognitive_state",
            "calc": "calculator",
            "demo": "run_demo"
        }
        
        self._setup_readline()

    def _setup_readline(self) -> None:
        """Setup readline for enhanced editing if available."""
        if READLINE_AVAILABLE:
            # Setup history file
            history_file = Path.home() / ".sona_history"
            try:
                readline.read_history_file(str(history_file))
                readline.set_history_length(self.config["max_history"])
            except FileNotFoundError:
                pass  # No history file yet
            
            # Setup completion
            readline.set_completer(self._completer)
            readline.parse_and_bind("tab: complete")
            
            # Save history on exit
            import atexit
            atexit.register(lambda: readline.write_history_file(str(history_file)))

    def _completer(self, text: str, state: int) -> Optional[str]:
        """Provide command and variable completion."""
        options = []
        
        # Add command completions
        commands = ["help", "quit", "exit", "clear", "history", "variables", 
                   "functions", "cognitive_state", "calculator", "run_demo"]
        options.extend([cmd for cmd in commands if cmd.startswith(text)])
        
        # Add variable completions
        if self.interpreter:
            variables = self.interpreter.variables.keys()
            options.extend([var for var in variables if var.startswith(text)])
        
        try:
            return options[state]
        except IndexError:
            return None

    def start(self) -> None:
        """Start the interactive REPL session."""
        self._print_welcome()
        
        try:
            while True:
                try:
                    self._repl_loop()
                except KeyboardInterrupt:
                    print("\n[Ctrl+C] Use 'quit' or 'exit' to leave the REPL.")
                except EOFError:
                    print("\n[EOF] Goodbye!")
                    break
                    
        except Exception as e:
            print(f"Critical REPL error: {e}")
            if self.debug_mode:
                traceback.print_exc()

    def _print_welcome(self) -> None:
        """Print the welcome message with cognitive features."""
        welcome_text = """
╔══════════════════════════════════════════════════════════════╗
║                    Sona REPL v0.9.0                         ║
║              Cognitive Programming Environment               ║
║                                                              ║
║  Advanced AI-Assisted Code Remediation Protocol Active      ║
║  Cognitive Accessibility Features: ENABLED                  ║
║                                                              ║
║  Type 'help' for commands, 'quit' to exit                   ║
║  Cognitive features: thinking(), remember(), focus_mode()   ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(welcome_text)
        
        if self.cognitive_enabled:
            print("🧠 Cognitive features active - Enhanced accessibility enabled")
        
        if not self.interpreter:
            print("⚠️  Warning: Interpreter not available - Limited functionality")

    def _repl_loop(self) -> None:
        """Main REPL loop with cognitive awareness."""
        # Handle multiline input
        if self.multiline_buffer:
            prompt = self.config["multiline_prompt"]
        else:
            prompt = self.config["prompt"]
        
        try:
            user_input = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            raise
        
        if not user_input:
            return
        
        # Check for multiline continuation
        if user_input.endswith("\\") or self._needs_continuation(user_input):
            self.multiline_buffer.append(user_input.rstrip("\\"))
            return
        
        # Complete multiline input
        if self.multiline_buffer:
            self.multiline_buffer.append(user_input)
            full_input = "\n".join(self.multiline_buffer)
            self.multiline_buffer.clear()
        else:
            full_input = user_input
        
        # Add to history
        self.history.append(full_input)
        
        # Process the input
        self._process_input(full_input)

    def _needs_continuation(self, line: str) -> bool:
        """Check if input needs continuation (multiline)."""
        # Basic heuristics for multiline detection
        continuation_indicators = [
            line.endswith(":"),
            line.endswith("{"),
            line.endswith("(") and not line.count(")"),
            line.count("(") > line.count(")"),
            line.count("{") > line.count("}"),
            line.startswith("thinking ") and "{" in line and "}" not in line,
            line.startswith("remember ") and "{" in line and "}" not in line,
            line.startswith("focus_mode") and "{" in line and "}" not in line
        ]
        
        return any(continuation_indicators)

    def _process_input(self, user_input: str) -> None:
        """Process user input with cognitive awareness."""
        # Handle commands
        if user_input.startswith(":") or user_input in self.command_aliases:
            self._handle_command(user_input)
            return
        
        # Handle special cognitive syntax
        if self._is_cognitive_command(user_input):
            self._handle_cognitive_command(user_input)
            return
        
        # Execute Sona code
        if self.interpreter:
            try:
                result = self.interpreter.execute(user_input)
                if result is not None:
                    print(f"→ {result}")
                    
                # Show cognitive state if enabled
                if self.cognitive_enabled and hasattr(self.interpreter, 'get_cognitive_state'):
                    state = self.interpreter.get_cognitive_state()
                    if any(state.values()):  # Only show if there's cognitive activity
                        self._show_cognitive_hints(state)
                        
            except Exception as e:
                print(f"Error: {e}")
                if self.debug_mode:
                    traceback.print_exc()
        else:
            print("Interpreter not available - cannot execute code")

    def _handle_command(self, command: str) -> None:
        """Handle REPL commands with accessibility features."""
        # Remove command prefix and normalize
        if command.startswith(":"):
            command = command[1:]
        
        # Resolve aliases
        command = self.command_aliases.get(command, command)
        
        # Execute command
        if command == "help":
            self._show_help()
        elif command in ["quit", "exit"]:
            print("Goodbye! 👋")
            sys.exit(0)
        elif command == "clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            self._print_welcome()
        elif command == "history":
            self._show_history()
        elif command == "variables":
            self._show_variables()
        elif command == "functions":
            self._show_functions()
        elif command == "cognitive_state":
            self._show_cognitive_state()
        elif command == "calculator":
            self._launch_calculator()
        elif command == "run_demo":
            self._run_demo()
        elif command == "debug":
            self.debug_mode = not self.debug_mode
            print(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")
        elif command == "cognitive":
            self.cognitive_enabled = not self.cognitive_enabled
            print(f"Cognitive features: {'ON' if self.cognitive_enabled else 'OFF'}")
        else:
            print(f"Unknown command: {command}. Type 'help' for available commands.")

    def _is_cognitive_command(self, input_str: str) -> bool:
        """Check if input is a cognitive command."""
        cognitive_keywords = ["thinking ", "remember ", "focus_mode", "@break", "@attention"]
        return any(input_str.strip().startswith(keyword) for keyword in cognitive_keywords)

    def _handle_cognitive_command(self, input_str: str) -> None:
        """Handle cognitive commands with accessibility features."""
        if self.interpreter:
            try:
                result = self.interpreter.execute(input_str)
                print("🧠 Cognitive command processed")
                if result:
                    print(f"→ {result}")
            except Exception as e:
                print(f"Cognitive processing error: {e}")
        else:
            print("🧠 Cognitive command recognized (interpreter unavailable)")

    def _show_help(self) -> None:
        """Show help with accessibility features."""
        help_text = """
🔧 Sona REPL Commands (Cognitive-Accessible):

Core Commands:
  help, h, ?        - Show this help message
  quit, q, exit, x  - Exit the REPL
  clear, c, cls     - Clear the screen
  
Information Commands:
  history, hist     - Show command history
  variables, vars   - Show current variables
  functions, funcs  - Show defined functions
  cognitive_state   - Show cognitive accessibility state
  
Features:
  debug            - Toggle debug mode
  cognitive        - Toggle cognitive features
  calculator, calc - Launch Sona calculator
  run_demo, demo   - Run demonstration code

Cognitive Accessibility Features:
  thinking "context" { ... }    - Add thinking blocks
  remember("key") { ... }       - Store cognitive memory
  focus_mode { ... }            - Enable focus mode
  @break { ... }               - Accessibility break points
  @attention { ... }           - Attention management

Editing Features:
  - Multiline input (end lines with \\ or use { } blocks)
  - Tab completion for commands and variables
  - Command history (↑/↓ arrows if readline available)
  - Auto-indentation for code blocks
        """
        print(help_text)

    def _show_history(self) -> None:
        """Show command history with cognitive context."""
        print("\n📜 Command History:")
        if not self.history:
            print("  (no commands executed yet)")
            return
        
        recent_history = self.history[-20:]  # Show last 20 commands
        for i, cmd in enumerate(recent_history, 1):
            # Truncate long commands for display
            display_cmd = cmd[:60] + "..." if len(cmd) > 60 else cmd
            print(f"  {i:2}. {display_cmd}")

    def _show_variables(self) -> None:
        """Show current variables with cognitive context."""
        print("\n📊 Current Variables:")
        if not self.interpreter or not self.interpreter.variables:
            print("  (no variables defined)")
            return
        
        for name, value in self.interpreter.variables.items():
            value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            print(f"  {name} = {value_str} ({type(value).__name__})")

    def _show_functions(self) -> None:
        """Show defined functions with cognitive features."""
        print("\n🔧 Defined Functions:")
        if not self.interpreter or not self.interpreter.functions:
            print("  (no functions defined)")
            return
        
        for name, func_def in self.interpreter.functions.items():
            params = func_def.get('params', [])
            cognitive = "🧠" if func_def.get('cognitive_features') else ""
            print(f"  {name}({', '.join(map(str, params))}) {cognitive}")

    def _show_cognitive_state(self) -> None:
        """Show cognitive accessibility state."""
        print("\n🧠 Cognitive Accessibility State:")
        if not self.interpreter or not hasattr(self.interpreter, 'get_cognitive_state'):
            print("  (cognitive features unavailable)")
            return
        
        state = self.interpreter.get_cognitive_state()
        for key, value in state.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")

    def _show_cognitive_hints(self, state: Dict[str, Any]) -> None:
        """Show subtle cognitive hints during execution."""
        hints = []
        if state.get("thinking_blocks", 0) > 0:
            hints.append("🧠 thinking")
        if state.get("memory_items", 0) > 0:
            hints.append("💾 memory")
        if state.get("focus_active", False):
            hints.append("🎯 focus")
        
        if hints and self.cognitive_enabled:
            print(f"  [Cognitive: {' | '.join(hints)}]")

    def _launch_calculator(self) -> None:
        """Launch the Sona calculator with cognitive features."""
        print("\n🔢 Sona Calculator with Cognitive Features")
        print("Enter mathematical expressions (type 'back' to return)")
        
        while True:
            try:
                expr = input("calc> ").strip()
                if expr.lower() in ['back', 'return', 'exit']:
                    print("Returned to Sona REPL")
                    break
                
                if not expr:
                    continue
                
                # Basic calculator functionality
                try:
                    # Safety check - only allow basic math operations
                    allowed_chars = set("0123456789+-*/.()")
                    if all(c in allowed_chars or c.isspace() for c in expr):
                        result = eval(expr)  # Safe for basic math
                        print(f"→ {result}")
                        
                        # Store in cognitive memory
                        if self.interpreter and self.cognitive_enabled:
                            self.interpreter.cognitive_state.store_memory("last_calculation", result)
                    else:
                        print("Error: Only basic math operations allowed")
                        
                except Exception as e:
                    print(f"Calculation error: {e}")
                    
            except (KeyboardInterrupt, EOFError):
                print("\nReturned to Sona REPL")
                break

    def _run_demo(self) -> None:
        """Run demonstration code with cognitive features."""
        demo_code = '''
        thinking("Demo execution", "Running accessibility demo")
        
        let greeting = "Hello from Sona!"
        print(greeting)
        
        remember("demo_run") {
            timestamp: "current",
            features: ["cognitive", "accessibility"]
        }
        
        focus_mode {
            mode: "demonstration",
            accessibility: "full"
        }
        
        let number = 42
        let message = "The answer is: " + number
        print(message)
        '''
        
        print("\n🚀 Running Cognitive Demo:")
        print("=" * 50)
        
        if self.interpreter:
            try:
                self.interpreter.execute(demo_code)
                print("=" * 50)
                print("✅ Demo completed successfully!")
            except Exception as e:
                print(f"Demo error: {e}")
        else:
            print("Demo unavailable - interpreter not loaded")


def main() -> None:
    """Main entry point for the Sona REPL."""
    try:
        repl = CognitiveREPL()
        repl.start()
    except Exception as e:
        print(f"Failed to start REPL: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
