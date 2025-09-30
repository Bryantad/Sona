#!/usr/bin/env python3
"""
Ultimate Code Quality Fixer v2.0
Final comprehensive solution to achieve zero VS Code lint errors
"""

import subprocess
import sys
from pathlib import Path


class UltimateCodeFixer:
    """The ultimate solution for achieving zero VS Code errors"""

    def __init__(self):
        self.root = Path.cwd()
        self.critical_files = [
            'sona_transpiler.py',
            'sona/interpreter.py',
            'sona/repl.py',
            'sona/cognitive_core.py',
            'sona/cognitive_integration.py',
            'sona/cognitive_parser.py',
            'sona/cognitive_syntax.py',
        ]

    def run_autopep8_aggressive(self):
        """Apply aggressive autopep8 formatting"""
        print("🔧 Applying aggressive autopep8 formatting...")

        try:
            # Install autopep8 if not available
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', 'autopep8'],
                capture_output=True,
                check=False,
            )

            # Apply to all Python files
            cmd = [
                sys.executable,
                '-m',
                'autopep8',
                '--aggressive',
                '--aggressive',
                '--aggressive',
                '--in-place',
                '--recursive',
                '--max-line-length',
                '79',
                '.',
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Autopep8 completed successfully")
                return True
            else:
                print(f"⚠️  Autopep8 warnings: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Autopep8 failed: {e}")
            return False

    def run_isort_imports(self):
        """Fix import sorting and organization"""
        print("📚 Organizing imports with isort...")

        try:
            # Install isort if not available
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', 'isort'],
                capture_output=True,
                check=False,
            )

            cmd = [
                sys.executable,
                '-m',
                'isort',
                '--profile',
                'black',
                '--line-length',
                '79',
                '--recursive',
                '.',
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Import organization completed")
                return True
            else:
                print(f"⚠️  Import organization warnings: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Import organization failed: {e}")
            return False

    def run_black_final(self):
        """Final Black formatting pass"""
        print("🎨 Applying final Black formatting...")

        try:
            cmd = [
                sys.executable,
                '-m',
                'black',
                '--line-length',
                '79',
                '--skip-string-normalization',
                '.',
                '--extend-exclude',
                'sona_transpiler_fixed.py|Lib/',
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            success_count = result.stdout.count('reformatted')
            error_count = result.stderr.count('failed to reformat')

            print(f"✅ Black formatting: {success_count} files reformatted")
            if error_count > 0:
                print(f"⚠️  {error_count} files could not be formatted")

            return error_count == 0

        except Exception as e:
            print(f"❌ Black formatting failed: {e}")
            return False

    def clean_temp_files(self):
        """Clean up temporary and cache files"""
        print("🧹 Cleaning temporary files...")

        patterns_to_clean = [
            '**/__pycache__',
            '**/*.pyc',
            '**/*.pyo',
            '**/.pytest_cache',
            '**/*.orig',
        ]

        cleaned_count = 0
        for pattern in patterns_to_clean:
            for path in self.root.glob(pattern):
                try:
                    if path.is_dir():
                        import shutil

                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    cleaned_count += 1
                except Exception:
                    pass

        print(f"✅ Cleaned {cleaned_count} temporary files")
        return True

    def validate_syntax(self):
        """Validate Python syntax in critical files"""
        print("✅ Validating Python syntax...")

        syntax_errors = 0
        for file_path in self.critical_files:
            full_path = self.root / file_path
            if not full_path.exists():
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                compile(content, str(full_path), 'exec')
                print(f"   ✓ {file_path}")

            except SyntaxError as e:
                print(f"   ❌ {file_path}: Line {e.lineno} - {e.msg}")
                syntax_errors += 1
            except Exception as e:
                print(f"   ⚠️  {file_path}: {e}")

        if syntax_errors == 0:
            print("✅ All critical files have valid Python syntax")
            return True
        else:
            print(f"❌ {syntax_errors} files have syntax errors")
            return False

    def run_comprehensive_fix(self):
        """Run the complete comprehensive fix process"""
        print("🚀 ULTIMATE CODE QUALITY FIXER v2.0")
        print("=" * 60)

        steps = [
            ("Clean temporary files", self.clean_temp_files),
            ("Apply aggressive autopep8", self.run_autopep8_aggressive),
            ("Organize imports", self.run_isort_imports),
            ("Final Black formatting", self.run_black_final),
            ("Validate syntax", self.validate_syntax),
        ]

        success_count = 0
        for step_name, step_func in steps:
            print(f"\n📋 Step: {step_name}")
            if step_func():
                success_count += 1
            else:
                print("⚠️  Step failed but continuing...")

        print("\n" + "=" * 60)
        print("🎯 COMPREHENSIVE FIX COMPLETE")
        print(f"   • Steps completed: {success_count}/{len(steps)}")
        print(
            f"   • Status: {'SUCCESS' if success_count >= 4 else 'PARTIAL SUCCESS'}"
        )

        if success_count >= 4:
            print("🎉 Code quality should now be at founder level!")
            print("💡 Run VS Code error check to verify remaining issues")
        else:
            print("⚠️  Some steps failed - manual review may be needed")

        return success_count >= 4


def main():
    """Main execution"""
    fixer = UltimateCodeFixer()
    success = fixer.run_comprehensive_fix()
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
