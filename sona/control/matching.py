"""
Pattern Matching System for Sona Language - Phase 2
Implements match/case statements with destructuring and guard clauses
"""

from typing import Any, List, Dict, Optional, Union, Tuple
from lark import Tree, Token
from sona.interpreter import SonaInterpreter


class Pattern:
    """Base class for all pattern types"""
    
    def matches(self, value: Any, bindings: Dict[str, Any]) -> bool:
        """Check if pattern matches value and populate bindings"""
        raise NotImplementedError
    
    def get_bindings(self) -> List[str]:
        """Get list of variable names this pattern binds"""
        return []


class LiteralPattern(Pattern):
    """Pattern that matches exact literal values"""
    
    def __init__(self, literal_value: Any):
        self.literal_value = literal_value
    
    def matches(self, value: Any, bindings: Dict[str, Any]) -> bool:
        return value == self.literal_value


class VariablePattern(Pattern):
    """Pattern that binds a value to a variable"""
    
    def __init__(self, var_name: str):
        self.var_name = var_name
    
    def matches(self, value: Any, bindings: Dict[str, Any]) -> bool:
        bindings[self.var_name] = value
        return True
    
    def get_bindings(self) -> List[str]:
        return [self.var_name]


class WildcardPattern(Pattern):
    """Pattern that matches anything without binding (_)"""
    
    def matches(self, value: Any, bindings: Dict[str, Any]) -> bool:
        return True


class TuplePattern(Pattern):
    """Pattern that matches tuples/lists with destructuring"""
    
    def __init__(self, element_patterns: List[Pattern]):
        self.element_patterns = element_patterns
    
    def matches(self, value: Any, bindings: Dict[str, Any]) -> bool:
        if not isinstance(value, (tuple, list)):
            return False
        
        if len(value) != len(self.element_patterns):
            return False
        
        # Check each element pattern
        for i, pattern in enumerate(self.element_patterns):
            if not pattern.matches(value[i], bindings):
                return False
        
        return True
    
    def get_bindings(self) -> List[str]:
        bindings = []
        for pattern in self.element_patterns:
            bindings.extend(pattern.get_bindings())
        return bindings


class DictPattern(Pattern):
    """Pattern that matches dictionaries with key extraction"""
    
    def __init__(self, key_patterns: Dict[str, Pattern]):
        self.key_patterns = key_patterns
    
    def matches(self, value: Any, bindings: Dict[str, Any]) -> bool:
        if not isinstance(value, dict):
            return False
        
        # Check that all required keys exist and match patterns
        for key, pattern in self.key_patterns.items():
            if key not in value:
                return False
            if not pattern.matches(value[key], bindings):
                return False
        
        return True
    
    def get_bindings(self) -> List[str]:
        bindings = []
        for pattern in self.key_patterns.values():
            bindings.extend(pattern.get_bindings())
        return bindings


class TypePattern(Pattern):
    """Pattern that matches based on type"""
    
    def __init__(self, type_name: str):
        self.type_name = type_name
        # Map Sona type names to Python types
        self.type_map = {
            'int': int,
            'float': float,
            'str': str,
            'bool': bool,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'None': type(None)
        }
    
    def matches(self, value: Any, bindings: Dict[str, Any]) -> bool:
        expected_type = self.type_map.get(self.type_name)
        if expected_type is None:
            return False
        return isinstance(value, expected_type)


class GuardPattern(Pattern):
    """Pattern with guard clause (condition)"""
    
    def __init__(self, base_pattern: Pattern, guard_expr: Tree):
        self.base_pattern = base_pattern
        self.guard_expr = guard_expr
    
    def matches(self, value: Any, bindings: Dict[str, Any]) -> bool:
        # First check if base pattern matches
        if not self.base_pattern.matches(value, bindings):
            return False
        
        # Then evaluate guard expression with bindings
        # This requires access to interpreter to evaluate expression
        return True  # Placeholder - will be evaluated by matcher
    
    def get_bindings(self) -> List[str]:
        return self.base_pattern.get_bindings()


class RangePattern(Pattern):
    """Pattern that matches values within a range"""
    
    def __init__(self, start: Any, end: Any, inclusive: bool = True):
        self.start = start
        self.end = end
        self.inclusive = inclusive
    
    def matches(self, value: Any, bindings: Dict[str, Any]) -> bool:
        try:
            if self.inclusive:
                return self.start <= value <= self.end
            else:
                return self.start <= value < self.end
        except TypeError:
            return False


class ListPattern(Pattern):
    """Pattern that matches lists with head/tail destructuring"""
    
    def __init__(self, head_patterns: List[Pattern], 
                 tail_pattern: Optional[Pattern] = None):
        self.head_patterns = head_patterns
        self.tail_pattern = tail_pattern
    
    def matches(self, value: Any, bindings: Dict[str, Any]) -> bool:
        if not isinstance(value, list):
            return False
        
        if len(value) < len(self.head_patterns):
            return False
        
        # Match head patterns
        for i, pattern in enumerate(self.head_patterns):
            if not pattern.matches(value[i], bindings):
                return False
        
        # Match tail pattern if present
        if self.tail_pattern:
            tail_values = value[len(self.head_patterns):]
            if not self.tail_pattern.matches(tail_values, bindings):
                return False
        
        return True
    
    def get_bindings(self) -> List[str]:
        bindings = []
        for pattern in self.head_patterns:
            bindings.extend(pattern.get_bindings())
        if self.tail_pattern:
            bindings.extend(self.tail_pattern.get_bindings())
        return bindings


class PatternParser:
    """Parser for pattern syntax in match expressions"""
    
    def __init__(self, interpreter: SonaInterpreter):
        self.interpreter = interpreter
    
    def parse_pattern(self, pattern_tree: Tree) -> Pattern:
        """Parse a pattern tree into a Pattern object"""
        if pattern_tree.data == 'literal_pattern':
            value = self.interpreter.visit_tree(pattern_tree.children[0])
            return LiteralPattern(value)
        
        elif pattern_tree.data == 'variable_pattern':
            var_name = str(pattern_tree.children[0])
            return VariablePattern(var_name)
        
        elif pattern_tree.data == 'wildcard_pattern':
            return WildcardPattern()
        
        elif pattern_tree.data == 'tuple_pattern':
            element_patterns = [
                self.parse_pattern(child) for child in pattern_tree.children
            ]
            return TuplePattern(element_patterns)
        
        elif pattern_tree.data == 'dict_pattern':
            key_patterns = {}
            for child in pattern_tree.children:
                key = str(child.children[0])
                pattern = self.parse_pattern(child.children[1])
                key_patterns[key] = pattern
            return DictPattern(key_patterns)
        
        elif pattern_tree.data == 'type_pattern':
            type_name = str(pattern_tree.children[0])
            return TypePattern(type_name)
        
        elif pattern_tree.data == 'guard_pattern':
            base_pattern = self.parse_pattern(pattern_tree.children[0])
            guard_expr = pattern_tree.children[1]
            return GuardPattern(base_pattern, guard_expr)
        
        elif pattern_tree.data == 'range_pattern':
            start = self.interpreter.visit_tree(pattern_tree.children[0])
            end = self.interpreter.visit_tree(pattern_tree.children[1])
            inclusive = (len(pattern_tree.children) < 3 or 
                        str(pattern_tree.children[2]) != 'exclusive')
            return RangePattern(start, end, inclusive)
        
        elif pattern_tree.data == 'list_pattern':
            head_patterns = []
            tail_pattern = None
            
            for child in pattern_tree.children:
                if child.data == 'tail_pattern':
                    tail_pattern = self.parse_pattern(child.children[0])
                else:
                    head_patterns.append(self.parse_pattern(child))
            
            return ListPattern(head_patterns, tail_pattern)
        
        else:
            raise ValueError(f"Unknown pattern type: {pattern_tree.data}")


class MatchCase:
    """Represents a single case in a match statement"""
    
    def __init__(self, pattern: Pattern, body: Tree, 
                 guard_expr: Optional[Tree] = None):
        self.pattern = pattern
        self.body = body
        self.guard_expr = guard_expr
    
    def matches(self, value: Any, interpreter: SonaInterpreter) -> Tuple[bool, Dict[str, Any]]:
        """Check if this case matches the value"""
        bindings = {}
        
        # Check pattern match
        if not self.pattern.matches(value, bindings):
            return False, {}
        
        # Check guard condition if present
        if self.guard_expr:
            # Create temporary scope with pattern bindings
            interpreter.env.append(bindings.copy())
            try:
                guard_result = interpreter.visit_tree(self.guard_expr)
                if not self._is_truthy(guard_result):
                    return False, {}
            finally:
                interpreter.env.pop()
        
        return True, bindings
    
    def execute(self, interpreter: SonaInterpreter, bindings: Dict[str, Any]) -> Any:
        """Execute this case's body with pattern bindings"""
        # Create new scope with pattern bindings
        interpreter.env.append(bindings.copy())
        try:
            return interpreter.visit_tree(self.body)
        finally:
            interpreter.env.pop()
    
    def _is_truthy(self, value: Any) -> bool:
        """Check if value is truthy"""
        if value is None or value is False:
            return False
        if isinstance(value, (int, float)) and value == 0:
            return False
        if isinstance(value, (str, list, dict, set)) and len(value) == 0:
            return False
        return True


class PatternMatcher:
    """Main pattern matching engine"""
    
    def __init__(self, interpreter: SonaInterpreter):
        self.interpreter = interpreter
        self.pattern_parser = PatternParser(interpreter)
    
    def execute_match_statement(self, value_expr: Tree, 
                               cases: List[Tree]) -> Any:
        """
        Execute match statement:
        match value {
            case pattern1 => body1
            case pattern2 if guard => body2
            case _ => default_body
        }
        """
        # Evaluate the value to match against
        match_value = self.interpreter.visit_tree(value_expr)
        
        # Parse and check each case
        for case_tree in cases:
            case = self._parse_case(case_tree)
            
            matched, bindings = case.matches(match_value, self.interpreter)
            if matched:
                return case.execute(self.interpreter, bindings)
        
        # No case matched - this should be a runtime error in most cases
        # unless there's a wildcard case
        raise RuntimeError(f"No pattern matched value: {match_value}")
    
    def _parse_case(self, case_tree: Tree) -> MatchCase:
        """Parse a case tree into a MatchCase object"""
        pattern_tree = case_tree.children[0]
        body = case_tree.children[-1]  # Last child is always body
        
        # Check if there's a guard expression
        guard_expr = None
        if len(case_tree.children) > 2:
            guard_expr = case_tree.children[1]
        
        pattern = self.pattern_parser.parse_pattern(pattern_tree)
        return MatchCase(pattern, body, guard_expr)


def integrate_pattern_matching(interpreter_class):
    """Integrate pattern matching into the Sona interpreter"""
    
    def handle_match_statement(self, tree):
        """Handle match statement"""
        if not hasattr(self, 'pattern_matcher'):
            self.pattern_matcher = PatternMatcher(self)
        
        value_expr = tree.children[0]
        cases = tree.children[1:]
        
        return self.pattern_matcher.execute_match_statement(value_expr, cases)
    
    def handle_destructuring_assignment(self, tree):
        """Handle destructuring assignment: let (a, b, c) = tuple_value"""
        if not hasattr(self, 'pattern_matcher'):
            self.pattern_matcher = PatternMatcher(self)
        
        pattern_tree = tree.children[0]
        value_expr = tree.children[1]
        
        # Evaluate the right-hand side
        value = self.visit_tree(value_expr)
        
        # Parse and match pattern
        pattern = self.pattern_matcher.pattern_parser.parse_pattern(pattern_tree)
        bindings = {}
        
        if pattern.matches(value, bindings):
            # Add bindings to current scope
            for var_name, var_value in bindings.items():
                self.env[-1][var_name] = var_value
            return value
        else:
            raise RuntimeError(f"Pattern does not match value: {value}")
    
    # Add methods to interpreter class
    interpreter_class.handle_match_statement = handle_match_statement
    interpreter_class.handle_destructuring_assignment = handle_destructuring_assignment
    
    return interpreter_class
