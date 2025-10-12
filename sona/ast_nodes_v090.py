"""
Sona v0.9.0 - Enhanced AST Nodes for Control Flow
================================================

This module defines the Abstract Syntax Tree (AST) nodes for Sona v0.9.0's
enhanced control flow features including:

1. Enhanced if/else/elif statements
2. Enhanced for/while loops with break/continue
3. Try/catch/finally exception handling
4. Module system imports/exports
5. AI integration statements
6. Cognitive programming constructs

Author: Sona Development Team
Version: 0.9.0
Date: August 2025
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# ========================================================================
# BASE AST NODE CLASSES
# ========================================================================

class ASTNode(ABC):
    """Base class for all AST nodes"""
    
    @abstractmethod
    def accept(self, visitor):
        """Accept a visitor for traversal"""
        pass
    
    @abstractmethod
    def execute(self, vm):
        """Execute this node in the given VM context"""
        pass

class Statement(ASTNode):
    """Base class for all statement nodes"""
    pass

class Expression(ASTNode):
    """Base class for all expression nodes"""
    
    @abstractmethod
    def evaluate(self, scope: dict[str, Any]) -> Any:
        """Evaluate this expression in the given scope"""
        pass

# ========================================================================
# ENHANCED CONTROL FLOW AST NODES
# ========================================================================

@dataclass
class EnhancedIfStatement(Statement):
    """Enhanced if/else/elif statement with complete support"""
    condition: Expression
    if_body: list[Statement]
    elif_clauses: list['ElifClause']
    else_body: list[Statement] | None = None
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_enhanced_if_statement(self)
    
    def execute(self, vm):
        """Execute enhanced if statement using the control flow engine"""
        if hasattr(vm, 'control_flow_integration'):
            return vm.control_flow_integration.execute_enhanced_if(self)
        else:
            # Fallback to basic execution
            return self._basic_execute(vm)
    
    def _basic_execute(self, vm):
        """Basic execution without enhanced features"""
        if self.condition.evaluate(vm):
            return vm.execute_statements(self.if_body)
        
        for elif_clause in self.elif_clauses:
            if elif_clause.condition.evaluate(vm):
                return vm.execute_statements(elif_clause.body)
        
        if self.else_body:
            return vm.execute_statements(self.else_body)
        
        return None

@dataclass
class ElifClause(ASTNode):
    """Elif clause for enhanced if statements"""
    condition: Expression
    body: list[Statement]
    
    def accept(self, visitor):
        return visitor.visit_elif_clause(self)
    
    def execute(self, vm):
        """Elif clauses are executed as part of if statements"""
        return vm.execute_statements(self.body)

@dataclass
@dataclass
class EnhancedForLoop(Statement):
    """Enhanced for loop with break/continue support"""
    iterator_var: str = ""
    iterable: Expression = None
    body: list[Statement] = None
    line_number: int | None = None
    
    def __post_init__(self):
        if self.body is None:
            self.body = []
    
    def accept(self, visitor):
        return visitor.visit_enhanced_for_loop(self)
    
    def execute(self, interpreter):
        """Execute enhanced for loop"""
        from .interpreter import BreakException, ContinueException
        
        # Evaluate the iterable expression
        iterable_value = self.iterable.evaluate(interpreter)
        
        # Push new scope for loop
        interpreter.memory.push_scope(f"for_loop")
        
        try:
            result = None
            for item in iterable_value:
                # Set iterator variable
                interpreter.memory.set_variable(self.iterator_var, item)
                
                # Execute loop body
                try:
                    result = interpreter.execute_block(self.body)
                except BreakException:
                    break
                except ContinueException:
                    continue
            
            return result
        finally:
            interpreter.memory.pop_scope()

@dataclass
class EnhancedWhileLoop(Statement):
    """Enhanced while loop with break/continue support"""
    condition: Expression
    body: list[Statement]
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_enhanced_while_loop(self)
    
    def execute(self, vm):
        """Execute enhanced while loop using the control flow engine"""
        if hasattr(vm, 'control_flow_integration'):
            return vm.control_flow_integration.execute_enhanced_while(self)
        else:
            return self._basic_execute(vm)
    
    def _basic_execute(self, vm):
        """Basic execution without enhanced features"""
        from .interpreter import BreakException, ContinueException
        
        result = None
        while self.condition.evaluate(vm):
            try:
                result = vm.execute_statements(self.body)
            except BreakException:
                break
            except ContinueException:
                continue
        return result



@dataclass
class EnhancedTryStatement(Statement):
    """Enhanced try/catch/finally with exception type matching"""
    try_body: list[Statement] = None
    catch_clauses: list['CatchClause'] = None
    finally_body: list[Statement] | None = None
    line_number: int | None = None
    
    def __post_init__(self):
        if self.try_body is None:
            self.try_body = []
        if self.catch_clauses is None:
            self.catch_clauses = []
    
    def accept(self, visitor):
        return visitor.visit_enhanced_try_statement(self)
    
    def execute(self, interpreter):
        """Execute enhanced try statement"""
        result = None
        exception_caught = False
        
        try:
            # Execute try block
            result = interpreter.execute_block(self.try_body)
        except Exception as e:
            # Try to match exception with catch clauses
            for catch_clause in self.catch_clauses:
                if catch_clause.matches_exception(e):
                    # Push scope for catch block
                    interpreter.memory.push_scope("catch_block")
                    try:
                        if catch_clause.var_name:
                            interpreter.memory.set_variable(
                                catch_clause.var_name, 
                                e
                            )
                        result = interpreter.execute_block(catch_clause.body)
                        exception_caught = True
                    finally:
                        interpreter.memory.pop_scope()
                    break
            
            # Re-raise if not caught
            if not exception_caught:
                raise
        finally:
            # Execute finally block if present
            if self.finally_body:
                interpreter.execute_block(self.finally_body)
        
        return result


@dataclass
class CatchClause(ASTNode):
    """Catch clause for enhanced try statements"""
    exception_type: str = ""
    var_name: str | None = None
    body: list[Statement] = None
    
    def __post_init__(self):
        if self.body is None:
            self.body = []
    
    def accept(self, visitor):
        return visitor.visit_catch_clause(self)
    
    def matches_exception(self, exception: Exception) -> bool:
        """Check if this catch clause matches the given exception"""
        # For now, match all exceptions
        # TODO: Implement proper exception type matching
        return True
    
    def execute(self, vm):
        """Catch clauses are executed as part of try statements"""
        return vm.execute_statements(self.body)
    
    def matches_exception(self, exception) -> bool:
        """Check if this catch clause handles the given exception"""
        if self.exception_type == "Exception":
            return True
        return type(exception).__name__ == self.exception_type

@dataclass
class BreakStatement(Statement):
    """Break statement for loop control"""
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_break_statement(self)
    
    def execute(self, vm):
        """Execute break statement"""
        from .interpreter import BreakException
        raise BreakException()


@dataclass
class ContinueStatement(Statement):
    """Continue statement for loop control"""
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_continue_statement(self)
    
    def execute(self, vm):
        """Execute continue statement"""
        from .interpreter import ContinueException
        raise ContinueException()
        if hasattr(vm, 'control_flow_integration'):
            return vm.control_flow_integration.execute_continue()
        else:
            raise RuntimeError("'continue' not properly in loop")

# ========================================================================
# MODULE SYSTEM AST NODES
# ========================================================================

@dataclass
class ImportStatement(Statement):
    """Import statement for module system"""
    module_path: str
    alias: str | None = None
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_import_statement(self)
    
    def execute(self, vm):
        """Execute import statement"""
        if hasattr(vm, 'module_system'):
            return vm.module_system.import_module(self.module_path, self.alias)
        else:
            raise RuntimeError(f"Module system not available: cannot import {self.module_path}")

@dataclass
class ImportFromStatement(Statement):
    """Import from statement for selective imports"""
    module_path: str
    import_list: list[str]
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_import_from_statement(self)
    
    def execute(self, vm):
        """Execute import from statement"""
        if hasattr(vm, 'module_system'):
            return vm.module_system.import_from_module(self.module_path, self.import_list)
        else:
            raise RuntimeError(f"Module system not available: cannot import from {self.module_path}")

@dataclass
class ExportStatement(Statement):
    """Export statement for module system"""
    exported_item: Statement  # Function, class, or variable
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_export_statement(self)
    
    def execute(self, vm):
        """Execute export statement"""
        # First execute the item being exported
        result = self.exported_item.execute(vm)
        
        # Then register it for export
        if hasattr(vm, 'module_system'):
            vm.module_system.register_export(self.exported_item, result)
        
        return result

# ========================================================================
# VARIABLE ASSIGNMENT NODES
# ========================================================================

@dataclass
class VariableAssignment(Statement):
    """Variable assignment statement (let/const)"""
    name: str
    value: Any  # Expression that evaluates to the value
    is_const: bool = False  # True for const, False for let
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_variable_assignment(self)
    
    def execute(self, vm):
        """Execute variable assignment"""
        # Evaluate the value expression
        if hasattr(self.value, 'execute'):
            evaluated_value = self.value.execute(vm)
        else:
            evaluated_value = self.value
            
        # Store in memory
        vm.memory.set_variable(self.name, evaluated_value)
        
        return evaluated_value

# ========================================================================
# AI INTEGRATION AST NODES
# ========================================================================

@dataclass
class AICompleteStatement(Statement):
    """AI code completion statement with multi-parameter support"""
    prompt: str
    options: list[Any] = None  # Additional parameters: language, level, etc.
    line_number: int | None = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = []
    
    def accept(self, visitor):
        return visitor.visit_ai_complete_statement(self)
    
    def execute(self, vm):
        """Execute AI completion with options"""
        # Extract the prompt text
        if isinstance(self.prompt, str):
            prompt_text = self.prompt
        elif hasattr(self.prompt, 'execute'):
            prompt_text = self.prompt.execute(vm)
        else:
            prompt_text = str(self.prompt)
            
        # Clean up the prompt text (remove brackets if present)
        prompt_text = str(prompt_text).strip('[]"\'')
        
        # Call the builtin AI function directly
        if hasattr(vm, '_builtin_ai_complete'):
            return vm._builtin_ai_complete(prompt_text)
        else:
            return f"Code completion for: {prompt_text}"

@dataclass
class AIExplainStatement(Statement):
    """AI code explanation statement with multi-parameter support"""
    target: Expression
    options: list[Any] = None  # Additional parameters: level, audience, etc.
    line_number: int | None = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = []
    
    def accept(self, visitor):
        return visitor.visit_ai_explain_statement(self)
    
    def execute(self, vm):
        """Execute AI explanation with options"""
        if hasattr(vm, 'ai_assistant'):
            return vm.ai_assistant.explain_code(self.target, self.options)
        else:
            return f"Code explanation for: {self.target}"

@dataclass
class AIDebugStatement(Statement):
    """AI debugging assistance statement with multi-parameter support"""
    code: str = ""
    options: list[Any] = None  # Additional parameters for debugging context
    line_number: int | None = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = []
    
    def accept(self, visitor):
        return visitor.visit_ai_debug_statement(self)
    
    def execute(self, vm):
        """Execute AI debugging with options"""
        if hasattr(vm, 'ai_assistant'):
            return vm.ai_assistant.debug_assistance(self.code, self.options)
        else:
            return f"Debug analysis for: {self.code}"

@dataclass
class AIOptimizeStatement(Statement):
    """AI code optimization statement with multi-parameter support"""
    code: str
    options: list[Any] = None  # Additional parameters for optimization context
    line_number: int | None = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = []
    
    def accept(self, visitor):
        return visitor.visit_ai_optimize_statement(self)
    
    def execute(self, vm):
        """Execute AI optimization with options"""
        if hasattr(vm, 'ai_assistant'):
            return vm.ai_assistant.optimize_code(self.code, self.options)
        else:
            return "Code appears optimized. Consider profiling for performance bottlenecks."

# ========================================================================
# COGNITIVE PROGRAMMING AST NODES
# ========================================================================

@dataclass
class CognitiveCheckStatement(Statement):
    """Cognitive load check statement"""
    body: dict[str, Expression]
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_cognitive_check_statement(self)
    
    def execute(self, vm):
        """Execute cognitive check"""
        if hasattr(vm, 'cognitive_monitor'):
            # Evaluate all body expressions
            evaluated_body = {}
            for key, expr in self.body.items():
                evaluated_body[key] = expr.evaluate(vm.current_scope)
            
            return vm.cognitive_monitor.check_cognitive_load(evaluated_body)
        else:
            # Basic execution without cognitive monitoring
            for key, expr in self.body.items():
                vm.current_scope[key] = expr.evaluate(vm.current_scope)
            return None

@dataclass
class FocusModeStatement(Statement):
    """Focus mode configuration statement"""
    body: dict[str, Expression]
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_focus_mode_statement(self)
    
    def execute(self, vm):
        """Execute focus mode configuration"""
        if hasattr(vm, 'cognitive_monitor'):
            # Evaluate all body expressions
            evaluated_body = {}
            for key, expr in self.body.items():
                evaluated_body[key] = expr.evaluate(vm.current_scope)
            
            return vm.cognitive_monitor.configure_focus_mode(evaluated_body)
        else:
            # Basic execution without cognitive features
            for key, expr in self.body.items():
                vm.current_scope[key] = expr.evaluate(vm.current_scope)
            return None

@dataclass
class WorkingMemoryStatement(Statement):
    """Working memory management statement"""
    body: dict[str, Expression]
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_working_memory_statement(self)
    
    def execute(self, vm):
        """Execute working memory management"""
        if hasattr(vm, 'cognitive_monitor'):
            # Evaluate all body expressions
            evaluated_body = {}
            for key, expr in self.body.items():
                evaluated_body[key] = expr.evaluate(vm.current_scope)
            
            return vm.cognitive_monitor.manage_working_memory(evaluated_body)
        else:
            # Basic execution without cognitive features
            for key, expr in self.body.items():
                vm.current_scope[key] = expr.evaluate(vm.current_scope)
            return None

# ========================================================================
# ENHANCED EXPRESSION NODES
# ========================================================================

@dataclass
class VariableExpression(Expression):
    """Variable reference expression"""
    name: str
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_variable_expression(self)
    
    def execute(self, interpreter):
        return self.evaluate(interpreter)
    
    def evaluate(self, interpreter) -> Any:
        """Get variable value from interpreter"""
        if hasattr(interpreter, 'memory'):
            # It's a SonaInterpreter
            return interpreter.memory.get_variable(self.name)
        elif isinstance(interpreter, dict):
            # It's a scope dict (backward compatibility)
            if self.name in interpreter:
                return interpreter[self.name]
            raise NameError(f"Variable '{self.name}' is not defined")
        else:
            raise TypeError(f"Cannot evaluate variable in {type(interpreter)}")

@dataclass
class LiteralExpression(Expression):
    """Literal value expression"""
    value: Any
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_literal_expression(self)
    
    def execute(self, interpreter):
        return self.value
    
    def evaluate(self, interpreter) -> Any:
        return self.value

@dataclass
class BinaryOperatorExpression(Expression):
    """Binary operator expression"""
    left: Expression
    operator: str
    right: Expression
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_binary_operator_expression(self)
    
    def execute(self, interpreter):
        return self.evaluate(interpreter)
    
    def evaluate(self, interpreter) -> Any:
        left_val = self.left.evaluate(interpreter)
        right_val = self.right.evaluate(interpreter)
        
        if self.operator == "+":
            # Auto-convert to string if either operand is a string
            if isinstance(left_val, str) or isinstance(right_val, str):
                return str(left_val) + str(right_val)
            return left_val + right_val
        elif self.operator == "-":
            return left_val - right_val
        elif self.operator == "*":
            return left_val * right_val
        elif self.operator == "/":
            return left_val / right_val
        elif self.operator == "%":
            return left_val % right_val
        elif self.operator == "**":
            return left_val ** right_val
        elif self.operator == "==":
            return left_val == right_val
        elif self.operator == "!=":
            return left_val != right_val
        elif self.operator == "<":
            return left_val < right_val
        elif self.operator == ">":
            return left_val > right_val
        elif self.operator == "<=":
            return left_val <= right_val
        elif self.operator == ">=":
            return left_val >= right_val
        elif self.operator == "&&":
            return left_val and right_val
        elif self.operator == "||":
            return left_val or right_val
        else:
            print(f"ERROR: Unknown operator: '{self.operator}' (type={type(self.operator)}, repr={repr(self.operator)})")
            raise RuntimeError(f"Unknown binary operator: {self.operator}")

@dataclass
class UnaryOperatorExpression(Expression):
    """Unary operator expression"""
    operator: str
    operand: Expression
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_unary_operator_expression(self)
    
    def execute(self, vm):
        return self.evaluate(vm.current_scope)
    
    def evaluate(self, scope: dict[str, Any]) -> Any:
        operand_val = self.operand.evaluate(scope)
        
        if self.operator == "+":
            return +operand_val
        elif self.operator == "-":
            return -operand_val
        elif self.operator == "!":
            return not operand_val
        else:
            raise RuntimeError(f"Unknown unary operator: {self.operator}")

@dataclass
@dataclass
class FunctionCallExpression(Expression):
    """Function call expression"""
    name: str = ""
    arguments: list[Expression] = None
    line_number: int | None = None
    
    def __post_init__(self):
        if self.arguments is None:
            self.arguments = []
    
    def accept(self, visitor):
        return visitor.visit_function_call_expression(self)
    
    def execute(self, interpreter):
        return self.evaluate(interpreter)
    
    def evaluate(self, interpreter) -> Any:
        """Evaluate the function call"""
        # Evaluate all arguments
        arg_values = [arg.evaluate(interpreter) for arg in self.arguments]
        
        # Check if it's a built-in function
        try:
            func = interpreter.memory.get_variable(self.name)
            if callable(func):
                return func(*arg_values)
        except NameError:
            pass
        
        # Check if it's a user-defined function
        if self.name in interpreter.functions:
            return interpreter.call_function(self.name, arg_values)
        
        raise NameError(f"Function '{self.name}' is not defined")


@dataclass
class PropertyAccessExpression(Expression):
    """Property access expression (e.g., obj.prop)"""
    object: Expression = None
    property_name: str = ""
    line_number: int | None = None
    
    def execute(self, interpreter):
        """Execute property access"""
        return self.evaluate(interpreter)
    
    def evaluate(self, interpreter):
        """Evaluate property access"""
        obj = self.object.evaluate(interpreter)
        
        # Handle module property access
        if hasattr(obj, self.property_name):
            attr = getattr(obj, self.property_name)
            return attr
        
        # Handle dictionary-style access
        if isinstance(obj, dict) and self.property_name in obj:
            return obj[self.property_name]
        
        raise AttributeError(
            f"Object has no property '{self.property_name}'"
        )
    
    def accept(self, visitor):
        return visitor.visit_property_access_expression(self)


@dataclass
class MethodCallExpression(Expression):
    """Method call expression (e.g., obj.method(args))"""
    object: Expression = None
    method_name: str = ""
    arguments: list[Expression] = None
    line_number: int | None = None
    
    def __post_init__(self):
        if self.arguments is None:
            self.arguments = []
    
    def execute(self, interpreter):
        """Execute method call"""
        return self.evaluate(interpreter)
    
    def evaluate(self, interpreter):
        """Evaluate method call"""
        obj = self.object.evaluate(interpreter)
        
        # Evaluate arguments
        arg_values = [arg.evaluate(interpreter) for arg in self.arguments]
        
        # Get the method from the object
        if hasattr(obj, self.method_name):
            method = getattr(obj, self.method_name)
            if callable(method):
                return method(*arg_values)
            else:
                raise TypeError(
                    f"'{self.method_name}' is not a callable method"
                )
        
        raise AttributeError(
            f"Object has no method '{self.method_name}'"
        )
    
    def accept(self, visitor):
        return visitor.visit_method_call_expression(self)


@dataclass
class IndexExpression(Expression):
    """Index expression (e.g., arr[0], dict["key"])"""
    object: Expression = None
    index: Expression = None
    line_number: int | None = None
    
    def execute(self, interpreter):
        """Execute index expression"""
        return self.evaluate(interpreter)
    
    def evaluate(self, interpreter):
        """Evaluate index expression"""
        obj = self.object.evaluate(interpreter)
        index_val = self.index.evaluate(interpreter)
        
        # Handle list/dict/string indexing
        try:
            return obj[index_val]
        except (KeyError, IndexError, TypeError) as e:
            raise RuntimeError(
                f"Indexing error: {e}"
            )
    
    def accept(self, visitor):
        return visitor.visit_index_expression(self)


# ========================================================================
# ADDITIONAL STATEMENTS (v0.9.6)
# ========================================================================

@dataclass
class PrintStatement(Statement):
    """Print statement - outputs values to console"""
    expression: Expression | None = None
    line_number: int | None = None
    
    def execute(self, interpreter):
        """Execute the print statement"""
        if self.expression:
            value = self.expression.evaluate(interpreter)
        else:
            value = ""
        print(value)
        return None
    
    def accept(self, visitor):
        return visitor.visit_print_statement(self)


@dataclass
class ReturnStatement(Statement):
    """Return statement - returns a value from a function"""
    expression: Expression | None = None
    line_number: int | None = None
    
    def execute(self, interpreter):
        """Execute the return statement"""
        if self.expression:
            value = self.expression.evaluate(interpreter)
            # Signal return to function executor
            raise ReturnValue(value)
        raise ReturnValue(None)
    
    def accept(self, visitor):
        return visitor.visit_return_statement(self)


@dataclass
class FunctionDefinition(Statement):
    """Function definition statement"""
    name: str = ""
    parameters: list[str] = None
    body: list[Statement] = None
    return_type: str | None = None
    line_number: int | None = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
        if self.body is None:
            self.body = []
    
    def execute(self, interpreter):
        """Execute the function definition - register the function"""
        interpreter.define_function(self.name, self)
        return None
    
    def accept(self, visitor):
        return visitor.visit_function_definition(self)


# ========================================================================
# ADDITIONAL EXPRESSIONS (v0.9.6)
# ========================================================================

@dataclass
class ListExpression(Expression):
    """List/Array literal expression"""
    elements: list[Expression] = None
    line_number: int | None = None
    
    def __post_init__(self):
        if self.elements is None:
            self.elements = []
    
    def execute(self, interpreter):
        """Execute the list expression"""
        return self.evaluate(interpreter)
    
    def evaluate(self, interpreter):
        """Evaluate the list expression"""
        return [elem.evaluate(interpreter) for elem in self.elements]
    
    def accept(self, visitor):
        return visitor.visit_list_expression(self)


@dataclass
class DictionaryExpression(Expression):
    """Dictionary/Map literal expression"""
    pairs: list[tuple[str, Expression]] = None
    line_number: int | None = None
    
    def __post_init__(self):
        if self.pairs is None:
            self.pairs = []
    
    def execute(self, interpreter):
        """Execute the dictionary expression"""
        return self.evaluate(interpreter)
    
    def evaluate(self, interpreter):
        """Evaluate the dictionary expression"""
        result = {}
        for key, value_expr in self.pairs:
            result[key] = value_expr.evaluate(interpreter)
        return result
    
    def accept(self, visitor):
        return visitor.visit_dictionary_expression(self)


# ========================================================================
# SPECIAL EXCEPTIONS
# ========================================================================

class ReturnValue(Exception):
    """Exception used to implement return statements"""
    
    def __init__(self, value):
        self.value = value
        super().__init__()


# ========================================================================
# AST VISITOR INTERFACE
# ========================================================================

class ASTVisitor(ABC):
    """Visitor interface for AST traversal"""
    
    @abstractmethod
    def visit_enhanced_if_statement(self, node: EnhancedIfStatement):
        pass
    
    @abstractmethod
    def visit_elif_clause(self, node: ElifClause):
        pass
    
    @abstractmethod
    def visit_enhanced_for_loop(self, node: EnhancedForLoop):
        pass
    
    @abstractmethod
    def visit_enhanced_while_loop(self, node: EnhancedWhileLoop):
        pass
    
    @abstractmethod
    def visit_enhanced_try_statement(self, node: EnhancedTryStatement):
        pass
    
    @abstractmethod
    def visit_catch_clause(self, node: CatchClause):
        pass
    
    @abstractmethod
    def visit_break_statement(self, node: BreakStatement):
        pass
    
    @abstractmethod
    def visit_continue_statement(self, node: ContinueStatement):
        pass
    
    # Module system visitors
    @abstractmethod
    def visit_import_statement(self, node: ImportStatement):
        pass
    
    @abstractmethod
    def visit_import_from_statement(self, node: ImportFromStatement):
        pass
    
    @abstractmethod
    def visit_export_statement(self, node: ExportStatement):
        pass
    
    # AI integration visitors
    @abstractmethod
    def visit_ai_complete_statement(self, node: AICompleteStatement):
        pass
    
    @abstractmethod
    def visit_ai_explain_statement(self, node: AIExplainStatement):
        pass
    
    @abstractmethod
    def visit_ai_debug_statement(self, node: AIDebugStatement):
        pass
    
    @abstractmethod
    def visit_ai_optimize_statement(self, node: AIOptimizeStatement):
        pass
    
    # Cognitive programming visitors
    @abstractmethod
    def visit_cognitive_check_statement(self, node: CognitiveCheckStatement):
        pass
    
    @abstractmethod
    def visit_focus_mode_statement(self, node: FocusModeStatement):
        pass
    
    @abstractmethod
    def visit_working_memory_statement(self, node: WorkingMemoryStatement):
        pass
    
    # Expression visitors
    @abstractmethod
    def visit_variable_expression(self, node: VariableExpression):
        pass
    
    @abstractmethod
    def visit_literal_expression(self, node: LiteralExpression):
        pass
    
    @abstractmethod
    def visit_binary_operator_expression(self, node: BinaryOperatorExpression):
        pass
    
    @abstractmethod
    def visit_unary_operator_expression(self, node: UnaryOperatorExpression):
        pass
    
    @abstractmethod
    def visit_function_call_expression(self, node: FunctionCallExpression):
        pass


# ========================================================================
# UTILITY FUNCTIONS
# ========================================================================

def create_ast_from_lark_tree(tree) -> ASTNode:
    """
    Convert a Lark parse tree to Sona AST nodes
    
    This function would be implemented to transform the parse tree
    from the Lark parser into our typed AST nodes.
    """
    # This would be a comprehensive transformer implementation
    # For now, just a placeholder
    raise NotImplementedError("AST transformation not yet implemented")

def validate_ast(node: ASTNode) -> bool:
    """
    Validate an AST node for correctness
    
    This function performs semantic validation on the AST,
    checking for things like variable usage, type consistency, etc.
    """
    # This would implement semantic validation
    # For now, just a placeholder
    return True

def optimize_ast(node: ASTNode) -> ASTNode:
    """
    Optimize an AST node for better performance
    
    This function applies various optimization techniques
    to improve execution performance.
    """
    # This would implement AST optimization
    # For now, just return the original node
    return node
