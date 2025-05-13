import sys
from sona.interpreter import run_code
from pathlib import Path
from sona import repl
from lark import Lark, UnexpectedInput
def main():
    if "--version" in sys.argv:
        version_file = Path(__file__).parent.parent / "VERSION"
        if version_file.exists():
            print("Sona Language Version:", version_file.read_text().strip())
        else:
            print("VERSION file not found.")
        return
    
    if len(sys.argv) == 2 and sys.argv[1] == "repl":
        repl()
        return
    
    if len(sys.argv) != 2:
        print("Usage: sona <filename.sona>")
        sys.exit(1)

    file_path = sys.argv[1]
    if not Path(file_path).exists():
        print(f"[ERROR] File '{file_path}' does not exist.")
        sys.exit(1)

    with open(file_path) as f:
        code = f.read()

    if not code.strip():
        print("[ERROR] File is empty.")
        sys.exit(1)
    print(f"[DEBUG] Running file: {file_path}")
    print(f"[DEBUG] Code:\n{code}")

    run_code(code)
def repl():
    print("\nSona REPL v0.4.3 - Type `exit` or `Ctrl+C` to quit.\n")
    from sona.interpreter import SonaInterpreter
    interpreter = SonaInterpreter()

    with open("sona/grammar.lark") as f:
        grammar = f.read()

    parser = Lark(grammar, parser="lalr", propagate_positions=True)
    buffer = ""

    while True:
        try:
            prompt = "sona> " if not buffer else "....> "
            line = input(prompt)
            if line.strip() in ("exit", "quit"):
                print("Exiting Sona REPL.")
                break

            buffer += line + "\n"

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
if __name__ == "__main__":
    main()
