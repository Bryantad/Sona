"""
Advanced Loop Constructs for Sona Language - Phase 2
Implements enhanced loop functionality including for...in, while...else, and comprehensions
"""

from typing import Any, List, Dict, Iterator, Optional, Union
from lark import Tree, Token
from sona.interpreter import SonaInterpreter


class LoopControl:
    """Control flow management for loops"""
    
    def __init__(self):
        self.break_flag = False
        self.continue_flag = False
        self.break_label = None
        self.loop_labels = []
    
    def set_break(self, label: Optional[str] = None):
        """Set break flag with optional label"""
        self.break_flag = True
        self.break_label = label
    
    def set_continue(self, label: Optional[str] = None):
        """Set continue flag with optional label"""
        self.continue_flag = True
        self.break_label = label
    
    def clear_flags(self):
        """Clear all control flags"""
        self.break_flag = False
        self.continue_flag = False
        self.break_label = None
    
    def should_break(self, current_label: Optional[str] = None) -> bool:
        """Check if should break from current loop"""
        if not self.break_flag:
            return False
        
        if self.break_label is None or current_label == self.break_label:
            return True
        
        return False
    
    def should_continue(self, current_label: Optional[str] = None) -> bool:
        """Check if should continue current loop"""
        if not self.continue_flag:
            return False
        
        if self.break_label is None or current_label == self.break_label:
            return True
        
        return False


class IteratorProtocol:
    """Iterator protocol implementation for Sona"""
    
    @staticmethod
    def create_iterator(iterable: Any) -> Iterator[Any]:
        """Create iterator from various iterable types"""
        if isinstance(iterable, (list, tuple, str)):
            return iter(iterable)
        elif isinstance(iterable, dict):
            return iter(iterable.keys())
        elif isinstance(iterable, range):
            return iter(iterable)
        elif hasattr(iterable, '__iter__'):
            return iter(iterable)
        elif hasattr(iterable, '__getitem__'):
            # Create iterator for indexable objects
            return IndexIterator(iterable)
        else:
            raise TypeError(f"'{type(iterable).__name__}' object is not iterable")
    
    @staticmethod
    def is_iterable(obj: Any) -> bool:
        """Check if object is iterable"""
        try:
            IteratorProtocol.create_iterator(obj)
            return True
        except TypeError:
            return False


class IndexIterator:
    """Iterator for objects that support indexing but not iteration"""
    
    def __init__(self, obj):
        self.obj = obj
        self.index = 0
    
    def __iter__(self):
        return self
    
    def __next__(self):
        try:
            value = self.obj[self.index]
            self.index += 1
            return value
        except (IndexError, KeyError):
            raise StopIteration


class ComprehensionEngine:
    """Engine for list, dict, and set comprehensions"""
    
    def __init__(self, interpreter: SonaInterpreter):
        self.interpreter = interpreter
    
    def evaluate_list_comprehension(self, expr_tree: Tree, 
                                  for_clauses: List[Tree],
                                  if_clauses: List[Tree] = None) -> List[Any]:
        """
        Evaluate list comprehension: [expr for var in iterable if condition]
        """
        if_clauses = if_clauses or []
        results = []
        
        # Start with the outermost for clause
        self._eval_comprehension_recursive(
            expr_tree, for_clauses, if_clauses, 0, results, 'list'
        )
        
        return results
    
    def evaluate_dict_comprehension(self, key_expr: Tree, value_expr: Tree,
                                  for_clauses: List[Tree],
                                  if_clauses: List[Tree] = None) -> Dict[Any, Any]:
        """
        Evaluate dict comprehension: {key: value for var in iterable if condition}
        """
        if_clauses = if_clauses or []
        results = {}
        
        self._eval_comprehension_recursive(
            (key_expr, value_expr), for_clauses, if_clauses, 0, results, 'dict'
        )
        
        return results
    
    def evaluate_set_comprehension(self, expr_tree: Tree,
                                 for_clauses: List[Tree],
                                 if_clauses: List[Tree] = None) -> set:
        """
        Evaluate set comprehension: {expr for var in iterable if condition}
        """
        if_clauses = if_clauses or []
        results = set()
        
        self._eval_comprehension_recursive(
            expr_tree, for_clauses, if_clauses, 0, results, 'set'
        )
        
        return results
    
    def _eval_comprehension_recursive(self, expr, for_clauses, if_clauses, 
                                    clause_index, results, comp_type):
        """Recursively evaluate nested for clauses in comprehension"""
        if clause_index >= len(for_clauses):
            # Base case: evaluate all if conditions and expression
            if self._eval_all_conditions(if_clauses):
                if comp_type == 'list':
                    value = self.interpreter.visit_tree(expr)
                    results.append(value)
                elif comp_type == 'dict':
                    key_expr, value_expr = expr
                    key = self.interpreter.visit_tree(key_expr)
                    value = self.interpreter.visit_tree(value_expr)
                    results[key] = value
                elif comp_type == 'set':
                    value = self.interpreter.visit_tree(expr)
                    results.add(value)
            return
        
        # Get current for clause
        for_clause = for_clauses[clause_index]
        var_name = str(for_clause.children[0])
        iterable_expr = for_clause.children[1]
        
        # Evaluate iterable
        iterable = self.interpreter.visit_tree(iterable_expr)
        iterator = IteratorProtocol.create_iterator(iterable)
        
        # Create new scope for loop variable
        self.interpreter.env.append({})
        
        try:
            for item in iterator:
                # Set loop variable
                self.interpreter.env[-1][var_name] = item
                
                # Recurse to next for clause or evaluate expression
                self._eval_comprehension_recursive(
                    expr, for_clauses, if_clauses, clause_index + 1, 
                    results, comp_type
                )
        finally:
            # Clean up scope
            self.interpreter.env.pop()
    
    def _eval_all_conditions(self, if_clauses: List[Tree]) -> bool:
        """Evaluate all if conditions in comprehension"""
        for if_clause in if_clauses:
            condition = self.interpreter.visit_tree(if_clause)
            if not self._is_truthy(condition):
                return False
        return True
    
    def _is_truthy(self, value: Any) -> bool:
        """Check if value is truthy in Sona"""
        if value is None or value is False:
            return False
        if isinstance(value, (int, float)) and value == 0:
            return False
        if isinstance(value, (str, list, dict, set)) and len(value) == 0:
            return False
        return True


class AdvancedLoops:
    """Advanced loop constructs implementation"""
    
    def __init__(self, interpreter: SonaInterpreter):
        self.interpreter = interpreter
        self.loop_control = LoopControl()
        self.comprehension_engine = ComprehensionEngine(interpreter)
    
    def execute_for_in_loop(self, var_name: str, iterable_expr: Tree, 
                           body: Tree, label: Optional[str] = None) -> Any:
        """
        Execute for...in loop: for var in iterable { body }
        """
        # Evaluate iterable
        iterable = self.interpreter.visit_tree(iterable_expr)
        iterator = IteratorProtocol.create_iterator(iterable)
        
        # Create new scope for loop
        self.interpreter.env.append({})
        last_value = None
        
        try:
            for item in iterator:
                # Set loop variable
                self.interpreter.env[-1][var_name] = item
                
                # Execute body
                try:
                    result = self.interpreter.visit_tree(body)
                    if result is not None:
                        last_value = result
                except Exception as e:
                    if "break" in str(e):
                        self.loop_control.set_break()
                    elif "continue" in str(e):
                        self.loop_control.set_continue()
                    else:
                        raise
                
                # Check control flow
                if self.loop_control.should_break(label):
                    self.loop_control.clear_flags()
                    break
                elif self.loop_control.should_continue(label):
                    self.loop_control.clear_flags()
                    continue
        
        finally:
            # Clean up scope
            self.interpreter.env.pop()
        
        return last_value
    
    def execute_while_else_loop(self, condition_expr: Tree, body: Tree,
                               else_body: Tree = None, 
                               label: Optional[str] = None) -> Any:
        """
        Execute while...else loop: while condition { body } else { else_body }
        """
        last_value = None
        loop_executed = False
        broke_early = False
        
        # Create new scope for loop
        self.interpreter.env.append({})
        
        try:
            while True:
                # Evaluate condition
                condition = self.interpreter.visit_tree(condition_expr)
                if not self._is_truthy(condition):
                    break
                
                loop_executed = True
                
                # Execute body
                try:
                    result = self.interpreter.visit_tree(body)
                    if result is not None:
                        last_value = result
                except Exception as e:
                    if "break" in str(e):
                        self.loop_control.set_break()
                        broke_early = True
                    elif "continue" in str(e):
                        self.loop_control.set_continue()
                    else:
                        raise
                
                # Check control flow
                if self.loop_control.should_break(label):
                    self.loop_control.clear_flags()
                    broke_early = True
                    break
                elif self.loop_control.should_continue(label):
                    self.loop_control.clear_flags()
                    continue
            
            # Execute else clause if loop completed normally (no break)
            if else_body and loop_executed and not broke_early:
                else_result = self.interpreter.visit_tree(else_body)
                if else_result is not None:
                    last_value = else_result
        
        finally:
            # Clean up scope
            self.interpreter.env.pop()
        
        return last_value
    
    def execute_loop_until(self, body: Tree, until_condition: Tree,
                          label: Optional[str] = None) -> Any:
        """
        Execute loop...until: loop { body } until condition
        """
        last_value = None
        
        # Create new scope for loop
        self.interpreter.env.append({})
        
        try:
            while True:
                # Execute body first (do-while style)
                try:
                    result = self.interpreter.visit_tree(body)
                    if result is not None:
                        last_value = result
                except Exception as e:
                    if "break" in str(e):
                        self.loop_control.set_break()
                    elif "continue" in str(e):
                        self.loop_control.set_continue()
                    else:
                        raise
                
                # Check control flow
                if self.loop_control.should_break(label):
                    self.loop_control.clear_flags()
                    break
                elif self.loop_control.should_continue(label):
                    self.loop_control.clear_flags()
                    # Continue to condition check
                
                # Check until condition
                condition = self.interpreter.visit_tree(until_condition)
                if self._is_truthy(condition):
                    break
        
        finally:
            # Clean up scope
            self.interpreter.env.pop()
        
        return last_value
    
    def _is_truthy(self, value: Any) -> bool:
        """Check if value is truthy in Sona"""
        if value is None or value is False:
            return False
        if isinstance(value, (int, float)) and value == 0:
            return False
        if isinstance(value, (str, list, dict, set)) and len(value) == 0:
            return False
        return True


def integrate_advanced_loops(interpreter_class):
    """Integrate advanced loop constructs into the Sona interpreter"""
    
    def handle_for_in_loop(self, tree):
        """Handle for...in loop construct"""
        if not hasattr(self, 'advanced_loops'):
            self.advanced_loops = AdvancedLoops(self)
        
        var_name = str(tree.children[0])
        iterable_expr = tree.children[1]
        body = tree.children[2]
        label = str(tree.children[3]) if len(tree.children) > 3 else None
        
        return self.advanced_loops.execute_for_in_loop(
            var_name, iterable_expr, body, label
        )
    
    def handle_while_else_loop(self, tree):
        """Handle while...else loop construct"""
        if not hasattr(self, 'advanced_loops'):
            self.advanced_loops = AdvancedLoops(self)
        
        condition = tree.children[0]
        body = tree.children[1]
        else_body = tree.children[2] if len(tree.children) > 2 else None
        label = str(tree.children[3]) if len(tree.children) > 3 else None
        
        return self.advanced_loops.execute_while_else_loop(
            condition, body, else_body, label
        )
    
    def handle_loop_until(self, tree):
        """Handle loop...until construct"""
        if not hasattr(self, 'advanced_loops'):
            self.advanced_loops = AdvancedLoops(self)
        
        body = tree.children[0]
        until_condition = tree.children[1]
        label = str(tree.children[2]) if len(tree.children) > 2 else None
        
        return self.advanced_loops.execute_loop_until(body, until_condition, label)
    
    def handle_list_comprehension(self, tree):
        """Handle list comprehension: [expr for var in iterable if condition]"""
        if not hasattr(self, 'advanced_loops'):
            self.advanced_loops = AdvancedLoops(self)
        
        expr = tree.children[0]
        for_clauses = [child for child in tree.children[1:] 
                      if child.data == 'for_clause']
        if_clauses = [child for child in tree.children[1:] 
                     if child.data == 'if_clause']
        
        return self.advanced_loops.comprehension_engine.evaluate_list_comprehension(
            expr, for_clauses, if_clauses
        )
    
    # Add methods to interpreter class
    interpreter_class.handle_for_in_loop = handle_for_in_loop
    interpreter_class.handle_while_else_loop = handle_while_else_loop
    interpreter_class.handle_loop_until = handle_loop_until
    interpreter_class.handle_list_comprehension = handle_list_comprehension
    
    return interpreter_class
