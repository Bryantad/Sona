"""Typed AST nodes used by the canonical Sona 0.15.x frontend.

Historical node names remain import-compatible. Executable parser paths are
limited to nodes certified by the canonical transformer.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


def _should_retry_legacy_call_signature(exc: TypeError) -> bool:
    """Return true only for Python call-signature TypeErrors.

    Older callable adapters accepted `call(args)` while newer Sona functions
    accept `call(args, kwargs)`. The retry path must not catch arbitrary
    TypeErrors raised from inside the called function body.
    """
    message = str(exc)
    signature_markers = (
        "positional argument",
        "positional arguments",
        "required positional",
        "unexpected keyword",
        "missing ",
        "takes ",
    )
    return any(marker in message for marker in signature_markers)


def _cognitive_error(message: str, node: Any | None = None):
    from .errors import ErrorCode, SourceLocation
    from .interpreter import SonaRuntimeError

    file = "<unknown>"
    if node is not None:
        span = getattr(node, "span", None)
        if span is not None:
            file = getattr(span, "file", file)
        else:
            file = getattr(getattr(node, "_runtime_vm", None), "current_filename", file)

    raise SonaRuntimeError(
        message,
        code=ErrorCode.INVALID_ARGUMENT,
        location=SourceLocation.from_node(node, file=file) if node is not None else SourceLocation.unknown(),
        suggestion="Use literal, positional, keyword, or list/map spread arguments.",
        diagnostic_id="SONA-COG-001",
    )


def _evaluate_cognitive_value(vm, value: Any, node: Any | None = None) -> Any:
    if value is None:
        return None

    positional = globals().get("PositionalArgument")
    keyword = globals().get("KeywordArgument")
    spread = globals().get("SpreadArgument")
    if positional is not None and isinstance(value, positional):
        return _evaluate_cognitive_value(vm, value.value, node)
    if keyword is not None and isinstance(value, keyword):
        return _evaluate_cognitive_value(vm, value.value, node)
    if spread is not None and isinstance(value, spread):
        return _evaluate_cognitive_value(vm, value.value, node)

    if hasattr(value, "evaluate"):
        return value.evaluate(vm)
    if isinstance(value, dict):
        return {
            key: _evaluate_cognitive_value(vm, item, node)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_evaluate_cognitive_value(vm, item, node) for item in value]
    if isinstance(value, tuple):
        return tuple(_evaluate_cognitive_value(vm, item, node) for item in value)
    return value


def _evaluate_cognitive_body(vm, body: Any, node: Any | None = None) -> dict[str, Any]:
    """Evaluate a cognitive statement payload without leaking host exceptions."""
    if node is not None:
        try:
            setattr(node, "_runtime_vm", vm)
        except Exception:
            pass
    if body is None:
        return {}
    if not isinstance(body, dict):
        _cognitive_error("Malformed cognitive statement payload.", node)

    evaluated: dict[str, Any] = {}
    next_arg = 0
    for key, expr in body.items():
        name = str(key)
        if name.startswith("arg"):
            try:
                next_arg = max(next_arg, int(name[3:]) + 1)
            except ValueError:
                pass
        if name.startswith("spread"):
            spread_value = _evaluate_cognitive_value(vm, expr, node)
            if isinstance(spread_value, dict):
                evaluated.update({str(k): v for k, v in spread_value.items()})
            elif isinstance(spread_value, (list, tuple)):
                for item in spread_value:
                    while f"arg{next_arg}" in evaluated:
                        next_arg += 1
                    evaluated[f"arg{next_arg}"] = item
                    next_arg += 1
            else:
                _cognitive_error("Cognitive spread arguments must evaluate to a list or map.", node)
            continue
        evaluated[name] = _evaluate_cognitive_value(vm, expr, node)
    return evaluated


def _attach_call_site_diagnostic(exc: Exception, node: Any, suggestion: str) -> None:
    from .errors import SourceLocation

    diagnostic = getattr(exc, "diagnostic", None)
    if diagnostic is None:
        return
    location = getattr(diagnostic, "location", None)
    if location is None or getattr(location, "file", "<unknown>") == "<unknown>":
        diagnostic.location = SourceLocation.from_node(node)
    if not getattr(diagnostic, "suggestion", ""):
        diagnostic.suggestion = suggestion


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
        interpreter.memory.declare_variable(self.iterator_var, None)
        
        try:
            result = None
            for item in iterable_value:
                if hasattr(interpreter, "_record_loop_iteration"):
                    interpreter._record_loop_iteration()
                # Set iterator variable
                interpreter.memory.set_local_variable(self.iterator_var, item)
                
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
            if hasattr(vm, "_record_loop_iteration"):
                vm._record_loop_iteration()
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
            # Never allow try/catch to swallow control-flow signals
            from .interpreter import BreakException, ContinueException
            if isinstance(e, (ReturnValue, BreakException, ContinueException)):
                raise

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
    
    def execute(self, vm):
        """Catch clauses are executed as part of try statements"""
        return vm.execute_statements(self.body)
    
    def matches_exception(self, exception) -> bool:
        """Check if this catch clause handles the given exception."""
        exc_type = (self.exception_type or "").strip()
        if (len(exc_type) >= 2) and (
            (exc_type[0] == '"' and exc_type[-1] == '"') or
            (exc_type[0] == "'" and exc_type[-1] == "'")
        ):
            exc_type = exc_type[1:-1]

        # Catch-all
        if exc_type in ("", "_", "*", "Exception"):
            return True

        # Try builtins exception hierarchy first (e.g., ValueError matches subclasses)
        import builtins
        builtin_exc = getattr(builtins, exc_type, None)
        if isinstance(builtin_exc, type) and issubclass(builtin_exc, BaseException):
            return isinstance(exception, builtin_exc)

        # Fallback: match by class name or fully-qualified name
        exc_class = type(exception)
        if exc_class.__name__ == exc_type:
            return True
        if f"{exc_class.__module__}.{exc_class.__name__}" == exc_type:
            return True
        return False

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
# MATCH / WHEN (v0.9.9)
# ========================================================================


@dataclass
class WhenCase:
    condition: Expression
    body: list[Statement]


@dataclass
class WhenStatement(Statement):
    test_expr: Expression
    cases: list[WhenCase]
    line_number: int | None = None

    def accept(self, visitor):
        method = getattr(visitor, 'visit_when_statement', None)
        if callable(method):
            return method(self)
        return None

    def execute(self, interpreter):
        # Evaluate cases in order; first truthy condition wins
        for case in self.cases:
            if case.condition.evaluate(interpreter):
                return interpreter.execute_block(case.body)
        return None


@dataclass
class WhenExprCase:
    condition: Expression
    value: Expression


@dataclass
class WhenExpression(Expression):
    cases: list[WhenExprCase]
    line_number: int | None = None

    def accept(self, visitor):
        method = getattr(visitor, 'visit_when_expression', None)
        if callable(method):
            return method(self)
        return None

    def execute(self, interpreter):
        return self.evaluate(interpreter)

    def evaluate(self, interpreter):
        default_value_expr: Expression | None = None

        for case in self.cases:
            # Treat `_` as a default branch without evaluating
            if isinstance(case.condition, VariableExpression) and case.condition.name == '_':
                default_value_expr = case.value
                continue

            if case.condition.evaluate(interpreter):
                return case.value.evaluate(interpreter)

        if default_value_expr is not None:
            return default_value_expr.evaluate(interpreter)
        return None


@dataclass
class PatternWildcard:
    pass


@dataclass
class PatternBinding:
    name: str


@dataclass
class MatchCase:
    pattern: Any  # Expression | PatternBinding | PatternWildcard
    body: list[Statement]


@dataclass
class MatchStatement(Statement):
    target: Expression
    cases: list[MatchCase]
    line_number: int | None = None

    def accept(self, visitor):
        method = getattr(visitor, 'visit_match_statement', None)
        if callable(method):
            return method(self)
        return None

    def execute(self, interpreter):
        target_value = self.target.evaluate(interpreter)

        for case in self.cases:
            interpreter.memory.push_scope("match_case")
            try:
                pattern = case.pattern

                if isinstance(pattern, PatternWildcard):
                    return interpreter.execute_block(case.body)

                if isinstance(pattern, PatternBinding):
                    interpreter.memory.set_variable(pattern.name, target_value)
                    return interpreter.execute_block(case.body)

                # Expression pattern: evaluate and compare
                if hasattr(pattern, 'evaluate'):
                    pat_val = pattern.evaluate(interpreter)
                else:
                    pat_val = pattern

                if target_value == pat_val:
                    return interpreter.execute_block(case.body)
            finally:
                interpreter.memory.pop_scope()

        return None

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
    is_declaration: bool = True
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
        if self.is_declaration and hasattr(vm.memory, "declare_variable"):
            vm.memory.declare_variable(
                self.name, evaluated_value, is_const=self.is_const,
                definition_span=getattr(self, "span", None),
            )
        else:
            vm.memory.set_variable(
                self.name, evaluated_value,
                assignment_span=getattr(self, "span", None),
            )
        
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
        evaluated_body = _evaluate_cognitive_body(vm, self.body, self)
        if hasattr(vm, 'cognitive_monitor'):
            return vm.cognitive_monitor.check_cognitive_load(evaluated_body)
        else:
            # Basic execution without cognitive monitoring
            for key, value in evaluated_body.items():
                vm.current_scope[key] = value
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
        evaluated_body = _evaluate_cognitive_body(vm, self.body, self)
        if hasattr(vm, 'cognitive_monitor'):
            return vm.cognitive_monitor.configure_focus_mode(evaluated_body)
        else:
            # Basic execution without cognitive features
            for key, value in evaluated_body.items():
                vm.current_scope[key] = value
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
        evaluated_body = _evaluate_cognitive_body(vm, self.body, self)
        if hasattr(vm, 'cognitive_monitor'):
            return vm.cognitive_monitor.manage_working_memory(evaluated_body)
        else:
            # Basic execution without cognitive features
            for key, value in evaluated_body.items():
                vm.current_scope[key] = value
            return None

@dataclass
class FocusBlockStatement(Statement):
    """Focus block that narrows diagnostics and boosts trace inside the block."""
    meta: dict[str, Expression]
    body: list[Statement]
    line_number: int | None = None

    def accept(self, visitor):
        return visitor.visit_focus_block_statement(self)

    def _eval_value(self, vm, value):
        if hasattr(value, 'evaluate'):
            return value.evaluate(vm)
        return value

    def execute(self, vm):
        meta_vals = _evaluate_cognitive_body(vm, self.meta, self)
        enter = getattr(vm, '_enter_focus_block', None)
        exit_block = getattr(vm, '_exit_focus_block', None)
        state = None
        if callable(enter):
            state = enter(meta_vals)
        error = False
        try:
            return vm.execute_block(self.body) if hasattr(vm, 'execute_block') else None
        except Exception:
            error = True
            raise
        finally:
            if state is not None and callable(exit_block):
                exit_block(state, error=error)

@dataclass
class IntentStatement(Statement):
    """Declare or update intent metadata for the current cognitive scope."""
    body: dict[str, Expression]
    line_number: int | None = None

    def accept(self, visitor):
        return visitor.visit_intent_statement(self)

    def _evaluate_body(self, vm) -> dict[str, Any]:
        return _evaluate_cognitive_body(vm, self.body, self)

    def execute(self, vm):
        values = self._evaluate_body(vm)
        if hasattr(vm, 'cognitive_monitor'):
            result = vm.cognitive_monitor.record_intent(values)
            recorder = getattr(vm, "record_memory_episode", None)
            if callable(recorder):
                recorder(
                    kind="intent_recorded",
                    source_type="runtime",
                    importance=0.75,
                    payload={
                        "goal": values.get("goal"),
                        "has_constraints": bool(values.get("constraints")),
                        "has_success": bool(
                            values.get("success")
                            or values.get("definition_of_done")
                        ),
                    },
                )
            return result
        return values

@dataclass
class DecisionStatement(Statement):
    """Record a decision and rationale for traceability."""
    body: dict[str, Expression]
    line_number: int | None = None

    def accept(self, visitor):
        return visitor.visit_decision_statement(self)

    def _evaluate_body(self, vm) -> dict[str, Any]:
        return _evaluate_cognitive_body(vm, self.body, self)

    def execute(self, vm):
        values = self._evaluate_body(vm)
        if hasattr(vm, 'cognitive_monitor'):
            return vm.cognitive_monitor.record_decision(values)
        return values

@dataclass
class CognitiveTraceStatement(Statement):
    """Toggle cognitive reasoning trace on/off."""
    body: dict[str, Expression]
    line_number: int | None = None

    def accept(self, visitor):
        return visitor.visit_cognitive_trace_statement(self)

    def execute(self, vm):
        if hasattr(vm, 'cognitive_monitor'):
            evaluated = _evaluate_cognitive_body(vm, self.body, self)
            return vm.cognitive_monitor.toggle_trace(evaluated)
        return None

@dataclass
class ExplainStepStatement(Statement):
    """Produce an explainability summary of the current cognitive state."""
    body: dict[str, Expression]
    line_number: int | None = None

    def accept(self, visitor):
        return visitor.visit_explain_step_statement(self)

    def execute(self, vm):
        if hasattr(vm, 'cognitive_monitor'):
            evaluated = _evaluate_cognitive_body(vm, self.body, self)
            return vm.cognitive_monitor.explain_step(evaluated)
        return None

@dataclass
class ProfileStatement(Statement):
    """Set or declare a cognitive accessibility profile for this scope/file."""
    body: dict[str, Expression]
    line_number: int | None = None

    def accept(self, visitor):
        return visitor.visit_profile_statement(self)

    def execute(self, vm):
        if hasattr(vm, 'cognitive_monitor'):
            evaluated = _evaluate_cognitive_body(vm, self.body, self)
            return vm.cognitive_monitor.set_profile(evaluated)
        return None

@dataclass
class CognitiveScopeStatement(Statement):
    """Create a cognitive scope boundary with its own intent/metadata."""
    name: Any
    meta: dict[str, Expression]
    body: list[Statement]
    line_number: int | None = None

    def accept(self, visitor):
        return visitor.visit_cognitive_scope_statement(self)

    def _eval_value(self, vm, value):
        return _evaluate_cognitive_value(vm, value, self)

    def execute(self, vm):
        monitor = getattr(vm, 'cognitive_monitor', None)
        name_val = self._eval_value(vm, self.name)
        meta_vals = _evaluate_cognitive_body(vm, self.meta, self)

        if not monitor:
            return vm.execute_block(self.body) if hasattr(vm, 'execute_block') else None

        monitor.push_scope(name=name_val, meta=meta_vals)
        monitor.evaluate_scope_budget(meta_vals, self.body)
        try:
            return vm.execute_block(self.body)
        finally:
            monitor.pop_scope()

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
            try:
                return interpreter.memory.get_variable(self.name)
            except NameError as error:
                from .errors import ErrorCode, SourceLocation
                from .interpreter import SonaRuntimeError
                raise SonaRuntimeError(
                    f"Undefined name '{self.name}'.",
                    code=ErrorCode.UNDEFINED_VARIABLE,
                    location=SourceLocation.from_node(self),
                    suggestion="Declare the name before using it.",
                    diagnostic_id="SONA-RUNTIME-003",
                ) from error
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
        try:
            left_val = self.left.evaluate(interpreter)
            if self.operator in {"&&", "and"} and not left_val:
                return left_val
            if self.operator in {"||", "or"} and left_val:
                return left_val
            right_val = self.right.evaluate(interpreter)

            if self.operator == "+":
                if isinstance(left_val, str) or isinstance(right_val, str):
                    return str(left_val) + str(right_val)
                return left_val + right_val
            if self.operator == "-":
                return left_val - right_val
            if self.operator == "*":
                return left_val * right_val
            if self.operator == "/":
                return left_val / right_val
            if self.operator == "%":
                return left_val % right_val
            if self.operator == "**":
                return left_val ** right_val
            if self.operator == "==":
                return left_val == right_val
            if self.operator == "!=":
                return left_val != right_val
            if self.operator == "<":
                return left_val < right_val
            if self.operator == ">":
                return left_val > right_val
            if self.operator == "<=":
                return left_val <= right_val
            if self.operator == ">=":
                return left_val >= right_val
            if self.operator in {"&&", "and"}:
                return left_val and right_val
            if self.operator in {"||", "or"}:
                return left_val or right_val
            raise TypeError(f"unknown operator {self.operator}")
        except ZeroDivisionError as error:
            from .errors import ErrorCode, SourceLocation
            from .interpreter import SonaRuntimeError
            raise SonaRuntimeError(
                "Division or modulo by zero.",
                code=ErrorCode.DIVISION_BY_ZERO,
                location=SourceLocation.from_node(self),
                suggestion="Use a nonzero divisor.",
                diagnostic_id="SONA-RUNTIME-004",
            ) from error
        except TypeError as error:
            from .errors import ErrorCode, SourceLocation
            from .interpreter import SonaRuntimeError
            raise SonaRuntimeError(
                f"Operator '{self.operator}' does not support these operand types.",
                code=ErrorCode.INVALID_OPERAND,
                location=SourceLocation.from_node(self),
                suggestion="Use operands supported by this operator or convert them explicitly.",
                diagnostic_id="SONA-RUNTIME-005",
            ) from error


@dataclass
class ChainedComparisonExpression(Expression):
    """Evaluate comparisons left-to-right while evaluating each operand once."""

    operands: list[Expression]
    operators: list[str]
    line_number: int | None = None

    def accept(self, visitor):
        method = getattr(visitor, "visit_chained_comparison_expression", None)
        return method(self) if callable(method) else None

    def execute(self, interpreter):
        return self.evaluate(interpreter)

    def evaluate(self, interpreter) -> bool:
        if not self.operands:
            return True
        left = self.operands[0].evaluate(interpreter)
        comparisons = {
            "<": lambda a, b: a < b,
            ">": lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            ">=": lambda a, b: a >= b,
        }
        try:
            for operator, operand in zip(self.operators, self.operands[1:]):
                right = operand.evaluate(interpreter)
                if not comparisons[operator](left, right):
                    return False
                left = right
        except TypeError as error:
            from .errors import ErrorCode, SourceLocation
            from .interpreter import SonaRuntimeError
            raise SonaRuntimeError(
                "Chained comparison operands are not mutually orderable.",
                code=ErrorCode.INVALID_OPERAND,
                location=SourceLocation.from_node(self),
                suggestion="Compare values of compatible types.",
                diagnostic_id="SONA-RUNTIME-005",
            ) from error
        return True

@dataclass
class UnaryOperatorExpression(Expression):
    """Unary operator expression"""
    operator: str
    operand: Expression
    line_number: int | None = None
    
    def accept(self, visitor):
        return visitor.visit_unary_operator_expression(self)
    
    def execute(self, interpreter):
        return self.evaluate(interpreter)
    
    def evaluate(self, interpreter) -> Any:
        operand_val = self.operand.evaluate(interpreter)
        
        if self.operator == "+":
            return +operand_val
        elif self.operator == "-":
            return -operand_val
        elif self.operator in ("!", "not"):
            return not operand_val
        else:
            raise RuntimeError(f"Unknown unary operator: {self.operator}")

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
        pos_args: list[Any] = []
        kw_args: dict[str, Any] = {}

        for arg in self.arguments:
            if isinstance(arg, PositionalArgument):
                pos_args.append(arg.value.evaluate(interpreter))
            elif isinstance(arg, KeywordArgument):
                kw_args[arg.name] = arg.value.evaluate(interpreter)
            elif isinstance(arg, SpreadArgument):
                spread_val = arg.value.evaluate(interpreter)
                if isinstance(spread_val, dict):
                    for k, v in spread_val.items():
                        kw_args[str(k)] = v
                elif isinstance(spread_val, (list, tuple)):
                    pos_args.extend(list(spread_val))
                else:
                    raise TypeError(
                        "Spread argument must be a list/tuple (positional) or dict (keyword)"
                    )
            elif hasattr(arg, 'evaluate'):
                pos_args.append(arg.evaluate(interpreter))
            else:
                pos_args.append(arg)
        
        # Check if it's a built-in function
        try:
            func = interpreter.memory.get_variable(self.name)
            if callable(func):
                try:
                    return func(*pos_args, **kw_args)
                except Exception as exc:
                    _attach_call_site_diagnostic(
                        exc,
                        self,
                        "Pass the arguments required by this function.",
                    )
                    raise
        except NameError:
            pass
        
        # Check if it's a user-defined function
        if self.name in interpreter.functions:
            try:
                return interpreter.call_function(self.name, pos_args, kw_args)
            except Exception as exc:
                _attach_call_site_diagnostic(
                    exc,
                    self,
                    "Pass the arguments required by this function.",
                )
                raise
        
        from .errors import ErrorCode, SourceLocation
        from .interpreter import SonaRuntimeError
        raise SonaRuntimeError(
            f"Undefined function '{self.name}'.",
            code=ErrorCode.UNDEFINED_FUNCTION,
            location=SourceLocation.from_node(self),
            suggestion="Declare or import the function before calling it.",
            diagnostic_id="SONA-RUNTIME-003",
        )


@dataclass
class CallExpression(Expression):
    """Call an expression value (e.g., f()(x), arr[i](x))"""
    callee: Expression
    arguments: list[Any] = None
    line_number: int | None = None

    def __post_init__(self):
        if self.arguments is None:
            self.arguments = []

    def execute(self, interpreter):
        return self.evaluate(interpreter)

    def evaluate(self, interpreter) -> Any:
        try:
            callee_value = self.callee.evaluate(interpreter)
        except Exception as exc:
            if isinstance(self.callee, VariableExpression):
                diagnostic = getattr(exc, "diagnostic", None)
                if getattr(diagnostic, "diagnostic_id", None) == "SONA-RUNTIME-003":
                    from .errors import ErrorCode, SourceLocation
                    from .interpreter import SonaRuntimeError
                    raise SonaRuntimeError(
                        f"Function '{self.callee.name}' is not defined.",
                        code=ErrorCode.UNDEFINED_FUNCTION,
                        location=SourceLocation.from_node(self),
                        suggestion="Declare or import the function before calling it.",
                        diagnostic_id="SONA-RUNTIME-003",
                    ) from exc
            raise

        pos_args: list[Any] = []
        kw_args: dict[str, Any] = {}

        for arg in self.arguments:
            if isinstance(arg, PositionalArgument):
                pos_args.append(arg.value.evaluate(interpreter))
            elif isinstance(arg, KeywordArgument):
                kw_args[arg.name] = arg.value.evaluate(interpreter)
            elif isinstance(arg, SpreadArgument):
                spread_val = arg.value.evaluate(interpreter)
                if isinstance(spread_val, dict):
                    for k, v in spread_val.items():
                        kw_args[str(k)] = v
                elif isinstance(spread_val, (list, tuple)):
                    pos_args.extend(list(spread_val))
                else:
                    raise TypeError(
                        "Spread argument must be a list/tuple (positional) or dict (keyword)"
                    )
            elif hasattr(arg, 'evaluate'):
                # Backward compatibility: treat as positional expression
                pos_args.append(arg.evaluate(interpreter))
            else:
                # Raw value
                pos_args.append(arg)

        if hasattr(callee_value, 'call') and callable(getattr(callee_value, 'call')):
            try:
                return callee_value.call(pos_args, kw_args)
            except Exception as exc:
                if not isinstance(exc, TypeError):
                    _attach_call_site_diagnostic(
                        exc,
                        self,
                        "Pass the arguments required by this function.",
                    )
                    raise
                if not _should_retry_legacy_call_signature(exc):
                    raise
                # Backward compatibility for older call() signatures
                try:
                    return callee_value.call(pos_args)
                except TypeError:
                    raise exc
                except Exception as retry_exc:
                    _attach_call_site_diagnostic(
                        retry_exc,
                        self,
                        "Pass the arguments required by this function.",
                    )
                    raise
        if callable(callee_value):
            try:
                return callee_value(*pos_args, **kw_args)
            except Exception as exc:
                _attach_call_site_diagnostic(
                    exc,
                    self,
                    "Pass the arguments required by this function.",
                )
                raise
        from .errors import ErrorCode, SourceLocation
        from .interpreter import SonaRuntimeError
        raise SonaRuntimeError(
            f"Object of type '{type(callee_value).__name__}' is not callable",
            code=ErrorCode.RUNTIME_ERROR,
            location=SourceLocation.from_node(self),
            suggestion="Call a function value or remove the call parentheses.",
            diagnostic_id="SONA-RUNTIME-002",
        )

    def accept(self, visitor):
        # Keep visitor compatibility for code that doesn't know about CallExpression
        method = getattr(visitor, 'visit_call_expression', None)
        if callable(method):
            return method(self)
        return visitor.visit_function_call_expression(self)


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

        # Prefer dictionary fields for object-like maps.
        if isinstance(obj, dict) and self.property_name in obj:
            return obj[self.property_name]

        # Handle module property access
        if hasattr(obj, self.property_name):
            attr = getattr(obj, self.property_name)
            return attr

        submodules = getattr(obj, "__sona_submodules__", None)
        if isinstance(submodules, dict) and self.property_name in submodules:
            return submodules[self.property_name]

        from .errors import ErrorCode, SourceLocation
        from .interpreter import SonaRuntimeError
        raise SonaRuntimeError(
            f"Object has no property '{self.property_name}'.",
            code=ErrorCode.RUNTIME_ERROR,
            location=SourceLocation.from_node(self),
            suggestion="Use an existing map key, module symbol, or object property.",
            diagnostic_id="SONA-RUNTIME-007",
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

        pos_args: list[Any] = []
        kw_args: dict[str, Any] = {}

        for arg in self.arguments:
            if isinstance(arg, PositionalArgument):
                pos_args.append(arg.value.evaluate(interpreter))
            elif isinstance(arg, KeywordArgument):
                kw_args[arg.name] = arg.value.evaluate(interpreter)
            elif isinstance(arg, SpreadArgument):
                spread_val = arg.value.evaluate(interpreter)
                if isinstance(spread_val, dict):
                    for k, v in spread_val.items():
                        kw_args[str(k)] = v
                elif isinstance(spread_val, (list, tuple)):
                    pos_args.extend(list(spread_val))
                else:
                    raise TypeError(
                        "Spread argument must be a list/tuple (positional) or dict (keyword)"
                    )
            elif hasattr(arg, 'evaluate'):
                pos_args.append(arg.evaluate(interpreter))
            else:
                pos_args.append(arg)

        # Support object-like dictionaries with callable fields.
        if isinstance(obj, dict) and self.method_name in obj:
            method = obj[self.method_name]
            if hasattr(method, 'call') and callable(getattr(method, 'call')):
                method_args = [obj, *pos_args]
                try:
                    return method.call(method_args, kw_args)
                except TypeError as exc:
                    if not _should_retry_legacy_call_signature(exc):
                        raise
                    try:
                        return method.call(method_args)
                    except TypeError:
                        raise exc
            if callable(method):
                return method(obj, *pos_args, **kw_args)
            from .errors import ErrorCode, SourceLocation
            from .interpreter import SonaRuntimeError
            raise SonaRuntimeError(
                f"'{self.method_name}' is not a callable method.",
                code=ErrorCode.NOT_CALLABLE,
                location=SourceLocation.from_node(self),
                diagnostic_id="SONA-RUNTIME-002",
            )

        # Get the method from the object
        if hasattr(obj, self.method_name):
            method = getattr(obj, self.method_name)
            if hasattr(method, 'call') and callable(getattr(method, 'call')):
                try:
                    return method.call(pos_args, kw_args)
                except TypeError as exc:
                    if not _should_retry_legacy_call_signature(exc):
                        raise
                    try:
                        return method.call(pos_args)
                    except TypeError:
                        raise exc
            if callable(method):
                return method(*pos_args, **kw_args)
            from .errors import ErrorCode, SourceLocation
            from .interpreter import SonaRuntimeError
            raise SonaRuntimeError(
                f"'{self.method_name}' is not a callable method.",
                code=ErrorCode.NOT_CALLABLE,
                location=SourceLocation.from_node(self),
                diagnostic_id="SONA-RUNTIME-002",
            )
        
        from .errors import ErrorCode, SourceLocation
        from .interpreter import SonaRuntimeError
        raise SonaRuntimeError(
            f"Object has no method '{self.method_name}'.",
            code=ErrorCode.RUNTIME_ERROR,
            location=SourceLocation.from_node(self),
            suggestion="Call an existing method or inspect the module's public symbols.",
            diagnostic_id="SONA-RUNTIME-007",
        )
    
    def accept(self, visitor):
        return visitor.visit_method_call_expression(self)


@dataclass
class PositionalArgument:
    value: Expression


@dataclass
class KeywordArgument:
    name: str
    value: Expression


@dataclass
class SpreadArgument:
    value: Expression


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
        except (KeyError, IndexError, TypeError) as error:
            from .errors import ErrorCode, SourceLocation
            from .interpreter import SonaRuntimeError
            raise SonaRuntimeError(
                "The requested index or key is not available for this value.",
                code=ErrorCode.INDEX_OUT_OF_BOUNDS,
                location=SourceLocation.from_node(self),
                suggestion="Use an in-range index or an existing map key.",
                diagnostic_id="SONA-RUNTIME-006",
            ) from error
    
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
    default_values: dict[str, Expression] = None
    varargs_param: str | None = None
    body: list[Statement] = None
    return_type: str | None = None
    line_number: int | None = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
        if self.default_values is None:
            self.default_values = {}
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
    def visit_focus_block_statement(self, node: FocusBlockStatement):
        pass
    
    @abstractmethod
    def visit_working_memory_statement(self, node: WorkingMemoryStatement):
        pass

    @abstractmethod
    def visit_intent_statement(self, node: IntentStatement):
        pass

    @abstractmethod
    def visit_decision_statement(self, node: DecisionStatement):
        pass

    @abstractmethod
    def visit_cognitive_trace_statement(self, node: CognitiveTraceStatement):
        pass

    @abstractmethod
    def visit_explain_step_statement(self, node: ExplainStepStatement):
        pass

    @abstractmethod
    def visit_profile_statement(self, node: ProfileStatement):
        pass

    @abstractmethod
    def visit_cognitive_scope_statement(self, node: CognitiveScopeStatement):
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
# End of certified AST compatibility surface.
