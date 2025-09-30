"""
Emergency File Fixer - Repairs severely corrupted Python files
Handles structural syntax errors, indentation problems, and format issues
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import Dict


class EmergencyFileFixer:
    """Emergency fixer for severely corrupted Python files"""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.files_fixed = 0

    def fix_structural_issues(self, content: str) -> str:
        """Fix severe structural syntax issues"""
        lines = content.split("\n")
        fixed_lines = []
        in_class = False
        in_function = False
        current_indent = 0

        for line in lines:
            original_line = line
            line = line.rstrip()

            # Skip empty lines
            if not line:
                fixed_lines.append("")
                continue

            # Remove broken syntax patterns
            if "( =======" in line or ")" == line.strip():
                continue

            # Fix class definitions
            if line.strip().startswith("class ") and ":" not in line:
                if (
                    "Enum" in line
                    or "Exception" in line
                    or any(x in line for x in ["(", ")"])
                ):
                    # Extract class name and inheritance
                    class_match = re.search(
                        r'class\s+(\w+).*?([A-Za-z]+).*?["\']([^"\']+)["\']',
                        line,
                    )
                    if class_match:
                        class_name, parent, docstring = class_match.groups()
                        fixed_lines.append(f"class {class_name}({parent}):")
                        fixed_lines.append(f'    """{docstring}"""')
                        in_class = True
                        current_indent = 4
                        continue

            # Fix function/method definitions
            if ("def " in line or "@" in line) and line.strip().endswith(":"):
                if line.strip().startswith("@"):
                    fixed_lines.append(" " * current_indent + line.strip())
                    continue
                elif "def " in line:
                    # Extract function signature properly
                    func_match = re.search(
                        r"def\s+(\w+)\s*\([^)]*\).*?:", line
                    )
                    if func_match:
                        if in_class:
                            fixed_lines.append(
                                " " * current_indent + line.strip()
                            )
                            in_function = True
                        else:
                            fixed_lines.append(line.strip())
                            in_function = True
                        continue

            # Handle docstrings and regular content
            stripped = line.strip()
            if stripped:
                # Calculate proper indentation
                if in_class and not in_function:
                    indent = current_indent
                elif in_function:
                    indent = current_indent + 4
                else:
                    indent = 0

                # Add the line with proper indentation
                if stripped.startswith(('"""', "'''")):
                    fixed_lines.append(" " * indent + stripped)
                elif stripped.startswith(("def ", "class ", "@")):
                    fixed_lines.append(" " * (indent - 4) + stripped)
                elif stripped.startswith(("return ", "yield ", "raise ")):
                    fixed_lines.append(" " * (indent + 4) + stripped)
                else:
                    fixed_lines.append(" " * indent + stripped)

        return "\n".join(fixed_lines)

    def repair_file(self, file_path: Path) -> bool:
        """Repair a single severely corrupted file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Apply structural fixes
            fixed_content = self.fix_structural_issues(content)

            # Write back
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)

            # Try to apply Black formatting
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "black",
                        "--line-length",
                        "79",
                        str(file_path),
                    ],
                    capture_output=True,
                    text=True,
                    cwd=self.root_path,
                )

                if result.returncode == 0:
                    print(f"✅ Emergency repair successful: {file_path.name}")
                    self.files_fixed += 1
                    return True
                else:
                    print(
                        f"⚠️  Partial repair (syntax fixed, formatting failed): {file_path.name}"
                    )
                    return False

            except Exception:
                print(f"⚠️  Basic repair only: {file_path.name}")
                return False

        except Exception as e:
            print(f"❌ Emergency repair failed for {file_path.name}: {e}")
            return False

    def fix_priority_files(self) -> Dict[str, bool]:
        """Fix the most critical files first"""
        priority_files = [
            "sona/cognitive_core.py",
            "sona/cognitive_integration.py",
            "sona/cognitive_parser.py",
            "sona/cognitive_syntax.py",
            "sona/repl.py",
            "sona/interpreter.py",
            "sona_transpiler.py",
        ]

        results = {}
        print("🚨 Emergency File Repair - Fixing Critical Files")
        print("=" * 50)

        for file_rel_path in priority_files:
            file_path = self.root_path / file_rel_path
            if file_path.exists():
                success = self.repair_file(file_path)
                results[file_rel_path] = success
            else:
                print(f"⚠️  File not found: {file_rel_path}")
                results[file_rel_path] = False

        print("\n📊 Emergency Repair Summary:")
        print(f"   • Files repaired: {self.files_fixed}")
        print(
            f"   • Success rate: {len([r for r in results.values() if r])}/{len(results)}"
        )

        return results


if __name__ == "__main__":
    fixer = EmergencyFileFixer(".")
    fixer.fix_priority_files()
