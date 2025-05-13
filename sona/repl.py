from lark import Lark, UnexpectedInput
from sona.interpreter import SonaInterpreter

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
:env      Display current variable values
:clear    Reset all variables and functions
:reload   Reload grammar and interpreter
:exit     Exit the REPL
""")

def main():
    print("Sona REPL v0.4.3 - Type `:help` or `exit` to quit.\n")

    def load_interpreter():
        with open("sona/grammar.lark") as f:
            grammar = f.read()
        return Lark(grammar, parser="lalr", propagate_positions=True), SonaInterpreter()

    parser, interpreter = load_interpreter()
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
            if user_input.strip() == ":help":
                print_help()
                continue
            if user_input.strip() == ":env":
                print("[ENVIRONMENT DUMP]")
                for scope in interpreter.env:
                    if isinstance(scope, dict):
                        for k, v in scope.items():
                            print(f"{k} = {v}")
                continue
            if user_input.strip() == ":clear":
                parser, interpreter = load_interpreter()
                buffer.clear()
                open_braces = 0
                print("[REPL] Cleared interpreter state.")
                continue
            if user_input.strip() == ":reload":
                parser, interpreter = load_interpreter()
                print("[REPL] Grammar and interpreter reloaded.")
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

            try:
                tree = parser.parse(code)
                result = interpreter.transform(tree)
                if result is not None:
                    print(f"[OUTPUT] {result}")
            except UnexpectedInput as e:
                print(f"[SYNTAX ERROR] {str(e).strip()}")
            except Exception as e:
                print(f"[REPL ERROR] {str(e)}")
            finally:
                buffer.clear()
                open_braces = 0

        except (KeyboardInterrupt, EOFError):
            print("\nExiting Sona REPL.")
            break

if __name__ == "__main__":
    main()