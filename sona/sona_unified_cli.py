#!/usr/bin/env python
"""
Sona CLI v0.9.0 - Unified Interpreter

This CLI script runs Sona programs using the unified interpreter,
supporting both traditional and cognitive accessibility syntax.
"""

import sys

from sona.unified_interpreter import SonaUnifiedInterpreter


def main(): """Main CLI entry point"""
    interpreter = SonaUnifiedInterpreter()

    if len(sys.argv) > 1: # Run a file
        file_path = sys.argv[1]
        try: with open(file_path, 'r') as f: code = f.read()
            interpreter.execute(code)
        except FileNotFoundError: print(f"Error: File not found: {file_path}")
        except Exception as e: print(f"Error executing code: {str(e)}")
    else: # Interactive mode
        print("Sona 0.9.0 Interactive Mode (Ctrl+D to exit)")
        while True: try: line = input("sona> ")
                result = interpreter.execute(line)
                if result is not None: print(result)
            except EOFError: print("\nGoodbye!")
                break
            except KeyboardInterrupt: print("\nInterrupted")
            except Exception as e: print(f"Error: {str(e)}")


if __name__ == "__main__": main()
