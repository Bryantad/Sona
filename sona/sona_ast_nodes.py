"""
Sona Language - Custom AST Node System
=====================================

Defines the complete AST node hierarchy for the Sona programming language,
providing a clean abstraction layer between the parser and interpreter.

This system replaces Python's built-in AST for Sona-specific
language constructs.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class SonaNodeType(Enum):
    """Enumeration of all Sona AST node types"""
    # Literals
    LITERAL = "literal"
    BOOLEAN_LITERAL = "boolean_literal"
    NULL_LITERAL = "null_literal"
    
    # Variables and Declarations
    VARIABLE = "variable"
    LET_DECLARATION = "let_declaration"
    CONST_DECLARATION = "const_declaration"
    ASSIGNMENT = "assignment"
    
    # Expressions
    BINARY_EXPRESSION = "binary_expression"
    UNARY_EXPRESSION = "unary_expression"
    CALL_EXPRESSION = "call_expression"
    MEMBER_EXPRESSION = "member_expression"
    
    # Statements
    EXPRESSION_STATEMENT = "expression_statement"
    BLOCK_STATEMENT = "block_statement"
    RETURN_STATEMENT = "return_statement"
    
    # Control Flow
    IF_STATEMENT = "if_statement"
    WHILE_STATEMENT = "while_statement"
    FOR_STATEMENT = "for_statement"
    BREAK_STATEMENT = "break_statement"
    CONTINUE_STATEMENT = "continue_statement"
    
    # Exception Handling
    TRY_STATEMENT = "try_statement"
    CATCH_CLAUSE = "catch_clause"
    FINALLY_CLAUSE = "finally_clause"
    
    # Functions
    FUNCTION_DECLARATION = "function_declaration"
    PARAMETER = "parameter"
    
    # AI Integration
    AI_COMPLETE_CALL = "ai_complete_call"
    AI_EXPLAIN_CALL = "ai_explain_call"
    AI_DEBUG_CALL = "ai_debug_call"
    AI_OPTIMIZE_CALL = "ai_optimize_call"
    
    # Cognitive Programming
    THINK_STATEMENT = "think_statement"
    FOCUS_MODE_STATEMENT = "focus_mode_statement"
    WORKING_MEMORY_STATEMENT = "working_memory_statement"
    
    # Module System
    IMPORT_STATEMENT = "import_statement"
    EXPORT_STATEMENT = "export_statement"
    
    # Program
    PROGRAM = "program"


class SonaASTNode(ABC):
    """Base class for all Sona AST nodes"""
    
    def __init__(
        self, node_type: SonaNodeType, line: int = 0, column: int = 0
    ):
        self.node_type = node_type
        self.line = line
        self.column = column
        self.parent = None
        self.children = []
    
    @abstractmethod
    def accept(self, visitor):
        """Accept a visitor for the visitor pattern"""
        pass
    
    def add_child(self, child):
        """Add a child node"""
        if child:
            child.parent = self
            self.children.append(child)
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.node_type.value})"


class SonaExpression(SonaASTNode):
    """Base class for all expressions"""
    
    def __init__(
        self, node_type: SonaNodeType, line: int = 0, column: int = 0
    ):
        super().__init__(node_type, line, column)
    
    @abstractmethod
    def evaluate(self, interpreter):
        """Evaluate the expression and return a value"""
        pass


class SonaStatement(SonaASTNode):
    """Base class for all statements"""
    
    def __init__(
        self, node_type: SonaNodeType, line: int = 0, column: int = 0
    ):
        super().__init__(node_type, line, column)
    
    @abstractmethod
    def execute(self, interpreter):
        """Execute the statement"""
        pass


# ==================== LITERAL EXPRESSIONS ====================

class LiteralExpression(SonaExpression):
    """Represents literal values (numbers, strings)"""
    
    def __init__(self, value: Any, line: int = 0, column: int = 0):
        super().__init__(SonaNodeType.LITERAL, line, column)
        self.value = value
    
    def accept(self, visitor):
        return visitor.visit_literal_expression(self)
    
    def evaluate(self, interpreter):
        return self.value


class BooleanLiteral(SonaExpression):
    """Represents Sona boolean literals (true/false)"""
    
    def __init__(self, value: bool, line: int = 0, column: int = 0):
        super().__init__(SonaNodeType.BOOLEAN_LITERAL, line, column)
        self.value = value
    
    def accept(self, visitor):
        return visitor.visit_boolean_literal(self)
    
    def evaluate(self, interpreter):
        return self.value


class NullLiteral(SonaExpression):
    """Represents Sona null literal"""
    
    def __init__(self, line: int = 0, column: int = 0):
        super().__init__(SonaNodeType.NULL_LITERAL, line, column)
    
    def accept(self, visitor):
        return visitor.visit_null_literal(self)
    
    def evaluate(self, interpreter):
        return None


# ==================== VARIABLE EXPRESSIONS ====================

class VariableExpression(SonaExpression):
    """Represents variable access"""
    
    def __init__(self, name: str, line: int = 0, column: int = 0):
        super().__init__(SonaNodeType.VARIABLE, line, column)
        self.name = name
    
    def accept(self, visitor):
        return visitor.visit_variable_expression(self)
    
    def evaluate(self, interpreter):
        return interpreter.memory.get_variable(self.name)


# ==================== BINARY EXPRESSIONS ====================

class BinaryExpression(SonaExpression):
    """Represents binary operations (+, -, *, /, ==, etc.)"""
    
    def __init__(
        self,
        left: SonaExpression,
        operator: str,
        right: SonaExpression,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(SonaNodeType.BINARY_EXPRESSION, line, column)
        self.left = left
        self.operator = operator
        self.right = right
        self.add_child(left)
        self.add_child(right)
    
    def accept(self, visitor):
        return visitor.visit_binary_expression(self)
    
    def evaluate(self, interpreter):
        left_val = self.left.evaluate(interpreter)
        right_val = self.right.evaluate(interpreter)
        
        # Implement Sona operators
        if self.operator == '+':
            return left_val + right_val
        elif self.operator == '-':
            return left_val - right_val
        elif self.operator == '*':
            return left_val * right_val
        elif self.operator == '/':
            return left_val / right_val
        elif self.operator == '%':
            return left_val % right_val
        elif self.operator == '==':
            return left_val == right_val
        elif self.operator == '!=':
            return left_val != right_val
        elif self.operator == '<':
            return left_val < right_val
        elif self.operator == '>':
            return left_val > right_val
        elif self.operator == '<=':
            return left_val <= right_val
        elif self.operator == '>=':
            return left_val >= right_val
        elif self.operator == '&&':
            return left_val and right_val
        elif self.operator == '||':
            return left_val or right_val
        else:
            raise RuntimeError(f"Unknown binary operator: {self.operator}")


# ==================== CALL EXPRESSIONS ====================

class CallExpression(SonaExpression):
    """Represents function calls"""
    
    def __init__(
        self, function: SonaExpression, arguments: list[SonaExpression],
        line: int = 0, column: int = 0
    ):
        super().__init__(SonaNodeType.CALL_EXPRESSION, line, column)
        self.function = function
        self.arguments = arguments
        self.add_child(function)
        for arg in arguments:
            self.add_child(arg)
    
    def accept(self, visitor):
        return visitor.visit_call_expression(self)
    
    def evaluate(self, interpreter):
        func = self.function.evaluate(interpreter)
        args = [arg.evaluate(interpreter) for arg in self.arguments]
        
        if callable(func):
            return func(*args)
        elif hasattr(func, 'call'):
            return func.call(args)
        else:
            raise RuntimeError(f"'{func}' is not callable")


# ==================== VARIABLE DECLARATIONS ====================

class LetDeclaration(SonaStatement):
    """Represents let variable declarations"""
    
    def __init__(
        self, name: str, initializer: SonaExpression | None = None,
        line: int = 0, column: int = 0
    ):
        super().__init__(SonaNodeType.LET_DECLARATION, line, column)
        self.name = name
        self.initializer = initializer
        if initializer:
            self.add_child(initializer)
    
    def accept(self, visitor):
        return visitor.visit_let_declaration(self)
    
    def execute(self, interpreter):
        value = (
            None
            if self.initializer is None
            else self.initializer.evaluate(interpreter)
        )
        interpreter.memory.set_variable(self.name, value)
        return value


class ConstDeclaration(SonaStatement):
    """Represents const variable declarations"""
    
    def __init__(
        self, name: str, initializer: SonaExpression,
        line: int = 0, column: int = 0
    ):
        super().__init__(SonaNodeType.CONST_DECLARATION, line, column)
        self.name = name
        self.initializer = initializer
        self.add_child(initializer)
    
    def accept(self, visitor):
        return visitor.visit_const_declaration(self)
    
    def execute(self, interpreter):
        value = self.initializer.evaluate(interpreter)
        interpreter.memory.set_variable(self.name, value)
        interpreter.constants.add(self.name)  # Mark as constant
        return value


class AssignmentStatement(SonaStatement):
    """Represents variable assignments"""
    
    def __init__(
        self, name: str, value: SonaExpression, line: int = 0, column: int = 0
    ):
        super().__init__(SonaNodeType.ASSIGNMENT, line, column)
        self.name = name
        self.value = value
        self.add_child(value)
    
    def accept(self, visitor):
        return visitor.visit_assignment_statement(self)
    
    def execute(self, interpreter):
        # Check if it's a constant
        if (
            hasattr(interpreter, 'constants')
            and self.name in interpreter.constants
        ):
            raise RuntimeError(f"Cannot reassign constant '{self.name}'")
        
        val = self.value.evaluate(interpreter)
        interpreter.memory.set_variable(self.name, val)
        return val


# ==================== CONTROL FLOW STATEMENTS ====================

class IfStatement(SonaStatement):
    """Represents if/else statements"""
    
    def __init__(
        self,
        condition: SonaExpression,
        then_branch: SonaStatement,
        else_branch: SonaStatement | None = None,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(SonaNodeType.IF_STATEMENT, line, column)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch
        self.add_child(condition)
        self.add_child(then_branch)
        if else_branch:
            self.add_child(else_branch)
    
    def accept(self, visitor):
        return visitor.visit_if_statement(self)
    
    def execute(self, interpreter):
        if self.condition.evaluate(interpreter):
            return self.then_branch.execute(interpreter)
        elif self.else_branch:
            return self.else_branch.execute(interpreter)
        return None


class WhileStatement(SonaStatement):
    """Represents while loops"""
    
    def __init__(
        self, condition: SonaExpression, body: SonaStatement,
        line: int = 0, column: int = 0
    ):
        super().__init__(SonaNodeType.WHILE_STATEMENT, line, column)
        self.condition = condition
        self.body = body
        self.add_child(condition)
        self.add_child(body)
    
    def accept(self, visitor):
        return visitor.visit_while_statement(self)
    
    def execute(self, interpreter):
        result = None
        while self.condition.evaluate(interpreter):
            try:
                result = self.body.execute(interpreter)
            except BreakException:
                break
            except ContinueException:
                continue
        return result


class ForStatement(SonaStatement):
    """Represents for loops"""
    
    def __init__(
        self, variable: str, iterable: SonaExpression, body: SonaStatement,
        line: int = 0, column: int = 0
    ):
        super().__init__(SonaNodeType.FOR_STATEMENT, line, column)
        self.variable = variable
        self.iterable = iterable
        self.body = body
        self.add_child(iterable)
        self.add_child(body)
    
    def accept(self, visitor):
        return visitor.visit_for_statement(self)
    
    def execute(self, interpreter):
        result = None
        iterable_val = self.iterable.evaluate(interpreter)
        
        # Push new scope for loop variable
        interpreter.memory.push_scope("for_loop")
        try:
            for item in iterable_val:
                interpreter.memory.set_variable(self.variable, item)
                try:
                    result = self.body.execute(interpreter)
                except BreakException:
                    break
                except ContinueException:
                    continue
        finally:
            interpreter.memory.pop_scope()
        return result


# ==================== FUNCTION DECLARATIONS ====================

class FunctionDeclaration(SonaStatement):
    """Represents function declarations"""
    
    def __init__(
        self, name: str, parameters: list[str], body: SonaStatement,
        line: int = 0, column: int = 0
    ):
        super().__init__(SonaNodeType.FUNCTION_DECLARATION, line, column)
        self.name = name
        self.parameters = parameters
        self.body = body
        self.add_child(body)
    
    def accept(self, visitor):
        return visitor.visit_function_declaration(self)
    
    def execute(self, interpreter):
        func = SonaFunction(self.name, self.parameters, self.body, interpreter)
        interpreter.memory.set_variable(self.name, func)
        return func


# ==================== AI INTEGRATION STATEMENTS ====================

class AICompleteCall(SonaExpression):
    """Represents ai_complete() calls"""
    
    def __init__(self, prompt: SonaExpression, line: int = 0, column: int = 0):
        super().__init__(SonaNodeType.AI_COMPLETE_CALL, line, column)
        self.prompt = prompt
        self.add_child(prompt)
    
    def accept(self, visitor):
        return visitor.visit_ai_complete_call(self)
    
    def evaluate(self, interpreter):
        prompt_text = self.prompt.evaluate(interpreter)
        return interpreter.ai_complete(prompt_text)


class AIExplainCall(SonaExpression):
    """Represents ai_explain() calls"""
    
    def __init__(self, target: SonaExpression, line: int = 0, column: int = 0):
        super().__init__(SonaNodeType.AI_EXPLAIN_CALL, line, column)
        self.target = target
        self.add_child(target)
    
    def accept(self, visitor):
        return visitor.visit_ai_explain_call(self)
    
    def evaluate(self, interpreter):
        target_val = self.target.evaluate(interpreter)
        return interpreter.ai_explain(target_val)


# ==================== COGNITIVE PROGRAMMING ====================

class ThinkStatement(SonaStatement):
    """Represents think statements"""
    
    def __init__(
        self, thought: SonaExpression, line: int = 0, column: int = 0
    ):
        super().__init__(SonaNodeType.THINK_STATEMENT, line, column)
        self.thought = thought
        self.add_child(thought)
    
    def accept(self, visitor):
        return visitor.visit_think_statement(self)
    
    def execute(self, interpreter):
        thought_text = self.thought.evaluate(interpreter)
        interpreter.think(thought_text)
        return thought_text


# ==================== UTILITY STATEMENTS ====================

class BlockStatement(SonaStatement):
    """Represents a block of statements"""
    
    def __init__(
        self, statements: list[SonaStatement], line: int = 0, column: int = 0
    ):
        super().__init__(SonaNodeType.BLOCK_STATEMENT, line, column)
        self.statements = statements
        for stmt in statements:
            self.add_child(stmt)
    
    def accept(self, visitor):
        return visitor.visit_block_statement(self)
    
    def execute(self, interpreter):
        result = None
        for stmt in self.statements:
            result = stmt.execute(interpreter)
        return result


class ExpressionStatement(SonaStatement):
    """Represents an expression used as a statement"""
    
    def __init__(
        self, expression: SonaExpression, line: int = 0, column: int = 0
    ):
        super().__init__(SonaNodeType.EXPRESSION_STATEMENT, line, column)
        self.expression = expression
        self.add_child(expression)
    
    def accept(self, visitor):
        return visitor.visit_expression_statement(self)
    
    def execute(self, interpreter):
        return self.expression.evaluate(interpreter)


class ReturnStatement(SonaStatement):
    """Represents return statements"""
    
    def __init__(
        self,
        value: SonaExpression | None = None,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(SonaNodeType.RETURN_STATEMENT, line, column)
        self.value = value
        if value:
            self.add_child(value)
    
    def accept(self, visitor):
        return visitor.visit_return_statement(self)
    
    def execute(self, interpreter):
        value = (
            None if self.value is None else self.value.evaluate(interpreter)
        )
        raise ReturnException(value)


# ==================== PROGRAM ROOT ====================

class Program(SonaASTNode):
    """Represents the root of a Sona program"""
    
    def __init__(
        self, statements: list[SonaStatement], line: int = 0, column: int = 0
    ):
        super().__init__(SonaNodeType.PROGRAM, line, column)
        self.statements = statements
        for stmt in statements:
            self.add_child(stmt)
    
    def accept(self, visitor):
        return visitor.visit_program(self)
    
    def execute(self, interpreter):
        result = None
        for stmt in self.statements:
            result = stmt.execute(interpreter)
        return result


# ==================== EXCEPTIONS ====================

class SonaFunction:
    """Represents a Sona function"""
    
    def __init__(
        self,
        name: str,
        parameters: list[str],
        body: SonaStatement,
        interpreter,
    ):
        self.name = name
        self.parameters = parameters
        self.body = body
        self.interpreter = interpreter
    
    def call(self, arguments: list[Any]) -> Any:
        """Call the function with given arguments"""
        if len(arguments) != len(self.parameters):
            raise RuntimeError(
                "Function '"
                (
                    f"{self.name}' expects {len(self.parameters)} arguments, "
                    f"got {len(arguments)}"
                )
            )
        
        # Push new scope for function execution
        self.interpreter.memory.push_scope(f"function:{self.name}")
        
        try:
            # Set parameters as local variables
            for param, arg in zip(self.parameters, arguments, strict=False):
                self.interpreter.memory.set_variable(param, arg)
            
            # Execute function body
            result = self.body.execute(self.interpreter)
            return result
        except ReturnException as ret:
            return ret.value
        finally:
            # Always pop the function scope
            self.interpreter.memory.pop_scope()


class ReturnException(Exception):
    """Exception used for return statements"""
    def __init__(self, value):
        self.value = value


class BreakException(Exception):
    """Exception used for break statements"""
    pass


class ContinueException(Exception):
    """Exception used for continue statements"""
    pass


# ==================== EXPORTS ====================

__all__ = [
    'SonaNodeType', 'SonaASTNode', 'SonaExpression', 'SonaStatement',
    'LiteralExpression', 'BooleanLiteral', 'NullLiteral', 'VariableExpression',
    'BinaryExpression', 'CallExpression', 'LetDeclaration', 'ConstDeclaration',
    'AssignmentStatement', 'IfStatement', 'WhileStatement', 'ForStatement',
    'FunctionDeclaration', 'AICompleteCall', 'AIExplainCall', 'ThinkStatement',
    'BlockStatement', 'ExpressionStatement', 'ReturnStatement', 'Program',
    'SonaFunction', 'ReturnException', 'BreakException', 'ContinueException'
]
