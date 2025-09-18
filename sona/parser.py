"""
Sona Parser - Primary Parser Entry Point
========================================

Core parsing interface that selects an enhanced or basic parser implementation
and exposes a small, stable API.
"""

try:
    from .parser_v090 import SonaParserv090 as EnhancedSonaParser
    ENHANCED_PARSER_AVAILABLE = True
except ImportError:
    ENHANCED_PARSER_AVAILABLE = False
    print("⚠️  Enhanced parser not available, using fallback")

try:  # Prefer explicit imports; fallback keeps runtime resilience
    from .ast_nodes_v090 import AdvancedNode  # type: ignore
    AST_NODES_AVAILABLE = True
except ImportError:  # pragma: no cover - optional feature
    AST_NODES_AVAILABLE = False
    AdvancedNode = None  # type: ignore
    print("⚠️  Advanced AST nodes not available")

try:
    from .sona_ast_nodes import SonaASTNode  # type: ignore
    SONA_AST_AVAILABLE = True
except ImportError:  # pragma: no cover - optional feature
    SONA_AST_AVAILABLE = False
    SonaASTNode = None  # type: ignore
    print("⚠️  Sona AST nodes not available")


class SonaParser:
    """
    Primary Sona parser with fallback capabilities
    """
    
    def __init__(self, parser_type='auto'):
        """
        Initialize parser with specified type
        
        Args:
            parser_type: 'enhanced', 'basic', or 'auto' for automatic selection
        """
        self.parser_type = parser_type
        self.parser_instance = None
        self._initialize_parser()
    
    def _initialize_parser(self):
        """Initialize the most appropriate parser"""
        if (
            self.parser_type in {'enhanced', 'auto'}
            and ENHANCED_PARSER_AVAILABLE
        ):
            try:
                self.parser_instance = EnhancedSonaParser()
                self.parser_type = 'enhanced'
                print("✅ Using enhanced Sona parser")
                return
            except Exception as e:  # pragma: no cover
                print(f"⚠️  Enhanced parser failed to initialize: {e}")
        
        # Fallback to basic parser
        self.parser_instance = BasicSonaParser()
        self.parser_type = 'basic'
        print("✅ Using basic Sona parser")
    
    def parse(self, source_code, filename="<string>"):
        """
        Parse Sona source code
        
        Args:
            source_code: The Sona source code to parse
            filename: Optional filename for error reporting
            
        Returns:
            AST representation of the parsed code
        """
        if not self.parser_instance:
            raise RuntimeError("Parser not initialized")
        
        try:
            return self.parser_instance.parse(source_code, filename)
        except Exception as e:
            raise SonaParseError(f"Parse error in {filename}: {e}") from e


class BasicSonaParser:
    """
    Basic fallback parser for Sona language
    Handles simple expressions and statements without advanced features
    """
    
    def __init__(self):
        self.tokens = []
        self.current_token = 0
    
    def parse(self, source_code, filename="<string>"):
        """Parse source code using basic parser"""
        # Simple tokenization and parsing
        lines = source_code.strip().split('\n')
        statements = []
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            try:
                stmt = self._parse_line(line, line_num)
                if stmt:
                    statements.append(stmt)
            except Exception as e:
                raise SonaParseError(f"Error on line {line_num}: {e}")
        
        return BasicAST(statements)
    
    def _parse_line(self, line, line_num):
        """Parse a single line of code"""
        # Handle variable declarations
        if line.startswith('let '):
            return self._parse_let_declaration(line[4:], line_num)
        elif line.startswith('const '):
            return self._parse_const_declaration(line[6:], line_num)
        # Handle expressions
        else:
            return self._parse_expression(line, line_num)
    
    def _parse_let_declaration(self, declaration, line_num):
        """Parse let declaration"""
        if '=' in declaration:
            name, value = declaration.split('=', 1)
            return {
                'type': 'let_declaration',
                'name': name.strip(),
                'value': self._parse_expression(value.strip(), line_num),
                'line': line_num
            }
        else:
            return {
                'type': 'let_declaration',
                'name': declaration.strip(),
                'value': None,
                'line': line_num
            }
    
    def _parse_const_declaration(self, declaration, line_num):
        """Parse const declaration"""
        if '=' in declaration:
            name, value = declaration.split('=', 1)
            return {
                'type': 'const_declaration',
                'name': name.strip(),
                'value': self._parse_expression(value.strip(), line_num),
                'line': line_num
            }
        else:
            raise SonaParseError("const declaration must have value")
    
    def _parse_expression(self, expr, line_num):
        """Parse expression"""
        expr = expr.strip()
        
        # Handle boolean literals
        literal_map = {
            'true': True,
            'false': False,
            'null': None,
        }
        if expr in literal_map:
            return {
                'type': 'literal',
                'value': literal_map[expr],
                'line': line_num,
            }
        
        # Handle string literals
        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            return {'type': 'literal', 'value': expr[1:-1], 'line': line_num}
        
        # Handle numeric literals
        try:
            if '.' in expr:
                return {
                    'type': 'literal',
                    'value': float(expr),
                    'line': line_num,
                }
            else:
                return {
                    'type': 'literal',
                    'value': int(expr),
                    'line': line_num,
                }
        except ValueError:
            pass
        
        # Handle function calls
        if '(' in expr and expr.endswith(')'):
            func_name = expr[:expr.index('(')]
            args_str = expr[expr.index('(')+1:-1]
            args = []
            if args_str.strip():
                # Simple argument parsing
                args = [
                    self._parse_expression(arg.strip(), line_num)
                    for arg in args_str.split(',')
                ]
            return {
                'type': 'function_call',
                'name': func_name.strip(),
                'args': args,
                'line': line_num
            }
        
        # Handle binary operations
        for op in ['+', '-', '*', '/', '%']:
            if op in expr:
                parts = expr.split(op, 1)
                if len(parts) == 2:
                    return {
                        'type': 'binary_op',
                        'operator': op,
                        'left': self._parse_expression(
                            parts[0].strip(), line_num
                        ),
                        'right': self._parse_expression(
                            parts[1].strip(), line_num
                        ),
                        'line': line_num,
                    }
        
        # Handle variable reference
        return {'type': 'variable', 'name': expr, 'line': line_num}


class BasicAST:
    """Basic AST container"""
    
    def __init__(self, statements):
        self.statements = statements
    
    def __iter__(self):
        return iter(self.statements)


class SonaParseError(Exception):
    """Exception raised during parsing"""
    pass


# Main parsing function for external use
def parse_sona_code(source_code, filename="<string>", parser_type='auto'):
    """
    Primary parsing function for Sona code
    
    Args:
        source_code: The Sona source code to parse
        filename: Optional filename for error reporting
        parser_type: 'enhanced', 'basic', or 'auto'
        
    Returns:
        AST representation of the parsed code
    """
    parser = SonaParser(parser_type)
    return parser.parse(source_code, filename)


# Export main classes and functions
__all__ = [
    'SonaParser',
    'BasicSonaParser',
    'SonaParserv090',  # Alias for compatibility
    'BasicAST',
    'SonaParseError',
    'parse_sona_code',
]

# Compatibility alias
SonaParserv090 = SonaParser
