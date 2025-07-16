"""
Sona Advanced Transpiler System
==============================
Multi-target transpiler supporting Python, JavaScript, TypeScript, and more

This module provides comprehensive transpilation capabilities for Sona code,
enabling cross-platform development while maintaining cognitive accessibility.
"""

import re
import ast
from typing import Dict, Any, List, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass
from pathlib import Path


class TargetLanguage(Enum):
    """Supported target languages for transpilation"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    C_SHARP = "csharp"
    GO = "go"
    RUST = "rust"


@dataclass
class TranspileOptions:
    """Options for transpilation process"""
    target_language: TargetLanguage
    include_comments: bool = True
    include_cognitive_blocks: bool = True
    optimize_code: bool = True
    strict_types: bool = False
    output_file: Optional[Path] = None


class SonaTranspiler:
    """Advanced transpiler for Sona programming language"""
    
    def __init__(self):
        self.cognitive_blocks = {}
        self.imports = set()
        self.functions = {}
        self.classes = {}
        self.variables = {}
        
    def transpile(self, sona_code: str, options: TranspileOptions) -> str:
        """
        Transpile Sona code to target language
        
        Args:
            sona_code: Source Sona code
            options: Transpilation options
            
        Returns:
            Transpiled code in target language
        """
        # Parse cognitive blocks first
        if options.include_cognitive_blocks:
            sona_code = self._extract_cognitive_blocks(sona_code)
        
        # Dispatch to appropriate transpiler
        if options.target_language == TargetLanguage.PYTHON:
            return self._transpile_to_python(sona_code, options)
        elif options.target_language == TargetLanguage.JAVASCRIPT:
            return self._transpile_to_javascript(sona_code, options)
        elif options.target_language == TargetLanguage.TYPESCRIPT:
            return self._transpile_to_typescript(sona_code, options)
        elif options.target_language == TargetLanguage.JAVA:
            return self._transpile_to_java(sona_code, options)
        elif options.target_language == TargetLanguage.C_SHARP:
            return self._transpile_to_csharp(sona_code, options)
        elif options.target_language == TargetLanguage.GO:
            return self._transpile_to_go(sona_code, options)
        elif options.target_language == TargetLanguage.RUST:
            return self._transpile_to_rust(sona_code, options)
        else:
            raise ValueError(f"Unsupported target language: {options.target_language}")
    
    def _extract_cognitive_blocks(self, code: str) -> str:
        """Extract and store cognitive thinking blocks"""
        thinking_pattern = r'thinking\s+"([^"]+)"\s*\{([^}]+)\}'
        matches = re.finditer(thinking_pattern, code, re.DOTALL)
        
        for match in matches:
            block_name = match.group(1)
            block_content = match.group(2).strip()
            self.cognitive_blocks[block_name] = self._parse_cognitive_block(block_content)
            
            # Replace with comment
            code = code.replace(match.group(0), f'// Cognitive: {block_name}')
        
        return code
    
    def _parse_cognitive_block(self, content: str) -> Dict[str, Any]:
        """Parse cognitive block content into structured data"""
        block_data = {}
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line and not line.startswith('//'):
                key, value = line.split(':', 1)
                block_data[key.strip()] = value.strip().strip('"\'')
        
        return block_data
    
    def _transpile_to_python(self, code: str, options: TranspileOptions) -> str:
        """Transpile to Python"""
        # Enhanced function definitions
        code = re.sub(r'function\s+(\w+)\s*\(([^)]*)\)\s*:\s*(\w+)\s*\{', 
                     r'def \1(\2) -> \3:', code)
        code = re.sub(r'function\s+(\w+)\s*\(([^)]*)\)\s*\{', 
                     r'def \1(\2):', code)
        
        # Arrow functions
        code = re.sub(r'\(([^)]*)\)\s*=>\s*([^;]+)', r'lambda \1: \2', code)
        
        # Variable declarations with type hints
        code = re.sub(r'let\s+(\w+)\s*:\s*(\w+)\s*=', r'\1: \2 =', code)
        code = re.sub(r'const\s+(\w+)\s*:\s*(\w+)\s*=', r'\1: \2 =', code)
        code = re.sub(r'(let|const|var)\s+(\w+)', r'\2', code)
        
        # Control structures
        code = re.sub(r'if\s*\(([^)]+)\)\s*\{', r'if \1:', code)
        code = re.sub(r'while\s*\(([^)]+)\)\s*\{', r'while \1:', code)
        code = re.sub(r'for\s*\((\w+)\s+in\s+([^)]+)\)\s*\{', r'for \1 in \2:', code)
        
        # Enhanced for loops
        for_pattern = r'for\s*\(([^;]+);\s*([^;]+);\s*([^)]+)\)\s*\{'
        def convert_for_loop(match):
            init, condition, increment = match.groups()
            var_name = init.split('=')[0].strip() if '=' in init else 'i'
            start_val = init.split('=')[1].strip() if '=' in init else '0'
            
            if '<' in condition:
                end_val = condition.split('<')[1].strip()
                return f'for {var_name} in range({start_val}, {end_val}):'
            elif '<=' in condition:
                end_val = condition.split('<=')[1].strip()
                return f'for {var_name} in range({start_val}, {end_val} + 1):'
            else:
                return f'for {var_name} in range(10):'
        
        code = re.sub(for_pattern, convert_for_loop, code)
        
        # Boolean and null values
        code = re.sub(r'\btrue\b', 'True', code)
        code = re.sub(r'\bfalse\b', 'False', code)
        code = re.sub(r'\bnull\b', 'None', code)
        
        # Operators
        code = re.sub(r'(\w+)\s*===\s*(\w+)', r'\1 is \2', code)
        code = re.sub(r'(\w+)\s*!==\s*(\w+)', r'\1 is not \2', code)
        code = re.sub(r'(\w+)\s*&&\s*(\w+)', r'\1 and \2', code)
        code = re.sub(r'(\w+)\s*\|\|\s*(\w+)', r'\1 or \2', code)
        
        # Error handling
        code = re.sub(r'try\s*\{', r'try:', code)
        code = re.sub(r'catch\s*\(([^)]+)\)\s*\{', r'except \1:', code)
        code = re.sub(r'finally\s*\{', r'finally:', code)
        
        # Classes
        code = re.sub(r'class\s+(\w+)\s*\{', r'class \1:', code)
        code = re.sub(r'constructor\s*\(([^)]*)\)\s*\{', r'def __init__(self, \1):', code)
        
        # Remove semicolons and process braces
        code = re.sub(r';$', '', code, flags=re.MULTILINE)
        code = self._process_braces_python(code)
        
        # Add cognitive context if enabled
        if options.include_cognitive_blocks:
            code = self._add_cognitive_context_python(code)
        
        return code
    
    def _transpile_to_javascript(self, code: str, options: TranspileOptions) -> str:
        """Transpile to JavaScript"""
        # Sona already has JavaScript-like syntax, so minimal changes needed
        
        # Convert thinking blocks to comments
        code = re.sub(r'thinking\s+"([^"]+)"\s*\{([^}]+)\}', 
                     r'/* Cognitive: \1\n\2 */', code)
        
        # Enhanced function definitions
        code = re.sub(r'function\s+(\w+)\s*\(([^)]*)\)\s*:\s*(\w+)\s*\{', 
                     r'function \1(\2) {', code)
        
        # Variable declarations
        code = re.sub(r'let\s+(\w+)\s*:\s*(\w+)\s*=', r'let \1 =', code)
        code = re.sub(r'const\s+(\w+)\s*:\s*(\w+)\s*=', r'const \1 =', code)
        
        # Add cognitive context
        if options.include_cognitive_blocks:
            code = self._add_cognitive_context_javascript(code)
        
        return code
    
    def _transpile_to_typescript(self, code: str, options: TranspileOptions) -> str:
        """Transpile to TypeScript"""
        # Enhanced function definitions with type annotations
        code = re.sub(r'function\s+(\w+)\s*\(([^)]*)\)\s*:\s*(\w+)\s*\{', 
                     r'function \1(\2): \3 {', code)
        
        # Variable declarations with types
        code = re.sub(r'let\s+(\w+)\s*:\s*(\w+)\s*=', r'let \1: \2 =', code)
        code = re.sub(r'const\s+(\w+)\s*:\s*(\w+)\s*=', r'const \1: \2 =', code)
        
        # Interface definitions
        code = re.sub(r'interface\s+(\w+)\s*\{', r'interface \1 {', code)
        
        # Type aliases
        code = re.sub(r'type\s+(\w+)\s*=', r'type \1 =', code)
        
        # Add cognitive context
        if options.include_cognitive_blocks:
            code = self._add_cognitive_context_typescript(code)
        
        return code
    
    def _transpile_to_java(self, code: str, options: TranspileOptions) -> str:
        """Transpile to Java"""
        java_code = []
        
        # Add class wrapper
        java_code.append("public class SonaProgram {")
        
        # Function definitions
        code = re.sub(r'function\s+(\w+)\s*\(([^)]*)\)\s*:\s*(\w+)\s*\{', 
                     r'public static \3 \1(\2) {', code)
        code = re.sub(r'function\s+(\w+)\s*\(([^)]*)\)\s*\{', 
                     r'public static void \1(\2) {', code)
        
        # Variable declarations
        code = re.sub(r'let\s+(\w+)\s*:\s*(\w+)\s*=', r'\2 \1 =', code)
        code = re.sub(r'const\s+(\w+)\s*:\s*(\w+)\s*=', r'final \2 \1 =', code)
        
        # Boolean values
        code = re.sub(r'\btrue\b', 'true', code)
        code = re.sub(r'\bfalse\b', 'false', code)
        code = re.sub(r'\bnull\b', 'null', code)
        
        # Main method
        if 'main' not in code:
            java_code.append("    public static void main(String[] args) {")
            java_code.append("        // Generated main method")
            java_code.append("    }")
        
        java_code.append(code)
        java_code.append("}")
        
        return '\n'.join(java_code)
    
    def _transpile_to_csharp(self, code: str, options: TranspileOptions) -> str:
        """Transpile to C#"""
        csharp_code = []
        
        # Add namespace and class
        csharp_code.append("using System;")
        csharp_code.append("namespace SonaProgram {")
        csharp_code.append("    public class Program {")
        
        # Function definitions
        code = re.sub(r'function\s+(\w+)\s*\(([^)]*)\)\s*:\s*(\w+)\s*\{', 
                     r'public static \3 \1(\2) {', code)
        code = re.sub(r'function\s+(\w+)\s*\(([^)]*)\)\s*\{', 
                     r'public static void \1(\2) {', code)
        
        # Variable declarations
        code = re.sub(r'let\s+(\w+)\s*:\s*(\w+)\s*=', r'\2 \1 =', code)
        code = re.sub(r'const\s+(\w+)\s*:\s*(\w+)\s*=', r'const \2 \1 =', code)
        
        # Boolean values
        code = re.sub(r'\btrue\b', 'true', code)
        code = re.sub(r'\bfalse\b', 'false', code)
        code = re.sub(r'\bnull\b', 'null', code)
        
        # Main method
        if 'Main' not in code:
            csharp_code.append("        public static void Main(string[] args) {")
            csharp_code.append("            // Generated main method")
            csharp_code.append("        }")
        
        csharp_code.append(code)
        csharp_code.append("    }")
        csharp_code.append("}")
        
        return '\n'.join(csharp_code)
    
    def _transpile_to_go(self, code: str, options: TranspileOptions) -> str:
        """Transpile to Go"""
        go_code = []
        
        # Add package declaration
        go_code.append("package main")
        go_code.append("import \"fmt\"")
        
        # Function definitions
        code = re.sub(r'function\s+(\w+)\s*\(([^)]*)\)\s*:\s*(\w+)\s*\{', 
                     r'func \1(\2) \3 {', code)
        code = re.sub(r'function\s+(\w+)\s*\(([^)]*)\)\s*\{', 
                     r'func \1(\2) {', code)
        
        # Variable declarations
        code = re.sub(r'let\s+(\w+)\s*:\s*(\w+)\s*=', r'var \1 \2 =', code)
        code = re.sub(r'const\s+(\w+)\s*:\s*(\w+)\s*=', r'const \1 \2 =', code)
        
        # Boolean values
        code = re.sub(r'\btrue\b', 'true', code)
        code = re.sub(r'\bfalse\b', 'false', code)
        code = re.sub(r'\bnull\b', 'nil', code)
        
        # Main function
        if 'main' not in code:
            go_code.append("func main() {")
            go_code.append("    // Generated main function")
            go_code.append("}")
        
        go_code.append(code)
        
        return '\n'.join(go_code)
    
    def _transpile_to_rust(self, code: str, options: TranspileOptions) -> str:
        """Transpile to Rust"""
        # Function definitions
        code = re.sub(r'function\s+(\w+)\s*\(([^)]*)\)\s*:\s*(\w+)\s*\{', 
                     r'fn \1(\2) -> \3 {', code)
        code = re.sub(r'function\s+(\w+)\s*\(([^)]*)\)\s*\{', 
                     r'fn \1(\2) {', code)
        
        # Variable declarations
        code = re.sub(r'let\s+(\w+)\s*:\s*(\w+)\s*=', r'let \1: \2 =', code)
        code = re.sub(r'const\s+(\w+)\s*:\s*(\w+)\s*=', r'const \1: \2 =', code)
        
        # Boolean values
        code = re.sub(r'\btrue\b', 'true', code)
        code = re.sub(r'\bfalse\b', 'false', code)
        code = re.sub(r'\bnull\b', 'None', code)
        
        # Main function
        if 'main' not in code:
            code = f"fn main() {{\n    // Generated main function\n}}\n\n{code}"
        
        return code
    
    def _process_braces_python(self, code: str) -> str:
        """Process braces for Python indentation"""
        lines = code.split('\n')
        python_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped or stripped.startswith('#'):
                python_lines.append(line)
                continue
            
            if stripped == '}':
                indent_level = max(0, indent_level - 1)
                continue
            
            if stripped.startswith(('else:', 'elif ')):
                indent_level = max(0, indent_level - 1)
            
            indented_line = '    ' * indent_level + stripped
            
            if stripped.endswith(':') or stripped.endswith('{'):
                indent_level += 1
                indented_line = indented_line.replace(' {', '')
            
            python_lines.append(indented_line)
        
        return '\n'.join(python_lines)
    
    def _add_cognitive_context_python(self, code: str) -> str:
        """Add cognitive context as Python comments"""
        context_lines = []
        
        if self.cognitive_blocks:
            context_lines.append("# Cognitive Context:")
            for name, data in self.cognitive_blocks.items():
                context_lines.append(f"# {name}: {data}")
            context_lines.append("")
        
        return '\n'.join(context_lines) + code
    
    def _add_cognitive_context_javascript(self, code: str) -> str:
        """Add cognitive context as JavaScript comments"""
        context_lines = []
        
        if self.cognitive_blocks:
            context_lines.append("/* Cognitive Context:")
            for name, data in self.cognitive_blocks.items():
                context_lines.append(f" * {name}: {data}")
            context_lines.append(" */")
            context_lines.append("")
        
        return '\n'.join(context_lines) + code
    
    def _add_cognitive_context_typescript(self, code: str) -> str:
        """Add cognitive context as TypeScript comments"""
        return self._add_cognitive_context_javascript(code)


def transpile_sona_code(sona_code: str, target_language: str, **kwargs) -> str:
    """
    Convenience function to transpile Sona code
    
    Args:
        sona_code: Source Sona code
        target_language: Target language (python, javascript, typescript, etc.)
        **kwargs: Additional transpilation options
    
    Returns:
        Transpiled code
    """
    transpiler = SonaTranspiler()
    
    # Convert string to enum
    try:
        target_enum = TargetLanguage(target_language.lower())
    except ValueError:
        raise ValueError(f"Unsupported target language: {target_language}")
    
    options = TranspileOptions(
        target_language=target_enum,
        include_comments=kwargs.get('include_comments', True),
        include_cognitive_blocks=kwargs.get('include_cognitive_blocks', True),
        optimize_code=kwargs.get('optimize_code', True),
        strict_types=kwargs.get('strict_types', False)
    )
    
    return transpiler.transpile(sona_code, options)


# Example usage
if __name__ == "__main__":
    # Example Sona code
    sona_code = '''
    thinking "algorithm_design" {
        approach: "iterative solution"
        complexity: "O(n)"
        cognitive_load: "medium"
    }
    
    function fibonacci(n: number): number {
        if (n <= 1) {
            return n;
        }
        
        let a: number = 0;
        let b: number = 1;
        
        for (let i = 2; i <= n; i++) {
            let temp = a + b;
            a = b;
            b = temp;
        }
        
        return b;
    }
    
    let result = fibonacci(10);
    print(result);
    '''
    
    # Transpile to different languages
    print("=== Python ===")
    python_code = transpile_sona_code(sona_code, "python")
    print(python_code)
    
    print("\n=== JavaScript ===")
    js_code = transpile_sona_code(sona_code, "javascript")
    print(js_code)
    
    print("\n=== TypeScript ===")
    ts_code = transpile_sona_code(sona_code, "typescript")
    print(ts_code)
