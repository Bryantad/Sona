"""
String Interpolation Implementation for Sona
Phase 1, Month 1 - Week 1-2 Implementation

Implements f-string style string interpolation:
f"Hello {name}, you are {age} years old!"
"""

import ast
import re
from typing import Any, List, Union

from lark import Token, Tree


class StringInterpolationError(Exception): """Raised when string interpolation fails"""

    pass


class InterpolatedStringPart: """Represents a part of an interpolated string"""

    pass


class LiteralPart(InterpolatedStringPart): """Literal text part of interpolated string"""

    def __init__(self, text: str): self.text = text

    def __repr__(self): return f"Literal({repr(self.text)})"


class ExpressionPart(InterpolatedStringPart): """Expression part of interpolated string"""

    def __init__(self, expression: str, format_spec: str = (
        None): self.expression = expression
    )
        self.format_spec = format_spec

    def __repr__(self): if self.format_spec: return f"Expression({self.expression}:{self.format_spec})"
        return f"Expression({self.expression})"


class StringInterpolationParser: """Parse f-strings into literal and expression parts"""

    # Regex to match {expression} or {expression:format_spec}
    INTERPOLATION_PATTERN = re.compile(
        r'\{([^{}:]+)(?::([^{}]*))?\}', re.MULTILINE | re.DOTALL
    )

    def __init__(self): self.parse_errors = []

    def parse_f_string(
        self, f_string_content: str
    ) -> List[InterpolatedStringPart]: """
        Parse f-string content into parts

        Args: f_string_content: Content of f-string without f" prefix/suffix

        Returns: List of InterpolatedStringPart objects
        """
        self.parse_errors.clear()
        parts = []
        last_end = 0

        for match in self.INTERPOLATION_PATTERN.finditer(f_string_content): start, end = (
            match.span()
        )

            # Add literal text before this expression
            if start > last_end: literal_text = (
                f_string_content[last_end:start]
            )
                if literal_text: parts.append(LiteralPart(literal_text))

            # Parse the expression part
            expression = match.group(1).strip()
            format_spec = match.group(2)

            if not expression: self.parse_errors.append(
                    f"Empty expression at position {start}"
                )
                continue

            # Validate expression syntax
            if not self._is_valid_expression(expression): self.parse_errors.append(
                    f"Invalid expression '{expression}' at position {start}"
                )
                continue

            parts.append(ExpressionPart(expression, format_spec))
            last_end = end

        # Add remaining literal text
        if last_end < len(f_string_content): remaining_text = (
            f_string_content[last_end:]
        )
            if remaining_text: parts.append(LiteralPart(remaining_text))

        return parts

    def _is_valid_expression(self, expression: str) -> bool: """
        Validate that expression is syntactically correct
        Uses Python's AST parser for validation
        """
        try: # Try to parse as Python expression
            ast.parse(expression, mode = 'eval')
            return True
        except SyntaxError: return False

    def get_parse_errors(self) -> List[str]: """Get any parsing errors that occurred"""
        return self.parse_errors.copy()


class StringInterpolationEvaluator: """Evaluate interpolated strings in Sona context"""

    def __init__(self, interpreter): self.interpreter = interpreter
        self.parser = StringInterpolationParser()

    def evaluate_f_string(self, f_string_content: str) -> str: """
        Evaluate f-string and return final string

        Args: f_string_content: Content without f" prefix/suffix
              Returns: Evaluated string with expressions substituted
        """
        parts = self.parser.parse_f_string(f_string_content)

        if self.parser.get_parse_errors(): errors = (
            "; ".join(self.parser.get_parse_errors())
        )
            raise StringInterpolationError(
                f"F-string parsing errors: {errors}"
            )

        result_parts = []

        for part in parts: if isinstance(part, LiteralPart): result_parts.append(part.text)
            elif isinstance(part, ExpressionPart): try: # Evaluate expression in current context
                    value = self._evaluate_expression(part.expression)
                    formatted_value = self._format_value(
                        value, part.format_spec
                    )
                    result_parts.append(formatted_value)
                except Exception as e: raise StringInterpolationError(
                        f"Error evaluating expression "
                        f"'{part.expression}': {str(e)}"
                    )

        return "".join(result_parts)

    def _evaluate_expression(self, expression: str) -> Any: """
        Evaluate expression in current Sona interpreter context
        """
        # Parse expression using Sona's parser
        # Get the grammar from the main interpreter
        # For now, use a simple approach - we'll enhance this

        # Try to evaluate as a simple variable first
        if self._is_simple_variable(expression): return self._get_variable_value(expression)

        # For complex expressions, we need to parse and evaluate
        # This is a simplified implementation
        try: # Use Python's eval for now (will be replaced with Sona evaluation)
            # In production, this would use the Sona interpreter's evaluation
            return eval(expression, {}, self._get_current_scope())
        except Exception as e: raise StringInterpolationError(f"Cannot evaluate expression: {e}")

    def _is_simple_variable(self, expression: str) -> bool: """Check if expression is just a simple variable name"""
        return expression.isidentifier() and not any(
            char in expression for char in '()[]{}., +-*/'
        )

    def _get_variable_value(self, var_name: str) -> Any: """Get variable value from interpreter environment"""
        # Search through environment stack
        for env in reversed(self.interpreter.env): if var_name in env: return env[var_name]

        # Check modules
        if var_name in self.interpreter.modules: return self.interpreter.modules[var_name]

        raise StringInterpolationError(f"Variable '{var_name}' not found")

    def _get_current_scope(self) -> dict: """Get current scope as a dictionary for evaluation"""
        scope = {}
        for env in self.interpreter.env: scope.update(env)
        scope.update(self.interpreter.modules)
        return scope

    def _format_value(self, value: Any, format_spec: str = None) -> str: """
        Format value according to format specification
        Implements basic formatting similar to Python's format()
        """
        if format_spec is None: return str(value)

        try: # Handle basic format specifications
            if isinstance(value, (int, float)): return self._format_number(value, format_spec)
            else: # For non-numeric values, just convert to string
                return str(value)
        except Exception: # If formatting fails, return string representation
            return str(value)

    def _format_number(
        self, value: Union[int, float], format_spec: str
    ) -> str: """Format numeric values according to format specification"""
        try: # Basic numeric formatting
            if '.' in format_spec: # Decimal precision: .2f, .3f, etc.
                if format_spec.endswith('f'): precision = (
                    int(format_spec[1:-1])
                )
                    return f"{value:.{precision}f}"

            # More format specifications can be added here
            return str(value)
        except Exception: return str(value)


def create_f_string_node(content: str) -> Tree: """Create a Tree node for f-string that can be processed by interpreter"""
    return Tree('f_string', [Token('STRING', content)])


class StringInterpolationIntegration: """Integration layer for adding string interpolation to Sona interpreter"""

    @staticmethod
    def add_to_interpreter(interpreter_class): """
        Add string interpolation methods to interpreter class
        This is called during interpreter initialization"""

        def handle_f_string(self, node): """Handle f-string evaluation in the interpreter"""
            if not hasattr(self, 'string_interpolator'): self.string_interpolator = (
                StringInterpolationEvaluator(self)
            )
            # Extract f-string content
            if len(node.children) = (
                = 1 and isinstance(node.children[0], Token): content = node.children[0].value
            )
                # Remove quotes if present
                f_prefixes = ('f"', "f'")
                quote_suffixes = ('"', "'")
                if content.startswith(f_prefixes) and content.endswith(
                    quote_suffixes
                ): content = content[2:-1]
                elif content.startswith(('f"""', "f'''")): content = (
                    content[4:-3]
                )

                return self.string_interpolator.evaluate_f_string(content)

            return ""

        # Add method to interpreter class
        interpreter_class.f_string = handle_f_string

        return interpreter_class


# Example usage and testing
def test_string_interpolation(): """Test string interpolation functionality"""

    class MockInterpreter: def __init__(self): self.env = (
        [{"name": "Alice", "age": 30, "score": 85.7}]
    )
            self.modules = {}

    interpreter = MockInterpreter()
    evaluator = StringInterpolationEvaluator(interpreter)

    test_cases = [
        ("Hello {name}!", "Hello Alice!"),
        ("Name: {name}, Age: {age}", "Name: Alice, Age: 30"),
        ("Score: {score:.1f}", "Score: 85.7"),
        ("Simple test", "Simple test"),
        ("{name} is {age} years old", "Alice is 30 years old"),
    ]

    print("Testing String Interpolation:")
    for f_string, expected in test_cases: try: result = (
        evaluator.evaluate_f_string(f_string)
    )
            status = "✅" if result == expected else "❌"
            print(f"{status} f\"{f_string}\" -> \"{result}\"")
            if result != expected: print(f"   Expected: \"{expected}\"")
        except Exception as e: print(f"❌ f\"{f_string}\" -> Error: {e}")


if __name__ == "__main__": test_string_interpolation()
