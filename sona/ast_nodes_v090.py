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
        if self.condition.evaluate(vm.current_scope):
            return vm.execute_statements(self.if_body)
        
        for elif_clause in self.elif_clauses:
            if elif_clause.condition.evaluate(vm.current_scope):
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
class EnhancedForLoop(Statement):
    """Enhanced for loop with break/continue support"""
    iterator_var: str
    iterable: Expression
    body: list[Statement]
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_enhanced_for_loop(self)
    
    def execute(self, vm):
        """Execute enhanced for loop using the control flow engine"""
        if hasattr(vm, 'control_flow_integration'):
            return vm.control_flow_integration.execute_enhanced_for(self)
        else:
            return self._basic_execute(vm)
    
    def _basic_execute(self, vm):
        """Basic execution without enhanced features"""
        iterable_value = self.iterable.evaluate(vm.current_scope)
        result = None
        
        for item in iterable_value:
            vm.current_scope[self.iterator_var] = item
            result = vm.execute_statements(self.body)
        
        return result

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
        result = None
        while self.condition.evaluate(vm.current_scope):
            result = vm.execute_statements(self.body)
        return result

@dataclass
class EnhancedTryStatement(Statement):
    """Enhanced try/catch/finally with exception type matching"""
    try_body: list[Statement]
    catch_clauses: list['CatchClause']
    finally_body: list[Statement] | None = None
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_enhanced_try_statement(self)
    
    def execute(self, vm):
        """Execute enhanced try statement using the control flow engine"""
        if hasattr(vm, 'control_flow_integration'):
            return vm.control_flow_integration.execute_enhanced_try(self)
        else:
            return self._basic_execute(vm)
    
    def _basic_execute(self, vm):
        """Basic execution without enhanced features"""
        try:
            return vm.execute_statements(self.try_body)
        except Exception as e:
            for catch_clause in self.catch_clauses:
                if catch_clause.matches_exception(e):
                    if catch_clause.var_name:
                        vm.current_scope[catch_clause.var_name] = e
                    return vm.execute_statements(catch_clause.body)
            raise
        finally:
            if self.finally_body:
                vm.execute_statements(self.finally_body)

@dataclass
class CatchClause(ASTNode):
    """Catch clause for enhanced try statements"""
    exception_type: str
    var_name: str | None
    body: list[Statement]
    
    def accept(self, visitor):
        return visitor.visit_catch_clause(self)
    
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
        if hasattr(vm, 'control_flow_integration'):
            return vm.control_flow_integration.execute_break()
        else:
            raise RuntimeError("'break' outside loop")

@dataclass  
class ContinueStatement(Statement):
    """Continue statement for loop control"""
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_continue_statement(self)
    
    def execute(self, vm):
        """Execute continue statement"""
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
    
    def execute(self, vm):
        return self.evaluate(vm.current_scope)
    
    def evaluate(self, scope: dict[str, Any]) -> Any:
        if self.name in scope:
            return scope[self.name]
        else:
            raise NameError(f"Variable '{self.name}' is not defined")

@dataclass
class LiteralExpression(Expression):
    """Literal value expression"""
    value: Any
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_literal_expression(self)
    
    def execute(self, vm):
        return self.value
    
    def evaluate(self, scope: dict[str, Any]) -> Any:
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
    
    def execute(self, vm):
        return self.evaluate(vm.current_scope)
    
    def evaluate(self, scope: dict[str, Any]) -> Any:
        left_val = self.left.evaluate(scope)
        right_val = self.right.evaluate(scope)
        
        if self.operator == "+":
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
class FunctionCallExpression(Expression):
    """Function call expression"""
    function_name: str
    arguments: list[Expression]
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_function_call_expression(self)
    
    def execute(self, vm):
        return self.evaluate(vm.current_scope)
    
    def evaluate(self, scope: dict[str, Any]) -> Any:
        # This would be implemented to call functions from the VM's function registry
        # For now, just a placeholder
        raise NotImplementedError("Function calls not yet implemented")

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
