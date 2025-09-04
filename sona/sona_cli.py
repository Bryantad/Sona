#!/usr/bin/env python3
"""
Sona CLI - Command Line Interface for Sona Programming Language
============================================================

Simple and clean CLI to fix the indentation errors and get Sona working.
"""

import sys
import os
from pathlib import Path


def get_grammar_path():
    """Get the grammar file path in a platform-independent way"""
    return Path(__file__).resolve().parent / "grammar.lark"


def main():
    """Main CLI entry point"""
    print("🚀 Sona Programming Language CLI v0.9.0")
    
    if len(sys.argv) == 1:
        # No arguments - start REPL
        print("Starting interactive Sona REPL...")
        start_repl()
    else:
        command = sys.argv[1]
        args = sys.argv[2:]
        
        if command == "help" or command == "--help" or command == "-h":
            print_help()
        elif command == "repl":
            start_repl()
        elif command == "version" or command == "--version":
            print("Sona v0.9.0 - AI-Native Programming Language")
        elif command.endswith('.sona'):
            # Execute Sona file
            execute_file(command)
        else:
            print(f"Unknown command: {command}")
            print("Use 'sona help' for available commands")


def print_help():
    """Print help information"""
    print("""
Sona Programming Language CLI

Usage:
  sona                    Start interactive REPL
  sona <file.sona>        Execute a Sona file
  sona repl               Start interactive REPL
  sona help               Show this help
  sona version            Show version

Examples:
  sona                    # Start REPL
  sona my_program.sona    # Run a Sona file
  sona repl               # Start REPL explicitly
""")


def start_repl():
    """Start the Sona REPL"""
    try:
        # Import the canonical interpreter
        from sona.interpreter import SonaInterpreter
        
        interpreter = SonaInterpreter()
        print("✅ Sona REPL ready! Type 'exit' to quit.")
        print("💡 Try: explain('Hello World'), think('how to code'), ai_complete('function')")
        print()
        
        while True:
            try:
                user_input = input("sona> ").strip()
                
                if user_input.lower() in ['exit', 'quit', ':q']:
                    print("👋 Goodbye!")
                    break
                
                if user_input:
                    result = interpreter.interpret(user_input)
                    if result is not None:
                        print(f"=> {result}")
                        
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except ImportError as e:
        print(f"❌ Failed to import Sona interpreter: {e}")
        print("💡 Make sure Sona is properly installed")


def execute_file(file_path):
    """Execute a Sona file"""
    try:
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return
        
        # Import the canonical interpreter
        from sona.interpreter import SonaInterpreter
        
        interpreter = SonaInterpreter()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        print(f"🚀 Executing: {file_path}")
        result = interpreter.interpret(code)
        
        if result is not None:
            print(f"=> {result}")
            
    except ImportError as e:
        print(f"❌ Failed to import Sona interpreter: {e}")
    except Exception as e:
        print(f"❌ Execution failed: {e}")


if __name__ == "__main__":
    main()
