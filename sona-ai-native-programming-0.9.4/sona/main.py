#!/usr/bin/env python3
"""
Sona Programming Language v0.9.2 - Main Entry Point
==================================================

World's first AI-native programming language with cognitive accessibility features.

Usage:
    python main.py [file.sona]      # Run a Sona program
    python main.py --repl          # Start interactive REPL
    python main.py --version       # Show version info
    python main.py --test          # Run test suite

Author: Sona AI Team
Version: 0.9.2
Date: August 8, 2025
"""

import argparse
import os
import sys


# Add the sona directory to Python path
sys.path.append(os.path.dirname(__file__))

try:
    from interpreter import SonaInterpreter  # Canonical interpreter path
    from parser_v090 import SonaParserv090
except ImportError as e:
    print(f"❌ Error importing Sona components: {e}")
    print("Please ensure all Sona dependencies are installed.")
    sys.exit(1)


def show_version():
    """Display version information."""
    print("=" * 60)
    print("🌟 Sona Programming Language v0.9.2")
    print("=" * 60)
    print("World's First AI-Native Programming Language")
    print("With Cognitive Accessibility Features")
    print("")
    print("Features:")
    print("  • 50+ built-in functions")
    print("  • Real AI integration (OpenAI, Anthropic, Azure)")
    print("  • Cognitive accessibility support")
    print("  • Natural language programming")
    print("  • Working memory and focus mode")
    print("  • Enterprise-ready infrastructure")
    print("")
    print("Author: Sona AI Team")
    print("Date: August 8, 2025")
    print("License: MIT")
    print("=" * 60)


def run_file(file_path):
    """Run a Sona program file."""
    try:
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        print(f"🚀 Running Sona program: {file_path}")
        
        # Read the file
        with open(file_path, encoding='utf-8') as f:
            code = f.read()
        
        # Parse and interpret
        parser = SonaParserv090()
        interpreter = SonaInterpreter()
        
        # Parse the code
        tree = parser.parse(code)
        print("✅ Parsed successfully")
        
        # Execute the code
        result = interpreter.execute(tree)
        print("✅ Execution completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error running Sona program: {e}")
        return False


def start_repl():
    """Start interactive REPL."""
    print("=" * 60)
    print("🌟 Sona AI-Native REPL v0.9.2")
    print("=" * 60)
    print("Type 'help()' for help, 'exit()' to quit")
    print("AI functions available: ai_complete(), working_memory(), focus_mode()")
    print("")
    
    interpreter = SonaInterpreter()
    parser = SonaParserv090()
    
    while True:
        try:
            # Get input
            code = input("sona> ")
            
            # Handle special commands
            if code.strip() in ['exit()', 'quit()', 'exit', 'quit']:
                print("👋 Goodbye!")
                break
            elif code.strip() in ['help()', 'help']:
                show_help()
                continue
            elif code.strip() == '':
                continue
            
            # Parse and execute
            try:
                tree = parser.parse(code)
                result = interpreter.execute(tree)
                if result is not None:
                    print(f"=> {result}")
            except Exception as e:
                print(f"❌ Error: {e}")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            print("\n👋 Goodbye!")
            break


def show_help():
    """Show REPL help."""
    print("""
🌟 Sona REPL Help
================

Basic Commands:
  help()         - Show this help
  exit()         - Exit REPL
  
Core Functions:
  print("text")  - Display text
  let x = 5      - Variable assignment
  
AI Functions:
  ai_complete("prompt")     - AI code completion
  ai_explain(code)          - AI code explanation
  ai_debug(code)            - AI debugging assistance
  
Cognitive Functions:
  working_memory()          - Access working memory
  focus_mode(true)          - Enable focus mode
  cognitive_check()         - Check cognitive state
  
Natural Language:
  explain("concept")        - Get explanations
  simplify("complex idea")  - Simplify concepts
  think("problem")          - Metacognitive processing
  
Examples:
  sona> let greeting = ai_complete("function that says hello")
  sona> print(greeting)
  sona> explain("recursion")
  sona> focus_mode(true)
""")


def run_tests():
    """Run Sona test suite."""
    print("🧪 Running Sona v0.9.2 Test Suite...")
    
    try:
        interpreter = SonaInterpreter()
        parser = SonaParserv090()
        
        # Test basic operations
        tests = [
            ('print("Hello, Sona!")', "Basic print"),
            ('let x = 42', "Variable assignment"),
            ('print(x)', "Variable access"),
            ('let y = x + 8', "Arithmetic"),
            ('print(y)', "Expression evaluation"),
        ]
        
        passed = 0
        for code, description in tests:
            try:
                tree = parser.parse(code)
                result = interpreter.execute(tree)
                print(f"  ✅ {description}")
                passed += 1
            except Exception as e:
                print(f"  ❌ {description}: {e}")
        
        print(f"\nTest Results: {passed}/{len(tests)} passed")
        
        # Test function count
        function_count = len([f for f in dir(interpreter) if callable(getattr(interpreter, f)) and not f.startswith('_')])
        print(f"Functions available: {function_count}")
        
        if function_count >= 50:
            print("✅ 50+ function requirement met!")
        else:
            print(f"⚠️  Only {function_count} functions (target: 50)")
        
        return passed == len(tests)
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sona Programming Language v0.9.2 - World's First AI-Native Language",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py program.sona     # Run a Sona program
  python main.py --repl          # Start interactive mode
  python main.py --version       # Show version
  python main.py --test          # Run tests
        """
    )
    
    parser.add_argument('file', nargs='?', help='Sona program file to run')
    parser.add_argument('--version', action='store_true', help='Show version information')
    parser.add_argument('--repl', action='store_true', help='Start interactive REPL')
    parser.add_argument('--test', action='store_true', help='Run test suite')
    
    args = parser.parse_args()
    
    # Handle arguments
    if args.version:
        show_version()
    elif args.test:
        success = run_tests()
        sys.exit(0 if success else 1)
    elif args.repl:
        start_repl()
    elif args.file:
        success = run_file(args.file)
        sys.exit(0 if success else 1)
    else:
        # No arguments - show help and start REPL
        show_version()
        print("\nNo file specified. Starting REPL mode...")
        print("Use --help for more options.")
        print()
        start_repl()


if __name__ == "__main__":
    main()
