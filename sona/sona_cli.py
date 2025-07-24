import os
import subprocess
import sys
from pathlib import Path

from lark import Lark, UnexpectedInput

from sona.cognitive_repl import CognitiveREPL
from sona.interpreter import SonaUnifiedInterpreter
from sona.utils.debug import debug, error
from sona_transpiler import transpile_sona_code


def get_grammar_path(): """Get the grammar file path in a platform-independent way"""
    return Path(__file__).resolve().parent / "grammar.lark"


def transpile_command(args): """Handle transpile command"""
    if len(args) < 2: print(
            "Usage: sona transpile <file.sona> [--target language] "
            "[--output file.ext]"
        )
        print(
            "Supported languages: python, javascript, typescript, java, "
            "csharp, go, rust"
        )
        return

    file_path = args[0]
    target_language = "python"  # default
    output_file = None

    # Parse arguments
    i = 1
    while i < len(args): if args[i] = (
        ( = "--target" and i + 1 < len(args): target_language = args[i + 1]
    )
    )
            i + = 2
        elif args[i] = (
            ( = "--output" and i + 1 < len(args): output_file = args[i + 1]
        )
        )
            i + = 2
        else: i + = 1

    try: # Read source file
        with open(file_path, 'r', encoding = (
            'utf-8') as f: sona_code = f.read()
        )

        # Transpile
        transpiled_code = transpile_sona_code(sona_code, target_language)

        # Output
        if output_file: with open(output_file, 'w', encoding = (
            'utf-8') as f: f.write(transpiled_code)
        )
            print(
                f"✅ Transpiled to {target_language} and saved to "
                f"{output_file}"
            )
        else: print(f"=== Transpiled to {target_language.upper()} ===")
            print(transpiled_code)

    except Exception as e: print(f"❌ Transpilation failed: {e}")


def print_help(): """Print help information for the Sona CLI."""
    print("Sona Programming Language CLI")
    print("Usage: sona [command] [options]")
    print("\nCommands:")
    print("  <file.sona>              Execute a Sona file")
    print("  run <file.py|file.sona>  Execute Python or Sona files")
    print("  repl                     Start interactive REPL")
    print("  transpile <file.sona>    Transpile Sona code to other languages")
    print("  init <project>           Initialize a new Sona project")
    print("  format <file.sona>       Format Sona code files")
    print("  check <file.sona>        Check Sona code for syntax errors")
    print("  info                     Show system and environment info")
    print("  clean                    Clean generated files and cache")
    print("  docs                     Open documentation or show reference")
    print("\nRun Options:")
    print(" --cwd <directory>        Set working directory")
    print(" --env KEY = VALUE          Set environment variable")
    print("  [args...]                Pass arguments to the script")
    print("\nTranspile Options:")
    print(
        " --target <language>      Target language (python, javascript, "
        "typescript, java, csharp, go, rust)"
    )
    print(" --output <file>          Output file (default: print to stdout)")
    print("\nGlobal Options:")
    print(" --help, -h               Show this help message")
    print(" --version                Show version information")
    print(" --debug                  Enable debug mode")
    print("\nExamples:")
    print("  sona program.sona                    # Execute program.sona")
    print("  sona run script.py                   # Execute script.py")
    print("  sona run program.sona                # Execute program.sona")
    print("  sona run script.py arg1 arg2         # Execute with arguments")
    print("  sona run script.py --cwd /path       # Execute in directory")
    print("  sona run script.py --env DEBUG = 1     # Execute with env var")
    print("  sona repl                            # Start REPL")
    print("  sona transpile code.sona             # Transpile to Python")
    print("  sona transpile code.sona --target js --output code.js")
    print("  sona init my_project                 # Initialize new project")
    print("  sona format code.sona                # Format Sona code")
    print("  sona check code.sona                 # Check syntax errors")
    print("  sona info                            # Show environment info")
    print("  sona clean                           # Clean generated files")
    print("  sona docs                            # Open documentation")


def init_command(args): """Initialize a new Sona project"""
    project_name = args[0] if args else "my-sona-project"

    try: # Create project directory
        os.makedirs(project_name, exist_ok = True)

        # Create main.sona file
        main_sona = f"""\
// {project_name} - Sona Project
// Generated by: sona init // Main program entry point
function main() {{
    think("Starting {project_name}");
    print("Hello from {project_name}!"); // Your code here
    return 0;
}} // Run the main function
main();
"""

        with open(f"{project_name}/main.sona", "w") as f: f.write(main_sona)

        # Create README.md
        readme = f"""\
# {project_name}

A Sona programming language project.

## Getting Started

```bash
# Run the project
sona {project_name}/main.sona

# Start REPL
sona repl

# Transpile to other languages
sona transpile {project_name}/main.sona --target javascript
```

## Project Structure - `main.sona` - Main program entry point
- `README.md` - This file

## Documentation - [Sona Language Documentation](https://github.com/Bryantad/Sona)
- [Sona CLI Reference](https://github.com/Bryantad/Sona/blob/main/CLI.md)
"""

        with open(f"{project_name}/README.md", "w") as f: f.write(readme)

        print(f"✅ Created new Sona project: {project_name}")
        print("📁 Project structure:")
        print("  {}/".format(project_name))
        print("  ├── main.sona")
        print("  └── README.md")
        print("\n🚀 Get started:")
        print(f"  cd {project_name}")
        print("  sona main.sona")

    except Exception as e: print(f"❌ Failed to create project: {e}")


def format_command(args): """Format Sona code files"""
    if not args: print("Usage: sona format <file.sona> [files...]")
        return

    import re

    def format_sona_code(code): """Basic Sona code formatter"""
        lines = code.split('\n')
        formatted_lines = []
        indent_level = 0

        for line in lines: line = line.strip()
            if not line: formatted_lines.append('')
                continue

            # Decrease indent for closing braces
            if line.startswith('}'): indent_level = max(0, indent_level - 1)

            # Add indentation
            formatted_line = '    ' * indent_level + line
            formatted_lines.append(formatted_line)

            # Increase indent for opening braces
            if line.endswith('{'): indent_level + = 1

        return '\n'.join(formatted_lines)

    for file_path in args: try: if not os.path.exists(file_path): print(f"❌ File not found: {file_path}")
                continue

            with open(file_path, 'r') as f: original_code = f.read()

            formatted_code = format_sona_code(original_code)

            # Write formatted code back
            with open(file_path, 'w') as f: f.write(formatted_code)

            print(f"✅ Formatted: {file_path}")

        except Exception as e: print(f"❌ Failed to format {file_path}: {e}")


def check_command(args): """Check Sona code for syntax errors"""
    if not args: print("Usage: sona check <file.sona> [files...]")
        return

    for file_path in args: try: if not os.path.exists(file_path): print(f"❌ File not found: {file_path}")
                continue

            with open(file_path, 'r') as f: code = f.read()

            # Basic syntax checking
            errors = []
            lines = code.split('\n')

            for i, line in enumerate(lines, 1): line = line.strip()
                if not line or line.startswith('//'): continue

                # Check for common syntax errors
                if line.count('{') ! = (
                    line.count('}'): if '{' in line and '}' not in line: # Opening brace - this is fine
                )
                        pass
                    elif '}' in line and '{' not in line: # Closing brace - this is fine
                        pass
                    else: errors.append(f"Line {i}: Unmatched braces")

                if line.count('(') ! = (
                    line.count(')'): errors.append(f"Line {i}: Unmatched parentheses")
                )

                if line.count('"') % 2 ! = (
                    0: errors.append(f"Line {i}: Unmatched quotes")
                )

            if errors: print(f"❌ {file_path}: {len(errors)} error(s)")
                for error in errors: print(f"  {error}")
            else: print(f"✅ {file_path}: No syntax errors found")

        except Exception as e: print(f"❌ Failed to check {file_path}: {e}")


def info_command(args): """Show system and Sona environment information"""
    import platform

    print("🔍 Sona Environment Information")
    print(" = " * 50)

    # System info
    print(f"🖥️  System: {platform.system()} {platform.release()}")
    print(f"🏗️  Architecture: {platform.machine()}")
    print(f"🐍 Python: {platform.python_version()}")
    print(f"📍 Python Path: {sys.executable}")

    # Sona info
    print(f"🎯 Sona Version: 0.8.0")
    print(f"📂 Working Directory: {os.getcwd()}")

    # Environment variables
    sona_vars = {k: v for k, v in os.environ.items() if k.startswith('SONA_')}
    if sona_vars: print(f"🌍 Sona Environment Variables:")
        for k, v in sona_vars.items(): print(f"  {k} = {v}")

    # Check for dependencies
    print(f"📦 Dependencies:")
    deps = [
        ('lark', 'lark'),
        ('tkinter', 'tkinter'),
        ('PySide6', 'PySide6'),
        ('colorama', 'colorama'),
    ]
    for dep_name, import_name in deps: try: if import_name = (
        ( = 'tkinter': import tkinter  # noqa: F401
    )
    )

                print(f"  ✅ {dep_name}: Available")
            else: __import__(import_name)
                print(f"  ✅ {dep_name}: Available")
        except ImportError: print(f"  ❌ {dep_name}: Not available")


def clean_command(args): """Clean generated files and cache"""
    patterns = [
        '*.pyc',
        '__pycache__',
        '*.pyo',
        '.DS_Store',
        'Thumbs.db',
        '*.tmp',
        '*.log',
    ]

    import glob
    import shutil

    cleaned_files = []

    for pattern in patterns: if pattern = (
        ( = '__pycache__': # Remove __pycache__ directories
    )
    )
            for root, dirs, files in os.walk('.'): for dirname in dirs: if dirname = (
                ( = '__pycache__': cache_dir = os.path.join(root, dirname)
            )
            )
                        shutil.rmtree(cache_dir)
                        cleaned_files.append(cache_dir)
        else: # Remove files matching pattern
            for file_path in glob.glob(pattern): os.remove(file_path)
                cleaned_files.append(file_path)

    if cleaned_files: print(f"🧹 Cleaned {len(cleaned_files)} files:")
        for file_path in cleaned_files: print(f"  🗑️  {file_path}")
    else: print("✨ No files to clean")


def docs_command(args): """Open documentation or show quick reference"""
    if args and args[0] == '--offline': # Show offline documentation
        print("📖 Sona Language Quick Reference")
        print(" = " * 50)
        print(
            """
🎯 Basic Syntax: function name(params) { ... } // Function definition
  think("message"); // Cognitive thinking
  print("output"); // Output to console

🔧 Variables: name = "value"; // String assignment
  number = 42; // Number assignment

🏗️  Control Flow: if (condition) { ... } // Conditional
  for (i = 0; i < 10; i++) { ... } // Loop

🎨 Classes: class Name { // Class definition
    constructor(params) { ... } // Constructor
    method() { ... } // Method
  }

🚀 Commands: sona file.sona // Execute Sona file
  sona run script.py // Execute Python script
  sona transpile file.sona // Transpile to other languages
  sona repl // Start interactive REPL
  sona init [project] // Create new project
  sona format file.sona // Format code
  sona check file.sona // Check syntax

For more help: sona --help
"""
        )
    else: # Try to open online documentation
        import webbrowser

        url = "https://github.com/Bryantad/Sona/blob/main/README.md"
        try: webbrowser.open(url)
            print(f"🌐 Opening documentation: {url}")
        except Exception: print(
                "❌ Could not open browser. Use 'sona docs --offline' for offline help"
            )


def main(): # Set debug mode from environment or command line flag
    if "--debug" in sys.argv: os.environ["SONA_DEBUG"] = "1"
        sys.argv.remove("--debug")

    if "--version" in sys.argv: print("Sona Language Version: 0.8.0")
        return

    if "--help" in sys.argv or "-h" in sys.argv: print_help()
        return

    # Handle commands
    if len(sys.argv) < 2: print_help()
        return

    # Handle transpile command
    if sys.argv[1] == "transpile": transpile_command(sys.argv[2:])
        return

    # Handle init command
    if len(sys.argv) >= 2 and sys.argv[1] == "init": init_command(sys.argv[2:])
        return

    # Handle format command
    if len(sys.argv) > = (
        2 and sys.argv[1] == "format": format_command(sys.argv[2:])
    )
        return

    # Handle check command
    if len(sys.argv) > = (
        2 and sys.argv[1] == "check": check_command(sys.argv[2:])
    )
        return

    # Handle info command
    if len(sys.argv) >= 2 and sys.argv[1] == "info": info_command(sys.argv[2:])
        return

    # Handle clean command
    if len(sys.argv) > = (
        2 and sys.argv[1] == "clean": clean_command(sys.argv[2:])
    )
        return

    # Handle docs command
    if len(sys.argv) >= 2 and sys.argv[1] == "docs": docs_command(sys.argv[2:])
        return

    # Handle run command
    if len(sys.argv) > = (
        2 and sys.argv[1] == "run": # Shift arguments for the runner
    )
        runner_args = sys.argv[2:]

        # Check for --cwd option
        cwd = None
        env_vars = {}
        if "--cwd" in runner_args: cwd_index = runner_args.index("--cwd")
            if cwd_index + 1 < len(runner_args): cwd = (
                runner_args[cwd_index + 1]
            )
                runner_args.pop(cwd_index)  # Remove --cwd
                runner_args.pop(cwd_index)  # Remove path

        # Check for --env option
        if "--env" in runner_args: env_index = runner_args.index("--env")
            while (
                env_index + 1 < len(runner_args)
                and " = " in runner_args[env_index + 1]
            ): key_value = runner_args[env_index + 1].split(" = ", 1)
                if len(key_value) == 2: env_vars[key_value[0]] = key_value[1]
                env_index + = 1
            runner_args.pop(env_index)  # Remove --env

        # Execute the file (support both .py and .sona files)
        if runner_args: target_file = runner_args[0]
            if os.path.exists(target_file): # Check if it's a Sona file
                if target_file.endswith('.sona'): # Import the transpiler
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    sys.path.insert(0, current_dir)
                    from sona_transpiler import SonaTranspiler

                    # Create a temporary Python file
                    temp_py = target_file.replace('.sona', '_temp.py')

                    try: # Transpile the Sona file
                        transpiler = SonaTranspiler()
                        with open(target_file, 'r') as f: sona_code = f.read()

                        # Create transpile options
                        from sona_transpiler import (
                            TargetLanguage,
                            TranspileOptions,
                        )

                        options = TranspileOptions(
                            target_language = TargetLanguage.PYTHON,
                            include_comments = True,
                            include_cognitive_blocks = True,
                            optimize_code = True,
                            strict_types = False,
                        )

                        python_code = transpiler.transpile(sona_code, options)

                        with open(temp_py, 'w') as f: f.write(python_code)

                        # Build the command
                        command = [sys.executable, temp_py] + runner_args[1:]

                        # Set environment variables
                        os.environ.update(env_vars)

                        # Change working directory if specified
                        if cwd and os.path.isdir(cwd): os.chdir(cwd)

                        # Execute the command
                        try: subprocess.run(command, check = True)
                        except subprocess.CalledProcessError as e: print(f"❌ Error executing {target_file}: {e}")
                        finally: # Clean up temporary file
                            if os.path.exists(temp_py): os.remove(temp_py)

                    except Exception as e: print(f"❌ Error transpiling {target_file}: {e}")
                        if os.path.exists(temp_py): os.remove(temp_py)

                else: # It's a Python file
                    # Build the command
                    command = [sys.executable, target_file] + runner_args[1:]

                    # Set environment variables
                    os.environ.update(env_vars)

                    # Change working directory if specified
                    if cwd and os.path.isdir(cwd): os.chdir(cwd)

                    # Execute the command
                    try: subprocess.run(command, check = True)
                    except subprocess.CalledProcessError as e: print(f"❌ Error executing {target_file}: {e}")
            else: print(f"❌ File not found: {target_file}")
        else: print("Usage: sona run <file.py|file.sona> [options]")
            print("Try 'sona run --help' for more information.")
        return

    # If we reach here, the command is not recognized
    print(f"❌ Unknown command: {sys.argv[1]}")
    print("Use 'sona --help' to see available commands.")


if __name__ == "__main__": main()
