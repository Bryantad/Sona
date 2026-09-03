"""Canonical Lark frontend for the certified Sona 0.15.x language subset.

Advanced productions may be recognized for migration purposes, but only the
constructs transformed into typed AST nodes are executable. Recognized but
uncertified syntax is rejected with ``SONA-SEM-099``.
"""

import os
import re
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .errors import ErrorCode, SonaSyntaxError, SourceLocation


_LARK_IMPORT_ERROR: ImportError | None = None
try:
    from lark import Lark, Token, Transformer, Tree, v_args
    from lark.exceptions import ParseError, UnexpectedInput, VisitError
except ImportError as exc:
    _LARK_IMPORT_ERROR = exc
    Lark = None

    class Token:  # type: ignore[no-redef]
        pass

    class Tree:  # type: ignore[no-redef]
        pass

    class Transformer:  # type: ignore[no-redef]
        pass

    class ParseError(Exception):  # type: ignore[no-redef]
        pass

    class UnexpectedInput(Exception):  # type: ignore[no-redef]
        pass

    class VisitError(Exception):  # type: ignore[no-redef]
        pass

    def v_args(*_args, **_kwargs):  # type: ignore[no-redef]
        def decorator(function):
            return function
        return decorator

from .ast_nodes import *

class SonaParserv090:
    """Canonical parser retained under its historical import name."""
    def __init__(self, grammar_file: str | None = None):
        """Initialize the enhanced parser"""
        self.grammar_file = grammar_file or self._get_default_grammar()
        self.parser = None
        self.transformer = None
        self.initialization_error: str | None = None
        
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
        # Canonical grammar (single source of truth)
        grammar_path = current_dir / "grammar.lark"

        return str(grammar_path)
    
    def _initialize_parser(self):
        """Initialize the Lark parser and transformer"""
        try:
            if Lark is None:
                self.initialization_error = "The required Lark parser dependency is unavailable."
                return
            
            # Load the packaged canonical grammar. There is no embedded fallback.
            if Path(self.grammar_file).exists():
                with open(self.grammar_file, encoding='utf-8') as f:
                    grammar_content = f.read()
            else:
                self.initialization_error = "The packaged canonical grammar resource is unavailable."
                return
            
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
            
        except Exception:
            self.initialization_error = "The canonical grammar could not be initialized."
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
            raise SonaSyntaxError(
                self.initialization_error or "The canonical parser is unavailable.",
                location=SourceLocation(file=filename, line=1, column=1),
                suggestion="Install the base parser dependency and reinstall Sona if the packaged grammar is missing.",
                diagnostic_id="SONA-PARSE-099",
            )

        legacy_use = re.search(r"(?m)^\s*use\s+([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*;?", source_code)
        if legacy_use:
            raise SonaSyntaxError(
                "'use' module syntax is not supported by the certified Sona 0.15.x frontend.",
                location=SourceLocation(
                    file=filename,
                    line=source_code[:legacy_use.start()].count("\n") + 1,
                    column=legacy_use.start() - source_code.rfind("\n", 0, legacy_use.start()),
                ),
                suggestion="Use canonical module syntax, for example: import math;",
                diagnostic_id="SONA-PARSE-001",
            )
        
        try:
            if self.transformer:
                self.transformer.current_filename = filename
            # Parse the source code
            parse_tree = self.parser.parse(source_code)
            unsupported = self._unsupported_production(parse_tree)
            if unsupported:
                feature, line, column = unsupported
                raise SonaSyntaxError(
                    f"SONA-SEM-099: '{feature}' syntax is recognized but is not certified for execution in Sona 0.15.5.",
                    location=SourceLocation(file=filename, line=line, column=column),
                    suggestion="Use certified 0.15.x syntax or retain legacy compatibility mode while migrating.",
                    diagnostic_id="SONA-SEM-099",
                )
            
            # Transform to AST
            if self.transformer:
                ast_nodes = self.transformer.transform(parse_tree)
                normalized = ast_nodes if isinstance(ast_nodes, list) else [ast_nodes]
                leaked = self._find_raw_parser_object(normalized)
                if leaked:
                    raise SonaSyntaxError(
                        f"The '{leaked}' construct is recognized but its executable transformation is not certified.",
                        location=SourceLocation(file=filename, line=1, column=1),
                        suggestion="Use a documented stable construct instead.",
                        diagnostic_id="SONA-SEM-099",
                    )
                return normalized
            else:
                raise SonaSyntaxError(
                    "The canonical AST transformer is unavailable.",
                    location=SourceLocation(file=filename, line=1, column=1),
                    diagnostic_id="SONA-PARSE-099",
                )
                
        except SonaSyntaxError:
            raise
        except VisitError as error:
            original = getattr(error, "orig_exc", None)
            if isinstance(original, SonaSyntaxError):
                raise original
            raise SonaSyntaxError(
                "The canonical parser could not transform this source safely.",
                location=SourceLocation(file=filename, line=1, column=1),
                suggestion="Report this parser transformation failure with a minimal source example.",
                diagnostic_id="SONA-PARSE-099",
            ) from error
        except (ParseError, UnexpectedInput) as error:
            lines = source_code.splitlines()
            line = int(getattr(error, "line", 1) or 1)
            column = int(getattr(error, "column", 1) or 1)
            legacy_fn = self._legacy_fn_declaration(source_code, error)
            if legacy_fn is not None:
                fn_line, fn_column = legacy_fn
                source_line = lines[fn_line - 1] if 0 < fn_line <= len(lines) else ""
                raise SonaSyntaxError(
                    "The 'fn' keyword is not supported in Sona.",
                    location=SourceLocation(
                        file=filename,
                        line=fn_line,
                        column=fn_column,
                    ),
                    source_line=source_line,
                    suggestion="Use 'func' to declare a function.",
                    diagnostic_id="SONA-PARSE-001",
                ) from error
            if line < 1:
                line = max(1, len(lines))
            if column < 1:
                column = 1
            source_line = lines[line - 1] if 0 < line <= len(lines) else ""
            diagnostic_id = (
                "SONA-PARSE-003"
                if self._has_unclosed_delimiter(source_code)
                else "SONA-PARSE-001"
            )
            raise SonaSyntaxError(
                "Unexpected or incomplete Sona syntax.",
                location=SourceLocation(file=filename, line=line, column=column),
                source_line=source_line,
                suggestion="Check delimiters, operators, and incomplete statements near this location.",
                diagnostic_id=diagnostic_id,
            ) from error
        except Exception as error:
            raise SonaSyntaxError(
                "The canonical parser encountered an internal infrastructure failure.",
                location=SourceLocation(file=filename, line=1, column=1),
                suggestion="Run with parser debugging enabled and report the failure; source was not executed.",
                diagnostic_id="SONA-PARSE-099",
            ) from error

    def _legacy_fn_declaration(
        self,
        source_code: str,
        original_error: Exception,
    ) -> tuple[int, int] | None:
        """Identify an ``fn name(...)`` parser blocker without substring matching.

        The scanner ignores comments and string literals.  A candidate is
        accepted only when replacing that exact token with ``func`` lets the
        canonical parser advance beyond the original failure (or parse the
        program completely).  This ties the migration diagnostic to a function
        declaration position instead of treating every occurrence of ``fn`` as
        reserved syntax.
        """

        if self.parser is None:
            return None
        original_offset = int(
            getattr(original_error, "pos_in_stream", len(source_code)) or 0
        )
        tokens = self._significant_tokens(source_code)
        for index in range(len(tokens) - 2):
            text, start, end, line, column = tokens[index]
            next_text = tokens[index + 1][0]
            after_text = tokens[index + 2][0]
            if (
                text != "fn"
                or start > original_offset
                or not next_text.isidentifier()
                or after_text != "("
            ):
                continue
            rewritten = source_code[:start] + "func" + source_code[end:]
            try:
                self.parser.parse(rewritten)
            except (ParseError, UnexpectedInput) as rewritten_error:
                rewritten_offset = int(
                    getattr(rewritten_error, "pos_in_stream", 0) or 0
                )
                # ``func`` is one character longer, so advancing beyond the
                # original parser failure proves that ``fn`` was the blocker.
                if rewritten_offset <= original_offset:
                    continue
            except Exception:
                continue
            return line, column
        return None

    @staticmethod
    def _significant_tokens(
        source_code: str,
    ) -> list[tuple[str, int, int, int, int]]:
        """Return identifier and punctuation tokens outside trivia."""

        tokens: list[tuple[str, int, int, int, int]] = []
        index = 0
        line = 1
        column = 1
        length = len(source_code)
        while index < length:
            character = source_code[index]
            if character in " \t\r":
                index += 1
                column += 1
                continue
            if character == "\n":
                index += 1
                line += 1
                column = 1
                continue
            if source_code.startswith("//", index) or character == "#":
                while index < length and source_code[index] != "\n":
                    index += 1
                    column += 1
                continue
            if character in {'"', "'"}:
                quote = character
                index += 1
                column += 1
                escaped = False
                while index < length:
                    current = source_code[index]
                    if current == "\n":
                        line += 1
                        column = 1
                        index += 1
                        escaped = False
                        continue
                    index += 1
                    column += 1
                    if escaped:
                        escaped = False
                    elif current == "\\":
                        escaped = True
                    elif current == quote:
                        break
                continue
            start = index
            token_line = line
            token_column = column
            if character.isalpha() or character == "_":
                index += 1
                column += 1
                while index < length and (
                    source_code[index].isalnum() or source_code[index] == "_"
                ):
                    index += 1
                    column += 1
            else:
                index += 1
                column += 1
            tokens.append(
                (
                    source_code[start:index],
                    start,
                    index,
                    token_line,
                    token_column,
                )
            )
        return tokens

    @staticmethod
    def _has_unclosed_delimiter(source_code: str) -> bool:
        """Return whether source ends with an unmatched opening delimiter.

        This deliberately ignores delimiters in strings and line comments.  It is
        only used to refine a parser failure into the stable missing-delimiter
        diagnostic; it never accepts or transforms source.
        """
        pairs = {")": "(", "]": "[", "}": "{"}
        stack: list[str] = []
        quote: str | None = None
        escaped = False
        comment = False
        for character in source_code:
            if comment:
                if character == "\n":
                    comment = False
                continue
            if quote is not None:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == quote:
                    quote = None
                continue
            if character in {'"', "'"}:
                quote = character
            elif character == "#":
                comment = True
            elif character in "([{":
                stack.append(character)
            elif character in pairs:
                if stack and stack[-1] == pairs[character]:
                    stack.pop()
        # Unterminated strings are lexical errors, even if they occur inside a
        # call with an otherwise unmatched opening delimiter.
        return quote is None and bool(stack)
    
    def parse_expression(self, expression_code: str) -> Expression | None:
        """Parse a single expression"""
        wrapped_code = f"result = {expression_code}"
        ast_nodes = self.parse(wrapped_code, filename="<expression>")
        if ast_nodes and hasattr(ast_nodes[0], "value"):
            return ast_nodes[0].value
        raise SonaSyntaxError(
            "The expression did not transform to an executable value.",
            location=SourceLocation(file="<expression>", line=1, column=1),
            diagnostic_id="SONA-PARSE-099",
        )
    
    def validate_syntax(
        self, source_code: str, filename: str = "<validation>"
    ) -> dict[str, Any]:
        """
        Validate syntax without creating AST
        
        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': False,
            'errors': [],
            'diagnostics': [],
            'warnings': [],
            'suggestions': []
        }
        
        try:
            self.parse(source_code, filename=filename)
            result['valid'] = True
        except SonaSyntaxError as error:
            item = error.diagnostic
            diagnostic_id = item.diagnostic_id or "SONA-PARSE-001"
            category = "semantic" if diagnostic_id.startswith("SONA-SEM-") else (
                "internal" if diagnostic_id == "SONA-PARSE-099" else "syntax"
            )
            result['errors'].append(f"{diagnostic_id}: {item.message}")
            result['diagnostics'].append({
                "diagnostic_id": diagnostic_id,
                "category": category,
                "severity": "error",
                "file": item.location.file,
                "line": item.location.line,
                "column": item.location.column,
                "end_line": item.location.line,
                "end_column": item.location.column + 1,
                "message": item.message,
                "hint": item.suggestion,
            })
            if item.suggestion:
                result['suggestions'].append(item.suggestion)
        
        return result

    @staticmethod
    def _unsupported_production(parse_tree) -> tuple[str, int, int] | None:
        unsupported = {
            "class_def": "class", "match_stmt": "match", "repeat_stmt": "repeat",
            "destructuring_assignment": "destructuring", "export_stmt": "export",
            "template_string": "template string", "show_stmt": "show",
            "think_stmt": "think", "calculate_stmt": "calculate",
            "when_stmt": "statement-form when",
        }
        for tree in parse_tree.iter_subtrees_topdown():
            name = str(getattr(tree, "data", ""))
            if name in unsupported:
                meta = getattr(tree, "meta", None)
                return unsupported[name], int(getattr(meta, "line", 1) or 1), int(getattr(meta, "column", 1) or 1)
        for token in parse_tree.scan_values(lambda value: isinstance(value, Token)):
            if getattr(token, "type", None) == "TEMPLATE_STRING":
                return "template string", int(getattr(token, "line", 1) or 1), int(getattr(token, "column", 1) or 1)
        return None

    @classmethod
    def _find_raw_parser_object(cls, value, seen: set[int] | None = None) -> str | None:
        """Return the first leaked Lark production name in transformed output."""
        seen = seen or set()
        marker = id(value)
        if marker in seen:
            return None
        seen.add(marker)
        if isinstance(value, Tree):
            return str(getattr(value, "data", "raw parse tree"))
        if isinstance(value, Token):
            return str(getattr(value, "type", "raw token"))
        if is_dataclass(value):
            for item in fields(value):
                found = cls._find_raw_parser_object(getattr(value, item.name), seen)
                if found:
                    return found
        elif isinstance(value, (list, tuple)):
            for item in value:
                found = cls._find_raw_parser_object(item, seen)
                if found:
                    return found
        elif isinstance(value, dict):
            for item in value.values():
                found = cls._find_raw_parser_object(item, seen)
                if found:
                    return found
        return None
    
    def _handle_parse_error(self, error: ParseError, source_code: str, filename: str):
        """Handle parsing errors with enhanced reporting"""
        if os.getenv("SONA_DEBUG_PARSER") != "1":
            return
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
        if os.getenv("SONA_DEBUG_PARSER") != "1":
            return
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
        self.current_filename = "<string>"

    def _with_span(self, node, token=None):
        """Attach the canonical SourceSpan without changing legacy AST constructors."""
        from .developer_intelligence.diagnostics import SourceSpan
        line = int(getattr(token, "line", self.current_line) or 1)
        column = int(getattr(token, "column", 1) or 1)
        end_line = getattr(token, "end_line", line)
        end_column = getattr(token, "end_column", column + len(str(token or "")))
        node.line_number = line
        node.span = SourceSpan(
            file=self.current_filename, start_line=line, start_column=column,
            end_line=end_line, end_column=end_column,
            node_type=type(node).__name__,
        )
        return node

    def _with_rule_span(self, node, meta):
        """Attach the exact Lark rule span to an executable node."""
        from .developer_intelligence.diagnostics import SourceSpan
        line = int(getattr(meta, "line", 1) or 1)
        column = int(getattr(meta, "column", 1) or 1)
        node.line_number = line
        node.span = SourceSpan(
            file=self.current_filename,
            start_line=line,
            start_column=column,
            end_line=int(getattr(meta, "end_line", line) or line),
            end_column=int(getattr(meta, "end_column", column + 1) or (column + 1)),
            node_type=type(node).__name__,
        )
        return node

    def _inherit_span(self, node, source):
        """Copy a source node's span to a normalized replacement node."""
        span = getattr(source, "span", None)
        if span is None:
            return node
        from .developer_intelligence.diagnostics import SourceSpan
        node.line_number = span.start_line
        node.span = SourceSpan(
            file=span.file,
            start_line=span.start_line,
            start_column=span.start_column,
            end_line=span.end_line,
            end_column=span.end_column,
            node_type=type(node).__name__,
        )
        return node
    
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
        return self._normalize_statement_sequence(result)

    def _normalize_statement_sequence(self, statements):
        """Fix ambiguous splits caused by optional separators."""
        from .ast_nodes import (
            BinaryOperatorExpression,
            CallExpression,
            Expression,
            IndexExpression,
            ListExpression,
            MethodCallExpression,
            PositionalArgument,
            PropertyAccessExpression,
            ReturnStatement,
            UnaryOperatorExpression,
            VariableAssignment,
            VariableExpression,
        )

        def _make_call(callee, arg):
            if isinstance(callee, PropertyAccessExpression):
                return self._inherit_span(MethodCallExpression(
                    object=callee.object,
                    method_name=callee.property_name,
                    arguments=[PositionalArgument(arg)],
                    line_number=getattr(callee, "line_number", None),
                ), callee)
            return self._inherit_span(CallExpression(
                callee=callee,
                arguments=[PositionalArgument(arg)],
                line_number=getattr(callee, "line_number", None),
            ), callee)

        normalized = []
        i = 0
        while i < len(statements):
            stmt = statements[i]
            if (
                isinstance(stmt, VariableAssignment)
                and i + 1 < len(statements)
                and isinstance(statements[i + 1], UnaryOperatorExpression)
                and statements[i + 1].operator in ("+", "-")
            ):
                unary = statements[i + 1]
                operand = unary.operand
                skip_extra = 0

                # Handle cases like "+ scores [1]" parsed as two statements.
                if (
                    i + 2 < len(statements)
                    and isinstance(statements[i + 2], ListExpression)
                    and len(statements[i + 2].elements) == 1
                ):
                    operand = IndexExpression(
                        object=operand,
                        index=statements[i + 2].elements[0],
                        line_number=getattr(unary, "line_number", None),
                    )
                    skip_extra = 1

                merged_expr = self._inherit_span(BinaryOperatorExpression(
                    left=stmt.value,
                    operator=unary.operator,
                    right=operand,
                    line_number=getattr(stmt, "line_number", None),
                ), stmt)
                normalized.append(
                    self._inherit_span(VariableAssignment(
                        name=stmt.name,
                        value=merged_expr,
                        is_const=stmt.is_const,
                        is_declaration=stmt.is_declaration,
                        line_number=stmt.line_number,
                    ), stmt)
                )
                i += 2 + skip_extra
                continue

            if (
                isinstance(stmt, VariableAssignment)
                and isinstance(stmt.value, BinaryOperatorExpression)
                and stmt.value.operator in ("+", "-")
                and i + 1 < len(statements)
                and isinstance(statements[i + 1], ListExpression)
                and len(statements[i + 1].elements) == 1
            ):
                list_expr = statements[i + 1]
                indexed = IndexExpression(
                    object=stmt.value.right,
                    index=list_expr.elements[0],
                    line_number=getattr(stmt.value, "line_number", None),
                )
                merged_expr = self._inherit_span(BinaryOperatorExpression(
                    left=stmt.value.left,
                    operator=stmt.value.operator,
                    right=indexed,
                    line_number=getattr(stmt.value, "line_number", None),
                ), stmt.value)
                normalized.append(
                    self._inherit_span(VariableAssignment(
                        name=stmt.name,
                        value=merged_expr,
                        is_const=stmt.is_const,
                        is_declaration=stmt.is_declaration,
                        line_number=stmt.line_number,
                    ), stmt)
                )
                i += 2
                continue

            if (
                isinstance(stmt, ReturnStatement)
                and stmt.expression is None
                and i + 1 < len(statements)
                and isinstance(statements[i + 1], Expression)
            ):
                normalized.append(
                    ReturnStatement(
                        statements[i + 1],
                        line_number=getattr(stmt, "line_number", None),
                    )
                )
                i += 2
                continue

            if (
                isinstance(stmt, Expression)
                and i + 1 < len(statements)
                and isinstance(statements[i + 1], UnaryOperatorExpression)
                and statements[i + 1].operator in ("+", "-")
            ):
                unary = statements[i + 1]
                operand = unary.operand
                skip_extra = 0

                # Handle cases like "x + scores [1]" parsed as two statements.
                if (
                    i + 2 < len(statements)
                    and isinstance(statements[i + 2], ListExpression)
                    and len(statements[i + 2].elements) == 1
                ):
                    operand = IndexExpression(
                        object=operand,
                        index=statements[i + 2].elements[0],
                        line_number=getattr(unary, "line_number", None),
                    )
                    skip_extra = 1

                normalized.append(
                    self._inherit_span(BinaryOperatorExpression(
                        left=stmt,
                        operator=unary.operator,
                        right=operand,
                        line_number=getattr(stmt, "line_number", None),
                    ), stmt)
                )
                i += 2 + skip_extra
                continue

            if (
                isinstance(stmt, VariableAssignment)
                and isinstance(stmt.value, (PropertyAccessExpression, VariableExpression))
                and i + 1 < len(statements)
                and isinstance(statements[i + 1], Expression)
            ):
                call_expr = _make_call(stmt.value, statements[i + 1])
                normalized.append(
                    VariableAssignment(
                        name=stmt.name,
                        value=call_expr,
                        is_const=stmt.is_const,
                        is_declaration=stmt.is_declaration,
                        line_number=stmt.line_number,
                    )
                )
                i += 2
                continue

            if (
                isinstance(stmt, (PropertyAccessExpression, VariableExpression))
                and i + 1 < len(statements)
                and isinstance(statements[i + 1], Expression)
            ):
                normalized.append(_make_call(stmt, statements[i + 1]))
                i += 2
                continue

            normalized.append(stmt)
            i += 1

        return normalized

    def cognitive_stmt(self, items):
        """Flatten cognitive_stmt wrapper."""
        if not items:
            return None
        if len(items) == 1:
            return items[0]
        return items

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
        """Transform a certified conditional statement."""
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
        """Transform catch clause with exception type"""
        return CatchClause(
            exception_type=str(exception_type) if exception_type else "Exception",
            var_name=str(var_name) if var_name else None,
            body=body
        )
    
    @v_args(inline=True)
    def catch_clause_simple(self, var_name, body):
        """Transform simple catch clause (catch-all with variable)"""
        return CatchClause(
            exception_type="Exception",  # Catch-all
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
            args = self._normalize_call_arguments(arguments)
            prompt = str(args[0]) if args else ""
            # Additional parameters: language, level, etc.
            options = args[1:] if len(args) > 1 else []
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
            args = self._normalize_call_arguments(arguments)
            target = args[0] if args else ""
            # Additional parameters: level, audience, etc.
            options = args[1:] if len(args) > 1 else []
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
            args = self._normalize_call_arguments(arguments)
            code = args[0] if args else ""
            options = args[1:] if len(args) > 1 else []
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
            args = self._normalize_call_arguments(arguments)
            code = args[0] if args else ""
            options = args[1:] if len(args) > 1 else []
        else:
            code = arguments
            options = []

        return AIOptimizeStatement(
            code=code,
            options=options,
            line_number=self.current_line
        )

    def _normalize_call_arguments(self, arguments):
        """Normalize parsed call arguments for non-runtime statement nodes."""
        try:
            from .ast_nodes import PositionalArgument, KeywordArgument, SpreadArgument
        except Exception:
            return arguments

        normalized = []
        for arg in arguments:
            if isinstance(arg, PositionalArgument):
                normalized.append(arg.value)
            elif isinstance(arg, KeywordArgument):
                normalized.append((arg.name, arg.value))
            elif isinstance(arg, SpreadArgument):
                normalized.append(arg.value)
            else:
                normalized.append(arg)
        return normalized

    def _arguments_to_mapping(self, arguments) -> dict[str, Any]:
        """Convert parsed arguments into a name->expression mapping for cognitive statements."""
        try:
            from .ast_nodes import PositionalArgument, KeywordArgument, SpreadArgument
        except Exception:
            PositionalArgument = KeywordArgument = SpreadArgument = None  # type: ignore

        if arguments is None:
            return {}
        if isinstance(arguments, list) and len(arguments) == 1 and isinstance(arguments[0], list):
            arguments = arguments[0]
        if isinstance(arguments, list) and all(item is None for item in arguments):
            return {}
        if not isinstance(arguments, list):
            return {"arg0": arguments}

        mapping: dict[str, Any] = {}
        positional_index = 0
        for idx, arg in enumerate(arguments):
            if arg is None:
                continue
            if KeywordArgument and isinstance(arg, KeywordArgument):
                mapping[arg.name] = arg.value
            elif PositionalArgument and isinstance(arg, PositionalArgument):
                mapping[f"arg{positional_index}"] = arg.value
                positional_index += 1
            elif SpreadArgument and isinstance(arg, SpreadArgument):
                mapping[f"spread{idx}"] = arg.value
            else:
                mapping[f"arg{positional_index}"] = arg
                positional_index += 1
        return mapping

    def _build_cognitive_statement(self, cls, arguments):
        """Shared builder for cognitive_* statements."""
        if not self.features_enabled.get('cognitive_programming', True):
            return None
        body = self._arguments_to_mapping(arguments)
        return cls(body=body, line_number=self.current_line)

    def cognitive_check_stmt(self, arguments=None):
        """Transform cognitive_check(...) into AST."""
        return self._build_cognitive_statement(CognitiveCheckStatement, arguments)

    def focus_mode_stmt(self, arguments=None):
        """Transform focus_mode(...) into AST."""
        return self._build_cognitive_statement(FocusModeStatement, arguments)

    def working_memory_stmt(self, arguments=None):
        """Transform working_memory(...) into AST."""
        return self._build_cognitive_statement(WorkingMemoryStatement, arguments)

    def intent_stmt(self, arguments=None):
        """Transform intent(...) into AST."""
        return self._build_cognitive_statement(IntentStatement, arguments)

    def intent_annotation_stmt(self, arguments=None):
        """Transform @intent ... into AST."""
        if not self.features_enabled.get('cognitive_programming', True):
            return None
        body = self._arguments_to_mapping(arguments)
        if "goal" not in body and "intent" not in body and "arg0" in body:
            body["goal"] = body["arg0"]
        body.setdefault("annotation", LiteralExpression(True))
        return IntentStatement(body=body, line_number=self.current_line)

    def decision_stmt(self, arguments=None):
        """Transform decision(...) into AST."""
        return self._build_cognitive_statement(DecisionStatement, arguments)

    def cognitive_trace_stmt(self, arguments=None):
        """Transform cognitive_trace(on/off) into AST."""
        return self._build_cognitive_statement(CognitiveTraceStatement, arguments)

    def explain_step_stmt(self, arguments=None):
        """Transform explain_step(...) into AST."""
        return self._build_cognitive_statement(ExplainStepStatement, arguments)

    def profile_stmt(self, arguments=None):
        """Transform profile(...) into AST."""
        return self._build_cognitive_statement(ProfileStatement, arguments)

    def cognitive_scope_stmt(self, items):
        """Transform cognitive_scope(name) { ... } into AST."""
        args = items[0] if items else None
        body = items[1] if len(items) > 1 else None
        body = body or []
        mapping = self._arguments_to_mapping(args)
        name_expr = mapping.get("name") or mapping.get("arg0")
        return CognitiveScopeStatement(
            name=name_expr,
            meta=mapping,
            body=body,
            line_number=self.current_line,
        )

    def focus_block_stmt(self, items):
        """Transform focus { ... } into AST."""
        args = None
        body = []
        if items:
            if len(items) == 1:
                body = items[0] or []
            else:
                args = items[0]
                body = items[1] or []
        mapping = self._arguments_to_mapping(args)
        return FocusBlockStatement(
            meta=mapping,
            body=body,
            line_number=self.current_line,
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
        if len(items) == 3:
            binding_kind, var_name, value = items
            # Create a variable assignment AST node
            from .ast_nodes import VariableAssignment
            return self._with_span(VariableAssignment(
                name=str(var_name),
                value=value,
                is_const=str(binding_kind) == "const",
                is_declaration=True,
                line_number=self.current_line
            ), var_name)
        return None
    
    def bare_assignment(self, items):
        """Transform bare assignment: x = value"""
        if len(items) == 2:
            var_name, value = items
            from .ast_nodes import VariableAssignment
            return self._with_span(VariableAssignment(
                name=str(var_name),
                value=value,
                is_const=False,
                is_declaration=False,
                line_number=self.current_line
            ), var_name)
        return None

    @v_args(meta=True)
    def power_expr(self, children, meta):
        """Transform right-associative exponentiation."""
        if len(children) < 3 or children[1] is None:
            return children[0]
        from .ast_nodes import BinaryOperatorExpression
        return self._with_rule_span(BinaryOperatorExpression(
            left=children[0], operator=str(children[1]), right=children[2],
            line_number=self.current_line,
        ), meta)
    
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
        import ast as python_ast
        token_text = str(token)
        content = token_text[1:-1]
        index = 0
        simple_escapes = set("\\\"'abfnrtv0")
        while index < len(content):
            if content[index] != "\\":
                index += 1
                continue
            if index + 1 >= len(content):
                valid = False
                width = 1
            else:
                escape = content[index + 1]
                if escape in simple_escapes:
                    valid, width = True, 2
                elif escape in {"x", "u", "U"}:
                    digits = {"x": 2, "u": 4, "U": 8}[escape]
                    payload = content[index + 2:index + 2 + digits]
                    valid = len(payload) == digits and all(char in "0123456789abcdefABCDEF" for char in payload)
                    width = 2 + digits
                else:
                    valid, width = False, 2
            if not valid:
                raise SonaSyntaxError(
                    "Invalid string escape sequence.",
                    code=ErrorCode.INVALID_ESCAPE,
                    location=SourceLocation(
                        file=self.current_filename,
                        line=int(getattr(token, "line", 1) or 1),
                        column=int(getattr(token, "column", 1) or 1) + index + 1,
                    ),
                    suggestion="Use a documented newline, tab, slash, quote, or Unicode escape.",
                    diagnostic_id="SONA-PARSE-001",
                )
            index += width
        try:
            content = python_ast.literal_eval(token_text)
        except (SyntaxError, ValueError) as error:
            raise SonaSyntaxError(
                "Invalid string literal.",
                location=SourceLocation(
                    file=self.current_filename,
                    line=int(getattr(token, "line", 1) or 1),
                    column=int(getattr(token, "column", 1) or 1),
                ),
                suggestion="Close the string and use valid escape sequences.",
                diagnostic_id="SONA-PARSE-001",
            ) from error
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
        return self._normalize_statement_sequence(result)
    
    def print_stmt(self, children):
        """Transform print statement"""
        # children contains the arguments to print
        if children and len(children) > 0:
            # Get the expression (may be nested in lists)
            expr = children[0]
            if isinstance(expr, list) and len(expr) > 0:
                args = self._normalize_call_arguments(expr)
                expr = args[0] if args else None
        else:
            expr = None
        
        from .ast_nodes import PrintStatement
        return PrintStatement(expr, line_number=self.current_line)
    
    def let_assign(self, children):
        """Transform let assignment"""
        name_token = children[0]
        value_expr = children[1]
        from .ast_nodes import VariableAssignment
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
        from .ast_nodes import VariableAssignment
        return VariableAssignment(
            name=str(name_token),
            value=value_expr,
            is_const=True,
            line_number=self.current_line
        )
    
    def variable(self, children):
        """Transform variable reference"""
        name_token = children[0]
        from .ast_nodes import VariableExpression
        return self._with_span(VariableExpression(str(name_token)), name_token)
    
    @v_args(meta=True)
    def postfix_expr(self, children, meta):
        """Transform postfix expressions (calls, indexing, props)"""
        from .ast_nodes import (
            VariableExpression,
            FunctionCallExpression,
            CallExpression,
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
                    if isinstance(base, PropertyAccessExpression):
                        # Method call: obj.method()
                        base = self._with_rule_span(MethodCallExpression(
                            object=base.object,
                            method_name=base.property_name,
                            arguments=args,
                            line_number=self.current_line
                        ), meta)
                    else:
                        base = self._with_rule_span(CallExpression(
                            callee=base,
                            arguments=args,
                            line_number=self.current_line
                        ), meta)
                        
                elif suffix_type == "index":
                    # Array/dict indexing
                    index_expr = suffix_data
                    from .ast_nodes import IndexExpression
                    base = self._with_rule_span(IndexExpression(
                        object=base,
                        index=index_expr,
                        line_number=self.current_line
                    ), meta)
                    
                elif suffix_type == "prop":
                    # Property access
                    prop_name = suffix_data
                    base = self._with_rule_span(PropertyAccessExpression(
                        object=base,
                        property_name=prop_name,
                        line_number=self.current_line
                    ), meta)
        
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

    def prop_name(self, children):
        """Normalize dotted property names (including keyword literals) to strings."""
        if not children:
            return ""
        child = children[0]
        if isinstance(child, Token):
            return str(child.value)
        return str(child)
    
    def arguments(self, children):
        """Transform function call arguments"""
        return children  # Already a list of expressions

    @v_args(meta=True)
    def unary_expr(self, children, meta):
        """Transform unary expression (+x, -x, !x, not x)"""
        if len(children) == 1:
            return children[0]

        op_token = children[0]
        operand = children[1]

        if isinstance(op_token, Token):
            operator = str(op_token.value)
        else:
            operator = str(op_token)

        from .ast_nodes import UnaryOperatorExpression
        return self._with_rule_span(UnaryOperatorExpression(
            operator=operator,
            operand=operand,
            line_number=self.current_line
        ), meta)
    
    @v_args(meta=True)
    def additive_expr(self, children, meta):
        """Transform additive expression (+ or -)"""
        # Grammar: multiplicative_expr (ADDITIVE_OP multiplicative_expr)*
        if len(children) == 1:
            return children[0]
        
        from .ast_nodes import BinaryOperatorExpression
        
        result = children[0]
        i = 1
        while i < len(children):
            op_token = children[i]
            if isinstance(op_token, Token):
                operator = str(op_token.value)
            else:
                operator = str(op_token)
            right = children[i + 1]
            
            result = self._with_rule_span(BinaryOperatorExpression(
                left=result,
                operator=operator,
                right=right,
                line_number=self.current_line
            ), meta)
            i += 2
        
        return result
    
    @v_args(meta=True)
    def multiplicative_expr(self, children, meta):
        """Transform multiplicative expression (* / %)"""
        # Grammar: power_expr (MULTIPLICATIVE_OP power_expr)*
        if len(children) == 1:
            return children[0]
        
        from .ast_nodes import BinaryOperatorExpression
        
        result = children[0]
        i = 1
        while i < len(children):
            op_token = children[i]
            if isinstance(op_token, Token):
                operator = str(op_token.value)
            else:
                operator = str(op_token)
            right = children[i + 1]
            
            result = self._with_rule_span(BinaryOperatorExpression(
                left=result,
                operator=operator,
                right=right,
                line_number=self.current_line
            ), meta)
            i += 2
        
        return result
    
    @v_args(meta=True)
    def comparison_expr(self, children, meta):
        """Transform comparison expression (<= >= < >)"""
        # Grammar: additive_expr (COMPARISON_OP additive_expr)*
        # children = [expr] or [expr, TOKEN, expr, TOKEN, expr, ...]
        if len(children) == 1:
            return children[0]
        
        from .ast_nodes import ChainedComparisonExpression
        operands = [children[0], *children[2::2]]
        operators = [
            str(item.value) if isinstance(item, Token) else str(item)
            for item in children[1::2]
        ]
        return self._with_rule_span(ChainedComparisonExpression(
            operands=operands,
            operators=operators,
            line_number=self.current_line,
        ), meta)
    
    # Note: operator helper functions (comparison_op, equality_op, etc.) 
    # are no longer used since operators are now extracted directly
    # from terminal tokens in the expression transformers above
    
    @v_args(meta=True)
    def or_expr(self, children, meta):
        """Transform or expression (|| or 'or')"""
        # Grammar: and_expr (OR_OP and_expr)*
        if len(children) == 1:
            return children[0]
        
        from .ast_nodes import BinaryOperatorExpression
        
        result = children[0]
        i = 1
        while i < len(children):
            op_token = children[i]
            if isinstance(op_token, Token):
                operator = str(op_token.value)
            else:
                operator = str(op_token)
            # Normalize 'or' to '||' for consistent handling
            if operator == 'or':
                operator = '||'
            right = children[i + 1]
            
            result = self._with_rule_span(BinaryOperatorExpression(
                left=result,
                operator=operator,
                right=right,
                line_number=self.current_line
            ), meta)
            i += 2
        
        return result
    
    @v_args(meta=True)
    def and_expr(self, children, meta):
        """Transform and expression (&& or 'and')"""
        # Grammar: equality_expr (AND_OP equality_expr)*
        if len(children) == 1:
            return children[0]
        
        from .ast_nodes import BinaryOperatorExpression
        
        result = children[0]
        i = 1
        while i < len(children):
            op_token = children[i]
            if isinstance(op_token, Token):
                operator = str(op_token.value)
            else:
                operator = str(op_token)
            # Normalize 'and' to '&&' for consistent handling
            if operator == 'and':
                operator = '&&'
            right = children[i + 1]
            
            result = self._with_rule_span(BinaryOperatorExpression(
                left=result,
                operator=operator,
                right=right,
                line_number=self.current_line
            ), meta)
            i += 2
        
        return result
    
    @v_args(meta=True)
    def equality_expr(self, children, meta):
        """Transform equality expression (== !=)"""
        # Grammar: comparison_expr (EQUALITY_OP comparison_expr)*
        if len(children) == 1:
            return children[0]
        
        from .ast_nodes import BinaryOperatorExpression
        
        result = children[0]
        i = 1
        while i < len(children):
            op_token = children[i]
            if isinstance(op_token, Token):
                operator = str(op_token.value)
            else:
                operator = str(op_token)
            right = children[i + 1]
            
            result = self._with_rule_span(BinaryOperatorExpression(
                left=result,
                operator=operator,
                right=right,
                line_number=self.current_line
            ), meta)
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

    def pos_arg(self, children):
        """Transform positional argument"""
        from .ast_nodes import PositionalArgument
        return PositionalArgument(children[0])

    def kw_arg(self, children):
        """Transform keyword argument"""
        name_token = children[0]
        value_expr = children[1]
        from .ast_nodes import KeywordArgument
        return KeywordArgument(str(name_token), value_expr)

    def spread_arg(self, children):
        """Transform spread argument"""
        from .ast_nodes import SpreadArgument
        return SpreadArgument(children[0])
    
    @v_args(meta=True)
    def func_def(self, children, meta):
        """Transform function definition"""
        name_token = children[0]

        params = []
        body = []
        if len(children) == 2:
            # No params provided; children[1] is the body
            body = children[1] or []
        elif len(children) >= 3:
            # Params (optional) + body
            params = children[1] or []
            body = children[2] or []
        
        # Extract parameter names
        if params and not isinstance(params, list):
            params = [params]

        default_values = {}
        param_names = []
        varargs_param = None
        for param in params:
            if isinstance(param, tuple) and len(param) == 3:
                param_name, default_expr, is_varargs = param
                if is_varargs:
                    if varargs_param is not None:
                        raise ValueError("Only one varargs parameter is allowed")
                    varargs_param = str(param_name)
                else:
                    param_names.append(str(param_name))
                    if default_expr is not None:
                        default_values[str(param_name)] = default_expr
            elif isinstance(param, tuple) and len(param) == 2:
                param_name, default_expr = param
                param_names.append(str(param_name))
                if default_expr is not None:
                    default_values[str(param_name)] = default_expr
            else:
                param_names.append(str(param))
        
        # Ensure body is a list
        if body and not isinstance(body, list):
            body = [body]
        
        from .ast_nodes import FunctionDefinition
        return self._with_rule_span(FunctionDefinition(
            name=str(name_token),
            parameters=param_names,
            default_values=default_values,
            varargs_param=varargs_param,
            body=body,
            line_number=self.current_line
        ), meta)
    
    def param_list(self, children):
        """Transform parameter list"""
        return [str(p) for p in children]
    
    def func_params(self, children):
        """Transform function parameters (v091 grammar)"""
        return children  # List of func_param results (already strings)
    
    def normal_param(self, children):
        """Transform a normal function parameter"""
        param_name = str(children[0])
        default_expr = children[1] if len(children) > 1 else None
        return (param_name, default_expr, False)

    def vararg_param(self, children):
        """Transform a varargs function parameter (e.g., ...rest)"""
        param_name = str(children[0])
        default_expr = children[1] if len(children) > 1 else None
        return (param_name, default_expr, True)
    
    @v_args(meta=True)
    def return_stmt(self, children, meta):
        """Transform return statement"""
        expr = children[0] if children else None
        from .ast_nodes import ReturnStatement
        return self._with_rule_span(ReturnStatement(expr, line_number=self.current_line), meta)
    
    @v_args(meta=True)
    def break_stmt(self, children, meta):
        """Transform break statement"""
        from .ast_nodes import BreakStatement
        return self._with_rule_span(BreakStatement(line_number=self.current_line), meta)
    
    @v_args(meta=True)
    def continue_stmt(self, children, meta):
        """Transform continue statement"""
        from .ast_nodes import ContinueStatement
        return self._with_rule_span(ContinueStatement(line_number=self.current_line), meta)
    
    def num(self, children):
        """Transform number literal"""
        value = float(children[0])
        if value.is_integer():
            value = int(value)
        from .ast_nodes import LiteralExpression
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
        from .ast_nodes import LiteralExpression
        return LiteralExpression(string_value, line_number=self.current_line)
    
    def true(self, children):
        """Transform true literal"""
        from .ast_nodes import LiteralExpression
        return LiteralExpression(True, line_number=self.current_line)
    
    def false(self, children):
        """Transform false literal"""
        from .ast_nodes import LiteralExpression
        return LiteralExpression(False, line_number=self.current_line)
    
    def null(self, children):
        """Transform null literal"""
        from .ast_nodes import LiteralExpression
        return LiteralExpression(None, line_number=self.current_line)
    
    def array(self, children):
        """Transform array literal"""
        elements = children[0] if children else []
        if not isinstance(elements, list):
            elements = [elements] if elements else []
        from .ast_nodes import ListExpression
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
        from .ast_nodes import DictionaryExpression
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
        from .ast_nodes import LiteralExpression
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
    
    @v_args(meta=True)
    def import_stmt(self, children, meta):
        """Transform import statement"""
        module_path = children[0]
        alias = children[1] if len(children) > 1 else None
        from .ast_nodes import ImportStatement
        return self._with_rule_span(ImportStatement(
            module_path=str(module_path),
            alias=str(alias) if alias else None,
            line_number=self.current_line
        ), meta)
    
    def module_path(self, children):
        """Transform module path"""
        return '.'.join(str(child) for child in children)
    
    def import_path(self, children):
        """Transform import path (v091 grammar)"""
        return '.'.join(str(child) for child in children)
    
    @v_args(meta=True)
    def enhanced_for_stmt(self, children, meta):
        """Transform enhanced for loop"""
        iterator_var = str(children[0])  # NAME token
        iterable_expr = children[1]
        body = children[2] if len(children) > 2 else []
        
        # Ensure body is a list
        if body and not isinstance(body, list):
            body = [body]
        
        from .ast_nodes import EnhancedForLoop
        return self._with_rule_span(EnhancedForLoop(
            iterator_var=iterator_var,
            iterable=iterable_expr,
            body=body,
            line_number=self.current_line
        ), meta)
    
    @v_args(meta=True)
    def enhanced_if_stmt(self, children, meta):
        """Transform enhanced if statement"""
        # Grammar: "if" expr "{" statement_list? "}" elif_clause* else_clause?
        # children[0] = condition expression
        # children[1:] = elif/else clauses (if_body is implicitly in grammar)
        
        # First child is the condition - it should already be transformed
        condition = children[0]
        
        # The optional statement_list is still present as an empty list, so its
        # position—not truthiness—distinguishes it from the else body.
        if_body = children[1] if len(children) > 1 and isinstance(children[1], list) else []
        elif_clauses = []
        else_body = None
        
        # Process remaining children
        for i in range(2, len(children)):
            child = children[i]
            # Check if it's a list (statement_list)
            if isinstance(child, list):
                else_body = child
            # Check if it's an ElifClause
            elif hasattr(child, '__class__'):
                if child.__class__.__name__ == 'ElifClause':
                    elif_clauses.append(child)
        
        from .ast_nodes import EnhancedIfStatement
        return self._with_rule_span(EnhancedIfStatement(
            condition=condition,
            if_body=if_body,
            elif_clauses=elif_clauses,
            else_body=else_body,
            line_number=self.current_line
        ), meta)
    
    def elif_clause(self, children):
        """Transform elif clause"""
        condition = children[0]
        body = children[1] if len(children) > 1 else []
        
        # Ensure body is a list
        if body and not isinstance(body, list):
            body = [body]
        
        from .ast_nodes import ElifClause
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
    
    @v_args(meta=True)
    def enhanced_while_stmt(self, children, meta):
        """Transform enhanced while loop"""
        condition = children[0]
        body = children[1] if len(children) > 1 else []
        
        # Ensure body is a list
        if body and not isinstance(body, list):
            body = [body]
        
        from .ast_nodes import EnhancedWhileLoop
        return self._with_rule_span(EnhancedWhileLoop(
            condition=condition,
            body=body,
            line_number=self.current_line
        ), meta)
    
    @v_args(meta=True)
    def enhanced_try_stmt(self, children, meta):
        """Transform enhanced try statement"""
        try_body = children[0] if children else []
        catch_clauses = []
        finally_body = None
        
        # Process remaining children (catch/finally clauses)
        for child in children[1:]:
            if hasattr(child, '__class__'):
                from .ast_nodes import CatchClause
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
        
        from .ast_nodes import EnhancedTryStatement
        return self._with_rule_span(EnhancedTryStatement(
            try_body=try_body,
            catch_clauses=catch_clauses,
            finally_body=finally_body,
            line_number=self.current_line
        ), meta)
    
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
        
        from .ast_nodes import CatchClause
        return CatchClause(
            exception_type=exception_type,
            var_name=var_name,
            body=body
        )

    def exception_type(self, children):
        """Transform exception_type (NAME | STRING) into a plain string"""
        return str(children[0]) if children else ""
    
    def finally_clause(self, children):
        """Transform finally clause"""
        body = children[0] if children else []
        if body and not isinstance(body, list):
            body = [body]
        return body  # Just return the body list

    # ========================================================================
    # MATCH / WHEN (v0.9.9)
    # ========================================================================

    def when_stmt(self, children):
        """Transform when statement"""
        test_expr = children[0] if children else None
        cases = children[1] if len(children) > 1 else []

        if cases and not isinstance(cases, list):
            cases = [cases]

        from .ast_nodes import WhenStatement
        return WhenStatement(
            test_expr=test_expr,
            cases=cases,
            line_number=self.current_line
        )

    def when_cases(self, children):
        return list(children)

    def when_case(self, children):
        condition = children[0] if children else None
        body = children[1] if len(children) > 1 else []
        if body and not isinstance(body, list):
            body = [body]

        from .ast_nodes import WhenCase
        return WhenCase(condition=condition, body=body)

    def match_stmt(self, children):
        """Transform match statement"""
        target = children[0] if children else None

        cases = []
        if len(children) > 1:
            # Arrow-form: match expr { match_cases }
            # Block-form: match expr { match_block_cases default_case? }
            for child in children[1:]:
                if child is None:
                    continue
                if isinstance(child, list):
                    cases.extend(child)
                else:
                    cases.append(child)

        from .ast_nodes import MatchStatement
        return MatchStatement(
            target=target,
            cases=cases,
            line_number=self.current_line
        )

    def match_cases(self, children):
        return list(children)

    def match_case(self, children):
        pattern = children[0] if children else None
        body = children[1] if len(children) > 1 else []
        if body and not isinstance(body, list):
            body = [body]

        from .ast_nodes import MatchCase
        return MatchCase(pattern=pattern, body=body)

    def match_block_cases(self, children):
        return list(children)

    def match_block_case(self, children):
        pattern_expr = children[0] if children else None
        body = children[1] if len(children) > 1 else []
        if body and not isinstance(body, list):
            body = [body]

        from .ast_nodes import MatchCase
        return MatchCase(pattern=pattern_expr, body=body)

    def default_case(self, children):
        body = children[0] if children else []
        if body and not isinstance(body, list):
            body = [body]

        from .ast_nodes import MatchCase, PatternWildcard
        return MatchCase(pattern=PatternWildcard(), body=body)

    def pattern(self, children):
        # pattern: expr | NAME
        if not children:
            from .ast_nodes import PatternWildcard
            return PatternWildcard()

        node = children[0]

        # NAME token comes through as Token; allow '_' wildcard and capture bindings
        if hasattr(node, 'type') and str(getattr(node, 'type', '')) == 'NAME':
            name = str(node)
            from .ast_nodes import PatternWildcard, PatternBinding
            if name == '_':
                return PatternWildcard()
            return PatternBinding(name=name)

        # Otherwise treat as expression
        return node

    @v_args(meta=True)
    def when_expr(self, children, meta):
        cases = children[0] if children else []
        if cases and not isinstance(cases, list):
            cases = [cases]

        from .ast_nodes import WhenExpression
        return self._with_rule_span(WhenExpression(
            cases=cases,
            line_number=self.current_line
        ), meta)

    def when_expr_cases(self, children):
        # Filter out separator tokens like ';'
        cases = []
        for child in children:
            if hasattr(child, 'type') and str(getattr(child, 'type', '')) == 'SEMICOLON':
                continue
            cases.append(child)
        return cases

    def when_expr_case(self, children):
        condition = children[0]
        value = children[1] if len(children) > 1 else None
        from .ast_nodes import WhenExprCase
        return WhenExprCase(condition=condition, value=value)
    
# ========================================================================
# UTILITY FUNCTIONS
# ========================================================================

def create_parser(grammar_file: str | None = None) -> SonaParserv090:
    """Create a new Sona v0.9.0 parser instance"""
    return SonaParserv090(grammar_file)

def parse_file(file_path: str, parser: SonaParserv090 | None = None) -> list[ASTNode]:
    """Parse a Sona file and return AST nodes"""
    if parser is None:
        parser = create_parser()
    
    with open(file_path, encoding='utf-8-sig') as f:
        source_code = f.read()
    return parser.parse(source_code, file_path)

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
        with open(file_path, encoding='utf-8-sig') as f:
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
