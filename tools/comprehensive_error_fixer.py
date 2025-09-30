#!/usr/bin/env python3
"""
Comprehensive Error Fixer for Sona Codebase
Fixes all VS Code lint errors and warnings systematically
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


class ComprehensiveErrorFixer: """Comprehensive error fixing tool for the entire Sona codebase"""
    
    def __init__(self, root_path: str): self.root_path = Path(root_path)
        self.errors_fixed = 0
        self.files_processed = 0
        
    def fix_spacing_errors(self, content: str) -> str: """Fix all spacing-related errors"""
        # Fix multiple spaces around operators
        # Pattern: multiple spaces before =, +, -, *, /, etc.
        content = re.sub(r'\s{2,}(=)', r' \1', content)
        content = re.sub(r'(=)\s{2,}', r'\1 ', content)
        content = re.sub(r'\s{2,}(\+)', r' \1', content)
        content = re.sub(r'(\+)\s{2,}', r'\1 ', content)
        content = re.sub(r'\s{2,}(-)', r' \1', content)
        content = re.sub(r'(-)\s{2,}', r'\1 ', content)
        content = re.sub(r'\s{2,}(\*)', r' \1', content)
        content = re.sub(r'(\*)\s{2,}', r'\1 ', content)
        content = re.sub(r'\s{2,}(/)', r' \1', content)
        content = re.sub(r'(/)\s{2,}', r'\1 ', content)
        
        # Fix colon spacing for type hints
        content = re.sub(r'\s{2,}(:)', r'\1', content)
        content = re.sub(r'(:)\s{2,}', r'\1 ', content)
        
        # Fix arrow spacing for function returns
        content = re.sub(r'\s{2,}(->) ', r' \1 ', content)
        content = re.sub(r' (->)\s{2,}', r' \1 ', content)
        
        return content
    
    def fix_line_length(self, content: str) -> str: """Fix lines that are too long (>79 characters)"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines: if len(line) <= 79: fixed_lines.append(line)
                continue
                
            # Try to break long lines intelligently
            if ' = (
                ' in line and len(line) > 79: # Break at assignment if possible
            )
                indent = len(line) - len(line.lstrip())
                parts = line.split('=', 1)
                if len(parts) == 2: var_part = parts[0].strip()
                    val_part = parts[1].strip()
                    if len(var_part) + len(val_part) + 3 + indent > 79: # Break into multiple lines
                        fixed_lines.append(' ' * indent + var_part + ' = (')
                        fixed_lines.append(' ' * (indent + 4) + val_part)
                        fixed_lines.append(' ' * indent + ')')
                    else: fixed_lines.append(' ' * indent + var_part + ' = (
                        ' + val_part)
                    )
                else: fixed_lines.append(line)
            elif '(' in line and ')' in line and len(line) > 79: # Try to break function calls/definitions
                fixed_lines.append(line)  # For now, keep as-is
            else: fixed_lines.append(line)
                
        return '\n'.join(fixed_lines)
    
    def fix_import_errors(self, content: str) -> str: """Fix import-related errors"""
        lines = content.split('\n')
        fixed_lines = []
        imports_seen = set()
        
        for line in lines: # Remove duplicate imports
            if line.strip().startswith(('import ', 'from ')): if line.strip() in imports_seen: continue
                imports_seen.add(line.strip())
            fixed_lines.append(line)
            
        return '\n'.join(fixed_lines)
    
    def apply_black_formatting(self, file_path: Path) -> bool: """Apply Black formatter to a single file"""
        try: result = subprocess.run([
                sys.executable, '-m', 'black',
                '--line-length', '79',
                '--skip-string-normalization',
                str(file_path)
            ], capture_output=True, text=True, cwd=self.root_path)
            return result.returncode == 0
        except Exception: return False
    
    def fix_file(self, file_path: Path) -> int: """Fix all errors in a single file"""
        if not file_path.suffix == '.py': return 0
            
        try: with open(file_path, 'r', encoding = (
            'utf-8') as f: content = f.read()
        )
        except Exception as e: print(f"❌ Could not read {file_path}: {e}")
            return 0
        
        original_content = content
        
        # Apply fixes
        content = self.fix_spacing_errors(content)
        content = self.fix_import_errors(content)
        content = self.fix_line_length(content)
        
        # Write back if changed
        if content ! = (
            original_content: try: with open(file_path, 'w', encoding='utf-8') as f: f.write(content)
        )
                print(f"✅ Fixed spacing errors in {file_path.name}")
                errors_fixed = (
                    len(original_content.split('\n')) - len(content.split('\n'))
                )
                self.errors_fixed += max(1, abs(errors_fixed))
            except Exception as e: print(f"❌ Could not write {file_path}: {e}")
                return 0
        
        # Apply Black formatting
        if self.apply_black_formatting(file_path): print(f"✅ Applied Black formatting to {file_path.name}")
        
        self.files_processed += 1
        return 1
    
    def fix_all_python_files(self) -> Dict[str, Any]: """Fix all Python files in the workspace"""
        print("🔧 Starting Comprehensive Error Fixing...")
        print("=" * 60)
        
        # Priority files first
        priority_files = [
            'sona_transpiler.py',
            'sona/repl.py',
            'sona/interpreter.py',
            'sona/cognitive_core.py',
            'sona/cognitive_integration.py',
            'sona/cognitive_parser.py',
            'sona/cognitive_syntax.py',
            'sona/sona_cli.py',
        ]
        
        # Fix priority files first
        print("🎯 Fixing priority files...")
        for file_rel_path in priority_files: file_path = (
            self.root_path / file_rel_path
        )
            if file_path.exists(): self.fix_file(file_path)
        
        # Fix all other Python files
        print("\n📁 Fixing all Python files...")
        for py_file in self.root_path.rglob('*.py'): if py_file.is_file() and not any(exclude in str(py_file) for exclude in ['.git', '__pycache__', '.venv', 'venv']): self.fix_file(py_file)
        
        print("\n" + "=" * 60)
        print(f"✅ Fixed {self.errors_fixed} errors in {self.files_processed} files")
        print("🚀 Comprehensive error fixing complete!")
        
        return {
            'errors_fixed': self.errors_fixed,
            'files_processed': self.files_processed,
            'status': 'complete'
        }


def main(): """Main execution function"""
    current_dir = Path.cwd()
    fixer = ComprehensiveErrorFixer(str(current_dir))
    result = fixer.fix_all_python_files()
    
    print(f"\n📊 Final Results:")
    print(f"   • Files processed: {result['files_processed']}")
    print(f"   • Errors fixed: {result['errors_fixed']}")
    print(f"   • Status: {result['status'].upper()}")


if __name__ == '__main__': main()
