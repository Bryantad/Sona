"""
Sona v0.9.0 - Enhanced Parser for New Language Features
======================================================

This module provides the enhanced parser for Sona v0.9.0, built on top of Lark
to handle the new control flow constructs, module system, AI integration,
and cognitive programming features.

The parser maintains full backward compatibility with existing Sona code while
adding support for the advanced features introduced in v0.9.0.

Author: Sona Development Team
Version: 0.9.0
Date: August 2025
"""

from pathlib import Path
from typing import Any, Dict, List, Optional


try:
    from lark import Lark, Token, Transformer, Tree, v_args
    from lark.exceptions import ParseError, VisitError
except ImportError:
    print("⚠️  Warning: Lark parser not available. Install with: pip install lark")
    Lark = None

# Import our AST nodes when available
AST_NODES_AVAILABLE = False
try:
    from .ast_nodes_v090 import *
    AST_NODES_AVAILABLE = True
except ImportError:
    # Fallback for development - define minimal placeholder classes
    class ASTNode:
        def accept(self, visitor): pass
        def execute(self, vm): pass
    
    class Statement(ASTNode): pass
    class Expression(ASTNode): 
        def evaluate(self, scope): pass
    
    class LiteralExpression(Expression):
        def __init__(self, value): self.value = value
        def evaluate(self, scope): return self.value
    
    class VariableExpression(Expression):
        def __init__(self, name): self.name = name
        def evaluate(self, scope): return scope.get(self.name)
    
    print("ℹ️  Using placeholder AST nodes - full nodes not available")

class SonaParserv090:
    """
    Enhanced parser for Sona v0.9.0 with full feature support
    
    This parser handles all v0.9.0 language constructs including:
    - Enhanced control flow (if/else/elif, loops, try/catch)
    - Module system (import/export)
    - AI integration statements
    - Cognitive programming constructs
    - Backward compatibility with existing syntax
    """
    
    def __init__(self, grammar_file: str | None = None):
        """Initialize the enhanced parser"""
        self.grammar_file = grammar_file or self._get_default_grammar()
        self.parser = None
        self.transformer = None
        
        # Feature flags
        self.features_enabled = {
            'enhanced_control_flow': True,
            'module_system': True,
            'ai_integration': True,
            'cognitive_programming': True,
            'backward_compatibility': True
        }
        
        # Initialize the parser
        self._initialize_parser()
    
    def _get_default_grammar(self) -> str:
        """Get the default grammar file path"""
        current_dir = Path(__file__).parent
        # Use the FIXED grammar with multi-parameter support
        grammar_path = current_dir / "grammar_v091_fixed.lark"
        
        if grammar_path.exists():
            return str(grammar_path)
        else:
            # Fallback to original if fixed version not found
            fallback_path = current_dir / "grammar_v090.lark"
            if fallback_path.exists():
                return str(fallback_path)
            else:
                # Final fallback to embedded grammar
                return self._get_embedded_grammar()
    
    def _get_embedded_grammar(self) -> str:
        """Get embedded grammar as fallback"""
        return '''
        // Embedded minimal grammar for Sona v0.9.0
        start: statement*
        
        statement: if_statement
                | for_statement  
                | while_statement
                | try_statement
                | break_statement
                | continue_statement
                | import_statement
                | assignment
                | expression_statement
        
        if_statement: "if" expression ":" block ("elif" expression ":" block)* ("else" ":" block)?
        for_statement: "for" IDENTIFIER "in" expression ":" block
        while_statement: "while" expression ":" block
        try_statement: "try" ":" block ("catch" IDENTIFIER? ":" block)* ("finally" ":" block)?
        
        break_statement: "break"
        continue_statement: "continue"
        
        import_statement: "import" IDENTIFIER ("as" IDENTIFIER)?
                       | "from" IDENTIFIER "import" IDENTIFIER ("," IDENTIFIER)*
        
        assignment: IDENTIFIER "=" expression
        expression_statement: expression
        
        expression: term
                  | expression "+" term
                  | expression "-" term
                  | expression "==" term
                  | expression "!=" term
                  | expression "<" term
                  | expression ">" term
                  | expression "<=" term
                  | expression ">=" term
                  | expression "&&" term
                  | expression "||" term
        
        term: factor
            | term "*" factor
            | term "/" factor
            | term "%" factor
        
        factor: "(" expression ")"
              | NUMBER
              | STRING
              | IDENTIFIER
              | function_call
        
        function_call: IDENTIFIER "(" (expression ("," expression)*)? ")"
        
        block: NEWLINE INDENT statement+ DEDENT
             | statement
        
        %import common.CNAME -> IDENTIFIER
        %import common.NUMBER
        %import common.ESCAPED_STRING -> STRING
        %import common.WS
        %import common.NEWLINE
        
        %ignore WS
        '''
    
    def _initialize_parser(self):
        """Initialize the Lark parser and transformer"""
        try:
            if Lark is None:
                raise ImportError("Lark parser not available")
            
            # Load grammar from file or use embedded
            if Path(self.grammar_file).exists():
                with open(self.grammar_file, encoding='utf-8') as f:
                    grammar_content = f.read()
            else:
                grammar_content = self.grammar_file  # Assume it's the embedded grammar
            
            # Create parser with enhanced error reporting
            self.parser = Lark(
                grammar_content,
                parser='earley',  # Use Earley for better error recovery
                lexer='standard',  # Fixed: Use standard lexer instead of contextual
                propagate_positions=True,
                maybe_placeholders=True,
                debug=False
            )
            
            # Initialize the transformer
            self.transformer = SonaASTTransformer(self.features_enabled)
            
            print("✅ Sona v0.9.6 parser initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize parser: {e}")
            print("   Falling back to basic parsing mode")
            self.parser = None
            self.transformer = None
    
    def parse(self, source_code: str, filename: str = "<string>") -> list[ASTNode] | None:
        """
        Parse Sona source code into AST nodes
        
        Args:
            source_code: The Sona source code to parse
            filename: Optional filename for error reporting
            
        Returns:
            List of AST nodes or None if parsing failed
        """
        if not self.parser:
            return self._fallback_parse(source_code)
        
        try:
            # Parse the source code
            parse_tree = self.parser.parse(source_code)
            
            # Transform to AST
            if self.transformer:
                ast_nodes = self.transformer.transform(parse_tree)
                return ast_nodes if isinstance(ast_nodes, list) else [ast_nodes]
            else:
                return self._fallback_transform(parse_tree)
                
        except ParseError as e:
            self._handle_parse_error(e, source_code, filename)
            return None
        except Exception as e:
            self._handle_general_error(e, source_code, filename)
            return None
    
    def parse_expression(self, expression_code: str) -> Expression | None:
        """Parse a single expression"""
        if not self.parser:
            return self._fallback_parse_expression(expression_code)
        
        try:
            # Wrap expression in a minimal program
            wrapped_code = f"result = {expression_code}"
            parse_tree = self.parser.parse(wrapped_code)
            
            if self.transformer:
                ast_nodes = self.transformer.transform(parse_tree)
                # Extract the expression from the assignment
                if ast_nodes and hasattr(ast_nodes[0], 'value'):
                    return ast_nodes[0].value
            
            return None
            
        except Exception as e:
            print(f"⚠️  Failed to parse expression '{expression_code}': {e}")
            return None
    
    def validate_syntax(self, source_code: str) -> dict[str, Any]:
        """
        Validate syntax without creating AST
        
        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        if not self.parser:
            result['errors'].append("Parser not available")
            return result
        
        try:
            # Try to parse
            parse_tree = self.parser.parse(source_code)
            result['valid'] = True
            
            # Check for potential issues
            warnings = self._analyze_parse_tree(parse_tree)
            result['warnings'] = warnings
            
        except ParseError as e:
            result['errors'].append(str(e))
            result['suggestions'] = self._get_parse_suggestions(e, source_code)
        except Exception as e:
            result['errors'].append(f"Unexpected error: {e}")
        
        return result
    
    def _fallback_parse(self, source_code: str) -> list[ASTNode]:
        """Fallback parsing when main parser is not available"""
        print("ℹ️  Using fallback parser")
        
        # Very basic line-by-line parsing
        lines = source_code.strip().split('\n')
        ast_nodes = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Try to create basic AST nodes
            node = self._parse_line_basic(line)
            if node:
                ast_nodes.append(node)
        
        return ast_nodes
    
    def _parse_line_basic(self, line: str) -> ASTNode | None:
        """Parse a single line with basic logic"""
        line = line.strip()
        
        # Assignment
        if '=' in line and not any(op in line for op in ['==', '!=', '<=', '>=']):
            parts = line.split('=', 1)
            if len(parts) == 2:
                var_name = parts[0].strip()
                value_expr = parts[1].strip()
                # Create a basic assignment node (would need proper implementation)
                return None  # Placeholder
        
        # If statement
        if line.startswith('if '):
            # Create basic if node (would need proper implementation)
            return None  # Placeholder
        
        # Return None for unrecognized lines
        return None
    
    def _fallback_parse_expression(self, expression_code: str) -> Expression | None:
        """Fallback expression parsing"""
        # Very basic expression parsing
        expression_code = expression_code.strip()
        
        # Number literal
        try:
            value = float(expression_code)
            return LiteralExpression(value)
        except ValueError:
            pass
        
        # String literal
        if (expression_code.startswith('"') and expression_code.endswith('"')) or \
           (expression_code.startswith("'") and expression_code.endswith("'")):
            return LiteralExpression(expression_code[1:-1])
        
        # Variable reference
        if expression_code.isidentifier():
            return VariableExpression(expression_code)
        
        # Could not parse
        return None
    
    def _fallback_transform(self, parse_tree) -> list[ASTNode]:
        """Fallback transformation when transformer is not available"""
        print("ℹ️  Using fallback transformation")
        # This would implement basic tree-to-AST conversion
        return []
    
    def _handle_parse_error(self, error: ParseError, source_code: str, filename: str):
        """Handle parsing errors with enhanced reporting"""
        print(f"❌ Parse error in {filename}:")
        print(f"   {error}")
        
        # Try to provide helpful suggestions
        suggestions = self._get_parse_suggestions(error, source_code)
        if suggestions:
            print("💡 Suggestions:")
            for suggestion in suggestions:
                print(f"   - {suggestion}")
    
    def _handle_general_error(self, error: Exception, source_code: str, filename: str):
        """Handle general errors during parsing"""
        print(f"❌ Error parsing {filename}: {error}")
        
        # Provide basic debugging info
        print(f"   Error type: {type(error).__name__}")
        if hasattr(error, 'line'):
            print(f"   Line: {error.line}")
        if hasattr(error, 'column'):
            print(f"   Column: {error.column}")
    
    def _get_parse_suggestions(self, error: ParseError, source_code: str) -> list[str]:
        """Generate helpful suggestions for parse errors"""
        suggestions = []
        
        error_msg = str(error).lower()
        
        if 'unexpected token' in error_msg:
            suggestions.append("Check for missing or extra punctuation")
            suggestions.append("Verify that all brackets and parentheses are balanced")
        
        if 'indentation' in error_msg or 'indent' in error_msg:
            suggestions.append("Check indentation - use consistent spaces or tabs")
            suggestions.append("Make sure block statements are properly indented")
        
        if 'eof' in error_msg or 'end of file' in error_msg:
            suggestions.append("Check for unclosed blocks or statements")
            suggestions.append("Ensure all control structures have proper endings")
        
        return suggestions
    
    def _analyze_parse_tree(self, parse_tree) -> list[str]:
        """Analyze parse tree for potential issues"""
        warnings = []
        
        # This would implement various heuristics to detect potential problems
        # For now, just return empty list
        
        return warnings
    
    def get_parser_info(self) -> dict[str, Any]:
        """Get information about the parser configuration"""
        return {
            'version': '0.9.0',
            'parser_available': self.parser is not None,
            'transformer_available': self.transformer is not None,
            'grammar_file': self.grammar_file,
            'features_enabled': self.features_enabled,
            'backend': 'Lark' if Lark else 'Fallback'
        }
    
    def enable_feature(self, feature_name: str) -> bool:
        """Enable a parser feature"""
        if feature_name in self.features_enabled:
            self.features_enabled[feature_name] = True
            # Reinitialize transformer with new settings
            if self.transformer:
                self.transformer.features_enabled = self.features_enabled
            return True
        return False
    
    def disable_feature(self, feature_name: str) -> bool:
        """Disable a parser feature"""
        if feature_name in self.features_enabled:
            self.features_enabled[feature_name] = False
            # Reinitialize transformer with new settings
            if self.transformer:
                self.transformer.features_enabled = self.features_enabled
            return True
        return False


class SonaASTTransformer(Transformer):
    """
    Transformer to convert Lark parse trees to Sona AST nodes
    
    This transformer handles all the new v0.9.0 language constructs
    while maintaining backward compatibility.
    """
    
    def __init__(self, features_enabled: dict[str, bool]):
        super().__init__()
        self.features_enabled = features_enabled
        self.current_line = 1
    
    # ========================================================================
    # PROGRAM STRUCTURE
    # ========================================================================
    
    def start(self, statements):
        """Transform the top-level program"""
        # Flatten statement_list results
        result = []
        for stmt in statements:
            if stmt is None:
                continue
            elif isinstance(stmt, list):
                result.extend(stmt)
            else:
                result.append(stmt)
        return result
    
    def statement(self, children):
        """Transform a statement"""
        if len(children) == 1:
            return children[0]
        return None
    
    # ========================================================================
    # ENHANCED CONTROL FLOW
    # ========================================================================
    
    @v_args(inline=True)
    def if_statement(self, condition, if_body, *rest):
        """Transform enhanced if statement"""
        if not self.features_enabled['enhanced_control_flow']:
            return self._basic_if_statement(condition, if_body, rest)
        
        elif_clauses = []
        else_body = None
        
        # Process elif and else clauses
        i = 0
        while i < len(rest):
            if isinstance(rest[i], Tree) and rest[i].data == 'elif_clause':
                elif_clauses.append(rest[i])
                i += 1
            elif isinstance(rest[i], Tree) and rest[i].data == 'else_clause':
                else_body = rest[i].children[0]  # The block
                break
            else:
                i += 1
        
        return EnhancedIfStatement(
            condition=condition,
            if_body=if_body,
            elif_clauses=elif_clauses,
            else_body=else_body,
            line_number=self.current_line
        )
    
    @v_args(inline=True)
    def elif_clause(self, condition, body):
        """Transform elif clause"""
        return ElifClause(condition=condition, body=body)
    
    @v_args(inline=True)
    def for_statement(self, iterator_var, iterable, body):
        """Transform enhanced for loop"""
        if not self.features_enabled['enhanced_control_flow']:
            return self._basic_for_statement(iterator_var, iterable, body)
        
        return EnhancedForLoop(
            iterator_var=str(iterator_var),
            iterable=iterable,
            body=body,
            line_number=self.current_line
        )
    
    @v_args(inline=True)
    def while_statement(self, condition, body):
        """Transform enhanced while loop"""
        if not self.features_enabled['enhanced_control_flow']:
            return self._basic_while_statement(condition, body)
        
        return EnhancedWhileLoop(
            condition=condition,
            body=body,
            line_number=self.current_line
        )
    
    @v_args(inline=True)
    def try_statement(self, try_body, *rest):
        """Transform enhanced try statement"""
        if not self.features_enabled['enhanced_control_flow']:
            return self._basic_try_statement(try_body, rest)
        
        catch_clauses = []
        finally_body = None
        
        for item in rest:
            if isinstance(item, Tree):
                if item.data == 'catch_clause':
                    catch_clauses.append(item)
                elif item.data == 'finally_clause':
                    finally_body = item.children[0]  # The block
        
        return EnhancedTryStatement(
            try_body=try_body,
            catch_clauses=catch_clauses,
            finally_body=finally_body,
            line_number=self.current_line
        )
    
    @v_args(inline=True)
    def catch_clause(self, exception_type, var_name, body):
        """Transform catch clause"""
        return CatchClause(
            exception_type=str(exception_type) if exception_type else "Exception",
            var_name=str(var_name) if var_name else None,
            body=body
        )
    
    def break_statement(self, children):
        """Transform break statement"""
        return BreakStatement(line_number=self.current_line)
    
    def continue_statement(self, children):
        """Transform continue statement"""
        return ContinueStatement(line_number=self.current_line)
    
    # ========================================================================
    # MODULE SYSTEM
    # ========================================================================
    
    @v_args(inline=True)
    def import_statement(self, module_path, alias=None):
        """Transform import statement"""
        if not self.features_enabled['module_system']:
            return None  # Skip if module system disabled
        
        return ImportStatement(
            module_path=str(module_path),
            alias=str(alias) if alias else None,
            line_number=self.current_line
        )
    
    @v_args(inline=True)
    def import_from_statement(self, module_path, *import_items):
        """Transform import from statement"""
        if not self.features_enabled['module_system']:
            return None  # Skip if module system disabled
        
        return ImportFromStatement(
            module_path=str(module_path),
            import_list=[str(item) for item in import_items],
            line_number=self.current_line
        )
    
    # ========================================================================
    # AI INTEGRATION (FIXED for multi-parameter support)
    # ========================================================================
    
    def arg_list(self, *args):
        """Transform argument list"""
        return list(args)
    
    def ai_complete_stmt(self, arguments):
        """Transform AI complete statement with multi-parameter support"""
        if not self.features_enabled['ai_integration']:
            return None  # Skip if AI integration disabled
        
        # Handle both single and multi-parameter calls
        if isinstance(arguments, list):
            prompt = str(arguments[0]) if arguments else ""
            # Additional parameters: language, level, etc.
            options = arguments[1:] if len(arguments) > 1 else []
        else:
            prompt = str(arguments)
            options = []
        
        return AICompleteStatement(
            prompt=prompt,
            options=options,
            line_number=self.current_line
        )
    
    def ai_explain_stmt(self, arguments):
        """Transform AI explain statement with multi-parameter support"""
        if not self.features_enabled['ai_integration']:
            return None  # Skip if AI integration disabled
            
        # Handle both single and multi-parameter calls
        if isinstance(arguments, list):
            target = arguments[0] if arguments else ""
            # Additional parameters: level, audience, etc.
            options = arguments[1:] if len(arguments) > 1 else []
        else:
            target = arguments
            options = []
        
        return AIExplainStatement(
            target=target,
            options=options,
            line_number=self.current_line
        )
    
    def ai_debug_stmt(self, arguments=None):
        """Transform AI debug statement with multi-parameter support"""
        if not self.features_enabled['ai_integration']:
            return None
            
        if arguments is None:
            code = ""
            options = []
        elif isinstance(arguments, list):
            code = arguments[0] if arguments else ""
            options = arguments[1:] if len(arguments) > 1 else []
        else:
            code = arguments
            options = []
            
        return AIDebugStatement(
            code=code,
            options=options,
            line_number=self.current_line
        )
    
    def ai_optimize_stmt(self, arguments):
        """Transform AI optimize statement with multi-parameter support"""
        if not self.features_enabled['ai_integration']:
            return None
            
        if isinstance(arguments, list):
            code = arguments[0] if arguments else ""
            options = arguments[1:] if len(arguments) > 1 else []
        else:
            code = arguments
            options = []
            
        return AIOptimizeStatement(
            code=code,
            options=options,
            line_number=self.current_line
        )
    
    # ========================================================================
    # AI FUNCTIONS AS EXPRESSIONS
    # ========================================================================
    
    def ai_complete_expr(self, arguments):
        """Transform AI complete as expression"""
        return self.ai_complete_stmt(arguments)
    
    def ai_explain_expr(self, arguments):
        """Transform AI explain as expression"""
        return self.ai_explain_stmt(arguments)
    
    def ai_debug_expr(self, arguments=None):
        """Transform AI debug as expression"""
        return self.ai_debug_stmt(arguments)
    
    def ai_optimize_expr(self, arguments):
        """Transform AI optimize as expression"""
        return self.ai_optimize_stmt(arguments)
    
    # ========================================================================
    # EXPRESSIONS
    # ========================================================================
    
    def var_assignment(self, items):
        """Transform variable assignment: let x = value"""
        if len(items) == 2:
            var_name, value = items
            # Create a variable assignment AST node
            from .ast_nodes_v090 import VariableAssignment
            return VariableAssignment(
                name=str(var_name),
                value=value,
                is_const=False,  # Will be updated for const
                line_number=self.current_line
            )
        return None
    
    def bare_assignment(self, items):
        """Transform bare assignment: x = value"""
        if len(items) == 2:
            var_name, value = items
            from .ast_nodes_v090 import VariableAssignment
            return VariableAssignment(
                name=str(var_name),
                value=value,
                is_const=False,
                line_number=self.current_line
            )
        return None
    
    @v_args(inline=True)
    def assignment(self, var_name, value):
        """Transform assignment statement"""
        # For now, create a basic assignment representation
        # This would need proper assignment AST node
        return None  # Placeholder
    
    def expression_statement(self, children):
        """Transform expression statement"""
        return children[0] if children else None
    
    @v_args(inline=True)
    def expression(self, *args):
        """Transform expression"""
        if len(args) == 1:
            return args[0]
        elif len(args) == 3:
            # Binary operation
            left, operator, right = args
            return BinaryOperatorExpression(
                left=left,
                operator=str(operator),
                right=right,
                line_number=self.current_line
            )
        return None
    
    def term(self, children):
        """Transform term"""
        return self.expression(children)
    
    @v_args(inline=True)
    def factor(self, value):
        """Transform factor"""
        return value
    
    @v_args(inline=True)
    def function_call(self, function_name, *arguments):
        """Transform function call"""
        return FunctionCallExpression(
            function_name=str(function_name),
            arguments=list(arguments),
            line_number=self.current_line
        )
    
    def block(self, statements):
        """Transform block of statements"""
        return [stmt for stmt in statements if stmt is not None]
    
    # ========================================================================
    # LITERALS
    # ========================================================================
    
    def NUMBER(self, token):
        """Transform number literal"""
        try:
            if '.' in str(token):
                return LiteralExpression(float(token))
            else:
                return LiteralExpression(int(token))
        except ValueError:
            return LiteralExpression(0)
    
    def STRING(self, token):
        """Transform string literal"""
        # Remove quotes
        content = str(token)[1:-1]
        return LiteralExpression(content)
    
    def IDENTIFIER(self, token):
        """Transform identifier"""
        return VariableExpression(str(token))
    
    # ========================================================================
    # TIER 1 TRANSFORMER METHODS (v0.9.6)
    # ========================================================================
    
    def statement_list(self, statements):
        """Transform list of statements"""
        result = []
        for stmt in statements:
            if stmt is not None:
                if isinstance(stmt, list):
                    result.extend(stmt)
                else:
                    result.append(stmt)
        return result
    
    def print_stmt(self, children):
        """Transform print statement"""
        # children contains the arguments to print
        if children and len(children) > 0:
            # Get the expression (may be nested in lists)
            expr = children[0]
            if isinstance(expr, list) and len(expr) > 0:
                expr = expr[0]
                if isinstance(expr, list) and len(expr) > 0:
                    expr = expr[0]
        else:
            expr = None
        
        from .ast_nodes_v090 import PrintStatement
        return PrintStatement(expr, line_number=self.current_line)
    
    def let_assign(self, children):
        """Transform let assignment"""
        name_token = children[0]
        value_expr = children[1]
        from .ast_nodes_v090 import VariableAssignment
        return VariableAssignment(
            name=str(name_token),
            value=value_expr,
            is_const=False,
            line_number=self.current_line
        )
    
    def const_assign(self, children):
        """Transform const assignment"""
        name_token = children[0]
        value_expr = children[1]
        from .ast_nodes_v090 import VariableAssignment
        return VariableAssignment(
            name=str(name_token),
            value=value_expr,
            is_const=True,
            line_number=self.current_line
        )
    
    def variable(self, children):
        """Transform variable reference"""
        name_token = children[0]
        from .ast_nodes_v090 import VariableExpression
        return VariableExpression(str(name_token))
    
    def postfix_expr(self, children):
        """Transform postfix expressions (calls, indexing, props)"""
        from .ast_nodes_v090 import (
            VariableExpression,
            FunctionCallExpression,
            PropertyAccessExpression,
            MethodCallExpression
        )
        
        base = children[0]
        
        # Apply suffixes left-to-right
        for suffix in children[1:]:
            if isinstance(suffix, tuple):
                suffix_type, suffix_data = suffix
                
                if suffix_type == "call":
                    # Function call
                    args = suffix_data if suffix_data else []
                    if isinstance(base, VariableExpression):
                        base = FunctionCallExpression(
                            name=base.name,
                            arguments=args,
                            line_number=self.current_line
                        )
                    elif isinstance(base, PropertyAccessExpression):
                        # Method call: obj.method()
                        base = MethodCallExpression(
                            object=base.object,
                            method_name=base.property_name,
                            arguments=args,
                            line_number=self.current_line
                        )
                    else:
                        raise NotImplementedError(
                            "Function calls on expressions not supported"
                        )
                        
                elif suffix_type == "index":
                    # Array/dict indexing
                    index_expr = suffix_data
                    from .ast_nodes_v090 import IndexExpression
                    base = IndexExpression(
                        object=base,
                        index=index_expr,
                        line_number=self.current_line
                    )
                    
                elif suffix_type == "prop":
                    # Property access
                    prop_name = suffix_data
                    base = PropertyAccessExpression(
                        object=base,
                        property_name=prop_name,
                        line_number=self.current_line
                    )
        
        return base
    
    def call_suffix(self, children):
        """Transform function call suffix"""
        args = children[0] if children else []
        # arguments already returns a list, don't wrap again
        return ("call", args if args else [])
    
    def index_suffix(self, children):
        """Transform index suffix"""
        index_expr = children[0]
        return ("index", index_expr)
    
    def prop_suffix(self, children):
        """Transform property access suffix"""
        prop_name = str(children[0])
        return ("prop", prop_name)
    
    def arguments(self, children):
        """Transform function call arguments"""
        return children  # Already a list of expressions
    
    def additive_expr(self, children):
        """Transform additive expression (+ or -)"""
        # Grammar: multiplicative_expr (ADDITIVE_OP multiplicative_expr)*
        if len(children) == 1:
            return children[0]
        
        from .ast_nodes_v090 import BinaryOperatorExpression
        
        result = children[0]
        i = 1
        while i < len(children):
            op_token = children[i]
            if isinstance(op_token, Token):
                operator = str(op_token.value)
            else:
                operator = str(op_token)
            right = children[i + 1]
            
            result = BinaryOperatorExpression(
                left=result,
                operator=operator,
                right=right,
                line_number=self.current_line
            )
            i += 2
        
        return result
    
    def multiplicative_expr(self, children):
        """Transform multiplicative expression (* / %)"""
        # Grammar: power_expr (MULTIPLICATIVE_OP power_expr)*
        if len(children) == 1:
            return children[0]
        
        from .ast_nodes_v090 import BinaryOperatorExpression
        
        result = children[0]
        i = 1
        while i < len(children):
            op_token = children[i]
            if isinstance(op_token, Token):
                operator = str(op_token.value)
            else:
                operator = str(op_token)
            right = children[i + 1]
            
            result = BinaryOperatorExpression(
                left=result,
                operator=operator,
                right=right,
                line_number=self.current_line
            )
            i += 2
        
        return result
    
    def comparison_expr(self, children):
        """Transform comparison expression (<= >= < >)"""
        # Grammar: additive_expr (COMPARISON_OP additive_expr)*
        # children = [expr] or [expr, TOKEN, expr, TOKEN, expr, ...]
        if len(children) == 1:
            return children[0]
        
        # Build left-to-right: expr OP expr OP expr => (expr OP expr) OP expr
        from .ast_nodes_v090 import BinaryOperatorExpression
        
        result = children[0]
        i = 1
        while i < len(children):
            # Get operator token
            op_token = children[i]
            if isinstance(op_token, Token):
                operator = str(op_token.value)
            else:
                operator = str(op_token)
            
            # Get right operand
            right = children[i + 1]
            
            # Build binary expression
            result = BinaryOperatorExpression(
                left=result,
                operator=operator,
                right=right,
                line_number=self.current_line
            )
            i += 2
        
        return result
    
    # Note: operator helper functions (comparison_op, equality_op, etc.) 
    # are no longer used since operators are now extracted directly
    # from terminal tokens in the expression transformers above
    
    def equality_expr(self, children):
        """Transform equality expression (== !=)"""
        # Grammar: comparison_expr (EQUALITY_OP comparison_expr)*
        if len(children) == 1:
            return children[0]
        
        from .ast_nodes_v090 import BinaryOperatorExpression
        
        result = children[0]
        i = 1
        while i < len(children):
            op_token = children[i]
            if isinstance(op_token, Token):
                operator = str(op_token.value)
            else:
                operator = str(op_token)
            right = children[i + 1]
            
            result = BinaryOperatorExpression(
                left=result,
                operator=operator,
                right=right,
                line_number=self.current_line
            )
            i += 2
        
        return result
    
    def equality_op(self, children):
        """Transform equality operator to string"""
        if not children:
            return "=="
        return str(children[0])
    
    def additive_op(self, children):
        """Transform additive operator to string"""
        if not children:
            return "+"
        return str(children[0])
    
    def multiplicative_op(self, children):
        """Transform multiplicative operator to string"""
        if not children:
            return "*"
        return str(children[0])
    
    def arg_list(self, children):
        """Transform argument list (from arguments rule)"""
        return children  # Return flat list of expressions
    
    def func_call(self, children):
        """Transform function call"""
        name_token = children[0]
        args = children[1] if len(children) > 1 else []
        if args and not isinstance(args, list):
            args = [args]
        from .ast_nodes_v090 import FunctionCallExpression
        return FunctionCallExpression(
            name=str(name_token),
            arguments=args,
            line_number=self.current_line
        )
    
    def func_def(self, children):
        """Transform function definition"""
        name_token = children[0]
        params = children[1] if len(children) > 1 else []
        body = children[2] if len(children) > 2 else []
        
        # Extract parameter names
        if params and not isinstance(params, list):
            params = [params]
        param_names = [str(p) for p in params]
        
        # Ensure body is a list
        if body and not isinstance(body, list):
            body = [body]
        
        from .ast_nodes_v090 import FunctionDefinition
        return FunctionDefinition(
            name=str(name_token),
            parameters=param_names,
            body=body,
            line_number=self.current_line
        )
    
    def param_list(self, children):
        """Transform parameter list"""
        return [str(p) for p in children]
    
    def func_params(self, children):
        """Transform function parameters (v091 grammar)"""
        return children  # List of func_param results (already strings)
    
    def func_param(self, children):
        """Transform single function parameter"""
        param_name = str(children[0])  # NAME token
        # default_value = children[1] if len(children) > 1 else None
        # For now, just return the parameter name
        # TODO: Handle default values
        return param_name
    
    def return_stmt(self, children):
        """Transform return statement"""
        expr = children[0] if children else None
        from .ast_nodes_v090 import ReturnStatement
        return ReturnStatement(expr, line_number=self.current_line)
    
    def break_stmt(self, children):
        """Transform break statement"""
        from .ast_nodes_v090 import BreakStatement
        return BreakStatement(line_number=self.current_line)
    
    def continue_stmt(self, children):
        """Transform continue statement"""
        from .ast_nodes_v090 import ContinueStatement
        return ContinueStatement(line_number=self.current_line)
    
    def num(self, children):
        """Transform number literal"""
        value = float(children[0])
        if value.is_integer():
            value = int(value)
        from .ast_nodes_v090 import LiteralExpression
        return LiteralExpression(value, line_number=self.current_line)
    
    def str(self, children):
        """Transform string literal"""
        import ast as python_ast
        string_token = children[0]
        token_str = str(string_token)
        # Use literal_eval to properly handle escape sequences
        try:
            string_value = python_ast.literal_eval(token_str)
        except Exception as e:
            # Fallback to simple quote removal
            string_value = token_str[1:-1]
        from .ast_nodes_v090 import LiteralExpression
        return LiteralExpression(string_value, line_number=self.current_line)
    
    def true(self, children):
        """Transform true literal"""
        from .ast_nodes_v090 import LiteralExpression
        return LiteralExpression(True, line_number=self.current_line)
    
    def false(self, children):
        """Transform false literal"""
        from .ast_nodes_v090 import LiteralExpression
        return LiteralExpression(False, line_number=self.current_line)
    
    def null(self, children):
        """Transform null literal"""
        from .ast_nodes_v090 import LiteralExpression
        return LiteralExpression(None, line_number=self.current_line)
    
    def array(self, children):
        """Transform array literal"""
        elements = children[0] if children else []
        if not isinstance(elements, list):
            elements = [elements] if elements else []
        from .ast_nodes_v090 import ListExpression
        return ListExpression(elements, line_number=self.current_line)
    
    def list_literal(self, children):
        """Transform list literal (v091 grammar)"""
        return self.array(children)
    
    def list_elements(self, children):
        """Transform list elements (v091 grammar)"""
        return list(children)
    
    def dict_literal(self, children):
        """Transform dictionary literal"""
        pairs = children[0] if children else []
        if not isinstance(pairs, list):
            pairs = [pairs] if pairs else []
        from .ast_nodes_v090 import DictionaryExpression
        return DictionaryExpression(pairs, line_number=self.current_line)
    
    def dict_elements(self, children):
        """Transform dictionary elements"""
        return list(children)  # List of (key, value) tuples
    
    def dict_pair(self, children):
        """Transform dictionary key-value pair"""
        key_item = children[0]
        value_expr = children[1]
        
        # Debug: check what we got
        # print(f"DEBUG dict_pair: key_item={key_item}, type={type(key_item)}")
        
        # Extract key string from token or expression
        from .ast_nodes_v090 import LiteralExpression
        if isinstance(key_item, LiteralExpression):
            key = str(key_item.value)
        elif hasattr(key_item, 'type'):
            if key_item.type == 'STRING':
                key = str(key_item)[1:-1]  # Remove quotes
            else:
                key = str(key_item)  # NAME token
        else:
            key = str(key_item)
        
        return (key, value_expr)
    
    def expr_list(self, children):
        """Transform expression list"""
        return list(children)
    
    def import_stmt(self, children):
        """Transform import statement"""
        module_path = children[0]
        alias = children[1] if len(children) > 1 else None
        from .ast_nodes_v090 import ImportStatement
        return ImportStatement(
            module_path=str(module_path),
            alias=str(alias) if alias else None,
            line_number=self.current_line
        )
    
    def module_path(self, children):
        """Transform module path"""
        return '.'.join(str(child) for child in children)
    
    def import_path(self, children):
        """Transform import path (v091 grammar)"""
        return '.'.join(str(child) for child in children)
    
    def enhanced_for_stmt(self, children):
        """Transform enhanced for loop"""
        iterator_var = str(children[0])  # NAME token
        iterable_expr = children[1]
        body = children[2] if len(children) > 2 else []
        
        # Ensure body is a list
        if body and not isinstance(body, list):
            body = [body]
        
        from .ast_nodes_v090 import EnhancedForLoop
        return EnhancedForLoop(
            iterator_var=iterator_var,
            iterable=iterable_expr,
            body=body,
            line_number=self.current_line
        )
    
    def enhanced_if_stmt(self, children):
        """Transform enhanced if statement"""
        # Grammar: "if" expr "{" statement_list? "}" elif_clause* else_clause?
        # children[0] = condition expression
        # children[1:] = elif/else clauses (if_body is implicitly in grammar)
        
        # First child is the condition - it should already be transformed
        condition = children[0]
        
        # Find the if body, elif clauses, and else body
        if_body = []
        elif_clauses = []
        else_body = None
        
        # Process remaining children
        for i in range(1, len(children)):
            child = children[i]
            # Check if it's a list (statement_list)
            if isinstance(child, list):
                # First list is if_body, others would be else_body
                if not if_body:
                    if_body = child
                else:
                    else_body = child
            # Check if it's an ElifClause
            elif hasattr(child, '__class__'):
                if child.__class__.__name__ == 'ElifClause':
                    elif_clauses.append(child)
        
        from .ast_nodes_v090 import EnhancedIfStatement
        return EnhancedIfStatement(
            condition=condition,
            if_body=if_body,
            elif_clauses=elif_clauses,
            else_body=else_body,
            line_number=self.current_line
        )
    
    def elif_clause(self, children):
        """Transform elif clause"""
        condition = children[0]
        body = children[1] if len(children) > 1 else []
        
        # Ensure body is a list
        if body and not isinstance(body, list):
            body = [body]
        
        from .ast_nodes_v090 import ElifClause
        return ElifClause(
            condition=condition,
            body=body
        )
    
    def else_clause(self, children):
        """Transform else clause"""
        # Return the body as a list
        body = children[0] if children else []
        if body and not isinstance(body, list):
            body = [body]
        return body
    
    def enhanced_while_stmt(self, children):
        """Transform enhanced while loop"""
        condition = children[0]
        body = children[1] if len(children) > 1 else []
        
        # Ensure body is a list
        if body and not isinstance(body, list):
            body = [body]
        
        from .ast_nodes_v090 import EnhancedWhileLoop
        return EnhancedWhileLoop(
            condition=condition,
            body=body,
            line_number=self.current_line
        )
    
    def enhanced_try_stmt(self, children):
        """Transform enhanced try statement"""
        try_body = children[0] if children else []
        catch_clauses = []
        finally_body = None
        
        # Process remaining children (catch/finally clauses)
        for child in children[1:]:
            if hasattr(child, '__class__'):
                from .ast_nodes_v090 import CatchClause
                if child.__class__.__name__ == 'CatchClause':
                    catch_clauses.append(child)
                elif isinstance(child, list):
                    # Could be finally body
                    if not catch_clauses:
                        catch_clauses.append(child)
                    else:
                        finally_body = child
        
        # Ensure try_body is a list
        if try_body and not isinstance(try_body, list):
            try_body = [try_body]
        
        from .ast_nodes_v090 import EnhancedTryStatement
        return EnhancedTryStatement(
            try_body=try_body,
            catch_clauses=catch_clauses,
            finally_body=finally_body,
            line_number=self.current_line
        )
    
    def catch_clause(self, children):
        """Transform catch clause"""
        exception_type = str(children[0])  # Exception type NAME
        var_name = None
        body = []
        
        # Check for 'as NAME' pattern
        if len(children) > 1:
            # Could be var_name or body
            if isinstance(children[1], str) or hasattr(children[1], 'type'):
                var_name = str(children[1])
                body = children[2] if len(children) > 2 else []
            else:
                body = children[1]
        
        # Ensure body is a list
        if body and not isinstance(body, list):
            body = [body]
        
        from .ast_nodes_v090 import CatchClause
        return CatchClause(
            exception_type=exception_type,
            var_name=var_name,
            body=body
        )
    
    def finally_clause(self, children):
        """Transform finally clause"""
        body = children[0] if children else []
        if body and not isinstance(body, list):
            body = [body]
        return body  # Just return the body list
    
    # ========================================================================
    # FALLBACK METHODS
    # ========================================================================
    
    def _basic_if_statement(self, condition, if_body, rest):
        """Basic if statement without enhanced features"""
        # Implement basic if statement
        return None  # Placeholder
    
    def _basic_for_statement(self, iterator_var, iterable, body):
        """Basic for statement without enhanced features"""
        # Implement basic for statement
        return None  # Placeholder
    
    def _basic_while_statement(self, condition, body):
        """Basic while statement without enhanced features"""
        # Implement basic while statement
        return None  # Placeholder
    
    def _basic_try_statement(self, try_body, rest):
        """Basic try statement without enhanced features"""
        # Implement basic try statement
        return None  # Placeholder


# ========================================================================
# UTILITY FUNCTIONS
# ========================================================================

def create_parser(grammar_file: str | None = None) -> SonaParserv090:
    """Create a new Sona v0.9.0 parser instance"""
    return SonaParserv090(grammar_file)

def parse_file(file_path: str, parser: SonaParserv090 | None = None) -> list[ASTNode] | None:
    """Parse a Sona file and return AST nodes"""
    if parser is None:
        parser = create_parser()
    
    try:
        with open(file_path, encoding='utf-8') as f:
            source_code = f.read()
        
        return parser.parse(source_code, file_path)
    
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return None
    except Exception as e:
        print(f"❌ Error reading file {file_path}: {e}")
        return None

def parse_string(source_code: str, parser: SonaParserv090 | None = None) -> list[ASTNode] | None:
    """Parse Sona source code string and return AST nodes"""
    if parser is None:
        parser = create_parser()
    
    return parser.parse(source_code)

def validate_file(file_path: str, parser: SonaParserv090 | None = None) -> dict[str, Any]:
    """Validate a Sona file and return validation results"""
    if parser is None:
        parser = create_parser()
    
    try:
        with open(file_path, encoding='utf-8') as f:
            source_code = f.read()
        
        return parser.validate_syntax(source_code)
    
    except FileNotFoundError:
        return {
            'valid': False,
            'errors': [f"File not found: {file_path}"],
            'warnings': [],
            'suggestions': []
        }
    except Exception as e:
        return {
            'valid': False,
            'errors': [f"Error reading file: {e}"],
            'warnings': [],
            'suggestions': []
        }


# ========================================================================
# EXAMPLE USAGE
# ========================================================================

if __name__ == "__main__":
    # Example usage of the enhanced parser
    print("Sona v0.9.0 Enhanced Parser Example")
    print("=" * 50)
    
    # Create parser
    parser = create_parser()
    print(f"Parser info: {parser.get_parser_info()}")
    
    # Example Sona v0.9.0 code
    example_code = '''
    // Enhanced control flow example
    if x > 10:
        print("High value")
    elif x > 5:
        print("Medium value") 
    else:
        print("Low value")
    
    // Enhanced loop with break/continue
    for item in items:
        if item < 0:
            continue
        if item > 100:
            break
        process(item)
    
    // Module import
    import math_utils as math
    from string_utils import split, join
    
    // AI integration
    ai_complete "suggest a sorting algorithm"
    ai_explain complex_function
    '''
    
    # Parse the example
    print("\nParsing example code...")
    ast_nodes = parser.parse(example_code)
    
    if ast_nodes:
        print(f"✅ Successfully parsed {len(ast_nodes)} statements")
        for i, node in enumerate(ast_nodes):
            if node:
                print(f"  {i+1}. {type(node).__name__}")
    else:
        print("❌ Parsing failed")
    
    # Validate syntax
    print("\nValidating syntax...")
    validation = parser.validate_syntax(example_code)
    print(f"Valid: {validation['valid']}")
    if validation['errors']:
        print("Errors:")
        for error in validation['errors']:
            print(f"  - {error}")
    if validation['warnings']:
        print("Warnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
