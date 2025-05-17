import sys
import os
from pathlib import Path
from sona.interpreter import run_code
from sona import repl as sona_repl
from sona.utils.debug import debug, error
from lark import Lark, UnexpectedInput

def get_grammar_path():
    """Get the grammar file path in a platform-independent way"""
    return Path(__file__).resolve().parent / "grammar.lark"

def main():
    # Set debug mode from environment or command line flag
    if "--debug" in sys.argv:
        os.environ["SONA_DEBUG"] = "1"
        sys.argv.remove("--debug")

    if "--version" in sys.argv:
        from sona import __version__
        print(f"Sona Language Version: {__version__}")
        return

    # No arguments - start REPL
    if len(sys.argv) == 1:
        sona_repl.repl()  # Call repl() function directly
        return
    
    # Handle 'repl' command explicitly
    if len(sys.argv) == 2 and sys.argv[1] in ["repl", "--repl", "-r"]:
        sona_repl.repl()  # Call repl() function directly
        return
      # Handle file execution
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        error(f"File '{file_path}' does not exist.")
        print("Usage: sona [repl] [filename.sona]")
        sys.exit(1)
        
    # Process file
    try:
        code = file_path.read_text(encoding='utf-8')
        if not code.strip():
            error("File is empty.")
            sys.exit(1)
        debug(f"Running file: {file_path}")
        debug(f"Code:\n{code}")

        debug_mode = os.environ.get("SONA_DEBUG") == "1"
        run_code(code, debug_mode)
    except Exception as e:
        error(f"Failed to read or execute file: {e}")
        sys.exit(1)

def repl():
    print("\nSona REPL v0.4.3 - Type `exit` or `Ctrl+C` to quit.\n")
    from sona.interpreter import SonaInterpreter
    interpreter = SonaInterpreter()

    grammar_path = get_grammar_path()
    try:
        with open(grammar_path, encoding='utf-8') as f:
            grammar = f.read()
    except Exception as e:
        print(f"[ERROR] Failed to load grammar file: {e}")
        sys.exit(1)

    parser = Lark(grammar, parser="lalr", propagate_positions=True)
    buffer = ""

    while True:
        try:
            prompt = "sona> " if not buffer else "....> "
            try:
                line = input(prompt)
            except UnicodeDecodeError:
                print("[ERROR] Input encoding error. Please use UTF-8 encoding.")
                continue

            if line.strip() in ("exit", "quit"):
                print("Exiting Sona REPL.")
                break

            buffer += line + os.linesep  # Use OS-specific line separator

            try:
                tree = parser.parse(buffer)
                interpreter.transform(tree)
                buffer = ""  # reset after successful parse
            except UnexpectedInput:
                # Wait for more lines
                continue
        except KeyboardInterrupt:
            print("\nExiting Sona REPL.")
            break
        except Exception as e:
            print(f"[REPL ERROR] {e}")
            buffer = ""  # Reset the buffer after an error

def run_module():
    """Run Sona as a module (python -m sona)"""
    argv = sys.argv[1:]  # Remove 'python -m' from args
    sys.argv = [sys.argv[0]] + argv
    main()

if __name__ == "__main__":
    main()
elif __name__ == "__mp_main__":  # For multiprocessing support
    main()
